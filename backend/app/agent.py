import os
import sys
import asyncio
import json
import tempfile
import shutil
import re
from pathlib import Path
from typing import TypedDict, List, Dict, Any, AsyncGenerator, Optional
from langgraph.graph import StateGraph, END
from langchain_cohere import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
import git

from .config import Config
from .utils import generate_pdf_base64, generate_txt, sanitize_text

# --- State ---
class AgentState(TypedDict):
    repo_url: str
    repo_tree: List[str]
    file_contents: Dict[str, str]
    code_metadata: Dict[str, Any]
    diagrams: Dict[str, str]
    final_report: str
    pdf_base64: str
    txt_content: str
    selected_diagram_types: List[str]  # new

# --- Two LLM instances ---
llm_json = ChatCohere(
    model=Config.COHERE_MODEL,
    cohere_api_key=Config.COHERE_API_KEY,
    temperature=0.2,
    max_tokens=4096,
    model_kwargs={"response_format": {"type": "json_object"}}
)

llm = ChatCohere(
    model=Config.COHERE_MODEL,
    cohere_api_key=Config.COHERE_API_KEY,
    temperature=0.3,
    max_tokens=4096,
)

# --- Fetch repo ---
async def fetch_repo_direct(repo_url: str) -> dict:
    temp_dir = tempfile.mkdtemp(prefix="repo_")
    repo_path = Path(temp_dir) / "repo"
    try:
        git.Repo.clone_from(repo_url, repo_path, depth=1)
        context = {"repo_url": repo_url, "tree": [], "contents": {}}
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            rel_root = Path(root).relative_to(repo_path)
            for file in files:
                if file.startswith('.'):
                    continue
                file_path = Path(root) / file
                rel_path = str(rel_root / file)
                ext = file_path.suffix.lower()
                if ext in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.md', '.txt', '.json', '.yaml', '.yml', '.html', '.css']:
                    try:
                        if file_path.stat().st_size < 50000:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if len(content) > 10000:
                                    content = content[:10000] + "\n... (truncated)"
                                context["contents"][rel_path] = content
                    except Exception:
                        pass
                context["tree"].append(rel_path)
        if len(context["tree"]) > 200:
            context["tree"] = context["tree"][:200]
        shutil.rmtree(temp_dir, ignore_errors=True)
        return context
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to fetch repo: {e}")

# --- Helper to strip markdown code fences ---
def strip_code_fences(content: str) -> str:
    lines = content.split('\n')
    if lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith('```'):
        lines = lines[:-1]
    return '\n'.join(lines).strip()

# --- Nodes ---
async def fetch_context(state: AgentState):
    print("📂 Fetching repository...")
    context = await fetch_repo_direct(state["repo_url"])
    state["repo_tree"] = context.get("tree", [])
    state["file_contents"] = context.get("contents", {})
    print(f"   ✅ Found {len(state['repo_tree'])} files, {len(state['file_contents'])} with content")
    return state

async def analyze_code(state: AgentState):
    print("🧠 Analyzing codebase...")
    tree_str = "\n".join(state["repo_tree"][:100])
    content_preview = "\n\n".join([f"File: {k}\n{v[:500]}" for k, v in list(state["file_contents"].items())[:5]])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Software Architect. Extract the following information from the repository context and return it **only** as a valid JSON object with these keys:
- "project_summary": string,
- "classes": list of objects with "name", "attributes", "methods",
- "entities": list of object names,
- "user_roles": list of strings,
- "dependencies": list of strings.

Do not include any extra text. Output only the JSON."""),
        ("user", "Repository Tree:\n{tree}\n\nSample File Contents:\n{contents}")
    ])
    parser = JsonOutputParser()
    chain = prompt | llm_json | parser
    try:
        state["code_metadata"] = chain.invoke({"tree": tree_str, "contents": content_preview})
        print("   ✅ JSON parsed successfully")
    except Exception as e:
        print(f"   ⚠️ JSON parsing failed: {e}")
        raw = (prompt | llm_json).invoke({"tree": tree_str, "contents": content_preview}).content
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            try:
                state["code_metadata"] = json.loads(json_match.group())
                print("   ✅ Fallback JSON extraction worked")
            except Exception:
                state["code_metadata"] = {}
                print("   ❌ Fallback JSON extraction failed")
        else:
            state["code_metadata"] = {}
            print("   ❌ No JSON found in response")
        if not state["code_metadata"]:
            state["code_metadata"] = {
                "project_summary": "Analysis failed.",
                "classes": [],
                "entities": [],
                "user_roles": [],
                "dependencies": []
            }
    for key in state["code_metadata"]:
        if isinstance(state["code_metadata"][key], str):
            state["code_metadata"][key] = sanitize_text(state["code_metadata"][key])
    return state

async def generate_diagrams(state: AgentState):
    print("📊 Generating diagrams...")
    metadata = state["code_metadata"]
    selected = state.get("selected_diagram_types", [])
    
    # If no selection, generate all
    if not selected:
        selected = ["Class_Diagram", "ER_Diagram", "Usecase_Diagram"]
    
    diagrams = {}
    
    # Define all possible diagrams
    all_configs = {
        "Class_Diagram": {
            "system": """Generate ONLY valid Mermaid classDiagram code.

Rules:
- Output Mermaid code only.
- First line must be exactly:
  classDiagram

- If a class has no members:
  class User

- If a class has members:
  class User {
      +String name
      +login()
  }

- Never generate:
  - nested braces
  - empty braces
  - explanations
  - markdown fences
  - ```mermaid

- Class identifiers must contain only:
  A-Z a-z 0-9 _

- If the displayed name contains spaces, slashes or dashes, use an alias:
  class GPT4["OpenAI GPT-4"]
  class MistralModel["mistralai/Mistral-7B-Instruct"]

- Use only Mermaid-supported relationships:
  --> ..> *-- o-- <|-- <|..

- Multiplicities must be quoted:
  User "1" --> "*" Review

- Ensure the output renders successfully in Mermaid Live Editor without any syntax errors.""",
            "fallback": """classDiagram
    class Project {
        +String name
        +String description
        +void start()
    }
    class Main {
        +void run()
    }
    Project --> Main : uses"""
        },
        "ER_Diagram": {
            "system": """Generate a valid Mermaid ER diagram.
Start with the keyword erDiagram.
Define entities and relationships using syntax like: ENTITY1 ||--o{ ENTITY2 : description
Do not include any extra text. Output only the Mermaid code.""",
            "fallback": """erDiagram
    PROJECT ||--o{ MODULE : contains
    MODULE ||--o{ FILE : has"""
        },
        "Usecase_Diagram": {
            "system": """Generate a Mermaid flowchart (left‑to‑right) that represents actors and their actions – this is a replacement for a use‑case diagram.
Start with 'flowchart LR'.
Define actors as nodes with square brackets: ActorName[Actor Name] (use underscores for spaces; avoid quotes and special characters).
Define actions/use cases as nodes with parentheses: ActionName((Action Description)) (use underscores for spaces).
Connect actors to actions with arrows: ActorName --> ActionName.
Only include actors and their direct interactions. Output only the Mermaid code.

Example:
flowchart LR
    User[User]
    Admin[Admin]
    Login((Login))
    ManageUsers((Manage Users))
    User --> Login
    Admin --> Login
    Admin --> ManageUsers""",
            "fallback": """flowchart LR
    User[User]
    Admin[Admin]
    ViewData((View Data))
    ManageSystem((Manage System))
    User --> ViewData
    Admin --> ManageSystem
    Admin --> ViewData"""
        }
    }
    
    for name in selected:
        if name not in all_configs:
            continue
        config = all_configs[name]
        try:
            messages = [
                SystemMessage(content=config["system"]),
                HumanMessage(content=f"Metadata:\n{json.dumps(metadata, indent=2)}")
            ]
            response = llm.invoke(messages)
            content = response.content.strip()
            content = strip_code_fences(content)
            # Additional cleaning for class diagrams (optional)
            if name == "Class_Diagram":
                # Remove duplicate class class, etc.
                content = clean_class_diagram(content)
            if not content or len(content) < 10:
                print(f"   ⚠️ Empty response for {name}, using fallback")
                content = config["fallback"]
            diagrams[name] = content
            print(f"   ✅ {name} generated ({len(content)} chars)")
        except Exception as e:
            print(f"   ❌ Error generating {name}: {e}")
            diagrams[name] = config["fallback"]
    
    state["diagrams"] = diagrams
    return state

# (Include the clean_class_diagram helper function here – paste from earlier, or just use a simple version)
def clean_class_diagram(code: str) -> str:
    # Simple cleaning: remove markdown fences, sanitize class names
    code = strip_code_fences(code)
    lines = code.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('class '):
            parts = stripped.split(' ')
            if len(parts) >= 2:
                name_part = parts[1].strip('"').strip("'")
                safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name_part)
                new_line = f"class {safe_name}"
                if len(parts) > 2:
                    new_line += " " + " ".join(parts[2:])
                cleaned.append(new_line)
            else:
                cleaned.append(line)
        else:
            cleaned.append(line)
    if not cleaned or cleaned[0] != 'classDiagram':
        cleaned.insert(0, 'classDiagram')
    return '\n'.join(cleaned)

async def compile_report(state: AgentState):
    print("📝 Generating comprehensive report...")
    metadata = state["code_metadata"]
    repo_url = state["repo_url"]

    report_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a technical documentation expert. Analyze the provided project metadata and produce a comprehensive project report in markdown format.

**IMPORTANT:** Your report must have exactly these sections in this order:

1. **Project Overview** – a concise summary: what the project does, its main purpose, and who it's for.
2. **Key Features** – list the main features that are **already implemented** (be specific, use bullet points).
3. **What is Missing / Gaps** – identify important features, components, or aspects that are currently missing, incomplete, or below standard (be precise).
4. **Suggestions & Future Enhancements** – provide actionable recommendations for:
   - Deployment (e.g., CI/CD, containerization, hosting)
   - Integration (e.g., third‑party services, APIs)
   - Testing (e.g., unit, integration, e2e)
   - Security (e.g., authentication, authorization, data protection)
   - Performance & scalability
   - Documentation (e.g., API docs, user guides)
   - Any other improvements you deem valuable.

Do not include any extra text outside these sections. Use clear, professional language. Format with proper markdown headings (##, ###) and bullet points where appropriate."""),
        ("user", "Repository URL: {repo_url}\n\nMetadata:\n{metadata}")
    ])

    try:
        response = (report_prompt | llm).invoke({
            "repo_url": repo_url,
            "metadata": json.dumps(metadata, indent=2)
        })
        report = response.content.strip()
        if not report or len(report) < 20:
            raise ValueError("Empty or too short report")
        state["final_report"] = sanitize_text(report)
        print("   ✅ Full report generated successfully")
    except Exception as e:
        print(f"   ⚠️ Report generation failed: {e}")
        fallback_report = f"""# 📘 Project Report

## Project Overview
{metadata.get("project_summary", "Summary not available.")}

## Key Features
- {', '.join([c.get('name', '') for c in metadata.get("classes", [])]) if metadata.get("classes") else "No main classes extracted."}

## What is Missing / Gaps
- Further analysis required. The metadata may be incomplete.

## Suggestions & Future Enhancements
- Set up CI/CD pipeline.
- Add comprehensive testing.
- Improve documentation and onboarding.
"""
        state["final_report"] = sanitize_text(fallback_report)
    return state

async def export_files(state: AgentState):
    print("💾 Exporting files...")
    try:
        state["pdf_base64"] = generate_pdf_base64(state["final_report"], state["diagrams"])
        state["txt_content"] = generate_txt(state["final_report"], state["diagrams"])
        print("   ✅ PDF and TXT generated")
    except Exception as e:
        print(f"   ❌ Export error: {e}")
        state["pdf_base64"] = ""
        state["txt_content"] = f"Error generating files: {e}\n\nReport:\n{state['final_report']}"
    return state

# --- Graph ---
def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("fetch_context", fetch_context)
    workflow.add_node("analyze_code", analyze_code)
    workflow.add_node("generate_diagrams", generate_diagrams)
    workflow.add_node("compile_report", compile_report)
    workflow.add_node("export_files", export_files)
    workflow.set_entry_point("fetch_context")
    workflow.add_edge("fetch_context", "analyze_code")
    workflow.add_edge("analyze_code", "generate_diagrams")
    workflow.add_edge("generate_diagrams", "compile_report")
    workflow.add_edge("compile_report", "export_files")
    workflow.add_edge("export_files", END)
    return workflow.compile()

# --- Streaming ---
async def run_agent_streaming(repo_url: str, diagram_types: Optional[List[str]] = None) -> AsyncGenerator[dict, None]:
    app = build_graph()
    initial_state: AgentState = {
        "repo_url": repo_url,
        "repo_tree": [],
        "file_contents": {},
        "code_metadata": {},
        "diagrams": {},
        "final_report": "",
        "pdf_base64": "",
        "txt_content": "",
        "selected_diagram_types": diagram_types or []
    }
    yield {"type": "status", "step": "starting", "message": "Agent started..."}

    final_state = initial_state.copy()
    step_names = ["fetch_context", "analyze_code", "generate_diagrams", "compile_report", "export_files"]
    step_index = 0

    try:
        async for event in app.astream(initial_state, config={"recursion_limit": 50}, stream_mode="values"):
            final_state = event
            if step_index < len(step_names):
                step_name = step_names[step_index]
                step_map = {
                    "fetch_context": "📂 Fetching repository...",
                    "analyze_code": "🧠 Analyzing codebase...",
                    "generate_diagrams": "📊 Generating diagrams...",
                    "compile_report": "📝 Writing report...",
                    "export_files": "💾 Exporting files..."
                }
                yield {
                    "type": "progress",
                    "step": step_name,
                    "message": step_map.get(step_name, step_name),
                    "data": event
                }
                step_index += 1
    except Exception as e:
        import traceback
        error_msg = f"Agent error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        yield {"type": "error", "message": error_msg}
    finally:
        if not final_state.get("diagrams"):
            final_state["diagrams"] = {
                "Class_Diagram": "classDiagram\n    class Project {\n        +String name\n    }",
                "ER_Diagram": "erDiagram\n    PROJECT ||--o{ MODULE : contains",
                "Usecase_Diagram": "flowchart LR\n    User[User]\n    Admin[Admin]\n    ViewData((View Data))\n    User --> ViewData\n    Admin --> ViewData"
            }
        if not final_state.get("final_report"):
            final_state["final_report"] = "Report could not be generated.\nPlease check the backend logs."

        yield {
            "type": "complete",
            "report": final_state.get("final_report", "Report not available"),
            "diagrams": final_state.get("diagrams", {}),
            "pdf_base64": final_state.get("pdf_base64", ""),
            "txt_content": final_state.get("txt_content", ""),
            "file_contents": final_state.get("file_contents", {}),
            "code_metadata": final_state.get("code_metadata", {})
        }
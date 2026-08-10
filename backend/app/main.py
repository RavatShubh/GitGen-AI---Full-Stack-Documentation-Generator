from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Dict, List, Any
from pydantic import BaseModel
from .agent import run_agent_streaming
from .config import Config
from langchain_cohere import ChatCohere
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache for repo contexts (file contents + metadata)
repo_cache: Dict[str, Dict[str, Any]] = {}

# Cohere chat instance (without JSON mode)
chat_llm = ChatCohere(
    model=Config.COHERE_MODEL,
    cohere_api_key=Config.COHERE_API_KEY,
    temperature=0.3,
    max_tokens=2048,
)

# Cohere instance for roadmap generation
roadmap_llm = ChatCohere(
    model=Config.COHERE_MODEL,
    cohere_api_key=Config.COHERE_API_KEY,
    temperature=0.3,
    max_tokens=4096,
)

# ------------------------- WebSocket for agent -------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        repo_data = json.loads(data)
        repo_url = repo_data.get("repo_url")
        if not repo_url:
            await websocket.send_json({"type": "error", "message": "Missing repo_url"})
            return

        final_state = {}
        async for event in run_agent_streaming(repo_url):
            await websocket.send_json(event)
            if event.get("type") == "complete":
                final_state = {
                    "file_contents": event.get("file_contents", {}),
                    "code_metadata": event.get("code_metadata", {}),
                    "diagrams": event.get("diagrams", {}),
                    "report": event.get("report", "")
                }
                # Cache the repo context
                repo_cache[repo_url] = {
                    "file_contents": final_state.get("file_contents", {}),
                    "metadata": final_state.get("code_metadata", {})
                }
                break
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})

# ------------------------- Chat Endpoint -------------------------
class ChatRequest(BaseModel):
    repo_url: str
    question: str
    history: List[Dict[str, str]] = []

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    repo_url = req.repo_url
    if repo_url not in repo_cache:
        raise HTTPException(status_code=404, detail="Repository not processed yet. Please generate documentation first.")

    context = repo_cache[repo_url]
    file_contents = context.get("file_contents", {})
    metadata = context.get("metadata", {})

    # Build a list of documents
    documents = []

    # 1. Add project metadata as a high‑level document
    project_overview = f"""
Project Summary: {metadata.get("project_summary", "Not available")}

Main Classes: {', '.join([c.get('name', '') for c in metadata.get("classes", [])])}

Key Dependencies: {', '.join(metadata.get("dependencies", []))}

User Roles: {', '.join(metadata.get("user_roles", []))}
"""
    documents.append({
        "text": project_overview[:2000],
        "metadata": {"source": "project_metadata"}
    })

    # 2. Add file contents (truncated and limited)
    file_list = list(file_contents.items())
    for path, content in file_list[:15]:
        truncated = content[:1500] + "..." if len(content) > 1500 else content
        documents.append({
            "text": f"File: {path}\n{truncated}",
            "metadata": {"source": path}
        })

    # System prompt – business-aware
    system_prompt = f"""You are a technical and business analyst assistant. 
You have access to the codebase of the project at {repo_url}. 
Your task is to answer questions about the project, its features, architecture, and potential use cases.

**When asked about potential organizations or companies that would use this project**:
- Analyse the project's purpose, features, and technology stack.
- Suggest specific types of organisations (e.g., startups, enterprises, government, specific industries) that would benefit.
- Give concrete examples of companies (or company types) and explain why they would adopt it.
- Base your answer on the code and metadata provided.

If you don't know the answer, say so clearly.
Do not mention that you are an AI; just provide helpful, factual responses.
"""

    messages = [SystemMessage(content=system_prompt)]

    # Trim history: keep only last 3 user-assistant pairs
    history = req.history
    if len(history) > 6:
        history = history[-6:]

    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"][:500]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"][:500]))

    current_question = req.question[:500]
    messages.append(HumanMessage(content=current_question))

    try:
        response = chat_llm.invoke(
            messages,
            documents=documents
        )
        answer = response.content
        return {"answer": answer}
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# ------------------------- Roadmap Endpoint -------------------------
class RoadmapRequest(BaseModel):
    repo_url: str

def generate_fallback_roadmap(metadata: dict) -> str:
    """Generate a fallback Mermaid timeline if the LLM fails."""
    return """timeline
    title Learning Roadmap
    
    Step 1 : Setup & Overview
           : Understand project purpose
           : Install dependencies
           : Run the project locally
    
    Step 2 : Core Concepts
           : Understand main architecture
           : Explore key classes
           : Learn data flow
    
    Step 3 : Deep Dive
           : Study critical components
           : Understand integrations
           : Review tests
    
    Step 4 : Extend & Contribute
           : Add a small feature
           : Write tests
           : Submit pull request"""

@app.post("/roadmap")
async def generate_roadmap(req: RoadmapRequest):
    """Generate a text-only learning roadmap."""
    repo_url = req.repo_url
    
    if repo_url not in repo_cache:
        raise HTTPException(status_code=404, detail="Repository not processed yet. Please generate documentation first.")
    
    context = repo_cache[repo_url]
    metadata = context.get("metadata", {})
    file_contents = context.get("file_contents", {})
    
    # Build file summary
    files_summary = []
    for path in list(file_contents.keys())[:20]:
        files_summary.append(f"- {path}")
    
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior software engineer and technical mentor. 
            Create a detailed learning roadmap for this codebase.

            The roadmap should be text-based with clear sections:
            1. **Prerequisites** – what to know before starting
            2. **Milestone 1: Setup** – how to set up the project
            3. **Milestone 2: Core Concepts** – key architectural patterns
            4. **Milestone 3: Key Features** – main functionality
            5. **Milestone 4: Testing & Quality** – testing strategy
            6. **Milestone 5: Contribution** – how to contribute
            7. **Additional Resources** – useful links/docs

            Be specific and reference actual files from the repository.
            Format as clean markdown with bold headers and bullet points."""),
            ("user", """Repository: {repo_url}

Project Summary: {summary}
Main Classes: {classes}
Dependencies: {dependencies}

Files in Repository:
{files}

Create a text-based learning roadmap.""")
        ])
        
        chain = prompt | roadmap_llm
        response = chain.invoke({
            "repo_url": repo_url,
            "summary": metadata.get("project_summary", "Project"),
            "classes": ', '.join([c.get('name', '') for c in metadata.get("classes", [])]),
            "dependencies": ', '.join(metadata.get("dependencies", [])),
            "files": '\n'.join(files_summary[:15])
        })
        
        return {"text_summary": response.content}
    except Exception as e:
        print(f"Roadmap generation error: {e}")
        return {"text_summary": create_text_summary(metadata, files_summary)}

def create_text_summary(metadata: dict, files: list) -> str:
    """Create a text-only fallback roadmap."""
    return f"""
# 🗺️ Learning Roadmap: {metadata.get('project_summary', 'Project')}

## 📋 Prerequisites
- Basic understanding of the language/framework used
- Git and GitHub basics
- Familiarity with the dependencies: {', '.join(metadata.get('dependencies', ['unknown']))}

## 🎯 Milestone 1: Setup & Overview (1-2 hours)
- Clone the repository: `git clone [repo-url]`
- Review README and documentation
- Install dependencies
- Run the project locally

## 🎯 Milestone 2: Core Architecture (3-4 hours)
- Understand the project structure
- Study main entry points and configuration
- Learn the architecture and design patterns
- Explore key modules and their responsibilities

## 🎯 Milestone 3: Key Features (4-5 hours)
- Deep dive into main features
- Understand the business logic
- Learn how data flows through the system
- Study API endpoints (if applicable)

## 🎯 Milestone 4: Testing & Quality (2-3 hours)
- Understand the testing strategy
- Run existing tests
- Write a simple test
- Learn about CI/CD pipeline (if applicable)

## 🎯 Milestone 5: Contribution (4-6 hours)
- Identify a small feature to add or bug to fix
- Implement with proper tests
- Follow contribution guidelines
- Submit a pull request

## 📂 Key Files to Focus On
{chr(10).join(files[:10])}

## 📚 Additional Resources
- Project documentation (if available)
- Relevant tutorials and guides
- Community channels
"""


@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
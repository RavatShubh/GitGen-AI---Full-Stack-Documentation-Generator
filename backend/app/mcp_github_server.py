import os
import shutil
import tempfile
from pathlib import Path
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import git
from .config import Config

server = Server("github-context-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_repo_context",
            description="Clones a GitHub repository and returns its directory tree and the content of key files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_url": {"type": "string", "description": "The HTTPS URL of the GitHub repository."},
                },
                "required": ["repo_url"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_repo_context":
        repo_url = arguments["repo_url"]
        temp_dir = tempfile.mkdtemp(prefix="mcp_repo_")
        repo_path = Path(temp_dir) / "repo"
        try:
            git.Repo.clone_from(repo_url, repo_path, depth=1)
            context_data = {"repo_url": repo_url, "tree": [], "contents": {}}
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
                relative_root = Path(root).relative_to(repo_path)
                for file in files:
                    if file.startswith('.'):
                        continue
                    file_path = Path(root) / file
                    relative_path = str(relative_root / file)
                    ext = file.suffix.lower()
                    if ext in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.md', '.txt', '.json', '.yaml', '.yml', '.html', '.css']:
                        try:
                            if file_path.stat().st_size < 50000:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    if len(content) > 10000:
                                        content = content[:10000] + "\n... (truncated)"
                                    context_data["contents"][relative_path] = content
                        except Exception:
                            pass
                    context_data["tree"].append(relative_path)
            if len(context_data["tree"]) > 200:
                context_data["tree"] = context_data["tree"][:200]
            shutil.rmtree(temp_dir)
            import json
            return [types.TextContent(type="text", text=json.dumps(context_data, indent=2))]
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return [types.TextContent(type="text", text=f"Error fetching repo: {str(e)}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="github-context-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
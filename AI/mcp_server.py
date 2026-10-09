"""
MCP (Model Context Protocol) Server for VaultMind Desktop.

This module provides HTTP API endpoints that allow external AI systems
(like Claude Code) to search and interact with the vault.
"""
import json
import time
import threading
from pathlib import Path
from typing import Optional, List
import logging
import sys

# Ensure imports work when run as module
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from AI.services.api_client import VaultMindClient
from AI.config import config

logger = logging.getLogger(__name__)

app = FastAPI(title="VaultMind MCP", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_client: Optional[VaultMindClient] = None


def get_client() -> VaultMindClient:
    global _client
    if _client is None:
        _client = VaultMindClient(config.api_url)
    return _client


@app.get("/health")
def health_check():
    return {"status": "healthy", "vault": config.default_vault}


@app.get("/search")
def search_vault(q: str, limit: int = 10):
    """Search the vault using semantic search."""
    try:
        client = get_client()
        results = client.search(config.default_vault, q, limit=limit)
        
        if not results:
            return {"query": q, "results": [], "count": 0}
        
        return {
            "query": q,
            "results": [
                {
                    "content": r.get("content", "")[:500],
                    "file": r.get("metadata", {}).get("file_path", "unknown"),
                    "score": r.get("score", 0),
                }
                for r in results
            ],
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats():
    """Get vault statistics."""
    try:
        client = get_client()
        collections = client.get_collections()
        
        return {
            "default_vault": config.default_vault,
            "collections": collections or [],
            "vault_path": config.vaults.get(config.default_vault, {}).get("path", ""),
            "mcp_port": config.mcp_port,
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files")
def list_files(path: str = None):
    """List files in vault."""
    try:
        vault_path = path or config.vaults.get(config.default_vault, {}).get("path", "")
        if not vault_path:
            raise HTTPException(status_code=400, detail="No vault path configured")
        
        vault = Path(vault_path)
        if not vault.exists():
            raise HTTPException(status_code=404, detail="Vault not found")
        
        files = []
        for item in sorted(vault.iterdir())[:50]:
            files.append({
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
            })
        
        return {"path": vault_path, "files": files, "count": len(files)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/read")
def read_file(path: str, offset: int = 0, limit: int = 2000):
    """Read a file from the vault."""
    try:
        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        content = file_path.read_text()
        lines = content.split("\n")
        
        if offset > 0:
            lines = lines[offset:]
        if limit > 0:
            lines = lines[:limit]
        
        return {
            "path": str(file_path),
            "content": "\n".join(lines),
            "total_lines": len(content.split("\n")),
            "truncated": limit > 0 and len(lines) >= limit,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Read error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/todos")
def get_todos():
    """Get all todos."""
    try:
        from ui.todo_view import TodoList
        todos = TodoList.load()
        return {"todos": todos, "count": len(todos)}
    except Exception as e:
        logger.error(f"Todos error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/todos")
def add_todo(content: str, priority: str = "medium"):
    """Add a new todo."""
    try:
        from ui.todo_view import TodoList
        todos = TodoList.load()
        todos.append({
            "id": str(int(time.time())),
            "content": content,
            "priority": priority,
            "completed": False,
            "created": time.time(),
        })
        TodoList.save(todos)
        return {"status": "added", "content": content}
    except Exception as e:
        logger.error(f"Add todo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/todos/{todo_id}")
def update_todo(todo_id: str, completed: bool = None, content: str = None):
    """Update a todo."""
    try:
        from ui.todo_view import TodoList
        todos = TodoList.load()
        for t in todos:
            if str(t.get("id")) == str(todo_id):
                if completed is not None:
                    t["completed"] = completed
                if content is not None:
                    t["content"] = content
                TodoList.save(todos)
                return {"status": "updated", "todo": t}
        raise HTTPException(status_code=404, detail="Todo not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update todo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: str):
    """Delete a todo."""
    try:
        from ui.todo_view import TodoList
        todos = TodoList.load()
        todos = [t for t in todos if str(t.get("id")) != str(todo_id)]
        TodoList.save(todos)
        return {"status": "deleted", "todo_id": todo_id}
    except Exception as e:
        logger.error(f"Delete todo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index")
def trigger_index(force: bool = False):
    """Trigger vault indexing."""
    try:
        client = get_client()
        vault_path = config.vaults.get(config.default_vault, {}).get("path", "")
        if not vault_path:
            raise HTTPException(status_code=400, detail="No vault path configured")
        
        job_id = client.index_vault(config.default_vault, vault_path, force_reindex=force)
        return {"status": "started", "job_id": job_id}
    except Exception as e:
        logger.error(f"Index error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
def get_config():
    """Get MCP server configuration."""
    return {
        "api_url": config.api_url,
        "default_vault": config.default_vault,
        "vaults": config.vaults,
        "theme": config.theme,
    }


class MCPServer:
    """MCP Server manager."""
    
    _instance: Optional["MCPServer"] = None
    _thread: Optional[threading.Thread] = None
    _running = False
    
    def __init__(self, port: int = 9090):
        self.port = port
    
    @classmethod
    def get_instance(cls, port: int = 9090) -> "MCPServer":
        if cls._instance is None:
            cls._instance = cls(port)
        return cls._instance
    
    def start(self):
        """Start MCP server in background thread."""
        if self._running:
            return True
        
        def _run():
            uvicorn.run(app, host="127.0.0.1", port=self.port, log_level="warning")
        
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        
        for _ in range(20):
            try:
                import httpx
                resp = httpx.get(f"http://127.0.0.1:{self.port}/health", timeout=1.0)
                if resp.status_code == 200:
                    self._running = True
                    logger.info(f"MCP Server started on port {self.port}")
                    return True
            except:
                pass
            time.sleep(0.5)
        
        logger.error("Failed to start MCP server")
        return False
    
    def stop(self):
        """Stop MCP server."""
        self._running = False
        self._thread = None
    
    def is_running(self) -> bool:
        return self._running


def start_mcp_server(port: int = 9090) -> bool:
    """Convenience function to start MCP server."""
    server = MCPServer.get_instance(port)
    return server.start()


def stop_mcp_server():
    """Convenience function to stop MCP server."""
    server = MCPServer.get_instance()
    server.stop()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9090
    print(f"Starting VaultMind MCP Server on port {port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)
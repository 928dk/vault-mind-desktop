"""OpenCode integration for VaultMind Desktop."""
import subprocess
import httpx
import json
import time
import logging
import threading
from typing import Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

OPENCODE_BIN = Path.home() / ".opencode" / "bin" / "opencode"
DEFAULT_PORT = 4097
DEFAULT_HOST = "127.0.0.1"


class OpenCodeIntegration:
    """Integration with OpenCode AI for VaultMind."""

    def __init__(
        self,
        port: int = DEFAULT_PORT,
        hostname: str = DEFAULT_HOST,
        on_output: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        self.port = port
        self.hostname = hostname
        self.base_url = f"http://{hostname}:{port}"
        self.on_output = on_output
        self.on_error = on_error
        self._process: Optional[subprocess.Popen] = None
        self._client: Optional[httpx.Client] = None
        self._is_running = False

    def start_server(self, timeout: int = 10) -> bool:
        """Start opencode server in background."""
        if self._is_running:
            return True

        try:
            cmd = [
                str(OPENCODE_BIN),
                "serve",
                "--port", str(self.port),
                "--hostname", self.hostname,
            ]
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if self._wait_for_server(timeout):
                self._client = httpx.Client(timeout=30.0)
                self._is_running = True
                logger.info(f"OpenCode server started at {self.base_url}")
                return True
            else:
                self._process.terminate()
                logger.error("Failed to start OpenCode server")
                return False

        except Exception as e:
            logger.error(f"Error starting OpenCode: {e}")
            return False

    def _wait_for_server(self, timeout: int) -> bool:
        """Wait for server to be ready."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = httpx.get(f"{self.base_url}/config", timeout=1.0)
                if resp.status_code in [200, 404]:
                    return True
            except:
                pass
            time.sleep(0.5)
        return False

    def stop_server(self):
        """Stop the opencode server."""
        self._is_running = False
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
        if self._client:
            self._client.close()
            self._client = None
        logger.info("OpenCode server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._is_running

    def run_prompt(self, prompt: str, cwd: str = None) -> dict:
        """Run a prompt via opencode CLI."""
        if not self._is_running:
            return {"error": "Server not running"}

        try:
            result = subprocess.run(
                [
                    str(OPENCODE_BIN),
                    "run",
                    "--server", self.base_url,
                    prompt
                ],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=120,
            )
            
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"error": result.stderr, "output": result.stdout}

        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": str(e)}

    def get_config(self) -> dict:
        """Get opencode configuration."""
        if not self._client:
            return {"error": "Client not initialized"}
        
        try:
            resp = self._client.get(f"{self.base_url}/config")
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def list_projects(self) -> list:
        """List opencode projects."""
        if not self._client:
            return []
        
        try:
            resp = self._client.get(f"{self.base_url}/project")
            if resp.status_code == 200:
                return resp.json().get("data", {}).get("projects", [])
        except:
            pass
        return []

    def get_tools(self) -> list:
        """List available tools."""
        if not self._client:
            return []
        
        try:
            resp = self._client.get(f"{self.base_url}/experimental/tool/ids")
            if resp.status_code == 200:
                return resp.json().get("data", [])
        except:
            pass
        return []

    def search_vault(self, query: str, vault_path: str = None) -> str:
        """Search vault using semantic search - exposed as opencode tool."""
        try:
            from services.api_client import VaultMindClient
            from config import config
            
            client = VaultMindClient(config.api_url)
            vault_name = config.default_vault or "my_vault"
            results = client.search(vault_name, query, limit=5)
            
            if not results:
                return "No results found."
            
            output = f"Search results for '{query}':\n\n"
            for i, r in enumerate(results, 1):
                filepath = r.get("metadata", {}).get("file_path", "Unknown")
                content = r.get("content", "")[:200]
                output += f"{i}. {filepath}\n   {content}...\n\n"
            
            return output
        except Exception as e:
            return f"Search error: {e}"

    def get_vault_stats(self) -> str:
        """Get vault statistics - exposed as opencode tool."""
        try:
            from services.api_client import VaultMindClient
            from config import config
            
            client = VaultMindClient(config.api_url)
            collections = client.get_collections()
            
            if not collections:
                return "No collections indexed."
            
            output = "Vault statistics:\n\n"
            for coll in collections:
                name = coll.get("name", "Unknown")
                count = coll.get("count", 0)
                output += f"- {name}: {count} documents\n"
            
            return output
        except Exception as e:
            return f"Error: {e}"

    def list_todos(self) -> str:
        """List personal todos - exposed as opencode tool."""
        try:
            from ui.todo_view import TodoList
            
            todos = TodoList.load()
            if not todos:
                return "No todos."
            
            output = "Personal TODO list:\n\n"
            for t in todos:
                status = "[x]" if t.get("completed") else "[ ]"
                priority = t.get("priority", "").upper()
                output += f"{status} {priority} {t.get('content', '')}\n"
            
            return output
        except Exception as e:
            return f"Error: {e}"

    def add_todo(self, content: str, priority: str = "medium") -> str:
        """Add a todo - exposed as opencode tool."""
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
            return f"Added todo: {content}"
        except Exception as e:
            return f"Error: {e}"

    def browse_vault(self, path: str = None) -> str:
        """Browse vault files - exposed as opencode tool."""
        try:
            from config import config
            
            vault_path = path or config.vaults.get(config.default_vault, {}).get("path", "")
            if not vault_path:
                return "No vault path configured."
            
            vault = Path(vault_path)
            if not vault.exists():
                return f"Vault not found: {vault_path}"
            
            output = f"Files in {vault_path}:\n\n"
            for item in sorted(vault.iterdir())[:20]:
                icon = "📁" if item.is_dir() else "📄"
                output += f"{icon} {item.name}\n"
            
            return output
        except Exception as e:
            return f"Error: {e}"


class OpenCodeServer:
    """Background server manager for opencode."""

    _instance: Optional["OpenCodeServer"] = None

    def __init__(self):
        self.integration = OpenCodeIntegration()
        self._thread: Optional[threading.Thread] = None

    @classmethod
    def get_instance(cls) -> "OpenCodeServer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self) -> bool:
        """Start server in background thread."""
        if self.integration.is_running():
            return True
        
        def _start():
            self.integration.start_server()
        
        self._thread = threading.Thread(target=_start, daemon=True)
        self._thread.start()
        
        for _ in range(20):
            if self.integration.is_running():
                return True
            time.sleep(0.5)
        return False

    def stop(self):
        """Stop the server."""
        self.integration.stop_server()

    def get_integration(self) -> OpenCodeIntegration:
        return self.integration

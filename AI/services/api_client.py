"""VaultMind API Client for desktop application."""
import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VaultMindClient:
    """Client for interacting with VaultMind API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self._client = httpx.Client(timeout=30.0)

    def health_check(self) -> dict:
        """Check if VaultMind API is healthy."""
        try:
            response = self._client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "message": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def is_healthy(self) -> bool:
        """Check if API is reachable."""
        result = self.health_check()
        return result.get("status") == "healthy"

    def get_collections(self) -> list:
        """Get all indexed collections."""
        try:
            response = self._client.get(f"{self.base_url}/api/collections")
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("collections", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            return []

    def get_collection_info(self, collection_name: str) -> Optional[dict]:
        """Get info about a specific collection."""
        try:
            response = self._client.get(
                f"{self.base_url}/api/collections/{collection_name}/info"
            )
            if response.status_code == 200:
                return response.json().get("data")
            return None
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None

    def search(
        self,
        vault_name: str,
        query: str,
        limit: int = 20,
        similarity_threshold: float = 0.0
    ) -> list:
        """Search the vault semantically."""
        try:
            response = self._client.post(
                f"{self.base_url}/api/search",
                json={
                    "vault_name": vault_name,
                    "query": query,
                    "limit": limit,
                    "similarity_threshold": similarity_threshold
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("results", [])
            logger.error(f"Search failed: {response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def index_vault(
        self,
        vault_name: str,
        vault_path: str,
        force_reindex: bool = False
    ) -> Optional[str]:
        """Start indexing a vault. Returns job_id if started."""
        try:
            response = self._client.post(
                f"{self.base_url}/api/index",
                json={
                    "vault_name": vault_name,
                    "vault_path": vault_path,
                    "force_reindex": force_reindex
                }
            )
            if response.status_code in [200, 201]:
                return response.json().get("data", {}).get("job_id")
            return None
        except Exception as e:
            logger.error(f"Failed to start indexing: {e}")
            return None

    def get_index_status(self, job_id: str) -> Optional[dict]:
        """Get status of an indexing job."""
        try:
            response = self._client.get(f"{self.base_url}/api/index/job/{job_id}")
            if response.status_code == 200:
                return response.json().get("data")
            return None
        except Exception as e:
            logger.error(f"Failed to get index status: {e}")
            return None

    def close(self):
        """Close the HTTP client."""
        self._client.close()

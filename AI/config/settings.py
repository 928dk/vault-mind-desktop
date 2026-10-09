"""Configuration management for VaultMind Desktop."""
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

CONFIG_DIR = Path.home() / ".config" / "vault-mind-desktop"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    """Application configuration."""
    theme: str = "system"  # system, light, dark
    api_url: str = "http://127.0.0.1:8000"
    default_vault: str = "obsidian"
    vaults: dict = None
    auto_start: bool = False
    start_minimized: bool = True
    window_width: int = 1000
    window_height: int = 700
    mcp_enabled: bool = False
    mcp_port: int = 9091

    def __post_init__(self):
        if self.vaults is None:
            self.vaults = {
                "obsidian": {
                    "name": "Obsidian",
                    "path": str(Path.home() / "Obsidian"),
                    "enabled": True
                },
                "projects": {
                    "name": "Projects",
                    "path": str(Path.home() / "projects"),
                    "enabled": False
                },
                "sync": {
                    "name": "Sync",
                    "path": str(Path.home() / "Sync" / "vault-git"),
                    "enabled": False
                }
            }

    def save(self):
        """Save configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> "AppConfig":
        """Load configuration from file."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                return cls(**data)
            except Exception:
                pass
        return cls()


# Global config instance
config = AppConfig.load()

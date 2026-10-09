# System Context

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              VaultMind Desktop (CustomTkinter)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  [Tray Icon]   │
│  │ Search   │  │ Browse   │  │ Status   │      ↓        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                │
│       │              │              │                      │
│       └──────────────┴──────────────┘                      │
│                      │                                      │
│              VaultMind API                                  │
│            (localhost:8000)                                 │
│                      │                                      │
│    ┌─────────────────┼─────────────────┐                   │
│    ↓                 ↓                 ↓                   │
│ ChromaDB           Ollama          Obsidian                 │
│ (embeddings)    (qwen2.5:3b)        (files)               │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Desktop App (CustomTkinter)
- **Main Window**: Single window with sidebar navigation
- **System Tray**: Minimize to tray, quick access menu
- **Search View**: Semantic search with results list
- **Browse View**: File tree browser for vaults
- **Status View**: Index status and management
- **Preview Pane**: Note preview without leaving app

### VaultMind API
- FastAPI backend running locally
- ChromaDB for vector storage
- Ollama (qwen2.5:3b) for embeddings

### Vaults
| Vault | Path | Status |
|-------|------|--------|
| Obsidian | ~/Obsidian | Primary |
| Projects | ~/projects | Future |
| Sync | ~/Sync/vault-git | Future |

## File Structure

```
vault-mind-desktop/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── README.md                  # This file
├── ui/
│   ├── main_window.py        # Main window + tray
│   ├── search_view.py        # Search interface
│   ├── vault_browser.py      # File browser
│   ├── preview_pane.py        # Note preview
│   └── status_view.py         # Index status
├── services/
│   └── api_client.py          # API wrapper
├── config/
│   └── settings.py            # Config management
└── docs/
    ├── README.md              # Overview
    ├── system_context.md      # This file
    ├── personality.md         # Design principles
    ├── install.md             # Installation
    ├── version.md             # Changelog
    └── session.md             # Session notes
```

## Dependencies

```
customtkinter==5.6.3    # Modern UI framework
httpx==0.27.2           # HTTP client
pillow>=10.0.0          # Image handling
pystray>=0.19.5         # System tray
```

## Configuration

Stored in: `~/.config/vault-mind-desktop/config.json`

```json
{
    "theme": "system",
    "api_url": "http://127.0.0.1:8000",
    "default_vault": "obsidian",
    "start_minimized": true,
    "vaults": {...}
}
```

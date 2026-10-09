# VaultMind Desktop

A native desktop application for semantic search of your Obsidian vaults and projects, powered by VaultMind and CustomTkinter.

## Features

- **Semantic Search**: Find notes by meaning, not just keywords
- **System Tray**: Minimizes to tray, starts hidden
- **Dark/Light Mode**: Follows system preference
- **File Browser**: Browse vault folders directly
- **Preview Pane**: Quick preview of notes
- **Index Management**: View status and reindex vaults
- **Offline**: Works locally without internet

## Requirements

- Python 3.10+
- VaultMind API running at `http://127.0.0.1:8000`
- X11/Wayland display

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or with system packages (if needed)
pip install --break-system-packages -r requirements.txt
```

## Running

```bash
# Start the application
python main.py

# Start with debug logging
python main.py --dev
```

## Configuration

Configuration is stored in `~/.config/vault-mind-desktop/config.json`:

```json
{
    "theme": "system",
    "api_url": "http://127.0.0.1:8000",
    "default_vault": "obsidian",
    "start_minimized": true,
    "vaults": {
        "obsidian": {
            "name": "Obsidian",
            "path": "~/Obsidian",
            "enabled": true
        },
        "projects": {
            "name": "Projects",
            "path": "~/projects",
            "enabled": false
        },
        "sync": {
            "name": "Sync",
            "path": "~/Sync/vault-git",
            "enabled": false
        }
    }
}
```

## Project Structure

```
vault-mind-desktop/
├── main.py                 # Entry point
├── requirements.txt         # Dependencies
├── ui/
│   ├── main_window.py      # Main window + tray
│   ├── search_view.py      # Search interface
│   ├── vault_browser.py    # File browser
│   ├── preview_pane.py     # Note preview
│   └── status_view.py      # Index status
├── services/
│   └── api_client.py       # VaultMind API client
└── config/
    └── settings.py         # Configuration management
```

## Usage

1. **Launch**: App starts minimized to system tray
2. **Open**: Click tray icon or use "Show" menu item
3. **Search**: Type query and press Enter or click Search
4. **Browse**: Navigate folders in Browse tab
5. **Preview**: Click a result to preview it
6. **Quit**: Right-click tray icon → Quit

## Keyboard Shortcuts

- `Ctrl+F`: Focus search field (when app is focused)

## Troubleshooting

### App won't start
- Ensure VaultMind API is running: `curl http://127.0.0.1:8000/health`
- Check display is available: `echo $DISPLAY`

### No search results
- Reindex the vault: Settings → Reindex Vault
- Check API logs at `vault-mind/backend/`

### Tray icon not showing
- Install pystray: `pip install pystray`
- Some WMs may not support system tray

## License

MIT

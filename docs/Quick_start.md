# Quick Start - vault-mind-desktop

## Overview
Desktop application for semantic search and management of Obsidian vaults.

## Prerequisites
- Python 3.10+
- VaultMind API running (port 8000)
- Obsidian vault indexed

## Quick Start

### 1. Installation
```bash
cd ~/projects/AI/vault-mind-desktop

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure
```bash
# Set vault path in config
# Edit src/config/settings.py or use GUI settings
```

### 3. Run
```bash
# Launch application
python src/main.py

# Or use launcher
~/vaultmind-desktop
```

### 4. System Tray
- App minimizes to system tray
- Right-click menu for options
- Double-click to restore

## Features
- Semantic search via VaultMind API
- Vault browser with folder navigation
- Note preview
- Dark/light theme (follows system)
- Keyboard shortcuts

## Configuration
- Vault path: Configured in settings
- API endpoint: http://localhost:8000

## Troubleshooting
- Check VaultMind API is running
- Verify vault path is correct
- Check index status in app

## Documentation
- [Version](docs/Version.md)
- [System Context](docs/system_context.md)
- [Personality](docs/personality.md)
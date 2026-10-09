# Installation Guide

## Prerequisites

1. **Python 3.10+**
   ```bash
   python --version
   ```

2. **VaultMind API running**
   ```bash
   curl http://127.0.0.1:8000/health
   ```

3. **Display environment** (for GUI)
   ```bash
   echo $DISPLAY
   ```

## Installation

### 1. Clone or Copy Project

```bash
# If using git
cd ~/projects
git clone <repo> vault-mind-desktop

# Or copy existing
cp -r /path/to/vault-mind-desktop ~/vault-mind-desktop
```

### 2. Install Dependencies

```bash
cd ~/vault-mind-desktop
pip install -r requirements.txt
```

If you get permission errors:
```bash
pip install --break-system-packages -r requirements.txt
```

### 3. Install Desktop Entry (Optional)

```bash
# Copy launcher to local bin
cp vaultmind-desktop.sh ~/.local/bin/
chmod +x ~/.local/bin/vaultmind-desktop

# Copy desktop entry
cp VaultMind-Desktop.desktop ~/Desktop/
chmod +x ~/Desktop/VaultMind-Desktop.desktop

# Enable autostart
cp VaultMind-Desktop.desktop ~/.config/autostart/
```

## Configuration

### API URL
Edit `~/.config/vault-mind-desktop/config.json`:
```json
{
    "api_url": "http://127.0.0.1:8000"
}
```

### Vault Paths
```json
{
    "vaults": {
        "obsidian": {
            "path": "/home/YOUR_USER/Obsidian",
            "enabled": true
        }
    }
}
```

### Start Minimized
```json
{
    "start_minimized": true
}
```

## Running

### From Terminal
```bash
cd ~/vault-mind-desktop
python main.py
```

### From Desktop Entry
Double-click `VaultMind-Desktop.desktop` on your desktop.

### From System Tray
The app minimizes to tray. Click the icon to show.

## Troubleshooting

### App Won't Start
1. Check VaultMind API is running:
   ```bash
   curl http://127.0.0.1:8000/health
   ```

2. Check display is available:
   ```bash
   echo $DISPLAY
   ```

3. Check Python and dependencies:
   ```bash
   python --version
   pip list | grep customtkinter
   ```

### No Search Results
1. Reindex the vault via Status tab
2. Check vault path in config
3. Verify notes exist in vault folder

### Tray Icon Missing
- Install pystray: `pip install pystray`
- Some WMs may not support tray

## Uninstallation

```bash
# Remove desktop entry
rm ~/Desktop/VaultMind-Desktop.desktop
rm ~/.config/autostart/vaultmind-desktop.desktop

# Remove launcher
rm ~/.local/bin/vaultmind-desktop

# Remove config
rm -rf ~/.config/vault-mind-desktop

# Remove project
rm -rf ~/vault-mind-desktop
```

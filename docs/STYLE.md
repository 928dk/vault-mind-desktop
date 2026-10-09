# Coding Style - vault-mind-desktop

This project follows the shared Python style guide.

## Shared Reference
See `~/Desktop/SHARED_STYLE.md` for base standards.

## Project-Specific Rules

### Framework
- **UI**: CustomTkinter (CTk)
- **Backend**: httpx for API calls
- **System Tray**: pystray

### Architecture
```
vault-mind-desktop/
├── src/
│   ├── main.py           # Entry point
│   ├── ui/               # UI components
│   ├── services/         # API client, config
│   └── config/           # Settings management
├── docs/                 # Documentation
└── vault-mind-desktop/  # App resources
```

### Key Patterns
```python
# CustomTkinter pattern
import customtkinter as ctk

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VaultMind")
        self.geometry("800x600")
        
    def setup_ui(self):
        # Build UI components
        pass
```

### System Tray
- Use pystray for cross-platform tray
- Handle minimize to tray
- Menu actions for quick access

## References
- `~/Desktop/SHARED_STYLE.md` - Base style guide
- `~/code-comments.md` - Comment best practices
- CustomTkinter Documentation
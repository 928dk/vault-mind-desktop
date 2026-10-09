# Version History

## v0.1.0 (2026-03-22)

### Features
- Semantic search via VaultMind API
- Vault browser with folder navigation
- Note preview pane
- Index status display
- System tray integration
- Start minimized to tray
- Dark/light theme (follows system)
- Keyboard shortcuts
- Search history with persistence
- Right-click context menus
- Desktop entry for launcher
- Autostart configuration

### Components
- `main.py` - Entry point
- `ui/main_window.py` - Main window (288 lines)
- `ui/search_view.py` - Search interface (227 lines)
- `ui/vault_browser.py` - File browser (188 lines)
- `ui/preview_pane.py` - Note preview (90 lines)
- `ui/status_view.py` - Status display (179 lines)
- `services/api_client.py` - API wrapper (92 lines)
- `config/settings.py` - Config management (51 lines)

### Architecture
- CustomTkinter for UI
- System tray via pystray
- API client via httpx
- Search history via JSON file

### Dependencies
- customtkinter==5.6.3
- httpx==0.27.2
- pillow>=10.0.0
- pystray>=0.19.5

### Known Issues
- None reported

### Next Steps (Future Versions)
- [ ] Global hotkey (Ctrl+Space) for quick search
- [ ] Multiple vault indexing
- [ ] Export search results
- [ ] Quick search popup from tray
- [ ] Window positioning memory
- [ ] Themes beyond system
- [ ] Search suggestions/autocomplete

# CHECKPOINT - UI Improvements (v0.2.0)
**Date:** 2026-03-22
**Time:** ~11:00
**Status:** ✅ STABLE

## What's New

### 1. Theme Switcher
- Location: Sidebar (below header)
- Options: System / Light / Dark
- Persists to config file
- Keyboard shortcut: None (dropdown menu)

### 2. Dashboard Tab
- Location: First in sidebar navigation
- Shows: Document count, Collections, Last indexed, API status, Model
- Auto-refreshes every 60 seconds
- Quick action buttons

### 3. Window Resizing
- Windows now resizable
- Size saved to config on resize
- Minimum size: 800x500

### 4. Auto-Refresh
- Dashboard: refreshes every 60 seconds
- Status view: refreshes when shown
- Manual refresh button available

## Files Changed

```
~/vault-mind-desktop/
├── ui/
│   ├── main_window.py        # Added: theme switcher, dashboard, resize
│   ├── dashboard_view.py     # NEW - Dashboard stats view
│   └── status_view.py        # Added: auto-refresh method
└── config/
    └── settings.py          # Already had save()
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+0 | Dashboard |
| Ctrl+1 | Search |
| Ctrl+2 | Browse |
| Ctrl+3 | Status |
| Ctrl+D | Dashboard |
| Ctrl+F | Focus search |
| Ctrl+H | Search history |
| Escape | Hide to tray |
| Ctrl+Q | Quit |

## Previous Fix (Still Valid)

**Tray runs in daemon thread:**
```python
if config.start_minimized:
    app.withdraw()
    if app.tray:
        def run_tray():
            app.tray.run()
        tray_thread = threading.Thread(target=run_tray, daemon=True)
        tray_thread.start()
app.mainloop()
```

## Known Issues

- None reported

## Checkpoints

| Date | Version | Description |
|------|---------|-------------|
| 2026-03-22 | v0.1.0 | Stable baseline |
| 2026-03-22 | v0.2.0 | UI improvements (this) |

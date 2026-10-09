"""Main window with system tray integration."""
import customtkinter as ctk
import sys
import os
import json
from pathlib import Path
import threading

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.search_view import SearchView
from ui.vault_browser import VaultBrowserView
from ui.preview_pane import PreviewPane
from ui.grid_view import GridView
from ui.dashboard_view import DashboardView
from ui.todo_view import TodoView
from ui.obsidian_view import ObsidianView
from ui.starmap_view import StarmapView
from ui.ai_assistant_view import AIAssistantView
from services.api_client import VaultMindClient
from services.obsidian_scanner import ObsidianScanner
from config import config

HISTORY_FILE = Path.home() / ".config" / "vault-mind-desktop" / "search_history.json"


class SearchHistory:
    """Simple search history manager."""

    def __init__(self, max_items: int = 20):
        self.max_items = max_items
        self.history = self._load()

    def _load(self) -> list:
        if HISTORY_FILE.exists():
            try:
                return json.loads(HISTORY_FILE.read_text())
            except:
                pass
        return []

    def _save(self):
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(json.dumps(self.history))

    def add(self, query: str):
        if query.strip() and query not in self.history:
            self.history.insert(0, query)
            self.history = self.history[:self.max_items]
            self._save()

    def get(self) -> list:
        return self.history.copy()

    def clear(self):
        self.history = []
        self._save()


class VaultMindDesktop(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Search history
        self.search_history = SearchHistory()
        self._resize_after_id = None

        # Configure window
        self.title("VaultMind Desktop")
        self.geometry(f"{config.window_width}x{config.window_height}")
        self.minsize(800, 500)

        # Initialize API client
        self.api_client = VaultMindClient(config.api_url)

        # Start MCP server if enabled
        if config.mcp_enabled:
            self._start_mcp_server()

        # Setup UI
        self.setup_ui()
        self.setup_keybindings()

        # Setup system tray
        self.setup_tray()

        # Center window
        self.center_window()

        # Protocol handlers
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

    def _start_mcp_server(self):
        """Start MCP server in background."""
        try:
            from mcp_server import start_mcp_server
            if start_mcp_server(config.mcp_port):
                print(f"MCP Server started on port {config.mcp_port}")
            else:
                print("Failed to start MCP server")
        except Exception as e:
            print(f"MCP server error: {e}")

    def setup_ui(self):
        """Set up the main UI."""
        # Configure grid for resizable window
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left sidebar (resizable)
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Sidebar header
        sidebar_header = ctk.CTkLabel(
            self.sidebar,
            text="🧠 VaultMind",
            font=("SF Pro", 18, "bold")
        )
        sidebar_header.grid(row=0, column=0, padx=20, pady=(15, 10))

        # Theme switcher
        theme_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        theme_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")

        self.theme_label = ctk.CTkLabel(
            theme_frame,
            text="Theme:",
            font=("SF Pro", 12)
        )
        self.theme_label.pack(side="left", padx=(0, 10))

        self.theme_segmented = ctk.CTkSegmentedButton(
            theme_frame,
            values=["System", "Light", "Dark"],
            width=180,
            height=28,
            font=("SF Pro", 10),
            command=self._change_theme,
        )
        self.theme_segmented.pack(side="left")
        
        # Set initial theme from config
        current_theme = config.theme.capitalize()
        if current_theme not in ["System", "Light", "Dark"]:
            current_theme = "System"
        self.theme_segmented.set(current_theme)

        # Navigation buttons
        nav_buttons = [
            ("📝", "Todos", 0),
            ("🌌", "Starmap", 1),
            ("📊", "Dashboard", 2),
            ("🔍", "Search", 3),
            ("📁", "Browse", 4),
            ("🤖", "AI", 5),
            ("🖥️", "Grid", 6),
        ]

        self.nav_buttons = {}
        for icon, label, row in nav_buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}  {label}",
                font=("SF Pro", 14),
                height=45,
                fg_color="transparent",
                hover_color=("gray85", "gray25"),
                anchor="w",
                command=lambda r=row: self.show_view(r)
            )
            btn.grid(row=row + 2, column=0, sticky="ew", padx=10, pady=2)
            self.nav_buttons[row] = btn

        # Active view indicator
        self.nav_buttons[0].configure(fg_color=("gray80", "gray30"))

        # Spacer
        spacer = ctk.CTkLabel(self.sidebar, text="")
        spacer.grid(row=6, column=0, pady=20)

        # Quit button at bottom
        quit_btn = ctk.CTkButton(
            self.sidebar,
            text="Quit",
            font=("SF Pro", 13),
            height=35,
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            anchor="w",
            command=self.quit_app
        )
        quit_btn.grid(row=10, column=0, sticky="s", padx=10, pady=(0, 10))

        # Main content area
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Create views
        self.views = {}

        # Todo view (index 0)
        self.todo_view = TodoView(self.content_frame)
        self.views[0] = self.todo_view

        # Obsidian TODO scanner (index 1) - now Starmap view
        self.obsidian_view = StarmapView(self.content_frame)
        self.views[1] = self.obsidian_view

        # Dashboard view (index 2)
        self.dashboard_view = DashboardView(
            self.content_frame,
            self.api_client
        )
        self.views[2] = self.dashboard_view

        # Search view (index 3)
        self.search_view = SearchView(
            self.content_frame,
            self.api_client,
            on_result_select=self.show_preview,
            on_search=self.search_history.add
        )
        self.views[3] = self.search_view

        # Browse view (index 4)
        self.browse_view = VaultBrowserView(
            self.content_frame,
            config.vaults,
            on_file_select=self.show_file_preview
        )
        self.views[4] = self.browse_view

        # AI Assistant view (index 5)
        self.ai_view = AIAssistantView(self.content_frame)
        self.views[5] = self.ai_view

        # Grid view (index 6)
        self.grid_view = GridView(self.content_frame)
        self.views[6] = self.grid_view

        # Preview pane (shown alongside search/browse)
        self.preview_pane = PreviewPane(self.content_frame)

        # Initialize Obsidian scanner
        self.obsidian_scanner = ObsidianScanner()
        self.obsidian_scanner.add_callback(self._on_obsidian_change)
        
        # Initial scan
        threading.Thread(target=self._run_initial_scan, daemon=True).start()
        
        # Start periodic scanning (every 5 minutes)
        self.obsidian_scanner.start_periodic(300)

        # Show todos by default
        self.show_view(0)

        # Start auto-refresh on dashboard
        self.dashboard_view.start_auto_refresh(60000)

        # Start vault scan on obsidian view
        self.obsidian_view.start_scan()

        # Focus search field
        self.after(100, lambda: self.search_view.search_entry.focus())

    def setup_keybindings(self):
        """Set up keyboard shortcuts."""
        # Ctrl+F - Focus search
        self.bind("<Control-f>", lambda e: self._focus_search())
        self.bind("<Control-F>", lambda e: self._focus_search())

        # Ctrl+T - Go to Todos
        self.bind("<Control-t>", lambda e: self.show_view(0))
        self.bind("<Control-T>", lambda e: self.show_view(0))

        # Ctrl+I - Go to Obsidian TODOs
        self.bind("<Control-i>", lambda e: self.show_view(1))
        self.bind("<Control-I>", lambda e: self.show_view(1))

        # Ctrl+0 - Go to Todos
        self.bind("<Control-0>", lambda e: self.show_view(0))

        # Ctrl+1 - Go to Obsidian
        self.bind("<Control-1>", lambda e: self.show_view(1))

        # Ctrl+2 - Go to Dashboard
        self.bind("<Control-2>", lambda e: self.show_view(2))

        # Ctrl+3 - Go to Search
        self.bind("<Control-3>", lambda e: self.show_view(3))

        # Ctrl+4 - Go to Browse
        self.bind("<Control-4>", lambda e: self.show_view(4))

        # Ctrl+5 - Go to AI Assistant
        self.bind("<Control-5>", lambda e: self.show_view(5))

        # Ctrl+6 - Go to Status
        self.bind("<Control-6>", lambda e: self.show_view(6))

        # Escape - Hide window to tray
        self.bind("<Escape>", lambda e: self.hide_window())

        # Ctrl+H - Show search history
        self.bind("<Control-h>", lambda e: self._show_history())

        # Ctrl+Q - Quit
        self.bind("<Control-q>", lambda e: self.quit_app())

        # Configure resizing
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        """Handle window resize with debounced config save."""
        if self._resize_after_id is not None:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(500, self._save_resize_config)

    def _save_resize_config(self):
        """Save window size to config (debounced)."""
        self._resize_after_id = None
        width = self.winfo_width()
        height = self.winfo_height()
        config.window_width = width
        config.window_height = height

    def _change_theme(self, theme: str):
        """Change the application theme."""
        theme_lower = theme.lower()
        
        if theme_lower == "system":
            ctk.set_appearance_mode("system")
        elif theme_lower == "light":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
        
        # Save to config
        config.theme = theme_lower
        config.save()

    def _run_initial_scan(self):
        """Run initial Obsidian scan in background."""
        try:
            result = self.obsidian_scanner.scan()
            if result.get("added") or result.get("modified"):
                print(f"Initial scan: {result.get('added', 0)} added, {result.get('modified', 0)} modified")
        except Exception as e:
            print(f"Initial scan error: {e}")

    def _on_obsidian_change(self, added: int = 0, modified: int = 0, deleted: int = 0):
        """Callback when Obsidian files change."""
        print(f"Obsidian changes: {added} added, {modified} modified, {deleted} deleted")
        # Could trigger UI update here
        self.after(0, lambda: self.obsidian_view.refresh_files())

    def _focus_search(self):
        """Focus the search entry."""
        self.show_view(3)
        self.search_view.search_entry.focus_set()
        self.search_view.search_entry.delete(0, "end")

    def _show_history(self):
        """Show search history popup."""
        history = self.search_history.get()
        if not history:
            return

        # Simple approach: just populate search with history
        popup = ctk.CTkToplevel(self)
        popup.title("Recent Searches")
        popup.geometry("400x300")
        popup.transient(self)
        popup.grab_set()

        frame = ctk.CTkScrollableFrame(popup)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        for query in history[:10]:
            btn = ctk.CTkButton(
                frame,
                text=query[:50] + ("..." if len(query) > 50 else ""),
                fg_color="transparent",
                hover_color=("gray85", "gray25"),
                anchor="w",
                command=lambda q=query: self._search_from_history(q, popup)
            )
            btn.pack(fill="x", pady=2)

        ctk.CTkButton(
            frame,
            text="Clear History",
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            command=lambda: (self.search_history.clear(), popup.destroy())
        ).pack(fill="x", pady=(10, 0))

    def _search_from_history(self, query: str, popup):
        """Search from history item."""
        popup.destroy()
        self._focus_search()
        self.search_view.set_search(query)

    def setup_tray(self):
        """Setup system tray icon."""
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            print("pystray not installed, tray icon disabled")
            return

        # Create tray icon
        self.tray = None
        self._create_tray_icon()

    def _create_tray_icon(self):
        """Create system tray icon."""
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            return

        # Create a simple icon image
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), 'white')
        dc = ImageDraw.Draw(image)
        dc.ellipse([8, 8, 56, 56], fill='#6366F1')
        dc.text((20, 24), 'V', fill='white')

        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Search", self.show_window),
            pystray.MenuItem("Quit", self.quit_app)
        )

        self.tray = pystray.Icon(
            "vaultmind",
            image,
            "VaultMind Desktop",
            menu
        )

    def show_window(self, icon=None, item=None):
        """Show the main window."""
        self.deiconify()
        self.after(0, self.focus)
        self.lift()

    def hide_window(self):
        """Hide window to tray."""
        self.withdraw()
        if self.tray:
            self.tray.run_detached()

    def show_view(self, view_id: int):
        """Switch to a different view."""
        # Hide all views
        for view in self.views.values():
            view.grid_forget()

        # Reset preview pane
        self.preview_pane.grid_forget()

        # Show selected view
        if view_id in self.views:
            self.views[view_id].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # Update nav buttons
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == view_id:
                btn.configure(fg_color=("gray80", "gray30"))
            else:
                btn.configure(fg_color="transparent")

        # Show preview pane for search and browse views (not todos/obsidian/dashboard)
        if view_id in [3, 4]:
            self.views[view_id].grid(row=0, column=0, sticky="nsew", padx=(0, 1), pady=0)
            self.preview_pane.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
            self.preview_pane.grid_columnconfigure(0, weight=1)

        # Refresh dashboard when shown
        if view_id == 2 and hasattr(self, 'dashboard_view'):
            self.dashboard_view.refresh()

        # Refresh grid when shown
        if view_id == 6 and hasattr(self, 'grid_view'):
            self.grid_view.refresh()

    def show_preview(self, result: dict):
        """Show preview for search result."""
        self.preview_pane.set_content(result)

    def show_file_preview(self, path: Path):
        """Show preview for file."""
        self.preview_pane.set_file(path)

    def handle_reindex(self, callback):
        """Handle reindex request."""
        vault_path = config.vaults.get(config.default_vault, {}).get("path", "")
        if not vault_path:
            callback(False)
            return

        job_id = self.api_client.index_vault(
            config.default_vault,
            vault_path,
            force_reindex=True
        )

        if job_id:
            callback(True)
        else:
            callback(False)

    def center_window(self):
        """Center window on screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def quit_app(self, icon=None, item=None):
        """Quit the application."""
        self.api_client.close()
        if self.tray:
            try:
                self.tray.stop()
            except:
                pass
        if config.mcp_enabled:
            try:
                from mcp_server import stop_mcp_server
                stop_mcp_server()
            except:
                pass
        self.destroy()
        sys.exit(0)


def main():
    """Main entry point."""
    import threading
    
    # Set appearance
    if config.theme == "system":
        ctk.set_appearance_mode("system")
    elif config.theme == "dark":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

    # Create and run app
    app = VaultMindDesktop()

    if config.start_minimized:
        app.withdraw()
        if app.tray:
            # Run tray in a separate thread
            def run_tray():
                app.tray.run()
            tray_thread = threading.Thread(target=run_tray, daemon=True)
            tray_thread.start()
    
    # Always run mainloop to handle window events
    app.mainloop()


if __name__ == "__main__":
    main()

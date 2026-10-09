"""Search view component."""
import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional
import threading
import time

from services.api_client import VaultMindClient
from config import config


class SearchView(ctk.CTkFrame):
    """Search interface for VaultMind Desktop."""

    def __init__(
        self,
        parent,
        api_client: VaultMindClient,
        on_result_select: Optional[Callable] = None,
        on_open_file: Optional[Callable] = None,
        on_search: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.api_client = api_client
        self.on_result_select = on_result_select
        self.on_open_file = on_open_file
        self.on_search = on_search
        self.results = []
        self.current_query = ""
        self.setup_ui()

    def setup_ui(self):
        """Set up the search interface."""
        # Search bar
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Search your vault...",
            font=("SF Pro", 16),
            height=45,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.do_search())

        self.search_btn = ctk.CTkButton(
            self.search_frame,
            text="Search",
            width=100,
            height=45,
            command=self.do_search,
        )
        self.search_btn.pack(side="right")

        # Status bar
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=("SF Pro", 12),
            text_color=("gray50", "gray60")
        )
        self.status_label.pack(anchor="w", padx=15, pady=(0, 5))

        # Results area with scrollbar
        self.results_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.results_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.results_container,
            text="Start typing to search your vault",
            font=("SF Pro", 14),
            text_color=("gray50", "gray60")
        )
        self.empty_label.pack(pady=50)

    def do_search(self):
        """Perform search."""
        query = self.search_entry.get().strip()
        if not query:
            return

        self.current_query = query
        self.status_label.configure(text="Searching...")
        self.search_btn.configure(state="disabled")

        # Run search in background thread
        thread = threading.Thread(target=self._search_thread, args=(query,))
        thread.daemon = True
        thread.start()

    def _search_thread(self, query: str):
        """Search in background thread."""
        try:
            self.results = self.api_client.search(config.default_vault, query, limit=20)
            self.after(0, self._display_results, query)
        except Exception as e:
            self.after(0, self._show_error, str(e))

    def _display_results(self, query: str):
        """Display search results in UI thread."""
        self.search_btn.configure(state="normal")

        if not self.results:
            self.status_label.configure(text=f"No results for '{query}'")
            self._show_empty_state("No results found")
            return

        self.status_label.configure(
            text=f"Found {len(self.results)} results for '{query}'"
        )
        self._show_results()

        # Save to history
        if self.on_search:
            self.on_search(query)

    def _show_error(self, error: str):
        """Show error message."""
        self.search_btn.configure(state="normal")
        self.status_label.configure(text=f"Error: {error}")
        self._show_empty_state(f"Search failed: {error}")

    def _show_empty_state(self, message: str):
        """Show empty state message."""
        for widget in self.results_container.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.results_container,
            text=message,
            font=("SF Pro", 14),
            text_color=("gray50", "gray60")
        ).pack(pady=50)

    def _show_results(self):
        """Display results list."""
        for widget in self.results_container.winfo_children():
            widget.destroy()

        for i, result in enumerate(self.results):
            self._create_result_card(i, result)

    def _create_result_card(self, index: int, result: dict):
        """Create a single result card."""
        card = ctk.CTkFrame(self.results_container, corner_radius=8)
        card.pack(fill="x", pady=(0, 8), padx=2)

        content = result.get("content", "")[:300]
        filepath = result.get("metadata", {}).get("file_path", "Unknown")
        similarity = result.get("similarity_score", 0)
        score_pct = max(0, min(100, int((1 - similarity) * 100)))
        filename = filepath.split("/")[-1] if filepath else "Unknown"

        # Header with filename and score
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(12, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text=filename,
            font=("SF Pro", 14, "bold"),
            anchor="w"
        )
        title_label.pack(side="left")

        score_label = ctk.CTkLabel(
            header_frame,
            text=f"{score_pct}%",
            font=("SF Pro", 12),
            text_color=("green" if score_pct > 70 else "orange" if score_pct > 50 else "gray"),
            width=50
        )
        score_label.pack(side="right")

        # Path (smaller)
        path_label = ctk.CTkLabel(
            card,
            text=filepath,
            font=("SF Pro", 10),
            text_color=("gray40", "gray60"),
            anchor="w"
        )
        path_label.pack(fill="x", padx=15, pady=(0, 8))

        # Content preview
        content_label = ctk.CTkLabel(
            card,
            text=content + "...",
            font=("SF Pro", 12),
            text_color=("gray20", "gray80"),
            anchor="w",
            justify="left",
            wraplength=700
        )
        content_label.pack(fill="x", padx=15, pady=(0, 12))

        # Make card clickable
        card.bind("<Button-1>", lambda e, r=result: self._on_result_click(r))
        card.bind("<Button-3>", lambda e, r=result: self._show_context_menu(e, r))
        title_label.bind("<Button-1>", lambda e, r=result: self._on_result_click(r))
        content_label.bind("<Button-1>", lambda e, r=result: self._on_result_click(r))

    def _on_result_click(self, result: dict):
        """Handle result click."""
        if self.on_result_select:
            self.on_result_select(result)

    def set_search(self, query: str):
        """Set search query programmatically."""
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, query)
        self.do_search()

    def _show_context_menu(self, event, result: dict):
        """Show right-click context menu."""
        menu = tk.Menu(self, tearoff=0)

        filepath = result.get("metadata", {}).get("file_path", "")
        content = result.get("content", "")

        menu.add_command(label="Open", command=lambda: self._open_file(filepath))
        menu.add_command(label="Copy Path", command=lambda: self._copy_to_clipboard(filepath))
        menu.add_command(label="Copy Content", command=lambda: self._copy_to_clipboard(content[:500]))
        menu.add_separator()
        menu.add_command(label="Preview", command=lambda: self._on_result_click(result))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _open_file(self, filepath: str):
        """Open file in default application."""
        import webbrowser
        if filepath:
            webbrowser.open(f"file://{filepath}")

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(text)

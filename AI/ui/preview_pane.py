"""Preview pane for showing note content."""
import customtkinter as ctk
import webbrowser
from pathlib import Path
from typing import Optional


class PreviewPane(ctk.CTkFrame):
    """Preview pane for notes and files."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_file = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the preview interface."""
        # Header
        self.header = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.header.pack(fill="x", pady=(0, 1))
        self.header.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.header,
            text="Preview",
            font=("SF Pro", 14, "bold")
        )
        self.title_label.pack(side="left", padx=15, pady=8)

        self.open_btn = ctk.CTkButton(
            self.header,
            text="Open",
            width=60,
            height=28,
            font=("SF Pro", 12),
            command=self._open_external
        )
        self.open_btn.pack(side="right", padx=10)
        self.open_btn.pack_forget()

        # Content area with scrollbar
        self.content_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=("gray95", "gray15")
        )
        self.content_scroll.pack(fill="both", expand=True)

        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.content_scroll,
            text="Select a note to preview",
            font=("SF Pro", 14),
            text_color=("gray50", "gray60")
        )
        self.empty_label.pack(pady=50)

        self.content_label = None

    def set_content(self, result: dict):
        """Set content to preview from search result."""
        self.current_file = result

        content = result.get("content", "")
        filepath = result.get("metadata", {}).get("file_path", "")

        self.title_label.configure(text=filepath.split("/")[-1] if filepath else "Preview")
        self.open_btn.pack(side="right", padx=10)

        # Clear previous content
        if self.content_label:
            self.content_label.destroy()

        self.empty_label.pack_forget()

        # Create content label with markdown-friendly display
        self.content_label = ctk.CTkLabel(
            self.content_scroll,
            text=self._format_content(content),
            font=("SF Pro", 13),
            anchor="nw",
            justify="left",
            wraplength=500
        )
        self.content_label.pack(fill="both", expand=True, padx=15, pady=15)

    def set_file(self, path: Path):
        """Set content to preview from file path."""
        self.current_file = {"metadata": {"file_path": str(path)}}

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()[:5000]  # Limit preview
        except:
            content = "[Cannot read file]"

        self.title_label.configure(text=path.name)
        self.open_btn.pack(side="right", padx=10)
        self.empty_label.pack_forget()

        if self.content_label:
            self.content_label.destroy()

        self.content_label = ctk.CTkLabel(
            self.content_scroll,
            text=self._format_content(content),
            font=("SF Mono", 12),
            anchor="nw",
            justify="left",
            wraplength=500
        )
        self.content_label.pack(fill="both", expand=True, padx=15, pady=15)

    def _format_content(self, content: str) -> str:
        """Format content for display."""
        if not content:
            return ""
        # Simple formatting: trim and limit
        lines = content.split("\n")[:100]
        return "\n".join(lines)

    def _open_external(self):
        """Open file in external application."""
        if not self.current_file:
            return

        filepath = self.current_file.get("metadata", {}).get("file_path")
        if filepath:
            webbrowser.open(f"file://{filepath}")

    def clear(self):
        """Clear the preview."""
        self.current_file = None
        self.title_label.configure(text="Preview")
        self.open_btn.pack_forget()

        if self.content_label:
            self.content_label.destroy()
            self.content_label = None

        self.empty_label.pack(pady=50)

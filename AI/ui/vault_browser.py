"""Vault browser view component."""
import customtkinter as ctk
import os
import webbrowser
from pathlib import Path
from typing import Optional, Callable
import threading


class VaultBrowserView(ctk.CTkFrame):
    """File browser for vault directories."""

    def __init__(
        self,
        parent,
        vault_paths: dict,
        on_file_select: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.vault_paths = vault_paths
        self.on_file_select = on_file_select
        self.current_path = None
        self.folders = []
        self.files = []
        self.setup_ui()

    def setup_ui(self):
        """Set up the browser interface."""
        # Left panel - folder tree
        self.left_panel = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.left_panel.pack(side="left", fill="y", padx=(0, 1))

        self.folder_label = ctk.CTkLabel(
            self.left_panel,
            text="Folders",
            font=("SF Pro", 14, "bold"),
            anchor="w"
        )
        self.folder_label.pack(anchor="w", padx=15, pady=(15, 10))

        self.folder_scroll = ctk.CTkScrollableFrame(
            self.left_panel,
            fg_color="transparent"
        )
        self.folder_scroll.pack(fill="both", expand=True, padx=5)

        # Right panel - file list and preview
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.pack(side="left", fill="both", expand=True)

        # File list header
        self.file_header = ctk.CTkLabel(
            self.right_panel,
            text="Files",
            font=("SF Pro", 14, "bold"),
            anchor="w"
        )
        self.file_header.pack(anchor="w", padx=15, pady=(15, 10))

        # File list
        self.file_scroll = ctk.CTkScrollableFrame(
            self.right_panel,
            fg_color="transparent"
        )
        self.file_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Load vault folders
        self._load_vaults()

    def _load_vaults(self):
        """Load vault folders into tree."""
        for widget in self.folder_scroll.winfo_children():
            widget.destroy()

        for vault_id, vault_info in self.vaults_paths.items():
            if not vault_info.get("enabled", False):
                continue

            vault_name = vault_info["name"]
            vault_path = Path(vault_info["path"])

            if not vault_path.exists():
                continue

            # Vault header
            vault_btn = ctk.CTkButton(
                self.folder_scroll,
                text=f"📁 {vault_name}",
                font=("SF Pro", 13, "bold"),
                fg_color="transparent",
                hover_color=("gray85", "gray25"),
                anchor="w",
                height=35,
                command=lambda p=vault_path, n=vault_name: self._browse_folder(p, n)
            )
            vault_btn.pack(fill="x", pady=(5, 0), padx=5)

    @property
    def vaults_paths(self) -> dict:
        """Get vault paths dict."""
        return self.vault_paths

    def _browse_folder(self, path: Path, name: str = ""):
        """Browse a folder."""
        self.current_path = path
        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            self._display_files(entries)
            if name:
                self.file_header.configure(text=f"📁 {name}/{path.name}")
            else:
                self.file_header.configure(text=f"📁 {path.name}")
        except PermissionError:
            self._show_error("Permission denied")

    def _display_files(self, entries: list):
        """Display file list."""
        for widget in self.file_scroll.winfo_children():
            widget.destroy()

        folders = [e for e in entries if e.is_dir() and not e.name.startswith(".")]
        files = [e for e in entries if e.is_file() and not e.name.startswith(".")]

        # Show parent folder if not at root
        if self.current_path and self.current_path.parent != self.current_path:
            parent_card = ctk.CTkFrame(self.file_scroll, corner_radius=8)
            parent_card.pack(fill="x", pady=(0, 5), padx=2)
            parent_btn = ctk.CTkButton(
                parent_card,
                text="📁 ..",
                font=("SF Pro", 13),
                fg_color="transparent",
                hover_color=("gray85", "gray25"),
                anchor="w",
                height=40,
                command=lambda: self._browse_folder(self.current_path.parent)
            )
            parent_btn.pack(fill="x", padx=10, pady=5)

        # Show folders
        for folder in folders[:50]:  # Limit to 50
            self._create_file_card(folder, is_folder=True)

        # Show files
        for file in files[:100]:  # Limit to 100
            self._create_file_card(file, is_folder=False)

        if not folders and not files:
            ctk.CTkLabel(
                self.file_scroll,
                text="Empty folder",
                font=("SF Pro", 12),
                text_color=("gray50", "gray60")
            ).pack(pady=20)

    def _create_file_card(self, path: Path, is_folder: bool):
        """Create a file/folder card."""
        card = ctk.CTkFrame(self.file_scroll, corner_radius=8)
        card.pack(fill="x", pady=(0, 5), padx=2)

        icon = "📁" if is_folder else "📄"
        if not is_folder:
            ext = path.suffix.lower()
            if ext in [".md", ".txt", ".markdown"]:
                icon = "📝"
            elif ext in [".py", ".js", ".ts", ".sh"]:
                icon = "💻"
            elif ext in [".jpg", ".png", ".gif", ".svg"]:
                icon = "🖼️"
            elif ext in [".pdf"]:
                icon = "📕"
            elif ext in [".json", ".yaml", ".yml", ".toml"]:
                icon = "⚙️"

        size_text = ""
        if not is_folder:
            try:
                size = path.stat().st_size
                if size < 1024:
                    size_text = f"{size} B"
                elif size < 1024 * 1024:
                    size_text = f"{size // 1024} KB"
                else:
                    size_text = f"{size // (1024*1024)} MB"
            except:
                pass

        content = ctk.CTkButton(
            card,
            text=f"{icon} {path.name}  {size_text}",
            font=("SF Pro", 13),
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            anchor="w",
            height=40,
            command=lambda p=path: (
                self._browse_folder(p) if is_folder else self._open_file(p)
            )
        )
        content.pack(fill="x", padx=10, pady=5)

    def _open_file(self, path: Path):
        """Open file in default application."""
        try:
            webbrowser.open(f"file://{path}")
            if self.on_file_select:
                self.on_file_select(path)
        except Exception as e:
            self._show_error(f"Could not open file: {e}")

    def _show_error(self, message: str):
        """Show error message."""
        for widget in self.file_scroll.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.file_scroll,
            text=f"⚠️ {message}",
            font=("SF Pro", 12),
            text_color="red"
        ).pack(pady=20)

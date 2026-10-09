"""Todo view for VaultMind Desktop."""
import customtkinter as ctk
from typing import Callable, Optional
import json
from pathlib import Path
from datetime import datetime

TODO_FILE = Path.home() / ".config" / "vault-mind-desktop" / "todos.json"


class TodoList:
    """Standalone todo list manager (used by MCP server and opencode integration)."""

    @staticmethod
    def load() -> list:
        """Load todos from file."""
        if TODO_FILE.exists():
            try:
                return json.loads(TODO_FILE.read_text())
            except Exception:
                pass
        return []

    @staticmethod
    def save(todos: list):
        """Save todos to file."""
        TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
        TODO_FILE.write_text(json.dumps(todos, indent=2))


class TodoView(ctk.CTkFrame):
    """Todo list management view."""

    def __init__(
        self,
        parent,
        on_open_note: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.on_open_note = on_open_note
        self.todos = self._load_todos()
        self.setup_ui()
        self.refresh()

    def _load_todos(self) -> list:
        """Load todos from file."""
        if TODO_FILE.exists():
            try:
                return json.loads(TODO_FILE.read_text())
            except:
                pass
        return []

    def _save_todos(self):
        """Save todos to file."""
        TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
        TODO_FILE.write_text(json.dumps(self.todos, indent=2))

    def setup_ui(self):
        """Set up the todo interface."""
        # Title and add button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="📝 Todos",
            font=("SF Pro", 24, "bold")
        )
        title.pack(side="left")

        add_btn = ctk.CTkButton(
            header_frame,
            text="+ Add",
            width=80,
            height=35,
            font=("SF Pro", 13),
            command=self._show_add_dialog
        )
        add_btn.pack(side="right")

        # Stats
        self.stats_label = ctk.CTkLabel(
            self,
            text="0/0 completed",
            font=("SF Pro", 12),
            text_color=("gray50", "gray60")
        )
        self.stats_label.pack(anchor="w", padx=25, pady=(0, 10))

        # Todo list container
        self.todo_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.todo_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def refresh(self):
        """Refresh todo list."""
        # Clear existing
        for widget in self.todo_container.winfo_children():
            widget.destroy()

        # Update stats
        total = len(self.todos)
        completed = len([t for t in self.todos if t.get("done", False)])
        self.stats_label.configure(text=f"{completed}/{total} completed")

        if total == 0:
            empty_label = ctk.CTkLabel(
                self.todo_container,
                text="No todos yet. Click '+ Add' to create one.",
                font=("SF Pro", 14),
                text_color=("gray50", "gray60")
            )
            empty_label.pack(pady=50)
            return

        # Show todos
        for i, todo in enumerate(self.todos):
            self._create_todo_card(i, todo)

    def _create_todo_card(self, index: int, todo: dict):
        """Create a todo card."""
        card = ctk.CTkFrame(self.todo_container, corner_radius=10)
        card.pack(fill="x", pady=(0, 8), padx=2)

        # Checkbox
        var = ctk.BooleanVar(value=todo.get("done", False))
        checkbox = ctk.CTkCheckBox(
            card,
            text="",
            variable=var,
            width=30,
            command=lambda i=index, v=var: self._toggle_todo(i, v)
        )
        checkbox.pack(side="left", padx=(12, 8), pady=12)

        # Content
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, pady=10)

        title_text = todo.get("title", "")
        done = todo.get("done", False)

        title_label = ctk.CTkLabel(
            content_frame,
            text=title_text,
            font=("SF Pro", 14, "bold" if not done else ""),
            anchor="w"
        )
        if done:
            title_label.configure(text_color=("gray50", "gray60"))
        title_label.pack(anchor="w")

        if todo.get("note"):
            note_label = ctk.CTkLabel(
                content_frame,
                text=todo["note"][:100] + ("..." if len(todo.get("note", "")) > 100 else ""),
                font=("SF Pro", 11),
                text_color=("gray50", "gray60"),
                anchor="w"
            )
            note_label.pack(anchor="w", pady=(2, 0))

        # Date
        if todo.get("created"):
            date_label = ctk.CTkLabel(
                content_frame,
                text=todo["created"][:10],
                font=("SF Pro", 10),
                text_color=("gray40", "gray70"),
                anchor="w"
            )
            date_label.pack(anchor="w", pady=(4, 0))

        # Delete button
        delete_btn = ctk.CTkButton(
            card,
            text="🗑️",
            width=40,
            height=30,
            fg_color="transparent",
            hover_color=("red", "darkred"),
            command=lambda i=index: self._delete_todo(i)
        )
        delete_btn.pack(side="right", padx=(8, 12), pady=10)

    def _toggle_todo(self, index: int, var: ctk.BooleanVar):
        """Toggle todo done state."""
        if 0 <= index < len(self.todos):
            self.todos[index]["done"] = var.get()
            self._save_todos()
            self.refresh()

    def _delete_todo(self, index: int):
        """Delete a todo."""
        if 0 <= index < len(self.todos):
            del self.todos[index]
            self._save_todos()
            self.refresh()

    def _show_add_dialog(self):
        """Show add todo dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Todo")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        # Title input
        title_label = ctk.CTkLabel(dialog, text="Title:", font=("SF Pro", 12))
        title_label.pack(anchor="w", padx=20, pady=(20, 5))
        title_entry = ctk.CTkEntry(dialog, width=360, font=("SF Pro", 14))
        title_entry.pack(padx=20, pady=(0, 15))

        # Note input
        note_label = ctk.CTkLabel(dialog, text="Note (optional):", font=("SF Pro", 12))
        note_label.pack(anchor="w", padx=20, pady=(0, 5))
        note_entry = ctk.CTkTextbox(dialog, width=360, height=100, font=("SF Pro", 12))
        note_entry.pack(padx=20, pady=(0, 15))

        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 10))

        def add_todo():
            title = title_entry.get().strip()
            if title:
                self.todos.insert(0, {
                    "title": title,
                    "note": note_entry.get("1.0", "end").strip(),
                    "done": False,
                    "created": datetime.now().isoformat()
                })
                self._save_todos()
                dialog.destroy()
                self.refresh()

        ctk.CTkButton(
            btn_frame,
            text="Add",
            width=100,
            command=add_todo
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            fg_color="transparent",
            command=dialog.destroy
        ).pack(side="right", padx=(0, 10))

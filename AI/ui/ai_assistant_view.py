"""AI Assistant view with OpenCode integration."""
import customtkinter as ctk
import threading
import time
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.opencode_integration import OpenCodeServer


class AIAssistantView(ctk.CTkFrame):
    """AI Assistant tab using OpenCode."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.server = OpenCodeServer.get_instance()
        self.current_input = ""
        self.setup_ui()
        self.check_server_status()

    def setup_ui(self):
        """Set up the UI."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray20"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="AI Assistant",
            font=("SF Pro", 16, "bold")
        )
        title.grid(row=0, column=0, padx=15, pady=10)

        self.status_label = ctk.CTkLabel(
            header,
            text="Connecting...",
            font=("SF Pro", 11),
            text_color=("gray40", "gray60")
        )
        self.status_label.grid(row=0, column=1, padx=15, pady=10)

        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.welcome_card = ctk.CTkFrame(self.content_frame)
        self.welcome_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.welcome_card.grid_columnconfigure(0, weight=1)

        welcome = ctk.CTkLabel(
            self.welcome_card,
            text="🤖 AI Assistant powered by OpenCode",
            font=("SF Pro", 14, "bold"),
            anchor="w"
        )
        welcome.grid(row=0, column=0, padx=15, pady=(15, 5))

        desc = ctk.CTkLabel(
            self.welcome_card,
            text="This tab integrates OpenCode AI for advanced coding assistance.\n"
                 "You can search your vault, manage todos, and get help with code.",
            font=("SF Pro", 12),
            text_color=("gray40", "gray60"),
            anchor="w",
            justify="left"
        )
        desc.grid(row=1, column=0, padx=15, pady=(0, 15))

        self.input_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray20"))
        self.input_frame.grid(row=2, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkTextbox(
            self.input_frame,
            height=80,
            font=("SF Mono", 12),
            border_width=0
        )
        self.input_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.input_entry.insert("1.0", "Ask me anything about your vault...")

        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Send",
            width=80,
            height=36,
            command=self.send_prompt
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.input_entry.bind("<Control-Return>", lambda e: self.send_prompt())

    def check_server_status(self):
        """Check if OpenCode server is running."""
        if self.server.start():
            self.status_label.configure(text="🟢 Connected", text_color=("green", "#4ade80"))
        else:
            self.status_label.configure(text="🔴 Disconnected", text_color=("red", "#f87171"))

        self.after(5000, self.check_server_status)

    def send_prompt(self):
        """Send prompt to OpenCode."""
        prompt = self.input_entry.get("1.0", "end").strip()
        if not prompt or prompt == "Ask me anything about your vault...":
            return

        self.input_entry.delete("1.0", "end")
        self.add_message("user", prompt)
        self.add_message("assistant", "Thinking...", is_loading=True)

        thread = threading.Thread(target=self._run_prompt, args=(prompt,))
        thread.daemon = True
        thread.start()

    def _run_prompt(self, prompt: str):
        """Run prompt in background."""
        integration = self.server.get_integration()
        result = integration.run_prompt(prompt)
        
        if "error" in result:
            response = f"Error: {result['error']}"
        else:
            response = result.get("output", "No response")
        
        self.after(0, self._show_response, response)

    def _show_response(self, response: str):
        """Show response in UI."""
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and hasattr(widget, '_is_loading'):
                if widget._is_loading:
                    widget.destroy()
                    break
        self.add_message("assistant", response)

    def add_message(self, role: str, content: str, is_loading: bool = False):
        """Add a message to the chat."""
        msg_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        msg_frame._is_loading = is_loading
        
        if role == "user":
            msg_frame.configure(fg_color=("gray85", "gray30"))
            icon = "👤"
        else:
            msg_frame.configure(fg_color=("gray80", "gray25"))
            icon = "🤖"

        row = len(self.content_frame.winfo_children())
        msg_frame.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        msg_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            msg_frame,
            text=f"{icon} {role.capitalize()}",
            font=("SF Pro", 11, "bold"),
            anchor="w"
        )
        header.grid(row=0, column=0, padx=12, pady=(10, 5), sticky="ew")

        msg = ctk.CTkLabel(
            msg_frame,
            text=content,
            font=("SF Pro", 12),
            anchor="w",
            justify="left",
            wraplength=600
        )
        msg.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.content_frame.after(100, lambda: self.content_frame._parent_scrollbar.set(
            1.0, 1.0
        ))

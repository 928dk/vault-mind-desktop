"""Status view for showing vault/index information."""
import customtkinter as ctk
from typing import Optional
import threading

from services.api_client import VaultMindClient


class StatusView(ctk.CTkFrame):
    """Status and index management view."""

    def __init__(
        self,
        parent,
        api_client: VaultMindClient,
        on_reindex: Optional[callable] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.api_client = api_client
        self.on_reindex = on_reindex
        self.setup_ui()
        # Schedule refresh after main loop starts

    def setup_ui(self):
        """Set up the status interface."""
        # Title
        title = ctk.CTkLabel(
            self,
            text="Vault Status",
            font=("SF Pro", 18, "bold")
        )
        title.pack(anchor="w", padx=20, pady=(20, 15))

        # API Status Card
        self.api_card = self._create_status_card(
            "API Status",
            "Checking...",
            "●"
        )
        self.api_card.pack(fill="x", padx=15, pady=(0, 10))

        # Collection Card
        self.collection_card = self._create_status_card(
            "Indexed Collections",
            "Loading...",
            "●"
        )
        self.collection_card.pack(fill="x", padx=15, pady=(0, 10))

        # Document count
        self.doc_card = self._create_status_card(
            "Documents",
            "0",
            "📄"
        )
        self.doc_card.pack(fill="x", padx=15, pady=(0, 10))

        # Last indexed
        self.last_indexed_card = self._create_status_card(
            "Last Indexed",
            "Unknown",
            "🕐"
        )
        self.last_indexed_card.pack(fill="x", padx=15, pady=(0, 20))

        # Reindex button
        self.reindex_btn = ctk.CTkButton(
            self,
            text="Reindex Vault",
            height=40,
            font=("SF Pro", 14),
            command=self._trigger_reindex
        )
        self.reindex_btn.pack(fill="x", padx=15, pady=(10, 5))

        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            self,
            text="Refresh",
            height=35,
            font=("SF Pro", 13),
            fg_color="transparent",
            command=self.refresh
        )
        self.refresh_btn.pack(fill="x", padx=15, pady=(0, 10))

    def _create_status_card(self, title: str, value: str, icon: str) -> ctk.CTkFrame:
        """Create a status card."""
        card = ctk.CTkFrame(self, corner_radius=10)
        card.pack(fill="x", pady=0)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)

        icon_label = ctk.CTkLabel(
            inner,
            text=icon,
            font=("SF Pro", 20),
            width=30
        )
        icon_label.pack(side="left", padx=(0, 10))

        text_frame = ctk.CTkFrame(inner, fg_color="transparent")
        text_frame.pack(side="left")

        title_label = ctk.CTkLabel(
            text_frame,
            text=title,
            font=("SF Pro", 12),
            text_color=("gray50", "gray60")
        )
        title_label.pack(anchor="w")

        value_label = ctk.CTkLabel(
            text_frame,
            text=value,
            font=("SF Pro", 14, "bold")
        )
        value_label.pack(anchor="w")

        # Store reference
        card.value_label = value_label
        card.icon_label = icon_label

        return card

    def refresh(self):
        """Refresh status from API."""
        self._update_api_status()
        thread = threading.Thread(target=self._fetch_collection_info)
        thread.daemon = True
        thread.start()

    def start_auto_refresh(self, interval_ms: int = 60000):
        """Start auto-refresh timer."""
        def auto_refresh():
            self.refresh()
            self.after(interval_ms, auto_refresh)
        self.after(interval_ms, auto_refresh)

    def _update_api_status(self):
        """Update API connection status."""
        health = self.api_client.health_check()
        is_healthy = health.get("data", {}).get("service_status") == "healthy"

        if is_healthy:
            self.api_card.value_label.configure(text="Connected")
            self.api_card.icon_label.configure(text="✓")
        else:
            self.api_card.value_label.configure(text="Disconnected")
            self.api_card.icon_label.configure(text="✗")

    def _fetch_collection_info(self):
        """Fetch collection info in background."""
        collections = self.api_client.get_collections()
        self.after(0, self._update_collection_display, collections)

    def _update_collection_display(self, collections: list):
        """Update collection display."""
        if collections:
            col = collections[0]
            count = col.get("document_count", 0)
            last_indexed = col.get("last_indexed_at", "Unknown")

            self.collection_card.value_label.configure(text=f"{len(collections)} collection(s)")
            self.doc_card.value_label.configure(text=f"{count:,}")
            self.last_indexed_card.value_label.configure(text=last_indexed)
        else:
            self.collection_card.value_label.configure(text="No collections")
            self.doc_card.value_label.configure(text="0")
            self.last_indexed_card.value_label.configure(text="Never")

    def _trigger_reindex(self):
        """Trigger vault reindexing."""
        if self.on_reindex:
            self.reindex_btn.configure(state="disabled", text="Indexing...")
            self.on_reindex(self._on_reindex_complete)

    def _on_reindex_complete(self, success: bool):
        """Callback when reindex completes."""
        self.after(0, lambda: self.reindex_btn.configure(
            state="normal",
            text="Reindex Vault"
        ))
        if success:
            self.after(1000, self.refresh)

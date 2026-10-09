"""Dashboard view for VaultMind Desktop - improved layout."""
import customtkinter as ctk
from typing import Optional
import threading

from services.api_client import VaultMindClient


class DashboardView(ctk.CTkFrame):
    """Dashboard showing vault overview and stats with improved layout."""

    def __init__(
        self,
        parent,
        api_client: VaultMindClient,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.api_client = api_client
        self.health_data = None
        self.collections_data = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the dashboard interface."""
        # Main container with scroll
        main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header
        header = ctk.CTkFrame(main_container, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))
        
        title = ctk.CTkLabel(
            header,
            text="📊 VaultMind Dashboard",
            font=("SF Pro", 28, "bold")
        )
        title.pack(side="left")
        
        self.refresh_btn = ctk.CTkButton(
            header,
            text="🔄",
            width=40,
            height=40,
            corner_radius=20,
            command=self.refresh
        )
        self.refresh_btn.pack(side="right")
        
        # Status banner
        self.status_banner = ctk.CTkFrame(main_container, corner_radius=12)
        self.status_banner.pack(fill="x", padx=25, pady=(0, 20), ipady=10)
        
        self.status_icon = ctk.CTkLabel(
            self.status_banner,
            text="⏳",
            font=("SF Pro", 24)
        )
        self.status_icon.pack(side="left", padx=(20, 10))
        
        self.status_text = ctk.CTkLabel(
            self.status_banner,
            text="Loading vault status...",
            font=("SF Pro", 14)
        )
        self.status_text.pack(side="left", padx=(10, 0))
        
        # Quick stats grid - 2x2
        stats_grid = ctk.CTkFrame(main_container, fg_color="transparent")
        stats_grid.pack(fill="x", padx=25, pady=(0, 20))
        
        # Row 1
        row1 = ctk.CTkFrame(stats_grid, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 15))
        
        self.doc_card = self._create_card(
            row1,
            "📄", "Documents", "—",
            "#2E7D32", "#4CAF50"
        )
        
        self.col_card = self._create_card(
            row1,
            "📚", "Collections", "—",
            "#1565C0", "#2196F3"
        )
        
        # Row 2
        row2 = ctk.CTkFrame(stats_grid, fg_color="transparent")
        row2.pack(fill="x")
        
        self.api_card = self._create_card(
            row2,
            "🔗", "API Status", "—",
            "#6A1B9A", "#9C27B0"
        )
        
        self.model_card = self._create_card(
            row2,
            "🤖", "Embedding Model", "—",
            "#00838F", "#00BCD4"
        )
        
        # Detailed metrics section
        metrics_frame = ctk.CTkFrame(main_container, corner_radius=15)
        metrics_frame.pack(fill="x", padx=25, pady=(0, 20), ipady=15)
        
        metrics_title = ctk.CTkLabel(
            metrics_frame,
            text="📈 System Metrics",
            font=("SF Pro", 18, "bold")
        )
        metrics_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Metrics grid
        metrics_grid = ctk.CTkFrame(metrics_frame, fg_color="transparent")
        metrics_grid.pack(fill="x", padx=20, pady=(0, 15))
        
        self.uptime_label = self._create_metric_row(metrics_grid, "Uptime", row=0)
        self.memory_label = self._create_metric_row(metrics_grid, "Memory", row=1)
        self.cpu_label = self._create_metric_row(metrics_grid, "CPU", row=2)
        self.embedding_label = self._create_metric_row(metrics_grid, "Embeddings", row=3)
        self.cache_label = self._create_metric_row(metrics_grid, "Cache", row=4)
        
        # Recent activity section
        activity_frame = ctk.CTkFrame(main_container, corner_radius=15)
        activity_frame.pack(fill="x", padx=25, pady=(0, 20), ipady=15)
        
        activity_title = ctk.CTkLabel(
            activity_frame,
            text="💡 Quick Actions",
            font=("SF Pro", 18, "bold")
        )
        activity_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Action buttons
        actions_grid = ctk.CTkFrame(activity_frame, fg_color="transparent")
        actions_grid.pack(fill="x", padx=20, pady=(0, 15))
        
        self.search_btn = ctk.CTkButton(
            actions_grid,
            text="🔍 Search Vault",
            height=45,
            font=("SF Pro", 14),
            fg_color=("#2196F3", "#1565C0"),
            command=lambda: self.master.master.show_view(3) if hasattr(self.master.master, 'show_view') else None
        )
        self.search_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        self.browse_btn = ctk.CTkButton(
            actions_grid,
            text="📁 Browse Files",
            height=45,
            font=("SF Pro", 14),
            fg_color=("#4CAF50", "#2E7D32"),
            command=lambda: self.master.master.show_view(4) if hasattr(self.master.master, 'show_view') else None
        )
        self.browse_btn.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        
        self.ai_btn = ctk.CTkButton(
            actions_grid,
            text="🤖 AI Assistant",
            height=45,
            font=("SF Pro", 14),
            fg_color=("#9C27B0", "#6A1B9A"),
            command=lambda: self.master.master.show_view(5) if hasattr(self.master.master, 'show_view') else None
        )
        self.ai_btn.grid(row=0, column=2, sticky="ew")
        
        actions_grid.columnconfigure(0, weight=1)
        actions_grid.columnconfigure(1, weight=1)
        actions_grid.columnconfigure(2, weight=1)
        
        # Last updated
        self.last_updated = ctk.CTkLabel(
            main_container,
            text="",
            font=("SF Pro", 11),
            text_color=("gray50", "gray60")
        )
        self.last_updated.pack(anchor="e", padx=25, pady=(0, 20))

    def _create_card(self, parent, icon: str, label: str, value: str, bg_dark: str, bg_light: str) -> ctk.CTkFrame:
        """Create a stat card."""
        card = ctk.CTkFrame(parent, corner_radius=15, height=120)
        card.pack(side="left", fill="both", expand=True, padx=(0, 12))
        card.pack_propagate(False)
        
        # Icon background circle
        icon_bg = ctk.CTkFrame(card, corner_radius=25, fg_color=bg_light)
        icon_bg.place(relx=0.5, rely=0.25, anchor="center", relWidth=0.35, relHeight=0.35)
        
        icon_label = ctk.CTkLabel(
            icon_bg,
            text=icon,
            font=("SF Pro", 20)
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Value
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("SF Pro", 24, "bold")
        )
        value_label.place(relx=0.5, rely=0.55, anchor="center")
        card.value_label = value_label
        
        # Label
        label_label = ctk.CTkLabel(
            card,
            text=label,
            font=("SF Pro", 12),
            text_color=("gray60", "gray80")
        )
        label_label.place(relx=0.5, rely=0.75, anchor="center")
        
        return card

    def _create_metric_row(self, parent, label: str, row: int) -> ctk.CTkLabel:
        """Create a metric row."""
        label_widget = ctk.CTkLabel(
            parent,
            text=f"{label}: —",
            font=("SF Pro", 13),
            anchor="w"
        )
        label_widget.grid(row=row, column=0, sticky="w", pady=3)
        return label_widget

    def refresh(self):
        """Refresh dashboard data."""
        self.refresh_btn.configure(state="disabled", text="...")
        thread = threading.Thread(target=self._fetch_thread)
        thread.daemon = True
        thread.start()

    def _fetch_thread(self):
        """Fetch data from API."""
        try:
            health = self.api_client.health_check()
            collections = self.api_client.get_collections()
            self.after(0, self._update_display, health, collections)
        except Exception as e:
            self.after(0, self._show_error, str(e))

    def _update_display(self, health: dict, collections: list):
        """Update display with fetched data."""
        self.refresh_btn.configure(state="normal", text="🔄")
        
        # Update status banner
        is_healthy = health.get("data", {}).get("service_status") == "healthy"
        if is_healthy:
            self.status_icon.configure(text="✅")
            self.status_text.configure(text="VaultMind API is healthy")
            self.status_banner.configure(fg_color=("#E8F5E9", "#1B5E20"))
        else:
            self.status_icon.configure(text="⚠️")
            self.status_text.configure(text="Service may have issues")
            self.status_banner.configure(fg_color=("#FFF3E0", "#E65100"))
        
        # Get data from health
        data = health.get("data", {})
        
        # API/Model cards
        self.api_card.value_label.configure(text="✅ Online" if is_healthy else "❌ Offline")
        
        model = data.get("embedding_service", {}).get("model_name", "Unknown")
        model_short = model[:18] + "..." if len(model) > 18 else model
        self.model_card.value_label.configure(text=model_short)
        
        # Collections
        if collections:
            col = collections[0]
            count = col.get("document_count", 0)
            self.doc_card.value_label.configure(text=f"{count:,}")
            self.col_card.value_label.configure(text=f"{len(collections)}")
        else:
            self.doc_card.value_label.configure(text="0")
            self.col_card.value_label.configure(text="0")
        
        # Metrics
        sys_data = data.get("system_status", {})
        embed_data = data.get("embedding_service", {})
        
        # Uptime
        uptime_sec = sys_data.get("uptime_seconds", 0)
        hours = int(uptime_sec // 3600)
        mins = int((uptime_sec % 3600) // 60)
        self.uptime_label.configure(text=f"Uptime: {hours}h {mins}m")
        
        # Memory
        mem_mb = sys_data.get("memory_usage_mb", 0)
        self.memory_label.configure(text=f"Memory: {mem_mb:.0f} MB")
        
        # CPU
        cpu = sys_data.get("cpu_usage_percent", 0)
        self.cpu_label.configure(text=f"CPU: {cpu:.1f}%")
        
        # Embeddings
        metrics = embed_data.get("metrics", {})
        total_req = metrics.get("total_requests", 0)
        self.embedding_label.configure(text=f"Requests: {total_req}")
        
        # Cache
        cache_size = embed_data.get("cache_size", 0)
        self.cache_label.configure(text=f"Cache: {cache_size} items")
        
        # Last updated
        from datetime import datetime
        self.last_updated.configure(text=f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    def _show_error(self, error: str):
        """Show error state."""
        self.refresh_btn.configure(state="normal", text="🔄")
        self.status_icon.configure(text="❌")
        self.status_text.configure(text=f"Error: {error}")
        self.status_banner.configure(fg_color=("#FFEBEE", "#B71C1C"))

    def start_auto_refresh(self, interval_ms: int = 60000):
        """Start auto-refresh timer."""
        def auto_refresh():
            self.refresh()
            self.after(interval_ms, auto_refresh)
        self.after(interval_ms, auto_refresh)
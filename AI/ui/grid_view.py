"""Grid Node Status View."""
import customtkinter as ctk
import threading
import json
import subprocess
import time
from typing import Callable, Optional


# Node inventory: the other machines this build can reach over SSH.
#
# Empty on purpose. A published build has no grid of its own to report on, and a
# hard-coded list of somebody's servers and addresses does not belong in a
# repository. Add your own entries, or point this at your own config file.
NODES: dict[str, dict] = {}


class GridView(ctk.CTkFrame):
    """Grid node status and control view."""

    def __init__(self, parent, on_sync: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_sync = on_sync
        self.nodes = {}
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray20"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Grid Nodes",
            font=("SF Pro", 16, "bold")
        )
        title.grid(row=0, column=0, padx=15, pady=10)

        self.refresh_btn = ctk.CTkButton(
            header,
            text="Refresh",
            width=80,
            height=30,
            command=self.refresh
        )
        self.refresh_btn.grid(row=0, column=1, padx=10, pady=10)

        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.content,
            text="Click Refresh to scan nodes...",
            font=("SF Pro", 12),
            text_color=("gray40", "gray60")
        )
        self.status_label.grid(row=0, column=0, pady=20)

    def refresh(self):
        """Refresh all node statuses."""
        self.status_label.configure(text="Scanning nodes...")
        self.refresh_btn.configure(state="disabled")
        
        thread = threading.Thread(target=self._scan_thread)
        thread.daemon = True
        thread.start()

    def _scan_thread(self):
        """Scan nodes in background."""
        results = {}
        for node_id, node in NODES.items():
            results[node_id] = self._get_node_info(node["ip"])
            time.sleep(0.3)
        
        self.after(0, self._display_results, results)

    def _get_node_info(self, ip: str) -> dict:
        """Get info from a single node."""
        info = {
            "status": "offline",
            "hostname": "N/A",
            "uptime": "N/A",
            "load": "N/A",
            "memory": "N/A",
            "vaultmind": "N/A",
            "ollama": "N/A"
        }
        
        try:
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=3", ip, "echo ok"],
                capture_output=True, timeout=5
            )
            if result.returncode != 0:
                return info
            
            info["status"] = "online"
            
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=3", ip, "hostname"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["hostname"] = result.stdout.strip()
            
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=3", ip, "uptime | sed 's/.*up /up /' | sed 's/,.*load/ load/'"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["uptime"] = result.stdout.strip()[:50]
            
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=3", ip, "curl -s http://localhost:8000/health | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"data\",{}).get(\"service_status\",\"unknown\"))' 2>/dev/null || echo offline"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["vaultmind"] = result.stdout.strip()
            
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=3", ip, "pgrep ollama > /dev/null && echo running || echo stopped"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["ollama"] = result.stdout.strip()
                
        except:
            pass
        
        return info

    def _display_results(self, results: dict):
        """Display scan results."""
        for widget in self.content.winfo_children():
            widget.destroy()
        
        online = sum(1 for r in results.values() if r["status"] == "online")
        self.status_label.configure(text=f"{online}/{len(results)} nodes online")
        
        row = 0
        for node_id, info in results.items():
            self._create_node_card(row, node_id, info)
            row += 1
        
        self.refresh_btn.configure(state="normal")

    def _create_node_card(self, row: int, node_id: str, info: dict):
        """Create a node status card."""
        card = ctk.CTkFrame(self.content, corner_radius=10)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 5))
        header.grid_columnconfigure(0, weight=1)
        
        status_color = "#4ade80" if info["status"] == "online" else "#f87171"
        status_icon = "🟢" if info["status"] == "online" else "🔴"
        
        title = ctk.CTkLabel(
            header,
            text=f"{status_icon} {node_id.upper()}",
            font=("SF Pro", 14, "bold")
        )
        title.grid(row=0, column=0, sticky="w")
        
        ip_label = ctk.CTkLabel(
            header,
            text=NODES.get(node_id, {}).get("ip", "N/A"),
            font=("SF Mono", 10),
            text_color=("gray40", "gray60")
        )
        ip_label.grid(row=0, column=1, sticky="e")
        
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))
        
        items = [
            ("Hostname", info["hostname"]),
            ("Uptime", info["uptime"]),
            ("VaultMind", info["vaultmind"]),
            ("Ollama", info["ollama"]),
        ]
        
        for i, (label, value) in enumerate(items):
            col = i % 2
            r = i // 2
            
            ctk.CTkLabel(
                grid,
                text=f"{label}:",
                font=("SF Pro", 11),
                text_color=("gray40", "gray60"),
                anchor="w"
            ).grid(row=r*2, column=col, sticky="w", padx=(0, 20))
            
            val_color = ("gray20", "gray80")
            if label == "VaultMind" and value == "healthy":
                val_color = ("green", "#4ade80")
            elif label == "VaultMind" and value != "healthy" and value != "N/A":
                val_color = ("orange", "#fbbf24")
            
            ctk.CTkLabel(
                grid,
                text=value[:40] if value else "N/A",
                font=("SF Pro", 11),
                text_color=val_color,
                anchor="w"
            ).grid(row=r*2+1, column=col, sticky="w", padx=(0, 20), pady=(0, 5))
        
        if info["status"] == "online":
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))
            
            ctk.CTkButton(
                btn_frame,
                text="Sync Desktop",
                height=28,
                command=lambda: self._sync_node(node_id)
            ).pack(side="left", padx=(0, 10))
            
            ctk.CTkButton(
                btn_frame,
                text="Trigger Index",
                height=28,
                command=lambda: self._trigger_index(node_id)
            ).pack(side="left")

    def _sync_node(self, node_id: str):
        """Sync desktop app to node."""
        ip = NODES.get(node_id, {}).get("ip")
        if not ip:
            return
        
        self.status_label.configure(text=f"Syncing to {node_id}...")
        
        def do_sync():
            try:
                result = subprocess.run([
                    "rsync", "-az", "--delete",
                    "-e", "ssh",
                    "--exclude", "*.pyc",
                    "--exclude", "__pycache__",
                    "$HOME/vault-mind-desktop/",
                    f"{ip}:$HOME/vault-mind-desktop/"
                ], capture_output=True, timeout=120)
                
                success = result.returncode == 0
                self.after(0, lambda: self.status_label.configure(
                    text=f"Sync {'SUCCESS' if success else 'FAILED'} to {node_id}"
                ))
                if success:
                    self.after(0, lambda: self.refresh())
            except:
                self.after(0, lambda: self.status_label.configure(
                    text=f"Sync FAILED to {node_id}"
                ))
        
        thread = threading.Thread(target=do_sync)
        thread.daemon = True
        thread.start()

    def _trigger_index(self, node_id: str):
        """Trigger indexing on node."""
        ip = NODES.get(node_id, {}).get("ip")
        if not ip:
            return
        
        self.status_label.configure(text=f"Triggering index on {node_id}...")
        
        def do_trigger():
            try:
                result = subprocess.run([
                    "ssh", ip,
                    "curl -s -X POST http://localhost:8000/api/index "
                    "-H 'Content-Type: application/json' "
                    "-d '{\"vault_name\": \"my_vault\", \"vault_path\": \"$HOME/Obsidian\"}'"
                ], capture_output=True, text=True, timeout=10)
                
                self.after(0, lambda: self.status_label.configure(
                    text=f"Index triggered on {node_id}"
                ))
            except:
                self.after(0, lambda: self.status_label.configure(
                    text=f"Index trigger FAILED on {node_id}"
                ))
        
        thread = threading.Thread(target=do_trigger)
        thread.daemon = True
        thread.start()

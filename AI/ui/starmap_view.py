"""Starmap view for Obsidian TODOs - visual constellation view."""
import customtkinter as ctk
from typing import Optional, Callable, List, Dict, Tuple
import threading
import math
import random
from pathlib import Path
from datetime import datetime

OBSIDIAN_PATH = Path.home() / "Obsidian"
SCAN_PATTERNS = ["TODO:", "todo:", "Idea:", "idea:", "Quest:", "quest:"]
KEYWORD_PATTERNS = ["TODO", "FIXME", "Active", "Working on", "In Progress", "Status:"]
HEADER_PATTERNS = [
    (r'^##\s*.*[🚧🔨]|^##.*Active|^##.*Working|^##.*In Progress', "SECTION"),
    (r'^##\s*.*[🥚🥚]|^##.*Shell|^##.*Ideas', "IDEA"),
    (r'^##\s*.*[🏁✅]|^##.*Finished|^##.*Complete|^##.*Done', "DONE"),
    (r'^#.*TODO|^#.*Task|^#.*Quest', "SECTION"),
]
CHECKBOX_DONE = __import__('re').compile(r'^\s*[-*]\s*\[[xX]\]')
CHECKBOX_TODO = __import__('re').compile(r'^\s*[-*]\s*\[ \]')


class StarMapNode:
    """Represents a single item in the starmap."""
    def __init__(self, x: float, y: float, item: Dict):
        self.x = x
        self.y = y
        self.item = item
        self.pulse_phase = random.random() * 2 * math.pi
        self.size = 8
    
    @property
    def type(self) -> str:
        return self.item.get("type", "TODO")
    
    @property
    def color(self) -> str:
        colors = {
            "TODO": "#FF6B6B",
            "IDEA": "#4ECDC4", 
            "SECTION": "#9B59B6",
            "DONE": "#27AE60",
        }
        return colors.get(self.type, "#95A5A6")


class StarMapConstellation:
    """Represents a file as a constellation of stars."""
    def __init__(self, filename: str, file_path: str):
        self.filename = filename
        self.file_path = file_path
        self.nodes: List[StarMapNode] = []
        self.center_x = 0
        self.center_y = 0
        self.radius = 50
        self.expanded = False


class StarmapView(ctk.CTkFrame):
    """Starmap visualization of Obsidian TODOs and Ideas."""

    def __init__(
        self,
        parent,
        on_open_file: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.on_open_file = on_open_file
        self.constellations: List[StarMapConstellation] = []
        self.selected_node: Optional[StarMapNode] = None
        self.dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.hover_node: Optional[StarMapNode] = None
        self.animation_phase = 0
        self.setup_ui()
        self.after(100, self._start_animation)

    def setup_ui(self):
        """Set up the starmap interface."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="🌌 Obsidian Starmap",
            font=("SF Pro", 24, "bold")
        )
        title.pack(side="left")

        # Controls
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.zoom_in_btn = ctk.CTkButton(
            controls_frame,
            text="🔍+",
            width=40,
            height=30,
            command=self._zoom_in
        )
        self.zoom_in_btn.pack(side="left", padx=(0, 5))

        self.zoom_out_btn = ctk.CTkButton(
            controls_frame,
            text="🔍-",
            width=40,
            height=30,
            command=self._zoom_out
        )
        self.zoom_out_btn.pack(side="left", padx=(0, 10))

        self.reset_btn = ctk.CTkButton(
            controls_frame,
            text="🎯 Reset View",
            width=100,
            height=30,
            command=self._reset_view
        )
        self.reset_btn.pack(side="left", padx=(0, 10))

        # Filter dropdown
        self.filter_var = ctk.StringVar(value="all")
        filter_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=["All", "TODOs", "Ideas", "Done"],
            variable=self.filter_var,
            command=self._apply_filter,
            width=120
        )
        filter_menu.pack(side="left", padx=(0, 10))

        self.rescan_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Rescan",
            width=80,
            height=30,
            command=self.scan_vault
        )
        self.rescan_btn.pack(side="right")

        # Stats label
        self.stats_label = ctk.CTkLabel(
            controls_frame,
            text="Scanning...",
            font=("SF Pro", 12),
            text_color=("gray50", "gray60")
        )
        self.stats_label.pack(side="right", padx=20)

        # Canvas container
        canvas_container = ctk.CTkFrame(self, corner_radius=15)
        canvas_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Starmap canvas
        self.canvas = ctk.CTkCanvas(
            canvas_container,
            bg="#0a0a1a",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_zoom)
        self.canvas.bind("<Motion>", self._on_hover)

        # Info panel
        self.info_frame = ctk.CTkFrame(self, corner_radius=10)
        self.info_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="🌟 Hover over a star to see details. Drag to pan. Scroll to zoom.",
            font=("SF Pro", 12),
            wraplength=600
        )
        self.info_label.pack(pady=15)

    def _start_animation(self):
        """Start the pulse animation."""
        def animate():
            self.animation_phase += 0.05
            self._redraw_canvas()
            self.after(50, animate)
        self.after(50, animate)

    def scan_vault(self):
        """Scan vault and build constellations."""
        self.stats_label.configure(text="Scanning...")
        thread = threading.Thread(target=self._scan_thread)
        thread.daemon = True
        thread.start()

    def _scan_thread(self):
        """Background scan thread."""
        items = self._do_scan()
        self.after(0, self._on_scan_complete, items)

    def _do_scan(self) -> List[Dict]:
        """Perform the actual scan."""
        items = []
        seen = {}
        
        if not OBSIDIAN_PATH.exists():
            return items
        
        SKIP_PATTERNS = [
            'password', 'passwd', 'secret', 'credential',
            'pwords', 'keys_', '_keys', 'api_key', 'apikey'
        ]
        
        def should_skip_file(filepath: str) -> bool:
            fname = filepath.lower()
            return any(p in fname for p in SKIP_PATTERNS)

        for md_file in OBSIDIAN_PATH.rglob("*.md"):
            if '.obsidian' in str(md_file) or should_skip_file(str(md_file)):
                continue
                
            try:
                with open(md_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\n")
                    
                for line_num, line in enumerate(lines, 1):
                    if CHECKBOX_DONE.match(line):
                        continue
                    
                    line_lower = line.lower()
                    if any(p in line_lower for p in SKIP_PATTERNS):
                        continue
                    
                    checkbox_match = CHECKBOX_TODO.match(line)
                    if checkbox_match:
                        content_text = line.strip()
                        normalized = content_text.lower()
                        key = f"checkbox:{normalized[:50]}"
                        
                        is_duplicate = key in seen
                        if key in seen:
                            seen[key] += 1
                        else:
                            seen[key] = 1
                        
                        items.append({
                            "type": "TODO",
                            "content": content_text,
                            "file": str(md_file),
                            "filename": md_file.name,
                            "line": line_num,
                        })
                        continue
                    
                    if line.strip().startswith('- ') or line.strip().startswith('* '):
                        line_lower = line.lower()
                        matched_keyword = None
                        
                        for keyword in KEYWORD_PATTERNS:
                            if keyword.lower() in line_lower:
                                matched_keyword = keyword
                                break
                        
                        if matched_keyword:
                            normalized = line.strip().lower()
                            key = f"bullet:{normalized[:50]}"
                            
                            is_duplicate = key in seen
                            if key in seen:
                                seen[key] += 1
                            else:
                                seen[key] = 1
                            
                            items.append({
                                "type": "TODO",
                                "content": line.strip(),
                                "file": str(md_file),
                                "filename": md_file.name,
                                "line": line_num,
                            })
                            continue
                    
                    for pattern in SCAN_PATTERNS:
                        if pattern in line:
                            normalized = line.strip().lower()
                            key = f"{pattern}:{normalized[:50]}"
                            
                            is_duplicate = key in seen
                            if key in seen:
                                seen[key] += 1
                            else:
                                seen[key] = 1
                            
                            items.append({
                                "type": "TODO" if "todo" in pattern.lower() else "IDEA",
                                "content": line.strip(),
                                "file": str(md_file),
                                "filename": md_file.name,
                                "line": line_num,
                            })
                            break
                    
                    for pattern, item_type in HEADER_PATTERNS:
                        import re
                        if re.match(pattern, line.strip(), re.IGNORECASE):
                            normalized = line.strip().lower()
                            key = f"header:{normalized[:50]}"
                            
                            is_duplicate = key in seen
                            if key in seen:
                                seen[key] += 1
                            else:
                                seen[key] = 1
                            
                            items.append({
                                "type": item_type,
                                "content": line.strip(),
                                "file": str(md_file),
                                "filename": md_file.name,
                                "line": line_num,
                            })
                            break
                            
            except Exception:
                continue
        
        return items

    def _on_scan_complete(self, items: List[Dict]):
        """Build constellations from scanned items."""
        self.constellations = []
        
        # Group by file
        files: Dict[str, List[Dict]] = {}
        for item in items:
            fname = item["filename"]
            if fname not in files:
                files[fname] = []
            files[fname].append(item)
        
        # Create constellations
        angle_step = 2 * math.pi / max(len(files), 1)
        constellation_radius = 150
        
        for i, (filename, file_items) in enumerate(files.items()):
            constellation = StarMapConstellation(
                filename,
                file_items[0]["file"]
            )
            
            # Position constellation in a ring
            angle = i * angle_step
            constellation.center_x = 400 + constellation_radius * math.cos(angle)
            constellation.center_y = 300 + constellation_radius * math.sin(angle)
            constellation.radius = 30 + len(file_items) * 5
            
            # Create nodes in spiral pattern
            node_count = len(file_items)
            for j, item in enumerate(file_items):
                node_angle = j * 2 * math.pi / node_count + random.uniform(-0.3, 0.3)
                node_dist = 20 + (j % 3) * 15
                x = constellation.center_x + node_dist * math.cos(node_angle)
                y = constellation.center_y + node_dist * math.sin(node_angle)
                node = StarMapNode(x, y, item)
                constellation.nodes.append(node)
            
            self.constellations.append(constellation)
        
        # Update stats
        todo_count = len([i for i in items if i["type"] == "TODO"])
        idea_count = len([i for i in items if i["type"] in ("IDEA", "SECTION")])
        done_count = len([i for i in items if i["type"] == "DONE"])
        
        self.stats_label.configure(
            text=f"🌟 {len(items)} stars in {len(self.constellations)} constellations"
        )
        
        self._redraw_canvas()

    def _redraw_canvas(self):
        """Redraw the starmap canvas."""
        self.canvas.delete("all")
        
        filter_type = self.filter_var.get().lower()
        
        # Draw constellation connections
        for constellation in self.constellations:
            visible_nodes = [n for n in constellation.nodes 
                          if self._node_matches_filter(n, filter_type)]
            
            if len(visible_nodes) > 1:
                # Draw constellation halo
                cx = (constellation.center_x + self.offset_x) * self.zoom
                cy = (constellation.center_y + self.offset_y) * self.zoom
                r = constellation.radius * self.zoom
                
                self.canvas.create_oval(
                    cx - r, cy - r, cx + r, cy + r,
                    outline="#334455",
                    width=1
                )
                
                # Draw connections
                for i, node in enumerate(visible_nodes):
                    for j in range(i + 1, len(visible_nodes)):
                        x1 = (node.x + self.offset_x) * self.zoom
                        y1 = (node.y + self.offset_y) * self.zoom
                        x2 = (visible_nodes[j].x + self.offset_x) * self.zoom
                        y2 = (visible_nodes[j].y + self.offset_y) * self.zoom
                        self.canvas.create_line(
                            x1, y1, x2, y2,
                            fill="#223344",
                            width=1
                        )
        
        # Draw stars
        for constellation in self.constellations:
            for node in constellation.nodes:
                if not self._node_matches_filter(node, filter_type):
                    continue
                
                x = (node.x + self.offset_x) * self.zoom
                y = (node.y + self.offset_y) * self.zoom
                
                # Pulse effect
                pulse = math.sin(self.animation_phase + node.pulse_phase) * 0.3 + 0.7
                size = node.size * self.zoom * pulse
                
                is_hover = node == self.hover_node
                is_selected = node == self.selected_node
                
                # Glow effect
                glow_color = node.color
                if is_selected:
                    glow_color = "#FFFFFF"
                
                # Draw glow
                self.canvas.create_oval(
                    x - size * 2, y - size * 2,
                    x + size * 2, y + size * 2,
                    fill=glow_color,
                    outline=""
                )
                self.canvas.create_oval(
                    x - size, y - size,
                    x + size, y + size,
                    fill="#FFFFFF" if is_selected else node.color,
                    outline=""
                )
        
        # Draw constellation labels
        for constellation in self.constellations:
            visible_nodes = [n for n in constellation.nodes 
                          if self._node_matches_filter(n, filter_type)]
            if visible_nodes:
                cx = (constellation.center_x + self.offset_x) * self.zoom
                cy = (constellation.center_y + self.offset_y) * self.zoom + constellation.radius * self.zoom + 15
                
                self.canvas.create_text(
                    cx, cy,
                    text=constellation.filename[:25] + "..." if len(constellation.filename) > 25 else constellation.filename,
                    fill="#667788",
                    font=("SF Pro", 9)
                )

    def _node_matches_filter(self, node: StarMapNode, filter_type: str) -> bool:
        if filter_type == "all" or filter_type == "todos" and node.type == "TODO":
            return True
        if filter_type == "ideas" and node.type in ("IDEA", "SECTION"):
            return True
        if filter_type == "done" and node.type == "DONE":
            return True
        return filter_type == "all"

    def _apply_filter(self, _=None):
        """Apply filter and redraw."""
        self._redraw_canvas()

    def _on_click(self, event):
        """Handle canvas click."""
        self.dragging = True
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        
        # Check for node selection
        clicked_node = self._find_node_at(event.x, event.y)
        if clicked_node:
            self.selected_node = clicked_node
            self._show_node_info(clicked_node)
            self._redraw_canvas()

    def _on_drag(self, event):
        """Handle canvas drag."""
        if self.dragging:
            dx = (event.x - self.last_mouse_x) / self.zoom
            dy = (event.y - self.last_mouse_y) / self.zoom
            self.offset_x += dx
            self.offset_y += dy
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self._redraw_canvas()

    def _on_release(self, event):
        """Handle mouse release."""
        self.dragging = False

    def _on_zoom(self, event):
        """Handle mouse wheel zoom."""
        if event.delta > 0:
            self.zoom = min(self.zoom * 1.1, 3.0)
        else:
            self.zoom = max(self.zoom / 1.1, 0.3)
        self._redraw_canvas()

    def _on_hover(self, event):
        """Handle mouse hover."""
        node = self._find_node_at(event.x, event.y)
        if node != self.hover_node:
            self.hover_node = node
            if node:
                self.info_label.configure(
                    text=f"🌟 {node.type}: {node.item['content'][:80]}... | {node.item['filename']}:{node.item['line']}"
                )
                self.canvas.configure(cursor="hand2")
            else:
                self.info_label.configure(
                    text="🌟 Hover over a star to see details. Drag to pan. Scroll to zoom."
                )
                self.canvas.configure(cursor="arrow")
            self._redraw_canvas()

    def _find_node_at(self, x: float, y: float) -> Optional[StarMapNode]:
        """Find node at canvas coordinates."""
        for constellation in self.constellations:
            for node in constellation.nodes:
                nx = (node.x + self.offset_x) * self.zoom
                ny = (node.y + self.offset_y) * self.zoom
                dist = math.sqrt((x - nx) ** 2 + (y - ny) ** 2)
                if dist < 15:
                    return node
        return None

    def _show_node_info(self, node: StarMapNode):
        """Show detailed info for selected node."""
        item = node.item
        self.info_label.configure(
            text=f"📄 {item['filename']}:{item['line']}\n{item['content'][:150]}...\n\nClick to open file."
        )

    def _zoom_in(self):
        """Zoom in."""
        self.zoom = min(self.zoom * 1.2, 3.0)
        self._redraw_canvas()

    def _zoom_out(self):
        """Zoom out."""
        self.zoom = max(self.zoom / 1.2, 0.3)
        self._redraw_canvas()

    def _reset_view(self):
        """Reset view to center."""
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self._redraw_canvas()

    def start_scan(self):
        """Start initial scan."""
        self.after(500, self.scan_vault)
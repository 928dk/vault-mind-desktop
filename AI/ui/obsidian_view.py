"""Obsidian view for scanning TODOs and ideas."""
import customtkinter as ctk
from typing import Optional, Callable, List, Dict
import threading
import re
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
CHECKBOX_DONE = re.compile(r'^\s*[-*]\s*\[[xX]\]')
CHECKBOX_TODO = re.compile(r'^\s*[-*]\s*\[ \]')


class ObsidianView(ctk.CTkFrame):
    """Obsidian dashboard for TODOs and ideas."""

    def __init__(
        self,
        parent,
        on_open_file: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.on_open_file = on_open_file
        self.all_items = []
        self.filtered_items = []
        self.current_index = 0
        self.setup_ui()
        # Don't scan here - will be called after mainloop starts

    def setup_ui(self):
        """Set up the Obsidian view interface."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="📋 Obsidian TODOs & Ideas",
            font=("SF Pro", 24, "bold")
        )
        title.pack(side="left")

        # Stats label
        self.stats_label = ctk.CTkLabel(
            header_frame,
            text="Scanning...",
            font=("SF Pro", 12),
            text_color=("gray50", "gray60")
        )
        self.stats_label.pack(side="right")

        # Filter buttons
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.filter_var = ctk.StringVar(value="all")
        
        filters = [
            ("all", "📋 All"),
            ("todo", "📋 TODOs"),
            ("idea", "💡 Sections"),
            ("completed", "✅ Done"),
        ]
        
        for val, label in filters:
            btn = ctk.CTkRadioButton(
                filter_frame,
                text=label,
                variable=self.filter_var,
                value=val,
                command=self._apply_filter
            )
            btn.pack(side="left", padx=(0, 15))

        # Refresh button
        refresh_btn = ctk.CTkButton(
            filter_frame,
            text="🔄 Rescan",
            width=100,
            height=32,
            font=("SF Pro", 12),
            command=self.scan_vault
        )
        refresh_btn.pack(side="right")

        # Item list container
        self.list_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.list_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Navigation for verification
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.prev_btn = ctk.CTkButton(
            self.nav_frame,
            text="◀ Previous",
            width=120,
            height=35,
            command=self._prev_item
        )
        self.prev_btn.pack(side="left")

        self.next_btn = ctk.CTkButton(
            self.nav_frame,
            text="Next ▶",
            width=120,
            height=35,
            command=self._next_item
        )
        self.next_btn.pack(side="right")

        self.nav_label = ctk.CTkLabel(
            self.nav_frame,
            text="",
            font=("SF Pro", 12)
        )
        self.nav_label.pack(side="left", padx=20)

        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.list_container,
            text="No TODOs or Ideas found.\nClick 'Rescan' to search again.",
            font=("SF Pro", 14),
            text_color=("gray50", "gray60")
        )

    def start_scan(self):
        """Start the initial vault scan (call after mainloop starts)."""
        self.after(500, self.scan_vault)

    def refresh_files(self):
        """Refresh the file list (called by scanner callback)."""
        self.scan_vault()

    def scan_vault(self):
        """Scan vault for TODOs and ideas."""
        self.stats_label.configure(text="Scanning...")
        self.prev_btn.configure(state="disabled")
        self.next_btn.configure(state="disabled")
        
        # Clear list
        for widget in self.list_container.winfo_children():
            widget.destroy()

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
        seen = {}  # Track for duplicates
        
        if not OBSIDIAN_PATH.exists():
            return items
        
        # Skip patterns for sensitive/deletable files
        SKIP_PATTERNS = [
            'password', 'passwd', 'secret', 'credential',
            'pwords', 'keys_', '_keys', 'api_key', 'apikey'
        ]
        
        def should_skip_file(filepath: str) -> bool:
            """Check if file should be skipped (sensitive files)."""
            fname = filepath.lower()
            return any(p in fname for p in SKIP_PATTERNS)

        for md_file in OBSIDIAN_PATH.rglob("*.md"):
            # Skip .obsidian and sensitive files
            if '.obsidian' in str(md_file) or should_skip_file(str(md_file)):
                continue
                
            try:
                with open(md_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\n")
                    
                for line_num, line in enumerate(lines, 1):
                    # Skip completed checkboxes
                    if CHECKBOX_DONE.match(line):
                        continue
                    
                    # Skip lines with sensitive references
                    line_lower = line.lower()
                    if any(p in line_lower for p in SKIP_PATTERNS):
                        continue
                    
                    # Check for checkbox TODOs (- [ ])
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
                            "duplicate_count": seen[key] if is_duplicate else 0,
                            "duplicate_key": key if is_duplicate else None
                        })
                        continue
                    
                    # Check for bullet points with keywords
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
                                "duplicate_count": seen[key] if is_duplicate else 0,
                                "duplicate_key": key if is_duplicate else None
                            })
                            continue
                    
                    # Check for text patterns
                    for pattern in SCAN_PATTERNS:
                        if pattern in line:
                            # Normalize text for duplicate detection
                            normalized = line.strip().lower()
                            key = f"{pattern}:{normalized[:50]}"
                            
                            # Track duplicates
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
                                "duplicate_count": seen[key] if is_duplicate else 0,
                                "duplicate_key": key if is_duplicate else None
                            })
                            break  # Only match first pattern per line
                    
                    # Check for section headers
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
                                "duplicate_count": seen[key] if is_duplicate else 0,
                                "duplicate_key": key if is_duplicate else None
                            })
                            break
                            
            except Exception:
                continue
        
        return items

    def _on_scan_complete(self, items: List[Dict]):
        """Handle scan completion."""
        self.all_items = items
        self.filtered_items = items
        self.current_index = 0
        
        # Count by type
        todo_count = len([i for i in items if i["type"] == "TODO"])
        idea_count = len([i for i in items if i["type"] in ("IDEA", "SECTION")])
        done_count = len([i for i in items if i["type"] == "DONE"])
        
        self.stats_label.configure(
            text=f"Found: {len(items)} items (📋{todo_count} | 💡{idea_count} | ✅{done_count})"
        )
        
        self._apply_filter()

    def _apply_filter(self):
        """Apply current filter."""
        filter_type = self.filter_var.get()
        
        if filter_type == "all":
            self.filtered_items = self.all_items
        elif filter_type == "todo":
            self.filtered_items = [i for i in self.all_items if i["type"] == "TODO"]
        elif filter_type == "idea":
            self.filtered_items = [i for i in self.all_items if i["type"] in ("IDEA", "SECTION")]
        elif filter_type == "completed":
            self.filtered_items = [i for i in self.all_items if i["type"] == "DONE"]
        
        self.current_index = 0
        self._show_items()

    def _show_items(self):
        """Display filtered items."""
        # Clear list
        for widget in self.list_container.winfo_children():
            widget.destroy()

        if not self.filtered_items:
            self.empty_label.pack(pady=50)
            self.nav_label.configure(text="No items")
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
            return

        # Show items
        for i, item in enumerate(self.filtered_items):
            self._create_item_card(i, item)

        # Update navigation
        total = len(self.filtered_items)
        self.nav_label.configure(text=f"{self.current_index + 1} / {total}")
        self.prev_btn.configure(state="normal" if self.current_index > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_index < total - 1 else "disabled")

    def _create_item_card(self, index: int, item: Dict):
        """Create an item card."""
        is_current = index == self.current_index
        bg_color = ("lightblue", "darkblue") if is_current else ("gray90", "gray20")
        
        card = ctk.CTkFrame(
            self.list_container,
            corner_radius=10,
            fg_color=bg_color
        )
        card.pack(fill="x", pady=(0, 8), padx=2)

        # Header
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(12, 5))

        # Type badge with icons
        type_icons = {
            "TODO": ("📋", "#FF6B6B"),
            "IDEA": ("💡", "#4ECDC4"),
            "SECTION": ("📁", "#9B59B6"),
            "DONE": ("✅", "#27AE60"),
        }
        icon, color = type_icons.get(item["type"], ("📄", "#95A5A6"))
        type_label = ctk.CTkLabel(
            header_frame,
            text=f"{icon} {item['type']}",
            font=("SF Pro", 11, "bold"),
            text_color=color
        )
        type_label.pack(side="left")

        # Duplicate warning
        if item["duplicate_count"] > 1:
            dup_label = ctk.CTkLabel(
                header_frame,
                text=f"⚠️ Duplicate #{item['duplicate_count']}",
                font=("SF Pro", 11),
                text_color="orange"
            )
            dup_label.pack(side="left", padx=(10, 0))

        # File info
        file_label = ctk.CTkLabel(
            header_frame,
            text=f"{item['filename']}:{item['line']}",
            font=("SF Pro", 10),
            text_color=("gray50", "gray60")
        )
        file_label.pack(side="right")

        # Content
        content_label = ctk.CTkLabel(
            card,
            text=item["content"][:200] + ("..." if len(item["content"]) > 200 else ""),
            font=("SF Pro", 13),
            anchor="w",
            justify="left",
            wraplength=600
        )
        content_label.pack(fill="x", padx=15, pady=(0, 12))

        # Open button
        open_btn = ctk.CTkButton(
            card,
            text="📖 Open File",
            width=120,
            height=30,
            font=("SF Pro", 11),
            fg_color="transparent",
            command=lambda f=item["file"]: self._open_file(f)
        )
        open_btn.pack(side="right", padx=15, pady=(0, 10))

    def _open_file(self, filepath: str):
        """Open file in default application."""
        import webbrowser
        webbrowser.open(f"file://{filepath}")

    def _prev_item(self):
        """Navigate to previous item."""
        if self.current_index > 0:
            self.current_index -= 1
            self._show_items()

    def _next_item(self):
        """Navigate to next item."""
        if self.current_index < len(self.filtered_items) - 1:
            self.current_index += 1
            self._show_items()

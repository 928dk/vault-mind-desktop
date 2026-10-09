"""
Obsidian Scanner - Periodic scanning of Obsidian vault for VaultMind

Monitors ~/Obsidian and syncs new/changed files to the knowledge base.
"""
import json
import sqlite3
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, List
import hashlib


class ObsidianScanner:
    """Periodic scanner for Obsidian vault."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path.home() / ".config" / "vault-mind-desktop" / "obsidian_scan.db"
        self.db_path = db_path
        self.obsidian_path = Path.home() / "Obsidian"
        self._lock = threading.Lock()
        self._scanning = False
        self._stop_event = threading.Event()
        self._scan_thread: Optional[threading.Thread] = None
        self._interval = 300  # 5 minutes default
        self._callbacks: List[Callable] = []
        self._init_db()
    
    def _init_db(self):
        """Initialize the scan database."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS obsidian_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                name TEXT,
                modified REAL,
                size INTEGER,
                checksum TEXT,
                frontmatter TEXT,
                tags TEXT,
                last_synced REAL
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS scan_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                files_added INTEGER,
                files_modified INTEGER,
                files_deleted INTEGER,
                errors TEXT
            )
        """)
        
        c.execute("""
            CREATE TABLE IF NOT EXISTS sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                action TEXT,
                file_path TEXT,
                success INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_callback(self, callback: Callable):
        """Add a callback to be called when files change."""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self, added: int, modified: int, deleted: int):
        """Notify all registered callbacks."""
        for cb in self._callbacks:
            try:
                cb(added=added, modified=modified, deleted=deleted)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def scan(self) -> dict:
        """Perform a single scan of the Obsidian vault."""
        if self._scanning:
            return {"error": "Scan already in progress"}
        
        with self._lock:
            self._scanning = True
        
        result = {
            "added": 0,
            "modified": 0,
            "deleted": 0,
            "errors": [],
            "timestamp": time.time()
        }
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            if not self.obsidian_path.exists():
                result["errors"].append(f"Obsidian path not found: {self.obsidian_path}")
                return result
            
            # Get existing files
            c.execute("SELECT path, checksum FROM obsidian_files")
            existing = {row[0]: row[1] for row in c.fetchall()}
            current_files = {}
            
            # Scan all .md files
            for md_file in self.obsidian_path.rglob("*.md"):
                if md_file.name.startswith("."):
                    continue
                    
                try:
                    stat = md_file.stat()
                    content = md_file.read_text(encoding='utf-8')
                    checksum = hashlib.md5(content.encode()).hexdigest()
                    current_files[str(md_file)] = checksum
                    
                    # Extract frontmatter and tags
                    frontmatter = self._extract_frontmatter(content)
                    tags = self._extract_tags(content)
                    
                    if str(md_file) not in existing:
                        # New file
                        c.execute("""
                            INSERT INTO obsidian_files 
                            (path, name, modified, size, checksum, frontmatter, tags, last_synced)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(md_file),
                            md_file.name,
                            stat.st_mtime,
                            stat.st_size,
                            checksum,
                            json.dumps(frontmatter),
                            json.dumps(tags),
                            time.time()
                        ))
                        result["added"] += 1
                        self._log_sync(conn, "add", str(md_file), True)
                        
                    elif existing[str(md_file)] != checksum:
                        # Modified file
                        c.execute("""
                            UPDATE obsidian_files SET
                                modified = ?,
                                checksum = ?,
                                frontmatter = ?,
                                tags = ?,
                                last_synced = ?
                            WHERE path = ?
                        """, (
                            stat.st_mtime,
                            checksum,
                            json.dumps(frontmatter),
                            json.dumps(tags),
                            time.time(),
                            str(md_file)
                        ))
                        result["modified"] += 1
                        self._log_sync(conn, "modify", str(md_file), True)
                        
                except Exception as e:
                    result["errors"].append(f"Error scanning {md_file}: {e}")
                    self._log_sync(conn, "error", str(md_file), False)
            
            # Find deleted files
            for old_path in existing:
                if old_path not in current_files:
                    c.execute("DELETE FROM obsidian_files WHERE path = ?", (old_path,))
                    result["deleted"] += 1
                    self._log_sync(conn, "delete", old_path, True)
            
            # Log scan
            c.execute("""
                INSERT INTO scan_log 
                (timestamp, files_added, files_modified, files_deleted, errors)
                VALUES (?, ?, ?, ?, ?)
            """, (
                time.time(),
                result["added"],
                result["modified"],
                result["deleted"],
                json.dumps(result["errors"]) if result["errors"] else None
            ))
            
            conn.commit()
            
        finally:
            conn.close()
            self._scanning = False
        
        # Notify callbacks
        if result["added"] > 0 or result["modified"] > 0:
            self._notify_callbacks(result["added"], result["modified"], result["deleted"])
        
        return result
    
    def _extract_frontmatter(self, content: str) -> dict:
        """Extract YAML frontmatter from markdown content."""
        import re
        frontmatter = {}
        
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            yaml_text = match.group(1)
            for line in yaml_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
        
        return frontmatter
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract Obsidian tags from content."""
        import re
        tags = []
        
        # #tag format
        tags.extend(re.findall(r'(?<!\w)#([\w-]+)', content))
        
        return list(set(tags))
    
    def _log_sync(self, conn, action: str, file_path: str, success: bool):
        """Log a sync action."""
        c = conn.cursor()
        c.execute("""
            INSERT INTO sync_history (timestamp, action, file_path, success)
            VALUES (?, ?, ?, ?)
        """, (time.time(), action, file_path, 1 if success else 0))
    
    def get_recent_changes(self, limit: int = 20) -> List[dict]:
        """Get recent file changes."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            SELECT path, name, modified, last_synced
            FROM obsidian_files
            ORDER BY last_synced DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in c.fetchall():
            results.append({
                "path": row[0],
                "name": row[1],
                "modified": row[2],
                "synced": row[3]
            })
        
        conn.close()
        return results
    
    def get_all_files(self) -> List[dict]:
        """Get all indexed files."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT path, name, modified, tags FROM obsidian_files ORDER BY name")
        
        results = []
        for row in c.fetchall():
            results.append({
                "path": row[0],
                "name": row[1],
                "modified": row[2],
                "tags": json.loads(row[3]) if row[3] else []
            })
        
        conn.close()
        return results
    
    def get_stats(self) -> dict:
        """Get scanning statistics."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM obsidian_files")
        file_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM scan_log")
        scan_count = c.fetchone()[0]
        
        c.execute("SELECT * FROM scan_log ORDER BY id DESC LIMIT 1")
        last_scan = c.fetchone()
        
        c.execute("SELECT SUM(files_added) + SUM(files_modified) FROM scan_log")
        total_changes = c.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "file_count": file_count,
            "scan_count": scan_count,
            "total_changes": total_changes,
            "last_scan_time": last_scan[2] if last_scan else None,
            "obsidian_path": str(self.obsidian_path)
        }
    
    def start_periodic(self, interval: int = 300):
        """Start periodic scanning in background thread."""
        self._interval = interval
        self._stop_event.clear()
        
        if self._scan_thread and self._scan_thread.is_alive():
            return
        
        def scan_loop():
            while not self._stop_event.is_set():
                self.scan()
                self._stop_event.wait(self._interval)
        
        self._scan_thread = threading.Thread(target=scan_loop, daemon=True)
        self._scan_thread.start()
    
    def stop_periodic(self):
        """Stop periodic scanning."""
        self._stop_event.set()
        if self._scan_thread:
            self._scan_thread.join(timeout=2)




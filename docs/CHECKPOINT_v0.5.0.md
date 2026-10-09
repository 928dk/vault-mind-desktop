# OpenMind Checkpoint v0.5.0

**Date:** 2026-03-22
**Version:** 0.5.0

## Summary

OpenMind is an enhanced LocalMind with OpenCode-like capabilities, MCP server support, auto-scanning, and backup/checkpoint system.

## New Features

### MCP Server (Model Context Protocol)
- REST API at configurable port (default 9090)
- Endpoints:
  - `GET /tools` - List tools
  - `POST /tools/{name}` - Execute tool
  - `GET /todos` - List todos
  - `POST /todos` - Add todo
  - `GET /projects` - List scanned projects
  - `POST /ask` - Ask question
  - `GET /backups` - List checkpoints
  - `POST /backups` - Create checkpoint

### Auto-Scanning
- **Project Scanner**: Detects project types (node, python, rust, go, docker, git)
- **File Scanner**: Indexes files by extension, size, modification time
- **Pattern Scanner**: Finds TODOs, FIXME, functions, classes
- **Background Scans**: Configurable interval (default 60 min)
- **Databases**:
  - `openmind_scan.db` - Project/file/pattern index
  - `scan_log` - Scan history

### Backup & Checkpoint System
- **BackupManager** class for managing backups
- Creates tar.gz archives with all databases
- Restore from any checkpoint
- Backup location: `~/.openmind/backups/`
- Commands:
  - `/backup [name]` - Create checkpoint
  - `/checkpoints` - List checkpoints
  - `/restore <path>` - Restore checkpoint

### Enhanced Commands
| Command | Description |
|---------|-------------|
| `/scan [path]` | Scan for projects |
| `/tree <path> [depth]` | Show project tree |
| `/backup [name]` | Create checkpoint |
| `/checkpoints` | List checkpoints |
| `/restore <path>` | Restore checkpoint |
| `/mcp [port]` | Start MCP server |

### Tools Available
- **File**: bash, read, write, glob, grep, ls, file_info
- **Web**: search, fetch
- **Task**: todos, addtodo, done
- **Scan**: scan_projects, find_patterns, project_tree
- **Backup**: create_checkpoint, restore_backup, list_backups

## Files

### Core
- `openmind.py` - Main engine (~1100 lines)
- `openmind_gui.py` - Desktop GUI (~480 lines)

### Databases
- `openmind_knowledge.db` - Knowledge cache
- `openmind_todos.db` - Todo list
- `openmind_sessions.db` - Session history
- `openmind_skills.db` - Skill registry
- `openmind_scan.db` - Scan index

## Integration with VaultMind

### OpenCode Plugin (vaultmind)
Located at: `~/.config/opencode/plugins/vaultmind/`
- vaultmind_search
- vaultmind_stats
- vaultmind_todos
- vaultmind_addtodo
- vaultmind_browse
- vaultmind_index

### Desktop App Tabs
- 0: Todos
- 1: Obsidian TODOs
- 2: Dashboard
- 3: Search
- 4: Browse
- 5: AI Assistant (OpenCode)
- 6: Grid Nodes

## Grid Sync

### Nodes
| Node | IP | Status | VaultMind | Ollama |
|------|-----|--------|-----------|--------|
| node-1 | 198.51.100.10 | Offline | - | - |
| node-2 | 198.51.100.11 | Online | healthy | running |
| node-3 | 198.51.100.12 | Online | healthy | stopped |
| node-4 | 198.51.100.13 | Online | healthy | running |

### Sync Commands
```bash
# Scan nodes
python3 grid_sync_enhanced.py --scan

# Sync to node
python3 grid_sync_enhanced.py --sync node-1

# Trigger index
python3 grid_sync_enhanced.py --index node-1
```

## Next Steps
- Add more MCP endpoints
- Implement skill marketplace
- Create scheduled checkpoints
- Sync checkpoints across grid

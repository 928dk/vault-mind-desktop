# VaultMind Desktop Checkpoint v0.3.0

**Date:** 2026-03-22
**Version:** 0.3.0

## Changes Since v0.2.0

### New Features
- **OpenCode Integration**
  - `services/opencode_integration.py` - Python SDK integration
  - `ui/ai_assistant_view.py` - AI Assistant tab (Ctrl+5)
  - OpenCode plugin at `~/.config/opencode/plugins/vaultmind/`
  
- **Grid Node Control**
  - `ui/grid_view.py` - Grid nodes tab (Ctrl+6)
  - `grid_sync.py` - Basic grid sync tool
  - `grid_sync_enhanced.py` - Enhanced SSH/rsync sync tool
  - Sync projects to remote nodes
  - Trigger indexing on remote nodes
  - Real-time node status monitoring

- **Tab Index Update**
  - 0: Todos
  - 1: Obsidian TODOs  
  - 2: Dashboard
  - 3: Search
  - 4: Browse
  - 5: AI Assistant (NEW)
  - 6: Grid Nodes (NEW - replaced Status)

### OpenCode Plugin Tools
- `vaultmind_search` - Semantic search in vault
- `vaultmind_stats` - Collection statistics
- `vaultmind_todos` - List personal todos
- `vaultmind_addtodo` - Add new todo
- `vaultmind_browse` - Browse vault files
- `vaultmind_index` - Trigger reindexing

### Grid Nodes Discovered
| Node | IP | Status | VaultMind | Ollama |
|------|-----|--------|-----------|--------|
| node-1 | 198.51.100.10 | Offline | - | - |
| node-2 | 198.51.100.11 | Online | healthy | running |
| node-3 | 198.51.100.12 | Online | healthy | stopped |
| node-4 | 198.51.100.13 | Online | healthy | running |

## Files Modified
- `ui/main_window.py` - Added AI + Grid tabs, updated nav
- `ui/ai_assistant_view.py` - New file
- `ui/grid_view.py` - New file
- `services/opencode_integration.py` - New file
- `~/projects/Grid-Server/grid-nexus/grid_sync.py` - New file
- `~/projects/Grid-Server/grid-nexus/grid_sync_enhanced.py` - New file
- `~/.config/opencode/opencode.json` - Added vaultmind plugin
- `~/.config/opencode/plugins/vaultmind/*` - New plugin files

## Next Steps
- Start nexus workers on remote nodes
- Add more OpenCode tools
- Test AI Assistant functionality
- Monitor indexing progress on node-1

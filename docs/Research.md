# Research Notes - vault-mind-desktop

## Research Areas

### Obsidian Integration
- Vault structure: Markdown files with YAML frontmatter
- Indexing: ChromaDB for semantic embeddings
- Search: Vector similarity with Ollama

### UI/UX Decisions
- CustomTkinter chosen over Flet (more stable)
- System tray integration for background operation
- Dark/light theme following system preference

### Context Engineering (from NxCode article)
- Atomic notes (one concept per note)
- Consistent naming: `YYYY-MM-DD-title.md`
- Tags for AI retrieval: #idea, #decision, #meeting
- Links between notes for context

## Lessons Learned

### Technical
- Threading: Don't call self.after() before mainloop starts
- System tray: pystray cross-platform works well
- API: httpx async client stable for search

### User Experience
- Right-click context menus essential
- Search history valuable
- Preview pane reduces switching

## Future Research
- MCP server integration
- Multiple vault support
- Global hotkey for quick access
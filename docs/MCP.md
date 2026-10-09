# MCP Server Integration

MCP (Model Context Protocol) allows external AI systems like Claude Code to interact with VaultMind Desktop programmatically.

## Quick Start

### 1. Enable MCP Server

Edit `~/.config/vault-mind-desktop/config.json`:

```json
{
  "mcp_enabled": true,
  "mcp_port": 9091
}
```

### 2. Start VaultMind Desktop

The MCP server starts automatically when the app launches if `mcp_enabled: true`.

### 3. Use with Claude Code

In Claude Code, add this to your project config to search your vault:

```json
{
  "mcpServers": {
    "vaultmind": {
      "url": "http://127.0.0.1:9091"
    }
  }
}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/search?q=...` | GET | Semantic search |
| `/stats` | GET | Vault statistics |
| `/files` | GET | List vault files |
| `/read?path=...` | GET | Read file content |
| `/todos` | GET | Get all todos |
| `/todos` | POST | Add new todo |
| `/todos/{id}` | PUT | Update todo |
| `/todos/{id}` | DELETE | Delete todo |
| `/index` | GET | Trigger indexing |

## Examples

### Search Vault

```bash
curl "http://127.0.0.1:9091/search?q=car%20repair&limit=5"
```

### Get Vault Stats

```bash
curl "http://127.0.0.1:9091/stats"
```

### List Files

```bash
curl "http://127.0.0.1:9091/files"
```

### Add Todo

```bash
curl -X POST "http://127.0.0.1:9091/todos?content=Buy%20oil&priority=high"
```

## Configuration

The MCP server runs on port **9091** by default (to avoid conflict with OpenMind MCP on 9090). To change it:

1. Edit `~/.config/vault-mind-desktop/config.json`
2. Set `"mcp_port": <your-port>`
3. Restart VaultMind Desktop

## Dependencies

- fastapi >= 0.100.0
- uvicorn >= 0.23.0

These are included in requirements.txt.
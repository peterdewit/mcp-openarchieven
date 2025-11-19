# Architecture

This project uses:

- [FastMCP](https://github.com/modelcontextprotocol/python-sdk) (`mcp.server.fastmcp.FastMCP`)
- [Uvicorn](https://www.uvicorn.org/) ASGI server
- HTTP Streamable MCP transport (`streamable_http_app()`)

---

## Components

### 1. FastMCP Server

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("openarchieven")
```

Tools are registered via the `@mcp.tool()` decorator.

### 2. Streamable HTTP App

```python
app = mcp.streamable_http_app()
```

This creates an ASGI application exposing MCP HTTP endpoints (e.g. `/mcp`), which Uvicorn serves.

### 3. Uvicorn

The Dockerfile and examples start:

```bash
uvicorn openarchieven_server:app --host 0.0.0.0 --port 8010
```

This provides:

- HTTP interface for MetaMCP / OpenWebUI
- Streamable HTTP MCP protocol
- Easy containerization

---

## Error Handling

All outbound API calls go through `safe_get()` which:

- Performs a GET with timeout.
- Distinguishes:
  - connection errors
  - HTTP errors (status != 200)
  - invalid JSON
- Returns a uniform shape:

```json
{ "ok": true, "data": { ... } }
```

or

```json
{
  "ok": false,
  "error": "connection_error|http_error|invalid_json",
  "details": { ... }
}
```

Tools then convert this into:

```json
{
  "status": "error",
  "error": "<code>",
  "details": { ... }
}
```

This consistent pattern helps the LLM understand failures without crashing the server.

---

## Why Streamable HTTP (Not SSE/stdio)

- Matches your existing infrastructure (MetaMCP + other MCP servers).
- Easier to deploy behind containers, proxies, and on systems like Unraid.
- Compatible with current OpenWebUI MCP “Streamable HTTP” mode.

---

## Why JSON-Only

OpenArchieven offers other formats for some endpoints:

- `.xml`
- `.gedcom`
- `.ttl`
- `.nt`

They are not used here because:

- Agents already handle JSON best.
- Extra formats add dependencies and complexity.
- For typical genealogical workflows, JSON A2A is sufficient.

---

## Interaction Model

1. LLM agent receives a user request (e.g. “find birth record for X born in 1850”).
2. Agent chooses appropriate tool:
   - `search_people` or `match_person`.
3. Agent interprets `normalized` results.
4. For a specific candidate record, agent calls `get_record_details`.
5. Agent may then write structured data into a separate genealogy memory MCP server.

The OpenArchieven MCP server is intentionally **stateless** and **read-only**.

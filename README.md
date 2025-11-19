# MCP OpenArchieven

MCP server for the public JSON API of [Open Archives (OpenArchieven.nl)](https://www.openarchieven.nl/).

This server exposes the OpenArchieven API as **Model Context Protocol (MCP) tools** so LLM agents (OpenWebUI, MetaMCP, etc.) can:

- Search people and events across linked archives
- Perform exact match lookups (name + birth year)
- Fetch detailed A2A record data
- Retrieve “born N years ago” lists
- Fetch historic census data for Dutch places
- List user comments attached to records

The server is designed to be:

- **LLM-friendly** – every tool returns both `raw` API JSON and `normalized` data
- **Genealogy-focused** – tools and normalization are tailored to genealogical workflows
- **Simple to run** – one Python file, one Dockerfile, HTTP Streamable MCP

---

## Features

- JSON-only usage of OpenArchieven API (versions 1.0 and 1.1)
- Clean FastMCP integration with `streamable_http_app()`
- Robust error handling and parameter validation
- Lightweight dependencies: `mcp`, `requests`, `uvicorn`
- Ready to plug into MetaMCP / OpenWebUI

See:

- [`docs/ENDPOINTS.md`](docs/ENDPOINTS.md) for API details
- [`docs/NORMALIZATION.md`](docs/NORMALIZATION.md) for raw vs normalized formats
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for design and reasoning

---

## Quick Start (Bare Python)

```bash
git clone https://github.com/yourname/mcp-openarchieven.git
cd mcp-openarchieven

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn openarchieven_server:app --host 0.0.0.0 --port 8010
```

The MCP HTTP endpoint will be available at:

```
http://localhost:8010/mcp
```

---

## Quick Start (Docker)

Build:

```bash
docker build -t mcp-openarchieven .
```

Run:

```bash
docker run -d --name mcp-openarchieven -p 8010:8010 mcp-openarchieven
```

---

## MCP / MetaMCP Integration

Configure this server as a **Streamable HTTP** MCP endpoint.

Example MetaMCP source entry:

```json
{
  "type": "server",
  "id": "openarchieven",
  "name": "Open Archieven API",
  "endpoint": {
    "type": "streamable-http",
    "url": "http://mcp-openarchieven:8010/mcp"
  }
}
```

For OpenWebUI + MetaMCP:

- Type: `Streamable HTTP`
- URL: `http://mcp-openarchieven:8010/mcp`

---

## Tools Exposed

All tools return:

- `status`: `"ok"` or `"error"`
- On success:
  - `raw`: original API JSON
  - `normalized`: simplified, LLM-oriented structure

Tools:

- `search_people` – search people/events across archives
- `search_people_all` – same, but fetch all pages
- `match_person` – exact match by name + birth year
- `get_record_details` – detailed A2A record (persons, event, source)
- `get_births_years_ago` – list of people born N years ago
- `get_census_data` – census data for place/municipality
- `list_comments` – user comments on records

Details for each tool are documented in `docs/ENDPOINTS.md` and `docs/NORMALIZATION.md`.

---

## Typical Genealogy Workflow

1. Start with `search_people` using a name (and possibly place/year filters).
2. Inspect `normalized.people` to select promising candidates.
3. For a chosen record, call `get_record_details` with `archive` and `identifier`.
4. Compare persons and events with your genealogy memory.
5. Optionally call `get_census_data` to give historical context for a place and year.
6. Use `list_comments` to see whether other researchers added useful notes.

---

## License

MIT License. See [LICENSE](LICENSE).

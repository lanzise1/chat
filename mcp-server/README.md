# demo MCP server

A tiny MCP server that exposes a handful of toy tools over **streamable-http**.

## Tools

| name | args | description |
| --- | --- | --- |
| `get_current_time` | `timezone: str = "Asia/Shanghai"` | current date/time in an IANA timezone |
| `add` | `a: float, b: float` | a + b |
| `echo` | `text: str` | echo back the text |
| `get_weather` | `city: str` | **fake** weather report for a city |

## Run

```bash
cd mcp-server
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python server.py
```

The server listens on `0.0.0.0:8765` by default (override with `MCP_HOST` / `MCP_PORT`).
MCP endpoint: `http://localhost:8765/mcp/`.

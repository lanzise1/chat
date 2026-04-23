"""A tiny MCP server exposing a handful of toy tools over streamable-http.

Run it with:
    python server.py

It will listen on 0.0.0.0:8765 and expose the MCP endpoint at /mcp/.
"""
from __future__ import annotations

import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from mcp.server.fastmcp import FastMCP

HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8765"))

mcp = FastMCP("demo-tools", host=HOST, port=PORT)


@mcp.tool()
def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """Return the current date/time in an IANA timezone (default: Asia/Shanghai)."""
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        return f"Unknown timezone: {timezone}"
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")


@mcp.tool()
def add(a: float, b: float) -> float:
    """Return a + b. Useful when the user asks you to do arithmetic."""
    return a + b


@mcp.tool()
def echo(text: str) -> str:
    """Echo the given text back verbatim. Handy for debugging the MCP pipe."""
    return text


@mcp.tool()
def get_weather(city: str) -> dict:
    """Return a FAKE weather report for a city. Not real data — for demo only."""
    conditions = ["sunny", "cloudy", "rainy", "windy", "snowy"]
    random.seed(city)
    return {
        "city": city,
        "condition": random.choice(conditions),
        "temperature_c": random.randint(-5, 35),
        "note": "This is mocked data from the demo MCP server.",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

"""SSE helper — format a dict as a single `data: ...\\n\\n` event line."""
from __future__ import annotations

import json
from typing import Any, Mapping


def sse_event(payload: Mapping[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

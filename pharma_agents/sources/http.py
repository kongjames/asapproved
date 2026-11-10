"""Minimal JSON fetch on the standard library, with the offline guard CI relies on."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

USER_AGENT = "pharma-agents (https://github.com/kongjames/pharma-agents)"


class OfflineError(RuntimeError):
    """Raised when ``PHARMA_AGENTS_OFFLINE=1`` and code tries to reach the network."""


def fetch_json(url: str, timeout: float = 30.0) -> dict[str, Any]:
    if os.environ.get("PHARMA_AGENTS_OFFLINE") == "1":
        raise OfflineError(f"PHARMA_AGENTS_OFFLINE=1: refusing to fetch {url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} from {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not reach {url}: {exc.reason}") from exc

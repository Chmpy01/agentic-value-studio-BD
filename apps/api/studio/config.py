"""Paths and runtime flags. Environment is read on each call so tests can isolate state."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "reference_projects"
DATA = ROOT / "data"
CONTRACTS = ROOT / "packages" / "contracts"

DENIED_ACTIONS = (
    "bms.setpoint.write",
    "plc.write",
    "access_control.write",
    "production.system.write",
)
ALLOWED_ACTIONS = (
    "read_synthetic_events",
    "reason_on_graph",
    "draft_work_order",
)
PACKS = ("office", "retail", "manufacturing")


def bind_host() -> str:
    return os.environ.get("BIND_HOST", "127.0.0.1")


def api_port() -> int:
    return int(os.environ.get("PORT", "8876"))


def a2a_port() -> int:
    return int(os.environ.get("A2A_PORT", "8877"))


def a2a_url() -> str:
    return os.environ.get("A2A_CONTEXT_URL", f"http://127.0.0.1:{a2a_port()}").rstrip("/")


def step_delay() -> float:
    return float(os.environ.get("STUDIO_STEP_DELAY", "0.55"))


def db_path() -> Path:
    raw = os.environ.get("STUDIO_DB")
    path = Path(raw) if raw else DATA / "state" / "studio.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def langgraph_db_path() -> Path:
    raw = os.environ.get("STUDIO_LG_DB")
    path = Path(raw) if raw else DATA / "state" / "langgraph.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def web_dist() -> Path | None:
    """Built web app to serve from the API (single-process mode). Off unless STUDIO_WEB_DIST is set."""
    raw = os.environ.get("STUDIO_WEB_DIST")
    if not raw:
        return None
    path = Path(raw).resolve()
    return path if (path / "index.html").is_file() else None


def agntcy_directory_enabled() -> bool:
    return os.environ.get("AGNTCY_DIRECTORY_ENABLED", "false").lower() in {"1", "true", "yes"}

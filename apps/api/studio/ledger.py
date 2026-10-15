"""SQLite audit log for runs and trace events."""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

from studio.config import db_path

_LOCK = threading.RLock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path()), timeout=5, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init() -> None:
    with _LOCK, connect() as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                pack TEXT NOT NULL,
                state TEXT NOT NULL,
                approval TEXT,
                intent_hash TEXT NOT NULL,
                plan_hash TEXT,
                trace_id TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                intent_version TEXT NOT NULL,
                expires_at TEXT,
                orchestrator TEXT NOT NULL,
                transport TEXT NOT NULL,
                actor TEXT,
                rationale TEXT,
                action_key TEXT,
                action_consumed INTEGER NOT NULL DEFAULT 0,
                ticket_json TEXT,
                auto INTEGER NOT NULL DEFAULT 0,
                created TEXT NOT NULL,
                updated TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                run_id TEXT NOT NULL,
                trace_id TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                pack_id TEXT NOT NULL,
                intent_version TEXT NOT NULL,
                intent_hash TEXT NOT NULL,
                agent TEXT NOT NULL,
                stage TEXT NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT NOT NULL,
                graph_refs TEXT NOT NULL,
                evidence_status TEXT NOT NULL,
                actor TEXT NOT NULL,
                created TEXT NOT NULL
            )
            """
        )


def create_run(
    *,
    pack: str,
    intent_hash: str,
    intent_version: str,
    orchestrator: str,
    transport: str,
    expires_at: str | None,
    auto: bool,
) -> dict:
    run_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    now = utc_now()
    with _LOCK, connect() as connection:
        connection.execute(
            """
            INSERT INTO runs (
                id, pack, state, approval, intent_hash, plan_hash, trace_id, correlation_id,
                intent_version, expires_at, orchestrator, transport, auto, created, updated
            ) VALUES (?, ?, 'READY', NULL, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                pack,
                intent_hash,
                trace_id,
                trace_id,
                intent_version,
                expires_at,
                orchestrator,
                transport,
                1 if auto else 0,
                now,
                now,
            ),
        )
    return get_run(run_id)


def update_run(run_id: str, **fields: object) -> None:
    if not fields:
        return
    columns = {
        "state": "state",
        "approval": "approval",
        "plan_hash": "plan_hash",
        "expires_at": "expires_at",
        "actor": "actor",
        "rationale": "rationale",
        "action_key": "action_key",
        "action_consumed": "action_consumed",
        "ticket_json": "ticket_json",
        "auto": "auto",
    }
    assignments = []
    values: list[object] = []
    for key, value in fields.items():
        if key not in columns:
            raise KeyError(key)
        assignments.append(f"{columns[key]}=?")
        values.append(value)
    assignments.append("updated=?")
    values.append(utc_now())
    values.append(run_id)
    with _LOCK, connect() as connection:
        connection.execute(f"UPDATE runs SET {', '.join(assignments)} WHERE id=?", values)


def append_event(
    run: dict,
    *,
    agent: str,
    stage: str,
    event_type: str,
    message: str,
    details: dict,
    evidence_status: str,
    actor: str,
    graph_refs: list[str] | None = None,
    event_id: str | None = None,
) -> dict | None:
    event_id = event_id or str(uuid.uuid4())
    refs = graph_refs if graph_refs is not None else list(details.get("graphRefs") or [])
    now = utc_now()
    with _LOCK, connect() as connection:
        try:
            connection.execute(
                """
                INSERT INTO events (
                    event_id, run_id, trace_id, correlation_id, pack_id, intent_version, intent_hash,
                    agent, stage, event_type, message, details, graph_refs, evidence_status, actor, created
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    run["id"],
                    run["trace_id"],
                    run["correlation_id"],
                    run["pack"],
                    run["intent_version"],
                    run["intent_hash"],
                    agent,
                    stage,
                    event_type,
                    message,
                    json.dumps(details, ensure_ascii=False),
                    json.dumps(refs),
                    evidence_status,
                    actor,
                    now,
                ),
            )
        except sqlite3.IntegrityError:
            return None
        connection.execute("UPDATE runs SET updated=? WHERE id=?", (now, run["id"]))
    return _events(run["id"])[-1]


def _row_run(row: sqlite3.Row) -> dict:
    data = dict(row)
    if data.get("ticket_json"):
        data["ticket"] = json.loads(data["ticket_json"])
    else:
        data["ticket"] = None
    data["action_consumed"] = bool(data["action_consumed"])
    data["auto"] = bool(data["auto"])
    return data


def _events(run_id: str) -> list[dict]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM events WHERE run_id=? ORDER BY seq", (run_id,)
        ).fetchall()
    events = []
    for row in rows:
        item = dict(row)
        item["details"] = json.loads(item["details"])
        item["graph_refs"] = json.loads(item["graph_refs"])
        events.append(item)
    return events


def get_run(run_id: str) -> dict | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    if row is None:
        return None
    run = _row_run(row)
    run["events"] = _events(run_id)
    return run


def events_after(run_id: str, seq: int) -> list[dict]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM events WHERE run_id=? AND seq>? ORDER BY seq", (run_id, seq)
        ).fetchall()
    events = []
    for row in rows:
        item = dict(row)
        item["details"] = json.loads(item["details"])
        item["graph_refs"] = json.loads(item["graph_refs"])
        events.append(item)
    return events


def public_run(run: dict) -> dict:
    """JSON shape returned to the studio."""
    return {
        "run": {
            "id": run["id"],
            "pack": run["pack"],
            "state": run["state"],
            "approval": run["approval"],
            "intentHash": run["intent_hash"],
            "planHash": run["plan_hash"],
            "traceId": run["trace_id"],
            "correlationId": run["correlation_id"],
            "intentVersion": run["intent_version"],
            "expiresAt": run["expires_at"],
            "orchestrator": run["orchestrator"],
            "transport": run["transport"],
            "actor": run["actor"],
            "rationale": run["rationale"],
            "actionKey": run["action_key"],
            "actionConsumed": run["action_consumed"],
            "auto": run["auto"],
            "created": run["created"],
            "updated": run["updated"],
            "ticket": run["ticket"],
        },
        "events": [
            {
                "seq": event["seq"],
                "eventId": event["event_id"],
                "runId": event["run_id"],
                "traceId": event["trace_id"],
                "correlationId": event["correlation_id"],
                "packId": event["pack_id"],
                "intentVersion": event["intent_version"],
                "intentHash": event["intent_hash"],
                "agent": event["agent"],
                "stage": event["stage"],
                "type": event["event_type"],
                "message": event["message"],
                "details": event["details"],
                "graphRefs": event["graph_refs"],
                "evidenceStatus": event["evidence_status"],
                "actor": event["actor"],
                "timestamp": event["created"],
            }
            for event in run["events"]
        ],
    }

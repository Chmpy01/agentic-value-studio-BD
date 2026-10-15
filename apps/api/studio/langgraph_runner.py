"""LangGraph StateGraph with a SQLite checkpointer and an approval interrupt.

The graph calls the same role and policy functions as the step machine.
It is an orchestrator, not an AGNTCY runtime and not a language model.
"""
from __future__ import annotations

import sqlite3
import time
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from studio import ledger
from studio.config import langgraph_db_path, step_delay
from studio.orchestrator import perform

_RUNTIME: dict[str, object] = {"conn": None, "graph": None, "path": None}


class FlowState(TypedDict, total=False):
    run_id: str
    pack: str
    approved: bool


def close_graph() -> None:
    connection = _RUNTIME.get("conn")
    if connection is not None:
        connection.close()
    _RUNTIME["conn"] = None
    _RUNTIME["graph"] = None
    _RUNTIME["path"] = None


def _pace(role: str):
    def node(state: FlowState) -> dict:
        delay = step_delay()
        if delay > 0:
            time.sleep(delay)
        perform(state["run_id"], role)
        return {}

    node.__name__ = role
    return node


def human_approval(state: FlowState) -> dict:
    interrupt(
        {
            "kind": "simulated-work-order",
            "runId": state["run_id"],
            "externalSystemsEnabled": False,
        }
    )
    run = ledger.get_run(state["run_id"])
    approved = bool(run and run["state"] == "APPROVED" and run["approval"] == "approved")
    return {"approved": approved}


def _after_guard(state: FlowState) -> str:
    run = ledger.get_run(state["run_id"])
    if run and run["state"] == "BLOCKED":
        return END
    return "human_approval"


def _after_approval(state: FlowState) -> str:
    if state.get("approved") is True:
        return "act"
    return END


def build_graph():
    graph = StateGraph(FlowState)
    for role in ("sense", "context", "value", "plan", "guard", "act", "verify"):
        graph.add_node(role, _pace(role))
    graph.add_node("human_approval", human_approval)
    graph.add_edge(START, "sense")
    graph.add_edge("sense", "context")
    graph.add_edge("context", "value")
    graph.add_edge("value", "plan")
    graph.add_edge("plan", "guard")
    graph.add_conditional_edges("guard", _after_guard)
    graph.add_conditional_edges("human_approval", _after_approval)
    graph.add_edge("act", "verify")
    graph.add_edge("verify", END)
    return graph


def get_graph():
    path = str(langgraph_db_path())
    if _RUNTIME["graph"] is not None and _RUNTIME["path"] == path:
        return _RUNTIME["graph"]
    close_graph()
    connection = sqlite3.connect(path, check_same_thread=False)
    saver = SqliteSaver(connection)
    compiled = build_graph().compile(checkpointer=saver)
    _RUNTIME["conn"] = connection
    _RUNTIME["graph"] = compiled
    _RUNTIME["path"] = path
    return compiled


def _config(run_id: str) -> dict:
    return {"configurable": {"thread_id": run_id}}


def run_until_pause(run_id: str) -> None:
    run = ledger.get_run(run_id)
    try:
        get_graph().invoke({"run_id": run_id, "pack": run["pack"]}, _config(run_id))
    except Exception as exc:  # noqa: BLE001 — audit then stop
        fresh = ledger.get_run(run_id)
        if fresh and fresh["state"] not in {"REJECTED", "EXPIRED", "BLOCKED", "COMPLETE_NOT_MEASURED", "ERROR"}:
            ledger.append_event(
                fresh,
                agent="system",
                stage="error",
                event_type="workflow.error",
                message=str(exc),
                details={"type": type(exc).__name__},
                evidence_status="POLICY",
                actor="langgraph",
            )
            ledger.update_run(run_id, state="ERROR")


def resume(run_id: str) -> None:
    try:
        get_graph().invoke(Command(resume=True), _config(run_id))
    except Exception as exc:  # noqa: BLE001
        fresh = ledger.get_run(run_id)
        if fresh and fresh["state"] not in {"COMPLETE_NOT_MEASURED", "ERROR", "REJECTED"}:
            ledger.append_event(
                fresh,
                agent="system",
                stage="error",
                event_type="workflow.error",
                message=str(exc),
                details={"type": type(exc).__name__},
                evidence_status="POLICY",
                actor="langgraph",
            )
            ledger.update_run(run_id, state="ERROR")

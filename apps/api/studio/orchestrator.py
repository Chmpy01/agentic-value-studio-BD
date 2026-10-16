"""Explicit stage machine. Each call performs one real role and writes one audit event."""
from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone

from studio import ledger, policy
from studio.adapters import FmTicketAdapter, PolicyDenied, collect_readings
from studio.compiler import ContractError, compile_pack
from studio.config import step_delay
from studio.roles import HANDLERS
from studio.transport import TransportError, resolve_context

PRE_ROLES = ("sense", "context", "value", "plan", "guard")
POST_ROLES = ("act", "verify")
TERMINAL = {"REJECTED", "EXPIRED", "BLOCKED", "COMPLETE_NOT_MEASURED", "ERROR"}
ROLE_ACTOR = {
    "sense": "signal-steward",
    "context": "context-resolver",
    "value": "value-reasoner",
    "plan": "intervention-planner",
    "guard": "policy-gate",
    "act": "action-broker",
    "verify": "outcome-auditor",
}
ROLE_TYPE = {
    "sense": "signal.observed",
    "context": "context.resolved",
    "value": "hypothesis.proposed",
    "plan": "intervention.planned",
    "guard": "policy.checked",
    "act": "action.simulated",
    "verify": "outcome.recorded",
}

_STOP: dict[str, threading.Event] = {}
_THREADS: dict[str, threading.Thread] = {}


class RunError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _completed(run: dict, role: str) -> bool:
    return any(event["agent"] == role and event["stage"] == "complete" for event in run["events"])


def start(
    pack: str,
    *,
    orchestrator: str = "deterministic",
    transport: str = "local",
    auto: bool = False,
    ttl_seconds: int = 900,
) -> dict:
    if orchestrator not in {"deterministic", "langgraph"}:
        raise RunError("orchestrator must be deterministic or langgraph")
    if transport not in {"local", "a2a"}:
        raise RunError("transport must be local or a2a")
    try:
        intent = compile_pack(pack)
    except ContractError as exc:
        raise RunError(str(exc)) from exc
    expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat(timespec="seconds")
    run = ledger.create_run(
        pack=pack,
        intent_hash=intent["intentHash"],
        intent_version=intent["intentVersion"],
        orchestrator=orchestrator,
        transport=transport,
        expires_at=expires,
        auto=auto or orchestrator == "langgraph",
    )
    if orchestrator == "langgraph":
        from studio.langgraph_runner import run_until_pause

        _spawn(run["id"], lambda: run_until_pause(run["id"]))
    elif auto:
        begin_auto(run["id"])
    return ledger.get_run(run["id"])


def _spawn(run_id: str, target) -> None:
    stop = _STOP.get(run_id) or threading.Event()
    _STOP[run_id] = stop
    stop.clear()
    thread = threading.Thread(target=target, name=f"run-{run_id[:8]}", daemon=True)
    _THREADS[run_id] = thread
    thread.start()


def begin_auto(run_id: str) -> None:
    def loop() -> None:
        stop = _STOP[run_id]
        while not stop.is_set():
            current = ledger.get_run(run_id)
            if current is None or current["state"] in TERMINAL or current["state"] == "AWAITING_APPROVAL":
                return
            try:
                step(run_id)
            except Exception as exc:  # noqa: BLE001 — recorded, not hidden
                _fail(run_id, exc)
                return
            delay = step_delay()
            waited = 0.0
            while delay and waited < delay and not stop.is_set():
                time.sleep(min(0.05, delay - waited))
                waited += 0.05
        current = ledger.get_run(run_id)
        if current and current["state"] == "READY":
            ledger.update_run(run_id, state="PAUSED")

    _spawn(run_id, loop)


def pause(run_id: str) -> dict:
    run = ledger.get_run(run_id)
    if run is None:
        raise RunError("run not found", 404)
    stop = _STOP.get(run_id)
    if stop:
        stop.set()
    if run["state"] == "READY":
        ledger.update_run(run_id, state="PAUSED")
    return ledger.get_run(run_id)


def step(run_id: str) -> dict:
    run = ledger.get_run(run_id)
    if run is None:
        raise RunError("run not found", 404)
    if run["orchestrator"] == "langgraph":
        raise RunError("this run is owned by the LangGraph orchestrator")
    if run["orchestrator"] == "discovery":
        raise RunError("this run is owned by the discovery agent; use /api/discovery/runs", 409)
    run = policy.expire_if_needed(run)
    if run["state"] in TERMINAL or run["state"] == "AWAITING_APPROVAL":
        return run
    if run["state"] == "PAUSED":
        ledger.update_run(run_id, state="READY")
        run = ledger.get_run(run_id)
    try:
        intent = compile_pack(run["pack"])
    except ContractError as exc:
        raise RunError(str(exc)) from exc
    if intent["intentHash"] != run["intent_hash"]:
        raise RunError("compiled intent hash changed; refusing to continue this run")
    if run["state"] in {"READY", "APPROVED"}:
        roles = PRE_ROLES if run["state"] == "READY" else POST_ROLES
        for role in roles:
            if not _completed(run, role):
                perform(run_id, role, intent)
                return ledger.get_run(run_id)
    return ledger.get_run(run_id)


def perform(run_id: str, role: str, intent: dict | None = None) -> dict:
    run = ledger.get_run(run_id)
    if run is None:
        raise RunError("run not found", 404)
    existing = next(
        (event for event in run["events"] if event["agent"] == role and event["stage"] == "complete"),
        None,
    )
    if existing:
        return existing["details"]
    if intent is None:
        intent = compile_pack(run["pack"])
    if role == "context":
        result = resolve_context(
            intent,
            transport=run["transport"],
            trace_id=run["trace_id"],
            correlation_id=run["correlation_id"],
        )
    elif role == "act":
        result = _draft_ticket(run, intent)
    elif role == "verify":
        result = HANDLERS["verify"](intent)
        result["realisedValue"] = None
        result["evidenceStatus"] = "NOT_MEASURED"
        result["verificationState"] = "NOT_MEASURED"
    else:
        result = HANDLERS[role](intent)
    if role == "sense":
        result["adapters"] = collect_readings(intent)
    if role == "guard" and not result["passed"]:
        ledger.append_event(
            run,
            agent="guard",
            stage="complete",
            event_type="policy.checked",
            message="Unsafe contract — policy gate refused execution",
            details=result,
            evidence_status="POLICY",
            actor=ROLE_ACTOR["guard"],
            graph_refs=result.get("graphRefs"),
        )
        ledger.update_run(run_id, state="BLOCKED")
        return result
    ledger.append_event(
        run,
        agent=role,
        stage="complete",
        event_type=ROLE_TYPE[role],
        message=result["name"],
        details=result,
        evidence_status=result["evidenceStatus"],
        actor=ROLE_ACTOR[role],
        graph_refs=result.get("graphRefs"),
    )
    if role == "plan":
        ledger.update_run(run_id, plan_hash=result["planHash"])
    if role == "guard":
        fresh = ledger.get_run(run_id)
        ledger.append_event(
            fresh,
            agent="human",
            stage="approval-needed",
            event_type="approval.requested",
            message="Awaiting approval. No tool writes are allowed.",
            details={
                "authority": intent["governance"]["approval"]["role"],
                "intentHash": fresh["intent_hash"],
                "planHash": fresh["plan_hash"],
                "expiresAt": fresh["expires_at"],
                "allowedActions": intent["governance"]["allowedActions"],
                "deniedActions": intent["governance"]["deniedActions"],
                "externalSystemWrite": False,
            },
            evidence_status="POLICY",
            actor="policy-gate",
            graph_refs=intent["valueIntent"]["primaryRefIds"],
        )
        ledger.update_run(run_id, state="AWAITING_APPROVAL")
    if role == "verify":
        ledger.update_run(run_id, state="COMPLETE_NOT_MEASURED")
    return result


def _draft_ticket(run: dict, intent: dict) -> dict:
    if run["state"] != "APPROVED" or run["approval"] != "approved" or not run["action_key"]:
        raise ApprovalErrorBridge("simulated action requires a bound approval")
    if run["action_consumed"]:
        raise ApprovalErrorBridge("action key already used")
    draft = HANDLERS["act"](intent, run["id"])
    with ledger._LOCK, ledger.connect() as connection:
        changed = connection.execute(
            """
            UPDATE runs SET action_consumed=1, updated=?
             WHERE id=? AND state='APPROVED' AND action_consumed=0 AND approval='approved'
            """,
            (ledger.utc_now(), run["id"]),
        ).rowcount
    if changed != 1:
        raise ApprovalErrorBridge("action key already used")
    receipt = FmTicketAdapter().invoke(
        "draft_work_order",
        {
            "approved": True,
            "consumed": False,
            "idempotencyKey": draft["idempotencyKey"],
            "summary": draft["actionSummary"],
        },
    )
    draft["toolReceipt"] = receipt
    ledger.update_run(run["id"], ticket_json=_ticket_json(draft))
    return draft


def _ticket_json(draft: dict) -> str:
    import json

    return json.dumps(
        {
            "ticketType": draft["ticketType"],
            "status": draft["status"],
            "idempotencyKey": draft["idempotencyKey"],
            "externalSystemWritten": False,
            "summary": draft["actionSummary"],
        },
        ensure_ascii=False,
    )


def decide(run_id: str, **kwargs) -> dict:
    run = policy.decide(run_id, **kwargs)
    if run["state"] != "APPROVED":
        return run
    if run["orchestrator"] == "langgraph":
        from studio.langgraph_runner import resume

        _spawn(run_id, lambda: resume(run_id))
    elif run["auto"]:
        begin_auto(run_id)
    return ledger.get_run(run_id)


def _fail(run_id: str, exc: Exception) -> None:
    run = ledger.get_run(run_id)
    if run is None or run["state"] in TERMINAL:
        return
    ledger.append_event(
        run,
        agent="system",
        stage="error",
        event_type="workflow.error",
        message=str(exc),
        details={"type": type(exc).__name__},
        evidence_status="POLICY",
        actor="orchestrator",
    )
    ledger.update_run(run_id, state="ERROR")


class ApprovalErrorBridge(RunError):
    pass


def raise_denied(action: str) -> None:
    """Used by the API to prove physical writes never dispatch."""
    try:
        FmTicketAdapter().invoke(action, {"approved": True})
    except PolicyDenied:
        raise
    raise PolicyDenied(action)

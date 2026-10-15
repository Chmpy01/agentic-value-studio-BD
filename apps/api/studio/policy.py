"""Deterministic approval policy. Models never approve an action."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone

from studio import ledger
from studio.config import DENIED_ACTIONS


class ApprovalError(Exception):
    def __init__(self, message: str, status: int = 409):
        super().__init__(message)
        self.status = status


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def expire_if_needed(run: dict) -> dict:
    if run["state"] != "AWAITING_APPROVAL":
        return run
    expires = _parse(run["expires_at"])
    if expires and datetime.now(timezone.utc) >= expires:
        ledger.append_event(
            run,
            agent="human",
            stage="expired",
            event_type="approval.expired",
            message="Approval window elapsed. No action was taken.",
            details={"decision": "expired", "externalSystemWrite": False},
            evidence_status="POLICY",
            actor="policy-gate",
        )
        ledger.update_run(run["id"], state="EXPIRED", approval="expired")
        return ledger.get_run(run["id"])
    return run


def decide(
    run_id: str,
    *,
    decision: str,
    actor: str,
    intent_hash: str,
    plan_hash: str,
    rationale: str = "",
) -> dict:
    if decision not in {"approved", "rejected"}:
        raise ApprovalError("decision must be approved or rejected", 400)
    actor = (actor or "").strip()
    if len(actor) < 2:
        raise ApprovalError("actor name is required", 400)
    run = ledger.get_run(run_id)
    if run is None:
        raise ApprovalError("run not found", 404)
    run = expire_if_needed(run)
    if run["state"] != "AWAITING_APPROVAL":
        raise ApprovalError(f"run is {run['state']}, not awaiting approval")
    if intent_hash != run["intent_hash"]:
        ledger.append_event(
            run,
            agent="human",
            stage="rejected",
            event_type="approval.mismatch",
            message="Approval rejected because the intent hash did not match.",
            details={"suppliedIntentHash": intent_hash, "expectedIntentHash": run["intent_hash"]},
            evidence_status="POLICY",
            actor=actor,
        )
        raise ApprovalError("intent hash mismatch")
    if not run["plan_hash"] or plan_hash != run["plan_hash"]:
        ledger.append_event(
            run,
            agent="human",
            stage="rejected",
            event_type="approval.mismatch",
            message="Approval rejected because the plan hash did not match.",
            details={"suppliedPlanHash": plan_hash, "expectedPlanHash": run["plan_hash"]},
            evidence_status="POLICY",
            actor=actor,
        )
        raise ApprovalError("plan hash mismatch")
    action_key = secrets.token_hex(16) if decision == "approved" else None
    with ledger._LOCK, ledger.connect() as connection:
        changed = connection.execute(
            """
            UPDATE runs
               SET state=?, approval=?, actor=?, rationale=?, action_key=?, updated=?
             WHERE id=? AND state='AWAITING_APPROVAL'
            """,
            (
                "APPROVED" if decision == "approved" else "REJECTED",
                decision,
                actor,
                rationale,
                action_key,
                ledger.utc_now(),
                run_id,
            ),
        ).rowcount
    if changed != 1:
        raise ApprovalError("approval already handled")
    fresh = ledger.get_run(run_id)
    ledger.append_event(
        fresh,
        agent="human",
        stage="decision",
        event_type="approval.decided",
        message="Approved a simulated work-order draft" if decision == "approved" else "Rejected: no action",
        details={
            "decision": decision,
            "actor": actor,
            "rationale": rationale,
            "intentHash": intent_hash,
            "planHash": plan_hash,
            "actionKeyIssued": bool(action_key),
            "externalSystemWrite": False,
            "deniedActions": list(DENIED_ACTIONS),
        },
        evidence_status="POLICY",
        actor=actor,
    )
    return ledger.get_run(run_id)

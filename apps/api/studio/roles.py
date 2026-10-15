"""Deterministic role handlers.

Provenance: reference_projects/agent_runtime/agents.py. These are logical
roles, not hosted language-model agents. Outcome verification never promotes
a simulation into a measured saving.
"""
from __future__ import annotations

import hashlib
import json

from studio.config import DATA, DENIED_ACTIONS

_PLAN_OPTIONS = json.loads((DATA / "plan_options.json").read_text())


def sense(intent: dict) -> dict:
    snapshots = intent["evidence"]["snapshots"]
    stale = [item for item in snapshots if item.get("quality") == "stale"]
    return {
        "name": "Normalised signals",
        "evidenceStatus": "STALE_SIMULATED" if stale else "SIMULATED",
        "readings": [
            {
                "source": item["source"],
                "name": item["name"],
                "value": item["value"],
                "quality": item.get("quality", "unknown"),
            }
            for item in snapshots
        ],
        "assertion": "Synthetic observations from local fixtures. No live Cisco, BMS, booking or historian connection.",
        "graphRefs": list(intent["valueIntent"]["primaryRefIds"]),
        "confounders": list(intent["evidence"]["confounders"]),
        "staleSignals": [item["name"] for item in stale],
    }


def context(intent: dict) -> dict:
    return {
        "name": "Value graph context",
        "evidenceStatus": "ILLUSTRATIVE",
        "sourcePack": intent["packId"],
        "linkedNodes": [node["id"] for node in intent["graph"]["nodes"]],
        "boardPriorities": intent["valueIntent"]["boardObjectives"],
        "owner": intent["valueIntent"]["owner"],
        "graphRefs": list(intent["valueIntent"]["primaryRefIds"]),
        "assertion": "This joins the event to the design-time graph. It is not a causal finding.",
    }


def value(intent: dict) -> dict:
    claimed = intent.get("evidence", {}).get("claimedRealised")
    return {
        "name": "Hypothesis evaluation",
        "evidenceStatus": "UNVALIDATED",
        "hypothesis": intent["valueIntent"]["hypothesis"],
        "metric": intent["valueIntent"]["metric"],
        "baseline": intent["valueIntent"]["baselineText"],
        "target": intent["valueIntent"]["targetText"],
        "confidence": "UNVALIDATED",
        "counterfactualNeeded": True,
        "certifiedBenefit": None,
        "realisedValue": None,
        "ignoredClaim": claimed,
        "graphRefs": [item["id"] for item in intent["valueIntent"]["hypotheses"]],
        "assertion": "Modelled benefit stays unvalidated until an independent measurement is accepted.",
    }


def plan(intent: dict) -> dict:
    scene = intent["presentation"]["scene"]
    options = list(_PLAN_OPTIONS.get(scene) or ["Review and create a work order"])
    return {
        "name": "Bounded intervention options",
        "evidenceStatus": "PROPOSED",
        "options": options,
        "selectedOption": options[0],
        "physicalCommands": False,
        "sideEffectsToCheck": ["comfort and safety", "operational continuity", "data confidentiality"],
        "graphRefs": [item["id"] for item in intent["valueIntent"]["hypotheses"]],
        "planHash": hashlib.sha256(
            json.dumps(options, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def guard(intent: dict) -> dict:
    policy = intent["governance"]
    allowed = set(policy["allowedActions"])
    forbidden = set(policy["deniedActions"])
    safe = (
        policy["mode"] == "SHADOW"
        and policy["externalSystemsEnabled"] is False
        and "draft_work_order" in allowed
        and set(DENIED_ACTIONS) <= forbidden
        and policy["approval"]["required"] is True
        and allowed.isdisjoint(forbidden)
    )
    return {
        "name": "Deterministic policy gate",
        "evidenceStatus": "POLICY",
        "passed": safe,
        "mode": policy["mode"],
        "approvalRequired": True,
        "approverRole": policy["approval"]["role"],
        "blockedCommands": sorted(forbidden),
        "canExecutePhysicalControls": False,
        "graphRefs": list(intent["valueIntent"]["primaryRefIds"]),
    }


def act(intent: dict, run_id: str) -> dict:
    return {
        "name": "Work-order draft (no external write)",
        "evidenceStatus": "SIMULATED",
        "ticketType": "SIMULATED_WORK_ORDER",
        "idempotencyKey": f"{run_id}:work-order",
        "status": "DRAFTED_ONLY",
        "externalSystemWritten": False,
        "physicalCommands": False,
        "actionSummary": "Request a human-led operational review for " + intent["presentation"]["title"],
        "graphRefs": list(intent["valueIntent"]["primaryRefIds"]),
    }


def verify(intent: dict) -> dict:
    return {
        "name": "Independent outcome ledger",
        "evidenceStatus": "NOT_MEASURED",
        "verificationState": "NOT_MEASURED",
        "realisedValue": None,
        "measurementStatus": "AWAITING_REAL_BASELINE_AND_OBSERVATION",
        "nextAction": "Gather before/after outcome evidence with controls and an agreed measurement period",
        "attribution": "NOT_ESTABLISHED",
        "graphRefs": [item["id"] for item in intent["valueIntent"]["metricRefs"]],
        "assertion": "A simulated work order is not a measured customer outcome.",
    }


HANDLERS = {
    "sense": sense,
    "context": context,
    "value": value,
    "plan": plan,
    "guard": guard,
    "act": act,
    "verify": verify,
}

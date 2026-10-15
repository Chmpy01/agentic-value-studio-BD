"""Compile a design-time pack and a runtime scenario into cvs.intent/v1.

Provenance: graph join and governance defaults follow
reference_projects/agent_runtime/compiler.py. The output schema is ours.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from studio.config import ALLOWED_ACTIONS, DENIED_ACTIONS, PACKS, REFERENCE

ROLES = [
    ("sense", "Signal Steward", "read-only", "Collect signals; inspect provenance and freshness"),
    ("context", "Context Resolver", "read-only", "Join the event to the value graph and the accountable owner"),
    ("value", "Value Reasoner", "recommend", "State a hypothesis without claiming cause or a realised saving"),
    ("plan", "Intervention Planner", "recommend", "Offer alternatives, assumptions and risk controls"),
    ("guard", "Policy and Risk Gate", "deterministic", "Allow only a simulated ticket inside the shadow boundary"),
    ("act", "Action Broker", "simulated-ticket", "Draft a local work order after a bound human approval"),
    ("verify", "Outcome Auditor", "read-only", "Record the outcome as not measured"),
]

CONFOUNDERS = [
    "weather and occupancy mix",
    "bookings, safety overrides and schedule exceptions",
    "asset operating state and sensor health",
]


class ContractError(ValueError):
    pass


def design_path(pack: str) -> Path:
    return REFERENCE / "value_studio" / "packs" / f"{pack}.json"


def scenario_path(pack: str) -> Path:
    return REFERENCE / "agent_runtime" / "data" / "scenarios" / f"{pack}-runtime.json"


def legacy_manifest_path(pack: str) -> Path:
    return REFERENCE / "agent_runtime" / "manifests" / f"{pack}.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_design(design: dict) -> list[str]:
    errors: list[str] = []
    nodes = design.get("nodes") or []
    seen: list[str] = []
    for node in nodes:
        node_id = node.get("id")
        if not node_id:
            errors.append("node without id")
            continue
        if node_id in seen:
            errors.append(f"duplicate node id {node_id}")
        seen.append(node_id)
    ids = set(seen)
    for edge in design.get("edges") or []:
        if edge.get("from") not in ids or edge.get("to") not in ids:
            errors.append(f"broken edge {edge.get('from')} -> {edge.get('to')}")
    for scene in design.get("story") or []:
        for node_id in scene.get("focusNodeIds") or []:
            if node_id not in ids:
                errors.append(f"story {scene.get('id')} references missing node {node_id}")
    return errors


def _canonical(document: dict) -> bytes:
    body = {key: value for key, value in document.items() if key != "intentHash"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def intent_hash(document: dict) -> str:
    return hashlib.sha256(_canonical(document)).hexdigest()


def compile_documents(design: dict, scenario: dict, *, design_name: str = "", scenario_name: str = "") -> dict:
    errors = validate_design(design)
    if errors:
        raise ContractError("; ".join(errors))
    if design.get("packId") != scenario.get("enterprisePackRef", {}).get("packId"):
        raise ContractError("design packId does not match scenario enterprisePackRef.packId")
    if scenario.get("packId") and design.get("packId") and scenario.get("scene") not in {None, design.get("packId")}:
        # scene is the industry key and matches pack id in the supplied files
        if scenario.get("scene") != design.get("packId"):
            raise ContractError("scenario scene does not match design pack")
    nodes = {node["id"]: node for node in design["nodes"]}
    links = list(scenario["enterprisePackRef"]["nodeIds"])
    missing = [node_id for node_id in links if node_id not in nodes]
    if missing:
        raise ContractError(f"scenario references missing design nodes: {missing}")
    selected_edges = [edge for edge in design["edges"] if edge["from"] in links or edge["to"] in links]
    selected_ids = set(links)
    for edge in selected_edges:
        selected_ids.update((edge["from"], edge["to"]))
    subnodes = [dict(nodes[node_id]) for node_id in nodes if node_id in selected_ids]
    objectives = [node for node in subnodes if node["type"] == "board"]
    hypotheses = [node for node in subnodes if node["type"] == "hypothesis"]
    metrics = [node for node in subnodes if node["type"] == "metric"]
    sources = [node for node in subnodes if node["type"] == "source"]
    intent_body = scenario["valueIntent"]
    document = {
        "schemaVersion": "cvs.intent/v1",
        "kind": "ValueIntent",
        "packId": design["packId"],
        "intentVersion": "0.1.0",
        "status": "synthetic/unvalidated",
        "source": {
            "designPackId": design["packId"],
            "runtimePackId": scenario["packId"],
            "designName": design_name,
            "scenarioName": scenario_name,
        },
        "valueIntent": {
            "boardObjectives": [{"id": node["id"], "name": node["title"]} for node in objectives],
            "owner": intent_body["accountableOwner"],
            "metric": intent_body["metric"],
            "baselineText": intent_body["baseline"],
            "targetText": intent_body["target"],
            "hypothesis": intent_body["benefitHypothesis"],
            "valueStatus": "UNVALIDATED",
            "approvalAuthority": intent_body["approvalAuthority"],
            "riskBoundary": intent_body["riskBoundary"],
            "objective": intent_body["objective"],
            "hypotheses": [{"id": node["id"], "name": node["title"]} for node in hypotheses],
            "metricRefs": [{"id": node["id"], "name": node["title"]} for node in metrics],
            "primaryRefIds": links,
        },
        "evidence": {
            "sources": [{"id": node["id"], "name": node["title"]} for node in sources],
            "snapshots": scenario["signalSnapshot"],
            "provenance": "synthetic",
            "confounders": list(CONFOUNDERS),
            "verification": "counterfactual required; no benefit certified",
            "evidenceStatus": "NOT_MEASURED",
        },
        "graph": {"nodes": subnodes, "edges": selected_edges, "primaryRefIds": links},
        "agentPlan": {
            "strategy": "coordinator-with-role-handlers",
            "agents": [
                {"id": role, "title": title, "authority": authority, "purpose": purpose}
                for role, title, authority, purpose in ROLES
            ],
            "flow": ["sense", "context", "value", "plan", "guard", "human-approval", "act", "verify"],
        },
        "governance": {
            "mode": "SHADOW",
            "minimumEvidence": "customer-verified before financial claim",
            "approval": {"required": True, "role": intent_body["approvalAuthority"]},
            "allowedActions": list(ALLOWED_ACTIONS),
            "deniedActions": list(DENIED_ACTIONS),
            "riskBoundary": intent_body["riskBoundary"],
            "externalSystemsEnabled": False,
        },
        "commercial": {
            "customer": {
                "objective": intent_body["objective"],
                "hypothesis": intent_body["benefitHypothesis"],
                "status": "NOT_MEASURED",
            },
            "partner": {"role": scenario.get("partnerRole"), "status": "commercial-hypothesis"},
            "cisco": {
                "capabilityPositioning": scenario.get("ciscoRole"),
                "status": "capability-hypothesis",
            },
            "separation": "Customer benefit, partner revenue and Cisco opportunity are not additive.",
        },
        "runtime": {
            "eventSource": "embedded-synthetic-snapshot",
            "eventTimeoutSeconds": 15,
            "idempotencyRequired": True,
            "auditRequired": True,
            "outcomeState": "NOT_MEASURED",
        },
        "presentation": {
            "title": scenario["title"],
            "subtitle": scenario.get("subtitle") or design.get("subtitle"),
            "scene": scenario["scene"],
            "industry": scenario.get("industry") or design.get("industry"),
            "name": design.get("name"),
            "accent": (design.get("theme") or {}).get("accent", "#2378ed"),
            "imagePath": (design.get("scene") or {}).get("imagePath"),
            "workflow": scenario.get("workflow") or [],
        },
    }
    document["intentHash"] = intent_hash(document)
    return document


def compile_pack(pack: str) -> dict:
    if pack not in PACKS:
        raise ContractError(f"unrecognised pack {pack}")
    return compile_documents(
        load_json(design_path(pack)),
        load_json(scenario_path(pack)),
        design_name=f"reference_projects/value_studio/packs/{pack}.json",
        scenario_name=f"reference_projects/agent_runtime/data/scenarios/{pack}-runtime.json",
    )


def load_legacy(pack: str) -> dict:
    if pack not in PACKS:
        raise ContractError(f"unrecognised pack {pack}")
    return load_json(legacy_manifest_path(pack))


def assert_legacy_safe(manifest: dict) -> None:
    if manifest.get("governance", {}).get("externalSystemsEnabled") is not False:
        raise ContractError("legacy manifest enables external systems")
    if manifest.get("runtime", {}).get("outcomeState") != "NOT_MEASURED":
        raise ContractError("legacy manifest outcome is not NOT_MEASURED")
    denied = set(manifest.get("governance", {}).get("deniedActions") or [])
    if not set(DENIED_ACTIONS) <= denied:
        raise ContractError("legacy manifest is missing a denied physical action")

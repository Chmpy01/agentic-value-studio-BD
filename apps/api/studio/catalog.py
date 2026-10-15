"""Read-only views over the supplied packs, navigation and interop flags."""
from __future__ import annotations

import json

from studio.compiler import (
    ContractError,
    assert_legacy_safe,
    compile_pack,
    design_path,
    load_json,
    load_legacy,
    scenario_path,
    validate_design,
)
from studio.config import CONTRACTS, DATA, PACKS, REFERENCE, agntcy_directory_enabled, a2a_url
from studio.transport import a2a_health


def navigation() -> dict:
    return json.loads((DATA / "navigation.json").read_text())


def oasf_record() -> dict:
    return json.loads((DATA / "oasf" / "context-resolver.record.json").read_text())


def interop() -> dict:
    health = a2a_health()
    return {
        "a2a": {
            "configuredUrl": a2a_url(),
            "reachable": health["reachable"],
            "protocol": "Agent Card at /.well-known/agent-card.json plus JSON-RPC method message/send",
            "scope": "Context Resolver only. Other roles stay in-process.",
            "error": health.get("error"),
        },
        "agntcyDirectory": {
            "enabled": agntcy_directory_enabled(),
            "status": "not-connected",
            "reason": "AGNTCY_DIRECTORY_ENABLED is off. Directory publishes agent metadata; it does not run this workflow.",
        },
        "slim": {
            "enabled": False,
            "status": "not-used",
            "reason": "One optional HTTP agent does not need SLIM group transport.",
        },
        "logicalRolesAreNotIndependentAgents": True,
    }


def module_lineage(pack: str) -> list[str]:
    folder = REFERENCE / "value_studio" / "modules" / pack
    if not folder.is_dir():
        return []
    return [f"reference_projects/value_studio/modules/{pack}/{path.name}" for path in sorted(folder.glob("*.json"))]


def pack_summary(pack: str) -> dict:
    design = load_json(design_path(pack))
    return {
        "id": pack,
        "name": design["name"],
        "industry": design["industry"],
        "accent": design["theme"]["accent"],
        "status": design["status"],
    }


def pack_detail(pack: str) -> dict:
    design = load_json(design_path(pack))
    scenario = load_json(scenario_path(pack))
    intent = compile_pack(pack)
    legacy = load_legacy(pack)
    assert_legacy_safe(legacy)
    health = a2a_health()
    agents = []
    for agent in intent["agentPlan"]["agents"]:
        if agent["id"] == "context" and health["reachable"]:
            hosting = "independent A2A service"
            placement = "remote-process"
        elif agent["id"] == "context":
            hosting = "in-process logical handler (A2A service not running)"
            placement = "in-process"
        else:
            hosting = "in-process logical handler"
            placement = "in-process"
        agents.append({**agent, "hosting": hosting, "placement": placement})
    agents.append(
        {
            "id": "human",
            "title": intent["governance"]["approval"]["role"],
            "authority": "human-approval",
            "purpose": "Approve or reject a simulated work-order draft. Does not approve physical control.",
            "hosting": "human decision",
            "placement": "human",
        }
    )
    return {
        "design": design,
        "scenario": {
            "packId": scenario["packId"],
            "title": scenario["title"],
            "subtitle": scenario.get("subtitle"),
            "status": scenario["status"],
            "connectors": scenario.get("connectors"),
            "stakeholders": scenario.get("stakeholders"),
            "valueIntent": scenario["valueIntent"],
            "signalSnapshot": scenario["signalSnapshot"],
            "partnerRole": scenario.get("partnerRole"),
            "ciscoRole": scenario.get("ciscoRole"),
            "workflow": scenario["workflow"],
            "outcome": scenario["outcome"],
            "controls": scenario["controls"],
            "provenance": scenario["provenance"],
            "enterprisePackRef": scenario["enterprisePackRef"],
        },
        "intent": intent,
        "legacy": {
            "apiVersion": legacy.get("apiVersion"),
            "sha256": legacy.get("metadata", {}).get("sha256"),
            "outcomeState": legacy["runtime"]["outcomeState"],
            "externalSystemsEnabled": legacy["governance"]["externalSystemsEnabled"],
        },
        "validation": {"ok": True, "errors": validate_design(design)},
        "lineage": {
            "design": f"reference_projects/value_studio/packs/{pack}.json",
            "scenario": f"reference_projects/agent_runtime/data/scenarios/{pack}-runtime.json",
            "legacyManifest": f"reference_projects/agent_runtime/manifests/{pack}.json",
            "modules": module_lineage(pack),
        },
        "network": agents,
        "imageUrl": f"/media/{pack}.webp",
    }


def validate_upload(document: dict) -> dict:
    if document.get("schemaVersion") == "cvs.intent/v1" or document.get("kind") == "ValueIntent":
        errors = []
        governance = document.get("governance") or {}
        if governance.get("externalSystemsEnabled") is not False:
            errors.append("externalSystemsEnabled must be false")
        denied = set(governance.get("deniedActions") or [])
        from studio.config import DENIED_ACTIONS

        if not set(DENIED_ACTIONS) <= denied:
            errors.append("deniedActions is missing a physical write")
        if document.get("runtime", {}).get("outcomeState") != "NOT_MEASURED":
            errors.append("outcomeState must be NOT_MEASURED")
        if document.get("valueIntent", {}).get("valueStatus") == "REALISED":
            errors.append("valueStatus REALISED is not accepted from an upload")
        return {"ok": not errors, "errors": errors, "kind": "intent"}
    try:
        errors = validate_design(document)
    except ContractError as exc:
        errors = [str(exc)]
    if "nodes" not in document or "edges" not in document:
        errors.append("a design pack needs nodes and edges")
    return {"ok": not errors, "errors": errors, "kind": "design-pack", "nodeCount": len(document.get("nodes") or [])}


def media_path(pack: str):
    if pack not in PACKS:
        return None
    path = REFERENCE / "value_studio" / "assets" / f"{pack}.webp"
    return path if path.is_file() else None


def contract_schema(name: str) -> dict:
    path = CONTRACTS / name
    return json.loads(path.read_text())

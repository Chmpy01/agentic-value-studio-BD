"""Project-authored overlay per pack: personas, outcome synergies, synthetic signal scenarios.

The supplied design pack is never modified. Every overlay reference must resolve to a
node of the expected type in that pack, otherwise the overlay is rejected.
"""
from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from studio.compiler import ContractError, design_path, load_json
from studio.config import CONTRACTS, DATA

_VALIDATOR = Draft202012Validator(json.loads((CONTRACTS / "pack-overlay.schema.json").read_text()))


def overlay_path(pack: str):
    return DATA / "overlays" / f"{pack}.json"


def validate_overlay(overlay: dict, design: dict) -> list[str]:
    errors = [f"{'/'.join(str(p) for p in error.path) or 'overlay'}: {error.message}" for error in _VALIDATOR.iter_errors(overlay)]
    if errors:
        return errors
    if overlay["packId"] != design.get("packId"):
        errors.append(f"overlay packId {overlay['packId']} does not match design {design.get('packId')}")
    types = {node["id"]: node["type"] for node in design.get("nodes", [])}

    def expect(ref: str, kind: str | None, where: str) -> None:
        if ref not in types:
            errors.append(f"{where}: unknown graph node {ref}")
        elif kind and types[ref] != kind:
            errors.append(f"{where}: {ref} is a {types[ref]}, expected {kind}")

    seen: set[str] = set()
    for persona in overlay["personas"]:
        where = f"persona {persona['id']}"
        if persona["id"] in seen or persona["id"] in types:
            errors.append(f"{where}: duplicate id")
        seen.add(persona["id"])
        expect(persona["functionId"], "function", where)
        for ref in persona["signalIds"]:
            expect(ref, "signal", where)
        for ref in persona["hypothesisIds"]:
            expect(ref, "hypothesis", where)
    for synergy in overlay["synergies"]:
        where = f"synergy {synergy['id']}"
        if synergy["id"] in seen or synergy["id"] in types:
            errors.append(f"{where}: duplicate id")
        seen.add(synergy["id"])
        for ref in synergy["hypothesisIds"]:
            expect(ref, "hypothesis", where)
        for ref in synergy["bridgeNodeIds"]:
            expect(ref, None, where)
    scenario_ids: set[str] = set()
    for scenario in overlay["reasoning"]["scenarios"]:
        where = f"scenario {scenario['id']}"
        if scenario["id"] in scenario_ids:
            errors.append(f"{where}: duplicate id")
        scenario_ids.add(scenario["id"])
        for reading in scenario["readings"]:
            expect(reading["signalId"], "signal", f"{where} reading {reading['id']}")
            expect(reading["sourceId"], "source", f"{where} reading {reading['id']}")
    return errors


def load_overlay(pack: str) -> dict:
    overlay = load_json(overlay_path(pack))
    errors = validate_overlay(overlay, load_json(design_path(pack)))
    if errors:
        raise ContractError("; ".join(errors))
    return overlay

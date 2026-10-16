"""Read-only access to the local research corpus.

There is no network call here and no live retrieval. The corpus is a set of
labelled local files. Every statement carries an evidence class, a confidence
and a source reference, so the discovery agent can cite rather than assert.
"""
from __future__ import annotations

import json

from studio.config import DATA

RESEARCH = DATA / "research"


class ResearchError(ValueError):
    pass


def _read(name: str) -> dict:
    path = RESEARCH / name
    if not path.is_file():
        raise ResearchError(f"missing research file {name}")
    return json.loads(path.read_text())


def template() -> dict:
    return _read("cvs_template.json")


def source_register() -> dict:
    return _read("sources.json")


def corpus() -> dict:
    return _read("corpus.json")


def sources_for(pack: str | None = None) -> list[dict]:
    register = source_register()["sources"]
    if pack is None:
        return register
    return [item for item in register if pack in item["industries"]]


def source_index() -> dict[str, dict]:
    return {item["id"]: item for item in source_register()["sources"]}


def industry(pack: str) -> dict:
    industries = corpus()["industries"]
    if pack not in industries:
        raise ResearchError(f"no research corpus for {pack}")
    return industries[pack]


def validation_status_for(evidence_type: str) -> str:
    mapping = template()["evidenceModel"]["statusByEvidenceType"]
    if evidence_type not in mapping:
        raise ResearchError(f"unknown evidence type {evidence_type}")
    return mapping[evidence_type]


def coverage(pack: str) -> dict:
    """How much of this pack rests on each evidence class. Used to stop over-claiming."""
    data = industry(pack)
    counts: dict[str, int] = {}

    def tally(evidence_type: str) -> None:
        counts[evidence_type] = counts.get(evidence_type, 0) + 1

    tally(data["industryContext"]["evidenceType"])
    for item in data["industryContext"]["pressures"]:
        tally(item["evidenceType"])
    for item in data["industryValueStreams"]:
        tally(item["evidenceType"])
    for item in data["customerReportExtracts"]:
        tally(item["evidenceType"])
    for item in data["customerValueStreams"]:
        tally(item["evidenceType"])
    for item in data["organisation"]["functions"]:
        tally(item["evidenceType"])
    for item in data["organisation"]["personas"]:
        tally(item["evidenceType"])
    for _ in data["unknowns"]:
        tally("unknown")
    return {
        "counts": counts,
        "total": sum(counts.values()),
        "validatedShare": round(counts.get("validated", 0) / max(1, sum(counts.values())), 3),
    }

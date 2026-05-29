"""Structured JSON export of an analysis. Pure (takes plain dicts)."""
from __future__ import annotations

from typing import Any


def export_json(analysis: dict, findings: list[dict], entities: list[dict],
                relationships: list[dict], risks: list[dict],
                warnings: list[dict], collectors: list[dict]) -> dict[str, Any]:
    return {
        "analysis": analysis,
        "summary": analysis.get("summary_json"),
        "exposure_score": analysis.get("exposure_score_json"),
        "findings": findings,
        "entities": entities,
        "relationships": relationships,
        "risk_hypotheses": risks,
        "warnings": warnings,
        "collectors": collectors,
    }

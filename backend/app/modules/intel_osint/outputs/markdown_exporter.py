"""Markdown summary export of an analysis. Pure (takes plain dicts)."""
from __future__ import annotations


def export_markdown(analysis: dict, findings: list[dict], entities: list[dict],
                    risks: list[dict], warnings: list[dict]) -> str:
    summary = analysis.get("summary_json") or {}
    exposure = analysis.get("exposure_score_json") or {}
    kpis = summary.get("kpis", {})

    lines: list[str] = []
    lines.append(f"# Intelligence Report — {analysis.get('target_company_name', '')}")
    if analysis.get("target_root_domain"):
        lines.append(f"**Domain:** {analysis['target_root_domain']}  ")
    lines.append(f"**Status:** {analysis.get('status')}  ")
    lines.append(f"**Depth:** {analysis.get('depth')}  ")
    lines.append(f"**Overall exposure:** {exposure.get('overall', 0)}/100\n")

    lines.append("## Executive summary\n")
    lines.append(summary.get("executive_summary", "_n/a_") + "\n")

    lines.append("## Key metrics\n")
    for k, v in kpis.items():
        lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
    lines.append("")

    lines.append("## Exposure by category\n")
    for cat, data in (exposure.get("categories") or {}).items():
        lines.append(f"- **{cat.replace('_', ' ').title()}:** {data.get('score')}/100 "
                     f"(confidence: {data.get('confidence')})")
    lines.append("")

    lines.append("## Risk hypotheses\n")
    if not risks:
        lines.append("_None generated._\n")
    for r in risks:
        lines.append(f"### {r.get('title')} ({r.get('risk_level')}, {r.get('confidence')})")
        lines.append(r.get("description") or "")
        if r.get("why_it_matters"):
            lines.append(f"- **Why it matters:** {r['why_it_matters']}")
        if r.get("recommended_validation"):
            lines.append(f"- **Validate:** {r['recommended_validation']}")
        if r.get("recommended_remediation"):
            lines.append(f"- **Remediate:** {r['recommended_remediation']}")
        lines.append("")

    if warnings:
        lines.append("## Collector warnings\n")
        for w in warnings:
            lines.append(f"- [{w.get('collector', '-')}] {w.get('message')}")
        lines.append("")

    lines.append(f"## Findings ({len(findings)})\n")
    lines.append("| Title | Type | Risk | Confidence | Source |")
    lines.append("|---|---|---|---|---|")
    for f in findings[:200]:
        lines.append(f"| {f.get('title','')} | {f.get('type','')} | {f.get('risk_level','')} "
                     f"| {f.get('confidence','')} | {f.get('source','')} |")
    lines.append("")
    return "\n".join(lines)

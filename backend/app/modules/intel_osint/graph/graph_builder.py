"""Build a simple node/edge graph from entities + relationships. Pure."""
from __future__ import annotations

from typing import Any


def build_graph(entities: list[dict], relationships: list[dict]) -> dict[str, Any]:
    nodes: dict[str, dict] = {}

    def add_node(value: str, ntype: str) -> None:
        if not value:
            return
        if value not in nodes:
            nodes[value] = {"id": value, "label": value, "type": ntype}

    for e in entities:
        add_node(e.get("normalized_value") or e.get("value"), e.get("entity_type", "unknown"))

    edges = []
    for r in relationships:
        s = r.get("source_value")
        t = r.get("target_value")
        if not s or not t:
            continue
        add_node(s, "domain")
        add_node(t, "unknown")
        edges.append({"source": s, "target": t,
                      "type": r.get("relationship_type", "related"),
                      "confidence": r.get("confidence", "medium")})

    return {"nodes": list(nodes.values()), "edges": edges,
            "counts": {"nodes": len(nodes), "edges": len(edges)}}

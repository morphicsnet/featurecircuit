from __future__ import annotations

from typing import Any


def structure_to_hif_v0(structure_artifact: dict[str, Any]) -> dict[str, Any]:
    nodes = set()
    hyperedges = []
    for idx, struct in enumerate(structure_artifact.get("structures", [])):
        members = [str(m) for m in struct.get("members", [])]
        if len(members) < 2:
            continue
        for m in members:
            nodes.add(m)
        hyperedges.append(
            {
                "id": f"he_{idx}",
                "nodes": sorted(members),
                "count": int(struct.get("support_count", 0)),
            }
        )
    return {
        "schema": "HIF-v0",
        "nodes": [{"id": n} for n in sorted(nodes)],
        "hyperedges": hyperedges,
    }


def structure_to_hif_legacy_demo(structure_artifact: dict[str, Any]) -> dict[str, Any]:
    edge_rows = []
    node_ints = set()
    for idx, struct in enumerate(structure_artifact.get("structures", [])):
        members = [int(m) for m in struct.get("members", [])]
        if len(members) < 2:
            continue
        members = sorted(set(members))
        node_ints.update(members)
        edge_rows.append(
            {
                "id": idx,
                "key": members,
                "observation_count": int(struct.get("support_count", 0)),
                "stii_weight": float(struct.get("stability_score", 0.0)),
            }
        )
    incidences = [{"edge": e["id"], "nodes": e["key"]} for e in edge_rows]
    return {
        "network-type": "hypergraph",
        "nodes": [{"id": i} for i in sorted(node_ints)],
        "edges": edge_rows,
        "incidences": incidences,
    }

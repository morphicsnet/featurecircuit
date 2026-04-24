from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from mair.manifest import load_manifest
except Exception as exc:  # pragma: no cover - exercised in integration usage
    load_manifest = None  # type: ignore
    _IMPORT_ERROR = exc


def _load_artifact(manifest_path: Path, artifact_type: str) -> dict[str, Any]:
    if load_manifest is None:
        raise RuntimeError(
            "MAIR bridge requires the installed mechlab-sdk runtime. "
            "Run python -m pip install mechlab-sdk and ensure the bundled MAIR helpers are importable."
        ) from _IMPORT_ERROR
    manifest = load_manifest(manifest_path)
    artifact = next(item for item in manifest["artifacts"] if item["artifact_type"] == artifact_type)
    return json.loads((manifest_path.parent / artifact["path"]).read_text(encoding="utf-8"))


def mair_manifest_to_hif_v0(manifest_path: str | Path) -> dict[str, Any]:
    manifest_file = Path(manifest_path)
    graph_ir = _load_artifact(manifest_file, "mair_graph_ir")
    grouped = _load_artifact(manifest_file, "grouped_clt_bundle")
    nodes = {node["id"] for node in graph_ir.get("nodes", [])}
    hyperedges = []
    for idx, edge in enumerate(graph_ir.get("edges", [])):
        members = sorted({str(edge["source"]), str(edge["target"])})
        nodes.update(members)
        hyperedges.append(
            {
                "id": f"he_{idx}",
                "nodes": members,
                "count": int(round(1 + edge.get("weight", 1.0))),
            }
        )
    offset = len(hyperedges)
    for idx, group in enumerate(grouped.get("groups", []), start=offset):
        members = sorted(node["id"] for node in graph_ir.get("nodes", []) if node.get("block_id") in group["group_id"])
        if not members:
            members = [group["group_id"]]
            nodes.add(group["group_id"])
        hyperedges.append(
            {
                "id": f"he_{idx}",
                "nodes": members,
                "count": int(group.get("size", 0)),
            }
        )
    return {
        "schema": "HIF-v0",
        "nodes": [{"id": node_id} for node_id in sorted(nodes)],
        "hyperedges": hyperedges,
    }


def mair_manifest_to_hif_legacy(manifest_path: str | Path) -> dict[str, Any]:
    modern = mair_manifest_to_hif_v0(manifest_path)
    node_map = {node["id"]: idx for idx, node in enumerate(modern["nodes"])}
    edges = []
    incidences = []
    for idx, edge in enumerate(modern["hyperedges"]):
        key = [node_map[node_id] for node_id in edge["nodes"]]
        edges.append(
            {
                "id": idx,
                "key": key,
                "observation_count": int(edge.get("count", 0)),
                "stii_weight": float(edge.get("count", 0)),
            }
        )
        incidences.append({"edge": idx, "nodes": key})
    return {
        "network-type": "hypergraph",
        "nodes": [{"id": idx} for idx in range(len(modern["nodes"]))],
        "edges": edges,
        "incidences": incidences,
    }

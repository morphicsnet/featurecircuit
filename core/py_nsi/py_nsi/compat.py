"""Compatibility shim for legacy demo-era py_nsi classes.

This module is temporary and scheduled for removal after one consolidation release.
"""

from __future__ import annotations

import json
import os
import warnings
from dataclasses import dataclass
from typing import Iterable

import numpy as np

_COMPAT_TTL = "one consolidation release"
_WARNED: set[str] = set()


def _warn_once(name: str, replacement: str) -> None:
    key = f"{name}->{replacement}"
    if key in _WARNED:
        return
    _WARNED.add(key)
    warnings.warn(
        (
            f"py_nsi.compat.{name} is deprecated and will be removed after {_COMPAT_TTL}. "
            f"Use {replacement} instead."
        ),
        DeprecationWarning,
        stacklevel=3,
    )


class PySimpleSaeEncoder:
    """Python fallback implementation matching legacy demo behavior."""

    def __init__(self, in_dim: int, out_dim: int, top_k: int, seed: int) -> None:
        _warn_once("PySimpleSaeEncoder", "py_nsi.EnsembleEncoder")
        if in_dim <= 0 or out_dim <= 0:
            raise ValueError("in_dim and out_dim must be > 0")
        if top_k < 0 or top_k > out_dim:
            raise ValueError("top_k must satisfy 0 <= top_k <= out_dim")
        self.in_dim = int(in_dim)
        self.out_dim = int(out_dim)
        self.top_k = int(top_k)
        self.seed = int(seed)
        rng = np.random.default_rng(self.seed)
        self.weights = rng.uniform(-0.1, 0.1, size=(self.out_dim, self.in_dim)).astype(np.float32)
        self.biases = rng.uniform(-0.01, 0.01, size=(self.out_dim,)).astype(np.float32)

    def encode(self, activations: list[float]) -> list[float]:
        x = np.asarray(activations, dtype=np.float32)
        if x.ndim != 1 or x.shape[0] != self.in_dim:
            return [0.0 for _ in range(self.out_dim)]
        y = np.maximum(self.weights @ x + self.biases, 0.0)
        k = min(max(self.top_k, 0), self.out_dim)
        if k == 0:
            return [0.0 for _ in range(self.out_dim)]
        if k < self.out_dim:
            order = sorted(range(self.out_dim), key=lambda i: (-float(y[i]), i))
            keep = set(order[:k])
            for i in range(self.out_dim):
                if i not in keep:
                    y[i] = 0.0
        return [float(v) for v in y.tolist()]


class PyEnsemble:
    def __init__(self, encoders: list[PySimpleSaeEncoder]) -> None:
        _warn_once("PyEnsemble", "py_nsi.EnsembleEncoder")
        self.encoders = list(encoders)

    def encode_all(self, activations: list[float]) -> list[list[float]]:
        return [enc.encode(activations) for enc in self.encoders]

    def intersect(self, outputs: list[list[float]], threshold: float) -> list[bool]:
        if not outputs:
            return []
        m = min(len(o) for o in outputs)
        out = []
        for i in range(m):
            out.append(all(float(o[i]) > float(threshold) for o in outputs))
        return out


@dataclass
class PySpike:
    ensemble_id: int
    neuron_id: int
    t: float

    def __post_init__(self) -> None:
        _warn_once("PySpike", "py_nsi.SpikeEvent")

    def node_id(self) -> int:
        return ((int(self.ensemble_id) & 0xFFFF) << 32) | (int(self.neuron_id) & 0xFFFFFFFF)


class PyGse:
    def __init__(self, window: float) -> None:
        _warn_once("PyGse", "py_nsi.GraphStreamingEngine")
        self.window = max(float(window), 0.0)
        self.buffer: list[PySpike] = []

    def ingest(self, spike: PySpike) -> list[list[PySpike]]:
        t_now = float(spike.t)
        self.buffer.append(spike)
        self.buffer = [s for s in self.buffer if (t_now - float(s.t)) <= self.window]
        latest_by_ens: dict[int, PySpike] = {}
        for s in reversed(self.buffer):
            if (t_now - float(s.t)) > self.window:
                break
            if int(s.ensemble_id) not in latest_by_ens:
                latest_by_ens[int(s.ensemble_id)] = s
        if len(latest_by_ens) < 2:
            return []
        island = sorted(latest_by_ens.values(), key=lambda s: int(s.node_id()))
        return [island]


class PyHypergraphStore:
    def __init__(self) -> None:
        _warn_once("PyHypergraphStore", "py_nsi.HypergraphStore")
        self._edges: dict[tuple[int, ...], dict[str, float | int]] = {}

    def add_island(self, island: Iterable[PySpike]) -> None:
        node_ids = sorted({int(s.node_id()) for s in island})
        if len(node_ids) < 2:
            return
        key = tuple(node_ids)
        row = self._edges.setdefault(key, {"observation_count": 0, "stii_weight": 0.0})
        row["observation_count"] = int(row["observation_count"]) + 1

    def compute_stii(self, node_ids: list[int], deltas: list[tuple[int, float]]) -> float:
        key = tuple(sorted(int(n) for n in node_ids))
        num = 0.0
        den = 0.0
        for w, v in deltas:
            if int(w) > 0:
                num += float(w) * float(v)
                den += float(w)
        stii = (num / den) if den > 0.0 else 0.0
        row = self._edges.setdefault(key, {"observation_count": 0, "stii_weight": 0.0})
        row["stii_weight"] = float(stii)
        return float(stii)

    def edges(self) -> list[dict[str, object]]:
        rows = []
        for key in sorted(self._edges.keys()):
            row = self._edges[key]
            rows.append(
                {
                    "key": list(key),
                    "observation_count": int(row.get("observation_count", 0)),
                    "stii_weight": float(row.get("stii_weight", 0.0)),
                }
            )
        return rows

    def export_hif(self, path: str) -> None:
        payload = self._legacy_hif_payload()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

    def export_hif_legacy_demo(self, path: str) -> None:
        self.export_hif(path)

    def export_hif_v0(self, path: str) -> None:
        node_ids = sorted({n for k in self._edges.keys() for n in k})
        hyperedges = []
        for i, key in enumerate(sorted(self._edges.keys())):
            row = self._edges[key]
            hyperedges.append(
                {
                    "id": f"he_{i}",
                    "nodes": [f"n:{n}" for n in key],
                    "count": int(row.get("observation_count", 0)),
                }
            )
        payload = {
            "schema": "HIF-v0",
            "nodes": [{"id": f"n:{n}"} for n in node_ids],
            "hyperedges": hyperedges,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

    def _legacy_hif_payload(self) -> dict[str, object]:
        node_ids = sorted({n for k in self._edges.keys() for n in k})
        sorted_keys = sorted(self._edges.keys())
        edges = []
        incidences = []
        for eid, key in enumerate(sorted_keys):
            row = self._edges[key]
            edge_obj = {
                "id": eid,
                "key": list(key),
                "observation_count": int(row.get("observation_count", 0)),
                "stii_weight": float(row.get("stii_weight", 0.0)),
            }
            edges.append(edge_obj)
            incidences.append({"edge": eid, "nodes": list(key)})
        return {
            "network-type": "hypergraph",
            "nodes": [{"id": int(n)} for n in node_ids],
            "edges": edges,
            "incidences": incidences,
        }


__all__ = [
    "PySimpleSaeEncoder",
    "PyEnsemble",
    "PySpike",
    "PyGse",
    "PyHypergraphStore",
]

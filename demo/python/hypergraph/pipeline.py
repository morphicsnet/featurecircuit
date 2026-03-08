from __future__ import annotations

from typing import Dict, List, Set, Tuple

import numpy as np


def _require_py_nsi():
    try:
        from py_nsi import GraphStreamingEngine, HypergraphStore  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "py_nsi is not importable. Build the local Rust wheel first:\n"
            "  maturin develop --release -m core/py_nsi/Cargo.toml\n"
            "Then re-run the demo."
        ) from e
    return GraphStreamingEngine, HypergraphStore


def node_id_u64(encoder_id: int, feature_idx: int) -> int:
    """Canonical 64-bit node id: (encoder_id << 32) | feature_idx."""
    return ((int(encoder_id) & 0xFFFF) << 32) | (int(feature_idx) & 0xFFFFFFFF)


def _island_key(island) -> Tuple[int, ...]:
    node_ids = sorted(
        {
            node_id_u64(int(ev.encoder_id), int(ev.feature_idx))
            for ev in getattr(island, "events", [])
        }
    )
    return tuple(node_ids)


def build_hypergraph_with_nodes(
    ensemble,
    acts: "np.ndarray",
    labels: "np.ndarray",
    t_start: float,
    delta_t: float,
    min_sigmoid: float,
    gse_window: float,
):
    """
    Build temporal-coincidence hypergraph and node-level sample features.

    Returns:
      (store,
       features_by_sample [N, E] bool,
       edge_keys list[tuple[u64]],
       edge_counts dict[tuple[u64], int],
       nodes_by_sample [N, U] bool,
       node_keys list[tuple[u64]])
    """
    GraphStreamingEngine, HypergraphStore = _require_py_nsi()

    if not isinstance(acts, np.ndarray) or acts.ndim != 2:
        raise ValueError("acts must be a 2D numpy array [N, D]")
    if not isinstance(labels, np.ndarray) or labels.ndim != 1:
        raise ValueError("labels must be a 1D numpy array [N]")
    if acts.shape[0] != labels.shape[0]:
        raise ValueError("acts and labels must have the same number of rows")

    N = int(acts.shape[0])
    acts_f32 = acts.astype(np.float32, copy=False)

    from python.encoders.spike import encode_spikes_batch

    store = HypergraphStore()

    edge_keys: List[Tuple[int, ...]] = []
    edge_index: Dict[Tuple[int, ...], int] = {}
    edge_counts: Dict[Tuple[int, ...], int] = {}
    active_cols_per_sample: List[Set[int]] = [set() for _ in range(N)]

    node_sets_per_sample: List[Set[int]] = [set() for _ in range(N)]
    all_nodes: Set[int] = set()

    spikes_per_sample: List[List] = encode_spikes_batch(
        ensemble=ensemble,
        acts=acts_f32,
        t_start=float(t_start),
        delta_t=float(delta_t),
        min_sigmoid=float(min_sigmoid),
    )

    for i in range(N):
        for ev in spikes_per_sample[i]:
            nid = node_id_u64(int(ev.encoder_id), int(ev.feature_idx))
            node_sets_per_sample[i].add(nid)
            all_nodes.add(nid)

    for i in range(N):
        gse = GraphStreamingEngine(float(gse_window))

        for ev in spikes_per_sample[i]:
            islands = gse.ingest(ev)
            sortable = []
            for isl in islands:
                key = _island_key(isl)
                if len(key) < 2:
                    continue
                sortable.append((key, isl))

            sortable.sort(key=lambda x: x[0])
            for key, isl in sortable:
                store.add_island(isl)
                edge_counts[key] = int(edge_counts.get(key, 0)) + 1
                if key not in edge_index:
                    edge_index[key] = len(edge_keys)
                    edge_keys.append(key)
                active_cols_per_sample[i].add(edge_index[key])

    E = len(edge_keys)
    features = np.zeros((N, E), dtype=bool)
    for i, cols in enumerate(active_cols_per_sample):
        if cols:
            idx = np.fromiter(cols, dtype=np.int64, count=len(cols))
            features[i, idx] = True

    node_keys: List[Tuple[int]] = [(nid,) for nid in sorted(all_nodes)]
    node_index: Dict[int, int] = {nid: j for j, (nid,) in enumerate(node_keys)}
    U = len(node_keys)
    nodes_by_sample = np.zeros((N, U), dtype=bool)
    for i, nset in enumerate(node_sets_per_sample):
        if nset:
            idx = np.fromiter((node_index[n] for n in sorted(nset)), dtype=np.int64, count=len(nset))
            nodes_by_sample[i, idx] = True

    return store, features, edge_keys, edge_counts, nodes_by_sample, node_keys


def build_hypergraph(
    ensemble,
    acts: "np.ndarray",
    labels: "np.ndarray",
    t_start: float,
    delta_t: float,
    min_sigmoid: float,
    gse_window: float,
) -> Tuple[object, np.ndarray, List[Tuple[int, ...]], Dict[Tuple[int, ...], int]]:
    """
    Build temporal-coincidence hypergraph and edge-level sample features.

    Returns:
      (store, features_by_sample [N, E] bool, edge_keys list[tuple[u64]], edge_counts)
    """
    GraphStreamingEngine, HypergraphStore = _require_py_nsi()

    if not isinstance(acts, np.ndarray) or acts.ndim != 2:
        raise ValueError("acts must be a 2D numpy array [N, D]")
    if not isinstance(labels, np.ndarray) or labels.ndim != 1:
        raise ValueError("labels must be a 1D numpy array [N]")
    if acts.shape[0] != labels.shape[0]:
        raise ValueError("acts and labels must have the same number of rows")

    N = int(acts.shape[0])
    acts_f32 = acts.astype(np.float32, copy=False)

    from python.encoders.spike import encode_spikes_batch

    store = HypergraphStore()
    edge_keys: List[Tuple[int, ...]] = []
    edge_index: Dict[Tuple[int, ...], int] = {}
    edge_counts: Dict[Tuple[int, ...], int] = {}
    active_cols_per_sample: List[Set[int]] = [set() for _ in range(N)]

    spikes_per_sample: List[List] = encode_spikes_batch(
        ensemble=ensemble,
        acts=acts_f32,
        t_start=float(t_start),
        delta_t=float(delta_t),
        min_sigmoid=float(min_sigmoid),
    )

    for i in range(N):
        gse = GraphStreamingEngine(float(gse_window))
        for ev in spikes_per_sample[i]:
            islands = gse.ingest(ev)
            sortable = []
            for isl in islands:
                key = _island_key(isl)
                if len(key) < 2:
                    continue
                sortable.append((key, isl))

            sortable.sort(key=lambda x: x[0])
            for key, isl in sortable:
                store.add_island(isl)
                edge_counts[key] = int(edge_counts.get(key, 0)) + 1
                if key not in edge_index:
                    edge_index[key] = len(edge_keys)
                    edge_keys.append(key)
                active_cols_per_sample[i].add(edge_index[key])

    E = len(edge_keys)
    features = np.zeros((N, E), dtype=bool)
    for i, cols in enumerate(active_cols_per_sample):
        if cols:
            idx = np.fromiter(cols, dtype=np.int64, count=len(cols))
            features[i, idx] = True

    return store, features, edge_keys, edge_counts

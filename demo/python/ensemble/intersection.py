from __future__ import annotations

import os
from typing import List

import numpy as np


def _require_py_nsi():
    try:
        from py_nsi import EnsembleEncoder  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "py_nsi is not importable. Build the local Rust wheel first:\n"
            "  maturin develop --release -m core/py_nsi/Cargo.toml\n"
            "Then re-run the demo."
        ) from e
    return EnsembleEncoder


def _resolve_input_dim() -> int:
    """
    Determine encoder input dimension. The orchestrator should set:
        os.environ['PY_NSI_INPUT_DIM'] = str(acts.shape[1])
    before calling build_pyensemble(). This keeps the required signature while
    ensuring correctness w.r.t. the model's activation size.
    """
    val = os.environ.get("PY_NSI_INPUT_DIM", "").strip()
    if not val.isdigit():
        raise RuntimeError(
            "PY_NSI_INPUT_DIM environment variable is not set or invalid. "
            "Set it to the activation dimension (acts.shape[1]) before calling build_pyensemble()."
        )
    return int(val)


class ProtocolEnsemble:
    """Canonical ensemble wrapper using solver-style py_nsi API."""

    def __init__(self, input_dim: int, feature_dim: int, top_k: int, seeds: List[int], inner) -> None:
        self.input_dim = int(input_dim)
        self.feature_dim = int(max(1, feature_dim))
        self.top_k = int(max(0, min(top_k, self.feature_dim)))
        self.seeds = [int(s) for s in seeds] if seeds else [0]
        self.inner = inner

        # Deterministic lift from model activation dim -> feature dim.
        rng_seed = (sum(self.seeds) + (self.input_dim * 131) + (self.feature_dim * 17)) & 0xFFFFFFFF
        rng = np.random.default_rng(rng_seed)
        scale = 1.0 / float(max(1, self.input_dim)) ** 0.5
        self.proj = rng.normal(0.0, scale, size=(self.input_dim, self.feature_dim)).astype(np.float32)

    def _project(self, x: np.ndarray) -> np.ndarray:
        if x.ndim != 1 or x.shape[0] != self.input_dim:
            raise ValueError(f"expected 1D activation vector of length {self.input_dim}")
        y = np.matmul(x.astype(np.float32, copy=False), self.proj)
        return np.maximum(y, 0.0).astype(np.float32, copy=False)

    def intersect_mask(self, x: np.ndarray, threshold: float) -> List[bool]:
        y = self._project(x)
        return self.inner.intersect_mask(y.tolist(), float(threshold))

    def masks_by_encoder(self, x: np.ndarray, threshold: float) -> List[List[bool]]:
        y = self._project(x)
        return self.inner.masks_by_encoder(y.tolist(), float(threshold))


def build_pyensemble(feature_dim: int, top_k: int, seeds: List[int]) -> object:
    """
    Construct a canonical EnsembleEncoder wrapper.

    Args:
        feature_dim: out_dim per encoder
        top_k: k nonzeros per encoder output (enforced inside encoder)
        seeds: list of integer seeds (diversity across encoders)

    Returns:
        A ProtocolEnsemble instance with canonical py_nsi backend.
    """
    EnsembleEncoder = _require_py_nsi()
    in_dim = _resolve_input_dim()
    seeds_i = [int(s) for s in seeds] if seeds else [0]
    dim = int(max(1, feature_dim))
    sparsity = float(max(0.01, min(1.0, float(top_k) / float(max(1, feature_dim)))))
    inner = EnsembleEncoder.from_seeds(
        seeds=[int(s) for s in seeds_i],
        dim=dim,
        sparsity=sparsity,
        agree_threshold=max(1, len(seeds_i)),
    )
    return ProtocolEnsemble(input_dim=in_dim, feature_dim=dim, top_k=top_k, seeds=seeds_i, inner=inner)


def encode_all_and_intersect(ensemble, acts: np.ndarray, threshold: float) -> np.ndarray:
    """
    For each activation vector x in acts, project into feature space and call:
      mask = ProtocolEnsemble.intersect_mask(x, threshold)
    Collect masks into a boolean array of shape [N, H].

    Args:
        ensemble: ProtocolEnsemble as returned by build_pyensemble()
        acts: np.ndarray [N, D] float activations
        threshold: float threshold for intersection (>)

    Returns:
        masks: np.ndarray [N, H] of dtype=bool
    """
    if not isinstance(acts, np.ndarray) or acts.ndim != 2:
        raise ValueError("acts must be a 2D numpy array [N, D]")

    acts_f32 = acts.astype(np.float32, copy=False)
    N = acts_f32.shape[0]
    out_rows: List[np.ndarray] = []

    # Probe first row to determine H
    if N == 0:
        return np.zeros((0, 0), dtype=bool)

    first_mask = ensemble.intersect_mask(acts_f32[0], float(threshold))
    H = len(first_mask)
    out_rows.append(np.asarray(first_mask, dtype=bool))

    # Remaining rows
    for i in range(1, N):
        mask = ensemble.intersect_mask(acts_f32[i], float(threshold))
        if len(mask) != H:
            raise RuntimeError(f"Inconsistent intersection length: got {len(mask)} vs expected {H}")
        out_rows.append(np.asarray(mask, dtype=bool))

    return np.stack(out_rows, axis=0)

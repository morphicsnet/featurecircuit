from __future__ import annotations

from typing import List

import numpy as np


def _require_py_nsi():
    try:
        # Imported lazily to allow repo to run without the wheel until needed
        from py_nsi import SpikeEncoder  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "py_nsi is not importable. Build the local Rust wheel first:\n"
            "  maturin develop --release -m core/py_nsi/Cargo.toml\n"
            "Then re-run the demo."
        ) from e
    return SpikeEncoder


def encode_spikes_for_sample(
    ensemble,
    activation_vector: "np.ndarray",
    t_start: float,
    delta_t: float,
    min_sigmoid: float,
) -> List:
    """
    For a single sample:
      - Build per-encoder boolean masks from the canonical ProtocolEnsemble wrapper.
      - Convert each mask into spike events via py_nsi.SpikeEncoder latency coding.
      - Return events sorted by (time, node-id) for determinism.

    Returns a list of py_nsi.SpikeEvent objects.
    """
    SpikeEncoder = _require_py_nsi()

    if not isinstance(activation_vector, np.ndarray) or activation_vector.ndim != 1:
        raise ValueError("activation_vector must be a 1D numpy array [D]")

    masks_per_encoder = ensemble.masks_by_encoder(
        activation_vector.astype(np.float32, copy=False),
        threshold=0.0,
    )

    spike_encoder = SpikeEncoder.from_params(
        min_val=0.0,
        max_val=1.0,
        t_min=float(t_start),
        t_max=float(t_start) + max(float(delta_t), 0.0),
        epsilon=float(min_sigmoid),
    )

    spikes: List = []
    for e_idx, mask in enumerate(masks_per_encoder):
        feats = [1.0 if bool(v) else 0.0 for v in mask]
        events = spike_encoder.encode_batch([feats], encoder_id=int(e_idx))
        for ev in events:
            node_id = ((int(ev.encoder_id) & 0xFFFF) << 32) | (int(ev.feature_idx) & 0xFFFFFFFF)
            spikes.append((float(ev.time), int(node_id), ev))

    spikes.sort(key=lambda x: (x[0], x[1]))
    return [sp for (_, __, sp) in spikes]


def encode_spikes_batch(
    ensemble,
    acts: "np.ndarray",
    t_start: float,
    delta_t: float,
    min_sigmoid: float,
) -> List[List]:
    """
    Encode a batch of activation vectors into spike-event lists, one list per sample.
    """
    if not isinstance(acts, np.ndarray) or acts.ndim != 2:
        raise ValueError("acts must be a 2D numpy array [N, D]")

    acts_f32 = acts.astype(np.float32, copy=False)
    out: List[List] = []
    for i in range(acts_f32.shape[0]):
        out.append(
            encode_spikes_for_sample(
                ensemble=ensemble,
                activation_vector=acts_f32[i],
                t_start=t_start,
                delta_t=delta_t,
                min_sigmoid=min_sigmoid,
            )
        )
    return out

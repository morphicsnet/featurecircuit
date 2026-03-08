from __future__ import annotations

from pathlib import Path


def test_canonical_binding_import_and_smoke(tmp_path: Path) -> None:
    from py_nsi import EnsembleEncoder, GraphStreamingEngine, HypergraphStore, SpikeEncoder

    cfg = tmp_path / "spike.yaml"
    cfg.write_text(
        "min_val: 0.0\n"
        "max_val: 1.0\n"
        "t_min: 0.0\n"
        "t_max: 1.0\n"
        "epsilon: 1e-6\n",
        encoding="utf-8",
    )

    enc = SpikeEncoder.from_config(str(cfg))
    events = enc.encode_batch([[0.0, 0.2, 0.8, 0.0], [0.1, 0.0, 0.3, 0.9]], encoder_id=0)

    gse = GraphStreamingEngine(window=0.05)
    store = HypergraphStore()
    for ev in events:
        islands = gse.ingest(ev)
        for isl in islands:
            store.add_island(isl)

    out = tmp_path / "canon.hif.json"
    store.export_hif(str(out))
    assert out.exists()

    ee = EnsembleEncoder(n_enc=3, dim=4, base_seed=42, sparsity=0.5, agree_threshold=2)
    mask = ee.intersect_mask([0.1, 0.5, 0.0, 1.0], thresh=0.05)
    assert len(mask) == 4

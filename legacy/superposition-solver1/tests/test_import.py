from pathlib import Path

def test_import_and_minimal_flow():
    from py_nsi import SpikeEncoder, GraphStreamingEngine, HypergraphStore, EnsembleEncoder

    repo_root = Path(__file__).resolve().parents[1]
    cfg_path = repo_root / "configs" / "spike.yaml"
    if not cfg_path.exists():
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(
            "min_val: 0.0\n"
            "max_val: 1.0\n"
            "t_min: 0.0\n"
            "t_max: 1.0\n"
            "epsilon: 1e-6\n"
        )
    enc = SpikeEncoder.from_config(str(cfg_path))

    acts = [[0.0, 0.2, 0.8, 0.0]]
    events = enc.encode_batch(acts, encoder_id=0)

    gse = GraphStreamingEngine(window=0.05)
    store = HypergraphStore()
    for ev in events:
        islands = gse.ingest(ev)
        for isl in islands:
            store.add_island(isl)

    out = repo_root / "outputs" / "hypergraphs" / "test_smoke.hif.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    store.export_hif(str(out))
    assert out.exists()

    ee = EnsembleEncoder(n_enc=3, dim=4, base_seed=42, sparsity=0.5, agree_threshold=2)
    mask = ee.intersect_mask([0.1, 0.5, 0.0, 1.0], thresh=0.05)
    assert len(mask) == 4

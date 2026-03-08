use std::path::Path;

#[test]
fn spike_and_hif_smoke() {
    use nsi_core::encoding::{SpikeEncoder, SpikeEncoderConfig};
    use nsi_core::hypergraph::{GraphStreamingEngine, HypergraphStore};

    let enc = SpikeEncoder::new(SpikeEncoderConfig::default());
    // batch=2, features=4
    let acts = vec![vec![0.0, 0.3, 0.7, 0.0], vec![0.2, 0.0, 0.5, 0.9]];
    let events = enc.encode_batch(&acts, 0);

    let mut gse = GraphStreamingEngine::new(0.1);
    let mut store = HypergraphStore::new();

    for ev in events {
        for island in gse.ingest(ev) {
            store.add_island(island);
        }
    }

    let out = "target/test_smoke.hif.json";
    std::fs::create_dir_all("target").unwrap();
    store.export_hif(out).unwrap();
    assert!(Path::new(out).exists());
}

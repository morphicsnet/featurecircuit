from __future__ import annotations

import json
from pathlib import Path

from py_nsi.compat import PyEnsemble, PyGse, PyHypergraphStore, PySimpleSaeEncoder, PySpike


def test_legacy_compat_flow(tmp_path: Path) -> None:
    enc1 = PySimpleSaeEncoder(4, 6, 2, 11)
    enc2 = PySimpleSaeEncoder(4, 6, 2, 23)
    ens = PyEnsemble([enc1, enc2])

    outs = ens.encode_all([0.1, 0.2, -0.1, 0.3])
    mask = ens.intersect(outs, 0.0)
    assert len(mask) == 6

    gse = PyGse(0.5)
    s1 = PySpike(0, 1, 0.0)
    s2 = PySpike(1, 2, 0.2)
    islands = []
    islands.extend(gse.ingest(s1))
    islands.extend(gse.ingest(s2))

    store = PyHypergraphStore()
    for isl in islands:
        store.add_island(isl)
    stii = store.compute_stii([s1.node_id(), s2.node_id()], [(1, 0.2), (2, 0.1)])
    assert isinstance(stii, float)

    out = tmp_path / "legacy_hif.json"
    store.export_hif(str(out))
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["network-type"] == "hypergraph"

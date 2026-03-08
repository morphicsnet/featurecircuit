from __future__ import annotations

from pathlib import Path

from featurecircuit_protocol.validation import validate_json_file
from py_nsi.compat import PyGse, PyHypergraphStore, PySpike


def test_hif_canonical_and_legacy_exports_validate(tmp_path: Path) -> None:
    store = PyHypergraphStore()
    gse = PyGse(0.5)
    for sp in [PySpike(0, 1, 0.0), PySpike(1, 2, 0.2), PySpike(0, 3, 0.21), PySpike(1, 4, 0.22)]:
        for island in gse.ingest(sp):
            store.add_island(island)

    legacy_path = tmp_path / "hif_legacy_demo.v0.json"
    canon_path = tmp_path / "hif.v0.json"

    store.export_hif(str(legacy_path))
    store.export_hif_v0(str(canon_path))

    validate_json_file(legacy_path, "hif_legacy_demo.v0.json")
    validate_json_file(canon_path, "hif.v0.json")

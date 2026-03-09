from __future__ import annotations

from featurecircuit_protocol.ids import candidate_id, feature_id, relation_id, snapshot_id, structure_id


def test_feature_id_deterministic() -> None:
    a = feature_id("fs1", 3, "sae_features", "12")
    b = feature_id("fs1", 3, "sae_features", "12")
    c = feature_id("fs1", 3, "sae_features", "13")
    assert a == b
    assert a != c


def test_relation_id_deterministic_and_ordered() -> None:
    rid1 = relation_id(
        relation_builder_type="coactivation",
        relation_builder_version="v1",
        member_feature_ids_ordered=["f1", "f2"],
        directionality="undirected",
        arity=2,
        construction_rule="threshold",
        threshold=0.5,
    )
    rid2 = relation_id(
        relation_builder_type="coactivation",
        relation_builder_version="v1",
        member_feature_ids_ordered=["f1", "f2"],
        directionality="undirected",
        arity=2,
        construction_rule="threshold",
        threshold=0.5,
    )
    rid3 = relation_id(
        relation_builder_type="coactivation",
        relation_builder_version="v1",
        member_feature_ids_ordered=["f2", "f1"],
        directionality="undirected",
        arity=2,
        construction_rule="threshold",
        threshold=0.5,
    )
    assert rid1 == rid2
    assert rid1 != rid3


def test_candidate_id_deterministic_sorted_members() -> None:
    c1 = candidate_id("hypergraph", "v1", ["f2", "f1"], "hyperedge", 2)
    c2 = candidate_id("hypergraph", "v1", ["f1", "f2"], "hyperedge", 2)
    c3 = candidate_id("hypergraph", "v1", ["f1", "f3"], "hyperedge", 2)
    assert c1 == c2
    assert c1 != c3


def test_structure_id_deterministic_sorted_members() -> None:
    s1 = structure_id("hypergraph", "v1", ["f2", "f1"], "hyperedge")
    s2 = structure_id("hypergraph", "v1", ["f1", "f2"], "hyperedge")
    s3 = structure_id("hypergraph", "v1", ["f1", "f3"], "hyperedge")
    assert s1 == s2
    assert s1 != s3


def test_snapshot_id_deterministic() -> None:
    a = snapshot_id("train-1", "ckpt-1", "fs-1", "cand-1")
    b = snapshot_id("train-1", "ckpt-1", "fs-1", "cand-1")
    c = snapshot_id("train-1", "ckpt-2", "fs-1", "cand-1")
    assert a == b
    assert a != c

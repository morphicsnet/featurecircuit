# Hypergraph Interchange Format (HIF) — Minimal Subset

This project exports a minimal HIF-like JSON:

{
  "schema": "HIF-v0",
  "nodes": [{"id": "e:0:f:12"}, ...],
  "hyperedges": [
    {"id": "he_0", "nodes": ["e:0:f:12", "e:1:f:12"], "count": 3}
  ]
}

- Node ids: "e:{encoder_id}:f:{feature_idx}"
- count: recurrence count observed by the Graph Streaming Engine.

Compatibility: JSON is importable in generic hypergraph tools by mapping nodes and hyperedges accordingly.

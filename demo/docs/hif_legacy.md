# Hypergraph Interchange Format (HIF) - Minimal HIF-v0 Export

This project exports a minimal HIF-like JSON from `core/nsi_core/src/hypergraph.rs`.

```json
{
  "schema": "HIF-v0",
  "nodes": [{"id": "e:0:f:12"}],
  "hyperedges": [
    {"id": "he_0", "nodes": ["e:0:f:12", "e:1:f:12"], "count": 3}
  ]
}
```

Conventions:
- Node ids are strings derived from encoder and feature ids: `e:{encoder_id}:f:{feature_idx}`
- `count` is the recurrence count observed by the Graph Streaming Engine

Compatibility notes:
- This is a minimal HIF-v0 export used by this repo only.
- It can be imported into generic hypergraph tools by mapping nodes and hyperedges accordingly.

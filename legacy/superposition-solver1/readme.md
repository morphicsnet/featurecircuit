# **Superposition Elimination: Reproducible Research Protocol & Repository Guide**

This repository provides a **fully reproducible experimental framework** for evaluating **superposition elimination**, **feature disentanglement**, and **causal circuit extraction** in transformer models—using a **Rust core with Python bindings**.

The project implements a software instantiation of the architecture described in the
📄 **SHG: Superposition Elimination Blueprint**


It includes:

* reproducible experiments,
* ensemble encoders,
* temporal spiking encoders,
* hypergraph construction,
* STII-based causal inference,
* standardized HIF hypergraph export,
* and a full methodological protocol for academic replicability.

This document is **both**:

1. A **Research Protocol** that labs can follow step-by-step, and
2. A **Repository README** outlining installation, structure, usage, and contribution.

---

# 📘 **1. Scientific Motivation**

Modern LLMs compress many unrelated semantic features into shared neurons—**superposition**.
This repository provides reproducible tools for testing the hypothesis:

> **Hypothesis H₁:**
> Representations built from **diverse encoder ensembles**, **temporal spike coding**, and **cross-ensemble coincidence hypergraphs** exhibit **significantly reduced polysemanticity** while maintaining task accuracy.

We quantify “superposition elimination” by:

* concept conditional activation entropy,
* monosemanticity ratio,
* representational purity,
* and causal necessity via STII/ACDC.

---

# 📂 **2. Repository Structure**

```
superposition-elimination/
│
├── nsi_core/                # Rust core (encoders, GSE, hypergraph, metrics)
│   ├── src/
│   ├── Cargo.toml
│   └── ...
│
├── py_nsi/                  # Python bindings built with pyo3
│   ├── src/
│   ├── Cargo.toml
│   └── ...
│
├── notebooks/               # Jupyter demos (baseline → causal circuits)
│   ├── 01_baseline_sae.ipynb
│   ├── 02_ensemble_intersection.ipynb
│   ├── 03_temporal_spikes_hypergraph.ipynb
│   ├── 04_stii_causal_extraction.ipynb
│   └── 05_dashboard.ipynb
│
├── configs/                 # YAML experiment configs for full reproducibility
│
├── data/                    # Small, standardized concept datasets
│
├── outputs/                 # HIF hypergraphs + logs produced by experiments
│
└── README.md                # (this document)
```

---

# ⚙️ **3. Installation**

### **Install Rust + Python dependencies**

```bash
rustup update
pip install maturin
pip install -r requirements.txt
```

### **Build and install Python bindings**

```bash
cd py_nsi
maturin develop --release
```

This exposes all Rust functionality as a Python module:

```python
from py_nsi import (
    EnsembleEncoder,
    SpikeEncoder,
    GraphStreamingEngine,
    HypergraphStore,
)
```

---

# 🧪 **4. Research Protocol Overview (Step-by-Step)**

This is the canonical experimental pipeline.
All steps are reproducible and parameterized via `configs/*.yaml`.

---

## **Step 1 — Baseline Superposition (SAE)**

**Goal:** Establish the level of polysemanticity in standard sparse autoencoders.

Run:

```bash
jupyter notebook notebooks/01_baseline_sae.ipynb
```

This notebook:

* trains SAEs on transformer layer activations,
* computes concept-conditional activations,
* outputs baseline polysemanticity histograms.

Record:

```
outputs/baseline/polysemanticity.json
```

---

## **Step 2 — Ensemble Encoder Intersection (Rust)**

**Goal:** Show that **orthogonal ensembles** + feature intersection reduce superposition.

Run:

```bash
jupyter notebook notebooks/02_ensemble_intersection.ipynb
```

This notebook uses:

* `EnsembleEncoder` from Rust,
* multiple encoders initialized with varied seeds/sparsity,
* intersection masks to isolate consensus features.

Evaluates:

* polysemanticity before/after intersection,
* probing accuracy,
* purity distributions.

Expected pattern:

> Sharp drop in polysemantic features without accuracy loss.

---

## **Step 3 — Temporal Spike Encoding + Hypergraph Construction**

**Goal:** Reproduce the blueprint’s temporal coincidence mechanism using software spiking.


Run:

```bash
jupyter notebook notebooks/03_temporal_spikes_hypergraph.ipynb
```

This notebook:

* converts activations → spike times (latency code),
* uses the **Graph Streaming Engine** to detect cross-ensemble spike coincidences,
* constructs a **Dynamic Causal Hypergraph** via `HypergraphStore`,
* exports it as a **HIF** file:

```
outputs/hypergraphs/layer4.hif.json
```

---

## **Step 4 — Causal Verification (STII, ACDC)**

**Goal:** Determine whether hyperedges represent **causally necessary** circuits.

Run:

```bash
jupyter notebook notebooks/04_stii_causal_extraction.ipynb
```

This notebook:

* enumerates subsets of the hyperedge,
* performs masked forward passes,
* calculates Shapley–Taylor Interaction Index (Rust),
* runs ACDC-style causal pruning,
* outputs minimal causal subgraphs.

Evaluates:

* hallucination circuits,
* dependency chains,
* possible harmful shortcuts or biases.

---

## **Step 5 — Visualization & Analysis Dashboard**

Run:

```bash
jupyter notebook notebooks/05_dashboard.ipynb
```

Features:

* monosemanticity plots,
* hypergraph statistics,
* causal circuit diagrams,
* task accuracy comparisons.

---

# 📊 **5. Key Metrics & Definitions**

### **Polysemanticity**

* `poly(f) = count(P(C_k|f) > ε)`
* or activation entropy (H(f))

### **Representational Purity**

Measures how consistently a feature maps to a single conceptual label.

### **Temporal Coincidence Score**

Measures synchronized spike timing across encoders.

### **STII (Shapley–Taylor Interaction Index)**

Quantifies whether a multi-node hyperedge is **causally synergistic**.

### **ACDC Node Retention %**

Measures how much of the hypergraph is required to preserve behavior.

---

# 🔄 **6. Reproducibility Infrastructure**

### **All experiments follow:**

* fixed random seeds (logged),
* version-pinned dependencies,
* dataset hash logging,
* YAML-controlled experiment parameters,
* HIF hypergraph export,
* reproducible notebooks.

### **Artifact export**

```
outputs/
  metrics/
  hypergraphs/
  logs/
  configs_used/
```

---

# 🏗️ **7. Rust Architecture (Core Modules)**

### `encoding.rs`

* latency coding
* spike generation
* optional phase coding

### `ensemble.rs`

* generic trait-based encoders
* ensemble intersection logic

### `hypergraph.rs` (GSE + GMF)

* graph streaming (temporal sliding window)
* hyperedge formation
* recurrence counting
* hashing for fast lookups

### `metrics.rs`

* polysemanticity
* representational purity
* STII aggregation (numerically stable)

---

# 🧩 **8. Python API**

Example:

```python
from py_nsi import EnsembleEncoder, SpikeEncoder, GraphStreamingEngine, HypergraphStore

ensemble = EnsembleEncoder.from_config("configs/ensemble.yaml")
spike_encoder = SpikeEncoder.from_config("configs/spike.yaml")

gse = GraphStreamingEngine(window=0.5)
store = HypergraphStore()

for acts, meta in stream_activations(model, prompts):
    spikes = spike_encoder.encode_batch(acts, meta)
    for spike in spikes:
        islands = gse.ingest(spike)
        for island in islands:
            store.add_island(island)

store.export_hif("outputs/hypergraphs/l4.hif.json")
```

---

# 🤝 **9. Contributing**

We welcome contributions that improve:

* causal metrics (STII variants),
* spiking encoders,
* hypergraph mining,
* visualization tools,
* new experiment notebooks,
* datasets for concept probing.

Submit PRs with:

1. unit tests,
2. reproducible notebooks,
3. updated configs,
4. benchmark metrics.

---

# 📚 **10. Citations**

If you use this repository in research, please cite the attached blueprint:

**“SHG: Superposition Elimination Blueprint”**



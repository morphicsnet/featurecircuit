# Investor Dashboard Summary

Output directory: `outputs/investor/20260308-110150`

## Selections
- baseline: `/Volumes/128/superposition-demo/outputs/baseline/20260308-105608`
- ensemble: `/Volumes/128/superposition-demo/outputs/ensemble/20260308-105621`
- spike_hypergraph: `/Volumes/128/superposition-demo/outputs/spike_hypergraph/20260308-105630`
- causal: `/Volumes/128/superposition-demo/outputs/causal/20260308-110147`

## Baseline (Demo 1)
- Median poly: 2.00
- Monosemantic rate: 0.014

## Ensemble Intersection (Demo 2)
- Single median poly: 2.00, mono: 0.013, acc: 0.700
- ∩ median poly: 2.00, mono: 0.000, acc: 0.500

## Spike–Hypergraph (Demo 3)
- #Edges: 1244, accuracy: 0.938
- Median poly: 1.00, monosemantic: 0.626

## Causal Circuits (Demo 4: STII + ACDC + Fairness)
- ACDC base→final accuracy: 0.600 → 0.775
- Kept edges: 50
- Fairness: biased nodes present in minimal? No (count=0)

## Artifacts
- baseline_poly_hist: `outputs/investor/20260308-110150/plots/baseline_poly_hist.png`
- ensemble_single_poly_hist: `outputs/investor/20260308-110150/plots/ensemble_single_poly_hist.png`
- ensemble_intersection_poly_hist: `outputs/investor/20260308-110150/plots/ensemble_intersection_poly_hist.png`
- hypergraph_poly_hist_src: `/Volumes/128/superposition-demo/outputs/spike_hypergraph/20260308-105630/poly_hist_hyperedges.png`
- stii_topk_bar: `outputs/investor/20260308-110150/plots/stii_topk_bar.png`

> Acceptance mapping: This report corresponds to the investor story in DEMO_CORRIDOR.md (polysemanticity collapse, intersection effects, topology summary, STII/ACDC, fairness).
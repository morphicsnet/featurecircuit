"""
Minimal GPT2-small activation harness for demonstration.

Note: Not executed in CI. Requires `transformers` and `torch`.
"""
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from py_nsi import SpikeEncoder, GraphStreamingEngine, HypergraphStore

def stream_activations(layer_idx: int = 4):
    model = AutoModelForCausalLM.from_pretrained("gpt2")
    tok = AutoTokenizer.from_pretrained("gpt2")
    model.eval()

    captures = {}

    def hook(module, inp, out):
        captures["acts"] = out.detach().cpu()

    handle = model.transformer.h[layer_idx].register_forward_hook(hook)

    prompts = ["Hello world!", "Mechanistic interpretability is fun."]
    for p in prompts:
        ids = tok(p, return_tensors="pt").input_ids
        _ = model(ids)
        yield captures["acts"]  # [batch, seq, hidden]
    handle.remove()

def main():
    enc = SpikeEncoder.from_config("configs/spike.yaml")
    gse = GraphStreamingEngine(window=0.05)
    store = HypergraphStore()

    for acts in stream_activations():
        # Collapse seq dimension by mean for demo
        acts2d = acts.mean(dim=1)  # [batch, hidden]
        batch = acts2d.numpy().tolist()
        events = enc.encode_batch(batch, encoder_id=0)
        for ev in events:
            for island in gse.ingest(ev):
                store.add_island(island)

    store.export_hif("outputs/hypergraphs/gpt2_demo.hif.json")

if __name__ == "__main__":
    main()

use crate::encoding::SpikeEvent;
use anyhow::Result;
use serde::Serialize;
use std::collections::{BTreeSet, HashMap};
use std::fs;
use std::path::Path;

#[derive(Clone, Debug)]
pub struct GraphStreamingEngine {
    window: f32,
    buffer: Vec<SpikeEvent>,
}

#[derive(Clone, Debug, Serialize)]
pub struct Island {
    pub events: Vec<SpikeEvent>,
}

impl GraphStreamingEngine {
    pub fn new(window: f32) -> Self {
        Self {
            window,
            buffer: Vec::new(),
        }
    }

    // Ingest one spike; return 0 or 1 island containing all spikes within +/- window
    // from different encoders.
    pub fn ingest(&mut self, ev: SpikeEvent) -> Vec<Island> {
        let t_now = ev.time;
        self.buffer.push(ev);
        // Retain only recent events within 2*window of current
        self.buffer.retain(|e| (t_now - e.time).abs() <= self.window);

        let mut encs = BTreeSet::new();
        let mut island_events = Vec::new();
        for e in &self.buffer {
            if (e.time - t_now).abs() <= self.window {
                encs.insert(e.encoder_id);
                island_events.push(e.clone());
            }
        }
        if encs.len() >= 2 {
            vec![Island { events: island_events }]
        } else {
            vec![]
        }
    }
}

pub struct HypergraphStore {
    // key = sorted unique node ids joined by '|', value = recurrence count
    edges: HashMap<String, usize>,
}

impl HypergraphStore {
    pub fn new() -> Self {
        Self {
            edges: HashMap::new(),
        }
    }

    pub fn add_island(&mut self, island: Island) {
        let mut nodes: Vec<String> = island
            .events
            .iter()
            .map(|e| format!("e:{}:f:{}", e.encoder_id, e.feature_idx))
            .collect();
        nodes.sort();
        nodes.dedup();
        if nodes.len() < 2 {
            // Ignore trivial edges
            return;
        }
        let key = nodes.join("|");
        *self.edges.entry(key).or_insert(0) += 1;
    }

    pub fn export_hif<P: AsRef<Path>>(&self, path: P) -> Result<()> {
        // Collect unique nodes
        let mut node_set: BTreeSet<String> = BTreeSet::new();
        for key in self.edges.keys() {
            for n in key.split('|') {
                node_set.insert(n.to_string());
            }
        }
        #[derive(Serialize)]
        struct HifNode {
            id: String,
        }
        #[derive(Serialize)]
        struct HifEdge {
            id: String,
            nodes: Vec<String>,
            count: usize,
        }
        #[derive(Serialize)]
        struct HifRoot {
            schema: String,
            nodes: Vec<HifNode>,
            hyperedges: Vec<HifEdge>,
        }

        let nodes: Vec<HifNode> = node_set.into_iter().map(|id| HifNode { id }).collect();
        let mut hyperedges = Vec::new();
        let mut idx = 0usize;
        for (key, count) in &self.edges {
            let nodes = key.split('|').map(|s| s.to_string()).collect();
            hyperedges.push(HifEdge {
                id: format!("he_{}", idx),
                nodes,
                count: *count,
            });
            idx += 1;
        }

        let root = HifRoot {
            schema: "HIF-v0".to_string(),
            nodes,
            hyperedges,
        };

        if let Some(parent) = path.as_ref().parent() {
            if !parent.as_os_str().is_empty() {
                fs::create_dir_all(parent)?;
            }
        }
        let json = serde_json::to_string_pretty(&root)?;
        fs::write(path, json)?;
        Ok(())
    }
}

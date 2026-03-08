use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SpikeEncoderConfig {
    pub min_val: f32,
    pub max_val: f32,
    pub t_min: f32,
    pub t_max: f32,
    pub epsilon: f32,
}

impl Default for SpikeEncoderConfig {
    fn default() -> Self {
        Self {
            min_val: 0.0,
            max_val: 1.0,
            t_min: 0.0,
            t_max: 1.0,
            epsilon: 1e-6,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SpikeEvent {
    pub time: f32,
    pub encoder_id: usize,
    pub feature_idx: usize,
    pub batch: usize,
}

impl SpikeEvent {
    pub fn new(time: f32, encoder_id: usize, feature_idx: usize, batch: usize) -> Self {
        Self {
            time,
            encoder_id,
            feature_idx,
            batch,
        }
    }
}

#[derive(Clone, Debug)]
pub struct SpikeEncoder {
    cfg: SpikeEncoderConfig,
}

impl SpikeEncoder {
    pub fn new(cfg: SpikeEncoderConfig) -> Self {
        Self { cfg }
    }

    pub fn from_config_yaml<P: AsRef<Path>>(path: P) -> Result<Self> {
        let text = fs::read_to_string(path)?;
        let cfg: SpikeEncoderConfig = serde_yaml::from_str(&text)?;
        Ok(Self::new(cfg))
    }

    // Encode a batch of activations [batch][features] into spike events (latency code).
    // Returns one SpikeEvent per (batch, feature) whose activation exceeds epsilon.
    pub fn encode_batch(&self, batch_acts: &[Vec<f32>], encoder_id: usize) -> Vec<SpikeEvent> {
        let mut out = Vec::new();
        for (b, feats) in batch_acts.iter().enumerate() {
            for (i, &v) in feats.iter().enumerate() {
                if let Some(t) = self.map_to_time(v) {
                    out.push(SpikeEvent::new(t, encoder_id, i, b));
                }
            }
        }
        out
    }

    fn map_to_time(&self, v: f32) -> Option<f32> {
        if v <= self.cfg.epsilon {
            return None;
        }
        let clamped = v.clamp(self.cfg.min_val, self.cfg.max_val);
        let denom = (self.cfg.max_val - self.cfg.min_val).max(1e-12);
        let norm = (clamped - self.cfg.min_val) / denom; // 0..1
        // Latency: larger activation -> earlier spike time
        let t = self.cfg.t_min + (1.0 - norm) * (self.cfg.t_max - self.cfg.t_min);
        Some(t)
    }
}

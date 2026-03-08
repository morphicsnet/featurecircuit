use rand::{rngs::StdRng, Rng, SeedableRng};

pub struct LinearEncoder {
    w: Vec<f32>,
}

impl LinearEncoder {
    pub fn new(dim: usize, seed: u64, sparsity: f32) -> Self {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut w = Vec::with_capacity(dim);
        for _ in 0..dim {
            // With probability sparsity, keep a random positive weight; else 0
            let keep = rng.gen::<f32>() < sparsity;
            w.push(if keep { rng.gen::<f32>() } else { 0.0 });
        }
        Self { w }
    }

    pub fn mask(&self, x: &[f32], thresh: f32) -> Vec<bool> {
        x.iter()
            .zip(self.w.iter())
            .map(|(xi, wi)| (*xi * *wi) > thresh)
            .collect()
    }

    pub fn dim(&self) -> usize {
        self.w.len()
    }
}

pub struct EnsembleEncoder {
    encoders: Vec<LinearEncoder>,
    agree_threshold: usize,
    dim: usize,
}

impl EnsembleEncoder {
    pub fn new(n_enc: usize, dim: usize, base_seed: u64, sparsity: f32, agree_threshold: usize) -> Self {
        let encoders = (0..n_enc)
            .map(|i| LinearEncoder::new(dim, base_seed + i as u64, sparsity))
            .collect::<Vec<_>>();
        Self {
            encoders,
            agree_threshold,
            dim,
        }
    }

    pub fn intersect_mask(&self, x: &[f32], thresh: f32) -> Vec<bool> {
        let mut counts = vec![0usize; self.dim];
        for enc in &self.encoders {
            let m = enc.mask(x, thresh);
            for (i, v) in m.iter().enumerate() {
                if *v {
                    counts[i] += 1;
                }
            }
        }
        counts
            .iter()
            .map(|&c| c >= self.agree_threshold)
            .collect::<Vec<_>>()
    }
}

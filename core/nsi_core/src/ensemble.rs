use rand::{rngs::StdRng, Rng, SeedableRng};

#[derive(Clone)]
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
        let seeds = (0..n_enc).map(|i| base_seed + i as u64).collect::<Vec<_>>();
        Self::from_seeds(&seeds, dim, sparsity, agree_threshold)
    }

    pub fn from_seeds(seeds: &[u64], dim: usize, sparsity: f32, agree_threshold: usize) -> Self {
        let encoders = seeds
            .iter()
            .map(|seed| LinearEncoder::new(dim, *seed, sparsity))
            .collect::<Vec<_>>();
        Self {
            encoders,
            agree_threshold,
            dim,
        }
    }

    pub fn masks_by_encoder(&self, x: &[f32], thresh: f32) -> Vec<Vec<bool>> {
        self.encoders
            .iter()
            .map(|enc| enc.mask(x, thresh))
            .collect::<Vec<_>>()
    }

    pub fn intersect_mask(&self, x: &[f32], thresh: f32) -> Vec<bool> {
        let mut counts = vec![0usize; self.dim];
        for m in self.masks_by_encoder(x, thresh) {
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

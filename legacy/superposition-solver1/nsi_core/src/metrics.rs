pub fn polysemanticity_count(probs: &[f32], eps: f32) -> usize {
    probs.iter().filter(|&p| *p > eps).count()
}

pub fn entropy(probs: &[f32]) -> f64 {
    let mut h = 0.0f64;
    for &p in probs {
        let p = p as f64;
        if p > 0.0 {
            h += -p * p.ln();
        }
    }
    h
}

// Simple purity = max class probability
pub fn representational_purity(probs: &[f32]) -> f32 {
    probs
        .iter()
        .cloned()
        .fold(0.0_f32, |m, v| if v > m { v } else { m })
}

// Placeholder STII aggregation (numerically stable sum)
pub fn stii_placeholder(vals: &[f64]) -> f64 {
    // Kahan summation
    let mut sum = 0.0f64;
    let mut c = 0.0f64;
    for x in vals {
        let y = *x - c;
        let t = sum + y;
        c = (t - sum) - y;
        sum = t;
    }
    sum
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_entropy_basic() {
        let p = [0.5, 0.5];
        let h = entropy(&p);
        assert!(h > 0.0);
    }

    #[test]
    fn test_purity() {
        let p = [0.1, 0.7, 0.2];
        assert_eq!(representational_purity(&p), 0.7);
    }
}

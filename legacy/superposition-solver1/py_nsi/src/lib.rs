use nsi_core::encoding::{SpikeEncoder as RsSpikeEncoder, SpikeEncoderConfig, SpikeEvent as RsSpikeEvent};
use nsi_core::ensemble::EnsembleEncoder as RsEnsembleEncoder;
use nsi_core::hypergraph::{GraphStreamingEngine as RsGse, HypergraphStore as RsStore, Island as RsIsland};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyModule;

fn to_py_err(e: anyhow::Error) -> pyo3::PyErr {
    PyValueError::new_err(format!("{}", e))
}

#[pyclass]
#[derive(Clone)]
pub struct SpikeEvent {
    #[pyo3(get)]
    pub time: f32,
    #[pyo3(get)]
    pub encoder_id: usize,
    #[pyo3(get)]
    pub feature_idx: usize,
    #[pyo3(get)]
    pub batch: usize,
}

impl From<RsSpikeEvent> for SpikeEvent {
    fn from(e: RsSpikeEvent) -> Self {
        Self {
            time: e.time,
            encoder_id: e.encoder_id,
            feature_idx: e.feature_idx,
            batch: e.batch,
        }
    }
}

impl From<&SpikeEvent> for RsSpikeEvent {
    fn from(e: &SpikeEvent) -> Self {
        RsSpikeEvent {
            time: e.time,
            encoder_id: e.encoder_id,
            feature_idx: e.feature_idx,
            batch: e.batch,
        }
    }
}

#[pyclass]
pub struct SpikeEncoder {
    inner: RsSpikeEncoder,
}

#[pymethods]
impl SpikeEncoder {
    #[staticmethod]
    pub fn from_config(path: String) -> PyResult<Self> {
        let enc = RsSpikeEncoder::from_config_yaml(path).map_err(to_py_err)?;
        Ok(Self { inner: enc })
    }

    #[staticmethod]
    pub fn from_defaults() -> Self {
        Self {
            inner: RsSpikeEncoder::new(SpikeEncoderConfig::default()),
        }
    }

    pub fn encode_batch(&self, activations: Vec<Vec<f32>>, encoder_id: usize) -> Vec<SpikeEvent> {
        self.inner
            .encode_batch(&activations, encoder_id)
            .into_iter()
            .map(SpikeEvent::from)
            .collect()
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Island {
    #[pyo3(get)]
    pub events: Vec<SpikeEvent>,
}

impl From<RsIsland> for Island {
    fn from(island: RsIsland) -> Self {
        Self {
            events: island.events.into_iter().map(SpikeEvent::from).collect(),
        }
    }
}

impl From<&Island> for RsIsland {
    fn from(island: &Island) -> Self {
        RsIsland {
            events: island.events.iter().map(|e| e.into()).collect(),
        }
    }
}

#[pyclass]
pub struct GraphStreamingEngine {
    inner: RsGse,
}

#[pymethods]
impl GraphStreamingEngine {
    #[new]
    pub fn new(window: f32) -> Self {
        Self {
            inner: RsGse::new(window),
        }
    }

    pub fn ingest(&mut self, event: &SpikeEvent) -> Vec<Island> {
        self.inner
            .ingest(event.into())
            .into_iter()
            .map(Island::from)
            .collect()
    }
}

#[pyclass]
pub struct HypergraphStore {
    inner: RsStore,
}

#[pymethods]
impl HypergraphStore {
    #[new]
    pub fn new() -> Self {
        Self { inner: RsStore::new() }
    }

    pub fn add_island(&mut self, island: &Island) {
        self.inner.add_island(island.into());
    }

    pub fn export_hif(&self, path: String) -> PyResult<()> {
        self.inner.export_hif(path).map_err(to_py_err)
    }
}

#[pyclass]
pub struct EnsembleEncoder {
    inner: RsEnsembleEncoder,
}

#[pymethods]
impl EnsembleEncoder {
    #[new]
    pub fn new(n_enc: usize, dim: usize, base_seed: u64, sparsity: f32, agree_threshold: usize) -> Self {
        Self {
            inner: RsEnsembleEncoder::new(n_enc, dim, base_seed, sparsity, agree_threshold),
        }
    }

    pub fn intersect_mask(&self, x: Vec<f32>, thresh: f32) -> Vec<bool> {
        self.inner.intersect_mask(&x, thresh)
    }
}

#[pymodule]
fn py_nsi(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<SpikeEvent>()?;
    m.add_class::<SpikeEncoder>()?;
    m.add_class::<Island>()?;
    m.add_class::<GraphStreamingEngine>()?;
    m.add_class::<HypergraphStore>()?;
    m.add_class::<EnsembleEncoder>()?;
    Ok(())
}

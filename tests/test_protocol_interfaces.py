from __future__ import annotations

from featurecircuit_protocol.interfaces import (
    AdapterError,
    BuilderError,
    ConfigError,
    ExportError,
    FeatureCircuitError,
    ModelLoadError,
    ValidationError,
)


def test_interface_error_hierarchy() -> None:
    assert issubclass(ConfigError, FeatureCircuitError)
    assert issubclass(ValidationError, FeatureCircuitError)
    assert issubclass(ModelLoadError, FeatureCircuitError)
    assert issubclass(AdapterError, FeatureCircuitError)
    assert issubclass(BuilderError, FeatureCircuitError)
    assert issubclass(ExportError, FeatureCircuitError)

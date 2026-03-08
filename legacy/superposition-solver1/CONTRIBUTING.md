# Contributing

Thanks for your interest in contributing to the Superposition Elimination research suite!

Workflow:
- Fork the repo and create a feature branch.
- Add unit tests and update docs/configs as needed.
- Run local checks:
  - Rust: `cargo fmt`, `cargo clippy -D warnings`, `cargo test --workspace`
  - Python: `pre-commit run -a` (format/ruff/isort)
  - Build bindings: `pip install maturin && maturin develop --release -m py_nsi/Cargo.toml`
- Open a PR with a clear description and reproducibility notes (seeds, data hashes).

Code style:
- Rust: Rust 2021 edition, Clippy clean, fmt enforced.
- Python: Black, Ruff, isort via pre-commit.

Reproducibility:
- Commit experiment YAML configs under `configs/` with pinned seeds.
- Log versions and hashes using `py_nsi/runlog.py`.

CI:
- CI must pass on Linux and macOS (Rust + Python jobs).

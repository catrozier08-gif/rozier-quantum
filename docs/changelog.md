# Rozier Quantum — Change Log

All notable changes to this project are documented here.

---

## [1.3.2] — 2026-04-23
### Added
- Professional README with full technical documentation
- Security manifest (Zero Network Calls statement)
- Vendor-specific baselines for IBM, Google, and IonQ
- Apache 2.0 license

### Fixed
- PyPI metadata now fully indexed and machine-readable
- README correctly embedded in package distribution

---

## [1.3.1] — 2026-04-23
### Added
- Initial README push to PyPI
- Security statement added to package description

---

## [1.3.0] — 2026-04-22
### Added
- Full clinical cycle engine (run_clinical_cycle)
- 83.58% stress reduction on 127-qubit IBM Eagle benchmark
- 6.08x success probability improvement
- Net qubit stability +82 on Boss Fight circuit
- Dynamic degree threshold scaling (circuit-aware Q-001)
- Vendor-specific baselines (IBM, Google, IonQ)
- Confidence scorer rebuilt to reward signal clarity
- Stability improvement projector uses stretch signal
- cluster_on_sparse_topology alignment added
- IBM_BASELINE, GOOGLE_BASELINE, IONQ_BASELINE exported

### Fixed
- run_clinical_cycle loading from correct local source
- Q-001 threshold no longer blanket-flags dense circuits
- expected_stability_improvement no longer returns 0.0
- Confidence no longer shows low on high-stress diagnosis

---

## [1.2.1] — 2026-04-21
### Added
- Export engine (JSON + Markdown)
- Vendor terminology translation layer
- Path mapper integrated
- IBM Heavy-Hex, Google Sycamore vendor profiles
- Chip Corridor Map visualization

---

## [1.0.0] — 2026-04-20
### Added
- Core perception and diagnosis engine
- MultiChipTopology foundation
- QubitHealthScanner OBD2 system
- Q-001 through Q-005 diagnostic codes
- System-level ID format (C{chip}Q{local})
- Initial PyPI release

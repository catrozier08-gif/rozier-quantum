## [1.5.1] - 2026-04-27

### Fixed
- README updated to reflect v1.5.0 features
  on PyPI project page.
- Added Q-007 and Q-008 to diagnostic codes section.
- Added run_structural_preview() to Quick Start.
- Updated version references throughout.
- Removed stray characters from code blocks.
- Updated Benchmarks table with Q-007 and Q-008.

## [1.5.0] - 2026-04-27

### Added
- run_structural_preview(): Combined four-diagnostic
  structural scan in a single pass.
- Q-007 (Bridge Overload): Detects excessive
  cross-chip communication.
- Q-008 (Thermal Risk): Detects dangerous qubit
  load concentration.
- Community Structure Detection: Identifies workload
  community count vs available chip capacity.
- Overflow Alert: Flags circuits that exceed
  hardware capacity.
- Consulting Hook: Every scan now recommends
  Refiner engagement with 22.48x projected gain.

### Security
- MANIFEST.in verified clean.
- .ipynb_checkpoints excluded from all builds.
- refiner.py is public stub only.
- Iron-Clad Protocol active for all future pushes.

## [1.4.3] - 2026-04-27

### Security
- Removed .ipynb_checkpoints from package build.
- Confirmed refiner.py is public stub only.
- MANIFEST.in corrected to properly exclude 
  proprietary files from all future builds.
- pyproject.toml updated to exclude checkpoint 
  directories permanently.

### Fixed
- Build pipeline now clean of all non-public files.
- Package size normalized to expected footprint.

## [1.4.1] - 2026-04-27

### Added
- Q-006 (Grid Stress): New diagnostic code that 
  translates routing friction into estimated electrical 
  waste (kW). Bridges quantum diagnostics to real-world 
  energy and utility grid impact.
- Scan Duration Reporting: Every Odometer scan now 
  self-reports its execution time.
- GitHub Star Call-to-Action integrated into scan output.

### Improved
- ROI Benchmark updated to verified 22.48x multiplier 
  from Industrial Refiner stress tests.
- Odometer output now returns structured dict including 
  grid_waste_kw and scan_duration fields.

### Security
- Zero network calls maintained.
- Air-gap compatibility confirmed.
- Apache 2.0 license maintained.
# Changelog — Rozier Quantum SystemReader

All notable changes to this project will be 
documented in this file.

---

## [1.4.0] - 2026-04-26

### Added
- Site Log Integration: Assign circuits to named 
  job sites with calibration generation tracking
  (site_name, calibration_gen metadata).
- Global Stress Odometer: Real-time calculation 
  of topological routing stress with projected 
  ROI mapping.
- Hyperscale Validation: Benchmarked at 100,000 
  qubits with sub-0.1s scan latency 
  (0.0322s verified).
- Refinement Potential output: Shows percentage 
  improvement available and 17.1x projected 
  efficiency multiplier.
- Consulting contact integration in scan output.
- Industrial Refiner Engine (Private Consulting):
  Hub-and-Spoke City Planning, Thermal Load
  Balancing, Cross-Chip Bridge Bracing,
  Hot-Swap Dynamic Re-Calibration, and
  Gate-Depth Compression. (Available under NDA).

### Improved
- SystemReader now handles sparse topologies 
  at industrial scale.
- Diagnostic output now includes Site Timestamp
  and Calibration Generation metadata.

### Security
- Zero network calls maintained.
- Air-gap compatibility confirmed at 100k scale.
- Apache 2.0 license maintained.

---

## [1.3.2] - 2026-04-23

### Fixed
- Security audit passed. Verified zero network 
  calls and no obfuscated code.
- README overhauled with full benchmark data,
  diagnostic code definitions, and PyPI/GitHub
  links.
- Apache 2.0 license formally declared.

### Added
- CHANGELOG.md established as public record.
- GitHub repository professionalized.

---

## [1.3.1] - 2026-04-22

### Fixed
- Minor packaging and import fixes.
- Stability improvements for multi-chip 
  topology parsing.

---

## [1.3.0] - 2026-04-22

### Added
- Initial public release of SystemReader.
- Clinical Cycle diagnostic engine.
- OBD2-style health codes Q-001 through Q-005.
- IBM Eagle-scale benchmark:
  83.58% stress reduction.
  6.08x success probability improvement.
- Multi-chip line topology support.
- Vendor profiles: IBM, Google, IonQ.
- PathMapper and PerceptionEngine modules.
- Apache 2.0 open source license.
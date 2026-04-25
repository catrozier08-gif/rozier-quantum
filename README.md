# Rozier Quantum SystemReader (v1.4.0)

### Structural Diagnostic Suite for Multi-Chip Quantum Scaling
**Author:** Rozier Quantum LLC  
**Website:** [rozierquantum.com](https://rozierquantum.com)  
**Security Status:** Verified No-Phone-Home / No-Network-Calls

---

## 🏗️ The Problem
As quantum hardware scales beyond 127 qubits (IBM Eagle) toward 4,000+ qubits (IBM Flamingo), the primary bottleneck shifts from individual qubit coherence to **Structural Communication Stress**. Multi-chip architectures introduce high-latency interconnects that can collapse success probability if the workload layout is not "site-calibrated" to the hardware's physical topology.

## 🛠️ The Solution: SystemReader
Rozier Quantum's `SystemReader` is an "OBD2 Scanner" for quantum workloads. It analyzes the structural alignment between a quantum circuit and the underlying hardware coupling map.

### [v1.4.0] The Hyperscale & Location Update
*   **Site Log Integration:** Assign circuits to physical job sites (e.g., `site_name="Data-Center-Alpha"`) for long-term calibration tracking.
*   **Global Stress Odometer:** Real-time calculation of topological routing stress.
*   **100k-Qubit Validation:** Benchmarked to process 100,000-qubit workloads in < 0.1 seconds.
*   **Projected ROI Mapping:** Identifies potential efficiency gains of up to 17.1x.

---

## 🚦 Diagnostic Codes (The OBD2 for Qubits)
SystemReader scans every qubit and link, assigning standard health codes:
*   **Q-001 (Overloaded):** Qubit interaction degree exceeds effective threshold for the circuit's density.
*   **Q-002 (Decoherence Risk):** High ratio of cross-chip interactions relative to local chip support.
*   **Q-003 (Isolation):** Active qubit with zero local support, spread across multiple remote chips.
*   **Q-004 (Bottleneck):** Qubit resides on a "Hot Corridor" link with projected routing congestion.
*   **Q-005 (Idle):** Qubit is allocated but receiving zero interaction traffic. Dead weight on the layout.

---

## 🛡️ Security & Integrity Statement
Rozier Quantum is built for secure, air-gapped laboratory environments. 
*   **Zero Network Calls:** The package does not import `requests`, `urllib`, or any networking libraries.
*   **Local Execution:** All analysis is performed entirely on the local machine.
*   **No Obfuscation:** The source code is clean, PEP8 compliant, and open for audit.

---

## 🚀 Quick Start
```python
from rozier import SystemReader, build_line_topology

# 1. Define your 4-chip hardware (34 qubits per chip)
topology = build_line_topology(num_chips=4, qubits_per_chip=34)

# 2. Initialize the Reader
reader = SystemReader(topology)

# 3. Run a Clinical Cycle on your circuit
results = reader.run_clinical_cycle(your_qiskit_circuit)

# 4. Run the Site Log and Odometer (NEW in v1.4.0)
reader.run_odometer_scan(site_name="Lab-Alpha", calibration_gen="Gen-1")

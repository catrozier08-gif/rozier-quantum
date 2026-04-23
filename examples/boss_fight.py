# Boss Fight — Complete Self-Contained Cell
# Run this after the path fix cell

import sys
import os
import time
import random

sys.path.insert(0, os.getcwd())

# ── Imports ───────────────────────────────────────────────
from qiskit import QuantumCircuit
from rozier import SystemReader, build_line_topology
from rozier.export import export_markdown, export_json

# ── Circuit Builder ───────────────────────────────────────
def create_structured_community_circuit(
    num_qubits=127,
    num_communities=4,
    interactions_per_comm=200,
    cross_comm_links=40,
    seed=42,
):
    random.seed(seed)
    qc = QuantumCircuit(num_qubits)
    qubits = list(range(num_qubits))
    random.shuffle(qubits)

    comms = [qubits[i::num_communities] for i in range(num_communities)]

    for comm in comms:
        for _ in range(interactions_per_comm):
            if len(comm) >= 2:
                q1, q2 = random.sample(comm, 2)
                qc.cx(q1, q2)

    for _ in range(cross_comm_links):
        c1, c2 = random.sample(range(num_communities), 2)
        q1 = random.choice(comms[c1])
        q2 = random.choice(comms[c2])
        qc.cx(q1, q2)

    return qc, comms

# ── Build Circuit and Topology ────────────────────────────
boss_circuit, communities = create_structured_community_circuit()

print(f"Circuit: {boss_circuit.num_qubits} qubits")
print(f"Gates:   {len(boss_circuit.data)}")
print(f"Communities: {len(communities)}, sizes: {[len(c) for c in communities]}")

boss_topo = build_line_topology(num_chips=4, qubits_per_chip=34)
reader = SystemReader(boss_topo)

print(f"\nrun_clinical_cycle available: {'run_clinical_cycle' in dir(reader)}")

# ── Run Clinical Cycle ────────────────────────────────────
start = time.time()

results = reader.run_clinical_cycle(
    boss_circuit,
    max_flagged_qubits=15,
)

elapsed = time.time() - start
print(f"\nTotal cycle time: {elapsed:.3f}s")

# ── Export ────────────────────────────────────────────────
export_markdown(
    results["pre"],
    "boss_fight_127q_v130.md",
    vendor="ibm",
    circuit_name="127-Qubit Community Stress Test — IBM Eagle Scale",
    max_flagged_qubits=15,
)

export_json(
    results["pre"],
    "boss_fight_127q_v130.json",
    vendor="ibm",
)

print("Exported: boss_fight_127q_v130.md")
print("Exported: boss_fight_127q_v130.json")

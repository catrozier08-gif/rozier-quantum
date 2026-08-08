# Rozier Quantum — SystemReader v2.1.1 - The Self-Healing Release + Real Heron Benchmark

**Fixes now EXECUTE and VERIFY on real IBM Heron 156q - tight string all the way**

> *"I don't sell hourly labor. I sell the Vision that clears the fog."* — Chris Rozier, CEO | Rozier Quantum LLC
> Built between layout jobs in Fort Wayne, Indiana - work laptop, two kids watching garage experiments, writing to physics journals

### Verified - Real Hardware + Simulation

**Real hardware benchmark - ibm_kingston 156q Heron (free tier):**
```
Worst case: 100 edges, all cross-chip
Circuit depth before transpile: 19
Baseline - Real ibm_kingston depth 269 SWAPs 0
Rozier - Real ibm_kingston depth 266 SWAPs 0
Fixer internal: Pre cross 100 -> Post 64 = 36.0% fewer cross-chip
Pre stress 4000 -> Post 1930 = 51.7% reduction
```

**Simulation thorough - 100k qubits:**
```
Test 1 Empty: PASS
Test 2 Small 3-qubit: Pre 50 -> Post 35 reduction 30.0% PASS
1000 qubits: 5.9% in 0.011s
10000 qubits: 6.1% in 0.110s
100000 qubits: 6.1% in 1.398s
Toolbags 3, gravity ranked 18 top 3 [14, 15, 18], placement 3 anchored
Qiskit plugin RozierPass: Available
```

### Quick Start v2.1.1

```bash
pip install rozier-quantum==2.1.1
```

```python
from rozier.auto_fixer import RozierAutoFixer, RozierPass
import networkx as nx

G = nx.Graph()
G.add_edges_from([(0,1),(1,2),(2,3)])

fixer = RozierAutoFixer(site_name="My Site")
result = fixer.fix_quantum(G, chip_size=34, num_chips=4, triggered_codes=["Q-007","Q-008"], execute=True)
print(result)  # {'pre_stress': 50, 'post_stress': 35, 'reduction_pct': 30.0, ...}

# Qiskit plugin for company native benchmarks - tested on ibm_kingston 156q Heron
from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager

qc = QuantumCircuit(20)
for i in range(19):
    qc.cx(i, i+1)

pm = PassManager([RozierPass(chip_size=34, num_chips=4)])
qc_fixed = pm.run(qc)
```

### RefinementEngine - Toolbag Logic Shining (Proud Work)

```python
from rozier.refiner import RefinementEngine
# pack_toolbags() louvain communities by traffic_density
# generate_gravity_map() connectivity * noise_dist safe ground away from Q-001/Q-002
# initial_placement() sorted by traffic, anchor to gravity ranked
# expand_clusters() queue neighbors
```

Toolbags 3, gravity ranked 18 top 3 [14,15,18], placement 3 anchored - real working knowledge applied from layout.

### Diagnostic Codes

Q-001 Overloaded, Q-002 Decoherence Risk, Q-007 Bridge Overload, Q-008 Thermal Risk, Q-009 Temporal Drift, Q-011 Gate Depth, Q-012 SWAP Cascade

### Who Built This

Chris Rozier, carpenter and layout lead, Fort Wayne, Indiana. Wife and two kids. 20 years reading physical space. No CS degree, no lab, no team. Started AI Jan 2026.

Patent pending - hardware separate, software open.

"The Layout is always the answer."

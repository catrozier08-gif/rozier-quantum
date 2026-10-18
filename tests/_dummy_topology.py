import networkx as nx
from types import SimpleNamespace

# Minimal synthetic MultiChipTopology used for tests
class DummyTopology:
    def __init__(self, num_chips=4, qubits_per_chip=4):
        self.num_chips = num_chips
        if isinstance(qubits_per_chip, int):
            self.qubits_per_chip = [qubits_per_chip] * num_chips
        else:
            self.qubits_per_chip = qubits_per_chip
        # simple line chip graph
        G = nx.path_graph(num_chips)
        self.chip_graph = G

    def __repr__(self):
        return f"DummyTopology(num_chips={self.num_chips}, capacities={self.qubits_per_chip})"

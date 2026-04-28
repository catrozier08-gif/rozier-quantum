from dataclasses import dataclass, field
import networkx as nx


@dataclass
class MultiChipTopology:
    num_chips: int
    qubits_per_chip: list
    chip_graph: nx.Graph = field(default_factory=nx.Graph)
    intra_chip_latency: float = 1.0
    intra_chip_fidelity: float = 0.999

    def __post_init__(self):
        if isinstance(self.qubits_per_chip, int):
            self.qubits_per_chip = [self.qubits_per_chip] * self.num_chips

        for chip in range(self.num_chips):
            self.chip_graph.add_node(chip, capacity=self.qubits_per_chip[chip])

    def add_link(self, chip_a, chip_b, latency=5.0, fidelity=0.95, bandwidth=1.0):
        self.chip_graph.add_edge(
            chip_a,
            chip_b,
            latency=latency,
            fidelity=fidelity,
            bandwidth=bandwidth,
        )


def build_line_topology(num_chips=4, qubits_per_chip=34):
    topology = MultiChipTopology(num_chips, qubits_per_chip)

    for i in range(num_chips - 1):
        topology.add_link(i, i + 1)

    return topology
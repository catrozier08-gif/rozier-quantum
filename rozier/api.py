from .optimizer import StablePlacementOptimizer


def preflight(topology, circuit):
    optimizer = StablePlacementOptimizer(topology, max_refine_passes=0)
    result = optimizer.optimize(circuit)

    return {
        "num_qubits": circuit.num_qubits,
        "num_chips": topology.num_chips,
        "chip_capacities": topology.qubits_per_chip,
        "initial_metrics": result["initial_metrics"],
    }


def analyze(topology, circuit, max_refine_passes=10, mode="production"):
    optimizer = StablePlacementOptimizer(
        topology,
        max_refine_passes=max_refine_passes
    )

    result = optimizer.optimize(circuit)

    if mode == "research":
        result["diagnostics"] = {
            "num_qubits": circuit.num_qubits,
            "num_chips": topology.num_chips,
            "chip_capacities": topology.qubits_per_chip,
        }

    return result


class RozierOptimizer:
    def __init__(self, topology, max_refine_passes=10):
        self.topology = topology
        self.max_refine_passes = max_refine_passes

    def preflight(self, circuit):
        return preflight(self.topology, circuit)

    def analyze(self, circuit, mode="production"):
        return analyze(
            self.topology,
            circuit,
            max_refine_passes=self.max_refine_passes,
            mode=mode
        )


def summarize_result(result, detailed=False):
    initial = result["initial_metrics"]
    refined = result["refined_metrics"]

    print("=== Placement Summary ===")
    print(f"Initial communication cost: {initial['communication_cost']}")
    print(f"Refined communication cost: {refined['communication_cost']}")

    delta = initial["communication_cost"] - refined["communication_cost"]
    pct = 100 * delta / initial["communication_cost"] if initial["communication_cost"] > 0 else 0.0

    print(f"Cost reduction: {delta} ({pct:.2f}%)")
    print()

    print(f"Initial success probability: {initial['estimated_success_probability']:.6f}")
    print(f"Refined success probability: {refined['estimated_success_probability']:.6f}")

    if detailed:
        placement = result["refined_placement"]
        chip_counts = {}

        for q, chip in placement.items():
            chip_counts[chip] = chip_counts.get(chip, 0) + 1

        print("\n--- Placement Distribution ---")
        for chip in sorted(chip_counts):
            print(f"Chip {chip}: {chip_counts[chip]} qubits")

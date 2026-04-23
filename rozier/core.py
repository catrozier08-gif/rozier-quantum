import networkx as nx
import random
from collections import defaultdict
from typing import Dict

from qiskit import QuantumCircuit
from qiskit.circuit import Gate


# =========================================================
# INTERACTION GRAPH BUILDER
# =========================================================

class InteractionGraphBuilder:
    @staticmethod
    def build(circuit: QuantumCircuit) -> nx.Graph:
        G = nx.Graph()

        for qubit in range(circuit.num_qubits):
            G.add_node(qubit)

        for instruction, qargs, _ in circuit.data:
            if isinstance(instruction, Gate) and len(qargs) == 2:
                q1 = circuit.find_bit(qargs[0]).index
                q2 = circuit.find_bit(qargs[1]).index

                if G.has_edge(q1, q2):
                    G[q1][q2]["weight"] += 1
                else:
                    G.add_edge(q1, q2, weight=1)

        return G


# =========================================================
# TOPOLOGY-AWARE COMMUNITY PLACEMENT
# =========================================================

# =========================================================
# STRUCTURED COMMUNITY-AWARE INITIALIZER
# =========================================================

class TopologyAwareCommunityPlacement:
    def __init__(self, topology):
        self.topology = topology

    def place(self, interaction_graph):
        placement = {}

        # Sort nodes by degree (highest first)
        nodes = sorted(
            interaction_graph.nodes(),
            key=lambda q: interaction_graph.degree(q),
            reverse=True
        )

        unplaced = set(nodes)

        chip_capacities = {
            chip: self.topology.qubits_per_chip[chip]
            for chip in range(self.topology.num_chips)
        }

        current_chip = 0

        while unplaced:
            if chip_capacities[current_chip] == 0:
                current_chip += 1
                continue

            # Start new region with highest-degree unplaced node
            seed = max(unplaced, key=lambda q: interaction_graph.degree(q))

            stack = [seed]

            while stack and chip_capacities[current_chip] > 0:
                node = stack.pop()

                if node not in unplaced:
                    continue

                # Place node
                placement[node] = current_chip
                unplaced.remove(node)
                chip_capacities[current_chip] -= 1

                # Add strongest neighbors next
                neighbors = sorted(
                    interaction_graph.neighbors(node),
                    key=lambda n: interaction_graph.degree(n),
                    reverse=True
                )

                for n in neighbors:
                    if n in unplaced:
                        stack.append(n)

        return placement


# =========================================================
# COST MODEL
# =========================================================


class FastPlacementCostModel:
    def __init__(self, topology):
        self.topology = topology

    def communication_cost(self, interaction_graph, placement):
        cost = 0.0

        for u, v, data in interaction_graph.edges(data=True):
            weight = data.get("weight", 1)
            chip_u = placement[u]
            chip_v = placement[v]

            if chip_u != chip_v:
                try:
                    path_length = nx.shortest_path_length(
                        self.topology.chip_graph,
                        chip_u,
                        chip_v,
                        weight="latency"
                    )
                except nx.NetworkXNoPath:
                    path_length = 10.0

                cost += weight * path_length

        return cost

    def evaluate(self, interaction_graph, placement):
        comm_cost = self.communication_cost(interaction_graph, placement)

        inter_chip_gates = sum(
            1
            for u, v in interaction_graph.edges()
            if placement[u] != placement[v]
        )

        success_probability = 1.0 / (1.0 + comm_cost)

        return {
            "communication_cost": comm_cost,
            "inter_chip_gates": inter_chip_gates,
            "estimated_success_probability": success_probability,
        }

# =========================================================
# LOCAL SEARCH REFINER
# =========================================================

class FastLocalSearchPlacementOptimizer:
    def __init__(self, topology, cost_model):
        self.topology = topology
        self.cost_model = cost_model

    def refine(self, interaction_graph, initial_placement, max_passes=10):
        current = initial_placement.copy()
        current_cost = self.cost_model.communication_cost(interaction_graph, current)

        for _ in range(max_passes):
            improved = False
            nodes = list(interaction_graph.nodes())

            # --- Single-qubit moves ---
            for q in nodes:
                old_chip = current[q]

                for new_chip in range(self.topology.num_chips):
                    if new_chip == old_chip:
                        continue

                    current[q] = new_chip
                    new_cost = self.cost_model.communication_cost(interaction_graph, current)

                    if new_cost < current_cost:
                        current_cost = new_cost
                        improved = True
                    else:
                        current[q] = old_chip

            # --- Swap moves ---
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    q1 = nodes[i]
                    q2 = nodes[j]

                    chip1 = current[q1]
                    chip2 = current[q2]

                    if chip1 == chip2:
                        continue

                    # swap
                    current[q1], current[q2] = chip2, chip1
                    new_cost = self.cost_model.communication_cost(interaction_graph, current)

                    if new_cost < current_cost:
                        current_cost = new_cost
                        improved = True
                    else:
                        # revert
                        current[q1], current[q2] = chip1, chip2

            if not improved:
                break

        return current

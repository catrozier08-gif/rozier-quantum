# rozier/perception.py
# =========================================================
# PERCEPTION ENGINE
#
# Layer 1 of the reader pipeline.
# Observes circuit and topology structure.
# Classifies shapes. Returns raw observations.
# No judgment — just reads what's there.
#
# Topology shape cache: classify_topology_shape() is
# expensive (graph analysis). Since topology doesn't
# change during a session, we cache the result after
# the first call.
# =========================================================

import networkx as nx
import statistics

from .core import InteractionGraphBuilder


class PerceptionEngine:

    def __init__(self, topology):
        self.topology = topology
        self._topology_shape_cache = None

    # =========================================================
    # TOPOLOGY SHAPE CLASSIFICATION
    # =========================================================

    def classify_topology_shape(self):
        """
        Reads chip_graph structure and returns a shape label.

        Cached after first call — topology doesn't change
        during a session.

        Checks ordered from most specific to least specific
        so a fully_connected graph isn't caught by mesh_like.
        """
        if self._topology_shape_cache is not None:
            return self._topology_shape_cache

        G = self.topology.chip_graph
        n = G.number_of_nodes()
        m = G.number_of_edges()

        if n == 0:
            result = "empty"

        else:
            degrees = [d for _, d in G.degree()]
            max_deg = max(degrees)
            min_deg = min(degrees)
            avg_deg = sum(degrees) / n

            if m == n * (n - 1) / 2:
                result = "fully_connected"

            elif nx.is_connected(G) and all(d == 2 for d in degrees):
                result = "ring"

            elif nx.is_tree(G) and max_deg <= 2:
                result = "line"

            elif max_deg == n - 1 and min_deg == 1:
                result = "star"

            elif max_deg > avg_deg * 2:
                result = "hub_dominant"

            elif nx.is_tree(G):
                result = "tree_like"

            elif nx.is_connected(G) and avg_deg > 2:
                result = "mesh_like"

            else:
                result = "irregular_sparse"

        self._topology_shape_cache = result
        return result

    # =========================================================
    # WORKLOAD SHAPE CLASSIFICATION
    # =========================================================

    def classify_workload_shape(self, interaction_graph):
        """
        Reads interaction graph structure and returns a shape label.

        Skips expensive operations (clustering, diameter,
        variance) for large circuits (n >= 2000) to keep
        performance acceptable at scale.

        Checks ordered: most distinctive patterns first.
        """
        n = interaction_graph.number_of_nodes()

        if n == 0:
            return "empty"

        degrees = dict(interaction_graph.degree())
        degree_values = list(degrees.values())

        avg_degree = sum(degree_values) / n
        max_degree = max(degree_values)
        density = nx.density(interaction_graph)

        large_circuit = n >= 2000

        # Expensive metrics — skip for large circuits
        if not large_circuit:
            try:
                clustering = nx.average_clustering(interaction_graph)
            except Exception:
                clustering = 0.0

            try:
                diameter = nx.diameter(interaction_graph)
            except Exception:
                diameter = 0

            degree_variance = (
                statistics.pvariance(degree_values)
                if len(degree_values) > 1 else 0
            )
        else:
            clustering = 0.0
            diameter = 0
            degree_variance = 0

        # Chain-like: sparse, long diameter
        if avg_degree <= 2.5 and diameter > n / 3:
            return "chain_like"

        # Hub dominated: one node carries most interactions
        if max_degree > avg_degree * 2 and clustering < 0.2:
            return "hub_dominated"

        # Clustered: tight local groups
        if clustering > 0.3 and degree_variance < avg_degree:
            return "clustered"

        # Random-like: moderate density, low clustering
        if density > 0.1 and clustering < 0.3:
            return "random_like"

        return "mixed_structure"

    # =========================================================
    # OBSERVATION
    # =========================================================

    def observe(self, circuit):
        """
        Gathers raw structural observations about the circuit
        and topology.

        Returns both the observation dict AND the interaction
        graph so DiagnosisEngine can reuse it without
        rebuilding.

        Returns:
            observation dict:
                topology: shape, num_chips, capacities, links
                workload: shape, qubits, interactions, avg_degree
            interaction_graph: nx.Graph
        """
        interaction_graph = InteractionGraphBuilder.build(circuit)

        workload_shape = self.classify_workload_shape(interaction_graph)
        topology_shape = self.classify_topology_shape()

        n_nodes = interaction_graph.number_of_nodes()
        total_degree = sum(dict(interaction_graph.degree()).values())

        topology_info = {
            "num_chips": self.topology.num_chips,
            "chip_capacities": self.topology.qubits_per_chip,
            "num_links": self.topology.chip_graph.number_of_edges(),
            "shape": topology_shape,
        }

        workload_info = {
            "num_qubits": circuit.num_qubits,
            "num_interactions": interaction_graph.number_of_edges(),
            "avg_degree": round(total_degree / n_nodes, 3) if n_nodes > 0 else 0,
            "shape": workload_shape,
        }

        observation = {
            "topology": topology_info,
            "workload": workload_info,
        }

        # Return graph alongside observation so callers
        # don't have to rebuild it
        return observation, interaction_graph

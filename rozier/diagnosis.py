# rozier/diagnosis.py
# =========================================================
# DIAGNOSIS ENGINE
#
# Layer 2 of the reader pipeline.
# Receives observations from PerceptionEngine.
# Projects stress, corridor load, concurrency pressure.
# Scores confidence and expected outcome.
# Produces full diagnosis report.
#
# KEY DESIGN:
#   - interaction_graph built ONCE in diagnose()
#     passed to all projection methods
#   - All-pairs shortest paths cached at init
#   - Confidence scorer rewards signal clarity,
#     not just alignment type
#   - Outcome projector uses stretch AND concurrency
# =========================================================

import networkx as nx

from .qubit_health import QubitHealthScanner
from .baselines import QUBIT_HEALTH_BASELINE


# =========================================================
# ALIGNMENT TABLE
#
# Maps (workload_shape, topology_shape) to
# (alignment_label, stress_risk, recommended_action)
#
# Add new validated pairs as you confirm them.
# Anything not listed falls through to moderate_mismatch.
# =========================================================

ALIGNMENT_TABLE = {
    ("chain_like",    "line"):            ("shape_aligned",          "low",      "minimal_intervention"),
    ("chain_like",    "ring"):            ("shape_aligned",          "low",      "minimal_intervention"),
    ("hub_dominated", "star"):            ("shape_aligned",          "low",      "minimal_intervention"),
    ("hub_dominated", "hub_dominant"):    ("shape_aligned",          "low",      "minimal_intervention"),
    ("clustered",     "mesh_like"):       ("shape_aligned",          "low",      "minimal_intervention"),
    ("clustered",     "fully_connected"): ("shape_aligned",          "low",      "minimal_intervention"),
    ("hub_dominated", "line"):            ("hub_on_sparse_topology", "high",     "placement_required"),
    ("hub_dominated", "tree_like"):       ("hub_on_sparse_topology", "high",     "placement_required"),
    ("clustered",     "line"):            ("cluster_on_sparse_topology", "high", "placement_required"),
    ("clustered",     "tree_like"):       ("cluster_on_sparse_topology", "high", "placement_required"),
    ("random_like",   "mesh_like"):       ("moderate_mismatch",      "moderate", "refinement_recommended"),
    ("random_like",   "fully_connected"): ("moderate_mismatch",      "moderate", "refinement_recommended"),
}

# Stress modifier per alignment pair
# Applied to base_cross_chip_prob in project_stress()
# 1.0 = no adjustment (full cross-chip pressure)
STRESS_MODIFIER_TABLE = {
    ("chain_like",    "line"):            0.3,
    ("chain_like",    "ring"):            0.35,
    ("hub_dominated", "star"):            0.4,
    ("hub_dominated", "hub_dominant"):    0.45,
    ("clustered",     "mesh_like"):       0.5,
    ("clustered",     "fully_connected"): 0.5,
    ("clustered",     "line"):            0.9,
    ("clustered",     "tree_like"):       0.9,
}

# Confidence weight table
# Maps alignment label to base confidence score
# Reflects how clearly the diagnosis identifies the problem
ALIGNMENT_CONFIDENCE = {
    "shape_aligned":               0.5,
    "hub_on_sparse_topology":      0.5,
    "cluster_on_sparse_topology":  0.5,
    "moderate_mismatch":           0.2,
}


class DiagnosisEngine:

    def __init__(self, topology, perception_engine,
                 baseline=None):
        self.topology   = topology
        self.perception = perception_engine
        self.health_scanner = QubitHealthScanner(
            topology,
            baseline=baseline or QUBIT_HEALTH_BASELINE,
        )

        # Cache all-pairs shortest paths at init
        # Topology never changes — compute once
        self._all_pairs_paths = self._build_path_cache()

    def _build_path_cache(self):
        """
        Precomputes all-pairs shortest paths on chip graph.
        Called once at init. Eliminates per-pair nx calls
        in project_corridor_stress().
        """
        topo_graph = self.topology.chip_graph
        try:
            return dict(
                nx.all_pairs_shortest_path(topo_graph)
            )
        except Exception:
            return {}

    # =========================================================
    # STRESS PROJECTION
    # =========================================================

    def project_stress(self, interaction_graph,
                       workload_shape, topology_shape):
        """
        Estimates global routing stress.
        Uses STRESS_MODIFIER_TABLE for shape-aware adjustment.
        """
        n = interaction_graph.number_of_nodes()
        total_edges = interaction_graph.number_of_edges()

        if total_edges == 0 or n == 0:
            return {
                "estimated_cross_chip_ratio": 0.0,
                "estimated_avg_path_length": 0.0,
                "projected_stretch": 0.0,
            }

        num_chips = self.topology.num_chips
        base_cross_chip_prob = 1 - (1 / num_chips)

        modifier = STRESS_MODIFIER_TABLE.get(
            (workload_shape, topology_shape), 1.0
        )
        cross_chip_prob = base_cross_chip_prob * modifier
        estimated_cross_chip_ratio = round(cross_chip_prob, 3)

        try:
            avg_path = nx.average_shortest_path_length(
                self.topology.chip_graph, weight="latency"
            )
        except Exception:
            avg_path = 0.0

        projected_stretch = round(
            estimated_cross_chip_ratio * avg_path, 3
        )

        return {
            "estimated_cross_chip_ratio": estimated_cross_chip_ratio,
            "estimated_avg_path_length": round(avg_path, 3),
            "projected_stretch": projected_stretch,
        }

    # =========================================================
    # CORRIDOR STRESS PROJECTION
    # =========================================================

    def project_corridor_stress(self, interaction_graph,
                                workload_shape, topology_shape):
        """
        Distributes expected cross-chip traffic across links.
        Uses precomputed _all_pairs_paths for performance.
        """
        topo_graph = self.topology.chip_graph
        num_chips  = self.topology.num_chips
        total_edges = interaction_graph.number_of_edges()

        if total_edges == 0:
            return {}

        base_cross_chip_prob = 1 - (1 / num_chips)

        if workload_shape == "chain_like" and topology_shape == "line":
            cross_chip_prob = base_cross_chip_prob * 0.3
            central_weight  = 0.8
        elif workload_shape in ("hub_dominated", "clustered") and topology_shape == "line":
            cross_chip_prob = base_cross_chip_prob * 0.9
            central_weight  = 1.2
        else:
            cross_chip_prob = base_cross_chip_prob
            central_weight  = 1.0

        expected_cross = total_edges * cross_chip_prob

        link_load = {
            tuple(sorted(edge)): 0.0
            for edge in topo_graph.edges()
        }

        chip_pairs = [
            (i, j)
            for i in range(num_chips)
            for j in range(i + 1, num_chips)
        ]

        if not chip_pairs:
            return {}

        interaction_per_pair = expected_cross / len(chip_pairs)

        for (i, j) in chip_pairs:
            path = self._all_pairs_paths.get(i, {}).get(j)
            if path is None:
                continue
            for k in range(len(path) - 1):
                edge = tuple(sorted((path[k], path[k + 1])))
                link_load[edge] += interaction_per_pair

        if topology_shape == "line":
            edges = list(link_load.keys())
            if edges:
                center_edge = edges[len(edges) // 2]
                link_load[center_edge] *= central_weight

        total_load = sum(link_load.values())
        if total_load > 0:
            for edge in link_load:
                link_load[edge] = round(
                    link_load[edge] / total_load, 3
                )

        return link_load

    # =========================================================
    # CONCURRENCY PRESSURE
    # =========================================================

    def project_concurrency_pressure(self, interaction_graph):
        """
        Finds highest-degree node in interaction graph.
        Pressure ratio = hub degree / (2 * total edges).
        """
        degrees     = dict(interaction_graph.degree())
        total_edges = interaction_graph.number_of_edges()

        if not degrees or total_edges == 0:
            return {
                "max_node_pressure": 0.0,
                "hub_node": None,
                "pressure_ratio": 0.0,
            }

        hub_node   = max(degrees, key=degrees.get)
        max_degree = degrees[hub_node]
        pressure_ratio = max_degree / (2 * total_edges)

        return {
            "hub_node": hub_node,
            "max_node_pressure": max_degree,
            "pressure_ratio": round(pressure_ratio, 3),
        }

    # =========================================================
    # CONFIDENCE ESTIMATION
    # =========================================================

    def estimate_confidence(self, diagnosis, stress,
                            concurrency):
        """
        Scores diagnostic clarity 0.0 - 1.0.

        Rebuilt to reward SIGNAL CLARITY not just alignment
        type. A clear high-stress diagnosis scores as high
        as a clear low-stress alignment.

        Weights:
            alignment signal clarity:  0.4
                (any named alignment, not just shape_aligned)
            stress risk clarity:       0.3
                (high or low, not moderate)
            stretch definitiveness:    0.2
                (stretch clearly high or clearly low)
            concurrency clarity:       0.1
                (pressure clearly present or clearly absent)
        """
        score = 0.0

        # Alignment signal — any named non-fallback alignment
        alignment = diagnosis["alignment"]
        score += ALIGNMENT_CONFIDENCE.get(alignment, 0.0)

        # Stress risk clarity
        if diagnosis["stress_risk"] in ["high", "low"]:
            score += 0.3

        # Stretch definitiveness
        stretch = stress["projected_stretch"]
        if stretch > 1.5 or stretch < 0.3:
            score += 0.2
        elif stretch > 0.8 or stretch < 0.5:
            score += 0.1

        # Concurrency clarity
        pressure = concurrency["pressure_ratio"]
        if pressure > 0.3 or pressure < 0.05:
            score += 0.1

        score = min(score, 1.0)

        if score >= 0.75:
            level = "high"
        elif score >= 0.45:
            level = "moderate"
        else:
            level = "low"

        return {
            "confidence_score": round(score, 2),
            "confidence_level": level,
        }

    # =========================================================
    # EXPECTED OUTCOME PROJECTION
    # =========================================================

    def project_expected_outcome(self, stretch,
                                 concurrency_ratio,
                                 stress_risk="moderate"):
        """
        Estimates potential improvement from treatment.

        spatial   = placement impact (stretch driven)
        stability = batching/routing impact

        Stability now uses THREE signals:
            1. Concurrency pressure (hub overload)
            2. Stretch magnitude (routing distance stress)
            3. Stress risk label (overall system risk)

        This prevents stability showing 0.0 on high-stress
        circuits where the bottleneck is routing not
        concurrency.
        """
        spatial   = 0.0
        stability = 0.0

        # Spatial: placement can reduce stretch
        if stretch > 1.0:
            spatial = round(min(0.4, stretch * 0.2), 2)

        # Stability signal 1: concurrency pressure
        if concurrency_ratio > 0.3:
            stability = max(
                stability,
                round(min(0.5, concurrency_ratio * 0.6), 2)
            )

        # Stability signal 2: stretch-based routing stress
        if stretch > 3.0:
            stability = max(stability, 0.4)
        elif stretch > 1.5:
            stability = max(stability, 0.25)

        # Stability signal 3: overall stress risk
        if stress_risk == "high":
            stability = max(stability, 0.35)

        stability = round(min(0.5, stability), 2)

        return {
            "expected_spatial_improvement":   spatial,
            "expected_stability_improvement": stability,
        }

    # =========================================================
    # FULL DIAGNOSIS
    # =========================================================

    def diagnose(self, circuit):
        """
        Full diagnosis cycle.

        Builds interaction_graph ONCE and passes it to all
        projection methods. This is the main performance fix
        vs the previous 4x rebuild pattern.

        Returns complete report dict including qubit health
        pre-run scan.
        """
        # Single graph build for the entire cycle
        observation, interaction_graph = (
            self.perception.observe(circuit)
        )

        workload_shape = observation["workload"]["shape"]
        topology_shape = observation["topology"]["shape"]

        stress_projection = self.project_stress(
            interaction_graph, workload_shape, topology_shape
        )
        corridor_projection = self.project_corridor_stress(
            interaction_graph, workload_shape, topology_shape
        )
        concurrency_projection = self.project_concurrency_pressure(
            interaction_graph
        )

        # Alignment lookup — table first, else fallback
        alignment, stress_risk, recommended_action = (
            ALIGNMENT_TABLE.get(
                (workload_shape, topology_shape),
                ("moderate_mismatch", "moderate",
                 "refinement_recommended")
            )
        )

        diagnosis = {
            "alignment":          alignment,
            "stress_risk":        stress_risk,
            "recommended_action": recommended_action,
        }

        confidence = self.estimate_confidence(
            diagnosis,
            stress_projection,
            concurrency_projection,
        )

        expected_outcome = self.project_expected_outcome(
            stress_projection["projected_stretch"],
            concurrency_projection["pressure_ratio"],
            stress_risk=stress_risk,
        )

        # Pre-run qubit health scan
        qubit_health_pre = self.health_scanner.scan_pre(
            circuit,
            interaction_graph,
            corridor_load=corridor_projection,
        )

        return {
            "observation":          observation,
            "diagnosis":            diagnosis,
            "stress_projection":    stress_projection,
            "corridor_projection":  corridor_projection,
            "concurrency_projection": concurrency_projection,
            "confidence":           confidence,
            "expected_outcome":     expected_outcome,
            "qubit_health":         qubit_health_pre,
            # Pass graph through so clinical cycle can reuse
            "_interaction_graph":   interaction_graph,
        }

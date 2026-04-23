# rozier/qubit_health.py
# =========================================================
# QUBIT HEALTH SCANNER
#
# OBD2-style health reader for quantum systems.
# Assigns system-level IDs, scores qubit health against
# baseline, produces pre-run and post-run reports.
#
# System-level ID format:  C{chip}Q{local_index}
#   Example: chip 0, local qubit 3  ->  C0Q3
#
# Health Codes:
#   Q-001  Overloaded         degree exceeds effective threshold
#   Q-002  Decoherence Risk   cross-chip ratio too high
#   Q-003  Entanglement       active qubit, zero local support,
#          Isolation          spread across 2+ remote chips
#   Q-004  Bottleneck         sits on hot corridor link
#   Q-005  Idle               zero interactions
#
# Performance:
#   All qubit->chip lookups O(1) via _qubit_chip_map
#   All label lookups O(1) via id_map
#   Chip computed once per qubit, reused in neighbor loop
#   Corridor hot links precomputed before qubit loop
#
# Dynamic degree threshold:
#   Q-001 threshold scales with circuit avg_degree so
#   dense clustered circuits don't flag every qubit.
#   Effective threshold = max(max_safe_degree,
#                             avg_degree * degree_scale_factor)
# =========================================================

from .baselines import QUBIT_HEALTH_BASELINE


class QubitHealthScanner:

    def __init__(self, topology, baseline=None):
        self.topology = topology
        self.baseline = (
            baseline if baseline is not None
            else QUBIT_HEALTH_BASELINE.copy()
        )

        self.id_map = {}
        self.reverse_map = {}
        self._qubit_chip_map = {}

        self._build_id_map()

    # =========================================================
    # SYSTEM-LEVEL ID MANAGEMENT
    # =========================================================

    def _build_id_map(self):
        """
        Builds three O(1) lookup dicts in a single pass.

        global_index -> "CxQy"  (id_map)
        "CxQy" -> global_index  (reverse_map)
        global_index -> chip    (_qubit_chip_map)
        """
        global_index = 0

        for chip in range(self.topology.num_chips):
            capacity = self.topology.qubits_per_chip[chip]

            for local_index in range(capacity):
                label = f"C{chip}Q{local_index}"
                self.id_map[global_index] = label
                self.reverse_map[label] = global_index
                self._qubit_chip_map[global_index] = chip
                global_index += 1

    def get_label(self, global_index):
        """O(1) system-level label for a global qubit index."""
        return self.id_map.get(global_index, f"Q{global_index}")

    def get_chip_for_qubit(self, global_index):
        """O(1) chip lookup for a global qubit index."""
        return self._qubit_chip_map.get(global_index, -1)

    def resolve_placement(self, placement):
        """
        Converts optimizer placement {global_index: chip}
        to labeled placement {system_label: chip}.
        """
        return {
            self.get_label(q): chip
            for q, chip in placement.items()
        }

    def _effective_degree_threshold(self, interaction_graph):
        """
        Computes the effective Q-001 threshold for this circuit.

        Scales the baseline max_safe_degree up when the circuit's
        natural density is high. This prevents every qubit in a
        dense clustered workload from being flagged as overloaded
        when the density is the circuit's normal operating range.

        Effective threshold = max(
            baseline max_safe_degree,
            avg_degree * degree_scale_factor
        )
        """
        n = interaction_graph.number_of_nodes()
        if n == 0:
            return self.baseline["max_safe_degree"]

        degrees = dict(interaction_graph.degree())
        avg_degree = sum(degrees.values()) / n

        scale_factor = self.baseline.get("degree_scale_factor", 1.5)
        scaled = avg_degree * scale_factor

        return max(self.baseline["max_safe_degree"], scaled)

    # =========================================================
    # PRE-RUN HEALTH SCAN
    # =========================================================

    def scan_pre(self, circuit, interaction_graph,
                 corridor_load=None):
        """
        Pre-run structural health scan.

        Reads starting positions and interaction structure.
        Scores every qubit against baseline.
        Returns forecast report.

        Dynamic threshold: Q-001 scales with circuit density
        so dense circuits don't blanket-flag every qubit.
        """
        baseline = self.baseline

        # Dynamic degree threshold for this circuit
        effective_max_degree = self._effective_degree_threshold(
            interaction_graph
        )

        decohere_thresh   = baseline["decoherence_risk_threshold"]
        bottleneck_thresh = baseline["bottleneck_load_threshold"]
        idle_thresh       = baseline["idle_threshold"]

        degrees = dict(interaction_graph.degree())

        # Precompute hot links by chip
        hot_links_by_chip = {}
        if corridor_load is not None:
            for edge, load in corridor_load.items():
                if load > bottleneck_thresh:
                    for chip in edge:
                        if chip not in hot_links_by_chip:
                            hot_links_by_chip[chip] = []
                        hot_links_by_chip[chip].append(
                            (edge, load)
                        )

        qubit_health = {}
        system_codes = []

        for q in interaction_graph.nodes():
            label = self.get_label(q)
            chip  = self._qubit_chip_map.get(q, -1)
            degree = degrees.get(q, 0)
            codes = []

            # Q-001: Overloaded (dynamic threshold)
            if degree > effective_max_degree:
                codes.append({
                    "code": "Q-001",
                    "name": "Overloaded",
                    "detail": (
                        f"{label} carries {degree} interactions "
                        f"(effective threshold "
                        f"{effective_max_degree:.1f})."
                    ),
                })

            # Single neighbor pass for Q-002 + Q-003
            cross_chip_count = 0
            same_chip_count  = 0
            neighbor_chips   = set()

            for neighbor in interaction_graph.neighbors(q):
                n_chip = self._qubit_chip_map.get(neighbor, -1)
                if n_chip != chip:
                    cross_chip_count += 1
                else:
                    same_chip_count += 1
                neighbor_chips.add(n_chip)

            # Q-002: Decoherence Risk
            if degree > 0:
                cross_ratio = cross_chip_count / degree
                if cross_ratio >= decohere_thresh:
                    codes.append({
                        "code": "Q-002",
                        "name": "Decoherence Risk",
                        "detail": (
                            f"{label} has {cross_ratio:.1%} of "
                            f"its interactions crossing chip "
                            f"boundaries (threshold "
                            f"{decohere_thresh:.1%})."
                        ),
                    })
            else:
                cross_ratio = 0.0

            # Q-003: Entanglement Isolation
            # Only flag when meaningfully active, zero local
            # support, spread across 2+ remote chips
            remote_chips = {
                c for c in neighbor_chips if c != chip
            }
            if (
                degree >= 4
                and len(remote_chips) >= 2
                and same_chip_count == 0
            ):
                codes.append({
                    "code": "Q-003",
                    "name": "Entanglement Isolation",
                    "detail": (
                        f"{label} has {degree} interactions "
                        f"with zero same-chip neighbors, "
                        f"spread across {len(remote_chips)} "
                        f"remote chips: "
                        f"{sorted(remote_chips)}."
                    ),
                })

            # Q-004: Bottleneck Exposure
            if chip in hot_links_by_chip:
                hot = hot_links_by_chip[chip]
                max_hot_edge, max_hot_load = max(
                    hot, key=lambda x: x[1]
                )
                codes.append({
                    "code": "Q-004",
                    "name": "Bottleneck Exposure",
                    "detail": (
                        f"{label} is on chip {chip}, "
                        f"which sits on hot link "
                        f"{max_hot_edge} "
                        f"(load {max_hot_load})."
                    ),
                })

            # Q-005: Idle
            if degree <= idle_thresh:
                codes.append({
                    "code": "Q-005",
                    "name": "Idle",
                    "detail": (
                        f"{label} has no interactions. "
                        f"Capacity may be wasted."
                    ),
                })

            qubit_health[label] = {
                "global_index": q,
                "chip": chip,
                "degree": degree,
                "cross_chip_ratio": round(cross_ratio, 3),
                "codes": codes,
                "status": self._status_from_codes(codes),
            }

            system_codes.extend(codes)

        return {
            "scan_type": "pre_run",
            "effective_degree_threshold": round(
                effective_max_degree, 2
            ),
            "qubit_health": qubit_health,
            "system_codes": system_codes,
            "summary": self._build_summary(
                qubit_health, system_codes
            ),
        }

    # =========================================================
    # POST-RUN HEALTH SCAN
    # =========================================================

    def scan_post(self, circuit, interaction_graph, placement,
                  corridor_load=None, pre_scan=None):
        """
        Post-run health scan with actual placement.
        Uses actual optimizer chip assignments.
        Compares to baseline and optionally to pre-run forecast.
        """
        baseline = self.baseline

        # Use same effective threshold as pre-scan for consistency
        effective_max_degree = self._effective_degree_threshold(
            interaction_graph
        )

        decohere_thresh   = baseline["decoherence_risk_threshold"]
        bottleneck_thresh = baseline["bottleneck_load_threshold"]
        idle_thresh       = baseline["idle_threshold"]

        labeled_placement = self.resolve_placement(placement)

        hot_links_by_chip = {}
        if corridor_load is not None:
            for edge, load in corridor_load.items():
                if load > bottleneck_thresh:
                    for chip in edge:
                        if chip not in hot_links_by_chip:
                            hot_links_by_chip[chip] = []
                        hot_links_by_chip[chip].append(
                            (edge, load)
                        )

        degrees = dict(interaction_graph.degree())
        qubit_health = {}
        system_codes = []

        for q in interaction_graph.nodes():
            label = self.get_label(q)
            chip  = placement.get(
                q, self._qubit_chip_map.get(q, -1)
            )
            degree = degrees.get(q, 0)
            codes  = []

            # Q-001: Overloaded (dynamic threshold)
            if degree > effective_max_degree:
                codes.append({
                    "code": "Q-001",
                    "name": "Overloaded",
                    "detail": (
                        f"{label} carries {degree} interactions "
                        f"after placement (effective threshold "
                        f"{effective_max_degree:.1f})."
                    ),
                })

            # Single neighbor pass
            cross_chip_count = 0
            same_chip_count  = 0
            neighbor_chips   = set()

            for neighbor in interaction_graph.neighbors(q):
                n_chip = placement.get(neighbor, -1)
                if n_chip != chip:
                    cross_chip_count += 1
                else:
                    same_chip_count += 1
                neighbor_chips.add(n_chip)

            # Q-002: Decoherence Risk
            if degree > 0:
                cross_ratio = cross_chip_count / degree
                if cross_ratio >= decohere_thresh:
                    codes.append({
                        "code": "Q-002",
                        "name": "Decoherence Risk",
                        "detail": (
                            f"{label} still has "
                            f"{cross_ratio:.1%} cross-chip "
                            f"interactions after placement."
                        ),
                    })
            else:
                cross_ratio = 0.0

            # Q-003: Entanglement Isolation
            remote_chips = {
                c for c in neighbor_chips if c != chip
            }
            if (
                degree >= 4
                and len(remote_chips) >= 2
                and same_chip_count == 0
            ):
                codes.append({
                    "code": "Q-003",
                    "name": "Entanglement Isolation",
                    "detail": (
                        f"{label} still has {degree} "
                        f"interactions with zero same-chip "
                        f"neighbors after placement, spread "
                        f"across {len(remote_chips)} remote "
                        f"chips."
                    ),
                })

            # Q-004: Bottleneck Exposure
            if chip in hot_links_by_chip:
                hot = hot_links_by_chip[chip]
                max_hot_edge, max_hot_load = max(
                    hot, key=lambda x: x[1]
                )
                codes.append({
                    "code": "Q-004",
                    "name": "Bottleneck Exposure",
                    "detail": (
                        f"{label} placed on chip {chip}, "
                        f"on hot link {max_hot_edge} "
                        f"(load {max_hot_load})."
                    ),
                })

            # Q-005: Idle
            if degree <= idle_thresh:
                codes.append({
                    "code": "Q-005",
                    "name": "Idle",
                    "detail": (
                        f"{label} has no interactions "
                        f"after placement."
                    ),
                })

            qubit_health[label] = {
                "global_index": q,
                "chip": chip,
                "degree": degree,
                "cross_chip_ratio": round(cross_ratio, 3),
                "codes": codes,
                "status": self._status_from_codes(codes),
            }

            system_codes.extend(codes)

        result = {
            "scan_type": "post_run",
            "effective_degree_threshold": round(
                effective_max_degree, 2
            ),
            "labeled_placement": labeled_placement,
            "qubit_health": qubit_health,
            "system_codes": system_codes,
            "summary": self._build_summary(
                qubit_health, system_codes
            ),
        }

        if pre_scan is not None:
            result["differential"] = self._build_differential(
                pre_scan, qubit_health
            )

        return result

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    def _status_from_codes(self, codes):
        """
        Priority:
            critical -> Q-001 or Q-002
            warning  -> Q-003 or Q-004
            idle     -> Q-005 only
            healthy  -> no codes
        """
        code_ids = {c["code"] for c in codes}

        if "Q-001" in code_ids or "Q-002" in code_ids:
            return "critical"
        if "Q-003" in code_ids or "Q-004" in code_ids:
            return "warning"
        if "Q-005" in code_ids:
            return "idle"
        return "healthy"

    def _build_summary(self, qubit_health, system_codes):
        status_counts = {
            "healthy": 0, "warning": 0,
            "critical": 0, "idle": 0,
        }
        code_counts = {}

        for data in qubit_health.values():
            status = data["status"]
            status_counts[status] = (
                status_counts.get(status, 0) + 1
            )
            for c in data["codes"]:
                code_id = c["code"]
                code_counts[code_id] = (
                    code_counts.get(code_id, 0) + 1
                )

        return {
            "total_qubits_scanned": len(qubit_health),
            "status_counts": status_counts,
            "code_counts": code_counts,
        }

    def _build_differential(self, pre_scan, post_health):
        pre_health = pre_scan["qubit_health"]
        rank = {
            "critical": 3, "warning": 2,
            "idle": 1, "healthy": 0, "unknown": -1,
        }

        improved  = []
        regressed = []
        unchanged = []

        all_labels = (
            set(pre_health.keys()) | set(post_health.keys())
        )

        for label in all_labels:
            pre_status = pre_health.get(
                label, {}
            ).get("status", "unknown")
            post_status = post_health.get(
                label, {}
            ).get("status", "unknown")

            pre_rank  = rank.get(pre_status,  -1)
            post_rank = rank.get(post_status, -1)

            entry = {
                "label":       label,
                "pre_status":  pre_status,
                "post_status": post_status,
            }

            if post_rank < pre_rank:
                improved.append(entry)
            elif post_rank > pre_rank:
                regressed.append(entry)
            else:
                unchanged.append(entry)

        return {
            "improved":        improved,
            "regressed":       regressed,
            "unchanged":       unchanged,
            "net_improvement": len(improved) - len(regressed),
        }

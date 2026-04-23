# rozier/path_mapper.py
# =========================================================
# PATH MAPPER
#
# Builds system-level qubit path data and ASCII maps.
# Uses system-level IDs from QubitHealthScanner.
#
# Two modes:
#   map_interaction_paths()  - shows qubit interaction paths
#                              through the topology
#   map_chip_corridors()     - shows chip-to-chip link load
#                              as an ASCII corridor map
#
# This file is data + ASCII now.
# Rendering hooks (matplotlib, web) slot in later
# without changing the data structures.
# =========================================================

import networkx as nx


class PathMapper:

    def __init__(self, topology, health_scanner):
        """
        Args:
            topology:       MultiChipTopology
            health_scanner: QubitHealthScanner
                            (provides system-level ID resolution)
        """
        self.topology = topology
        self.scanner = health_scanner

    # =========================================================
    # INTERACTION PATH MAPPING
    # =========================================================

    def map_interaction_paths(self, interaction_graph, placement=None):
        """
        For every edge in the interaction graph, builds the
        chip-level routing path between the two qubits.

        If placement is provided (post-run), uses actual chip
        assignments. Otherwise uses structural chip assignment
        from system ID map.

        Returns:
            list of path_entry dicts, one per interaction edge.

        Each path_entry:
            {
                "qubit_a":      system label
                "qubit_b":      system label
                "chip_a":       int
                "chip_b":       int
                "chip_path":    [chip_0, chip_1, ...] topology route
                "hops":         number of chip boundaries crossed
                "cross_chip":   bool
                "weight":       interaction count on this edge
            }
        """
        paths = []
        topo_graph = self.topology.chip_graph

        for u, v, data in interaction_graph.edges(data=True):
            label_u = self.scanner.get_label(u)
            label_v = self.scanner.get_label(v)

            if placement is not None:
                chip_u = placement.get(u, self.scanner.get_chip_for_qubit(u))
                chip_v = placement.get(v, self.scanner.get_chip_for_qubit(v))
            else:
                chip_u = self.scanner.get_chip_for_qubit(u)
                chip_v = self.scanner.get_chip_for_qubit(v)

            weight = data.get("weight", 1)

            if chip_u == chip_v:
                chip_path = [chip_u]
                hops = 0
                cross_chip = False
            else:
                try:
                    chip_path = nx.shortest_path(topo_graph, chip_u, chip_v)
                    hops = len(chip_path) - 1
                    cross_chip = True
                except nx.NetworkXNoPath:
                    chip_path = []
                    hops = -1
                    cross_chip = True

            paths.append({
                "qubit_a": label_u,
                "qubit_b": label_v,
                "chip_a": chip_u,
                "chip_b": chip_v,
                "chip_path": chip_path,
                "hops": hops,
                "cross_chip": cross_chip,
                "weight": weight,
            })

        # Sort by hops descending — longest/most stressed paths first
        paths.sort(key=lambda x: x["hops"], reverse=True)

        return paths

    # =========================================================
    # ASCII PATH RENDERING
    # =========================================================

    def render_paths_ascii(self, paths, max_display=20):
        """
        Renders the top N interaction paths as ASCII.

        Example output:

            === INTERACTION PATH MAP ===

            C0Q3 ──── C1Q7       (local, 0 hops, weight 3)
            C0Q1 ══╦══ C1Q4      (cross-chip, 1 hop, weight 2)
            C0Q2 ══╦══ C2Q9      (cross-chip, 2 hops, weight 1)
                   ║
               [C1 corridor]

        Args:
            paths:       output of map_interaction_paths()
            max_display: cap display at this many paths

        Returns:
            string — ready to print
        """
        lines = []
        lines.append("=== INTERACTION PATH MAP ===")
        lines.append("")

        display = paths[:max_display]

        for p in display:
            a = p["qubit_a"]
            b = p["qubit_b"]
            hops = p["hops"]
            weight = p["weight"]
            chip_path = p["chip_path"]

            if not p["cross_chip"]:
                connector = "────"
                tag = f"(local, 0 hops, weight {weight})"
                lines.append(f"  {a} {connector} {b}   {tag}")

            else:
                if hops == 1:
                    connector = "══╦══"
                    tag = f"(cross-chip, {hops} hop, weight {weight})"
                    lines.append(f"  {a} {connector} {b}   {tag}")
                    lines.append(f"       ║")
                    if len(chip_path) >= 2:
                        lines.append(
                            f"   [C{chip_path[0]}→C{chip_path[1]} corridor]"
                        )

                else:
                    # Multi-hop: show intermediate chips
                    tag = f"(cross-chip, {hops} hops, weight {weight})"
                    corridor_str = " → ".join(f"C{c}" for c in chip_path)
                    lines.append(f"  {a} ══...══ {b}   {tag}")
                    lines.append(f"       path: {corridor_str}")

            lines.append("")

        if len(paths) > max_display:
            lines.append(
                f"  ... {len(paths) - max_display} more paths not shown "
                f"(increase max_display to see all)"
            )
            lines.append("")

        return "\n".join(lines)

    # =========================================================
    # CORRIDOR LOAD MAP
    # =========================================================

    def map_chip_corridors(self, corridor_load):
        """
        Builds a data structure describing each chip-to-chip
        link with its load and status.

        Args:
            corridor_load: dict {(chip_a, chip_b): load}
                           from DiagnosisEngine.project_corridor_stress()

        Returns:
            list of corridor_entry dicts
        """
        corridors = []

        for edge, load in corridor_load.items():
            chip_a, chip_b = edge

            if load > 0.5:
                status = "critical"
            elif load > 0.35:
                status = "hot"
            elif load > 0.15:
                status = "moderate"
            else:
                status = "light"

            corridors.append({
                "link": edge,
                "chip_a": chip_a,
                "chip_b": chip_b,
                "load": load,
                "status": status,
            })

        corridors.sort(key=lambda x: x["load"], reverse=True)

        return corridors

    def render_corridors_ascii(self, corridor_load):
        """
        Renders corridor load as an ASCII chip map.

        Example:

            === CHIP CORRIDOR MAP ===

            C0 ══[0.45 HOT]══ C1 ──[0.20 mod]── C2 ──[0.10 lite]── C3

        Returns:
            string — ready to print
        """
        corridors = self.map_chip_corridors(corridor_load)

        # Index by link for quick lookup
        load_index = {c["link"]: c for c in corridors}

        topo_graph = self.topology.chip_graph
        num_chips = self.topology.num_chips

        lines = []
        lines.append("=== CHIP CORRIDOR MAP ===")
        lines.append("")

        # Try to render as a line if topology is line-shaped
        # For other topologies, fall back to list format
        if self._is_line_topology():
            chip_line = []

            for chip in range(num_chips):
                chip_line.append(f"C{chip}")

                if chip < num_chips - 1:
                    edge = tuple(sorted((chip, chip + 1)))
                    corridor = load_index.get(edge)

                    if corridor:
                        load = corridor["load"]
                        status = corridor["status"].upper()[:3]

                        if corridor["status"] in ["critical", "hot"]:
                            connector = f" ══[{load:.2f} {status}]══ "
                        else:
                            connector = f" ──[{load:.2f} {status}]── "

                        chip_line.append(connector)
                    else:
                        chip_line.append(" ── ")

            lines.append("  " + "".join(chip_line))

        else:
            # Non-line topology: list each link
            for c in corridors:
                edge = c["link"]
                load = c["load"]
                status = c["status"].upper()
                bar = self._load_bar(load)
                lines.append(
                    f"  C{edge[0]} <──> C{edge[1]}  "
                    f"{bar}  {load:.3f}  [{status}]"
                )

        lines.append("")

        return "\n".join(lines)

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    def _is_line_topology(self):
        """
        Returns True if topology chip_graph is a line/path graph.
        Used to choose ASCII render style.
        """
        G = self.topology.chip_graph
        n = G.number_of_nodes()

        if n == 0:
            return False

        degrees = [d for _, d in G.degree()]

        return (
            nx.is_tree(G)
            and max(degrees) <= 2
        )

    def _load_bar(self, load, width=10):
        """
        Renders a simple ASCII load bar.
        Example: [████░░░░░░]  0.4
        """
        filled = int(load * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

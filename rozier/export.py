# rozier/export.py
# =========================================================
# EXPORT MODULE
#
# Converts SystemReader reports to shareable formats:
#   - JSON (machine-readable, API-friendly)
#   - Markdown (human-readable, converts to PDF)
#   - PDF (requires pandoc installed)
#
# Usage:
#   from rozier.export import export_json, export_markdown
#   export_json(report, "report.json", vendor="ibm")
#   export_markdown(report, "report.md", vendor="ibm")
# =========================================================

import json
from datetime import datetime
from .version import __version__
from .vendors import get_vendor_profile, translate_term


def _make_json_safe(obj):
    """
    Recursively converts a report dict to JSON-safe types.
    Tuple keys become string keys. Sets become sorted lists.
    """
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            if isinstance(k, tuple):
                str_key = f"{k[0]},{k[1]}"
            else:
                str_key = k
            clean[str_key] = _make_json_safe(v)
        return clean

    elif isinstance(obj, (list, tuple)):
        return [_make_json_safe(i) for i in obj]

    elif isinstance(obj, set):
        return sorted([_make_json_safe(i) for i in obj])

    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    else:
        return str(obj)


def export_json(report, filepath, vendor="generic", indent=2):
    """
    Exports prescribe() report to JSON file.
    Strips internal keys. Adds metadata header.
    """
    clean_report = {
        k: v for k, v in report.items()
        if not k.startswith("_")
    }

    profile = get_vendor_profile(vendor)

    output = {
        "meta": {
            "generator": "Rozier Quantum SystemReader",
            "version": __version__,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "vendor_profile": profile["name"],
        },
        "report": clean_report,
    }

    safe_output = _make_json_safe(output)

    with open(filepath, "w") as f:
        json.dump(safe_output, f, indent=indent)

    print(f"Exported JSON: {filepath}")


def export_markdown(report, filepath, vendor="generic",
                    circuit_name="Unnamed Circuit",
                    include_health_details=True,
                    max_flagged_qubits=20):
    """
    Exports prescribe() report to Markdown file.
    Converts to PDF via pandoc if needed.
    """
    profile = get_vendor_profile(vendor)
    term = lambda t: translate_term(t, vendor)

    topo         = report["observation"]["topology"]
    work         = report["observation"]["workload"]
    diag         = report["diagnosis"]
    stress       = report["stress_projection"]
    corridor     = report["corridor_projection"]
    concurrency  = report["concurrency_projection"]
    confidence   = report["confidence"]
    outcome      = report["expected_outcome"]
    health       = report.get("qubit_health", {})
    prescription = report.get("prescription", {})

    lines = []

    # --- Header ---
    lines.append("# Rozier Quantum — Structural Analysis Report")
    lines.append("")
    lines.append(f"**Circuit:** {circuit_name}  ")
    lines.append(f"**Vendor Profile:** {profile['name']}  ")
    lines.append(
        f"**Generated:** "
        f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  "
    )
    lines.append(
        f"**Rozier Quantum SystemReader** v{__version__}  "
    )
    lines.append(
        "[rozierquantum.com](https://rozierquantum.com)  "
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- Executive Summary ---
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Workload Shape | `{work['shape']}` |")
    lines.append(f"| Topology Shape | `{topo['shape']}` |")
    lines.append(f"| Alignment | `{diag['alignment']}` |")
    lines.append(
        f"| Stress Risk | **{diag['stress_risk'].upper()}** |"
    )
    lines.append(
        f"| Confidence | {confidence['confidence_level']} "
        f"({confidence['confidence_score']}) |"
    )
    lines.append(
        f"| Recommended Action | "
        f"`{diag['recommended_action']}` |"
    )
    lines.append(
        f"| Prescription | "
        f"`{prescription.get('tool', 'N/A')}` / "
        f"`{prescription.get('mode', 'N/A')}` |"
    )
    lines.append("")

    # --- Vendor Terminology ---
    lines.append("## Vendor Terminology")
    lines.append("")
    lines.append(f"- **Cross-chip:** {term('cross_chip')}")
    lines.append(f"- **Corridor:** {term('corridor')}")
    lines.append(f"- **Bottleneck:** {term('bottleneck')}")
    lines.append(f"- **Placement:** {term('placement')}")
    lines.append(f"- **Interaction:** {term('interaction')}")
    lines.append("")

    # --- Hardware Topology ---
    lines.append("## Hardware Topology")
    lines.append("")
    lines.append(f"- **Shape:** {topo['shape']}")
    lines.append(f"- **Chips:** {topo['num_chips']}")
    lines.append(f"- **Links:** {topo['num_links']}")
    lines.append(
        f"- **Capacity:** {topo['chip_capacities']} qubits/chip"
    )
    lines.append("")

    # --- Workload Structure ---
    lines.append("## Workload Structure")
    lines.append("")
    lines.append(f"- **Shape:** {work['shape']}")
    lines.append(f"- **Qubits:** {work['num_qubits']:,}")
    lines.append(
        f"- **{term('interaction').title()}s:** "
        f"{work['num_interactions']:,}"
    )
    lines.append(f"- **Avg Degree:** {work['avg_degree']}")
    lines.append("")

    # --- Stress Projection ---
    lines.append("## Projected Stress")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(
        f"| {term('cross_chip').title()} Ratio | "
        f"{stress['estimated_cross_chip_ratio']} |"
    )
    lines.append(
        f"| Avg Path Length | "
        f"{stress['estimated_avg_path_length']} |"
    )
    lines.append(
        f"| Projected Stretch | "
        f"{stress['projected_stretch']} |"
    )
    lines.append("")

    # --- Corridor Load ---
    if corridor:
        lines.append(
            f"## {term('corridor').title()} Load Distribution"
        )
        lines.append("")
        lines.append("| Link | Load | Status |")
        lines.append("|------|------|--------|")

        for edge, load in sorted(
            corridor.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if load > 0.5:
                status = "🔴 CRITICAL"
            elif load > 0.35:
                status = "🟠 HOT"
            elif load > 0.15:
                status = "🟡 MODERATE"
            else:
                status = "🟢 LIGHT"
            lines.append(f"| {edge} | {load:.3f} | {status} |")

        lines.append("")

        # Bottleneck interpretation using vendor term
        max_link = max(corridor, key=corridor.get)
        max_load = corridor[max_link]
        lines.append(
            f"Highest {term('bottleneck')} occurs on link "
            f"{max_link} with normalized load {max_load:.3f}."
        )
        lines.append("")

    # --- Concurrency ---
    lines.append("## Concurrency Pressure")
    lines.append("")
    lines.append(f"- **Hub Node:** {concurrency['hub_node']}")
    lines.append(
        f"- **Max Degree:** "
        f"{concurrency['max_node_pressure']}"
    )
    lines.append(
        f"- **Pressure Ratio:** "
        f"{concurrency['pressure_ratio']}"
    )
    lines.append("")

    # --- Treatment Projection ---
    lines.append("## Projected Treatment Impact")
    lines.append("")
    lines.append(
        f"- **Spatial Improvement Potential:** "
        f"{outcome['expected_spatial_improvement']}"
    )
    lines.append(
        f"- **Stability Improvement Potential:** "
        f"{outcome['expected_stability_improvement']}"
    )
    lines.append("")

    # --- Qubit Health ---
    if health:
        summary       = health.get("summary", {})
        status_counts = summary.get("status_counts", {})
        code_counts   = summary.get("code_counts", {})

        lines.append("## Qubit Health Scan  *(pre-run)*")
        lines.append("")
        lines.append(
            f"**Scanned:** "
            f"{summary.get('total_qubits_scanned', 0):,} qubits"
        )
        lines.append("")
        lines.append("| Status | Count |")
        lines.append("|--------|-------|")
        lines.append(
            f"| 🟢 Healthy  | "
            f"{status_counts.get('healthy', 0):,} |"
        )
        lines.append(
            f"| 🟡 Warning  | "
            f"{status_counts.get('warning', 0):,} |"
        )
        lines.append(
            f"| 🔴 Critical | "
            f"{status_counts.get('critical', 0):,} |"
        )
        lines.append(
            f"| ⚪ Idle     | "
            f"{status_counts.get('idle', 0):,} |"
        )
        lines.append("")

        if code_counts:
            lines.append("### Health Codes Triggered")
            lines.append("")
            lines.append("| Code | Name | Count |")
            lines.append("|------|------|-------|")

            code_names = {
                "Q-001": "Overloaded",
                "Q-002": "Decoherence Risk",
                "Q-003": "Entanglement Isolation",
                "Q-004": "Bottleneck Exposure",
                "Q-005": "Idle",
            }

            for code, count in sorted(code_counts.items()):
                name = code_names.get(code, "")
                lines.append(
                    f"| {code} | {name} | {count:,} |"
                )
            lines.append("")

        if include_health_details:
            qubit_health = health.get("qubit_health", {})
            flagged = {
                label: data
                for label, data in qubit_health.items()
                if data.get("status") != "healthy"
            }

            if flagged:
                severity = {
                    "critical": 0,
                    "warning": 1,
                    "idle": 2,
                }
                sorted_flagged = sorted(
                    flagged.items(),
                    key=lambda x: (
                        severity.get(x[1]["status"], 3),
                        -x[1]["degree"],
                        x[0],
                    )
                )

                display = sorted_flagged[:max_flagged_qubits]

                lines.append(
                    "### Flagged Qubits — Top Issues"
                )
                lines.append("")
                lines.append(
                    "| Qubit | Chip | Status | "
                    "Degree | Cross-Chip | Codes |"
                )
                lines.append(
                    "|-------|------|--------|"
                    "--------|------------|-------|"
                )

                icons = {
                    "critical": "🔴",
                    "warning": "🟡",
                    "idle": "⚪",
                }

                for label, data in display:
                    icon = icons.get(data["status"], "⚪")
                    codes_str = ", ".join(
                        c["code"] for c in data["codes"]
                    )
                    lines.append(
                        f"| {label} "
                        f"| {data['chip']} "
                        f"| {icon} {data['status']} "
                        f"| {data['degree']} "
                        f"| {data['cross_chip_ratio']:.1%} "
                        f"| {codes_str} |"
                    )

                lines.append("")

                remaining = (
                    len(flagged) - max_flagged_qubits
                )
                if remaining > 0:
                    lines.append(
                        f"*... and {remaining:,} more flagged "
                        f"qubits. Increase `max_flagged_qubits` "
                        f"to see all.*"
                    )
                    lines.append("")
            else:
                lines.append(
                    "*All qubits within baseline parameters.*"
                )
                lines.append("")

    # --- Footer ---
    lines.append("---")
    lines.append("")
    lines.append(
        f"*Generated by "
        f"[Rozier Quantum](https://rozierquantum.com) "
        f"SystemReader v{__version__}*"
    )
    lines.append("")

    with open(filepath, "w") as f:
        f.write("\n".join(lines))

    print(f"Exported Markdown: {filepath}")


def export_pdf(report, filepath, vendor="generic", **kwargs):
    """
    Exports to PDF via Markdown intermediate.
    Requires pandoc installed on system.
    """
    import subprocess

    md_path = filepath.replace(".pdf", "_report.md")
    export_markdown(report, md_path, vendor=vendor, **kwargs)

    try:
        subprocess.run(
            [
                "pandoc", md_path,
                "-o", filepath,
                "--pdf-engine=pdflatex",
                "-V", "geometry:margin=1in",
            ],
            check=True,
            capture_output=True,
        )
        print(f"Exported PDF: {filepath}")

    except FileNotFoundError:
        print("PDF export requires pandoc. Install with:")
        print("  macOS:   brew install pandoc")
        print("  Linux:   apt install pandoc")
        print("  Windows: choco install pandoc")
        print(f"Markdown saved at: {md_path}")

    except subprocess.CalledProcessError as e:
        print(f"PDF conversion failed: {e.stderr.decode()}")
        print(f"Markdown saved at: {md_path}")
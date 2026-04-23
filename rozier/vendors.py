# rozier/vendors.py
# =========================================================
# VENDOR PROFILES
#
# Maps vendor-specific terminology, topology patterns,
# and baseline specs. Allows reports to speak the
# language of the target platform.
#
# Supported:
#   - ibm (Qiskit, Heavy-Hex topology)
#   - google (Cirq, Sycamore topology)
#   - ionq (Trapped ion, all-to-all connectivity)
#   - rigetti (Aspen topology)
#   - rozier (Rozier Quantum architecture)
#   - generic (Default, no vendor assumptions)
# =========================================================


VENDOR_PROFILES = {

    "ibm": {
        "name": "IBM Quantum",
        "topology_type": "heavy_hex",
        "qubit_label_format": "Q{index}",
        "chip_label_format": "Chip {index}",
        "terminology": {
            "cross_chip": "inter-chip link",
            "corridor": "coupling map edge",
            "decoherence_risk": "T2 degradation risk",
            "bottleneck": "routing congestion",
            "placement": "qubit mapping",
            "interaction": "two-qubit gate",
        },
        "baseline_overrides": {
            "max_safe_degree": 6,
            "decoherence_risk_threshold": 0.6,
            "bottleneck_load_threshold": 0.30,
        },
        "notes": "Heavy-hex topology, 127-1121 qubit systems, Qiskit Runtime",
    },

    "google": {
        "name": "Google Quantum AI",
        "topology_type": "sycamore",
        "qubit_label_format": "q{index}",
        "chip_label_format": "Processor {index}",
        "terminology": {
            "cross_chip": "inter-processor link",
            "corridor": "coupler",
            "decoherence_risk": "dephasing risk",
            "bottleneck": "coupler saturation",
            "placement": "qubit assignment",
            "interaction": "two-qubit operation",
        },
        "baseline_overrides": {
            "max_safe_degree": 4,
            "decoherence_risk_threshold": 0.65,
            "bottleneck_load_threshold": 0.35,
        },
        "notes": "Sycamore grid topology, Cirq framework",
    },

    "ionq": {
        "name": "IonQ",
        "topology_type": "all_to_all",
        "qubit_label_format": "ion{index}",
        "chip_label_format": "Trap {index}",
        "terminology": {
            "cross_chip": "inter-trap shuttle",
            "corridor": "ion transport channel",
            "decoherence_risk": "motional heating risk",
            "bottleneck": "shuttle congestion",
            "placement": "ion assignment",
            "interaction": "Mølmer-Sørensen gate",
        },
        "baseline_overrides": {
            "max_safe_degree": 10,
            "decoherence_risk_threshold": 0.8,
            "bottleneck_load_threshold": 0.5,
        },
        "notes": "Trapped ion, all-to-all within trap, shuttle between traps",
    },

    "rigetti": {
        "name": "Rigetti Computing",
        "topology_type": "aspen",
        "qubit_label_format": "q{index}",
        "chip_label_format": "Tile {index}",
        "terminology": {
            "cross_chip": "inter-tile link",
            "corridor": "octagonal coupler",
            "decoherence_risk": "T1 decay risk",
            "bottleneck": "tile boundary congestion",
            "placement": "qubit allocation",
            "interaction": "CZ gate",
        },
        "baseline_overrides": {
            "max_safe_degree": 4,
            "decoherence_risk_threshold": 0.6,
            "bottleneck_load_threshold": 0.35,
        },
        "notes": "Aspen octagonal tile topology, PyQuil/Quil framework",
    },

    "rozier": {
        "name": "Rozier Quantum",
        "topology_type": "rozier_architecture",
        "qubit_label_format": "C{chip}Q{local}",
        "chip_label_format": "Node {index}",
        "terminology": {
            "cross_chip": "inter-node link",
            "corridor": "structural corridor",
            "decoherence_risk": "coherence stress",
            "bottleneck": "corridor saturation",
            "placement": "structural placement",
            "interaction": "entanglement edge",
        },
        "baseline_overrides": {},
        "notes": "Rozier Quantum architecture",
    },

    "generic": {
        "name": "Generic Quantum System",
        "topology_type": "unknown",
        "qubit_label_format": "C{chip}Q{local}",
        "chip_label_format": "Chip {index}",
        "terminology": {
            "cross_chip": "cross-chip",
            "corridor": "corridor",
            "decoherence_risk": "decoherence risk",
            "bottleneck": "bottleneck",
            "placement": "placement",
            "interaction": "interaction",
        },
        "baseline_overrides": {},
        "notes": "Generic system, no vendor-specific assumptions",
    },
}


def get_vendor_profile(vendor="generic"):
    """Returns profile dict for a vendor. Falls back to generic."""
    return VENDOR_PROFILES.get(vendor.lower(), VENDOR_PROFILES["generic"])


def list_vendors():
    """Returns list of supported vendor keys."""
    return list(VENDOR_PROFILES.keys())


def translate_term(term, vendor="generic"):
    """
    Translates a generic term to vendor-specific terminology.

    Example:
        translate_term("bottleneck", "ibm")
        -> "routing congestion"
    """
    profile = get_vendor_profile(vendor)
    return profile["terminology"].get(term, term)

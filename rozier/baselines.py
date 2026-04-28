# rozier/baselines.py
# =========================================================
# QUBIT HEALTH BASELINE CONFIGURATION
#
# "Factory spec" values the health scanner measures against.
# Think of this as your OBD2 spec sheet — the values a
# healthy qubit system should fall within.
#
# Override any value by passing a modified dict to:
#   QubitHealthScanner(topology, baseline=your_baseline)
#
# degree_scale_factor
#   When present, the health scanner adjusts max_safe_degree
#   dynamically based on the circuit's observed average
#   degree. This prevents every qubit in a dense clustered
#   circuit from being flagged as overloaded when high
#   density is the circuit's normal operating range.
#
#   Effective threshold = max(
#       max_safe_degree,
#       avg_degree * degree_scale_factor
#   )
#
#   1.5 means: flag qubits carrying 50% more than average.
#   Raise this to 2.0 for very dense circuits.
#   Lower to 1.2 for strict mode.
# =========================================================

QUBIT_HEALTH_BASELINE = {

    # ── Q-001: Overloaded ─────────────────────────────────
    # Maximum interactions before overload flag.
    # This is the floor. For dense circuits the scanner
    # will automatically scale up via degree_scale_factor.
    "max_safe_degree": 6,

    # Dynamic scaling factor for Q-001 threshold.
    # Effective threshold = max(
    #     max_safe_degree,
    #     avg_degree * degree_scale_factor
    # )
    "degree_scale_factor": 1.5,

    # ── Q-002: Decoherence Risk ───────────────────────────
    # Cross-chip interaction fraction before
    # decoherence risk is flagged per qubit.
    "decoherence_risk_threshold": 0.7,

    # ── Q-003: System Cross-Chip ──────────────────────────
    # System-level cross-chip fraction before
    # system flag is raised.
    "max_safe_cross_chip_ratio": 0.6,

    # ── Q-004: Bottleneck Exposure ────────────────────────
    # Corridor load above which a link is considered hot.
    "bottleneck_load_threshold": 0.35,

    # ── Q-005: Idle ───────────────────────────────────────
    # Interactions at or below this count = idle qubit.
    "idle_threshold": 0,
}


# =========================================================
# VENDOR-SPECIFIC BASELINE OVERRIDES
#
# Use these when analyzing a specific vendor's hardware.
# Pass the relevant dict to QubitHealthScanner as baseline.
#
# Example:
#   from rozier.baselines import IBM_BASELINE
#   scanner = QubitHealthScanner(topology, baseline=IBM_BASELINE)
# =========================================================

IBM_BASELINE = {
    **QUBIT_HEALTH_BASELINE,
    # IBM heavy-hex topology has lower natural degree
    # so we tighten the overload threshold slightly
    "max_safe_degree": 5,
    "degree_scale_factor": 1.4,
    "decoherence_risk_threshold": 0.65,
    "bottleneck_load_threshold": 0.30,
}

GOOGLE_BASELINE = {
    **QUBIT_HEALTH_BASELINE,
    # Google Sycamore grid is denser
    # so we allow slightly higher natural degree
    "max_safe_degree": 7,
    "degree_scale_factor": 1.6,
    "decoherence_risk_threshold": 0.72,
    "bottleneck_load_threshold": 0.38,
}

IONQ_BASELINE = {
    **QUBIT_HEALTH_BASELINE,
    # IonQ all-to-all connectivity means every qubit
    # can naturally reach every other qubit
    # so degree flags are less meaningful
    "max_safe_degree": 12,
    "degree_scale_factor": 2.0,
    "decoherence_risk_threshold": 0.80,
    "bottleneck_load_threshold": 0.50,
}
# rozier/__init__.py

from .version import __version__
from .api import preflight, analyze, RozierOptimizer, summarize_result
from .topology import MultiChipTopology, build_line_topology
from .perception import PerceptionEngine
from .diagnosis import DiagnosisEngine
from .qubit_health import QubitHealthScanner
from .path_mapper import PathMapper
from .baselines import (
    QUBIT_HEALTH_BASELINE,
    IBM_BASELINE,
    GOOGLE_BASELINE,
    IONQ_BASELINE,
)
from .vendors import (
    VENDOR_PROFILES,
    get_vendor_profile,
    list_vendors,
    translate_term,
)
from .export import export_json, export_markdown, export_pdf
from .optimizer import StablePlacementOptimizer
from .reader import SystemReader

__all__ = [
    # Core API
    "preflight",
    "analyze",
    "RozierOptimizer",
    "summarize_result",

    # Topology
    "MultiChipTopology",
    "build_line_topology",

    # Reader pipeline
    "SystemReader",
    "PerceptionEngine",
    "DiagnosisEngine",
    "QubitHealthScanner",
    "PathMapper",
    "StablePlacementOptimizer",

    # Configuration
    "QUBIT_HEALTH_BASELINE",
    "IBM_BASELINE",
    "GOOGLE_BASELINE",
    "IONQ_BASELINE",
    "VENDOR_PROFILES",
    "get_vendor_profile",
    "list_vendors",
    "translate_term",

    # Export
    "export_json",
    "export_markdown",
    "export_pdf",

    # Version
    "__version__",
]
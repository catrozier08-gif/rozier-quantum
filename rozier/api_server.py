# rozier/api_server.py
# =========================================================
# ROZIER QUANTUM — API SERVER
#
# FastAPI server exposing SystemReader as a REST API.
#
# Install server dependencies:
#   pip install rozier-quantum[server]
#
# Run locally:
#   uvicorn rozier.api_server:app --host 0.0.0.0 --port 8000
#
# Endpoints:
#   GET  /                  health check
#   GET  /vendors           list supported vendors
#   POST /analyze           full structural analysis
#   POST /preflight         quick preflight check
#
# rozierquantum.com
# =========================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import time

from .topology import MultiChipTopology, build_line_topology
from .reader import SystemReader
from .export import _make_json_safe
from .vendors import list_vendors, get_vendor_profile
from .version import __version__


app = FastAPI(
    title="Rozier Quantum SystemReader API",
    description=(
        "Structural diagnostic tool for multi-chip quantum systems. "
        "Reads, diagnoses, and prescribes for any quantum topology."
    ),
    version=__version__,
    contact={
        "name": "Rozier Quantum LLC",
        "url": "https://rozierquantum.com",
        "email": "contact@rozierquantum.com",
    },
)


# =========================================================
# REQUEST / RESPONSE MODELS
# =========================================================

class TopologySpec(BaseModel):
    num_chips: int = Field(
        ..., ge=2, le=1000,
        description="Number of chips in topology"
    )
    qubits_per_chip: int = Field(
        ..., ge=1, le=10000,
        description="Qubits per chip (uniform)"
    )
    topology_type: str = Field(
        "line",
        description="Topology shape: line (more types coming)"
    )


class AnalyzeRequest(BaseModel):
    qasm: str = Field(
        ...,
        description="OpenQASM 2.0 or 3.0 circuit string"
    )
    topology: TopologySpec
    vendor: str = Field(
        "generic",
        description="Vendor profile: ibm, google, ionq, rigetti, rozier, generic"
    )
    include_health_details: bool = Field(
        False,
        description="Include per-qubit health details in response"
    )


class PreflightRequest(BaseModel):
    qasm: str = Field(..., description="OpenQASM circuit string")
    topology: TopologySpec


# =========================================================
# CIRCUIT LOADING
# =========================================================

def load_circuit_from_qasm(qasm_string: str):
    """
    Loads a QuantumCircuit from QASM string.
    Tries QASM 3 first, falls back to QASM 2.
    """
    try:
        from qiskit.qasm3 import loads as qasm3_loads
        return qasm3_loads(qasm_string)
    except Exception:
        pass

    try:
        from qiskit import QuantumCircuit
        return QuantumCircuit.from_qasm_str(qasm_string)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse QASM circuit: {str(e)}"
        )


def build_topology(spec: TopologySpec) -> MultiChipTopology:
    """
    Builds topology from spec.
    Currently supports line topology.
    More topologies coming.
    """
    if spec.topology_type == "line":
        return build_line_topology(
            num_chips=spec.num_chips,
            qubits_per_chip=spec.qubits_per_chip,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Topology type '{spec.topology_type}' not yet supported. "
                f"Currently supported: line"
            )
        )


# =========================================================
# ENDPOINTS
# =========================================================

@app.get("/")
def health_check():
    """Health check and version info."""
    return {
        "status": "ok",
        "service": "Rozier Quantum SystemReader API",
        "version": __version__,
        "website": "https://rozierquantum.com",
    }


@app.get("/vendors")
def get_vendors():
    """List supported vendor profiles."""
    vendors = {}
    for key in list_vendors():
        profile = get_vendor_profile(key)
        vendors[key] = {
            "name": profile["name"],
            "topology_type": profile["topology_type"],
            "notes": profile["notes"],
        }
    return {"supported_vendors": vendors}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Full structural analysis.

    Submit a QASM circuit and topology spec.
    Returns complete diagnostic report including
    qubit health scan, stress projection, and prescription.

    Response includes timing metadata.
    """
    t_start = time.time()

    circuit = load_circuit_from_qasm(request.qasm)
    topology = build_topology(request.topology)
    reader = SystemReader(topology)

    t_read = time.time()
    report = reader.prescribe(circuit)
    t_done = time.time()

    # Strip internal keys, make JSON-safe
    clean = {
        k: v for k, v in report.items()
        if not k.startswith("_")
    }

    # If health details not requested, replace with summary only
    if not request.include_health_details and "qubit_health" in clean:
        clean["qubit_health"] = {
            "scan_type": clean["qubit_health"]["scan_type"],
            "summary": clean["qubit_health"]["summary"],
        }

    safe_report = _make_json_safe(clean)

    return {
        "meta": {
            "version": __version__,
            "vendor_profile": request.vendor,
            "circuit_qubits": circuit.num_qubits,
            "topology_chips": topology.num_chips,
            "analysis_time_seconds": round(t_done - t_read, 3),
            "total_time_seconds": round(t_done - t_start, 3),
        },
        "report": safe_report,
    }


@app.post("/preflight")
def preflight(request: PreflightRequest):
    """
    Quick preflight check — no optimization, just observation.

    Faster than /analyze. Use this to get a quick read on
    circuit/topology fit before committing to full analysis.
    """
    t_start = time.time()

    circuit = load_circuit_from_qasm(request.qasm)
    topology = build_topology(request.topology)

    from .api import preflight as rozier_preflight
    result = rozier_preflight(topology, circuit)

    t_done = time.time()

    return {
        "meta": {
            "version": __version__,
            "circuit_qubits": circuit.num_qubits,
            "topology_chips": topology.num_chips,
            "total_time_seconds": round(t_done - t_start, 3),
        },
        "result": _make_json_safe(result),
    }
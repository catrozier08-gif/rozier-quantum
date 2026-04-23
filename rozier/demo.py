# rozier/demo.py
# =========================================================
# ROZIER QUANTUM — SystemReader Demo
#
# Run:
#   python -m rozier.demo
#   python -m rozier.demo --qubits 1000 --depth 5000 --chips 8
#   python -m rozier.demo --vendor ibm --export
#
# rozierquantum.com
# =========================================================

import argparse
import time
import random
from qiskit import QuantumCircuit


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rozier Quantum SystemReader Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m rozier.demo
  python -m rozier.demo --qubits 1000 --depth 5000 --chips 8
  python -m rozier.demo --vendor ibm --export
        """
    )
    parser.add_argument(
        "--qubits", type=int, default=500,
        help="Number of qubits (default: 500)"
    )
    parser.add_argument(
        "--depth", type=int, default=2000,
        help="Circuit depth / gate count (default: 2000)"
    )
    parser.add_argument(
        "--chips", type=int, default=4,
        help="Number of chips (default: 4)"
    )
    parser.add_argument(
        "--qubits-per-chip", type=int, default=None,
        help="Qubits per chip (default: qubits / chips)"
    )
    parser.add_argument(
        "--vendor", type=str, default="generic",
        choices=[
            "ibm", "google", "ionq",
            "rigetti", "rozier", "generic",
        ],
        help="Vendor profile (default: generic)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Export JSON and Markdown reports"
    )
    parser.add_argument(
        "--clinical", action="store_true",
        help="Run full clinical cycle"
    )
    return parser.parse_args()


def build_circuit(num_qubits, depth, seed):
    random.seed(seed)
    qc = QuantumCircuit(num_qubits)
    for _ in range(depth):
        q1, q2 = random.sample(range(num_qubits), 2)
        qc.cx(q1, q2)
    return qc


def main():
    args = parse_args()

    qpc = args.qubits_per_chip or max(
        1, args.qubits // args.chips
    )

    print()
    print("=" * 56)
    print("  ROZIER QUANTUM — SystemReader")
    print("  rozierquantum.com")
    print("=" * 56)
    print()
    print(f"  Qubits:          {args.qubits:,}")
    print(f"  Gate depth:      {args.depth:,}")
    print(f"  Chips:           {args.chips}")
    print(f"  Qubits/chip:     {qpc}")
    print(f"  Vendor profile:  {args.vendor}")
    print(f"  Seed:            {args.seed}")
    print()

    from rozier import SystemReader, build_line_topology

    print("Building circuit...")
    t0 = time.time()
    circuit = build_circuit(args.qubits, args.depth, args.seed)
    t1 = time.time()
    print(f"  Done in {t1 - t0:.2f}s")
    print()

    topology = build_line_topology(
        num_chips=args.chips,
        qubits_per_chip=qpc,
    )

    reader = SystemReader(topology)

    print("Running structural analysis...")
    t2 = time.time()
    report = reader.prescribe(circuit)
    t3 = time.time()
    print(f"  Done in {t3 - t2:.3f}s")
    print()

    print(reader.generate_report(circuit))

    if args.export:
        from rozier import export_json, export_markdown

        json_path = (
            f"rozier_report_{args.qubits}q_{args.vendor}.json"
        )
        md_path = (
            f"rozier_report_{args.qubits}q_{args.vendor}.md"
        )

        export_json(report, json_path, vendor=args.vendor)
        export_markdown(
            report,
            md_path,
            vendor=args.vendor,
            circuit_name=(
                f"{args.qubits:,} Qubit / "
                f"{args.depth:,} Gate Demo Circuit"
            ),
            max_flagged_qubits=15,
        )
        print()
        print("Reports saved:")
        print(f"  {json_path}")
        print(f"  {md_path}")

    if args.clinical:
        print()
        print("Running clinical cycle...")
        reader.run_clinical_cycle(circuit)

    print()
    print("=" * 56)
    print("  Analysis complete.")
    print("  rozierquantum.com | contact@rozierquantum.com")
    print("=" * 56)
    print()


if __name__ == "__main__":
    main()

# Security Policy — Rozier Quantum

## Our Commitment
Rozier Quantum is built for use in secure,
air-gapped laboratory and enterprise environments.
We take security seriously at every level of the stack.

---

## Zero Network Calls
The rozier-quantum package does not make any
network calls at runtime.

Specifically, the package does NOT import:
- requests
- urllib (beyond stdlib path utilities)
- socket
- httpx
- aiohttp
- paramiko
- ftplib
- or any other networking library

All analysis is performed entirely on the local machine.
No data is transmitted to any external server.
No telemetry is collected.
No API keys are required.

This has been verified by static audit:

    python -m twine check dist/*
    grep -r "import requests" rozier  → No results
    grep -r "import socket" rozier    → No results
    grep -r "import urllib" rozier    → No results

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.3.x   | Yes       |
| 1.2.x   | No        |
| < 1.2   | No        |

---

## Reporting a Vulnerability
If you discover a security issue in rozier-quantum,
please report it privately before public disclosure.

Contact: chris.rozier@rozierquantum.com

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact assessment

We will respond within 48 hours and work
with you on a responsible disclosure timeline.

---

## License
rozier-quantum is released under the Apache 2.0 License.
See LICENSE for full terms including patent grant language.

Rozier Quantum LLC
rozierquantum.com

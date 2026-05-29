"""Binary allowlist — only explicitly listed binaries may be executed.

Adding a binary here does NOT grant permission to use it in production.
Each binary must also be configured per ScanProfile and per Program.
Tool execution is only permitted from the worker service (D-09).
"""
from __future__ import annotations

# Binaries that the system knows about. Keys are canonical names,
# values are the expected executable names (searched in PATH).
# NOTE: These are NOT all enabled by default. ScanProfile controls enablement.
ALLOWED_BINARIES: dict[str, str] = {
    # Passive recon
    "subfinder": "subfinder",
    "assetfinder": "assetfinder",
    "chaos": "chaos",
    # DNS
    "dnsx": "dnsx",
    "puredns": "puredns",
    "massdns": "massdns",
    # HTTP probing (medium mode only)
    "httpx": "httpx",
    # Crawling (medium mode only)
    "katana": "katana",
    # URL harvesting (passive)
    "gau": "gau",
    "waybackurls": "waybackurls",
    # Screenshots (medium mode only)
    "gowitness": "gowitness",
    # Scanning (active mode only — never default)
    "naabu": "naabu",
    "nuclei": "nuclei",
    # Active scanners (require explicit confirmation)
    "nmap": "nmap",
    "ffuf": "ffuf",
    "feroxbuster": "feroxbuster",
    "arjun": "arjun",
    # Secret detection (passive)
    "trufflehog": "trufflehog",
    "gitleaks": "gitleaks",
    # Utilities (post-processing, no network)
    "jq": "jq",
    "anew": "anew",
    "uro": "uro",
}


class BinaryNotAllowedError(ValueError):
    """Raised when a binary is not in the allowlist."""


def assert_binary_allowed(binary_name: str) -> str:
    """Return the executable name if allowed, raise BinaryNotAllowedError otherwise."""
    if binary_name not in ALLOWED_BINARIES:
        raise BinaryNotAllowedError(
            f"Binary '{binary_name}' is not in the allowlist. "
            "Add it to ALLOWED_BINARIES with justification before using."
        )
    return ALLOWED_BINARIES[binary_name]

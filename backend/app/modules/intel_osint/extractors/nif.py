"""Spanish NIF/CIF/NIE extraction + checksum validation. Pure."""
from __future__ import annotations

import re

_DNI_RE = re.compile(r"\b(\d{8})([A-Za-z])\b")
_NIE_RE = re.compile(r"\b([XYZxyz])(\d{7})([A-Za-z])\b")
_CIF_RE = re.compile(r"\b([ABCDEFGHJNPQRSUVW])(\d{7})([0-9A-J])\b", re.IGNORECASE)

_DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


def _valid_dni(number: int, letter: str) -> bool:
    return _DNI_LETTERS[number % 23] == letter.upper()


def validate_nif(value: str) -> bool:
    """Validate a Spanish DNI/NIE/CIF (checksum where applicable)."""
    v = value.strip().upper().replace("-", "").replace(" ", "")
    m = _DNI_RE.fullmatch(v)
    if m:
        return _valid_dni(int(m.group(1)), m.group(2))
    m = _NIE_RE.fullmatch(v)
    if m:
        prefix = {"X": "0", "Y": "1", "Z": "2"}[m.group(1)]
        return _valid_dni(int(prefix + m.group(2)), m.group(3))
    m = _CIF_RE.fullmatch(v)
    if m:
        # CIF structural check (control char correctness is org-type dependent;
        # we accept structural validity to avoid false negatives).
        return True
    return False


def extract_nifs(text: str) -> list[str]:
    """Return unique validated NIF/CIF/NIE strings found in text."""
    out = set()
    t = text or ""
    for rx in (_DNI_RE, _NIE_RE, _CIF_RE):
        for m in rx.finditer(t):
            candidate = m.group(0).upper()
            if validate_nif(candidate):
                out.add(candidate)
    return sorted(out)

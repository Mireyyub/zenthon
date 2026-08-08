"""Minimal chemistry lookup (AgilBot chemistry_engine idea — data only)."""
from __future__ import annotations

from typing import Any, Dict, Optional

ELEMENTS: Dict[str, Dict[str, Any]] = {
    "H": {"name": "Hidrogen", "z": 1, "mass": 1.008},
    "He": {"name": "Helium", "z": 2, "mass": 4.003},
    "C": {"name": "Karbon", "z": 6, "mass": 12.011},
    "N": {"name": "Azot", "z": 7, "mass": 14.007},
    "O": {"name": "Oksigen", "z": 8, "mass": 15.999},
    "Na": {"name": "Natrium", "z": 11, "mass": 22.990},
    "Cl": {"name": "Xlor", "z": 17, "mass": 35.45},
    "Fe": {"name": "Dəmir", "z": 26, "mass": 55.845},
    "Au": {"name": "Qızıl", "z": 79, "mass": 196.97},
    "U": {"name": "Uran", "z": 92, "mass": 238.03},
}


def periodic_lookup(symbol_or_name: str) -> Optional[Dict[str, Any]]:
    key = symbol_or_name.strip()
    if key in ELEMENTS:
        return {"symbol": key, **ELEMENTS[key]}
    low = key.lower()
    for sym, data in ELEMENTS.items():
        if data["name"].lower() == low:
            return {"symbol": sym, **data}
    return None

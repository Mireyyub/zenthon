"""
LEGACY ML/DL models — NOT part of Leon cognitive core.

See LEGACY.md and ARCHITECTURE.md.
Do not import from cognitive modules (brain, knowledge, memory, learning).
"""

import warnings

warnings.warn(
    "models package is LEGACY and optional. Use Leon cognitive path "
    "(brain.reasoning, knowledge, memory) instead.",
    DeprecationWarning,
    stacklevel=2,
)

"""
LEGACY training stack — NOT Leon cognitive learning.

Cognitive learning: learning.engine.LearningEngine + curriculum.
See LEGACY.md.
"""

import warnings

warnings.warn(
    "training package is LEGACY ML. Prefer learning.engine + curriculum for Leon.",
    DeprecationWarning,
    stacklevel=2,
)

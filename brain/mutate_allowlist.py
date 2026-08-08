"""Mutable path policy for Leon self-mutation.

security/, core kernel paths, and self_mutate itself stay forbidden.
"""

ALLOWED_PREFIXES = (
    "curriculum/volumes/",
    "genome/",
    "schemas/",
    "multimodal/",
    "learning/",
    "knowledge/",
    "memory/",
    "agents/",
    "brain/",
    "evaluation/",
    "docs/",
    "tools/",
    "interfaces/cli/",
)

FORBIDDEN_PREFIXES = (
    "security/",
    "core/kernel",
    "core/bootstrap",
    "core/config",
    "core/service_registry",
    ".git/",
    "venv/",
    ".venv/",
    "__pycache__/",
    "brain/self_mutate.py",
    "brain/mutate_allowlist.py",
)

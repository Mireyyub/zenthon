"""Bind shared mutate allowlist into SelfMutateEngine module globals."""

from __future__ import annotations


def bind_mutate_policy() -> bool:
    try:
        from brain import mutate_allowlist as pol
        import brain.self_mutate as sm

        sm.ALLOWED_PREFIXES = tuple(pol.ALLOWED_PREFIXES)
        sm.FORBIDDEN_PREFIXES = tuple(pol.FORBIDDEN_PREFIXES)
        return True
    except Exception:
        return False


# auto-bind on import
BOUND = bind_mutate_policy()

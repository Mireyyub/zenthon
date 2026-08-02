"""Async wrappers for ThinkingBrain and orchestrator."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Union


async def run_in_executor(fn, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


class AsyncThinkingMixin:
    """Mixin: athink() → thread pool-da sinxron think."""

    async def athink(
        self,
        input_data: Union[str, Dict[str, Any], List[Any]],
        goal: Optional[str] = None,
        reasoning_mode: str = "auto",
        max_steps: int = 8,
        allow_rethink: bool = True,
        use_knowledge: bool = True,
    ) -> Dict[str, Any]:
        return await run_in_executor(
            self.think,
            input_data,
            goal=goal,
            reasoning_mode=reasoning_mode,
            max_steps=max_steps,
            allow_rethink=allow_rethink,
            use_knowledge=use_knowledge,
        )

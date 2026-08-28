"""Research Agent – retrieve + curriculum + optional LLM summary via LLMProvider."""

from __future__ import annotations

from typing import Any, Dict, Optional

from agents.base import BaseAgent, AgentResult
from core.logger import logger


class ResearchAgent(BaseAgent):
    PRODUCTION = False  # experimental but functional

    def __init__(self, name: str = "ResearchAgent", description: str = "Araşdırma və xülasə"):
        super().__init__(name=name, description=description)

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        logger.info(f"ResearchAgent: {task[:80]}")
        context = context or {}
        snippets = []
        sources = []

        # 1) Curriculum exact/fuzzy
        try:
            from curriculum import CurriculumEngine

            ans = CurriculumEngine().ask(task)
            if ans.get("matched") and ans.get("answer"):
                snippets.append(str(ans["answer"]))
                sources.append(ans.get("source") or "curriculum")
        except Exception as e:
            logger.debug(f"research curriculum: {e}")

        # 2) Unified retrieve / GraphRAG
        try:
            from memory.retrieve import retrieve

            ret = retrieve(task, top_k=6)
            for c in ret.get("candidates") or []:
                snippets.append(c.get("content", ""))
                sources.append(c.get("source", "retrieve"))
        except Exception:
            try:
                from knowledge.graphrag import GraphRAG

                gr = GraphRAG().retrieve(task, top_k=5)
                snippets.extend(gr.get("combined") or [])
                sources.append("graphrag")
            except Exception as e:
                logger.debug(f"research retrieve: {e}")

        # 3) Optional LLM synthesis via provider
        synthesis = None
        llm_used = False
        provider_name = None
        try:
            from brain.llm.provider import get_llm_provider

            provider = get_llm_provider()
            provider_name = provider.name
            if provider.is_available and snippets:
                ctx = "\n".join(f"- {s}" for s in snippets[:8] if s)
                comp = provider.complete(
                    f"Sual: {task}\n\nMəlumat:\n{ctx}\n\nQısa, dəqiq cavab yaz.",
                    system="Sən araşdırma xülasəçisisən. Yalnız verilən məlumata əsaslan.",
                    temperature=0.2,
                    max_tokens=400,
                )
                if comp.ok:
                    synthesis = comp.text
                    llm_used = True
        except Exception:
            pass

        if not snippets and not synthesis:
            return AgentResult(
                success=False,
                error="Heç bir evidence tapılmadı",
                metadata={"experimental": True},
            )

        output = synthesis or (snippets[0] if snippets else "")
        return AgentResult(
            success=True,
            output=output,
            metadata={
                "snippets": snippets[:10],
                "sources": sources[:10],
                "llm_used": llm_used,
                "provider": provider_name,
                "experimental": True,
            },
        )

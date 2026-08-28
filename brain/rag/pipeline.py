"""
RAG Pipeline — from Drive zenthon_v08, adapted for Leon.
Chunk → hybrid retrieve → optional LLM generate (via LLMProvider).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import logger


@dataclass
class Document:
    doc_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    content: str
    embedding: Optional[List[float]] = None
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


@dataclass
class RetrievedContext:
    chunks: List[Chunk]
    combined_text: str
    sources: List[str]
    total_chunks: int
    query_rewritten: Optional[str] = None


class TextChunker:
    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _extract_keywords(self, text: str, n: int = 8) -> List[str]:
        words = re.findall(r"[\wəıöüğçşƏIÖÜĞÇŞ]{3,}", text.lower())
        from collections import Counter

        return [w for w, _ in Counter(words).most_common(n)]

    def chunk(
        self, text: str, doc_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks: List[Chunk] = []
        current: List[str] = []
        current_len = 0
        for sent in sentences:
            if not sent:
                continue
            if current_len + len(sent) > self.chunk_size and current:
                chunk_text = " ".join(current)
                cid = hashlib.md5(f"{doc_id}:{len(chunks)}:{chunk_text[:40]}".encode()).hexdigest()[
                    :12
                ]
                chunks.append(
                    Chunk(
                        chunk_id=cid,
                        doc_id=doc_id,
                        content=chunk_text,
                        keywords=self._extract_keywords(chunk_text),
                        metadata=metadata or {},
                    )
                )
                overlap_text = chunk_text[-self.overlap :] if self.overlap else ""
                current = [overlap_text, sent] if overlap_text else [sent]
                current_len = sum(len(x) for x in current)
            else:
                current.append(sent)
                current_len += len(sent)
        if current:
            chunk_text = " ".join(current)
            cid = hashlib.md5(f"{doc_id}:{len(chunks)}:{chunk_text[:40]}".encode()).hexdigest()[:12]
            chunks.append(
                Chunk(
                    chunk_id=cid,
                    doc_id=doc_id,
                    content=chunk_text,
                    keywords=self._extract_keywords(chunk_text),
                    metadata=metadata or {},
                )
            )
        return chunks


class RAGPipeline:
    def __init__(self, persist_dir: Optional[str] = None):
        try:
            from core.config import config

            base = Path(config.path.leon_dir) / "rag"
        except Exception:
            base = Path("data/leon/rag")
        self.dir = Path(persist_dir) if persist_dir else base
        self.dir.mkdir(parents=True, exist_ok=True)
        self.chunker = TextChunker()
        self._chunks: List[Chunk] = []
        self._docs: Dict[str, Document] = {}

    def ingest_text(
        self, text: str, source: str = "manual", doc_id: Optional[str] = None
    ) -> Document:
        doc_id = doc_id or hashlib.md5(text[:80].encode()).hexdigest()[:12]
        doc = Document(doc_id=doc_id, content=text, source=source)
        self._docs[doc_id] = doc
        for ch in self.chunker.chunk(text, doc_id, {"source": source}):
            self._chunks.append(ch)
        logger.info(f"RAG ingest {doc_id} chunks={len(self._chunks)}")
        return doc

    def retrieve(self, query: str, top_k: int = 5) -> RetrievedContext:
        q_words = set(re.findall(r"[\wəıöüğçş]{3,}", query.lower()))
        scored: List[Chunk] = []
        for ch in self._chunks:
            kw = set(ch.keywords) | set(re.findall(r"[\wəıöüğçş]{3,}", ch.content.lower()))
            overlap = len(q_words & kw)
            if overlap:
                c = Chunk(**{**ch.__dict__, "score": float(overlap)})
                scored.append(c)
        scored.sort(key=lambda x: x.score, reverse=True)
        top = scored[:top_k]
        combined = "\n\n".join(c.content for c in top)
        sources = list({c.metadata.get("source", c.doc_id) for c in top})
        return RetrievedContext(
            chunks=top, combined_text=combined, sources=sources, total_chunks=len(top)
        )

    def query(self, question: str, top_k: int = 5, generate: bool = False) -> Dict[str, Any]:
        ctx = self.retrieve(question, top_k=top_k)
        answer = None
        llm_meta: Dict[str, Any] = {}
        if generate and ctx.combined_text:
            try:
                from brain.llm.provider import get_llm_provider

                provider = get_llm_provider()
                prompt = (
                    f"Kontekst:\n{ctx.combined_text[:2000]}\n\nSual: {question}\nCavab:"
                )
                comp = provider.complete(
                    prompt, system="Kontekstə əsaslan.", max_tokens=400
                )
                if comp.ok and comp.text:
                    answer = comp.text
                    llm_meta = {
                        "provider": comp.provider,
                        "model": comp.model,
                        "latency_ms": comp.latency_ms,
                    }
                else:
                    answer = f"[generate failed] {comp.error or 'empty'}"
            except Exception as e:
                answer = f"[generate failed] {e}"
        out: Dict[str, Any] = {
            "question": question,
            "context": ctx.combined_text,
            "sources": ctx.sources,
            "chunks": len(ctx.chunks),
            "answer": answer,
        }
        if llm_meta:
            out["llm"] = llm_meta
        return out

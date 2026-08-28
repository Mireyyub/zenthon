"""
RAG Pipeline — chunk → hybrid retrieve → optional LLM generate (LLMProvider).
Phase 8: disk persist under data/leon/rag.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import logger
from core.persistence import write_json, read_json


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "content": self.content,
            "keywords": list(self.keywords),
            "metadata": dict(self.metadata),
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Chunk":
        return cls(
            chunk_id=str(d.get("chunk_id") or ""),
            doc_id=str(d.get("doc_id") or ""),
            content=str(d.get("content") or ""),
            keywords=list(d.get("keywords") or []),
            metadata=dict(d.get("metadata") or {}),
            score=float(d.get("score") or 0),
        )


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
    def __init__(self, persist_dir: Optional[str] = None, auto_load: bool = True):
        try:
            from core.config import config

            base = Path(config.path.leon_dir) / "rag"
        except Exception:
            base = Path("data/leon/rag")
        self.dir = Path(persist_dir) if persist_dir else base
        self.dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.dir / "index.json"
        self.chunker = TextChunker()
        self._chunks: List[Chunk] = []
        self._docs: Dict[str, Document] = {}
        if auto_load:
            self.load()

    def ingest_text(
        self, text: str, source: str = "manual", doc_id: Optional[str] = None
    ) -> Document:
        doc_id = doc_id or hashlib.md5(text[:80].encode()).hexdigest()[:12]
        doc = Document(doc_id=doc_id, content=text, source=source)
        self._docs[doc_id] = doc
        for ch in self.chunker.chunk(text, doc_id, {"source": source}):
            self._chunks.append(ch)
        self.save()
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
        meta: Dict[str, Any] = {}
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
                if comp.ok:
                    answer = comp.text
                    meta = {
                        "provider": comp.provider,
                        "model": comp.model,
                        "latency_ms": comp.latency_ms,
                    }
                else:
                    answer = f"[generate failed] {comp.error}"
            except Exception as e:
                answer = f"[generate failed] {e}"
        return {
            "question": question,
            "context": ctx.combined_text,
            "sources": ctx.sources,
            "chunks": len(ctx.chunks),
            "answer": answer,
            "generate_meta": meta,
            "persisted_chunks": len(self._chunks),
        }

    def save(self) -> None:
        payload = {
            "version": 1,
            "saved_at": datetime.now().isoformat(),
            "chunks": [c.to_dict() for c in self._chunks],
            "docs": {
                did: {
                    "doc_id": d.doc_id,
                    "content": d.content[:2000],
                    "source": d.source,
                    "created_at": d.created_at,
                }
                for did, d in self._docs.items()
            },
        }
        write_json(self._index_path, payload)

    def load(self) -> int:
        data = read_json(self._index_path, default={})
        if not isinstance(data, dict):
            return 0
        self._chunks = [Chunk.from_dict(c) for c in (data.get("chunks") or []) if isinstance(c, dict)]
        docs_raw = data.get("docs") or {}
        self._docs = {}
        for did, d in docs_raw.items():
            if isinstance(d, dict):
                self._docs[did] = Document(
                    doc_id=str(d.get("doc_id") or did),
                    content=str(d.get("content") or ""),
                    source=str(d.get("source") or "unknown"),
                    created_at=str(d.get("created_at") or ""),
                )
        return len(self._chunks)

    def stats(self) -> Dict[str, Any]:
        return {
            "chunks": len(self._chunks),
            "docs": len(self._docs),
            "index_path": str(self._index_path),
            "index_exists": self._index_path.exists(),
        }

    def clear(self) -> None:
        self._chunks.clear()
        self._docs.clear()
        self.save()

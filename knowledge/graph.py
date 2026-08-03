"""
Knowledge Graph — LEON canonical semantic store (spec 005 / 021).
Disk persistence (Faza 1).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
import uuid

from core.persistence import write_json, read_json

NODE_TYPES = {"Entity", "Concept", "Event", "Rule", "Procedure", "entity", "concept", "object"}
EDGE_TYPES = {
    "is_a",
    "instance_of",
    "part_of",
    "has_property",
    "causes",
    "depends_on",
    "before",
    "after",
    "related_to",
    "located_in",
    "contains",
}


class KnowledgeGraph:
    def __init__(self, path: Optional[Path | str] = None, auto_persist: bool = True):
        if path is None:
            try:
                from core.config import config

                path = config.path.graph_dir / "graph.json"
            except Exception:
                path = Path("data/leon/graph/graph.json")
        self.path = Path(path)
        self.auto_persist = auto_persist
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Dict[str, Any]] = []
        self.load()

    def _persist(self) -> None:
        if self.auto_persist:
            self.save()

    def create_node(
        self,
        name: str,
        node_type: str = "Entity",
        attributes: Optional[Dict] = None,
        description: str = "",
        confidence: float = 1.0,
        source: str = "",
    ) -> str:
        return self.add_node(
            name,
            node_type=node_type,
            properties={
                **(attributes or {}),
                "description": description,
                "confidence": confidence,
                "source": source,
            },
        )

    def add_node(self, label: str, node_type: str = "entity", properties: Optional[Dict] = None) -> str:
        existing = self.find_by_label(label)
        exact = [n for n in existing if n["label"].lower() == label.lower()]
        if exact:
            return exact[0]["id"]
        node_id = "N-" + str(uuid.uuid4())[:10]
        self._nodes[node_id] = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "properties": properties or {},
            "created_at": datetime.now().isoformat(),
            "version": 1,
        }
        self._persist()
        return node_id

    def update_node(self, node_id: str, **fields) -> bool:
        n = self._nodes.get(node_id)
        if not n:
            return False
        if "label" in fields:
            n["label"] = fields["label"]
        if "type" in fields:
            n["type"] = fields["type"]
        if "properties" in fields and isinstance(fields["properties"], dict):
            n["properties"].update(fields["properties"])
        n["version"] = int(n.get("version", 1)) + 1
        self._persist()
        return True

    def link_nodes(
        self,
        source_id: str,
        target_id: str,
        relation: str = "related_to",
        weight: float = 1.0,
        confidence: float = 1.0,
    ) -> None:
        self.add_edge(source_id, target_id, relation, weight=weight, confidence=confidence)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
        confidence: float = 1.0,
    ) -> None:
        if source_id not in self._nodes or target_id not in self._nodes:
            raise ValueError("Both nodes must exist")
        self._edges.append({
            "source": source_id,
            "target": target_id,
            "relation": relation,
            "weight": weight,
            "confidence": confidence,
        })
        self._persist()

    def unlink_nodes(self, source_id: str, target_id: str, relation: Optional[str] = None) -> int:
        before = len(self._edges)
        self._edges = [
            e for e in self._edges
            if not (
                e["source"] == source_id
                and e["target"] == target_id
                and (relation is None or e["relation"] == relation)
            )
        ]
        removed = before - len(self._edges)
        if removed:
            self._persist()
        return removed

    def get_node(self, node_id: str) -> Optional[Dict]:
        return self._nodes.get(node_id)

    def find_by_label(self, label: str) -> List[Dict]:
        q = label.lower()
        return [n for n in self._nodes.values() if q in n["label"].lower()]

    def neighbors(self, node_id: str) -> List[Tuple[Dict, str]]:
        result = []
        for e in self._edges:
            if e["source"] == node_id and e["target"] in self._nodes:
                result.append((self._nodes[e["target"]], e["relation"]))
            elif e["target"] == node_id and e["source"] in self._nodes:
                result.append((self._nodes[e["source"]], e["relation"]))
        return result

    def query(self, text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        scored: List[Tuple[float, Dict]] = []
        q = text.lower()
        for n in self._nodes.values():
            score = 0.0
            if q == n["label"].lower():
                score = 1.0
            elif q in n["label"].lower():
                score = 0.7
            elif any(q in str(v).lower() for v in (n.get("properties") or {}).values()):
                score = 0.4
            if score > 0:
                scored.append((score, n))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [n for _, n in scored[:top_k]]

    def validate_integrity(self) -> Dict[str, Any]:
        issues = []
        for e in self._edges:
            if e["source"] not in self._nodes or e["target"] not in self._nodes:
                issues.append(f"orphan_edge:{e}")
        is_a_adj: Dict[str, List[str]] = {}
        for e in self._edges:
            if e["relation"] == "is_a":
                is_a_adj.setdefault(e["source"], []).append(e["target"])

        def has_cycle(start: str, seen: Set[str]) -> bool:
            if start in seen:
                return True
            seen = set(seen)
            seen.add(start)
            for nxt in is_a_adj.get(start, []):
                if has_cycle(nxt, seen):
                    return True
            return False

        for nid in is_a_adj:
            if has_cycle(nid, set()):
                issues.append(f"circular_is_a:{nid}")
                break

        return {"ok": len(issues) == 0, "issues": issues}

    def stats(self) -> Dict[str, int]:
        return {"nodes": len(self._nodes), "edges": len(self._edges)}

    def clear(self) -> None:
        self._nodes.clear()
        self._edges.clear()
        self._persist()

    def save(self) -> None:
        write_json(self.path, {"nodes": self._nodes, "edges": self._edges})

    def load(self) -> Dict[str, int]:
        data = read_json(self.path, default={})
        if not isinstance(data, dict):
            return self.stats()
        nodes = data.get("nodes") or {}
        edges = data.get("edges") or []
        if isinstance(nodes, dict):
            self._nodes = nodes
        if isinstance(edges, list):
            self._edges = edges
        return self.stats()

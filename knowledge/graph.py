"""Knowledge Graph – düyünlər və əlaqələr."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
import uuid


class KnowledgeGraph:
    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Dict[str, Any]] = []

    def add_node(self, label: str, node_type: str = "entity", properties: Optional[Dict] = None) -> str:
        node_id = str(uuid.uuid4())[:10]
        self._nodes[node_id] = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "properties": properties or {},
            "created_at": datetime.now().isoformat(),
        }
        return node_id

    def add_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0) -> None:
        if source_id not in self._nodes or target_id not in self._nodes:
            raise ValueError("Both nodes must exist")
        self._edges.append({
            "source": source_id,
            "target": target_id,
            "relation": relation,
            "weight": weight,
        })

    def get_node(self, node_id: str) -> Optional[Dict]:
        return self._nodes.get(node_id)

    def find_by_label(self, label: str) -> List[Dict]:
        q = label.lower()
        return [n for n in self._nodes.values() if q in n["label"].lower()]

    def neighbors(self, node_id: str) -> List[Tuple[Dict, str]]:
        """(node, relation) siyahısı."""
        result = []
        for e in self._edges:
            if e["source"] == node_id and e["target"] in self._nodes:
                result.append((self._nodes[e["target"]], e["relation"]))
            elif e["target"] == node_id and e["source"] in self._nodes:
                result.append((self._nodes[e["source"]], e["relation"]))
        return result

    def stats(self) -> Dict[str, int]:
        return {"nodes": len(self._nodes), "edges": len(self._edges)}

    def clear(self) -> None:
        self._nodes.clear()
        self._edges.clear()

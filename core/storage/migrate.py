"""
JSON → SQLite migration helpers (Phase 5).

Non-destructive: copies facts/graph from data/leon JSON into leon.db.
Does not delete JSON files. Safe to re-run (UPSERT).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.logger import logger
from core.storage.sqlite_db import LeonSQLite, get_connection, init_schema


def _facts_json_path() -> Path:
    try:
        from core.config import config

        return Path(config.path.facts_dir) / "facts.json"
    except Exception:
        return Path("data/leon/facts/facts.json")


def _graph_json_path() -> Path:
    try:
        from core.config import config

        return Path(config.path.graph_dir) / "graph.json"
    except Exception:
        return Path("data/leon/graph/graph.json")


def migrate_facts(conn=None) -> int:
    path = _facts_json_path()
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"migrate_facts read failed: {e}")
        return 0
    facts = data.get("facts") if isinstance(data, dict) else {}
    if not isinstance(facts, dict):
        return 0
    c = conn or get_connection()
    n = 0
    for fid, fact in facts.items():
        if not isinstance(fact, dict):
            continue
        c.execute(
            """
            INSERT INTO facts(id, statement, source, confidence, created_at, meta_json)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                statement=excluded.statement,
                source=excluded.source,
                confidence=excluded.confidence
            """,
            (
                fact.get("id") or fid,
                fact.get("statement") or "",
                fact.get("source") or "user",
                float(fact.get("confidence") or 1.0),
                fact.get("created_at"),
                json.dumps({k: v for k, v in fact.items() if k not in ("id", "statement", "source", "confidence", "created_at")}, ensure_ascii=False, default=str),
            ),
        )
        n += 1
    c.commit()
    return n


def migrate_graph(conn=None) -> Dict[str, int]:
    path = _graph_json_path()
    if not path.exists():
        return {"nodes": 0, "edges": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"migrate_graph read failed: {e}")
        return {"nodes": 0, "edges": 0}
    nodes = data.get("nodes") or {}
    edges = data.get("edges") or []
    c = conn or get_connection()
    nn = 0
    if isinstance(nodes, dict):
        for nid, node in nodes.items():
            if not isinstance(node, dict):
                continue
            c.execute(
                """
                INSERT INTO graph_nodes(id, label, node_type, properties_json, created_at, version)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    label=excluded.label,
                    node_type=excluded.node_type,
                    properties_json=excluded.properties_json,
                    version=excluded.version
                """,
                (
                    node.get("id") or nid,
                    node.get("label") or "",
                    node.get("type") or "entity",
                    json.dumps(node.get("properties") or {}, ensure_ascii=False, default=str),
                    node.get("created_at"),
                    int(node.get("version") or 1),
                ),
            )
            nn += 1
    # edges: clear+reinsert is simplest for full sync of this table
    ne = 0
    if isinstance(edges, list):
        c.execute("DELETE FROM graph_edges")
        for e in edges:
            if not isinstance(e, dict):
                continue
            src = e.get("source") or e.get("source_id")
            tgt = e.get("target") or e.get("target_id")
            if not src or not tgt:
                continue
            # skip if nodes missing (FK)
            if not c.execute("SELECT 1 FROM graph_nodes WHERE id=?", (src,)).fetchone():
                continue
            if not c.execute("SELECT 1 FROM graph_nodes WHERE id=?", (tgt,)).fetchone():
                continue
            c.execute(
                """
                INSERT INTO graph_edges(source_id, target_id, relation, weight, confidence)
                VALUES(?,?,?,?,?)
                """,
                (
                    src,
                    tgt,
                    e.get("relation") or "related_to",
                    float(e.get("weight") or 1.0),
                    float(e.get("confidence") or 1.0),
                ),
            )
            ne += 1
    c.commit()
    return {"nodes": nn, "edges": ne}


def migrate_json_to_sqlite() -> Dict[str, Any]:
    """Run full non-destructive migration."""
    init_schema()
    c = get_connection()
    facts_n = migrate_facts(c)
    graph = migrate_graph(c)
    db = LeonSQLite()
    db.set_meta("last_migrate", "ok")
    report = {
        "ok": True,
        "facts_migrated": facts_n,
        "graph": graph,
        "db": db.stats(),
        "json_preserved": True,
    }
    logger.info(f"migrate_json_to_sqlite: {report}")
    return report


def migration_status() -> Dict[str, Any]:
    init_schema()
    db = LeonSQLite()
    return {
        "db": db.stats(),
        "facts_json_exists": _facts_json_path().exists(),
        "graph_json_exists": _graph_json_path().exists(),
        "facts_json_path": str(_facts_json_path()),
        "graph_json_path": str(_graph_json_path()),
        "last_migrate": db.get_meta("last_migrate"),
    }

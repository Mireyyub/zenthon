"""
Leon SQLite connection + schema (Phase 5).

Uses stdlib sqlite3 only. Default path: data/leon/leon.db
JSON under data/leon/ remains authoritative for FactStore/Graph until
callers opt into SQLite repos; tasks use SQLite as primary durable store.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional

from core.logger import logger

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    statement TEXT NOT NULL,
    source TEXT DEFAULT 'user',
    confidence REAL DEFAULT 1.0,
    created_at TEXT,
    meta_json TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_facts_statement ON facts(statement);

CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    node_type TEXT DEFAULT 'entity',
    properties_json TEXT DEFAULT '{}',
    created_at TEXT,
    version INTEGER DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_label ON graph_nodes(label);

CREATE TABLE IF NOT EXISTS graph_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY(source_id) REFERENCES graph_nodes(id),
    FOREIGN KEY(target_id) REFERENCES graph_nodes(id)
);
CREATE INDEX IF NOT EXISTS idx_graph_edges_src ON graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_tgt ON graph_edges(target_id);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    goal TEXT DEFAULT '',
    action TEXT DEFAULT 'noop',
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'normal',
    params_json TEXT DEFAULT '{}',
    result_json TEXT,
    error TEXT,
    agent_name TEXT,
    plan_id TEXT,
    progress REAL DEFAULT 0.0,
    created_at TEXT,
    updated_at TEXT,
    started_at TEXT,
    finished_at TEXT,
    metadata_json TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    action TEXT NOT NULL,
    detail_json TEXT DEFAULT '{}'
);
"""

_local = threading.local()
_path_lock = threading.Lock()
_resolved_path: Optional[Path] = None


def db_path() -> Path:
    global _resolved_path
    with _path_lock:
        if _resolved_path is not None:
            return _resolved_path
        try:
            from core.config import config

            p = Path(config.path.leon_dir) / "leon.db"
        except Exception:
            p = Path("data/leon/leon.db")
        p.parent.mkdir(parents=True, exist_ok=True)
        _resolved_path = p
        return p


def get_connection(path: Optional[Path | str] = None) -> sqlite3.Connection:
    """Thread-local connection (check_same_thread=False for WS/thread pool)."""
    p = Path(path) if path else db_path()
    key = str(p.resolve())
    conn: Optional[sqlite3.Connection] = getattr(_local, "conn", None)
    conn_key = getattr(_local, "conn_key", None)
    if conn is not None and conn_key == key:
        return conn
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _local.conn = conn
    _local.conn_key = key
    return conn


def init_schema(path: Optional[Path | str] = None) -> Path:
    p = Path(path) if path else db_path()
    conn = get_connection(p)
    conn.executescript(_SCHEMA)
    conn.commit()
    # schema version
    conn.execute(
        "INSERT OR REPLACE INTO meta(key, value, updated_at) VALUES(?,?,datetime('now'))",
        ("schema_version", "5"),
    )
    conn.commit()
    logger.debug(f"Leon SQLite schema ready at {p}")
    return p


class LeonSQLite:
    """Small facade for scripts / CLI."""

    def __init__(self, path: Optional[Path | str] = None):
        self.path = Path(path) if path else db_path()
        init_schema(self.path)

    @property
    def conn(self) -> sqlite3.Connection:
        return get_connection(self.path)

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key, value, updated_at) VALUES(?,?,datetime('now'))",
            (key, value),
        )
        self.conn.commit()

    def get_meta(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def stats(self) -> dict[str, Any]:
        c = self.conn
        def _count(table: str) -> int:
            try:
                return int(c.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"])
            except Exception:
                return 0

        return {
            "path": str(self.path),
            "schema_version": self.get_meta("schema_version", "?"),
            "facts": _count("facts"),
            "graph_nodes": _count("graph_nodes"),
            "graph_edges": _count("graph_edges"),
            "tasks": _count("tasks"),
            "audit_log": _count("audit_log"),
        }

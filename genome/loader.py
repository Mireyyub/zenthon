"""LEON Genome — cognitive genes loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

GENOME_DIR = Path(__file__).resolve().parent


def list_genes() -> List[str]:
    return sorted(p.stem for p in GENOME_DIR.glob("GENE_*.yaml"))


def load_gene(gene_id: str) -> Dict[str, Any]:
    """Load GENE-000001 or GENE_000001_EXISTENCE."""
    path = _resolve(gene_id)
    if path is None:
        raise FileNotFoundError(f"Gene not found: {gene_id}")
    return _parse_yaml_simple(path.read_text(encoding="utf-8"))


def load_all_genes() -> List[Dict[str, Any]]:
    genes = []
    for p in sorted(GENOME_DIR.glob("GENE_*.yaml")):
        genes.append(_parse_yaml_simple(p.read_text(encoding="utf-8")))
    return genes


def _resolve(gene_id: str) -> Optional[Path]:
    gid = gene_id.replace("-", "_").upper()
    for p in GENOME_DIR.glob("GENE_*.yaml"):
        if gid in p.stem.upper() or gene_id.upper() in p.stem.upper():
            return p
        # numeric match
        if gene_id.isdigit() and gene_id in p.stem:
            return p
    return None


def _parse_yaml_simple(text: str) -> Dict[str, Any]:
    """Minimal YAML subset parser (no external dep)."""
    data: Dict[str, Any] = {}
    current_list_key = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.strip().startswith("#"):
            continue
        if line.strip().startswith("- ") and current_list_key:
            data.setdefault(current_list_key, []).append(line.strip()[2:].strip())
            continue
        if ":" in line and not line.strip().startswith("-"):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "" or val == "[]":
                data[key] = [] if val == "[]" else []
                current_list_key = key
            else:
                data[key] = val.strip("\"'")
                current_list_key = None
    return data


def activate_genes_into_facts() -> int:
    """Inject gene definitions into FactStore."""
    try:
        from knowledge.facts import FactStore
        facts = FactStore()
    except Exception:
        return 0
    n = 0
    for g in load_all_genes():
        name = g.get("name", "")
        definition = g.get("definition", "")
        gid = g.get("id", "")
        if definition:
            facts.add(f"[Gene {gid}] {name}: {definition}", source="genome")
            n += 1
    return n

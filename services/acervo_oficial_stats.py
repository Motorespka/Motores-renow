#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estatisticas do acervo OFICIAL (manifest + indice SQLite local)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "exports" / "review" / "master_release_v2_manifest.csv"
SQLITE = REPO_ROOT / "data" / "oficial_search.sqlite"


def _t(v: Any) -> str:
    return "" if v is None else str(v).strip()


def count_oficial_manifest() -> int:
    if not MANIFEST.is_file():
        return 0
    n = 0
    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if _t(row.get("status_release")).upper() == "OFICIAL":
                n += 1
    return n


def load_acervo_stats() -> dict[str, Any]:
    stats: dict[str, Any] = {
        "manifest_path": str(MANIFEST),
        "sqlite_path": str(SQLITE),
        "oficial_manifest": count_oficial_manifest(),
        "sqlite_exists": SQLITE.is_file(),
        "indexed_total": 0,
        "file_complete": 0,
        "with_geometry": 0,
        "index_generated_at": "",
    }
    if not SQLITE.is_file():
        return stats
    try:
        import sqlite3

        conn = sqlite3.connect(SQLITE)
        stats["indexed_total"] = conn.execute("SELECT COUNT(*) FROM motores_oficial").fetchone()[0]
        stats["file_complete"] = conn.execute(
            "SELECT COUNT(*) FROM motores_oficial WHERE is_file = 1"
        ).fetchone()[0]
        meta = {
            r[0]: r[1] for r in conn.execute("SELECT key, value FROM index_meta").fetchall()
        }
        stats["with_geometry"] = int(meta.get("with_geometry", 0) or 0)
        stats["index_generated_at"] = meta.get("generated_at", "")
        conn.close()
    except Exception:
        pass
    return stats

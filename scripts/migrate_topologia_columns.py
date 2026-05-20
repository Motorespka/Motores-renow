#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adiciona colunas tipo_bobinagem ao SQLite existente e re-infera valores."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_DB = REPO_ROOT / "data" / "oficial_search.sqlite"

sys.path.insert(0, str(REPO_ROOT))
from app.topologia_bobinagem import infer_tipo_bobinagem, label_tipo, norm_tipo_bobinagem  # noqa: E402


def migrate(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(motores_oficial)").fetchall()}
    if "tipo_bobinagem" not in cols:
        conn.execute("ALTER TABLE motores_oficial ADD COLUMN tipo_bobinagem TEXT DEFAULT ''")
        conn.execute("ALTER TABLE motores_oficial ADD COLUMN tipo_bobinagem_norm TEXT DEFAULT ''")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tipo_bobinagem_norm ON motores_oficial(tipo_bobinagem_norm)"
        )
    rows = conn.execute(
        "SELECT sha, passo_principal, fio_principal FROM motores_oficial"
    ).fetchall()
    n = 0
    for sha, passo, _fio in rows:
        topo = infer_tipo_bobinagem(passo_principal=passo or "")
        norm = norm_tipo_bobinagem(topo) or "DESCONHECIDO"
        conn.execute(
            "UPDATE motores_oficial SET tipo_bobinagem=?, tipo_bobinagem_norm=? WHERE sha=?",
            (label_tipo(norm), norm, sha),
        )
        n += 1
    conn.commit()
    conn.close()
    print(f"Atualizados {n} registros em {db_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args()
    if not args.db.is_file():
        print(f"DB nao encontrado: {args.db}")
        raise SystemExit(2)
    migrate(args.db.resolve())

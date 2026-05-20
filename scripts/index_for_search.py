#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Indexa motores OFICIAIS (master_release_v2_manifest.csv + JSONLs de extracao)
em SQLite local para busca rapida na demo Streamlit.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REVIEW_DIR = REPO_ROOT / "exports" / "review"
MASTER_CSV = REVIEW_DIR / "master_release_v2_manifest.csv"
DEFAULT_DB = REPO_ROOT / "data" / "oficial_search.sqlite"

sys.path.insert(0, str(REPO_ROOT))
from app.search_lib import (  # noqa: E402
    norm_carcaca,
    parse_awg_number,
    parse_mm,
    parse_passo_nums,
    parse_scalar,
)
from app.topologia_bobinagem import infer_tipo_bobinagem, label_tipo, norm_tipo_bobinagem  # noqa: E402


def _t(v) -> str:
    return "" if v is None else str(v).strip()


def _norm_path(s: str) -> str:
    return s.replace("/", "\\").lower().strip()


def index_all_jsonls(review_dir: Path) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for fp in sorted(review_dir.glob("*.jsonl")):
        try:
            with fp.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    arr = _t(rec.get("arquivo_rel"))
                    if not arr:
                        arq = _t(rec.get("arquivo"))
                        if not arq:
                            continue
                        arr = arq.replace("/", "\\")
                    key = _norm_path(arr)
                    rec["_source_jsonl"] = fp.name
                    prev = idx.get(key)
                    if prev is None or _t(rec.get("generated_at")) > _t(prev.get("generated_at")):
                        idx[key] = rec
        except OSError:
            continue
    return idx


def row_from_rec(rec: dict, sha: str, status: str) -> dict | None:
    res = rec.get("resultado") or {}
    if not isinstance(res, dict):
        return None
    d_raw = _t(res.get("diametro_mm"))
    p_raw = _t(res.get("pacote_mm"))
    d_mm = parse_mm(d_raw)
    p_mm = parse_mm(p_raw)
    passo_p = _t(res.get("passo_principal"))
    esp_p = parse_scalar(_t(res.get("espiras_principal")))
    esp_a = parse_scalar(_t(res.get("espiras_auxiliar")))
    sidecar = rec.get("schema_sidecar") or {}
    rebob = (sidecar.get("campos_expandidos") or {}).get("rebobinagem") or {}
    nested_p = rebob.get("_gemini_nested_principal") or {}
    ligacao = _t(nested_p.get("ligacao")) or _t(res.get("ligacao"))
    obs = _t(res.get("observacoes"))
    ocr = _t((rec.get("local") or {}).get("texto_ocr_bruto"))
    tipo_topo = infer_tipo_bobinagem(
        passo_principal=passo_p,
        passo_auxiliar=_t(res.get("passo_auxiliar")),
        observacoes=obs,
        texto_ocr=ocr,
        rebobinagem_sidecar=rebob,
    )
    tipo_norm = norm_tipo_bobinagem(tipo_topo) or "DESCONHECIDO"
    is_file = int(
        bool(d_mm and p_mm and _t(res.get("carcaca")) and passo_p and _t(res.get("fio_principal")) and esp_p)
    )
    return {
        "sha": sha.lower(),
        "arquivo_rel": _t(rec.get("arquivo_rel")) or _t(res.get("arquivo")),
        "melhor_status": status,
        "carcaca": _t(res.get("carcaca")),
        "carcaca_norm": norm_carcaca(_t(res.get("carcaca"))),
        "diametro_mm": d_mm,
        "pacote_mm": p_mm,
        "diametro_raw": d_raw,
        "pacote_raw": p_raw,
        "passo_principal": passo_p,
        "passo_nums_json": json.dumps(parse_passo_nums(passo_p), ensure_ascii=False),
        "fio_principal": _t(res.get("fio_principal")),
        "fio_principal_num": parse_awg_number(_t(res.get("fio_principal"))),
        "espiras_principal": esp_p,
        "fio_auxiliar": _t(res.get("fio_auxiliar")),
        "fio_auxiliar_num": parse_awg_number(_t(res.get("fio_auxiliar"))),
        "espiras_auxiliar": esp_a,
        "potencia_cv": _t(res.get("potencia_cv")),
        "polos": _t(res.get("polos")),
        "tipo_motor": _t(res.get("tipo_motor")),
        "source_jsonl": _t(rec.get("_source_jsonl")),
        "ligacao": ligacao,
        "tipo_bobinagem": label_tipo(tipo_norm),
        "tipo_bobinagem_norm": tipo_norm,
        "is_file": is_file,
    }


def build_db(db_path: Path, manifest_path: Path, review_dir: Path) -> dict:
    jsonl_idx = index_all_jsonls(review_dir)
    oficial_rows: list[dict[str, str]] = []
    with manifest_path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if _t(r.get("status_release")).upper() == "OFICIAL":
                oficial_rows.append(r)

    records: list[dict] = []
    missing_jsonl = 0
    no_geom = 0
    for r in oficial_rows:
        ar = _t(r.get("arquivo_rel"))
        sha = _t(r.get("sha256_arquivo")).lower()
        status = _t(r.get("melhor_status"))
        rec = jsonl_idx.get(_norm_path(ar))
        if rec is None:
            missing_jsonl += 1
            continue
        row = row_from_rec(rec, sha, status)
        if row is None:
            continue
        if row["diametro_mm"] is None and row["pacote_mm"] is None:
            no_geom += 1
        records.append(row)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.is_file():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE motores_oficial (
            sha TEXT PRIMARY KEY,
            arquivo_rel TEXT NOT NULL,
            melhor_status TEXT,
            carcaca TEXT,
            carcaca_norm TEXT,
            diametro_mm REAL,
            pacote_mm REAL,
            diametro_raw TEXT,
            pacote_raw TEXT,
            passo_principal TEXT,
            passo_nums_json TEXT,
            fio_principal TEXT,
            fio_principal_num REAL,
            espiras_principal REAL,
            fio_auxiliar TEXT,
            fio_auxiliar_num REAL,
            espiras_auxiliar REAL,
            potencia_cv TEXT,
            polos TEXT,
            tipo_motor TEXT,
            source_jsonl TEXT,
            ligacao TEXT,
            tipo_bobinagem TEXT,
            tipo_bobinagem_norm TEXT,
            is_file INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX idx_is_file ON motores_oficial(is_file);
        CREATE INDEX idx_geom ON motores_oficial(diametro_mm, pacote_mm);
        CREATE INDEX idx_carcaca_norm ON motores_oficial(carcaca_norm);
        CREATE INDEX idx_tipo_bobinagem_norm ON motores_oficial(tipo_bobinagem_norm);
        CREATE TABLE index_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    cols = [
        "sha",
        "arquivo_rel",
        "melhor_status",
        "carcaca",
        "carcaca_norm",
        "diametro_mm",
        "pacote_mm",
        "diametro_raw",
        "pacote_raw",
        "passo_principal",
        "passo_nums_json",
        "fio_principal",
        "fio_principal_num",
        "espiras_principal",
        "fio_auxiliar",
        "fio_auxiliar_num",
        "espiras_auxiliar",
        "potencia_cv",
        "polos",
        "tipo_motor",
        "source_jsonl",
        "ligacao",
        "tipo_bobinagem",
        "tipo_bobinagem_norm",
        "is_file",
    ]
    conn.executemany(
        f"INSERT INTO motores_oficial ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
        [[row[c] for c in cols] for row in records],
    )
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta = {
        "generated_at": utc,
        "oficial_manifest_rows": str(len(oficial_rows)),
        "indexed_rows": str(len(records)),
        "missing_jsonl": str(missing_jsonl),
        "no_geometry": str(no_geom),
        "with_geometry": str(sum(1 for x in records if x["diametro_mm"] or x["pacote_mm"])),
        "file_complete": str(sum(1 for x in records if x.get("is_file"))),
        "jsonl_sources": str(len(jsonl_idx)),
    }
    for k, v in meta.items():
        conn.execute("INSERT INTO index_meta (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

    return {
        "db_path": str(db_path.resolve()),
        **{k: int(v) if v.isdigit() else v for k, v in meta.items()},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Indexa acervo OFICIAL para busca na demo.")
    ap.add_argument("--manifest", type=Path, default=MASTER_CSV)
    ap.add_argument("--review-dir", type=Path, default=REVIEW_DIR)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args()

    if not args.manifest.is_file():
        print(f"ERRO: manifest nao encontrado: {args.manifest}", file=sys.stderr)
        return 2

    stats = build_db(args.db.resolve(), args.manifest.resolve(), args.review_dir.resolve())
    print("=" * 72)
    print("INDICE DE BUSCA — acervo OFICIAL")
    print("=" * 72)
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("=" * 72)
    print(f"Pronto. Rode a demo: streamlit run app/demo.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera knowledge/referencia_oficina.json a partir do acervo OFICIAL indexado
(~1062 cálculos / extrações da oficina).

Uso:
    python scripts/build_referencia_oficina.py
    python scripts/build_referencia_oficina.py --sqlite data/oficial_search.sqlite
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_DB = REPO_ROOT / "data" / "oficial_search.sqlite"
DEFAULT_OUT = REPO_ROOT / "knowledge" / "referencia_oficina.json"
FALLBACK_CSV = REPO_ROOT / "data" / "banco_motores_completos.csv"

sys.path.insert(0, str(REPO_ROOT))

from app.search_lib import norm_carcaca, parse_awg_number, parse_mm, parse_scalar  # noqa: E402
from engine.physics_audit import (  # noqa: E402
    current_density_a_per_mm2,
    infer_wire_from_fio,
    nominal_line_current_a,
    power_kw_from_cv,
)

_RE_CV_FRAC = re.compile(
    r"^(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)\s*(?:cv)?",
    re.IGNORECASE,
)


def parse_potencia_cv(raw: str) -> Optional[float]:
    """Converte potencia_cv do acervo para CV numérico."""
    s = (raw or "").strip().lower().replace(",", ".")
    if not s:
        return None
    m = _RE_CV_FRAC.match(s)
    if m:
        den = float(m.group(2).replace(",", "."))
        if den > 0:
            return round(float(m.group(1).replace(",", ".")) / den, 4)
    m2 = re.search(r"(\d+(?:\.\d+)?)\s*cv", s)
    if m2:
        return float(m2.group(1))
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if not nums:
        return None
    v = float(nums[0])
    if v > 200:
        return None
    return v


def cv_bucket(cv: float) -> str:
    """Chave estável para agrupamento (ex.: 1.5, 0.5, 12)."""
    if cv < 0.2:
        return "0.12"
    if cv < 0.35:
        return "0.25"
    if cv < 0.75:
        return "0.5"
    if cv < 1.25:
        return "1.0"
    if cv < 1.75:
        return "1.5"
    if cv < 2.5:
        return "2.0"
    if cv < 4:
        return "3.0"
    if cv < 7.5:
        return "5.0"
    if cv < 15:
        return "10.0"
    if cv < 35:
        return "20.0"
    return "50.0"


def geom_bucket(carcaca: str, pacote_mm: Optional[float]) -> str:
    cn = norm_carcaca(carcaca) or "desconhecido"
    if pacote_mm is None or pacote_mm <= 0:
        return cn
    p = int(round(float(pacote_mm) / 5.0) * 5)
    return f"{cn}|{p}"


def _percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(s[int(k)], 2)
    return round(s[f] + (s[c] - s[f]) * (k - f), 2)


def _agg_stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    return {
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "media": round(statistics.mean(values), 2),
        "mediana": round(statistics.median(values), 2),
        "p10": _percentile(values, 0.10),
        "p90": _percentile(values, 0.90),
    }


def _top_awg(counter: Counter, n: int = 8) -> list[dict[str, Any]]:
    total = sum(counter.values()) or 1
    return [
        {"awg": int(awg), "count": cnt, "pct": round(100.0 * cnt / total, 1)}
        for awg, cnt in counter.most_common(n)
    ]


def load_rows_sqlite(db_path: Path) -> list[dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    q = """
        SELECT carcaca, carcaca_norm, diametro_mm, pacote_mm, passo_principal,
               fio_principal, fio_principal_num, espiras_principal, potencia_cv, polos,
               tipo_bobinagem_norm
        FROM motores_oficial
        WHERE espiras_principal IS NOT NULL AND espiras_principal > 0
    """
    rows = [dict(r) for r in conn.execute(q)]
    conn.close()
    return rows


def load_rows_csv(csv_path: Path) -> list[dict[str, Any]]:
    import csv

    out: list[dict[str, Any]] = []
    if not csv_path.is_file():
        return out
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            esp = parse_scalar(str(r.get("espiras_principal") or r.get("espiras") or ""))
            if not esp or esp <= 0:
                continue
            awg = parse_awg_number(str(r.get("fio_principal") or r.get("fio") or ""))
            out.append(
                {
                    "carcaca": str(r.get("carcaca") or ""),
                    "carcaca_norm": norm_carcaca(str(r.get("carcaca") or "")),
                    "diametro_mm": parse_mm(str(r.get("diametro_mm") or "")),
                    "pacote_mm": parse_mm(str(r.get("pacote_mm") or "")),
                    "passo_principal": str(r.get("passo") or ""),
                    "fio_principal": str(r.get("fio") or ""),
                    "fio_principal_num": awg,
                    "espiras_principal": esp,
                    "potencia_cv": str(r.get("potencia") or ""),
                    "polos": str(r.get("polos") or ""),
                    "tipo_bobinagem_norm": "",
                }
            )
    return out


def enrich_record(row: dict[str, Any]) -> Optional[dict[str, Any]]:
    esp = float(row.get("espiras_principal") or 0)
    if esp <= 0:
        return None
    cv = parse_potencia_cv(str(row.get("potencia_cv") or ""))
    if cv is None or cv <= 0:
        return None

    fio_raw = row.get("fio_principal") or ""
    par, awg = infer_wire_from_fio(str(fio_raw), tipo_bobinagem=str(row.get("tipo_bobinagem_norm") or ""))
    if row.get("fio_principal_num"):
        try:
            awg = float(row["fio_principal_num"])
        except (TypeError, ValueError):
            pass
    if awg <= 0:
        return None

    p_kw = power_kw_from_cv(cv)
    i_nom = nominal_line_current_a(p_kw, voltage_v=220.0)
    j_val = current_density_a_per_mm2(i_nom, awg, parallel_count=par)

    pacote = row.get("pacote_mm")
    try:
        pacote_f = float(pacote) if pacote is not None else None
    except (TypeError, ValueError):
        pacote_f = None

    return {
        "cv": cv,
        "cv_bucket": cv_bucket(cv),
        "espiras": esp,
        "awg": int(round(awg)),
        "paralelo": par,
        "j_a_mm2": j_val,
        "carcaca": str(row.get("carcaca") or ""),
        "carcaca_norm": str(row.get("carcaca_norm") or norm_carcaca(str(row.get("carcaca") or ""))),
        "geom_bucket": geom_bucket(str(row.get("carcaca") or ""), pacote_f),
        "pacote_mm": pacote_f,
        "passo": str(row.get("passo_principal") or ""),
    }


def build_knowledge(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_cv: dict[str, list[dict]] = defaultdict(list)
    by_geom: dict[str, list[dict]] = defaultdict(list)
    all_j: list[float] = []
    all_esp: list[float] = []

    for rec in records:
        by_cv[rec["cv_bucket"]].append(rec)
        by_geom[rec["geom_bucket"]].append(rec)
        if rec.get("j_a_mm2") is not None:
            all_j.append(float(rec["j_a_mm2"]))
        all_esp.append(float(rec["espiras"]))

    por_cv: dict[str, Any] = {}
    for bucket, items in sorted(by_cv.items(), key=lambda x: float(x[0]) if x[0].replace(".", "").isdigit() else 0):
        espiras = [float(x["espiras"]) for x in items]
        j_vals = [float(x["j_a_mm2"]) for x in items if x.get("j_a_mm2") is not None]
        awg_ctr: Counter = Counter()
        for x in items:
            awg_ctr[int(x["awg"])] += 1
        por_cv[bucket] = {
            "cv_representativo": float(bucket),
            "n_registros": len(items),
            "espiras": _agg_stats(espiras),
            "faixa_espiras_aceitavel": {
                "min": _percentile(espiras, 0.05) if espiras else 0,
                "max": _percentile(espiras, 0.95) if espiras else 0,
            },
            "awg_mais_usados": _top_awg(awg_ctr),
            "densidade_j_a_mm2": _agg_stats(j_vals),
            "faixa_j_aceitavel": {
                "min": _percentile(j_vals, 0.05) if j_vals else 0,
                "max": _percentile(j_vals, 0.95) if j_vals else 0,
            },
        }

    por_geom: dict[str, Any] = {}
    for gkey, items in sorted(by_geom.items(), key=lambda x: -len(x[1]))[:400]:
        if len(items) < 3:
            continue
        j_vals = [float(x["j_a_mm2"]) for x in items if x.get("j_a_mm2") is not None]
        espiras = [float(x["espiras"]) for x in items]
        por_geom[gkey] = {
            "n_registros": len(items),
            "carcaca": items[0].get("carcaca", ""),
            "pacote_mm_medio": round(
                statistics.mean([x["pacote_mm"] for x in items if x.get("pacote_mm")]), 1
            )
            if any(x.get("pacote_mm") for x in items)
            else None,
            "espiras": _agg_stats(espiras),
            "densidade_j_a_mm2": _agg_stats(j_vals),
            "faixa_j_aceitavel": {
                "min": _percentile(j_vals, 0.05) if j_vals else 0,
                "max": _percentile(j_vals, 0.95) if j_vals else 0,
            },
        }

    return {
        "meta": {
            "gerado_em": datetime.now(timezone.utc).isoformat(),
            "total_registros_processados": len(records),
            "fonte_principal": "motores_oficial (OFICIAL / acervo indexado)",
            "prioridade": "Conhecimento da oficina sobrepõe limites IEC genéricos na auditoria.",
        },
        "por_cv": por_cv,
        "por_carcaca_pacote": por_geom,
        "global": {
            "n_registros": len(records),
            "espiras": _agg_stats(all_esp),
            "densidade_j_a_mm2": _agg_stats(all_j),
            "faixa_j_aceitavel": {
                "min": _percentile(all_j, 0.03) if all_j else 2.0,
                "max": _percentile(all_j, 0.97) if all_j else 10.0,
            },
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Gera knowledge/referencia_oficina.json")
    ap.add_argument("--sqlite", type=Path, default=DEFAULT_DB)
    ap.add_argument("--csv", type=Path, default=FALLBACK_CSV)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    raw_rows: list[dict[str, Any]] = []
    if args.sqlite.is_file():
        raw_rows = load_rows_sqlite(args.sqlite)
        print(f"SQLite: {len(raw_rows)} linhas com espiras")
    if len(raw_rows) < 500 and args.csv.is_file():
        extra = load_rows_csv(args.csv)
        print(f"CSV fallback: +{len(extra)} linhas")
        raw_rows.extend(extra)

    enriched: list[dict[str, Any]] = []
    for row in raw_rows:
        e = enrich_record(row)
        if e:
            enriched.append(e)

    print(f"Registros com CV+espiras+AWG: {len(enriched)}")

    payload = build_knowledge(enriched)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito: {args.out} ({args.out.stat().st_size // 1024} KB)")
    print(f"Faixas CV: {len(payload['por_cv'])} | Geometrias: {len(payload['por_carcaca_pacote'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

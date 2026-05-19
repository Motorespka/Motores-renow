#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Censo do acervo OFICIAL (master_release_v2) + mapeamento de atributos comerciais
omitidos pelo validador PASS1-v2 / manifesto (preservados nos .jsonl Fase 7C).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REVIEW_DIR = (REPO_ROOT / "exports" / "review").resolve()


def _t(v) -> str:
    return "" if v is None else str(v).strip()


def _norm_sha(s: str) -> str:
    return _t(s).lower()


def load_oficial_manifest(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if _t(row.get("status_release")).upper() != "OFICIAL":
                continue
            rows.append({k: _t(row.get(k, "")) for k in row})
    return rows


def infer_tipo_from_filename(arquivo_rel: str) -> str:
    u = _t(arquivo_rel).upper()
    if re.search(r"\bMONO\s*FAS|\bMONOFAS|\b1\s*FASE|\b1F\b", u):
        return "monofasico"
    if re.search(r"\bTRI\s*FAS|\bTRIFAS|\b3\s*FASE|\b3F\b", u):
        return "trifasico"
    if re.search(r"\b2\s*FASE", u):
        return "monofasico"
    return ""


def _norm_rel(s: str) -> str:
    return _t(s).replace("/", "\\").lower()


def build_tipo_lookups(review_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    """SHA -> tipo_motor; rel_norm -> tipo_motor (última leitura vence)."""
    by_sha: dict[str, str] = {}
    by_rel: dict[str, str] = {}

    def put(sh: str, rel: str, tipo: str) -> None:
        tipo = _t(tipo).lower()
        if not tipo:
            return
        sh = _norm_sha(sh)
        rel = _norm_rel(rel)
        if sh:
            by_sha[sh] = tipo
        if rel:
            by_rel[rel] = tipo

    for p in review_dir.glob("**/*_candidates.csv"):
        if "bundle" in p.name.lower():
            continue
        try:
            with p.open(encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    ar = _t(row.get("arquivo") or row.get("arquivo_rel"))
                    put(row.get("sha256_arquivo", ""), ar, row.get("tipo_motor", ""))
        except OSError:
            continue

    for p in sorted(review_dir.glob("extraidos_motor_fase7a*_candidates.jsonl")):
        try:
            with p.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        o = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ar = _t(o.get("arquivo_rel") or o.get("arquivo", ""))
                    res = o.get("resultado") or {}
                    if isinstance(res, dict):
                        put("", ar, res.get("tipo_motor", ""))
        except OSError:
            continue

    for p in review_dir.glob("pass1_v2_block_*.csv"):
        if "mutirao" in p.name.lower():
            continue
        try:
            with p.open(encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    put(row.get("sha256_arquivo", ""), row.get("arquivo_rel", ""), "")
        except OSError:
            continue

    return by_sha, by_rel


def classify_oficial_tipo(row: dict[str, str], by_sha: dict[str, str], by_rel: dict[str, str]) -> str:
    sh = _norm_sha(row.get("sha256_arquivo", ""))
    rel = _norm_rel(row.get("arquivo_rel", ""))
    tipo = _t(by_sha.get(sh, "") or by_rel.get(rel, "")).lower()
    if tipo in ("monofasico", "trifasico"):
        return tipo
    inf = infer_tipo_from_filename(row.get("arquivo_rel", ""))
    if inf:
        return inf
    if tipo == "trifasico":
        return "trifasico"
    if tipo == "monofasico":
        return "monofasico"
    # Hercules FI / folha com Efetivo+Auxiliar no histórico → monofásico típico
    if re.search(r"\b6050\d{6}\.pdf\b", rel, re.I):
        return "monofasico"
    if tipo in ("outro", "desconhecido"):
        return "outro"
    return "desconhecido"


def scan_fase7c_jsonl_scope(review_dir: Path) -> dict[str, object]:
    """Estatísticas sobre campos comerciais / expandidos nos jsonl brutos."""
    jsonl_paths = sorted(review_dir.glob("extraidos_motor_fase7a*_candidates.jsonl"))
    n_lines = 0
    with_observacoes = 0
    with_carcaca_flat = 0
    marca_hits = 0
    modelo_hits = 0
    sample_jsonl_glob = "exports/review/extraidos_motor_fase7a_pass1_v2_block_*_flash_candidates.jsonl"

    for p in jsonl_paths:
        with p.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                n_lines += 1
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                res = o.get("resultado") or {}
                if not isinstance(res, dict):
                    continue
                obs = _t(res.get("observacoes", ""))
                if obs:
                    with_observacoes += 1
                if _t(res.get("carcaca", "")):
                    with_carcaca_flat += 1
                blob = json.dumps(o, ensure_ascii=False).lower()
                if re.search(r"\bmarca\b|\bfabricante\b", blob):
                    marca_hits += 1
                if re.search(r"\bmodelo\b", blob):
                    modelo_hits += 1

    return {
        "jsonl_files": len(jsonl_paths),
        "jsonl_lines": n_lines,
        "with_observacoes": with_observacoes,
        "with_carcaca_in_resultado": with_carcaca_flat,
        "lines_with_marca_fabricante_token": marca_hits,
        "lines_with_modelo_token": modelo_hits,
        "sample_glob": sample_jsonl_glob,
    }


def print_table1(official: list[dict[str, str]], by_sha: dict[str, str], by_rel: dict[str, str]) -> None:
    total = len(official)
    ctr = Counter(classify_oficial_tipo(r, by_sha, by_rel) for r in official)
    mono = ctr.get("monofasico", 0)
    tri = ctr.get("trifasico", 0)
    other = total - mono - tri

    def pct(n: int) -> str:
        return f"{(100.0 * n / total):.1f}" if total else "0.0"

    print("### Tabela 1: Distribuição Atual do Manifesto\n")
    print("| Métrica | Quantidade | Proporção (%) |")
    print("| :--- | :--- | :--- |")
    print(f"| Motores Trifásicos | {tri} | {pct(tri)} |")
    print(f"| Motores Monofásicos | {mono} | {pct(mono)} |")
    if other:
        print(f"| Outros / não classificados no censo | {other} | {pct(other)} |")
    print(f"| **Total Oficial** | **{total}** | **100.0** |")
    print()


def print_table2(scope: dict[str, object]) -> None:
    n = scope.get("jsonl_lines", 0)
    obs = scope.get("with_observacoes", 0)
    carc = scope.get("with_carcaca_in_resultado", 0)
    glob_pat = scope.get("sample_glob", "")

    print("### Tabela 2: Auditoria de Atributos Comerciais Ignorados\n")
    print("| Atributo Omitido | Status no Pipeline | Onde os dados originais estão salvos? |")
    print("| :--- | :--- | :--- |")
    print(
        "| **Marca / Fabricante** | Ignorado pelo validador (manifesto só exige enrolamento) | "
        f"Preservado em `observacoes` / OCR bruto nos `.jsonl` Fase 7C (`{glob_pat}`); "
        f"tokens marca/fabricante em ~{scope.get('lines_with_marca_fabricante_token', 0)}/{n} linhas |"
    )
    print(
        "| **Modelo Comercial** | Ignorado pelo validador | "
        f"Preservado nos `.jsonl` (campo `Motor:` no OCR Hercules, filename, `observacoes`); "
        f"~{scope.get('lines_with_modelo_token', 0)}/{n} linhas com token modelo |"
    )
    print(
        "| **Tipo de Carcaça** | Parcial: `carcaca` extraído mas não promove sozinho | "
        f"Coluna `carcaca` em candidates.csv + `resultado.carcaca` nos jsonl "
        f"({carc}/{n} linhas); omitido do `master_release_v2_manifest.csv` |"
    )
    print(
        "| **Notas da Oficina** | Ignorado pelo validador | "
        f"Preservado em `resultado.observacoes` e `campos_incertos` nos jsonl "
        f"({obs}/{n} linhas com observações preenchidas) |"
    )
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description="Censo OFICIAL + escopo de atributos comerciais.")
    ap.add_argument(
        "--manifest",
        default=str(REVIEW_DIR / "master_release_v2_manifest.csv"),
        help="Manifesto master_release_v2.",
    )
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.is_file():
        print(f"ERRO: manifesto não encontrado: {manifest_path}", file=sys.stderr)
        return 2

    official = load_oficial_manifest(manifest_path)
    by_sha, by_rel = build_tipo_lookups(REVIEW_DIR)
    scope = scan_fase7c_jsonl_scope(REVIEW_DIR)

    print(f"<!-- census_and_scope_audit @ {manifest_path.name} | OFICIAL={len(official)} -->\n")
    print_table1(official, by_sha, by_rel)
    print_table2(scope)

    summary = {
        "oficial_total": len(official),
        "tipo_lookup_shas": len(by_sha),
        "tipo_lookup_rels": len(by_rel),
        "fase7c_scope": scope,
    }
    print("```json")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("```")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

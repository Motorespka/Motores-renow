#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera fila unificada de mutirão (sidecar) para a cauda B58/B59:
alert_manifest + manual_review → tail_mutirao_pendencias.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REVIEW_DIR = (REPO_ROOT / "exports" / "review").resolve()
LOGS_DIR = (REPO_ROOT / "logs").resolve()

NEMA42_BASENAME = "605012085.pdf"

FIELD_LABELS = {
    "tipo_motor": "tipo de motor",
    "tensao": "tensão",
    "fio_principal": "fiação principal",
    "espiras_principal": "espiras principal",
    "passo_principal": "passo principal",
    "fio_auxiliar": "fiação auxiliar",
    "espiras_auxiliar": "espiras auxiliar",
    "passo_auxiliar": "passo auxiliar",
}

CSV_COLUMNS = [
    "sha",
    "file_name",
    "block",
    "status_atual",
    "alert_codes",
    "rpm_detectado",
    "potencia_detectada",
    "observacao_mutirao",
]


def _t(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _basename(rel: str) -> str:
    return Path(_t(rel).replace("\\", "/")).name


def _read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _alert_tokens(raw: str) -> List[str]:
    """Extrai códigos A01, A08, faltando_obrigatorio, etc."""
    if not raw:
        return []
    out: List[str] = []
    seen: Set[str] = set()
    for part in re.split(r"[;|]", raw):
        p = _t(part)
        if not p:
            continue
        if p.startswith("A*:"):
            p = p[3:]
        m = re.match(r"^(A\d{2})_", p)
        if m:
            code = m.group(1)
        elif p == "faltando_obrigatorio" or p.startswith("faltando_obrigatorio"):
            code = "faltando_obrigatorio"
        elif p.startswith("S_pipeline_"):
            code = "S_pipeline"
        else:
            m2 = re.match(r"^(A\d{2})", p)
            code = m2.group(1) if m2 else p.split("_")[0] if "_" in p else p
        if code and code not in seen:
            seen.add(code)
            out.append(code)
    return out


def _merge_codes(*parts: str) -> str:
    seen: Set[str] = set()
    ordered: List[str] = []
    for raw in parts:
        for c in _alert_tokens(raw):
            if c not in seen:
                seen.add(c)
                ordered.append(c)
    return ";".join(ordered)


def _block_paths(block: int) -> Dict[str, Path]:
    stem = f"extraidos_motor_fase7a_pass1_v2_block_{block}"
    return {
        "alert": REVIEW_DIR / f"{stem}_alert_manifest.csv",
        "manual": REVIEW_DIR / f"{stem}_manual_review.csv",
        "candidates": REVIEW_DIR / f"{stem}_flash_candidates.csv",
        "quality": REVIEW_DIR / f"gemini_extraction_quality_{stem}_flash.csv",
        "categorized_manual": REVIEW_DIR / f"{stem}_flash_categorized_manual_review.csv",
        "log": LOGS_DIR / f"{stem}_flash.log",
    }


def _load_enrichment(block: int) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]]]:
    """sha -> row from candidates; sha -> row from quality (by arquivo basename match too)."""
    paths = _block_paths(block)
    by_sha: Dict[str, Dict[str, str]] = {}
    by_file: Dict[str, Dict[str, str]] = {}

    for row in _read_csv(paths["candidates"]):
        sha = _t(row.get("sha256_arquivo") or row.get("sha"))
        rel = _t(row.get("arquivo") or row.get("arquivo_rel"))
        if not sha and rel:
            continue
        if not sha:
            # candidates may lack sha — match later by file
            by_file[_basename(rel)] = row
        else:
            by_sha[sha.lower()] = row
        if rel:
            by_file[_basename(rel)] = row

    for row in _read_csv(paths["quality"]):
        rel = _t(row.get("arquivo"))
        bn = _basename(rel)
        if bn:
            by_file[bn] = {**by_file.get(bn, {}), **row}

    for row in _read_csv(paths["categorized_manual"]):
        rel = _t(row.get("arquivo"))
        bn = _basename(rel)
        if bn:
            by_file[bn] = {**by_file.get(bn, {}), **row}

    return by_sha, by_file


def _pick_enriched(sha: str, file_name: str, by_sha: Dict[str, Dict], by_file: Dict[str, Dict]) -> Dict[str, str]:
    if sha and sha.lower() in by_sha:
        return by_sha[sha.lower()]
    return by_file.get(file_name, {})


def _required_fields_detail(row: Dict[str, str]) -> Tuple[List[str], str]:
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        from extract_rebobinagem_batch import required_fields_status  # noqa: WPS433
    except ImportError:
        return [], ""

    tipo, missing = required_fields_status(row)
    if missing:
        labels = [FIELD_LABELS.get(k, k) for k in missing]
        return missing, (
            f"Campos obrigatórios ausentes (tipo={tipo}): "
            + ", ".join(labels)
            + f" [chaves: {', '.join(missing)}]"
        )
    return [], ""


def _nema42_observation(blocks: List[int], row: Dict[str, str], file_name: str) -> str:
    parts: List[str] = []

    campos = _t(row.get("campos_obrig_faltando"))
    if campos:
        labels = [FIELD_LABELS.get(k.strip(), k.strip()) for k in campos.split(",") if k.strip()]
        parts.append(
            "NEMA 42 (605012085.pdf) — histórico B58/B59: "
            f"campos obrigatórios em falta segundo categorize: {', '.join(labels)} "
            f"({campos})."
        )

    _, req_msg = _required_fields_detail(row)
    if req_msg:
        parts.append(req_msg)

    present = []
    for k, label in [
        ("tensao", "tensão"),
        ("fio_principal", "fiação principal"),
        ("espiras_principal", "espiras principal"),
        ("passo_principal", "passo principal"),
        ("capacitor", "capacitor"),
        ("rpm", "RPM extraído"),
        ("potencia_cv", "potência CV"),
    ]:
        v = _t(row.get(k))
        if v:
            present.append(f"{label}={v}")
    if present:
        parts.append("Valores já extraídos (Gemini): " + "; ".join(present) + ".")

    log_lines: List[str] = []
    for bn in blocks:
        log_path = _block_paths(bn)["log"]
        if not log_path.is_file():
            continue
        text = log_path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if "605012085" in line:
                log_lines.append(f"B{bn}: {line.strip()}")
    if log_lines:
        parts.append("Logs de extração: " + " | ".join(log_lines[-4:]))

    alertas = _t(row.get("alertas_criticos") or row.get("alertas_criticos_A") or row.get("alertas"))
    if alertas:
        parts.append(f"Alertas de auditoria associados: {alertas}.")

    parts.append(
        "Decisão sugerida: preencher enrolamento auxiliar no sidecar OU reclassificar tipo_motor "
        "se o PDF for apenas trifásico/sem auxiliar documentado."
    )
    return " ".join(parts)


def collect_pending(blocks: List[int]) -> Dict[str, Dict[str, Any]]:
    """sha -> aggregated record."""
    pending: Dict[str, Dict[str, Any]] = {}

    def upsert(
        sha: str,
        arquivo_rel: str,
        block: int,
        status: str,
        audit_a: str = "",
        extra_codes: str = "",
    ) -> None:
        sha = sha.lower()
        fn = _basename(arquivo_rel)
        rec = pending.get(sha)
        if not rec:
            rec = {
                "sha": sha,
                "file_name": fn,
                "blocks": set(),
                "status_atual": status,
                "audit_raw": [],
                "extra_codes": [],
                "arquivo_rel": arquivo_rel,
            }
            pending[sha] = rec
        rec["blocks"].add(block)
        # AMARELO prevalece; senão último bloco maior atualiza VCA
        if status == "AMARELO_REVISAR":
            rec["status_atual"] = status
        elif rec["status_atual"] != "AMARELO_REVISAR" and block >= max(rec["blocks"]):
            rec["status_atual"] = status
        if audit_a:
            rec["audit_raw"].append(audit_a)
        if extra_codes:
            rec["extra_codes"].append(extra_codes)
        if fn:
            rec["file_name"] = fn

    for block in blocks:
        paths = _block_paths(block)
        for row in _read_csv(paths["alert"]):
            upsert(
                _t(row.get("sha256_arquivo")),
                _t(row.get("arquivo_rel")),
                block,
                _t(row.get("categoria_pos_auditoria")) or "VERDE_COM_ALERTA",
                _t(row.get("audit_warnings_A")),
            )
        for row in _read_csv(paths["manual"]):
            upsert(
                _t(row.get("sha256_arquivo")),
                _t(row.get("arquivo_rel")),
                block,
                _t(row.get("status_extrato")) or "AMARELO_REVISAR",
                extra_codes=_t(row.get("motivo_codigo")),
            )

    return pending


def build_rows(blocks: List[int], pending: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    enrich_cache: Dict[int, Tuple[Dict[str, Dict], Dict[str, Dict]]] = {
        b: _load_enrichment(b) for b in blocks
    }

    rows: List[Dict[str, str]] = []
    for sha, rec in sorted(pending.items(), key=lambda x: (max(x[1]["blocks"]), x[1]["file_name"])):
        block_list = sorted(rec["blocks"])
        block_str = ";".join(f"B{b}" for b in block_list)
        latest = max(block_list)

        enriched: Dict[str, str] = {}
        for b in block_list:
            by_sha, by_file = enrich_cache[b]
            merged = _pick_enriched(sha, rec["file_name"], by_sha, by_file)
            if merged:
                enriched = {**enriched, **merged}

        rpm = _t(enriched.get("rpm") or enriched.get("audit_rpm_original") or enriched.get("audit_rpm_normalizado"))
        pot = _t(enriched.get("potencia_cv") or enriched.get("potencia_cv_original_auditor"))

        codes = _merge_codes(
            ";".join(rec.get("audit_raw", [])),
            ";".join(rec.get("extra_codes", [])),
            _t(enriched.get("alertas_criticos")),
            _t(enriched.get("alertas_criticos_A")),
            _t(enriched.get("alertas")),
            _t(enriched.get("motivos_bloqueio")),
            _t(enriched.get("audit_warnings_A")),
        )

        obs = ""
        if rec["file_name"] == NEMA42_BASENAME or "605012085" in rec["file_name"]:
            obs = _nema42_observation(block_list, enriched, rec["file_name"])

        rows.append(
            {
                "sha": sha,
                "file_name": rec["file_name"],
                "block": block_str,
                "status_atual": rec["status_atual"],
                "alert_codes": codes,
                "rpm_detectado": rpm,
                "potencia_detectada": pot,
                "observacao_mutirao": obs,
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Fila unificada de mutirão cauda B58/B59.")
    ap.add_argument(
        "--blocks",
        default="58,59",
        help="Blocos PASS1-v2 a varrer (default: 58,59).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=REVIEW_DIR / "tail_mutirao_pendencias.csv",
        help="CSV de saída.",
    )
    args = ap.parse_args()
    blocks = [int(x.strip()) for x in args.blocks.split(",") if x.strip()]

    pending = collect_pending(blocks)
    if not pending:
        print("Nenhuma pendência em alert_manifest/manual_review para blocos", blocks, file=sys.stderr)
        return 1

    rows = build_rows(blocks, pending)
    out_path: Path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    summary = {
        "blocks": blocks,
        "pendencias": len(rows),
        "amarelos": sum(1 for r in rows if r["status_atual"] == "AMARELO_REVISAR"),
        "verde_com_alerta": sum(1 for r in rows if r["status_atual"] == "VERDE_COM_ALERTA"),
        "out": str(out_path),
    }
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

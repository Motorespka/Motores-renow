from __future__ import annotations

"""
Pós-auditoria offline do lote N (últimas linhas do bundle_review_candidates).
Somente leitura de ficheiros já gerados — sem Gemini, Supabase ou alterações ao bundle original.
"""

import argparse
import csv
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
MOTORES_ROOT = SCRIPT_DIR.parent

try:
    from tail_mutirao_correcoes_loader import (
        apply_correcao_to_audit_row,
        apply_correcao_to_row,
        load_tail_mutirao_correcoes,
        lookup_correcao,
    )
except ImportError:
    from scripts.tail_mutirao_correcoes_loader import (  # type: ignore
        apply_correcao_to_audit_row,
        apply_correcao_to_row,
        load_tail_mutirao_correcoes,
        lookup_correcao,
    )


def _t(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_tipo_motor(raw: str) -> str:
    t = _t(raw).lower()
    if "trif" in t or ("3" in t and "fase" in t):
        return "trifasico"
    if "mono" in t or ("1" in t and "fase" in t):
        return "monofasico"
    if t in {"monofasico", "trifasico"}:
        return t
    if not t:
        return "desconhecido"
    return "outro"


def required_fields_status(data: Dict[str, str]) -> Tuple[str, List[str]]:
    tipo = normalize_tipo_motor(_t(data.get("tipo_motor")))
    missing: List[str] = []

    def need(k: str) -> None:
        if not _t(data.get(k)):
            missing.append(k)

    if tipo == "monofasico":
        need("tipo_motor")
        need("tensao")
        need("fio_principal")
        need("espiras_principal")
        need("passo_principal")
        need("fio_auxiliar")
        need("espiras_auxiliar")
        need("passo_auxiliar")
    elif tipo == "trifasico":
        need("tipo_motor")
        need("tensao")
        need("fio_principal")
        need("espiras_principal")
        need("passo_principal")
    else:
        need("tensao")

    return tipo, missing


def required_fields_status_with_override(row: Dict[str, str], tipo_override: str) -> Tuple[str, List[str]]:
    """Calcula missing como se `tipo_motor` fosse `tipo_override` (sem alterar a linha original)."""
    tmp = dict(row)
    tmp["tipo_motor"] = tipo_override
    return required_fields_status(tmp)


def norm_arquivo_key(path_like: str) -> str:
    return path_like.replace("/", "\\").strip().lower()


def parse_critical_alert_codes(alertas_criticos_cell: str) -> List[str]:
    s = _t(alertas_criticos_cell)
    if not s:
        return []
    # `alertas_criticos` só contém alertas determinísticos que bloqueiam VERDE_SEGURO.
    return [x.strip() for x in s.split(";") if x.strip() and x.strip().startswith("A")]


def parse_auditor_warning_codes(cell: str) -> List[str]:
    s = _t(cell)
    if not s:
        return []
    out: List[str] = []
    for x in s.split(";"):
        t = x.strip()
        if t and t.startswith("A"):
            out.append(t)
    return out


def is_infrastructure_failure(
    *,
    status: str,
    motivos: str,
    gem: Optional[Dict[str, Any]],
) -> bool:
    """Heurística: fila de reprocesso (não culpa da imagem de forma primária)."""
    if not _t(status).upper().startswith("VERMELHO"):
        return False
    parts: List[str] = []
    if motivos:
        parts.append(motivos)
    if gem:
        if gem.get("falhou") and _t(gem.get("erro_resumido")):
            parts.append(_t(gem.get("erro_resumido")))
        if not gem.get("falhou") and _t(gem.get("erro_resumido")):
            parts.append(_t(gem.get("erro_resumido")))
    blob = " ".join(parts).lower()

    needles = (
        "no_keys",
        "nenhuma chave disponível",
        "quota_exhausted",
        "resource_exhausted",
        " exceeded ",
        "429",
        "rate limit",
        "cooldown",
        "quota",
        "billing",
        "rate_limit",
        "resource exhausted",
    )
    return any(n in blob for n in needles)


def load_bundle_last_rows(path: Path, last_n: int) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if last_n <= 0:
        return rows
    return rows[-last_n:]


def load_quality_map(path: Path) -> Dict[str, Dict[str, str]]:
    """Map arquivo -> linha do audit CSV."""
    if not path.exists():
        return {}
    out: Dict[str, Dict[str, str]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            k = norm_arquivo_key(row.get("arquivo") or "")
            out[k] = dict(row)
    return out


def load_jsonl_gemini_map(path: Path) -> Dict[str, Dict[str, Any]]:
    """Último evento por arquivo_rel (substitui entradas anteriores)."""
    if not path.exists():
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            rel = obj.get("arquivo_rel") or ""
            k = norm_arquivo_key(str(rel))
            if k:
                out[k] = obj.get("gemini") or {}
    return out


def summarize_keys_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"error": "file_missing"}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": str(exc)}
    keys = raw.get("keys") or raw.get("results") or []
    now = int(time.time())
    ok_ready = 0
    ok_in_cooldown = 0
    by_status: Counter[str] = Counter()
    quota_now = 0
    perm_denied = 0
    invalid_k = 0
    for item in keys:
        st = _t(item.get("status"))
        by_status[st] += 1
        if st == "invalid":
            invalid_k += 1
        if st == "permission_denied":
            perm_denied += 1
        if st == "quota_exhausted":
            quota_now += 1
        if st != "ok":
            continue
        ce = int(item.get("cooldown_until_epoch") or 0)
        if ce and now < ce:
            ok_in_cooldown += 1
        else:
            ok_ready += 1
    return {
        "total_keys_tracked": len(keys),
        "by_status": dict(by_status),
        "ok_sem_cooldown_ativo": ok_ready,
        "ok_em_cooldown": ok_in_cooldown,
        "quota_exhausted_agora": quota_now,
        "permission_denied": perm_denied,
        "invalid": invalid_k,
    }


def log_tail_hint(path: Path, max_lines: int = 120) -> str:
    if not path.exists():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return ""
    tail = lines[-max_lines:] if len(lines) > max_lines else lines
    return "\n".join(tail)


def categorize_row(
    row: Dict[str, str],
    audit_row: Optional[Dict[str, str]],
    gem: Optional[Dict[str, Any]],
) -> Tuple[str, str]:
    """
    Retorna (categoria, notas curtas).
    """
    status = _t(row.get("status_revisao")).upper()
    motivos = _t(row.get("motivos_bloqueio"))

    crit_codes: List[str] = []
    warn_codes: List[str] = []
    audit_trace = ""
    if audit_row:
        crit_codes = parse_critical_alert_codes(audit_row.get("alertas_criticos") or "")
        warn_codes = parse_auditor_warning_codes(audit_row.get("alertas_warnings") or "")
        audit_trace = _t(audit_row.get("audit_normalizacao_rastreavel"))
        audit_out_mec = _t(audit_row.get("audit_outlier_mecanico"))
        audit_out_note = _t(audit_row.get("audit_outlier_trace_note"))
    else:
        audit_out_mec = ""
        audit_out_note = ""
    tipo_nf, missing = required_fields_status(row)

    warn_power = [w for w in warn_codes if "A07_WARNING_NORMALIZAVEL" in w]
    tipo_sug = _t(audit_row.get("audit_tipo_motor_sugerido")) if audit_row else ""
    warn_mechanic = [w for w in warn_codes if w.startswith("A11_WARNING")]
    warn_non_mechanic = [w for w in warn_codes if not w.startswith("A11_WARNING")]

    if status.startswith("VERDE"):
        has_block = bool(crit_codes)
        # Se auditor inferiu tipo de forma rastreável, validar campos obrigatórios para esse tipo.
        missing_eff = missing
        if audit_trace == "1" and tipo_sug in {"monofasico", "trifasico"}:
            _, missing_eff = required_fields_status_with_override(row, tipo_sug)
        fields_ok = len(missing_eff) == 0
        if has_block:
            return "VERDE_COM_ALERTA", f"A*:{';'.join(crit_codes)}"
        if not fields_ok:
            return "VERDE_COM_ALERTA", f"campos_obrig_incompletos:{','.join(missing_eff)}"
        if warn_codes and audit_trace != "1":
            if warn_non_mechanic:
                if warn_power:
                    return "VERDE_COM_ALERTA", f"W*:{';'.join(warn_power)}"
                return "VERDE_COM_ALERTA", f"W*:{';'.join(warn_non_mechanic)}"
            # Só warnings mecânicos A11: permite VERDE_SEGURO com rastreio em colunas audit_outlier_*
            if warn_mechanic and audit_out_mec.startswith("warning") and audit_out_note:
                return "VERDE_SEGURO", ""
            if warn_mechanic:
                return "VERDE_COM_ALERTA", f"W*:{';'.join(warn_mechanic)}"
            return "VERDE_COM_ALERTA", f"W*:{';'.join(warn_codes)}"
        return "VERDE_SEGURO", ""

    if status.startswith("AMARELO"):
        return "AMARELO_REVISAR", motivos[:220]

    if status.startswith("PAUSA"):
        return "PENDENTE_INFRA", motivos[:220]

    if status.startswith("VERMELHO"):
        if is_infrastructure_failure(status=status, motivos=motivos, gem=gem):
            return "VERMELHO_NO_KEYS_OU_QUOTA", motivos[:220]
        return "VERMELHO_DADO_RUIM", motivos[:220]

    return "OUTRO", status


def main() -> int:
    ap = argparse.ArgumentParser(description="Categoriza últimas N linhas do bundle (pós-lote, só leitura).")
    ap.add_argument("--last", type=int, default=100)
    ap.add_argument("--bundle-csv", default=str(MOTORES_ROOT / "exports" / "review" / "bundle_review_candidates.csv"))
    ap.add_argument("--jsonl", default=str(MOTORES_ROOT / "exports" / "review" / "bundle_review_candidates.jsonl"))
    ap.add_argument("--quality-csv", default=str(MOTORES_ROOT / "exports" / "review" / "gemini_extraction_quality_lote_100.csv"))
    ap.add_argument("--keys-json", default=str(MOTORES_ROOT / "logs" / "gemini_keys_status.json"))
    ap.add_argument("--batch-log", default=str(MOTORES_ROOT / "logs" / "rebobinagem_batch.log"))
    ap.add_argument("--out-prefix", default=str(MOTORES_ROOT / "exports" / "review" / "lote_100_categorized_quality"))
    ap.add_argument(
        "--tail-correcoes-json",
        default="",
        help="Opcional: metadata/sidecars/tail_mutirao_correcoes.json — aplica override_fields e bypass A* antes de categorizar.",
    )
    args = ap.parse_args()

    last_n = int(args.last)
    bundle_path = Path(args.bundle_csv).expanduser().resolve()
    if not bundle_path.exists():
        print(f"ERRO: bundle CSV inexistente: {bundle_path}", file=sys.stderr)
        return 2

    rows = load_bundle_last_rows(bundle_path, last_n)
    if not rows:
        print("ERRO: nenhuma linha no bundle.", file=sys.stderr)
        return 2

    qmap = load_quality_map(Path(args.quality_csv).expanduser().resolve())
    gmap = load_jsonl_gemini_map(Path(args.jsonl).expanduser().resolve())
    ksum = summarize_keys_status(Path(args.keys_json).expanduser().resolve())

    correcoes_raw: Dict[str, Any] = {}
    corr_path = _t(getattr(args, "tail_correcoes_json", ""))
    if corr_path:
        correcoes_raw = load_tail_mutirao_correcoes(Path(corr_path).expanduser().resolve())
    elif (MOTORES_ROOT / "metadata" / "sidecars" / "tail_mutirao_correcoes.json").is_file():
        correcoes_raw = load_tail_mutirao_correcoes()

    out_base = Path(args.out_prefix).expanduser()
    out_csv = out_base.with_suffix(".csv") if out_base.suffix.lower() != ".csv" else out_base
    out_json = out_base.with_suffix(".json") if out_base.suffix.lower() != ".csv" else out_base.with_suffix(".json")
    out_md = out_base.with_suffix(".md") if out_base.suffix.lower() != ".csv" else out_base.with_suffix(".md")
    _default_categorize = (MOTORES_ROOT / "exports" / "review" / "lote_100_categorized_quality").resolve()
    _is_default_out = out_base.resolve() == _default_categorize

    enriched: List[Dict[str, Any]] = []
    motivos_ctr: Counter[str] = Counter()
    cat_ctr: Counter[str] = Counter()

    fieldnames_base = list(rows[0].keys())
    extra_cols = [
        "categoria",
        "notas",
        "campos_obrig_faltando",
        "alertas_criticos_A",
        "audit_normalizacao_rastreavel",
        "audit_warnings_A",
        "audit_outlier_mecanico",
        "audit_outlier_trace_note",
        "diametro_mm_original_auditor",
        "diametro_mm_normalizado",
        "espiras_principal_original_auditor",
        "espiras_auxiliar_original_auditor",
        "espiras_principal_normalizada",
        "espiras_auxiliar_normalizada",
        "audit_espiras_trace_note",
        "gemini_falhou",
        "gemini_erro_resumo",
    ]

    safe_green: List[Dict[str, str]] = []
    manual: List[Dict[str, str]] = []
    reprocess: List[Dict[str, str]] = []

    for row in rows:
        ak = norm_arquivo_key(row.get("arquivo") or "")
        audit = qmap.get(ak)
        gem = gmap.get(ak)

        correcao = lookup_correcao(correcoes_raw, arquivo=_t(row.get("arquivo"))) if correcoes_raw else None
        row_eff = apply_correcao_to_row(row, correcao)
        audit_eff = apply_correcao_to_audit_row(audit, correcao)

        crit = (
            ";".join(parse_critical_alert_codes(audit_eff.get("alertas_criticos") or ""))
            if audit_eff
            else ""
        )
        tipo_nf, missing = required_fields_status(row_eff)
        cat, notas = categorize_row(row_eff, audit_eff, gem)
        if correcao and _t(correcao.get("comentario")):
            notas = (notas + "|" if notas else "") + f"mutirao:{_t(correcao.get('comentario'))[:120]}"

        rec = dict(row_eff)
        rec["categoria"] = cat
        rec["notas"] = notas
        rec["campos_obrig_faltando"] = ",".join(missing)
        rec["alertas_criticos_A"] = crit
        ar = audit_eff or audit
        rec["audit_normalizacao_rastreavel"] = _t(ar.get("audit_normalizacao_rastreavel")) if ar else ""
        rec["audit_warnings_A"] = ";".join(parse_auditor_warning_codes(ar.get("alertas_warnings") or "")) if ar else ""
        rec["audit_outlier_mecanico"] = _t(ar.get("audit_outlier_mecanico")) if ar else ""
        rec["audit_outlier_trace_note"] = _t(ar.get("audit_outlier_trace_note")) if ar else ""
        rec["diametro_mm_original_auditor"] = _t(ar.get("diametro_mm_original_auditor")) if ar else ""
        rec["diametro_mm_normalizado"] = _t(ar.get("diametro_mm_normalizado")) if ar else ""
        rec["espiras_principal_original_auditor"] = _t(ar.get("espiras_principal_original_auditor")) if ar else ""
        rec["espiras_auxiliar_original_auditor"] = _t(ar.get("espiras_auxiliar_original_auditor")) if ar else ""
        rec["espiras_principal_normalizada"] = _t(ar.get("espiras_principal_normalizada")) if ar else ""
        rec["espiras_auxiliar_normalizada"] = _t(ar.get("espiras_auxiliar_normalizada")) if ar else ""
        rec["audit_espiras_trace_note"] = _t(ar.get("audit_espiras_trace_note")) if ar else ""
        rec["gemini_falhou"] = "1" if gem and gem.get("falhou") else "0"
        rec["gemini_erro_resumo"] = _t(gem.get("erro_resumido"))[:300] if gem else ""

        enriched.append({"record": rec, "cat": cat, "arquivo": row.get("arquivo")})

        cat_ctr[cat] += 1
        for tok in (_t(row.get("motivos_bloqueio")).split(";")):
            tt = tok.strip()
            if tt:
                motivos_ctr[tt] += 1

        if cat == "VERDE_SEGURO":
            safe_green.append(dict(row))
        elif cat in {"VERDE_COM_ALERTA", "AMARELO_REVISAR", "VERMELHO_DADO_RUIM"}:
            manual.append(rec)
        elif cat in {"VERMELHO_NO_KEYS_OU_QUOTA", "PENDENTE_INFRA"}:
            reprocess.append(rec)

    total = len(rows)
    n_seguro = cat_ctr.get("VERDE_SEGURO", 0)
    pct_seguro = (100.0 * n_seguro / total) if total else 0.0
    n_infra = cat_ctr.get("VERMELHO_NO_KEYS_OU_QUOTA", 0)
    pct_infra = (100.0 * n_infra / total) if total else 0.0

    ok_ready = int(ksum.get("ok_sem_cooldown_ativo") or 0)
    quota_now = int(ksum.get("quota_exhausted_agora") or 0)

    escalar_tecnico = pct_seguro >= 75.0 and pct_infra <= 15.0 and ok_ready >= 1 and quota_now == 0
    motivos_escalar_txt = []
    if pct_seguro < 75.0:
        motivos_escalar_txt.append(f"taxa VERDE_SEGURO ({pct_seguro:.1f}%) abaixo de 75%")
    if pct_infra > 15.0:
        motivos_escalar_txt.append(f"fila infraestrutura alta ({pct_infra:.1f}% VERMELHO_NO_KEYS_OU_QUOTA)")
    if ok_ready < 1:
        motivos_escalar_txt.append("nenhuma chave com status ok fora de cooldown (ou ficheiro de chaves desatualizado)")
    if quota_now > 0:
        motivos_escalar_txt.append(f"chaves em quota_exhausted agora: {quota_now}")
    if not escalar_tecnico and not motivos_escalar_txt:
        motivos_escalar_txt.append("verificação agregada não atingiu limiares (OCR local 0% no lote 100 — risco de depender só de Gemini)")

    # O ficheiro de chaves pode ser de data antiga; ainda assim sinaliza 429 agregado
    if ksum.get("quota_exhausted_agora", 0) and quota_now > 0:
        motivos_escalar_txt.append("infra Gemini com quota imediata nos últimos estados gravados")

    recomendacao = "**Não escalar agora.** " + "; ".join(motivos_escalar_txt) if not escalar_tecnico else "**Critérios mínimos numéricos cumpridos**, mas rever infraestrutura (OCR local + quotas) antes do lote 1100."

    summary_block = {
        "generated_at": _utc_now_iso(),
        "last_n": last_n,
        "bundle_csv": str(bundle_path),
        "inputs_used": {
            "quality_csv": str(Path(args.quality_csv)),
            "jsonl": str(Path(args.jsonl)),
            "keys_json": str(Path(args.keys_json)),
            "batch_log": str(Path(args.batch_log)),
        },
        "totais_por_categoria": dict(cat_ctr),
        "percentagens": {
            "verde_seguro": round(pct_seguro, 2),
            "vermelho_infra": round(pct_infra, 2),
        },
        "aproveitamento_import_seguro_pct": round(pct_seguro, 2),
        "gemini_keys_status_resumo": ksum,
        "escalar_aprovado_criterio_automatico": bool(escalar_tecnico),
        "motivos_nao_escalar": motivos_escalar_txt,
        "top_motivos_bloqueio_bundle": motivos_ctr.most_common(25),
    }

    # CSV principal
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fn_out = fieldnames_base + [c for c in extra_cols if c not in fieldnames_base]
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fn_out, extrasaction="ignore")
        w.writeheader()
        for item in enriched:
            w.writerow(item["record"])

    if _is_default_out:
        rep_csv = out_csv.parent / "lote_100_reprocess_no_keys.csv"
        man_csv = out_csv.parent / "lote_100_manual_review.csv"
        safe_csv = out_csv.parent / "lote_100_safe_green_candidates.csv"
    else:
        stem = out_csv.stem
        rep_csv = out_csv.parent / f"{stem}_reprocess_no_keys.csv"
        man_csv = out_csv.parent / f"{stem}_manual_review.csv"
        safe_csv = out_csv.parent / f"{stem}_safe_green_candidates.csv"
    with open(rep_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fn_out, extrasaction="ignore")
        w.writeheader()
        for r in reprocess:
            w.writerow(r)

    with open(man_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fn_out, extrasaction="ignore")
        w.writeheader()
        for r in manual:
            w.writerow(r)
    safe_fields = fieldnames_base
    with open(safe_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=safe_fields, extrasaction="ignore")
        w.writeheader()
        for r in safe_green:
            w.writerow({k: r.get(k, "") for k in safe_fields})

    payload = {
        **summary_block,
        "lists": {
            "VERDE_SEGURO": [_t(x.get("arquivo")) for x in safe_green],
            "VERDE_COM_ALERTA": [_t(r.get("arquivo")) for r in manual if r.get("categoria") == "VERDE_COM_ALERTA"],
            "AMARELO_REVISAR": [_t(r.get("arquivo")) for r in manual if r.get("categoria") == "AMARELO_REVISAR"],
            "VERMELHO_NO_KEYS_OU_QUOTA": [_t(r.get("arquivo")) for r in reprocess],
            "VERMELHO_DADO_RUIM": [_t(r.get("arquivo")) for r in manual if r.get("categoria") == "VERMELHO_DADO_RUIM"],
        },
        "saida_csv": {
            "categorized": str(out_csv.resolve()),
            "reprocess_no_keys": str(rep_csv.resolve()),
            "manual_review": str(man_csv.resolve()),
            "safe_green": str(safe_csv.resolve()),
        },
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown relatório
    md: List[str] = []
    md.append("# Relatório pós-lote — categorização de qualidade\n")
    md.append(f"- Gerado: `{summary_block['generated_at']}`")
    md.append(f"- Últimas linhas analisadas (bundle): **{last_n}**")
    md.append(f"- CSV bundle: `{bundle_path}`\n")

    md.append("## Totais por categoria\n")
    md.append("| Categoria | Quantidade | % do lote |")
    md.append("|---|---:|---:|")
    for k in sorted(cat_ctr.keys()):
        v = cat_ctr[k]
        md.append(f"| {k} | {v} | {100.0 * v / total:.1f}% |")

    md.append("\n## Aproveitamento real (import seguro)\n")
    md.append(f"- **VERDE_SEGURO**: **{n_seguro}** (**{pct_seguro:.1f}%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.")
    md.append(f"- **VERMELHO infra (no_keys/quota/429)**: **{n_infra}** (**{pct_infra:.1f}%**) da amostra.")

    md.append("\n## Estado das chaves (ficheiro gemini_keys_status.json)\n")
    md.append(f"- OK sem cooldown ativo (aprox.): **{ok_ready}**")
    md.append(f"- Em quota_exhausted no último snapshot: **{quota_now}**")
    md.append(f"- Distribuição por status: `{json.dumps(ksum.get('by_status', {}), ensure_ascii=False)}`")

    md.append("\n## Critério automático “pronto para escalar”\n")
    md.append("- VERDE_SEGURO ≥ **75%**")
    md.append("- infraestrutura **VERMELHO_NO_KEYS_OU_QUOTA** relativamente **baixa**")
    md.append("- pelo menos **uma chave OK** utilizável (sem cooldown imediato)")
    md.append("- sem **quota_exhausted** generalizada no snapshot")
    md.append("")
    md.append(f"**Resultado:** {'✅ Critérios numéricos principais OK' if escalar_tecnico else '❌ Critérios não cumpridos ou infraestrutura frágil'}.")
    md.append("")
    md.append(f"**Recomendação:** {recomendacao}")

    md.append("\n## Top motivos de bloqueio (campo motivos_bloqueio no bundle)\n")
    for tok, cnt in motivos_ctr.most_common(15):
        md.append(f"- `{tok}`: **{cnt}**")

    def bullet_list(title: str, paths: List[str]) -> None:
        md.append(f"\n## {title}\n")
        md.append(f"*Total: {len(paths)}*\n")
        for p in paths:
            md.append(f"- `{p}`")

    bullet_list("VERDE_SEGURO (lista)", payload["lists"]["VERDE_SEGURO"])
    bullet_list("VERDE_COM_ALERTA", payload["lists"]["VERDE_COM_ALERTA"])
    bullet_list("AMARELO_REVISAR", payload["lists"]["AMARELO_REVISAR"])
    bullet_list("VERMELHO — infra (reprocessar depois)", payload["lists"]["VERMELHO_NO_KEYS_OU_QUOTA"])
    bullet_list("VERMELHO — dados / revisão humana", payload["lists"]["VERMELHO_DADO_RUIM"])

    md.append("\n## Saídas geradas\n")
    md.append(f"- `{out_csv.resolve()}`")
    md.append(f"- `{out_json.resolve()}`")
    md.append(f"- `{rep_csv.resolve()}`")
    md.append(f"- `{man_csv.resolve()}`")
    md.append(f"- `{safe_csv.resolve()}`")

    md.append("\n## Nota sobre OCR local\n")
    md.append(
        "No lote 100 registado, o texto OCR local estava vazio em todas as linhas — "
        "qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais."
    )

    out_md.write_text("\n".join(md), encoding="utf-8")

    print(json.dumps(summary_block, ensure_ascii=False, indent=2))
    print(f"\nSaídas: {payload['saida_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

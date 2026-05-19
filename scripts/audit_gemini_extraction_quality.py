from __future__ import annotations

"""
Auditoria determinística das últimas N linhas de bundle_review_candidates.csv.
Não chama APIs, não altera o CSV de entrada, não toca Supabase.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
MOTORES_ROOT = SCRIPT_DIR.parent

try:
    from tail_mutirao_correcoes_loader import (
        apply_correcao_to_row,
        filter_alert_codes,
        load_tail_mutirao_correcoes,
        lookup_correcao,
    )
except ImportError:
    from scripts.tail_mutirao_correcoes_loader import (  # type: ignore
        apply_correcao_to_row,
        filter_alert_codes,
        load_tail_mutirao_correcoes,
        lookup_correcao,
    )


def _t(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dedupe_ordered(parts: Sequence[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for x in parts:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _empty_field(s: str) -> bool:
    return not _t(s)


def _normalize_tipo(raw: str) -> str:
    x = _t(raw).lower()
    if x in {"", "desconhecido", "outro"}:
        return x or "vazio"
    if "mono" in x:
        return "monofasico"
    if "trif" in x:
        return "trifasico"
    return x


def _parse_polos_int(polos_raw: str) -> Optional[int]:
    s = _t(polos_raw)
    if not s:
        return None
    m = re.search(r"(\d+)", s)
    if not m:
        return None
    n = int(m.group(1))
    return n if n in {2, 4, 6, 8} else n


def _parse_rpm_numbers(rpm_raw: str) -> List[int]:
    s = _t(rpm_raw)
    if not s:
        return []
    # números com 3–5 dígitos (rpm típicos); ignora fragmentos pequenos
    return [int(x) for x in re.findall(r"\b(\d{3,5})\b", s)]


def _rpm_band_for_polos(p: int) -> Optional[Tuple[int, int]]:
    if p == 2:
        return (2800, 3700)
    if p == 4:
        return (1200, 1900)
    if p == 6:
        return (800, 1300)
    return None


def _rpm_band_for_polos_freq(pol: int, frequencia_s: str) -> Optional[Tuple[int, int]]:
    """
    Faixa conservadora de rpm por polos. Motores 2p alimentados só a 50 Hz têm
    rotação nominal abaixo da faixa usada para o conjunto típico 60 Hz (ex.: 2650
    em placa 50 Hz); evita falso A08 sem relaxar 50/60 explicitados.
    """
    base = _rpm_band_for_polos(pol)
    if not base:
        return None
    if pol != 2:
        return base
    fu = _t(frequencia_s).upper().replace("HZ", " ")
    if re.search(r"50\s*[/,-]\s*60|60\s*[/,-]\s*50|50/60|60/50", fu):
        return base
    if re.search(r"\b50\b", fu) and not re.search(r"\b60\b", fu):
        return (2500, 3200)
    return base


def _parse_medida_mm_val(raw: str) -> Optional[float]:
    """Extrai primeiro número tipo mm/cc (campo texto com vírgula ou ponto)."""
    x = _t(raw).upper().replace("MM", " ").strip()
    if not x:
        return None
    x = x.replace(",", ".")
    m = re.search(r"(\d{1,4}(?:\.\d{1,3})?)", x)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _parse_ranhuras_int_slots(raw: str) -> Optional[int]:
    m = re.search(r"(\d{1,3})", _t(raw))
    if not m:
        return None
    return int(m.group(1))


def _is_pot_frac_or_small_cv(pot_raw: str) -> bool:
    p = _t(pot_raw)
    if not p:
        return False
    if re.search(r"\d\s*/\s*\d+", p):
        return True
    pu = p.lower().replace(",", ".")
    mf = re.search(r"([\d]{1,2})\.([\d]{1,2})\s*cv\b", pu)
    if mf:
        v = float(f"{mf.group(1)}.{mf.group(2)}")
        if v <= 5.0:
            return True
    mh = re.search(r"(?<![\d/])(\d)\s*(?:cv|c\.v\.)\b", pu)
    if mh and "/" not in p:
        if int(mh.group(1)) <= 5:
            return True
    return False


def _iec_carcc_pequeno(carcaca_raw: str) -> bool:
    return bool(re.search(r"\b(56[A-Z]?|63[A-Z]?|71[A-Z]?|NEMA\s*42|NEMA\s*48)\b", _t(carcaca_raw), re.I))


def _iec_c80_marker(arquivo_raw: str, carcaca_raw: str, blob_text: str) -> bool:
    """Carcaça/nome IEC 80 ou equivalente VOGE BK (CV-C80A/B …). Conservador."""
    combo = (_t(arquivo_raw) + "\n" + _t(carcaca_raw) + "\n" + _t(blob_text)).upper()
    if re.search(r"(CV[-–]?\s*C\s*80\s*[AB]?|(?<!\d)CV[-–]?C\s*80\s*[AB]?|\bC80[AB]\b|\bIEC\s*[-–]?\s*80\b|\bIEC80\b)", combo, re.I):
        return True
    cx = _t(carcaca_raw).lower().replace(" ", "")
    return bool(re.fullmatch(r"(80|80a|80b|iec80)", cx))


def _dia855_frac_c80_evidence(
    *,
    dm: Optional[float],
    dm_raw_txt: str,
    row: Dict[str, str],
    blob_concat: str,
    grande: bool,
) -> Tuple[bool, str]:
    """
    Evidência forte (sem Gemini) para ler 855 mm como erro colunar/decimal coerente com IEC C80
    quando potência e ranhuras/pacote apontam motor pequeno. Não corrige OCR no PDF — só auditor.
    """
    if grande:
        return False, ""
    if dm is None or abs(dm - 855.0) > 0.75:
        return False, ""
    pot_raw = _t(row.get("potencia_cv"))
    if not _is_pot_frac_or_small_cv(pot_raw):
        return False, ""

    arquivo = row.get("arquivo") or ""
    carcac = row.get("carcaca") or ""
    pkt = _parse_medida_mm_val(_t(row.get("pacote_mm")))
    rz = _parse_ranhuras_int_slots(_t(row.get("ranhuras")))

    if not _iec_c80_marker(arquivo, carcac, blob_concat):
        return False, ""
    if pkt is None or not (40.0 <= pkt <= 110.0):
        return False, ""
    if rz is None or not (20 <= rz <= 48):
        return False, ""

    note = (
        f"855_mm_bruto→85.5_mm_normalizado_auditor;C80_nom/carc;cfr_pacote_{pkt:g}mm;cfr_slots_{rz};"
        f"pot={pot_raw[:30]};arq_match"
    )
    return True, note


def _merge_audit_trace_one(meta: Dict[str, str]) -> None:
    meta["audit_normalizacao_rastreavel"] = "1"


def _extract_mono_espiras_bobina_pair(blob: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Folha de instrução: após 'Espiras por bobina', duas linhas tipo 12:25:33 e 8:12:28 (efetivo/auxiliar).
    Conservador: só captura triplets 1–3 dígitos por segmento.
    """
    if not _t(blob):
        return None, None, ""
    m = re.search(
        r"(?is)espiras\s+por\s+bobina[\s\S]{0,200}?(\d{1,3}\s*:\s*\d{1,3}\s*:\s*\d{1,3})\s+(\d{1,3}\s*:\s*\d{1,3}\s*:\s*\d{1,3})",
        blob,
    )
    if not m:
        return None, None, ""

    def _norm_triplet(x: str) -> str:
        return ":".join(p.strip() for p in re.split(r"\s*:\s*", x.strip()) if p.strip())

    return _norm_triplet(m.group(1)), _norm_triplet(m.group(2)), "folha_instrucao_espiras_por_bobina"


def _field_looks_wire_catalog_in_espiras_slot(s: str) -> bool:
    """Código de fio tipo 10.5002.010 colado no campo espiras (não é contagem)."""
    x = _t(s)
    if not x:
        return False
    return bool(re.search(r"\d+\.\d+\.\d{3,}", x))


def _normalize_espiras_colon_tokens_leading_zeros(val: str, blob_u: str) -> Tuple[Optional[str], str]:
    """
    Lista técnica '011:012:010' → strip de zeros à esquerda por token só se o compacto aparece no blob.
    """
    raw = _t(val)
    if ":" not in raw:
        return None, ""
    parts = [_t(p) for p in raw.split(":") if _t(p)]
    if len(parts) < 2:
        return None, ""
    new_parts: List[str] = []
    changed = False
    for p in parts:
        if re.fullmatch(r"0+(\d+)", p):
            nv = str(int(p))
            if nv != p:
                changed = True
            new_parts.append(nv)
        elif re.fullmatch(r"\d+", p):
            new_parts.append(str(int(p)))
        else:
            return None, ""
    if not changed:
        return None, ""
    cand = ":".join(new_parts)
    compact_blob = re.sub(r"\s+", "", blob_u)
    compact_cand = re.sub(r"\s+", "", cand.upper())
    if compact_cand in compact_blob:
        return cand, "tokens_zeros_espiadas_substring_blob"
    return None, ""


def _motor_grande_provavel(pot_raw: str, carcaca_raw: str) -> bool:
    """Motor grande/industrial — relaxa outliers de φ muito grandes (conservador)."""
    pot = _t(pot_raw).upper().replace(",", ".")
    numbers = []
    if "/" not in pot:
        numbers = [int(g) for g in re.findall(r"(?<!\d)(\d{2,3})\b", pot) if g.isdigit()]
    if numbers and max(numbers) >= 30:
        return True
    c = _t(carcaca_raw).upper()
    if re.search(r"\b(225|250|280|315|355|400|450|560|630)\b", c):
        return True
    return False


def _is_visual_placeholder_aux(s: str) -> bool:
    """Valores tipo placeholder — não contam como campo preenchido (aux/principal)."""
    u = _t(s).upper().replace("\u2013", "-").replace("\u2014", "-")
    if not u:
        return True
    u_ns = "".join(ch for ch in u if not ch.isspace())
    if u_ns in {
        "*_*-*",
        "*_*-*",
        "*-*-*",
        "*_*",
        "***",
        "---",
        "-",
        "/",
        "N/A",
        "NA",
        "?",
    }:
        return True
    if re.fullmatch(r"[*.\-_#/\\]+", u_ns.replace(" ", "")):
        return True
    if len(u_ns) >= 3 and re.fullmatch(r"[*\-_/]+", u_ns.replace(":", "")):
        return True
    return False


def _field_nonempty_audit(fp: Optional[str]) -> bool:
    return not _is_visual_placeholder_aux(fp or "")


def _filename_decimal_cv_echoes_potencia(arquivo_raw: str, pot_raw: str) -> str:
    """
    Quando o campo potência traz decimal 12–14 CV (ex.: 12,5) e o basename do PDF repete o mesmo
    literal antes de CV → evidência não ambígua vinda do próprio ficheiro (rastreável).
    """
    fn = Path(_t(arquivo_raw).replace("\\", "/")).name.upper().replace(",", ".")
    pu = _t(pot_raw).upper().replace(" ", "").replace(",", ".")
    m = re.search(r"\b(1[234])\.(\d+)\b", pu)
    if not m:
        return ""
    a, b = m.group(1), m.group(2)
    needle = f"{a}.{b}".upper()
    fn_compact = re.sub(r"\s+", "", fn)
    # basename tipo "12.5cv 4p" → compacto "12.5CV4P"; evitar \\b após V se vier dígito (ex.: "...CV4p").
    nc = re.sub(r"\s+", "", needle)
    pat = rf"(?<![0-9.]){re.escape(nc)}[\s._-]*C\.?V"
    if re.search(pat, fn_compact, flags=re.I):
        return f"filename_decimal_cv_echo_{needle}"
    return ""


def _audit_concat_blob(row: Dict[str, str], extra_evidence: str = "") -> str:
    cols = (
        row.get("potencia_cv"),
        row.get("tensao"),
        row.get("rpm"),
        row.get("carcaca"),
        row.get("capacitor"),
        row.get("fio_principal"),
        row.get("fio_auxiliar"),
        row.get("arquivo"),
        row.get("motivos_bloqueio"),
    )
    chunks = [_t(x) for x in cols if _t(x)]
    if extra_evidence:
        chunks.append(extra_evidence)
    blob = "\n".join(chunks)
    if len(blob) > 24000:
        return blob[:24000]
    return blob


def _fraction_evidence_strength(blob_u: str) -> Dict[str, bool]:
    b = blob_u.upper()
    return {
        "meio": bool(
            re.search(
                r"(\b1\s*/\s*2\b|½|\\bMEIO\b|\bHALF\b|\\bHP\b|[=]\s*\s*1\s*/\s*2|\\bCV\s*=?\s*\s*1\s*/\s*2|CV\s*[0O]\s*[,\.]?\s*5\b)",
                b,
                re.I,
            )
        ),
        "quarto": bool(
            re.search(
                r"(\b1\s*/\s*4\b|¼|\\bQUART|\\bCV\s*=?\s*\s*1\s*/\s*4|\\bCV\s*[0O]\s*[,\.]?\s*25\b|\\b[\.,]\s*25\s*CV)",
                b,
                re.I,
            )
        ),
        "terço": bool(re.search(r"(\b1\s*/\s*3\b|⅓|TER[CÇ]O)", b, re.I)),
    }


def _infer_tipo_motor_from_evidence(
    *,
    tipo_norm: str,
    tensao: str,
    capacitor: str,
    fio_principal: str,
    fio_auxiliar: str,
    espiras_auxiliar: str,
    passo_auxiliar: str,
    blob_u: str,
) -> Tuple[str, str]:
    """
    Inferência conservadora do tipo de motor quando `tipo_motor` vem vazio/outro/desconhecido.
    Retorna (tipo_sugerido, nota_evidencia). Vazio se não for possível inferir sem inventar.
    """
    if tipo_norm in {"monofasico", "trifasico"}:
        return "", ""

    fa_nz = _field_nonempty_audit(fio_auxiliar)
    ea_nz = _field_nonempty_audit(espiras_auxiliar)
    pa_nz = _field_nonempty_audit(passo_auxiliar)
    cap_nz = _field_nonempty_audit(capacitor)

    # Monofásico: presença explícita de bobina auxiliar (e/ou capacitor) é evidência forte.
    if (fa_nz and ea_nz and pa_nz) or (cap_nz and (fa_nz or ea_nz or pa_nz)):
        return "monofasico", "auxiliar_e/ou_capacitor_preenchidos"

    # Trifásico: tensão típica com 3 níveis e ausência de auxiliar; ou padrão 3X no fio principal.
    tens_u = _t(tensao).upper().replace(" ", "")
    fio_p_u = _t(fio_principal).upper().replace(" ", "")
    if ("/" in tens_u and tens_u.count("/") >= 2) and not (fa_nz or ea_nz or pa_nz):
        return "trifasico", "tensao_tripla_sem_auxiliar"
    if re.search(r"\b3X\b|\b3\s*X\b", fio_p_u) and not (fa_nz or ea_nz or pa_nz):
        return "trifasico", "fio_principal_padrao_3X_sem_auxiliar"

    # Texto bruto: procura explícita por mono/trif (quando disponível via evidence).
    if re.search(r"\bMONO(FA(SI)?CO)?\b|\b1\s*FA(SE)?\b", blob_u, re.I):
        return "monofasico", "texto_evidence_menciona_mono"
    if re.search(r"\bTRI(FA(SI)?CO)?\b|\b3\s*FA(SE)?\b", blob_u, re.I):
        return "trifasico", "texto_evidence_menciona_trif"

    return "", ""


def _audit_norm_arquivo_key(path_like: str) -> str:
    return _t(path_like).replace("/", "\\").lower()


def load_audit_evidence_jsonl(jsonl_path: Optional[Path]) -> Dict[str, str]:
    """Chave arquivo_rel baixa → texto (OCR local + trechos resultado) para A07/aux."""
    if jsonl_path is None or not jsonl_path.is_file():
        return {}
    out: Dict[str, str] = {}
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            rel = _t(obj.get("arquivo_rel") or "")
            if not rel:
                continue
            local = obj.get("local") if isinstance(obj.get("local"), dict) else {}
            texto = _t(local.get("texto_ocr_bruto") if isinstance(local, dict) else "")
            bits: List[str] = []
            r = obj.get("resultado")
            if isinstance(r, dict):
                for kk in ("tipo_motor", "potencia_cv", "carcaca", "capacitor", "motivos_bloqueio"):
                    vv = _t(r.get(kk))
                    if vv:
                        bits.append(f"{kk}={vv}")
            blob_parts = []
            if texto:
                blob_parts.append(texto)
            if bits:
                blob_parts.append("\n".join(bits))
            blob = "\n".join(blob_parts)
            k = _audit_norm_arquivo_key(rel)
            if k:
                out[k] = blob[:32768]
    return out


def _collect_alerts_blocking_and_warnings(
    row: Dict[str, str],
    *,
    evidence_extra: str = "",
) -> Tuple[List[str], List[str], Dict[str, str]]:
    """Retorna alertas para `alertas_criticos` (bloqueiam VERDE_SEGURO) e warnings (orientação)."""
    blocking: List[str] = []
    warnings: List[str] = []
    meta: Dict[str, str] = {
        "potencia_cv_original_auditor": "",
        "potencia_cv_normalizada": "",
        "audit_normalizacao_rastreavel": "",
        "audit_power_trace_note": "",
        "audit_tipo_motor_sugerido": "",
        "audit_type_trace_note": "",
        "audit_rpm_original": "",
        "audit_rpm_normalizado": "",
        "audit_rpm_trace_note": "",
        "audit_outlier_mecanico": "",
        "audit_outlier_trace_note": "",
        "diametro_mm_original_auditor": "",
        "diametro_mm_normalizado": "",
        "espiras_principal_original_auditor": "",
        "espiras_auxiliar_original_auditor": "",
        "espiras_principal_normalizada": "",
        "espiras_auxiliar_normalizada": "",
        "audit_espiras_trace_note": "",
        "audit_trace_note": "",
    }

    pot_raw = _t(row.get("potencia_cv"))
    meta["potencia_cv_original_auditor"] = pot_raw

    tipo_raw = _t(row.get("tipo_motor"))
    tipo = _normalize_tipo(tipo_raw)

    blob = _audit_concat_blob(row, evidence_extra)
    blob_u = blob.upper()

    def add_block(code: str) -> None:
        if code not in blocking:
            blocking.append(code)

    def add_warn(code: str) -> None:
        if code not in warnings:
            warnings.append(code)

    fp, ep, pp = _t(row.get("fio_principal")), _t(row.get("espiras_principal")), _t(row.get("passo_principal"))
    fa = row.get("fio_auxiliar")
    ea = row.get("espiras_auxiliar")
    pa = row.get("passo_auxiliar")

    fp_nz = _field_nonempty_audit(fp)
    ep_nz = _field_nonempty_audit(ep)
    pp_nz = _field_nonempty_audit(pp)
    fa_nz = _field_nonempty_audit(fa if fa else "")
    ea_nz = _field_nonempty_audit(ea if ea else "")
    pa_nz = _field_nonempty_audit(pa if pa else "")

    tensao = _t(row.get("tensao"))
    rpm_s = _t(row.get("rpm"))
    polos_s = _t(row.get("polos"))
    pot = pot_raw
    capacitor = _t(row.get("capacitor"))

    fra = _fraction_evidence_strength(blob_u)
    evid_any = fra["meio"] or fra["quarto"] or fra["terço"]

    # tipo / tensão
    if not tipo_raw or tipo in {"vazio", "desconhecido", "outro"}:
        sug, note = _infer_tipo_motor_from_evidence(
            tipo_norm=tipo,
            tensao=tensao,
            capacitor=capacitor,
            fio_principal=fp,
            fio_auxiliar=_t(fa),
            espiras_auxiliar=_t(ea),
            passo_auxiliar=_t(pa),
            blob_u=blob_u,
        )
        if sug:
            meta["audit_tipo_motor_sugerido"] = sug
            meta["audit_type_trace_note"] = note
            meta["audit_normalizacao_rastreavel"] = "1"
            add_warn(f"A10_WARNING_tipo_inferido_com_evidencia={sug};{note}")
        else:
            add_block("A10_tipo_vazio_ou_desconhecido")

    if _empty_field(tensao):
        add_block("A09_tensao_vazia")

    # monóf ausência real (placeholder não conta como preenchido)
    if tipo == "monofasico":
        if not fp_nz or not ep_nz or not pp_nz:
            add_block("A01_mono_sem_fio_espiras_passo_principal")

    if tipo == "monofasico":
        if not fa_nz or not ea_nz or not pa_nz:
            add_block("A02_mono_sem_fio_espiras_passo_auxiliar")

    # trifásico: apenas aux “real”; placeholders não disparam A03
    if tipo == "trifasico":
        aux_any = fa_nz or ea_nz or pa_nz
        if aux_any:
            add_block("A03_trifasico_com_auxiliar_preenchido")
        princ_empty = (not fp_nz) or (not ep_nz) or (not pp_nz)
        if princ_empty and aux_any:
            add_block("A03b_trifasico_principal_vazio_aux_preenchido")

    wireish_in_passo = re.compile(
        r"(?is)\b1\s*[xX]\s*\d{2}\b|\b2\s*[xX]\s*\d{2}\b|\bAWG\b|\b1\.18\b|\b0\.80\b"
    )
    for label, val in (("principal", pp), ("auxiliar", pa)):
        if wireish_in_passo.search(_t(val)):
            add_block(f"A04_passo_com_padrao_de_fio_{label}")

    espira_like = re.compile(r"^\s*(35|70|115)\s*$")
    for label, val in (("principal", pp), ("auxiliar", pa)):
        if espira_like.match(_t(val)):
            add_block(f"A05_passo_valor_tipo_espiras_{label}")

    fio_mm_only = re.compile(r"^\s*(1\.18|0\.80)\s*$")
    for label, val in (("principal", fp), ("auxiliar", fa)):
        if fio_mm_only.match(_t(val)):
            add_block(f"A04b_fio_apenas_metrica_mm_{label}")

    leading_zero = re.compile(r"(?<!\d)0\d{2,}(?!\d)")
    ep_s = _t(ep)
    ea_s = _t(ea)
    meta["espiras_principal_original_auditor"] = ep_s
    meta["espiras_auxiliar_original_auditor"] = ea_s
    meta["espiras_principal_normalizada"] = ""
    meta["espiras_auxiliar_normalizada"] = ""
    meta["audit_espiras_trace_note"] = ""

    skip_a06_princ = False
    skip_a06_aux = False
    esp_trace_bits: List[str] = []

    # A06 — recuperação conservadora (mono + texto instrução) ou tokens com zero à esquerda com evidência no blob
    if tipo == "monofasico":
        p_blob, s_blob, blob_note = _extract_mono_espiras_bobina_pair(blob)
        wire_p = _field_looks_wire_catalog_in_espiras_slot(ep_s)
        wire_a = _field_looks_wire_catalog_in_espiras_slot(ea_s)
        a06p = bool(leading_zero.search(ep_s))
        a06a = bool(leading_zero.search(ea_s))
        if p_blob and s_blob and (wire_p or wire_a or a06p or a06a):
            meta["espiras_principal_normalizada"] = p_blob
            meta["espiras_auxiliar_normalizada"] = s_blob
            esp_trace_bits.append(f"mono_recuperado_instrucao;{blob_note}")
            _merge_audit_trace_one(meta)
            add_warn("A06_WARNING_espiras_normalizada_rastreavel")
            skip_a06_princ = True
            skip_a06_aux = True

    if not skip_a06_princ:
        np, nn = _normalize_espiras_colon_tokens_leading_zeros(ep_s, blob_u)
        if np:
            meta["espiras_principal_normalizada"] = np
            esp_trace_bits.append(nn)
            _merge_audit_trace_one(meta)
            add_warn("A06_WARNING_espiras_normalizada_rastreavel")
            skip_a06_princ = True

    if not skip_a06_aux:
        na, nn2 = _normalize_espiras_colon_tokens_leading_zeros(ea_s, blob_u)
        if na:
            meta["espiras_auxiliar_normalizada"] = na
            esp_trace_bits.append(nn2)
            _merge_audit_trace_one(meta)
            add_warn("A06_WARNING_espiras_normalizada_rastreavel")
            skip_a06_aux = True

    if esp_trace_bits:
        meta["audit_espiras_trace_note"] = "; ".join(esp_trace_bits)[:800]

    for label, val, skipped in (
        ("principal", ep, skip_a06_princ),
        ("auxiliar", ea, skip_a06_aux),
    ):
        if skipped:
            continue
        if leading_zero.search(_t(val)):
            add_block(f"A06_espiras_zero_a_esquerda_{label}")

    # ----- A7 potência -----
    pot_u = pot.upper().replace(" ", "")
    trace_notes: List[str] = []

    if pot_u:
        decimal_markup = bool(re.search(r"(?<!\d)(?:12|13|14)([\.,]\d+)\b", pot.upper()))
        if decimal_markup:
            fn_cv_ev = _filename_decimal_cv_echoes_potencia(_t(row.get("arquivo")), pot_raw)
            if fra["meio"] and bool(re.search(r"12([\.,]\d+)", pot_u)):
                trace_notes.append("evid_frac_meio_placa_vs_campo_decimal")
                meta["audit_normalizacao_rastreavel"] = "1"
                meta["potencia_cv_normalizada"] = "1/2"
                add_warn(f"A07_WARNING_potencia_normalizada_rastreavel=1/2;potencia_cv={pot_raw[:60]}")
            elif evid_any:
                trace_notes.append("fracoes_no_blob_potencia_decimal")
                meta["audit_normalizacao_rastreavel"] = "1"
                add_warn(f"A07_WARNING_NORMALIZAVEL_frac_ambigua_potencia_cv={pot_raw[:60]}")
            elif fn_cv_ev:
                trace_notes.append(fn_cv_ev)
                meta["audit_normalizacao_rastreavel"] = "1"
                meta["audit_trace_note"] = fn_cv_ev
                _merge_audit_trace_one(meta)
                add_warn(f"A07_WARNING_potencia_decimal_filename_evidencia;potencia_cv={pot_raw[:60]}")
            else:
                trace_notes.append("decimal_sem_frac_strong_manter_critico_manual")
                add_block(f"A07_potencia_decimal_sem_evidencia_frac_potencia_cv={pot_raw[:60]}")
        else:
            if "1/2" not in pot and "½" not in pot:
                if re.search(r"(?<![\d/])\b12\b(?!\s*/)", pot_u) or pot_u in {"12", "12CV"}:
                    if evid_any or fra["meio"]:
                        trace_notes.append("int12_vs_frac_com_contexto_blob")
                        meta["audit_normalizacao_rastreavel"] = "1"
                        add_warn(f"A07_WARNING_NORMALIZAVEL_int12_frac_context_potencia_cv={pot_raw[:60]}")
                    else:
                        add_block("A07_potencia_12_possivel_confusao_com_meio_cv")

            if "1/4" not in pot:
                if re.search(r"(?<![\d/])\b14\b(?!\s*/)", pot_u) or pot_u in {"14", "14CV"}:
                    if evid_any or fra["quarto"]:
                        trace_notes.append("int14_frac_ctx")
                        meta["audit_normalizacao_rastreavel"] = "1"
                        add_warn(f"A07_WARNING_NORMALIZAVEL_int14_frac_context_potencia_cv={pot_raw[:60]}")
                    else:
                        add_block("A07_potencia_14_possivel_confusao_com_quarto_cv")

            if "1/3" not in pot:
                if re.search(r"(?<![\d/])\b13\b(?!\s*/)", pot_u) or pot_u in {"13", "13CV"}:
                    if evid_any or fra["terço"]:
                        trace_notes.append("int13_frac_ctx")
                        meta["audit_normalizacao_rastreavel"] = "1"
                        add_warn(f"A07_WARNING_NORMALIZAVEL_int13_frac_context_potencia_cv={pot_raw[:60]}")
                    else:
                        add_block("A07_potencia_13_possivel_confusao_com_terco_cv")

        if trace_notes:
            meta["audit_power_trace_note"] = "; ".join(trace_notes)[:500]

    # rpm vs polos (conservador; permite WARNING rastreável quando plausível)
    pol = _parse_polos_int(polos_s)
    rpms = _parse_rpm_numbers(rpm_s)
    freq_for_band = _t(row.get("frequencia"))
    band_base_2p = _rpm_band_for_polos(pol) if pol == 2 else None
    band = _rpm_band_for_polos_freq(pol, freq_for_band) if pol is not None else None
    meta["audit_rpm_original"] = rpm_s
    if band and rpms:
        lo, hi = band
        # Regra dura: rpm absurdo -> bloqueia sempre
        absurd = [r for r in rpms if r > 5000]
        if absurd:
            add_block(f"A08_rpm_absoluto_absurdo_rpm={absurd[0]}")
            meta["audit_rpm_trace_note"] = f"absurdo_gt5000; rpms={rpms}"
        else:
            in_band = [r for r in rpms if lo <= r <= hi]
            out_band = [r for r in rpms if r < lo or r > hi]
            if in_band and not out_band:
                if pol == 2 and band_base_2p and band != band_base_2p:
                    note = (
                        f"faixa_rpm_2p_monofreq_50Hz=({lo}-{hi})_ref_padrao_60Hz="
                        f"({band_base_2p[0]}-{band_base_2p[1]})"
                    )
                    meta["audit_trace_note"] = note[:800]
                    meta["audit_rpm_trace_note"] = note[:500]
                    _merge_audit_trace_one(meta)
            elif in_band and out_band:
                # caso comum: rpm duplo 50/60 com um valor levemente fora
                freq_u = _t(row.get("frequencia")).upper()
                has_50_60 = bool(re.search(r"\b50\b|\b60\b|50/60|50-60", freq_u)) or ("/" in rpm_s)
                # tolerâncias por polos
                tol = 0
                if pol == 2:
                    tol = 250  # ex.: 2730 vs 2800, com 50/60
                elif pol == 4:
                    tol = 150
                elif pol == 6:
                    tol = 120
                within_tol = all((lo - tol) <= r <= (hi + tol) for r in out_band)
                if has_50_60 and within_tol:
                    meta["audit_rpm_normalizado"] = str(max(in_band))
                    meta["audit_rpm_trace_note"] = f"dual_or_freq; in_band={in_band}; out_band={out_band}; tol={tol}"
                    meta["audit_normalizacao_rastreavel"] = "1"
                    add_warn(
                        f"A08_WARNING_rpm_leve_fora_faixa_mas_plausivel_{pol}p_({lo}-{hi})_rpms={rpms}"
                    )
                else:
                    add_block(f"A08_rpm_fora_faixa_polos_{pol}p_({lo}-{hi})_rpm={out_band[0]}")
                    meta["audit_rpm_trace_note"] = f"fora_sem_evid; rpms={rpms}; freq={freq_u}"
            else:
                # nenhum dentro da faixa
                freq_u = _t(row.get("frequencia")).upper()
                add_block(f"A08_rpm_fora_faixa_polos_{pol}p_({lo}-{hi})_rpm={out_band[0] if out_band else rpms[0]}")
                meta["audit_rpm_trace_note"] = f"nenhum_in_band; rpms={rpms}; freq={freq_u}"

    # ----- A11 outliers mecânicos (conservador; sem corrigir valores) -----
    carcac = _t(row.get("carcaca"))
    dm = _parse_medida_mm_val(_t(row.get("diametro_mm")))
    pkt = _parse_medida_mm_val(_t(row.get("pacote_mm")))
    rz = _parse_ranhuras_int_slots(_t(row.get("ranhuras")))
    omeca_parts: List[str] = []
    out_crit = False
    out_warn = False
    dia_norm_855 = False

    dm_raw_saved = _t(row.get("diametro_mm"))
    meta["diametro_mm_original_auditor"] = dm_raw_saved
    meta["diametro_mm_normalizado"] = ""

    if pkt is not None and pkt > 1000:
        add_block(f"A11_pacote_mm_gt1000_mm={pkt:.1f}")
        out_crit = True
        omeca_parts.append(f"pacote_mm>{1000}:{pkt:g}")

    if rz is not None:
        if rz < 4 or rz > 120:
            add_block(f"A11_ranhuras_absurdas={rz}")
            out_crit = True
            omeca_parts.append(f"ranhuras_crit:{rz}")
        elif rz < 8 or rz > 96:
            add_warn(f"A11_WARNING_ranhuras_fora_faixa_slots={rz}")
            out_warn = True
            omeca_parts.append(f"ranhuras_warn:{rz}")

    small_like = _is_pot_frac_or_small_cv(pot) or _iec_carcc_pequeno(carcac)
    grande = _motor_grande_provavel(pot, carcac)

    ok_855_hist, dia855_note = _dia855_frac_c80_evidence(
        dm=dm,
        dm_raw_txt=dm_raw_saved,
        row=row,
        blob_concat=blob,
        grande=grande,
    )

    if dm is not None:
        if ok_855_hist:
            dia_norm_855 = True
            meta["diametro_mm_original_auditor"] = dm_raw_saved if dm_raw_saved else f"{dm:g}"
            meta["diametro_mm_normalizado"] = "85.5"
            _merge_audit_trace_one(meta)
            add_warn("A11_WARNING_diametro_normalizado_rastreavel")
            out_warn = True
            omeca_parts.append("dia_warn_norm855_auditor_para_85.5")
            omeca_parts.append(dia855_note[:400])
            # Substitui o bloqueio duro gt800 apenas neste cenário rastreado.
        elif dm > 800 and not grande:
            add_block(f"A11_diametro_provavel_erro_gt800_sem_motor_grande_mm={dm:.1f}".rstrip("0").rstrip("."))
            out_crit = True
            omeca_parts.append(f"diam_crit>800:{dm:g}")
        elif dm > 800 and grande:
            add_warn(f"A11_WARNING_diametro_grande_mas_motor_provavel_potente_mm={dm:.1f}".rstrip("0").rstrip("."))
            out_warn = True
            omeca_parts.append(f"diam_warn>800_grande:{dm:g}")
        elif dm > 500 and small_like and not grande and not dia_norm_855:
            add_warn(f"A11_WARNING_diametro_alto_frac_ou_carcaca_pequena_mm={dm:.1f}".rstrip("0").rstrip("."))
            out_warn = True
            omeca_parts.append(f"diam_warn>500_frac_peq:{dm:g}")

    lvl = ""
    if out_crit and out_warn:
        lvl = "critico|warning"
    elif out_crit:
        lvl = "critico"
    elif out_warn:
        lvl = "warning"
    meta["audit_outlier_mecanico"] = lvl
    meta["audit_outlier_trace_note"] = "; ".join(omeca_parts)[:800]

    return blocking, warnings, meta


def _pipeline_status_alerts(status_raw: str) -> List[str]:
    """Marcadores determinísticos pelo status já atribuído pelo pipeline (não são os A*critérios)."""
    st = _t(status_raw).upper()
    if st.startswith("AMARELO"):
        return ["S_pipeline_AMARELO_REVISAR"]
    if st.startswith("VERMELHO"):
        return ["S_pipeline_VERMELHO_REVISAR"]
    return []


def _status_bucket(status: str) -> str:
    s = _t(status).upper()
    if s.startswith("VERDE"):
        return "verde"
    if s.startswith("AMARELO"):
        return "amarelo"
    if s.startswith("VERMELHO"):
        return "vermelho"
    return "outro"


def _load_last_rows(csv_path: Path, last_n: int) -> List[Dict[str, str]]:
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows: List[Dict[str, str]] = [dict(r) for r in reader]
    if last_n <= 0:
        return rows
    return rows[-last_n:]


def main() -> int:
    ap = argparse.ArgumentParser(description="Auditoria determinística das últimas N linhas do bundle_review_candidates.")
    ap.add_argument(
        "--input",
        default=str(MOTORES_ROOT / "exports" / "review" / "bundle_review_candidates.csv"),
        help="CSV de entrada (somente leitura).",
    )
    ap.add_argument("--last", type=int, default=20, help="Últimas N linhas (dados) a auditar.")
    ap.add_argument(
        "--out",
        default=str(MOTORES_ROOT / "exports" / "review" / "gemini_extraction_quality_lote_06"),
        help="Prefixo de saída (sem extensão): gera .csv, .json e .md no mesmo diretório.",
    )
    ap.add_argument(
        "--jsonl-evidence",
        default="",
        help="Opcional: JSONL paralelo ao CSV (ex. *_candidates.jsonl) com OCR/resumo linha→evidências A07.",
    )
    ap.add_argument(
        "--tail-correcoes-json",
        default="",
        help="Opcional: metadata/sidecars/tail_mutirao_correcoes.json — override_fields + force_bypass_alerts.",
    )
    args = ap.parse_args()

    csv_in = Path(args.input).expanduser().resolve()
    if not csv_in.exists():
        print(f"ERRO: CSV não encontrado: {csv_in}", file=sys.stderr)
        return 2

    out_base = Path(args.out).expanduser()
    if out_base.suffix.lower() == ".csv":
        out_base = out_base.with_suffix("")
    out_dir = out_base.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_base.with_suffix(".csv")
    out_json = out_base.with_suffix(".json")
    out_md = out_base.with_suffix(".md")

    jsonl_ev = _t(getattr(args, "jsonl_evidence", ""))
    jpath = Path(jsonl_ev).expanduser().resolve() if jsonl_ev else None
    ev_map = load_audit_evidence_jsonl(jpath)

    correcoes_raw: Dict[str, Any] = {}
    corr_path = _t(getattr(args, "tail_correcoes_json", ""))
    if corr_path:
        correcoes_raw = load_tail_mutirao_correcoes(Path(corr_path).expanduser().resolve())
    elif (MOTORES_ROOT / "metadata" / "sidecars" / "tail_mutirao_correcoes.json").is_file():
        correcoes_raw = load_tail_mutirao_correcoes()

    slice_rows = _load_last_rows(csv_in, args.last)
    enriched: List[Dict[str, Any]] = []
    alert_counter: Counter[str] = Counter()
    block_counter: Counter[str] = Counter()
    manual_review: List[str] = []

    for row in slice_rows:
        st = _t(row.get("status_revisao"))
        arquivo = _t(row.get("arquivo"))
        ak = _audit_norm_arquivo_key(arquivo)
        ev_extra = ev_map.get(ak, "")
        correcao = lookup_correcao(correcoes_raw, arquivo=arquivo) if correcoes_raw else None
        row_eff = apply_correcao_to_row(row, correcao)
        blocking, warns, meta = _collect_alerts_blocking_and_warnings(row_eff, evidence_extra=ev_extra)
        if correcao:
            bypass = correcao.get("force_bypass_alerts") or []
            blocking = filter_alert_codes(list(blocking), bypass)
            warns = filter_alert_codes(list(warns), bypass)
        pipe = _pipeline_status_alerts(row.get("status_revisao") or "")
        all_alerts = _dedupe_ordered(list(blocking) + list(warns) + list(pipe))
        for a in all_alerts:
            alert_counter[a] += 1
        for b in blocking:
            block_counter[b] += 1

        rec = dict(row)
        rec["potencia_cv_original_auditor"] = meta.get("potencia_cv_original_auditor", "")
        rec["potencia_cv_normalizada"] = meta.get("potencia_cv_normalizada", "")
        rec["audit_normalizacao_rastreavel"] = meta.get("audit_normalizacao_rastreavel", "")
        rec["audit_power_trace_note"] = meta.get("audit_power_trace_note", "")
        rec["audit_tipo_motor_sugerido"] = meta.get("audit_tipo_motor_sugerido", "")
        rec["audit_type_trace_note"] = meta.get("audit_type_trace_note", "")
        rec["audit_rpm_original"] = meta.get("audit_rpm_original", "")
        rec["audit_rpm_normalizado"] = meta.get("audit_rpm_normalizado", "")
        rec["audit_rpm_trace_note"] = meta.get("audit_rpm_trace_note", "")
        rec["audit_outlier_mecanico"] = meta.get("audit_outlier_mecanico", "")
        rec["audit_outlier_trace_note"] = meta.get("audit_outlier_trace_note", "")
        rec["diametro_mm_original_auditor"] = meta.get("diametro_mm_original_auditor", "")
        rec["diametro_mm_normalizado"] = meta.get("diametro_mm_normalizado", "")
        rec["espiras_principal_original_auditor"] = meta.get("espiras_principal_original_auditor", "")
        rec["espiras_auxiliar_original_auditor"] = meta.get("espiras_auxiliar_original_auditor", "")
        rec["espiras_principal_normalizada"] = meta.get("espiras_principal_normalizada", "")
        rec["espiras_auxiliar_normalizada"] = meta.get("espiras_auxiliar_normalizada", "")
        rec["audit_espiras_trace_note"] = meta.get("audit_espiras_trace_note", "")
        rec["audit_trace_note"] = meta.get("audit_trace_note", "")
        rec["alertas"] = ";".join(all_alerts)
        rec["alertas_warnings"] = ";".join(warns)
        rec["alertas_criticos"] = ";".join(blocking)
        rec["n_alertas"] = str(len(all_alerts))
        rec["n_alertas_blocking"] = str(len(blocking))
        rec["n_alertas_warnings"] = str(len(warns))
        rec["n_alertas_criticos"] = str(len(blocking))
        enriched.append(
            {
                "row": rec,
                "blocking": blocking,
                "warnings": warns,
                "alerts": all_alerts,
                "status": st,
                "arquivo": arquivo,
            }
        )

        if all_alerts or _status_bucket(st) in {"amarelo", "vermelho"}:
            if arquivo:
                manual_review.append(arquivo)

    manual_review = sorted(set(manual_review))

    verde_sem = verde_com = amarelos = vermelhos = 0
    for item in enriched:
        st = item["status"]
        blocking_codes: List[str] = item.get("blocking") or []
        bucket = _status_bucket(st)
        if bucket == "verde":
            if blocking_codes:
                verde_com += 1
            else:
                verde_sem += 1
        elif bucket == "amarelo":
            amarelos += 1
        elif bucket == "vermelho":
            vermelhos += 1

    total = len(enriched)
    top_alerts = alert_counter.most_common(50)
    top_critical = block_counter.most_common(30)

    summary = {
        "generated_at": _utc_now_iso(),
        "input_csv": str(csv_in),
        "last_n": args.last,
        "total_auditado": total,
        "verdes_sem_alerta": verde_sem,
        "verdes_com_alerta": verde_com,
        "amarelos": amarelos,
        "vermelhos": vermelhos,
        "top_motivos_alerta": [{"codigo": k, "count": v} for k, v in top_alerts],
        "top_alertas_criticos_A": [{"codigo": k, "count": v} for k, v in top_critical],
        "arquivos_revisao_manual": manual_review,
        "saidas": {"csv": str(out_csv), "json": str(out_json), "md": str(out_md)},
    }

    # CSV de saída
    if enriched:
        fieldnames = list(enriched[0]["row"].keys())
    else:
        fieldnames = []

    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for item in enriched:
            w.writerow(item["row"])

    payload = {
        **summary,
        "linhas": [
            {
                "arquivo": x["arquivo"],
                "status_revisao": x["status"],
                "alertas": x["alerts"],
            }
            for x in enriched
        ],
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines: List[str] = []
    md_lines.append(f"# Auditoria extração Gemini (determinística)\n")
    md_lines.append(f"- Gerado: `{summary['generated_at']}`")
    md_lines.append(f"- Entrada: `{csv_in}`")
    md_lines.append(f"- Últimas linhas: **{args.last}**")
    md_lines.append(f"- Total auditado: **{total}**\n")
    md_lines.append("## Resumo\n")
    md_lines.append(f"| Métrica | Valor |")
    md_lines.append(f"|---|---:|")
    md_lines.append(f"| Verdes sem alerta | {verde_sem} |")
    md_lines.append(f"| Verdes com alerta | {verde_com} |")
    md_lines.append(f"| Amarelos | {amarelos} |")
    md_lines.append(f"| Vermelhos | {vermelhos} |")
    md_lines.append("")
    md_lines.append("## Top motivos de alerta (todos os códigos)\n")
    for cod, cnt in top_alerts[:20]:
        md_lines.append(f"- `{cod}`: **{cnt}**")
    md_lines.append("\n## Top alertas críticos (prefixo `A`, heurísticas de campo)\n")
    if top_critical:
        for cod, cnt in top_critical[:20]:
            md_lines.append(f"- `{cod}`: **{cnt}**")
    else:
        md_lines.append("- *(nenhum nos registros auditados)*")
    md_lines.append("\n## Revisão manual sugerida\n")
    md_lines.append("Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:\n")
    for a in manual_review:
        md_lines.append(f"- `{a}`")
    md_lines.append("\n## Saídas\n")
    md_lines.append(f"- CSV: `{out_csv}`")
    md_lines.append(f"- JSON: `{out_json}`")
    out_md.write_text("\n".join(md_lines), encoding="utf-8")

    print("Auditoria concluída.")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Regras de coerência de oficina / rebobinagem (severidade calibrada).

``critico`` só para conflito forte; lacunas → ``insuficiente``; heurística fraca → ``alerta``.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from core.calculadora import mensagem_bobinagem_auxiliar_incompleta


def _has_nums(blob: Dict[str, Any]) -> bool:
    n = blob.get("numbers")
    return bool(n)


def _has_tokens(blob: Dict[str, Any]) -> bool:
    return bool(blob.get("tokens"))


def _electric_ns_rpm(electric_norm: Dict[str, Any]) -> Optional[float]:
    f = electric_norm.get("frequency_hz")
    p = electric_norm.get("poles")
    if f is None or p is None:
        return None
    try:
        return 120.0 * float(f) / float(p)
    except Exception:
        return None


def _detect_ocr_numeric_conflict(raw: Dict[str, Any], electric_norm: Dict[str, Any]) -> bool:
    """Heurística conservadora: muitos RPM candidatos no OCR, nenhum próximo da placa."""
    ocr = str(raw.get("texto_ocr") or "")
    rpm = electric_norm.get("rpm_nominal")
    if len(ocr) < 250 or rpm is None:
        return False
    r = float(rpm)
    nums = [int(m.group(1)) for m in re.finditer(r"\b(1\d{3}|[2-9]\d{3})\b", ocr)]
    if len(nums) < 5:
        return False
    close = [n for n in nums if abs(n - r) <= 100]
    far = [n for n in nums if abs(n - r) > 180]
    return len(close) == 0 and len(far) >= 4


def run_rewinding_validation(
    raw: Dict[str, Any],
    rew_norm: Dict[str, Any],
    electric_norm: Dict[str, Any],
) -> Tuple[Dict[str, Any], float]:
    issues: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    pr = rew_norm.get("principal") or {}
    ax = rew_norm.get("auxiliar") or {}
    pr_p, pr_e, pr_f = pr.get("passos") or {}, pr.get("espiras") or {}, pr.get("fios") or {}
    ax_p, ax_e, ax_f = ax.get("passos") or {}, ax.get("espiras") or {}, ax.get("fios") or {}
    ran = (rew_norm.get("esquema") or {}).get("ranhuras") or {}
    d_mm = (rew_norm.get("mecanica") or {}).get("diametro_mm") or {}
    p_mm = (rew_norm.get("mecanica") or {}).get("pacote_mm") or {}

    # --- Crítico: RPM placa > síncrona (reuso elétrico) ---
    ns = _electric_ns_rpm(electric_norm)
    rpm = electric_norm.get("rpm_nominal")
    if ns is not None and rpm is not None and float(rpm) > ns * 1.002:
        issues.append(
            {
                "code": "rpm_above_sync_rebob",
                "severity": "critico",
                "message": "RPM da placa acima da rotação síncrona estimada — incompatível com indução em rede fixa.",
                "heuristic": True,
            }
        )

    if ran.get("value") is not None and int(ran["value"]) < 0:
        issues.append(
            {
                "code": "ranhuras_invalidas",
                "severity": "critico",
                "message": "Ranhuras negativas ou inválidas.",
                "heuristic": False,
            }
        )

    # --- Principal: passo sem espiras ---
    if _has_nums(pr_p) or _has_tokens(pr_p):
        if not _has_nums(pr_e):
            warnings.append(
                {
                    "code": "principal_passo_sem_espiras",
                    "severity": "alerta",
                    "message": "Há passo(s) principal(is) documentados sem espiras correspondentes — conferir cálculo de oficina.",
                    "heuristic": True,
                }
            )

    # --- Auxiliar (regra já existente do produto, aqui só como alerta de coerência) ---
    bob_raw = raw.get("bobinagem_auxiliar") if isinstance(raw.get("bobinagem_auxiliar"), dict) else {}
    msg_aux = mensagem_bobinagem_auxiliar_incompleta({"bobinagem_auxiliar": bob_raw})
    if msg_aux:
        warnings.append(
            {
                "code": "auxiliar_incompleta",
                "severity": "alerta",
                "message": msg_aux,
                "heuristic": True,
            }
        )

    # --- Passo vs espiras contagem ---
    if _has_nums(pr_p) and _has_nums(pr_e):
        lp, le = len(pr_p["numbers"]), len(pr_e["numbers"])
        if lp > 1 and le > 1 and lp != le:
            warnings.append(
                {
                    "code": "passo_espiras_cardinalidade",
                    "severity": "alerta",
                    "message": f"Quantidade de passos ({lp}) difere da de grupos de espiras ({le}) — pode ser válido, mas merece revisão.",
                    "heuristic": True,
                }
            )

    # --- Geometria pacote / diâmetro ---
    dv, pv = d_mm.get("value_mm"), p_mm.get("value_mm")
    if dv and pv and dv > 0 and pv > 0:
        if pv > dv * 3.5:
            warnings.append(
                {
                    "code": "pacote_vs_diametro",
                    "severity": "alerta",
                    "message": "Pacote muito grande face ao diâmetro informado — verificar unidade (mm) e leitura.",
                    "heuristic": True,
                }
            )

    # --- Ranhuras vs porte (muito grosseiro) ---
    slots = ran.get("value")
    p_kw = electric_norm.get("power_kw")
    if slots is not None and p_kw and float(p_kw) > 40 and int(slots) < 18:
        warnings.append(
            {
                "code": "ranhuras_potencia",
                "severity": "alerta",
                "message": "Ranhuras baixas para potência aparente — possível OCR errado ou motor especial.",
                "heuristic": True,
            }
        )

    # --- OCR conflito leve ---
    if _detect_ocr_numeric_conflict(raw, electric_norm):
        warnings.append(
            {
                "code": "ocr_rpm_ambiguous",
                "severity": "alerta",
                "message": "Texto OCR contém muitos RPM candidatos diferentes da placa — revisão humana recomendada.",
                "heuristic": True,
            }
        )

    # --- Lacunas ---
    has_any = (
        _has_tokens(pr_p)
        or _has_nums(pr_e)
        or _has_tokens(ax_p)
        or ran.get("value") is not None
        or d_mm.get("value_mm")
        or p_mm.get("value_mm")
    )

    richness = sum(
        1
        for x in (
            _has_nums(pr_p),
            _has_nums(pr_e),
            pr_f.get("gauge_token"),
            ran.get("value"),
            d_mm.get("value_mm"),
            p_mm.get("value_mm"),
        )
        if x
    )

    ocr_meta = bool((rew_norm.get("texto") or {}).get("ocr_meta_flag"))
    parse_local = bool(
        pr_p.get("needs_review")
        or pr_e.get("needs_review")
        or pr_f.get("needs_review")
        or ax_p.get("needs_review")
        or ax_e.get("needs_review")
        or ran.get("needs_review")
    )

    needs_human_review = ocr_meta or parse_local or bool(warnings and richness >= 2)

    if issues:
        status = "critico"
    elif not has_any:
        status = "insuficiente"
    elif richness <= 1 and not issues:
        status = "insuficiente"
    elif warnings:
        status = "alerta"
    elif ocr_meta:
        status = "alerta"
    else:
        status = "ok"

    conf = 0.35 + 0.1 * richness
    conf -= 0.18 * len(issues)
    conf -= 0.06 * len(warnings)
    if status == "insuficiente":
        conf = min(conf, 0.55)
    conf = max(0.0, min(1.0, round(conf, 3)))

    val = {
        "status": status,
        "severity_color": {"ok": "green", "alerta": "yellow", "critico": "red", "insuficiente": "gray"}.get(
            status, "gray"
        ),
        "issues": issues,
        "warnings": warnings,
        "needs_human_review": needs_human_review,
        "confidence": conf,
    }
    return val, conf


def build_rewinding_summary_one_liner(validation: Dict[str, Any], rew_norm: Dict[str, Any]) -> str:
    st = validation.get("status")
    if validation.get("issues"):
        return str(validation["issues"][0].get("message") or "")[:140]
    if st == "insuficiente":
        return "Dados de oficina insuficientes (passo, espiras, ranhuras ou dimensões) para validar rebobinagem com força."
    if validation.get("warnings"):
        return str(validation["warnings"][0].get("message") or "")[:140]
    if validation.get("needs_human_review"):
        return "Revisão humana sugerida: leitura OCR ou formato de campo a conferir, sem condenação automática."
    return "Coerência de rebobinagem compatível com o modelo heurístico atual (sempre confirmar em oficina)."


def build_rewinding_summary_full(validation: Dict[str, Any], rew_norm: Dict[str, Any]) -> str:
    one = build_rewinding_summary_one_liner(validation, rew_norm)
    extra: List[str] = []
    for w in (validation.get("warnings") or [])[1:3]:
        extra.append(str(w.get("message") or ""))
    tail = (
        " Limites: sem tabela AWG/mm² nem modelo de ranhura; "
        "não substitui projeto de bobina nem laudo de conformidade."
    )
    return (one + (" " + " ".join(x for x in extra if x)).strip() + tail).strip()

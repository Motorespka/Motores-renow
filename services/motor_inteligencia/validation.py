"""
Motor de validação técnica: comparações entre placa, derivados e heurísticas de indução.

Nunca reprova “automaticamente” por dúvida isolada: conflitos fracos viram ``warnings``
e ``needs_human_review``.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from services.motor_inteligencia.calculations import compute_derived_metrics
from services.motor_inteligencia.normalization import normalize_motor_inteligencia_input


def _ns_value(derived: Dict[str, Any]) -> Optional[float]:
    blk = derived.get("ns_rpm") or {}
    v = blk.get("value")
    return float(v) if isinstance(v, (int, float)) else None


def _rpm_value(normalized: Dict[str, Any]) -> Optional[float]:
    r = normalized.get("rpm_nominal")
    return float(r) if isinstance(r, (int, float)) else None


def _pin_value(derived: Dict[str, Any]) -> Optional[float]:
    blk = derived.get("pin_kw") or {}
    v = blk.get("value")
    return float(v) if isinstance(v, (int, float)) else None


def _pout_value(derived: Dict[str, Any]) -> Optional[float]:
    blk = derived.get("pout_kw") or {}
    v = blk.get("value")
    return float(v) if isinstance(v, (int, float)) else None


def _slip_value(derived: Dict[str, Any]) -> Optional[float]:
    blk = derived.get("slip_percent") or {}
    v = blk.get("value")
    return float(v) if isinstance(v, (int, float)) else None


def _richness_score(normalized: Dict[str, Any]) -> int:
    """Quantos campos-chave estão preenchidos (0–6); usado para separar insuficiente de alarme."""
    n = 0
    if normalized.get("rpm_nominal") is not None:
        n += 1
    if normalized.get("frequency_hz") is not None:
        n += 1
    if normalized.get("poles") is not None:
        n += 1
    if normalized.get("tension_v_primary") is not None:
        n += 1
    if normalized.get("current_a") is not None:
        n += 1
    if normalized.get("power_kw") is not None:
        n += 1
    return n


def run_validation(normalized: Dict[str, Any], derived: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    calculos_concluidos = list(derived.get("calculos_concluidos") or [])
    calculos_impossiveis = list(derived.get("calculos_impossiveis") or [])

    ns = _ns_value(derived)
    rpm = _rpm_value(normalized)
    slip = _slip_value(derived)
    pin = _pin_value(derived)
    pout = _pout_value(derived)
    p_kw = normalized.get("power_kw")
    v = normalized.get("tension_v_primary")
    i = normalized.get("current_a")
    phases = normalized.get("phases") or "unknown"
    fp = normalized.get("power_factor")
    eta = normalized.get("efficiency")

    ocr_or_parser_flag = bool(normalized.get("needs_review"))

    # --- Crítico: RPM acima da síncrona (modelo indução clássico; heurística) ---
    if ns is not None and rpm is not None and rpm > ns * 1.002:
        issues.append(
            {
                "code": "rpm_above_sync",
                "severity": "critico",
                "message": f"RPM nominal ({rpm}) acima da rotação síncrona calculada ({ns:.1f} rpm) — inviável para motor de indução clássico alimentado em frequência fixa.",
                "heuristic": True,
            }
        )

    if slip is not None and slip < -0.5:
        issues.append(
            {
                "code": "negative_slip",
                "severity": "critico",
                "message": f"Escorregamento negativo ({slip:.3f}%) — incompatível com motor de indução em regime comum.",
                "heuristic": True,
            }
        )

    # --- Alerta: polos x frequência x RPM (faixa de escorregamento plausível) ---
    if ns is not None and rpm is not None and 0 < rpm <= ns:
        s = (ns - rpm) / ns * 100.0
        if s > 15:
            warnings.append(
                {
                    "code": "high_slip",
                    "severity": "alerta",
                    "message": f"Escorregamento elevado (~{s:.2f}%) frente ao modelo típico — motor especial, dados de placa ou polos/frequência a rever.",
                    "heuristic": True,
                }
            )
        if s < 0.05 and _richness_score(normalized) >= 4:
            warnings.append(
                {
                    "code": "very_low_slip",
                    "severity": "alerta",
                    "message": "Escorregamento quase nulo — possível motor síncrono, leitura de RPM ou frequência a confirmar.",
                    "heuristic": True,
                }
            )

    # --- Coerência potência x Pin (ordem de grandeza) ---
    if pin is not None and p_kw is not None and p_kw > 0:
        ratio = pin / p_kw if pin >= p_kw else p_kw / pin
        if ratio > 3.2:
            warnings.append(
                {
                    "code": "power_pin_mismatch",
                    "severity": "alerta",
                    "message": (
                        f"Pin estimado ({pin:.3f} kW) distante da potência de placa ({p_kw:.3f} kW) "
                        "— verificar fp, rendimento, tensão de trabalho e fases."
                    ),
                    "heuristic": True,
                }
            )

    # --- Corrente “fora do esperado” (muito grosseiro, só com fp e eta) ---
    if (
        pin is not None
        and p_kw is not None
        and v
        and i
        and fp
        and eta
        and phases == "tri"
    ):
        try:
            i_expected = (p_kw * 1000.0) / (math.sqrt(3) * v * fp * eta)
            if i_expected > 0 and (i / i_expected > 2.2 or i / i_expected < 0.5):
                warnings.append(
                    {
                        "code": "current_band",
                        "severity": "alerta",
                        "message": (
                            f"Corrente informada ({i} A) fora de faixa grosseira vs. estimativa "
                            f"({i_expected:.2f} A) a partir de P, V, fp e rendimento — revisão recomendada."
                        ),
                        "heuristic": True,
                    }
                )
        except Exception:
            pass

    richness = _richness_score(normalized)

    # --- Status agregado (fase 2: menos alarmismo; crítico só com incoerência forte) ---
    if issues:
        status = "critico"
    elif richness <= 2:
        # Poucos campos: tratar como lacuna de dados, não como falha grave
        status = "insuficiente"
    elif not calculos_concluidos:
        # Dados parciais ou não fecham o modelo mínimo (ex.: falta f/polos para ns)
        status = "insuficiente"
    elif warnings:
        status = "alerta"
    elif ocr_or_parser_flag:
        status = "alerta"
    else:
        status = "ok"

    needs_human_review = bool(issues) or bool(warnings) or ocr_or_parser_flag

    confidence = float(normalized.get("confidence_base") or 0.0)
    confidence -= 0.14 * len(issues)
    confidence -= 0.05 * len(warnings)
    if status == "insuficiente" and richness <= 2:
        confidence = min(confidence, 0.55)
    confidence = max(0.0, min(1.0, round(confidence, 3)))

    severity_color = {
        "ok": "green",
        "alerta": "yellow",
        "critico": "red",
        "insuficiente": "gray",
    }.get(status, "gray")

    return {
        "status": status,
        "severity_color": severity_color,
        "issues": issues,
        "warnings": warnings,
        "calculos_concluidos": calculos_concluidos,
        "calculos_impossiveis": calculos_impossiveis,
        "confidence": confidence,
        "needs_human_review": needs_human_review,
    }


def validate_motor(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    API pedida: valida a partir do dicionário bruto (linha Supabase, JSON de oficina, etc.).
    Read-only; não altera ``data``.
    """
    normalized = normalize_motor_inteligencia_input(data)
    derived = compute_derived_metrics(normalized)
    return run_validation(normalized, derived)


def build_summary_one_liner(
    normalized: Dict[str, Any],
    derived: Dict[str, Any],
    validation: Dict[str, Any],
    max_len: int = 118,
) -> str:
    """Uma linha curta para cards (consulta); prioriza mensagem acionável em português."""
    st = str(validation.get("status") or "insuficiente")
    if validation.get("issues"):
        msg = str(validation["issues"][0].get("message") or "")
        if len(msg) > max_len:
            return msg[: max_len - 1].rstrip() + "…"
        return msg
    if st == "insuficiente":
        miss = normalized.get("insufficient_for") or []
        if miss:
            tip = str(miss[0])
            if len(tip) > 52:
                tip = tip[:49].rstrip() + "…"
            base = f"Elétrico incompleto: {tip}."
        else:
            base = "Ficha sem RPM/polos/Hz/tensão suficientes para análise elétrica fechada."
        return (base[: max_len - 1] + "…") if len(base) > max_len else base
    if st == "alerta" and validation.get("warnings"):
        msg = str(validation["warnings"][0].get("message") or "")
        if len(msg) > max_len:
            return msg[: max_len - 1].rstrip() + "…"
        return msg
    if st == "alerta":
        return "Alerta: rever OCR/formato (sem reprovação automática)."

    ns = _ns_value(derived)
    rpm = _rpm_value(normalized)
    poles = normalized.get("poles")
    f_hz = normalized.get("frequency_hz")
    if ns is not None and rpm is not None and poles and f_hz:
        slip = _slip_value(derived)
        slip_txt = f" Escorregamento ~{slip:.1f}%." if slip is not None else ""
        base = (
            f"Motor coerente com {int(poles)} polos / {f_hz:.0f} Hz e rotação próxima da síncrona "
            f"(~{ns:.0f} rpm vs {rpm:.0f} rpm na placa).{slip_txt}"
        )
        return (base[: max_len - 1] + "…") if len(base) > max_len else base.strip()
    return "Parâmetros alinhados com o modelo de indução usado nesta camada, dentro dos limites atuais."


def build_technical_summary(
    normalized: Dict[str, Any],
    derived: Dict[str, Any],
    validation: Dict[str, Any],
) -> str:
    """Resumo mais longo para humanos (painel / export)."""
    one = build_summary_one_liner(normalized, derived, validation, max_len=260)
    extras: List[str] = []
    ns = _ns_value(derived)
    rpm = _rpm_value(normalized)
    if validation.get("issues") and len(validation["issues"]) > 1:
        extras.append(validation["issues"][1].get("message", ""))
    if validation.get("warnings") and len(validation["warnings"]) > 1:
        extras.append(validation["warnings"][1].get("message", ""))
    tail = " Heurística de apoio — não substitui laudo nem projeto de bobina."
    extra_txt = (" " + " ".join(x for x in extras if x)).strip()
    return (one + extra_txt + tail).strip()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoria física WEG/IEC — densidade de corrente (J), fator de enchimento (ff),
saturação magnética (B ≤ 1.5 T) e score de confiança dinâmico.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from engine.winding_sanity import (
    FEM_DEFAULT_FREQUENCY_HZ,
    FEM_DEFAULT_VOLTAGE_V,
    FEM_MAX_FLUX_DENSITY_T,
    FEM_WINDING_FACTOR,
    apply_fem_physics_guard,
    espiras_from_fem_equation,
    estimate_physical_slot_fill_limit,
    slot_fill_ratio,
)

# --- Limites normativos (sobrevivência) ---
B_MAX_TESLA = 1.5
B_ABORT_TESLA = 1.8
J_MIN_A_MM2 = 3.0
J_MAX_A_MM2 = 7.0
J_IDEAL_A_MM2 = 4.0
FF_MIN = 0.25
FF_MAX = 0.45
FF_IDEAL = 0.35

MSG_FF_IMPOSSIVEL = (
    "Cálculo impossível: fator de enchimento ff > 45% — o fio não cabe na ranhura."
)
MSG_FF_SUB = (
    "Subdimensionado: ff < 25% — motor perderá rendimento (cobre insuficiente na ranhura)."
)
MSG_J_INVALIDO = (
    "Densidade de corrente J fora da faixa segura 3–7 A/mm² — cálculo invalidado."
)
MSG_B_SATURACAO = (
    "Risco de saturação magnética: espiras abaixo do mínimo FEM (B > 1.5 T)."
)
MSG_B_ABORT = (
    "Cálculo Abortado: Risco Severo de Saturação. O núcleo excederia 1.8T."
)

# Calibração ff: ocupação relativa 67% → ff nominal 35%
_FF_FROM_FILL_RATIO = FF_IDEAL / 0.67

# 1 CV (Brasil/IEC) ≈ 735,5 W
CV_TO_KW = 0.7355
# Heurística ferro (Ø e L em mm) calibrada ~1,1 kW em 80×70 mm 2p — não superestimar J
_IRON_KW_PER_MM3_SCALE = 0.0000025


@dataclass
class PhysicsAuditResult:
    espiras: float
    awg: float
    parallel_count: int = 1
    fill_factor_ff: float = 0.0
    current_density_j: Optional[float] = None
    flux_density_ok: bool = True
    fem_reference_turns: float = 0.0
    power_estimated_kw: Optional[float] = None
    nominal_current_a: Optional[float] = None
    confidence_score: int = 0
    survival_pass: bool = True
    calculation_aborted: bool = False
    flux_density_b_t: Optional[float] = None
    alerts: list[str] = field(default_factory=list)
    corrections: list[str] = field(default_factory=list)


def is_camada_dupla_context(tipo_bobinagem: str = "", passo: str = "") -> bool:
    """Camada dupla / passos 4-6-8 — faixa de ff um pouco mais ampla na bancada."""
    t = (tipo_bobinagem or "").upper()
    p = re.sub(r"\s+", "", (passo or "").upper())
    if any(k in t for k in ("DUPLA", "DUPLO", "DOUBLE", "CD")):
        return True
    if re.search(r"4[-:./]6[-:./]8|4-6-8|4/6/8", p):
        return True
    if re.search(r"1[:/]4[-:./]6", p):
        return True
    return False


def infer_wire_from_fio(
    fio_raw: str | float | int,
    *,
    tipo_bobinagem: str = "",
) -> tuple[int, float]:
    """Retorna (paralelos, AWG por condutor) a partir do campo fio (ex.: 2x22, 21)."""
    from app.fio_paralelo import parse_wire_config

    cfg = parse_wire_config(str(fio_raw).strip())
    if cfg:
        return max(1, cfg.parallel_count), float(cfg.awg)
    try:
        awg = float(str(fio_raw).replace(",", "."))
    except ValueError:
        awg = 19.0
    return 1, awg


def power_kw_from_cv(cv: float) -> float:
    if cv <= 0:
        return 0.0
    return round(float(cv) * CV_TO_KW, 3)


def resolve_power_and_current(
    *,
    diametro_mm: float,
    pacote_mm: float,
    polos: Optional[int] = None,
    voltage_v: float = FEM_DEFAULT_VOLTAGE_V,
    potencia_cv: Optional[float] = None,
    potencia_kw: Optional[float] = None,
    corrente_nominal_a: Optional[float] = None,
) -> tuple[float, float, bool]:
    """
    (power_kw, current_a, corrente_informada_pelo_usuario)
    Prioridade: corrente direta > CV/kW informados > estimativa pelo ferro.
    """
    user_current = corrente_nominal_a is not None and float(corrente_nominal_a) > 0
    if user_current:
        i_a = round(float(corrente_nominal_a), 3)
        if potencia_kw and float(potencia_kw) > 0:
            p_kw = round(float(potencia_kw), 3)
        elif potencia_cv and float(potencia_cv) > 0:
            p_kw = power_kw_from_cv(float(potencia_cv))
        else:
            p_kw = round(
                (i_a * voltage_v * math.sqrt(3.0) * 0.78 * 0.85) / 1000.0, 3
            )
        return p_kw, i_a, True

    if potencia_kw and float(potencia_kw) > 0:
        p_kw = round(float(potencia_kw), 3)
        return p_kw, nominal_line_current_a(p_kw, voltage_v=voltage_v), False
    if potencia_cv and float(potencia_cv) > 0:
        p_kw = power_kw_from_cv(float(potencia_cv))
        return p_kw, nominal_line_current_a(p_kw, voltage_v=voltage_v), False

    p_kw = estimate_power_from_iron_kw(diametro_mm, pacote_mm, polos)
    return p_kw, nominal_line_current_a(p_kw, voltage_v=voltage_v), False


def estimate_slot_fill_factor_ff(
    espiras: float,
    awg: float,
    *,
    ranhuras: int,
    diametro_mm: float,
    pacote_mm: float,
    parallel_count: int = 1,
    tipo_bobinagem: str = "",
    passo: str = "",
) -> float:
    """ff ≈ cobre na ranhura / área útil (calibrado via slot_fill_ratio do acervo)."""
    if espiras <= 0 or awg <= 0 or ranhuras <= 0:
        return 0.0
    limit = estimate_physical_slot_fill_limit(ranhuras, diametro_mm, pacote_mm)
    if limit <= 0:
        return 0.0
    eq_awg = awg
    ratio = slot_fill_ratio(espiras, eq_awg, limit)
    if is_camada_dupla_context(tipo_bobinagem, passo):
        ratio = ratio * 1.85
    if parallel_count > 1:
        ratio = ratio * min(parallel_count, 3)
    return round(min(1.0, ratio * _FF_FROM_FILL_RATIO), 4)


def estimate_power_from_iron_kw(
    diametro_mm: float,
    pacote_mm: float,
    polos: Optional[int] = None,
) -> float:
    """
    Potência inferida pelo volume de ferro (caixa preta, sem placa).
    Heurística IEC/WEG: kW ≈ 0.00085 × (Ø_mm)² × L_mm × fator_polos.
    """
    d = max(float(diametro_mm), 1.0)
    l = max(float(pacote_mm), 1.0)
    p = int(polos) if polos and polos >= 2 else 4
    pole_factor = 1.0 if p == 2 else (1.15 if p == 4 else 1.25)
    kw = _IRON_KW_PER_MM3_SCALE * (d**2) * l * pole_factor
    return round(max(0.15, min(kw, 75.0)), 3)


def nominal_line_current_a(
    power_kw: float,
    *,
    voltage_v: float = FEM_DEFAULT_VOLTAGE_V,
    efficiency: float = 0.78,
    power_factor: float = 0.85,
    phases: int = 3,
) -> float:
    """Corrente de linha nominal estimada (trifásico por padrão)."""
    if power_kw <= 0 or voltage_v <= 0:
        return 0.0
    p_w = power_kw * 1000.0
    denom = efficiency * power_factor
    if phases >= 3:
        denom *= math.sqrt(3.0) * voltage_v
    else:
        denom *= voltage_v
    if denom <= 0:
        return 0.0
    return round(p_w / denom, 3)


def current_density_a_per_mm2(
    current_a: float,
    awg: int | float,
    *,
    parallel_count: int = 1,
) -> Optional[float]:
    from services.motor_rebobinagem.wire_gauge import awg_integer_to_mm2

    awg_i = int(round(float(awg)))
    area = awg_integer_to_mm2(awg_i)
    if not area or area <= 0:
        return None
    total_area = area * max(1, int(parallel_count))
    if total_area <= 0:
        return None
    return round(current_a / total_area, 3)


def espiras_weg_fem(
    *,
    voltage_v: float = FEM_DEFAULT_VOLTAGE_V,
    flux_wb: Optional[float] = None,
    diametro_mm: float = 80.0,
    pacote_mm: float = 70.0,
    polos: int = 2,
    frequencia_hz: float = FEM_DEFAULT_FREQUENCY_HZ,
    xi: float = FEM_WINDING_FACTOR,
    k_stack: float = 0.95,
    k1: float = 1.0,
    k2: float = 1.0,
) -> float:
    """
    Z_f = 50·V / (2.22·Φ·f·ξ·(k·k1)/k2)  — forma WEG/IEC.
    Se Φ não informado, deriva de B=1.5 T e área de ferro do polo.
    """
    if flux_wb is not None and flux_wb > 0:
        denom = 2.22 * flux_wb * frequencia_hz * xi * (k_stack * k1) / max(k2, 1e-6)
        if denom <= 0:
            return 0.0
        z = (50.0 * voltage_v) / denom
        p = int(polos) if polos and polos >= 2 else 2
        if p > 2:
            z *= (2.0 / float(p)) ** 0.72
        return round(z, 1)
    # Sem Φ medido: equivalente calibrado à FEM 4.44 (mesmo B=1,5 T e ferro)
    return espiras_from_fem_equation(
        diametro_mm,
        pacote_mm,
        polos,
        tensao_fase_v=voltage_v,
        frequencia_hz=frequencia_hz,
        flux_density_t=B_MAX_TESLA,
        winding_factor=xi,
    )


def estimate_operating_flux_density_t(
    espiras: float,
    diametro_mm: float,
    pacote_mm: float,
    polos: Optional[int],
    *,
    voltage_v: float = FEM_DEFAULT_VOLTAGE_V,
    b_design_t: float = FEM_MAX_FLUX_DENSITY_T,
) -> float:
    """
    Estima B operacional (T) a partir da razão espiras reais vs FEM de referência.
    N ∝ 1/B  →  B ≈ B_design × (N_ref / N_actual).
    """
    esp = float(espiras)
    if esp <= 0:
        return float("inf")
    n_ref = espiras_from_fem_equation(
        diametro_mm, pacote_mm, polos, tensao_fase_v=voltage_v, flux_density_t=b_design_t
    )
    if n_ref <= 0:
        return float("inf")
    return round(b_design_t * (n_ref / esp), 3)


def check_extreme_saturation_abort(
    espiras: float,
    diametro_mm: float,
    pacote_mm: float,
    polos: Optional[int],
    *,
    voltage_v: float = FEM_DEFAULT_VOLTAGE_V,
) -> tuple[bool, float, str]:
    """Trava de física extrema (auditoria): B > 1.8 T → abortar sem exceção."""
    b_t = estimate_operating_flux_density_t(
        espiras, diametro_mm, pacote_mm, polos, voltage_v=voltage_v
    )
    if b_t > B_ABORT_TESLA:
        return True, b_t, MSG_B_ABORT
    return False, b_t, ""


def audit_auditoria_user_winding(
    *,
    espiras: float,
    awg: float,
    diametro_mm: float,
    pacote_mm: float,
    ranhuras: int,
    polos: Optional[int] = None,
    carcaca: str = "",
    parallel_count: int = 1,
    voltage_v: float = FEM_DEFAULT_VOLTAGE_V,
    corrente_nominal_a: Optional[float] = None,
    potencia_cv: Optional[float] = None,
    potencia_kw: Optional[float] = None,
    tipo_bobinagem: str = "",
    passo: str = "",
) -> PhysicsAuditResult:
    """
    Avalia o cálculo informado pelo usuário (espiras originais, sem guarda FEM).
    Se B > 1.8 T: confiança 0%, relatório seguro, sem quebrar pipeline.
    """
    esp_raw = round(float(espiras), 1)
    aborted, b_t, msg = check_extreme_saturation_abort(
        esp_raw, diametro_mm, pacote_mm, polos, voltage_v=voltage_v
    )
    if aborted:
        return PhysicsAuditResult(
            espiras=esp_raw,
            awg=float(awg),
            parallel_count=parallel_count,
            fill_factor_ff=0.0,
            current_density_j=None,
            flux_density_ok=False,
            fem_reference_turns=round(
                espiras_from_fem_equation(diametro_mm, pacote_mm, polos) or 0, 1
            ),
            confidence_score=0,
            survival_pass=False,
            calculation_aborted=True,
            flux_density_b_t=b_t,
            alerts=[msg],
        )
    return audit_winding_physics(
        espiras=esp_raw,
        awg=awg,
        diametro_mm=diametro_mm,
        pacote_mm=pacote_mm,
        ranhuras=ranhuras,
        polos=polos,
        carcaca=carcaca,
        parallel_count=parallel_count,
        voltage_v=voltage_v,
        corrente_nominal_a=corrente_nominal_a,
        potencia_cv=potencia_cv,
        power_kw=potencia_kw,
        tipo_bobinagem=tipo_bobinagem,
        passo=passo,
        apply_fem_turns_guard=False,
    )


def physics_confidence_score(
    *,
    j_a_mm2: Optional[float],
    ff: float,
    flux_ok: bool,
    survival_pass: bool,
) -> int:
    """
    100% apenas se J ≈ 4 A/mm², ff ≈ 35% e B dentro do limite.
    Cálculos suspeitos recebem nota baixa com penalidades graduais.
    """
    if not survival_pass:
        return 0
    score = 100
    if j_a_mm2 is not None:
        dev_j = abs(j_a_mm2 - J_IDEAL_A_MM2)
        score -= int(min(55, dev_j * 12))
        if j_a_mm2 < J_MIN_A_MM2 or j_a_mm2 > J_MAX_A_MM2:
            score -= 35
    dev_ff = abs(ff - FF_IDEAL)
    score -= int(min(40, dev_ff * 120))
    if ff > FF_MAX or (ff > 0 and ff < FF_MIN):
        score -= 30
    if not flux_ok:
        score -= 40
    return max(0, min(100, score))


def audit_winding_physics(
    *,
    espiras: float,
    awg: float,
    diametro_mm: float,
    pacote_mm: float,
    ranhuras: int,
    polos: Optional[int] = None,
    carcaca: str = "",
    parallel_count: int = 1,
    voltage_v: float = FEM_DEFAULT_VOLTAGE_V,
    power_kw: Optional[float] = None,
    corrente_nominal_a: Optional[float] = None,
    potencia_cv: Optional[float] = None,
    ligacao: str = "",
    tipo_bobinagem: str = "",
    passo: str = "",
    apply_fem_turns_guard: bool = True,
) -> PhysicsAuditResult:
    """Filtros de sobrevivência + score para modo auditoria ou candidatos."""
    alerts: list[str] = []
    corrections: list[str] = []
    esp = round(float(espiras), 1)
    awg_f = float(awg)

    b_t = estimate_operating_flux_density_t(
        esp, diametro_mm, pacote_mm, polos, voltage_v=voltage_v
    )
    if b_t > B_ABORT_TESLA:
        return PhysicsAuditResult(
            espiras=esp,
            awg=awg_f,
            parallel_count=parallel_count,
            confidence_score=0,
            survival_pass=False,
            calculation_aborted=True,
            flux_density_b_t=b_t,
            flux_density_ok=False,
            fem_reference_turns=round(
                espiras_from_fem_equation(diametro_mm, pacote_mm, polos) or 0, 1
            ),
            alerts=[MSG_B_ABORT],
        )

    fem_ref = 0.0
    if apply_fem_turns_guard:
        esp_guard, fem_ref, fem_msgs = apply_fem_physics_guard(
            esp,
            diametro_mm=diametro_mm,
            pacote_mm=pacote_mm,
            polos=polos,
            ranhuras=ranhuras,
            carcaca=carcaca,
            tensao_fase_v=voltage_v,
        )
        if esp_guard != esp:
            corrections.extend(fem_msgs)
            esp = esp_guard
            b_t = estimate_operating_flux_density_t(
                esp, diametro_mm, pacote_mm, polos, voltage_v=voltage_v
            )
    else:
        fem_ref = espiras_from_fem_equation(diametro_mm, pacote_mm, polos)

    fem_alt = espiras_from_fem_equation(diametro_mm, pacote_mm, polos)
    flux_ok = fem_ref <= 0 or esp >= fem_ref * 0.82 if fem_ref else b_t <= B_MAX_TESLA * 1.05
    if not flux_ok:
        alerts.append(MSG_B_SATURACAO)

    camada_dupla = is_camada_dupla_context(tipo_bobinagem, passo)
    ff_max = 0.52 if camada_dupla else FF_MAX
    ff_min = 0.20 if camada_dupla else FF_MIN

    ff = estimate_slot_fill_factor_ff(
        esp,
        awg_f,
        ranhuras=ranhuras,
        diametro_mm=diametro_mm,
        pacote_mm=pacote_mm,
        parallel_count=parallel_count,
        tipo_bobinagem=tipo_bobinagem,
        passo=passo,
    )
    if ff > ff_max:
        alerts.append(MSG_FF_IMPOSSIVEL)
    elif 0 < ff < ff_min:
        alerts.append(MSG_FF_SUB)

    p_kw, i_nom, user_i = resolve_power_and_current(
        diametro_mm=diametro_mm,
        pacote_mm=pacote_mm,
        polos=polos,
        voltage_v=voltage_v,
        potencia_cv=potencia_cv,
        potencia_kw=power_kw,
        corrente_nominal_a=corrente_nominal_a,
    )
    j_val = current_density_a_per_mm2(i_nom, awg_f, parallel_count=parallel_count)
    if j_val is not None and (j_val < J_MIN_A_MM2 or j_val > J_MAX_A_MM2):
        if user_i:
            alerts.append(
                f"Aviso: J≈{j_val} A/mm² fora da faixa típica 3–7 (corrente nominal informada: {i_nom} A)."
            )
        else:
            alerts.append(MSG_J_INVALIDO)

    survival = not any(
        a.startswith("Cálculo impossível")
        or ("invalidado" in a and not user_i)
        for a in alerts
    )
    score = physics_confidence_score(
        j_a_mm2=j_val, ff=ff, flux_ok=flux_ok, survival_pass=survival
    )

    return PhysicsAuditResult(
        espiras=esp,
        awg=awg_f,
        parallel_count=parallel_count,
        fill_factor_ff=ff,
        current_density_j=j_val,
        flux_density_ok=flux_ok,
        fem_reference_turns=round(fem_ref or fem_alt, 1),
        power_estimated_kw=p_kw,
        nominal_current_a=i_nom,
        confidence_score=score,
        survival_pass=survival,
        calculation_aborted=False,
        flux_density_b_t=b_t,
        alerts=alerts,
        corrections=corrections,
    )


def check_required_inputs(
    entrada: dict[str, Any],
    *,
    modo: str,
) -> tuple[bool, list[str]]:
    """Checklist de dados vitais — trava relatório se incompleto."""
    missing: list[str] = []
    d = entrada.get("diametro_mm") or entrada.get("diametro")
    p = entrada.get("pacote_mm") or entrada.get("pacote")
    if not d or float(d) <= 0:
        missing.append("Diâmetro interno do estator (mm) — medir com paquímetro ou régua na foto")
    if not p or float(p) <= 0:
        missing.append("Comprimento do pacote de ferro (mm)")
    ran = entrada.get("ranhuras")
    if not ran or int(ran) <= 0:
        if modo == "caixa_preta":
            missing.append(
                "Número de ranhuras — contar na foto ou confirmar após visão computacional"
            )
        else:
            missing.append("Número de ranhuras do estator")
    if not entrada.get("tensao_v") and not entrada.get("voltagem"):
        missing.append("Tensão de rede (V) — padrão 220 V trifásico se não informado")
    if modo == "auditoria":
        if not entrada.get("espiras_engenheiro") and not entrada.get("espiras"):
            missing.append("Espiras do cálculo suspeito a auditar")
        if not entrada.get("fio_engenheiro") and not entrada.get("fio_awg"):
            missing.append("Bitola AWG do cálculo suspeito")
    return len(missing) == 0, missing

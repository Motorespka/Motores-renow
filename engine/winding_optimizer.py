#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de Projetos de Bobinagem (Winding Optimizer).

Gera três cenários determinísticos com base em:
- Fórmula proporcional (verificação)
- Fator de ocupação de ranhura (limite 75% no cenário A)
- Proxy de densidade de fluxo magnético
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from app.fio_paralelo import (
    WireConfig,
    equivalent_single_awg,
    format_wire_suggestion,
    parallel_from_single_awg,
    wire_display_options,
)
from app.oficial_engine import (
    HIST_DIVERGENCE_REVISAR_PCT,
    CalculationSuggestion,
    filter_file,
    suggest_calculation,
    validate_required_motor_inputs,
)
from app.topologia_bobinagem import (
    TipoInferencia,
    infer_tipo_from_referencias,
    label_tipo,
    norm_tipo_bobinagem,
    usuario_informou_tipo,
)
from app.search_lib import MotorRow, awg_to_mm2, norm_carcaca, passo_canonical, passo_exact_match, slot_fill_units
from engine.outlier_filter import (
    robust_historical_median,
    should_exclude_cadastro_pollution_80_90,
    should_exclude_motor_row_pollution,
)
from engine.physics_audit import (
    FF_MAX,
    MSG_FF_IMPOSSIVEL,
    select_awg_for_ff_cap,
    scenario_passes_hard_physics_limits,
)
from engine.winding_sanity import (
    ALERT_ESPIRAS_BAIXAS,
    ALERT_POLARIDADE,
    CALIBRE_INVALIDO,
    COMMERCIAL_BOBINAGEM_AWGS,
    HIST_BIAS_MAX_DEVIATION,
    MSG_AWG_COMERCIAL,
    MSG_CENARIO_A_INVALIDO,
    MSG_ESTIMATIVA_TECNICA_FORCADA,
    MSG_BUSSOLA_DIVERGENTE,
    MSG_FEM_VETO_TURNS,
    apply_commercial_awg_preserve_copper,
    awg_for_fill_with_limits,
    awg_table_index,
    busola_historica_inconsistente,
    clamp_awg_to_safe_range,
    enforce_fem_turns_veto,
    espiras_from_fem_equation,
    is_awg_in_range,
    nearest_awg_from_table,
    polarity_sanity_alert,
    proportional_vs_hist_alert,
    resolve_slot_fill_limit,
    scenario_a_is_acceptable,
    select_awg_for_slot_fill,
    should_alert_low_turns,
    slot_fill_ratio,
    stator_volume_mm3,
    tune_slot_occupation_band,
)

MAX_SLOT_OCCUPATION = 0.75
ALERT_SATURACAO = "Risco de Saturação Magnética"
ALERT_OCUPACAO = "Dificuldade de Ocupação"
ALERT_DESVIO_HIST = "Atenção: Desvio significativo da média histórica"


@dataclass
class StatorInput:
    diametro_mm: float
    pacote_mm: float
    ranhuras: int
    polos: Optional[int] = None
    carcaca: str = ""
    passo: str = ""
    tipo_bobinagem: str = ""
    ligacao: str = ""
    espiras_validacao_usuario: Optional[float] = None
    fio_validacao_usuario_awg: Optional[float] = None


@dataclass
class WindingScenario:
    cenario_id: str
    titulo: str
    descricao: str
    espiras: float
    wire: WireConfig
    fio_texto: str
    fator_ocupacao_ranhura: float
    densidade_fluxo_indice: float
    confidence_score: int
    alertas: list[str] = field(default_factory=list)
    desvio_historico_pct: Optional[float] = None
    desvio_proporcional_pct: Optional[float] = None
    espiras_proporcional_ref: Optional[float] = None
    espiras_busola_ref: Optional[float] = None
    slot_fill_units: Optional[float] = None
    slot_fill_limite: Optional[float] = None
    fio_alternativa_paralelo: str = ""
    calibre_display: str = ""
    desabilitado: bool = False
    cenario_principal: bool = False
    fill_factor_ff: Optional[float] = None
    current_density_j: Optional[float] = None
    physics_confidence: Optional[int] = None
    reprovado_fisicamente: bool = False


@dataclass
class WindingOptimizationResult:
    entrada: dict[str, Any]
    cenarios: list[WindingScenario]
    calculo_baseado_em: str = ""
    media_historica_espiras: Optional[float] = None
    media_proporcional_espiras: Optional[float] = None
    slot_fill_limite: Optional[float] = None
    n_referencias: int = 0
    validation_status: str = ""
    validation_message: str = ""
    modo_sobrevivencia: bool = False
    is_estimativa: bool = False
    forcar_gemini: bool = False
    base_suggestion: Optional[dict[str, Any]] = None
    cenario_recomendado: str = "B"
    tipo_inferido: str = ""
    tipo_inferido_label: str = ""
    explicacao_tipo: str = ""
    tipo_foi_inferido: bool = False
    media_historica_limpa: Optional[float] = None
    n_outliers_removidos: int = 0
    cenario_a_suprimido: bool = False
    usa_validacao_usuario: bool = False
    busola_historica_inconsistente: bool = False
    espiras_validacao_usuario: Optional[float] = None
    magnetic_sanity_gate_active: bool = False
    volume_estator_mm3: float = 0.0
    n_removed_pollution: int = 0
    gemini_topologia_camada1: bool = False
    candidate_pool: list[dict[str, Any]] = field(default_factory=list)
    gemini_evaluation: dict[str, Any] = field(default_factory=dict)
    neuro_symbolic_active: bool = False


def _awg_area_mm2(awg: float) -> float:
    from engine.physics_validator import PhysicsValidator

    return PhysicsValidator.calculate_wire_area(awg)


def _raw_adjacent_combinations(
    stator: StatorInput,
    *,
    esp_ref: float,
    awg_base: float,
    min_candidates: int = 5,
    max_candidates: int = 8,
) -> list[tuple[float, float, int]]:
    """Combinações brutas AWG ±2 e espiras proporcionais — sem filtros físicos."""
    esp_base = max(float(esp_ref), 1.0)
    awg0, _, _ = clamp_awg_to_safe_range(float(awg_base), stator.carcaca)
    area0 = _awg_area_mm2(awg0)
    combos: list[tuple[float, float, int]] = []
    seen: set[tuple[float, float, int]] = set()

    def _add(esp: float, awg: float, par: int = 1) -> None:
        if len(combos) >= max_candidates:
            return
        awg_safe, _, _ = clamp_awg_to_safe_range(float(awg), stator.carcaca)
        esp_safe = max(round(float(esp), 1), 1.0)
        key = (esp_safe, round(awg_safe, 1), int(par))
        if key in seen:
            return
        seen.add(key)
        combos.append(key)

    for delta in (-2, -1, 0, 1, 2):
        awg, _, _ = clamp_awg_to_safe_range(awg0 + delta, stator.carcaca)
        area = _awg_area_mm2(awg)
        esp = round(esp_base * (area0 / area), 1) if area0 > 0 and area > 0 else esp_base
        _add(esp, awg, 1)

    _add(esp_base + 2.0, awg0 + 1, 1)
    _add(esp_base - 2.0, awg0 - 1, 1)
    _add(esp_base, awg0, 2)

    pad_i = 0
    while len(combos) < min_candidates and pad_i < 24:
        delta_awg = (pad_i % 5) - 2
        delta_esp = (pad_i % 7) - 3
        _add(esp_base + delta_esp, awg0 + delta_awg, 1)
        pad_i += 1

    if not combos:
        _add(esp_base, awg0, 1)

    return combos[:max_candidates]


def _audit_soft_nominal_wire_and_packaging(*, eq_awg: float, ff: Optional[float], j_a_mm2: Optional[float]) -> dict[str, Any]:
    """
    Restrições suaves / referências teóricas — apenas auditoria textual.
    d_w_mm: progressão IEC-style d = 0,127 × 92^((36−AWG)/39) mm (inteiro mais próximo de eq_awg).
    """
    awg_round = int(round(max(1.0, min(40.0, float(eq_awg)))))
    dw = 0.127 * (92 ** ((36 - awg_round) / 39))
    ff_sq = math.pi / 4.0
    ff_hex = math.pi / (2.0 * math.sqrt(3.0))
    soft_audit_messages: list[str] = []
    warn_ff = False
    warn_j = False
    if ff is not None:
        fv = float(ff)
        if fv > 1.0:
            fv = fv / 100.0
        if fv > 0.75:
            warn_ff = True
            soft_audit_messages.append(
                f"Auditoria suave: ff operacional ≈ {fv:.3f} > 0,75 "
                "(empacotamento prático severo segundo referência de engenharia)."
            )
    if j_a_mm2 is not None and float(j_a_mm2) > 8.0:
        warn_j = True
        soft_audit_messages.append(
            f"Auditoria suave: J = {float(j_a_mm2):.2f} A/mm² > 8,0 "
            "(risco térmico severo)."
        )
    return {
        "d_w_mm_nominal_formula": round(dw, 4),
        "awg_round_for_dw": awg_round,
        "ff_packaging_square_theory": round(ff_sq, 6),
        "ff_packaging_hex_theory": round(ff_hex, 6),
        "warn_ff_above_075": warn_ff,
        "warn_j_above_8": warn_j,
        "soft_audit_messages": soft_audit_messages,
    }


def _minimal_scored_candidate(
    stator: StatorInput,
    *,
    espiras: float,
    awg: float,
    parallel_count: int = 1,
) -> dict[str, Any]:
    """Stub bruto quando o motor de auditoria falha — mantém o pool vivo."""
    wire = WireConfig(
        parallel_count=max(1, int(parallel_count)),
        awg=round(float(awg), 1),
    )
    esp = max(round(float(espiras), 1), 1.0)
    return {
        "espiras": esp,
        "awg": round(float(awg), 1),
        "parallel_count": wire.parallel_count,
        "wire": wire,
        "fio_texto": format_wire_suggestion(esp, wire),
        "j_a_mm2": None,
        "ff": None,
        "b_tesla": None,
        "physics_confidence": 0,
        "violations": [],
        "aprovado_fisica": False,
        "reprovado_fisicamente": True,
        "calculation_aborted": False,
        "audit_soft": _audit_soft_nominal_wire_and_packaging(
            eq_awg=float(awg),
            ff=None,
            j_a_mm2=None,
        ),
    }


def _evaluate_inference_candidate(
    stator: StatorInput,
    *,
    espiras: float,
    awg: float,
    parallel_count: int = 1,
    apply_fem_turns_guard: bool = True,
) -> dict[str, Any]:
    """Calcula J, ff e B via PhysicsValidator — registra violações, nunca descarta."""
    from engine.physics_audit import audit_winding_physics, compute_slot_occupation_ratio
    from engine.physics_validator import PhysicsValidatorEngine

    try:
        wire = WireConfig(
            parallel_count=max(1, int(parallel_count)),
            awg=round(float(awg), 1),
        )
        eq_awg = equivalent_single_awg(wire)
        phys = audit_winding_physics(
            espiras=espiras,
            awg=eq_awg,
            diametro_mm=stator.diametro_mm,
            pacote_mm=stator.pacote_mm,
            ranhuras=stator.ranhuras,
            polos=stator.polos,
            carcaca=stator.carcaca,
            parallel_count=wire.parallel_count,
            tipo_bobinagem=stator.tipo_bobinagem,
            passo=stator.passo,
            apply_fem_turns_guard=apply_fem_turns_guard,
        )
        esp_final = round(float(phys.espiras), 1)
        ff = compute_slot_occupation_ratio(
            esp_final,
            eq_awg,
            ranhuras=stator.ranhuras,
            diametro_mm=stator.diametro_mm,
            pacote_mm=stator.pacote_mm,
            parallel_count=wire.parallel_count,
            tipo_bobinagem=stator.tipo_bobinagem,
            passo=stator.passo,
        )
        verdict = PhysicsValidatorEngine.validate_scenario_render(
            espiras=esp_final,
            awg=eq_awg,
            parallel_count=wire.parallel_count,
            fill_factor_ff=ff,
            current_density_j=phys.current_density_j,
            b_tesla=phys.flux_density_b_t,
            validate_j=True,
        )
        audit_soft = _audit_soft_nominal_wire_and_packaging(
            eq_awg=float(eq_awg),
            ff=ff,
            j_a_mm2=phys.current_density_j,
        )
        return {
            "espiras": esp_final,
            "awg": round(float(eq_awg), 1),
            "parallel_count": wire.parallel_count,
            "wire": wire,
            "fio_texto": format_wire_suggestion(esp_final, wire),
            "j_a_mm2": phys.current_density_j,
            "ff": ff,
            "b_tesla": phys.flux_density_b_t,
            "physics_confidence": int(phys.confidence_score),
            "violations": list(verdict.mensagens),
            "aprovado_fisica": bool(verdict.aprovado),
            "reprovado_fisicamente": bool(verdict.reprovado_fisicamente),
            "calculation_aborted": bool(phys.calculation_aborted),
            "audit_soft": audit_soft,
        }
    except Exception:
        return _minimal_scored_candidate(
            stator,
            espiras=espiras,
            awg=awg,
            parallel_count=parallel_count,
        )


def generate_inference_candidate_pool(
    stator: StatorInput,
    *,
    esp_ref: float,
    awg_base: float,
    apply_fem_turns_guard: bool = True,
    min_candidates: int = 5,
    max_candidates: int = 8,
) -> list[dict[str, Any]]:
    """
    Etapa 1 — Gerador burro: 5–8 combinações adjacentes.
    Métricas J/ff/B são anexadas; NENHUM candidato é descartado por limite físico.
    """
    del apply_fem_turns_guard  # geração bruta sempre sem veto FEM interno
    combos = _raw_adjacent_combinations(
        stator,
        esp_ref=esp_ref,
        awg_base=awg_base,
        min_candidates=min_candidates,
        max_candidates=max_candidates,
    )
    pool: list[dict[str, Any]] = []
    for idx, (esp, awg, par) in enumerate(combos):
        scored = _evaluate_inference_candidate(
            stator,
            espiras=esp,
            awg=awg,
            parallel_count=par,
            apply_fem_turns_guard=False,
        )
        scored["index"] = idx
        pool.append(scored)

    if not pool:
        stub = _minimal_scored_candidate(
            stator,
            espiras=max(float(esp_ref), 1.0),
            awg=float(awg_base),
        )
        stub["index"] = 0
        pool.append(stub)

    return pool[:max_candidates]


def run_neuro_symbolic_selection(
    stator: StatorInput,
    *,
    entrada: dict[str, Any],
    esp_ref: float,
    awg_base: float,
    apply_fem_turns_guard: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any], Optional[dict[str, Any]]]:
    """
    Pipeline completo: pool determinístico + juiz Gemini (fallback J/ff).
    Retorna (pool, evaluation, best_candidate_or_none).
    """
    from services.gemini_evaluator import evaluate_candidate_pool_with_gemini, resolve_best_candidate

    pool = generate_inference_candidate_pool(
        stator,
        esp_ref=esp_ref,
        awg_base=awg_base,
        apply_fem_turns_guard=apply_fem_turns_guard,
    )

    stator_info = {
        **entrada,
        "espiras_referencia_fem": esp_ref,
        "awg_base_acervo": awg_base,
    }
    try:
        evaluation = evaluate_candidate_pool_with_gemini(pool, stator_info)
    except Exception as exc:
        from services.gemini_evaluator import deterministic_candidate_fallback

        evaluation = deterministic_candidate_fallback(
            pool,
            reason=f"Juiz IA indisponível ({type(exc).__name__}).",
        )
    evaluation, best = resolve_best_candidate(pool, evaluation)
    return pool, evaluation, best


def _candidate_pool_for_storage(pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored: list[dict[str, Any]] = []
    for row in pool:
        item = {k: v for k, v in row.items() if k != "wire"}
        stored.append(item)
    return stored


def _flux_density_index(
    espiras: float, diametro_mm: float, pacote_mm: float, polos: Optional[int]
) -> float:
    """Proxy adimensional: menos espiras no mesmo ferro => maior risco de saturação."""
    p = polos if polos and polos > 0 else 4
    denom = max(diametro_mm * pacote_mm * max(p, 2), 1.0)
    return round(espiras / denom, 6)


def _slot_occupation_ratio(fill_units: float, limit_units: Optional[float]) -> float:
    if not limit_units or limit_units <= 0:
        return round(fill_units, 4)
    return round(fill_units / limit_units, 4)


def _hist_deviation_pct(espiras: float, media_hist: Optional[float]) -> Optional[float]:
    if not media_hist or media_hist <= 0:
        return None
    return round(abs(espiras - media_hist) / media_hist, 4)


def _prop_deviation_pct(espiras: float, media_prop: Optional[float]) -> Optional[float]:
    if not media_prop or media_prop <= 0:
        return None
    return round(abs(espiras - media_prop) / media_prop, 4)


def _confidence_score(
    *,
    espiras: float,
    media_prop: Optional[float],
    media_hist: Optional[float],
    fill_ratio: float,
    flux_index: float,
    flux_ref: float,
    n_refs: int,
    is_estimativa: bool = False,
) -> tuple[int, list[str]]:
    score = 92
    alertas: list[str] = []

    if fill_ratio > MAX_SLOT_OCCUPATION:
        score -= 48
        alertas.append(ALERT_OCUPACAO)
    elif fill_ratio > MAX_SLOT_OCCUPATION * 0.95:
        score -= 18

    if media_prop and media_prop > 0 and espiras < media_prop * 0.90:
        score -= 42
        if ALERT_SATURACAO not in alertas:
            alertas.append(ALERT_SATURACAO)
    elif flux_ref > 0 and flux_index > flux_ref * 1.12:
        score -= 35
        if ALERT_SATURACAO not in alertas:
            alertas.append(ALERT_SATURACAO)

    if fill_ratio < 0.35 and fill_ratio > 0:
        score -= 15

    desvio = _hist_deviation_pct(espiras, media_hist)
    if desvio is not None and desvio > HIST_DIVERGENCE_REVISAR_PCT:
        score -= 22
        if ALERT_DESVIO_HIST not in alertas:
            alertas.append(ALERT_DESVIO_HIST)

    if n_refs < 3 and not is_estimativa:
        score -= 12
    elif is_estimativa and n_refs >= 3:
        score -= 5
    if n_refs == 0:
        score = min(score, 35)

    return max(0, min(100, score)), alertas


def _build_scenario(
    *,
    cenario_id: str,
    titulo: str,
    descricao: str,
    espiras: float,
    wire: WireConfig,
    media_prop: Optional[float],
    media_hist: Optional[float],
    slot_limit: Optional[float],
    flux_ref: float,
    stator: StatorInput,
    n_refs: int,
    fio_alternativa_paralelo: str = "",
    is_estimativa: bool = False,
    calibre_display: str = "",
    desabilitado: bool = False,
    cenario_principal: bool = False,
    apply_fem_turns_guard: bool = True,
) -> WindingScenario:
    eq_awg = equivalent_single_awg(wire)
    fill_u = slot_fill_units(espiras, eq_awg)
    fill_ratio = _slot_occupation_ratio(fill_u, slot_limit)
    flux_idx = _flux_density_index(espiras, stator.diametro_mm, stator.pacote_mm, stator.polos)
    from engine.physics_audit import audit_winding_physics

    phys = audit_winding_physics(
        espiras=espiras,
        awg=eq_awg,
        diametro_mm=stator.diametro_mm,
        pacote_mm=stator.pacote_mm,
        ranhuras=stator.ranhuras,
        polos=stator.polos,
        carcaca=stator.carcaca,
        parallel_count=wire.parallel_count,
        tipo_bobinagem=stator.tipo_bobinagem,
        passo=stator.passo,
        apply_fem_turns_guard=apply_fem_turns_guard,
    )
    esp_final = round(float(phys.espiras), 1)
    if phys.calculation_aborted:
        desabilitado = True
    if esp_final != round(float(espiras), 1):
        espiras = esp_final
        fill_u = slot_fill_units(espiras, eq_awg)
        fill_ratio = _slot_occupation_ratio(fill_u, slot_limit)
        flux_idx = _flux_density_index(
            espiras, stator.diametro_mm, stator.pacote_mm, stator.polos
        )
    score, alertas = _confidence_score(
        espiras=espiras,
        media_prop=media_prop,
        media_hist=media_hist,
        fill_ratio=fill_ratio,
        flux_index=flux_idx,
        flux_ref=flux_ref,
        n_refs=n_refs,
        is_estimativa=is_estimativa,
    )
    for pa in phys.alerts:
        if pa not in alertas:
            alertas.append(pa)
    score = min(score, phys.confidence_score)
    desvio_hist = _hist_deviation_pct(espiras, media_hist)
    desvio_prop = _prop_deviation_pct(espiras, media_prop)
    if desvio_prop is not None and desvio_prop > HIST_DIVERGENCE_REVISAR_PCT:
        msg = ALERT_DESVIO_HIST
        if msg not in alertas:
            alertas.append(msg)
    if should_alert_low_turns(
        espiras, media_hist, polos=stator.polos, ranhuras=stator.ranhuras
    ):
        if ALERT_ESPIRAS_BAIXAS not in alertas:
            alertas.append(ALERT_ESPIRAS_BAIXAS)

    fio_txt = calibre_display or format_wire_suggestion(espiras, wire)
    if calibre_display == CALIBRE_INVALIDO:
        fio_txt = CALIBRE_INVALIDO

    from engine.physics_audit import compute_slot_occupation_ratio

    final_ff = compute_slot_occupation_ratio(
        espiras,
        eq_awg,
        ranhuras=stator.ranhuras,
        diametro_mm=stator.diametro_mm,
        pacote_mm=stator.pacote_mm,
        parallel_count=wire.parallel_count,
        tipo_bobinagem=stator.tipo_bobinagem,
        passo=stator.passo,
    )
    physics_conf = int(phys.confidence_score)
    if final_ff > FF_MAX + 1e-6:
        desabilitado = True
        if MSG_FF_IMPOSSIVEL not in alertas:
            alertas.append(MSG_FF_IMPOSSIVEL)
        score = 0
        physics_conf = 0

    from engine.physics_validator import PhysicsValidatorEngine

    awg_ref: Optional[float] = None
    if stator.fio_validacao_usuario_awg and stator.fio_validacao_usuario_awg > 0:
        awg_ref = float(stator.fio_validacao_usuario_awg)
    usa_val = bool(
        stator.espiras_validacao_usuario and stator.espiras_validacao_usuario > 0
    )
    verdict = PhysicsValidatorEngine.validate_scenario_render(
        espiras=espiras,
        awg=eq_awg,
        parallel_count=wire.parallel_count,
        fill_factor_ff=final_ff,
        current_density_j=phys.current_density_j if usa_val else None,
        b_tesla=phys.flux_density_b_t,
        awg_referencia=awg_ref if awg_ref and abs(awg_ref - eq_awg) >= 0.05 else None,
        parallel_referencia=1,
        espiras_referencia=stator.espiras_validacao_usuario,
        strict_j=usa_val,
        validate_j=usa_val,
    )
    reprovado_fisicamente = verdict.reprovado_fisicamente
    if reprovado_fisicamente:
        desabilitado = True
        cenario_principal = False
        score = 0
        physics_conf = 0
        for msg in verdict.mensagens:
            if msg not in alertas:
                alertas.append(msg)

    return WindingScenario(
        cenario_id=cenario_id,
        titulo=titulo,
        descricao=descricao,
        espiras=round(espiras, 1),
        wire=wire,
        fio_texto=fio_txt,
        calibre_display=calibre_display or wire.label(),
        desabilitado=desabilitado,
        cenario_principal=cenario_principal,
        fator_ocupacao_ranhura=round(fill_ratio * 100, 1),
        densidade_fluxo_indice=flux_idx,
        confidence_score=score,
        alertas=alertas,
        desvio_historico_pct=desvio_hist,
        desvio_proporcional_pct=desvio_prop,
        espiras_proporcional_ref=media_prop,
        espiras_busola_ref=media_hist,
        slot_fill_units=round(fill_u, 4),
        slot_fill_limite=slot_limit,
        fio_alternativa_paralelo=fio_alternativa_paralelo,
        fill_factor_ff=final_ff,
        current_density_j=phys.current_density_j,
        physics_confidence=physics_conf,
        reprovado_fisicamente=reprovado_fisicamente,
    )


def _wire_texts_for_awg(espiras: float, awg: float) -> tuple[str, str, WireConfig]:
    opts = wire_display_options(espiras, awg)
    principal = opts["principal"]
    alt = opts.get("alternativa_paralelo") or ""
    wire = WireConfig(parallel_count=1, awg=round(awg, 1))
    return principal, alt, wire


def _lei_absoluta_validacao(stator: StatorInput, user_esp: Optional[float]) -> bool:
    """Validação humana ou motor 24 ranhuras / 2 polos com espiras informadas."""
    if user_esp is None or user_esp <= 0:
        return False
    if stator.ranhuras == 24 and stator.polos == 2:
        return True
    return True


GEMINI_LAYER1_SAMPLE_CAP = 280


def _parse_topologia_layer1_espiras(topo: dict[str, Any]) -> Optional[float]:
    for key in (
        "espiras_topologia_base",
        "espiras_base",
        "espiras_sugeridas",
        "espiras",
        "N_base",
    ):
        v = topo.get(key)
        if v is None:
            continue
        try:
            fv = float(v)
            if fv > 0:
                return fv
        except (TypeError, ValueError):
            continue
    return None


def _motor_compact_gemini_row(m: MotorRow) -> dict[str, Any]:
    return {
        "sha": (m.sha or "")[:12],
        "carcaca": m.carcaca,
        "d_mm": round(float(m.diametro_mm or 0), 1) if m.diametro_mm else None,
        "p_mm": round(float(m.pacote_mm or 0), 1) if m.pacote_mm else None,
        "polos_txt": str(m.polos or "").strip(),
        "passo": m.passo_principal,
        "tipo": (m.tipo_bobinagem_norm or m.tipo_bobinagem or "").strip(),
        "espiras": float(m.espiras_principal) if m.espiras_principal else None,
        "fio": (m.fio_principal or "").strip(),
    }


def build_gemini_layer1_topology_payload(
    *,
    stator: StatorInput,
    base: CalculationSuggestion,
    motors: list[MotorRow],
    media_prop: float,
    media_hist: Optional[float],
    user_norte_espiras: Optional[float],
    user_norte_awg: Optional[float],
) -> dict[str, Any]:
    pool = filter_file(motors)
    pool = [m for m in pool if not should_exclude_motor_row_pollution(m)]
    uc = norm_carcaca(stator.carcaca)
    pp = passo_canonical(stator.passo)

    def _prior(motor: MotorRow) -> tuple[int, int]:
        pc = (
            0
            if (uc and uc == norm_carcaca(motor.carcaca))
            else 1
        )
        pe = (
            0
            if (pp and passo_exact_match(stator.passo, motor.passo_principal))
            else 1
        )
        return (pc, pe)

    ordered = sorted(pool, key=_prior)
    amostra = [_motor_compact_gemini_row(m) for m in ordered[:GEMINI_LAYER1_SAMPLE_CAP]]

    norte: dict[str, Any]
    if (user_norte_espiras and user_norte_espiras > 0) or (
        user_norte_awg and user_norte_awg > 0
    ):
        norte = {
            "ativo": True,
            "espiras_norte_obrigatorias": round(float(user_norte_espiras), 1)
            if user_norte_espiras and user_norte_espiras > 0
            else None,
            "awg_norte": round(float(user_norte_awg), 1)
            if user_norte_awg and user_norte_awg > 0
            else None,
            "mensagem": (
                "O usuario definiu valores de validacao — use-os como norte absoluto para "
                "espiras-base e compatibilidade de bitola/enchimento de ranhura."
            ),
        }
    else:
        norte = {
            "ativo": False,
            "mensagem": "Sem norte do usuario: escolha o padrao dominante fisicamente plausivel no contexto cru.",
        }

    return {
        "estator_entrada": {
            "diametro_mm": stator.diametro_mm,
            "pacote_mm": stator.pacote_mm,
            "ranhuras": stator.ranhuras,
            "polos": stator.polos,
            "carcaca": stator.carcaca,
            "passo": str(stator.passo or "").strip(),
            "tipo_bobinagem": stator.tipo_bobinagem,
            "ligacao": stator.ligacao,
            "volume_estator_mm3_aprox": round(
                stator_volume_mm3(stator.diametro_mm, stator.pacote_mm), 1
            ),
        },
        "media_proporcional": media_prop,
        "media_historica": media_hist,
        "norte_validacao_usuario": norte,
        "resumo_acervo": {
            "n_registros_pos_filtros": len(pool),
            "amostras_enviadas_ia": len(amostra),
            "referencias_topo_engine": getattr(base, "n_matches", 0),
        },
        "amostra_registros": amostra,
        "n_amostra": len(amostra),
    }


class WindingOptimizer:
    """Gera cenários A/B/C de bobinagem a partir do acervo e leis de ranhura."""

    def __init__(self, motors: list[MotorRow]) -> None:
        self.motors = motors
        self._motor_by_sha = {m.sha: m for m in motors}

    def _resolve_tipo_efetivo(
        self,
        stator: StatorInput,
        base: CalculationSuggestion,
        *,
        skip_hierarchical: bool = False,
    ) -> tuple[str, Optional[TipoInferencia]]:
        if usuario_informou_tipo(stator.tipo_bobinagem):
            return norm_tipo_bobinagem(stator.tipo_bobinagem), None

        pool = filter_file(self.motors)
        infer = infer_tipo_from_referencias(
            base.top_matches,
            motor_by_sha=self._motor_by_sha,
        )
        if infer is None and pool and not skip_hierarchical:
            from app.hierarchical_search import hierarchical_find_references

            hier = hierarchical_find_references(
                pool,
                diametro_mm=stator.diametro_mm,
                pacote_mm=stator.pacote_mm,
                carcaca=stator.carcaca,
                passo=stator.passo,
                tipo_bobinagem="",
                top_k=15,
                min_refs=1,
            )
            infer = infer_tipo_from_referencias(
                hier.matches,
                motor_by_sha=self._motor_by_sha,
            )

        if infer is None:
            from app.topologia_bobinagem import infer_tipo_bobinagem

            guess = infer_tipo_bobinagem(
                passo_principal=stator.passo,
                explicit="",
            )
            if guess and guess != "DESCONHECIDO":
                infer = TipoInferencia(
                    codigo=guess,
                    label=label_tipo(guess),
                    explicacao=(
                        f"Tipo sugerido por heurística do passo **{stator.passo or '—'}**: "
                        f"**{label_tipo(guess)}**. Confirme na ficha ou no motor original."
                    ),
                    confianca_pct=55.0,
                    amostra=0,
                )

        if infer is None:
            return "", None
        return infer.codigo, infer

    def optimize(
        self,
        stator: StatorInput,
        *,
        use_gemini: bool = False,
        top_k: int = 5,
        use_neuro_symbolic: bool = False,
    ) -> WindingOptimizationResult:
        ok, msg = validate_required_motor_inputs(
            diametro_mm=stator.diametro_mm,
            pacote_mm=stator.pacote_mm,
            ranhuras=stator.ranhuras,
            polos=stator.polos,
        )
        entrada = {
            "diametro_mm": stator.diametro_mm,
            "pacote_mm": stator.pacote_mm,
            "ranhuras": stator.ranhuras,
            "polos": stator.polos,
            "carcaca": stator.carcaca,
            "passo": stator.passo,
            "tipo_bobinagem": stator.tipo_bobinagem,
            "ligacao": stator.ligacao,
        }
        if not ok:
            return WindingOptimizationResult(
                entrada=entrada,
                cenarios=[],
                validation_status="INCOMPLETO",
                validation_message=msg,
            )

        tipo_calc_in = (
            stator.tipo_bobinagem
            if usuario_informou_tipo(stator.tipo_bobinagem)
            else ""
        )
        user_esp_pre: Optional[float] = None
        if stator.espiras_validacao_usuario and stator.espiras_validacao_usuario > 0:
            user_esp_pre = float(stator.espiras_validacao_usuario)
        user_hard_override_validacao = user_esp_pre is not None
        use_gemini_eff = False if user_hard_override_validacao else use_gemini

        base: CalculationSuggestion = suggest_calculation(
            self.motors,
            diametro_mm=stator.diametro_mm,
            pacote_mm=stator.pacote_mm,
            carcaca=stator.carcaca,
            passo=stator.passo,
            tipo_bobinagem=tipo_calc_in,
            ligacao=stator.ligacao,
            ranhuras=stator.ranhuras,
            polos=stator.polos,
            top_k=top_k,
            use_gemini=False,
        )

        tipo_infer: Optional[TipoInferencia] = None
        if not usuario_informou_tipo(stator.tipo_bobinagem):
            _, tipo_infer = self._resolve_tipo_efetivo(
                stator,
                base,
                skip_hierarchical=user_hard_override_validacao,
            )
            if tipo_infer and tipo_infer.confianca_pct >= 40:
                base = suggest_calculation(
                    self.motors,
                    diametro_mm=stator.diametro_mm,
                    pacote_mm=stator.pacote_mm,
                    carcaca=stator.carcaca,
                    passo=stator.passo,
                    tipo_bobinagem=tipo_infer.codigo,
                    ligacao=stator.ligacao,
                    ranhuras=stator.ranhuras,
                    polos=stator.polos,
                    top_k=top_k,
                    use_gemini=False,
                )

        media_prop = base.espiras_media_top5 or base.sugestao_espira
        filtered_espiras: list[float] = []
        n_removed_pollution = 0
        for h in base.top_matches:
            if not h.espiras_historico or h.espiras_historico <= 0:
                continue
            eh = float(h.espiras_historico)
            if should_exclude_cadastro_pollution_80_90(h.carcaca, eh):
                n_removed_pollution += 1
                continue
            filtered_espiras.append(eh)

        media_hist_clean: Optional[float]
        if filtered_espiras:
            media_hist_clean, n_hist_total, n_hist_clean = robust_historical_median(
                filtered_espiras
            )
        else:
            media_hist_clean, n_hist_total, n_hist_clean = None, 0, 0
        media_hist = media_hist_clean
        n_outliers = max(0, n_hist_total - n_hist_clean)
        slot_limit_raw = base.slot_fill_limit
        slot_limit = resolve_slot_fill_limit(
            slot_limit_raw,
            ranhuras=stator.ranhuras,
            diametro_mm=stator.diametro_mm,
            pacote_mm=stator.pacote_mm,
        )
        n_refs = base.n_matches

        is_estimativa = base.is_estimativa
        forcar_gemini = base.forcar_gemini

        if media_prop is None or media_prop <= 0:
            return WindingOptimizationResult(
                entrada=entrada,
                cenarios=[],
                calculo_baseado_em=base.calculo_baseado_em,
                validation_status=base.validation_status or "SEM_REFERENCIA",
                validation_message=base.validation_message,
                is_estimativa=is_estimativa,
                forcar_gemini=forcar_gemini,
                base_suggestion=asdict(base),
            )

        esp_prop = float(media_prop)
        vol_mm3 = stator_volume_mm3(stator.diametro_mm, stator.pacote_mm)

        user_esp = user_esp_pre
        usa_validacao = _lei_absoluta_validacao(stator, user_esp)
        apply_fem_guard = not usa_validacao
        busola_inconsistente = False
        magnetic_sanity_gate_active = False
        gemini_topologia_camada1 = False
        alertas_globais: list[str] = []

        if usa_validacao:
            espiras_hist = round(float(user_esp), 1)
            if busola_historica_inconsistente(espiras_hist, media_hist):
                busola_inconsistente = True
                alertas_globais.append(MSG_BUSSOLA_DIVERGENTE)
            alertas_globais.append(
                "Validação humana ('Seu cálculo'): projeção A/B/C exclusiva ao valor informado; "
                "média do acervo, hierarquia e Gemini não dirigem espiras/bitola-base."
            )
            if stator.ranhuras == 24 and stator.polos == 2:
                alertas_globais.append(
                    "Motor 24 ranhuras / 2 polos: espiras informadas tratadas como constante K central."
                )
        else:
            espiras_hist = round(esp_prop, 1)
            aviso_hist = proportional_vs_hist_alert(espiras_hist, media_hist)
            if aviso_hist:
                alertas_globais.append(aviso_hist)

        esp_ref, esp_fem, fem_msgs = enforce_fem_turns_veto(
            espiras_hist,
            diametro_mm=stator.diametro_mm,
            pacote_mm=stator.pacote_mm,
            polos=stator.polos,
            ranhuras=stator.ranhuras,
            carcaca=stator.carcaca,
        )
        if fem_msgs:
            alertas_globais.extend(fem_msgs)
        if esp_fem > 0:
            alertas_globais.append(
                f"Referência FEM (220 V / 60 Hz / B=1.5 T): **{esp_fem}** espiras por polo."
            )
        if esp_ref > espiras_hist + 0.05 and MSG_FEM_VETO_TURNS not in alertas_globais:
            alertas_globais.append(MSG_FEM_VETO_TURNS)

        meta_hist_comparison: Optional[float] = (
            esp_ref
            if usa_validacao or gemini_topologia_camada1 or magnetic_sanity_gate_active
            else media_hist
        )

        if stator.fio_validacao_usuario_awg and stator.fio_validacao_usuario_awg > 0:
            awg_base_raw = float(stator.fio_validacao_usuario_awg)
        else:
            awg_base_raw = float(base.sugestao_fio_awg or 23.0)

        candidate_pool: list[dict[str, Any]] = []
        gemini_evaluation: dict[str, Any] = {}
        neuro_symbolic_active = False
        ns_best: Optional[dict[str, Any]] = None

        if use_neuro_symbolic and not usa_validacao:
            candidate_pool, gemini_evaluation, ns_best = run_neuro_symbolic_selection(
                stator,
                entrada=entrada,
                esp_ref=esp_ref,
                awg_base=awg_base_raw,
                apply_fem_turns_guard=apply_fem_guard,
            )
            neuro_symbolic_active = True
            ns_status = str(gemini_evaluation.get("status") or "INVIÁVEL")
            ns_just = str(gemini_evaluation.get("engineering_justification") or "").strip()
            if ns_best:
                esp_ref = float(ns_best["espiras"])
                awg_base_raw = float(ns_best["awg"])
                if ns_just:
                    alertas_globais.insert(
                        0,
                        f"Neuro-simbólico ({ns_status}): {ns_just}",
                    )
            elif candidate_pool:
                from services.gemini_evaluator import deterministic_candidate_fallback

                fb = deterministic_candidate_fallback(candidate_pool)
                fb_idx = int(fb.get("best_candidate_index", 0))
                ns_best = candidate_pool[max(0, min(fb_idx, len(candidate_pool) - 1))]
                gemini_evaluation = fb
                esp_ref = float(ns_best["espiras"])
                awg_base_raw = float(ns_best["awg"])
                alertas_globais.insert(
                    0,
                    f"Neuro-simbólico (fallback): {fb.get('engineering_justification', '')}",
                )

        esp_b = round(esp_ref, 1)
        from engine.physics_audit import compute_slot_occupation_ratio

        if usa_validacao:
            awg_b = awg_base_raw
            ff_b = compute_slot_occupation_ratio(
                esp_b,
                awg_b,
                ranhuras=stator.ranhuras,
                diametro_mm=stator.diametro_mm,
                pacote_mm=stator.pacote_mm,
                tipo_bobinagem=stator.tipo_bobinagem,
                passo=stator.passo,
            )
            ff_msgs_b = []
            if ff_b > FF_MAX + 1e-6:
                alertas_globais.append(MSG_FF_IMPOSSIVEL)
            awg_adj_b = False
            msg_b_awg = ""
        elif neuro_symbolic_active and ns_best:
            awg_b = float(ns_best["awg"])
            ff_b = float(ns_best["ff"])
            ff_msgs_b = []
            awg_adj_b = False
            msg_b_awg = ""
        else:
            awg_b, ff_b, ff_msgs_b = select_awg_for_ff_cap(
                esp_b,
                awg_base_raw,
                ranhuras=stator.ranhuras,
                diametro_mm=stator.diametro_mm,
                pacote_mm=stator.pacote_mm,
                carcaca=stator.carcaca,
                ff_max=FF_MAX,
                tipo_bobinagem=stator.tipo_bobinagem,
                passo=stator.passo,
                polos=stator.polos,
            )
            if ff_msgs_b:
                alertas_globais.extend(ff_msgs_b)
            if ff_b > FF_MAX + 1e-6:
                alertas_globais.append(MSG_FF_IMPOSSIVEL)
            awg_adj_b = abs(awg_b - awg_base_raw) >= 0.05
            msg_b_awg = MSG_AWG_COMERCIAL if awg_adj_b else ""
        if usa_validacao and slot_limit and slot_limit > 0:
            fill_hist = slot_fill_ratio(esp_b, awg_b, slot_limit)
            if fill_hist > MAX_SLOT_OCCUPATION:
                alertas_globais.append(
                    f"Aviso: ocupação de ranhura {fill_hist:.0%} acima do alvo "
                    f"({MAX_SLOT_OCCUPATION:.0%}) — bitola informada mantida na validação humana."
                )
                ff_b = compute_slot_occupation_ratio(
                    esp_b,
                    awg_b,
                    ranhuras=stator.ranhuras,
                    diametro_mm=stator.diametro_mm,
                    pacote_mm=stator.pacote_mm,
                    tipo_bobinagem=stator.tipo_bobinagem,
                    passo=stator.passo,
                )
        if neuro_symbolic_active and ns_best and isinstance(ns_best.get("wire"), WireConfig):
            wire_b = ns_best["wire"]
        else:
            wire_b = WireConfig(parallel_count=1, awg=awg_b)
        if ff_b > FF_MAX + 1e-6 and MSG_FF_IMPOSSIVEL not in alertas_globais:
            alertas_globais.append(MSG_FF_IMPOSSIVEL)
        flux_ref = _flux_density_index(
            esp_ref, stator.diametro_mm, stator.pacote_mm, stator.polos
        )

        # --- Cenário B: referência principal (usuário ou histórico limpo) ---
        txt_b, alt_b, _ = _wire_texts_for_awg(esp_b, awg_b)
        if neuro_symbolic_active and ns_best and ns_best.get("fio_texto"):
            txt_b = str(ns_best["fio_texto"])
        if usa_validacao:
            desc_b = (
                f"Padrão validado pelo usuário: **{esp_ref}** espiras "
                f"(Constante K a partir desta referência; média histórica não dita o resultado)."
            )
            if media_hist:
                desc_b += (
                    f" Média histórica limpa (somente comparativo): "
                    f"{round(media_hist, 1)} espiras."
                )
            if busola_inconsistente:
                desc_b += f" {MSG_BUSSOLA_DIVERGENTE}."
        else:
            desc_b = (
                f"**Padrão de referência (física validada)** — **{esp_ref}** espiras "
                f"(max entre histórico proporcional e FEM B≤1.5 T)"
            )
            if media_hist:
                desc_b += (
                    f" (mediana histórica limpa comparativa: "
                    f"**{round(media_hist, 1)}** esp."
                )
                if n_outliers > 0:
                    desc_b += (
                        f"; {n_outliers} outlier(s) removido(s) — faixa Média ±30% / Z-score"
                    )
                desc_b += ")"
            if n_removed_pollution > 0:
                desc_b += (
                    f" **{n_removed_pollution}** registro(s) excluído(s) (<20 esp. em carcaça 80–90)."
                )
        if awg_adj_b and msg_b_awg:
            desc_b = f"{desc_b} {msg_b_awg}"
        if is_estimativa:
            desc_b = f"{desc_b} {base.validation_message or base.calculo_baseado_em}"
        cenario_b = _build_scenario(
            cenario_id="B",
            titulo="Padrão de Referência",
            descricao=desc_b,
            espiras=esp_b,
            wire=wire_b,
            media_prop=media_prop,
            media_hist=meta_hist_comparison,
            slot_limit=slot_limit,
            flux_ref=flux_ref,
            stator=stator,
            n_refs=n_refs,
            fio_alternativa_paralelo=alt_b,
            is_estimativa=is_estimativa,
            cenario_principal=True,
            apply_fem_turns_guard=apply_fem_guard,
        )
        cenario_b.fio_texto = txt_b
        if alertas_globais:
            cenario_b.alertas = alertas_globais + cenario_b.alertas

        # --- Cenário A: mesa AWG comercial fixa (14–22) ---
        alertas_a: list[str] = []
        desc_a = (
            f"Maior seção de cobre possível com ocupação de ranhura até "
            f"{MAX_SLOT_OCCUPATION:.0%} do limite histórico."
        )
        esp_a = esp_ref
        calibre_a = ""
        desabilitar_a = False
        awg_a = awg_b
        wire_a = WireConfig(parallel_count=1, awg=awg_a)
        a_ok = True

        if usa_validacao:
            idx = awg_table_index(awg_b)
            awg_a = float(COMMERCIAL_BOBINAGEM_AWGS[idx - 1]) if idx > 0 else awg_b
            if slot_limit and slot_limit > 0:
                fill_thick = slot_fill_ratio(esp_ref, awg_a, slot_limit)
                if fill_thick > MAX_SLOT_OCCUPATION:
                    awg_a = float(
                        select_awg_for_slot_fill(
                            esp_ref,
                            slot_limit,
                            target_lo=0.55,
                            target_hi=MAX_SLOT_OCCUPATION,
                            prefer_awg=awg_b,
                        )
                    )
            esp_a = round(esp_ref, 1)
            wire_a = WireConfig(parallel_count=1, awg=awg_a)
            desc_a = (
                f"Otimizado mantendo **{esp_a}** espiras (validação); bitola comercial "
                f"**1×{int(awg_a)} AWG** sem recalcular espiras (equivalência N-3 preservada nos cenários B/C)."
            )
        else:
            if slot_limit and slot_limit > 0:
                awg_a_raw, adj_a, msg_a = awg_for_fill_with_limits(
                    esp_a, slot_limit, MAX_SLOT_OCCUPATION, stator.carcaca
                )
            else:
                awg_a_raw, adj_a, msg_a = clamp_awg_to_safe_range(
                    max(awg_b - 1.0, 10.0), stator.carcaca
                )

            if msg_a == CALIBRE_INVALIDO or not is_awg_in_range(awg_a_raw, stator.carcaca):
                desabilitar_a = True
                calibre_a = CALIBRE_INVALIDO
                alertas_a.append(
                    f"{CALIBRE_INVALIDO} — use o Cenário B (referência proporcional) como principal."
                )
                awg_a = awg_b
                esp_a = esp_ref
                wire_a = WireConfig(parallel_count=1, awg=awg_a)
            else:
                esp_a, awg_a, comm_adj, comm_msg = apply_commercial_awg_preserve_copper(
                    esp_a, awg_a_raw, stator.carcaca
                )
                if adj_a and msg_a:
                    alertas_a.append(msg_a)
                if comm_adj and comm_msg:
                    alertas_a.append(comm_msg)
                    desc_a = f"{desc_a} {comm_msg}"
                wire_a = WireConfig(parallel_count=1, awg=awg_a)
                if slot_limit and slot_limit > 0:
                    fill_a = _slot_occupation_ratio(slot_fill_units(esp_a, awg_a), slot_limit)
                    if fill_a > MAX_SLOT_OCCUPATION:
                        awg_a2, adj2, msg2 = awg_for_fill_with_limits(
                            esp_a, slot_limit, MAX_SLOT_OCCUPATION * 0.98, stator.carcaca
                        )
                        if msg2 != CALIBRE_INVALIDO:
                            if adj2 and msg2:
                                alertas_a.append(msg2)
                            esp_a, awg_a, comm2, msg_comm2 = apply_commercial_awg_preserve_copper(
                                esp_a, awg_a2, stator.carcaca
                            )
                            if comm2 and msg_comm2:
                                alertas_a.append(msg_comm2)
                            wire_a = WireConfig(parallel_count=1, awg=awg_a)

            if slot_limit and slot_limit > 0 and not desabilitar_a:
                esp_a, awg_a, tune_a_msgs = tune_slot_occupation_band(esp_a, awg_a, slot_limit)
                alertas_a.extend(tune_a_msgs)
                wire_a = WireConfig(parallel_count=1, awg=awg_a)

            if slot_limit and slot_limit > 0:
                fill_a_ratio = _slot_occupation_ratio(
                    slot_fill_units(esp_a, awg_a), slot_limit
                )
                a_ok = scenario_a_is_acceptable(
                    esp_a,
                    meta_hist_comparison or media_hist,
                    fill_a_ratio,
                    max_deviation=HIST_BIAS_MAX_DEVIATION,
                )
            if not a_ok:
                desabilitar_a = True
                calibre_a = MSG_CENARIO_A_INVALIDO
                ref_val = meta_hist_comparison if meta_hist_comparison is not None else media_hist
                ref_txt = f"{ref_val:.0f}" if ref_val is not None else "—"
                alertas_a.append(
                    f"{MSG_CENARIO_A_INVALIDO}: desvio >20% da bússola histórica limpa "
                    f"({esp_a:.0f} vs {ref_txt}) ou ocupação de ranhura inaceitável. "
                    "Use o Cenário B como referência principal."
                )
                esp_a = esp_ref
                awg_a = awg_b
                wire_a = WireConfig(parallel_count=1, awg=awg_a)

        if (
            not usa_validacao
            and polarity_sanity_alert(stator.polos, esp_a, media_hist, stator.carcaca)
        ):
            alertas_a.append(ALERT_POLARIDADE)

        _, alt_a, _ = _wire_texts_for_awg(esp_a, awg_a)
        titulo_a = (
            MSG_CENARIO_A_INVALIDO
            if desabilitar_a and calibre_a == MSG_CENARIO_A_INVALIDO
            else "Otimizado / Eficiência"
        )
        cenario_a = _build_scenario(
            cenario_id="A",
            titulo=titulo_a,
            descricao=desc_a,
            espiras=esp_a,
            wire=wire_a,
            media_prop=media_prop,
            media_hist=meta_hist_comparison,
            slot_limit=slot_limit,
            flux_ref=flux_ref,
            stator=stator,
            n_refs=n_refs,
            fio_alternativa_paralelo=alt_a,
            is_estimativa=is_estimativa,
            calibre_display=calibre_a,
            desabilitado=desabilitar_a,
            cenario_principal=False,
            apply_fem_turns_guard=apply_fem_guard,
        )
        cenario_a.alertas = alertas_a + cenario_a.alertas
        if desabilitar_a:
            cenario_a.confidence_score = min(cenario_a.confidence_score, 20)
            if calibre_a == MSG_CENARIO_A_INVALIDO:
                cenario_a.fio_texto = MSG_CENARIO_A_INVALIDO
            elif calibre_a == CALIBRE_INVALIDO:
                cenario_a.fio_texto = CALIBRE_INVALIDO

        if (
            not usa_validacao
            and polarity_sanity_alert(stator.polos, esp_b, media_hist, stator.carcaca)
        ):
            cenario_b.alertas = [ALERT_POLARIDADE] + cenario_b.alertas

        # --- Cenário C: facilidade — fios em paralelo (regra N-3, espiras fixas) ---
        wire_c = parallel_from_single_awg(awg_b, 2)
        esp_c = round(esp_ref, 1)
        tune_c_msgs: list[str] = []
        if slot_limit and slot_limit > 0 and not usa_validacao:
            eq_fill_c = equivalent_single_awg(wire_c)
            _, eq_awg_c, tune_c_msgs = tune_slot_occupation_band(esp_c, eq_fill_c, slot_limit)
            wire_c = parallel_from_single_awg(eq_awg_c, 2)
            esp_c = round(esp_ref, 1)
        txt_c = format_wire_suggestion(esp_c, wire_c)
        desc_c = (
            "Fios em paralelo para bobinagem manual (regra N-3: 1×19 ≡ 2×22, 1×17 ≡ 2×20), "
            f"mantendo **{esp_c}** espiras."
        )
        cenario_c = _build_scenario(
            cenario_id="C",
            titulo="Facilidade de Execução",
            descricao=desc_c,
            espiras=esp_c,
            wire=wire_c,
            media_prop=media_prop,
            media_hist=meta_hist_comparison,
            slot_limit=slot_limit,
            flux_ref=flux_ref,
            stator=stator,
            n_refs=n_refs,
            fio_alternativa_paralelo=txt_c if wire_c.parallel_count <= 1 else "",
            is_estimativa=is_estimativa,
            apply_fem_turns_guard=apply_fem_guard,
        )
        cenario_c.fio_texto = txt_c
        if tune_c_msgs:
            cenario_c.alertas = tune_c_msgs + list(cenario_c.alertas)

        cenario_a_suprimido = desabilitar_a and calibre_a == MSG_CENARIO_A_INVALIDO
        cenarios: list[WindingScenario] = [cenario_b, cenario_c]
        if not cenario_a_suprimido:
            cenarios.insert(1, cenario_a)

        for cen in cenarios:
            cen.cenario_principal = False
        cenario_recomendado = ""
        for cid in ("B", "C", "A"):
            cen_pick = next((c for c in cenarios if c.cenario_id == cid), None)
            if cen_pick and scenario_passes_hard_physics_limits(cen_pick):
                cenario_recomendado = cid
                cen_pick.cenario_principal = True
                break
        if not cenario_recomendado:
            cenario_recomendado = ""
            for cen in cenarios:
                cen.cenario_principal = False

        if neuro_symbolic_active and ns_best and not cenario_recomendado:
            cen_b = next((c for c in cenarios if c.cenario_id == "B"), None)
            if cen_b is not None:
                cenario_recomendado = "B"
                cen_b.cenario_principal = True
                cen_b.desabilitado = False
                cen_b.espiras = round(float(ns_best["espiras"]), 1)
                cen_b.fill_factor_ff = ns_best.get("ff")
                cen_b.current_density_j = ns_best.get("j_a_mm2")
                pc = int(getattr(cen_b, "physics_confidence", 0) or 0)
                ns_pc = int(ns_best.get("physics_confidence") or 0)
                cen_b.confidence_score = max(int(cen_b.confidence_score or 0), ns_pc, 35)
                cen_b.physics_confidence = max(pc, ns_pc, 35)
                ns_just = str(gemini_evaluation.get("engineering_justification") or "").strip()
                if ns_just:
                    tag = f"IA engenharia ({gemini_evaluation.get('status')}): {ns_just}"
                    if tag not in cen_b.alertas:
                        cen_b.alertas.insert(0, tag)

        if magnetic_sanity_gate_active:
            for cen in cenarios:
                cen.confidence_score = min(int(cen.confidence_score), 40)
                if MSG_ESTIMATIVA_TECNICA_FORCADA not in cen.alertas:
                    cen.alertas.insert(0, MSG_ESTIMATIVA_TECNICA_FORCADA)

        base_out: dict[str, Any] = asdict(base)
        if use_gemini_eff and cenarios:
            from engine.physics_audit import cenario_valido_para_painel_recomendado

            cen_gem = None
            if cenario_recomendado:
                cand = next(
                    (c for c in cenarios if c.cenario_id == cenario_recomendado),
                    None,
                )
                if cand and cenario_valido_para_painel_recomendado(asdict(cand)):
                    cen_gem = cand
            if cen_gem is None:
                for cid in ("B", "C", "A"):
                    cand = next((c for c in cenarios if c.cenario_id == cid), None)
                    if cand and cenario_valido_para_painel_recomendado(asdict(cand)):
                        cen_gem = cand
                        break
            try:
                from services.gemini_engineering_validator import (
                    _GEMINI_ABORT_COMENTARIO,
                    build_magnetic_validation_abort_payload,
                    build_magnetic_validation_payload_final,
                    validate_magnetic_with_gemini,
                )

                if cen_gem is not None:
                    gem_payload = build_magnetic_validation_payload_final(
                        entrada=entrada,
                        cen=asdict(cen_gem),
                        base=base,
                        slot_fill_limit=slot_limit,
                        modo_validacao_usuario=usa_validacao,
                        espiras_validacao_usuario=user_esp,
                    )
                else:
                    gem_payload = build_magnetic_validation_abort_payload(
                        entrada=entrada,
                        cenarios=[asdict(c) for c in cenarios],
                        base=base,
                        slot_fill_limit=slot_limit,
                    )
                gem = validate_magnetic_with_gemini(gem_payload)
                comentario = str(gem.get("comentario_validacao") or "").strip()
                if cen_gem is not None:
                    if comentario:
                        base_out["justificativa_tecnica"] = (
                            f"{base.calculo_baseado_em}. Cenario {cen_gem.cenario_id}: "
                            f"{cen_gem.espiras} espiras, {cen_gem.fio_texto}. "
                            f"Validacao magnetica (valores finais pos-FEM/ff): {comentario}"
                        )
                    base_out["sugestao_espira"] = cen_gem.espiras
                    base_out["sugestao_fio_awg"] = cen_gem.wire.awg
                    base_out["sugestao_fio_texto"] = cen_gem.fio_texto
                    base_out["calculo_abortado"] = False
                else:
                    base_out["calculo_abortado"] = True
                    base_out["sugestao_espira"] = None
                    base_out["sugestao_fio_awg"] = None
                    base_out["sugestao_fio_texto"] = ""
                    base_out["justificativa_tecnica"] = _GEMINI_ABORT_COMENTARIO
                    comentario = _GEMINI_ABORT_COMENTARIO
                base_out["gemini_usado"] = True
                base_out["validacao_magnetica"] = (
                    "ABORTADO" if cen_gem is None else gem.get("validacao_magnetica", "")
                )
                gem_alerta = str(gem.get("alerta_risco") or "").strip()
                if gem_alerta:
                    base_out["alerta_risco"] = gem_alerta
            except Exception as exc:
                base_out["justificativa_tecnica"] = (
                    f"{base.calculo_baseado_em} (Gemini indisponivel: {exc})"
                )

        if neuro_symbolic_active:
            base_out["neuro_symbolic_active"] = True
            base_out["gemini_evaluation"] = dict(gemini_evaluation)
            base_out["candidate_pool"] = _candidate_pool_for_storage(candidate_pool)
            if cenario_recomendado:
                cen_pick = next(
                    (c for c in cenarios if c.cenario_id == cenario_recomendado),
                    None,
                )
                if cen_pick is not None:
                    base_out["calculo_abortado"] = False
                    base_out["sugestao_espira"] = cen_pick.espiras
                    base_out["sugestao_fio_awg"] = cen_pick.wire.awg
                    base_out["sugestao_fio_texto"] = cen_pick.fio_texto
                    ns_just = str(gemini_evaluation.get("engineering_justification") or "")
                    if ns_just:
                        base_out["justificativa_tecnica"] = (
                            f"{base.calculo_baseado_em}. Neuro-simbólico ({gemini_evaluation.get('status')}): "
                            f"{ns_just}"
                        )

        return WindingOptimizationResult(
            entrada=entrada,
            cenarios=cenarios,
            calculo_baseado_em=base.calculo_baseado_em,
            media_historica_espiras=media_hist,
            media_historica_limpa=media_hist,
            n_outliers_removidos=n_outliers,
            cenario_a_suprimido=cenario_a_suprimido,
            media_proporcional_espiras=media_prop,
            slot_fill_limite=slot_limit,
            n_referencias=n_refs,
            validation_status=base.validation_status,
            validation_message=base.validation_message,
            modo_sobrevivencia=base.modo_sobrevivencia,
            is_estimativa=is_estimativa,
            forcar_gemini=forcar_gemini,
            cenario_recomendado=cenario_recomendado,
            tipo_inferido=tipo_infer.codigo if tipo_infer else "",
            tipo_inferido_label=tipo_infer.label if tipo_infer else "",
            explicacao_tipo=tipo_infer.explicacao if tipo_infer else "",
            tipo_foi_inferido=bool(tipo_infer),
            usa_validacao_usuario=usa_validacao,
            busola_historica_inconsistente=busola_inconsistente,
            espiras_validacao_usuario=user_esp,
            magnetic_sanity_gate_active=magnetic_sanity_gate_active,
            volume_estator_mm3=vol_mm3,
            n_removed_pollution=n_removed_pollution,
            gemini_topologia_camada1=gemini_topologia_camada1,
            candidate_pool=_candidate_pool_for_storage(candidate_pool),
            gemini_evaluation=dict(gemini_evaluation),
            neuro_symbolic_active=neuro_symbolic_active,
            base_suggestion=base_out,
        )

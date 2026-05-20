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

from dataclasses import asdict, dataclass, field
from statistics import median
from typing import Any, Optional

from app.fio_paralelo import (
    WireConfig,
    choose_wire_config,
    equivalent_single_awg,
    format_wire_suggestion,
    parallel_from_single_awg,
)
from app.oficial_engine import (
    HIST_DIVERGENCE_REVISAR_PCT,
    CalculationSuggestion,
    suggest_calculation,
    validate_required_motor_inputs,
)
from app.search_lib import (
    MotorRow,
    awg_from_mm2,
    awg_to_mm2,
    slot_fill_units,
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
    polos: int
    carcaca: str = ""
    passo: str = ""
    tipo_bobinagem: str = ""
    ligacao: str = ""


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
    slot_fill_units: Optional[float] = None
    slot_fill_limite: Optional[float] = None


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
    base_suggestion: Optional[dict[str, Any]] = None


def _flux_density_index(espiras: float, diametro_mm: float, pacote_mm: float, polos: int) -> float:
    """Proxy adimensional: menos espiras no mesmo ferro => maior risco de saturação."""
    denom = max(diametro_mm * pacote_mm * max(polos, 2), 1.0)
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


def _awg_for_target_fill(espiras: float, slot_limit: float, occupation: float) -> float:
    """AWG equivalente (1 condutor) para ocupação alvo da ranhura."""
    if espiras <= 0 or slot_limit <= 0:
        return 23.0
    area = (occupation * slot_limit) / espiras
    awg = awg_from_mm2(max(area, 1e-9))
    return round(awg if awg is not None else 23.0, 1)


def _confidence_score(
    *,
    espiras: float,
    media_prop: Optional[float],
    media_hist: Optional[float],
    fill_ratio: float,
    flux_index: float,
    flux_ref: float,
    n_refs: int,
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

    if n_refs < 3:
        score -= 12
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
) -> WindingScenario:
    eq_awg = equivalent_single_awg(wire)
    fill_u = slot_fill_units(espiras, eq_awg)
    fill_ratio = _slot_occupation_ratio(fill_u, slot_limit)
    flux_idx = _flux_density_index(espiras, stator.diametro_mm, stator.pacote_mm, stator.polos)
    score, alertas = _confidence_score(
        espiras=espiras,
        media_prop=media_prop,
        media_hist=media_hist,
        fill_ratio=fill_ratio,
        flux_index=flux_idx,
        flux_ref=flux_ref,
        n_refs=n_refs,
    )
    desvio_hist = _hist_deviation_pct(espiras, media_hist)
    desvio_prop = _prop_deviation_pct(espiras, media_prop)
    if desvio_prop is not None and desvio_prop > HIST_DIVERGENCE_REVISAR_PCT:
        msg = ALERT_DESVIO_HIST
        if msg not in alertas:
            alertas.append(msg)

    return WindingScenario(
        cenario_id=cenario_id,
        titulo=titulo,
        descricao=descricao,
        espiras=round(espiras, 1),
        wire=wire,
        fio_texto=format_wire_suggestion(espiras, wire),
        fator_ocupacao_ranhura=round(fill_ratio * 100, 1),
        densidade_fluxo_indice=flux_idx,
        confidence_score=score,
        alertas=alertas,
        desvio_historico_pct=desvio_hist,
        desvio_proporcional_pct=desvio_prop,
        espiras_proporcional_ref=media_prop,
        slot_fill_units=round(fill_u, 4),
        slot_fill_limite=slot_limit,
    )


class WindingOptimizer:
    """Gera cenários A/B/C de bobinagem a partir do acervo e leis de ranhura."""

    def __init__(self, motors: list[MotorRow]) -> None:
        self.motors = motors

    def optimize(
        self,
        stator: StatorInput,
        *,
        use_gemini: bool = False,
        top_k: int = 5,
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

        base: CalculationSuggestion = suggest_calculation(
            self.motors,
            diametro_mm=stator.diametro_mm,
            pacote_mm=stator.pacote_mm,
            carcaca=stator.carcaca,
            passo=stator.passo,
            tipo_bobinagem=stator.tipo_bobinagem,
            ligacao=stator.ligacao,
            ranhuras=stator.ranhuras,
            polos=stator.polos,
            top_k=top_k,
            use_gemini=use_gemini,
        )

        media_prop = base.espiras_media_top5 or base.sugestao_espira
        media_hist = base.media_historica_espiras
        slot_limit = base.slot_fill_limit
        n_refs = base.n_matches
        fio_samples = [h.fio_principal for h in base.top_matches if h.fio_principal]

        if media_prop is None or media_prop <= 0:
            return WindingOptimizationResult(
                entrada=entrada,
                cenarios=[],
                calculo_baseado_em=base.calculo_baseado_em,
                validation_status=base.validation_status or "SEM_REFERENCIA",
                validation_message=base.validation_message,
                base_suggestion=asdict(base),
            )

        esp_base = float(media_prop)
        awg_base = float(base.sugestao_fio_awg or 23.0)
        flux_ref = _flux_density_index(
            esp_base, stator.diametro_mm, stator.pacote_mm, stator.polos
        )

        # --- Cenário B: média estatística / proporcional do acervo ---
        wire_b = choose_wire_config(awg_base, fio_samples, prefer_parallel=False)
        cenario_b = _build_scenario(
            cenario_id="B",
            titulo="Padrão de Referência",
            descricao="Mediana proporcional do acervo OFICIAL com lei da ranhura.",
            espiras=esp_base,
            wire=wire_b,
            media_prop=media_prop,
            media_hist=media_hist,
            slot_limit=slot_limit,
            flux_ref=flux_ref,
            stator=stator,
            n_refs=n_refs,
        )

        # --- Cenário A: máxima ocupação de cobre (até 75% do limite histórico) ---
        if slot_limit and slot_limit > 0:
            awg_a = _awg_for_target_fill(esp_base, slot_limit, MAX_SLOT_OCCUPATION)
        else:
            awg_a = max(awg_base - 1.5, 14.0)
        wire_a = WireConfig(parallel_count=1, awg=awg_a)
        fill_a = _slot_occupation_ratio(
            slot_fill_units(esp_base, awg_a), slot_limit
        )
        if fill_a > MAX_SLOT_OCCUPATION and slot_limit:
            awg_a = _awg_for_target_fill(esp_base, slot_limit, MAX_SLOT_OCCUPATION * 0.98)
            wire_a = WireConfig(parallel_count=1, awg=awg_a)
        cenario_a = _build_scenario(
            cenario_id="A",
            titulo="Otimizado / Eficiência",
            descricao=(
                f"Maior seção de cobre possível com ocupação de ranhura até "
                f"{MAX_SLOT_OCCUPATION:.0%} do limite histórico."
            ),
            espiras=esp_base,
            wire=wire_a,
            media_prop=media_prop,
            media_hist=media_hist,
            slot_limit=slot_limit,
            flux_ref=flux_ref,
            stator=stator,
            n_refs=n_refs,
        )

        # --- Cenário C: facilidade — fios em paralelo para bobina manual ---
        wire_c = choose_wire_config(awg_base, fio_samples, prefer_parallel=True)
        if wire_c.parallel_count < 2 and awg_base >= 17:
            wire_c = parallel_from_single_awg(awg_base, 2)
        esp_c = esp_base
        if slot_limit and slot_limit > 0:
            eq = equivalent_single_awg(wire_c)
            fill_c = slot_fill_units(esp_c, eq) * wire_c.parallel_count / slot_limit
            if fill_c > MAX_SLOT_OCCUPATION:
                esp_c = round(esp_base * 1.02, 1)
        cenario_c = _build_scenario(
            cenario_id="C",
            titulo="Facilidade de Execução",
            descricao="Fios em paralelo para bobinagem manual, mantendo seção equivalente.",
            espiras=esp_c,
            wire=wire_c,
            media_prop=media_prop,
            media_hist=media_hist,
            slot_limit=slot_limit,
            flux_ref=flux_ref,
            stator=stator,
            n_refs=n_refs,
        )

        cenarios = [cenario_a, cenario_b, cenario_c]
        return WindingOptimizationResult(
            entrada=entrada,
            cenarios=cenarios,
            calculo_baseado_em=base.calculo_baseado_em,
            media_historica_espiras=media_hist,
            media_proporcional_espiras=media_prop,
            slot_fill_limite=slot_limit,
            n_referencias=n_refs,
            validation_status=base.validation_status,
            validation_message=base.validation_message,
            modo_sobrevivencia=base.modo_sobrevivencia,
            base_suggestion=asdict(base),
        )

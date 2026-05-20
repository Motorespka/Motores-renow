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
    wire_display_options,
)
from app.oficial_engine import (
    HIST_DIVERGENCE_REVISAR_PCT,
    CalculationSuggestion,
    suggest_calculation,
    validate_required_motor_inputs,
)
from app.search_lib import MotorRow, awg_to_mm2, slot_fill_units
from engine.winding_sanity import (
    CALIBRE_INVALIDO,
    MSG_AJUSTE_LIMITE,
    awg_for_fill_with_limits,
    clamp_awg_to_safe_range,
    espiras_constante_k,
    is_awg_in_range,
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
    fio_alternativa_paralelo: str = ""
    calibre_display: str = ""
    desabilitado: bool = False
    cenario_principal: bool = False


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
        is_estimativa=is_estimativa,
    )
    desvio_hist = _hist_deviation_pct(espiras, media_hist)
    desvio_prop = _prop_deviation_pct(espiras, media_prop)
    if desvio_prop is not None and desvio_prop > HIST_DIVERGENCE_REVISAR_PCT:
        msg = ALERT_DESVIO_HIST
        if msg not in alertas:
            alertas.append(msg)

    fio_txt = calibre_display or format_wire_suggestion(espiras, wire)
    if calibre_display == CALIBRE_INVALIDO:
        fio_txt = CALIBRE_INVALIDO

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
        slot_fill_units=round(fill_u, 4),
        slot_fill_limite=slot_limit,
        fio_alternativa_paralelo=fio_alternativa_paralelo,
    )


def _wire_texts_for_awg(espiras: float, awg: float) -> tuple[str, str, WireConfig]:
    opts = wire_display_options(espiras, awg)
    principal = opts["principal"]
    alt = opts.get("alternativa_paralelo") or ""
    wire = WireConfig(parallel_count=1, awg=round(awg, 1))
    if alt:
        from app.fio_paralelo import parallel_alternative_for_single

        par = parallel_alternative_for_single(awg)
        if par:
            wire = par
    return principal, alt, wire


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

        esp_base = float(media_prop)
        awg_base_raw = float(base.sugestao_fio_awg or 23.0)
        awg_base, base_adj, base_msg = clamp_awg_to_safe_range(awg_base_raw, stator.carcaca)
        if base_adj and base_msg == CALIBRE_INVALIDO:
            awg_base = 23.0
        flux_ref = _flux_density_index(
            esp_base, stator.diametro_mm, stator.pacote_mm, stator.polos
        )

        # --- Cenário B: média estatística / proporcional do acervo (referência K) ---
        txt_b, alt_b, wire_b = _wire_texts_for_awg(esp_base, awg_base)
        desc_b = "Mediana proporcional do acervo OFICIAL com lei da ranhura."
        if is_estimativa:
            desc_b = f"{desc_b} {base.validation_message or base.calculo_baseado_em}"
        cenario_b = _build_scenario(
            cenario_id="B",
            titulo="Padrão de Referência",
            descricao=desc_b,
            espiras=esp_base,
            wire=wire_b,
            media_prop=media_prop,
            media_hist=media_hist,
            slot_limit=slot_limit,
            flux_ref=flux_ref,
            stator=stator,
            n_refs=n_refs,
            fio_alternativa_paralelo=alt_b,
            is_estimativa=is_estimativa,
            cenario_principal=True,
        )
        cenario_b.fio_texto = txt_b

        # --- Cenário A: máxima ocupação de cobre (AWG 14–26, espiras com constante K) ---
        alertas_a: list[str] = []
        desc_a = (
            f"Maior seção de cobre possível com ocupação de ranhura até "
            f"{MAX_SLOT_OCCUPATION:.0%} do limite histórico."
        )
        esp_a = esp_base
        calibre_a = ""
        desabilitar_a = False

        if slot_limit and slot_limit > 0:
            awg_a_raw, adj_a, msg_a = awg_for_fill_with_limits(
                esp_a, slot_limit, MAX_SLOT_OCCUPATION, stator.carcaca
            )
        else:
            awg_a_raw, adj_a, msg_a = clamp_awg_to_safe_range(
                max(awg_base - 1.0, 14.0), stator.carcaca
            )

        if msg_a == CALIBRE_INVALIDO or not is_awg_in_range(awg_a_raw, stator.carcaca):
            desabilitar_a = True
            calibre_a = CALIBRE_INVALIDO
            alertas_a.append(
                f"{CALIBRE_INVALIDO} — use o Cenário B (referência proporcional) como principal."
            )
            awg_a = awg_base
            esp_a = esp_base
        else:
            awg_a = awg_a_raw
            if adj_a and msg_a:
                alertas_a.append(msg_a)
                esp_a = espiras_constante_k(esp_base, awg_base, awg_a)
                desc_a = f"{desc_a} {MSG_AJUSTE_LIMITE} Espiras recalculadas (constante K)."

        wire_a = WireConfig(parallel_count=1, awg=awg_a)
        if not desabilitar_a and slot_limit and slot_limit > 0:
            fill_a = _slot_occupation_ratio(slot_fill_units(esp_a, awg_a), slot_limit)
            if fill_a > MAX_SLOT_OCCUPATION:
                awg_a2, adj2, msg2 = awg_for_fill_with_limits(
                    esp_a, slot_limit, MAX_SLOT_OCCUPATION * 0.98, stator.carcaca
                )
                if msg2 != CALIBRE_INVALIDO:
                    if adj2 and msg2:
                        alertas_a.append(msg2)
                    esp_a = espiras_constante_k(esp_base, awg_base, awg_a2)
                    awg_a = awg_a2
                    wire_a = WireConfig(parallel_count=1, awg=awg_a)

        _, alt_a, _ = _wire_texts_for_awg(esp_a, awg_a)
        cenario_a = _build_scenario(
            cenario_id="A",
            titulo="Otimizado / Eficiência",
            descricao=desc_a,
            espiras=esp_a,
            wire=wire_a,
            media_prop=media_prop,
            media_hist=media_hist,
            slot_limit=slot_limit,
            flux_ref=flux_ref,
            stator=stator,
            n_refs=n_refs,
            fio_alternativa_paralelo=alt_a,
            is_estimativa=is_estimativa,
            calibre_display=calibre_a,
            desabilitado=desabilitar_a,
            cenario_principal=False,
        )
        cenario_a.alertas = alertas_a + cenario_a.alertas
        if desabilitar_a:
            cenario_a.confidence_score = min(cenario_a.confidence_score, 25)
            cenario_a.fio_texto = CALIBRE_INVALIDO

        # --- Cenário C: facilidade — fios em paralelo para bobina manual ---
        awg_c_base, _, _ = clamp_awg_to_safe_range(awg_base, stator.carcaca)
        wire_c = choose_wire_config(awg_c_base, fio_samples, prefer_parallel=True)
        if wire_c.parallel_count < 2 and awg_c_base >= 17:
            wire_c = parallel_from_single_awg(awg_c_base, 2)
        eq_c = equivalent_single_awg(wire_c)
        eq_c, _, _ = clamp_awg_to_safe_range(eq_c, stator.carcaca)
        esp_c = espiras_constante_k(esp_base, awg_base, eq_c)
        if slot_limit and slot_limit > 0:
            eq_fill = equivalent_single_awg(wire_c)
            fill_c = _slot_occupation_ratio(slot_fill_units(esp_c, eq_fill), slot_limit)
            if fill_c > MAX_SLOT_OCCUPATION:
                esp_c = round(espiras_constante_k(esp_base, awg_base, eq_fill) * 0.98, 1)
        txt_c = format_wire_suggestion(esp_c, wire_c)
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
            fio_alternativa_paralelo=txt_c if wire_c.parallel_count <= 1 else "",
            is_estimativa=is_estimativa,
        )
        cenario_c.fio_texto = txt_c

        cenario_recomendado = "B"
        if desabilitar_a or calibre_a == CALIBRE_INVALIDO:
            cenario_recomendado = "B"
        elif cenario_b.confidence_score >= cenario_a.confidence_score:
            cenario_recomendado = "B"
        else:
            cenario_recomendado = "A"

        cenarios = [cenario_b, cenario_a, cenario_c]
        if cenario_recomendado == "A":
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
            is_estimativa=is_estimativa,
            forcar_gemini=forcar_gemini,
            cenario_recomendado=cenario_recomendado,
            base_suggestion=asdict(base),
        )

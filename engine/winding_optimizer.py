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
from engine.winding_sanity import (
    ALERT_ESPIRAS_BAIXAS,
    ALERT_POLARIDADE,
    CALIBRE_INVALIDO,
    HIST_BIAS_MAX_DEVIATION,
    MSG_AJUSTE_LIMITE,
    MSG_CENARIO_A_INVALIDO,
    MSG_MAGNETIC_GATE_HIST_OVERRIDE,
    MSG_ESTIMATIVA_TECNICA_FORCADA,
    MSG_BUSSOLA_DIVERGENTE,
    apply_commercial_awg_preserve_copper,
    apply_magnetic_floor_two_pole_frame,
    awg_for_fill_with_limits,
    busola_historica_inconsistente,
    clamp_awg_to_safe_range,
    effective_frame_mm,
    espiras_busola_oficina,
    espiras_constante_k,
    force_busola_if_underturn,
    is_awg_in_range,
    polarity_sanity_alert,
    scenario_a_is_acceptable,
    should_alert_low_turns,
    should_override_hist_by_magnetic_gate,
    stator_volume_mm3,
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
    if should_alert_low_turns(
        espiras, media_hist, polos=stator.polos, ranhuras=stator.ranhuras
    ):
        if ALERT_ESPIRAS_BAIXAS not in alertas:
            alertas.append(ALERT_ESPIRAS_BAIXAS)

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
        espiras_busola_ref=media_hist,
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
    ) -> tuple[str, Optional[TipoInferencia]]:
        if usuario_informou_tipo(stator.tipo_bobinagem):
            return norm_tipo_bobinagem(stator.tipo_bobinagem), None

        pool = filter_file(self.motors)
        infer = infer_tipo_from_referencias(
            base.top_matches,
            motor_by_sha=self._motor_by_sha,
        )
        if infer is None and pool:
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
            use_gemini=use_gemini,
        )

        tipo_infer: Optional[TipoInferencia] = None
        if not usuario_informou_tipo(stator.tipo_bobinagem):
            _, tipo_infer = self._resolve_tipo_efetivo(stator, base)
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
                    use_gemini=use_gemini,
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

        esp_prop = float(media_prop)
        vol_mm3 = stator_volume_mm3(stator.diametro_mm, stator.pacote_mm)
        frame_eff = effective_frame_mm(stator.carcaca, stator.diametro_mm)

        user_esp = (
            float(stator.espiras_validacao_usuario)
            if stator.espiras_validacao_usuario and stator.espiras_validacao_usuario > 0
            else None
        )
        usa_validacao = user_esp is not None
        busola_inconsistente = False
        magnetic_sanity_gate_active = False
        gemini_topologia_camada1 = False
        alertas_globais: list[str] = []
        forced_busola = False

        if usa_validacao:
            esp_ref = round(user_esp, 1)
            if busola_historica_inconsistente(esp_ref, media_hist):
                busola_inconsistente = True
                alertas_globais.append(MSG_BUSSOLA_DIVERGENTE)
            forced_busola = False

        elif use_gemini:
            try:
                from services.gemini_engineering_validator import (
                    propose_topology_base_with_gemini,
                )

                topo_payload = build_gemini_layer1_topology_payload(
                    stator=stator,
                    base=base,
                    motors=self.motors,
                    media_prop=esp_prop,
                    media_hist=media_hist,
                    user_norte_espiras=user_esp,
                    user_norte_awg=float(stator.fio_validacao_usuario_awg)
                    if (
                        stator.fio_validacao_usuario_awg
                        and stator.fio_validacao_usuario_awg > 0
                    )
                    else None,
                )
                topo_ia = propose_topology_base_with_gemini(topo_payload)
                esp_topo = _parse_topologia_layer1_espiras(topo_ia)
                if esp_topo is not None:
                    esp_ref = round(esp_topo, 1)
                    gemini_topologia_camada1 = True
                    forcar_gemini = True
                    is_estimativa = True
                    cmt = (
                        str(
                            topo_ia.get("comentario_topologia")
                            or topo_ia.get("comentario")
                            or ""
                        ).strip()
                    )
                    if cmt:
                        alertas_globais.append(
                            f"Gemini Camada 1 — topologia-base: {cmt[:520]}"
                        )
            except Exception:
                gemini_topologia_camada1 = False

            if not gemini_topologia_camada1:
                if should_override_hist_by_magnetic_gate(
                    stator.polos,
                    frame_eff,
                    media_hist,
                ):
                    magnetic_sanity_gate_active = True
                    is_estimativa = True
                    alertas_globais.append(MSG_MAGNETIC_GATE_HIST_OVERRIDE)
                    esp_ref = round(float(esp_prop), 1)
                    esp_ref, forced_busola = force_busola_if_underturn(
                        esp_ref,
                        None,
                        diametro_mm=stator.diametro_mm,
                        carcaca=stator.carcaca,
                    )
                else:
                    esp_ref = espiras_busola_oficina(media_hist, media_prop)
                    esp_ref, forced_busola = force_busola_if_underturn(
                        esp_ref,
                        media_hist,
                        diametro_mm=stator.diametro_mm,
                        carcaca=stator.carcaca,
                    )

        elif should_override_hist_by_magnetic_gate(
            stator.polos,
            frame_eff,
            media_hist,
        ):
            magnetic_sanity_gate_active = True
            is_estimativa = True
            alertas_globais.append(MSG_MAGNETIC_GATE_HIST_OVERRIDE)
            esp_ref = round(float(esp_prop), 1)
            esp_ref, forced_busola = force_busola_if_underturn(
                esp_ref,
                None,
                diametro_mm=stator.diametro_mm,
                carcaca=stator.carcaca,
            )
        else:
            esp_ref = espiras_busola_oficina(media_hist, media_prop)
            esp_ref, forced_busola = force_busola_if_underturn(
                esp_ref,
                media_hist,
                diametro_mm=stator.diametro_mm,
                carcaca=stator.carcaca,
            )

        esp_pre_floor = esp_ref
        esp_ref, phy_floor_msgs = apply_magnetic_floor_two_pole_frame(
            esp_pre_floor,
            polos=stator.polos,
            carcaca=stator.carcaca,
            diametro_mm=stator.diametro_mm,
            pacote_mm=stator.pacote_mm,
            cite_ia_correction_msg=bool(gemini_topologia_camada1),
        )
        if phy_floor_msgs:
            alertas_globais.extend(phy_floor_msgs)

        meta_hist_comparison: Optional[float] = (
            esp_ref
            if usa_validacao
            or magnetic_sanity_gate_active
            or gemini_topologia_camada1
            else media_hist
        )

        if stator.fio_validacao_usuario_awg and stator.fio_validacao_usuario_awg > 0:
            awg_base_raw = float(stator.fio_validacao_usuario_awg)
        else:
            awg_base_raw = float(base.sugestao_fio_awg or 23.0)
        esp_b, awg_b, awg_adj_b, msg_b_awg = apply_commercial_awg_preserve_copper(
            esp_ref, awg_base_raw, stator.carcaca
        )
        wire_b = WireConfig(parallel_count=1, awg=awg_b)
        flux_ref = _flux_density_index(
            esp_ref, stator.diametro_mm, stator.pacote_mm, stator.polos
        )
        ref_cenario_a = (
            esp_ref
            if usa_validacao
            or magnetic_sanity_gate_active
            or gemini_topologia_camada1
            else media_hist
        )

        # --- Cenário B: referência principal (usuário ou histórico limpo) ---
        txt_b, alt_b, _ = _wire_texts_for_awg(esp_b, awg_b)
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
            if gemini_topologia_camada1:
                desc_b = (
                    "Referência **Camada 1 (Gemini)**: topologia-base a partir de contexto bruto amostrado "
                    f"(até {GEMINI_LAYER1_SAMPLE_CAP} registros). **Camada 2** aplicou travas físicas "
                    f"(espiras após piso magnético: **{esp_ref}**). "
                    f"Proporcional (engine): {esp_prop} esp.; histórico limpo: {media_hist or '—'}."
                )
            elif magnetic_sanity_gate_active:
                desc_b = (
                    f"Bloqueio de sanidade magnético (2 polos, carcaça {frame_eff or '—'}, "
                    f"≥71–90 mm): média histórica **{(round(media_hist, 1) if media_hist else '—')}** "
                    "espiras ignorada (< 35). "
                    f"Referência física desde **42** espiras @ Ø80×70 mm escalada pelo volume "
                    f"útil (**{vol_mm3:.0f} mm³**). Comparativo proporcional: {esp_prop} espiras."
                )
                if forced_busola:
                    desc_b += (
                        " Ajuste adicional pela regra física do estator grande."
                    )
            else:
                desc_b = (
                    f"Padrão de referência da oficina: média histórica limpa "
                    f"{round(media_hist, 1) if media_hist else '—'} espiras"
                )
                if n_outliers > 0:
                    desc_b += f" ({n_outliers} outlier(s) removido(s) — faixa ±30%)."
                desc_b += f" Proporcional (comparativo): {esp_prop} espiras."
                if n_removed_pollution > 0:
                    desc_b += (
                        f" **{n_removed_pollution}** registro(s) excluído(s) (< 20 esp. em carcaça 80–90)."
                    )
                if forced_busola:
                    desc_b += (
                        " Espiras forçadas para a bússola "
                        "(cálculo bruto abaixo do mínimo físico)."
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
        )
        cenario_b.fio_texto = txt_b
        if alertas_globais:
            cenario_b.alertas = alertas_globais + cenario_b.alertas

        # --- Cenário A: máxima ocupação de cobre (AWG 14–26, espiras com constante K) ---
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

        if slot_limit and slot_limit > 0:
            awg_a_raw, adj_a, msg_a = awg_for_fill_with_limits(
                esp_a, slot_limit, MAX_SLOT_OCCUPATION, stator.carcaca
            )
        else:
            awg_a_raw, adj_a, msg_a = clamp_awg_to_safe_range(
                max(awg_b - 1.0, 14.0), stator.carcaca
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

        fill_a_ratio = _slot_occupation_ratio(
            slot_fill_units(esp_a, awg_a), slot_limit
        )
        a_ok = scenario_a_is_acceptable(
            esp_a,
            ref_cenario_a,
            fill_a_ratio,
            max_deviation=HIST_BIAS_MAX_DEVIATION,
        )
        if not a_ok:
            desabilitar_a = True
            calibre_a = MSG_CENARIO_A_INVALIDO
            ref_lbl = (
                "validação do usuário"
                if usa_validacao
                else (
                    "referência física segura"
                    if magnetic_sanity_gate_active
                    else "média histórica limpa"
                )
            )
            ref_val = ref_cenario_a if ref_cenario_a is not None else meta_hist_comparison
            alertas_a.append(
                f"{MSG_CENARIO_A_INVALIDO}: desvio >20% da {ref_lbl} "
                f"({esp_a:.0f} vs {ref_val:.0f}) ou ocupação de ranhura inaceitável."
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

        # --- Cenário C: facilidade — fios em paralelo (bússola histórica) ---
        awg_c_base, _, _ = clamp_awg_to_safe_range(awg_b, stator.carcaca)
        wire_c = choose_wire_config(awg_c_base, fio_samples, prefer_parallel=True)
        if wire_c.parallel_count < 2 and awg_c_base >= 17:
            wire_c = parallel_from_single_awg(awg_c_base, 2)
        eq_c_raw = equivalent_single_awg(wire_c)
        esp_c, eq_c, _, _ = apply_commercial_awg_preserve_copper(
            esp_ref, eq_c_raw, stator.carcaca
        )
        wire_c = choose_wire_config(eq_c, fio_samples, prefer_parallel=True)
        if wire_c.parallel_count < 2 and eq_c >= 17:
            wire_c = parallel_from_single_awg(eq_c, 2)
        esp_c = espiras_constante_k(esp_ref, awg_b, equivalent_single_awg(wire_c))
        if slot_limit and slot_limit > 0:
            eq_fill = equivalent_single_awg(wire_c)
            fill_c = _slot_occupation_ratio(slot_fill_units(esp_c, eq_fill), slot_limit)
            if fill_c > MAX_SLOT_OCCUPATION:
                esp_c = round(espiras_constante_k(esp_ref, awg_b, eq_fill) * 0.98, 1)
        txt_c = format_wire_suggestion(esp_c, wire_c)
        cenario_c = _build_scenario(
            cenario_id="C",
            titulo="Facilidade de Execução",
            descricao="Fios em paralelo para bobinagem manual, mantendo seção equivalente.",
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
        )
        cenario_c.fio_texto = txt_c

        cenario_recomendado = "B"
        cenario_a_suprimido = desabilitar_a and calibre_a == MSG_CENARIO_A_INVALIDO
        cenarios: list[WindingScenario] = [cenario_b, cenario_c]
        if not cenario_a_suprimido:
            cenarios.insert(1, cenario_a)

        if magnetic_sanity_gate_active:
            for cen in cenarios:
                cen.confidence_score = min(int(cen.confidence_score), 40)
                if MSG_ESTIMATIVA_TECNICA_FORCADA not in cen.alertas:
                    cen.alertas.insert(0, MSG_ESTIMATIVA_TECNICA_FORCADA)

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
            base_suggestion=asdict(base),
        )

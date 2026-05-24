#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de engenharia Gemini — gêmeo digital PINN/física.
Modo validação magnética, auditoria crítica e caixa preta.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.system_prompt_digital_twin import (
    SYSTEM_PROMPT_DIGITAL_TWIN,
    get_system_prompt_digital_twin,
)


def _prompt_validacao_magnetica(payload: dict[str, Any]) -> str:
    entrada = json.dumps(payload.get("entrada", {}), ensure_ascii=False, indent=2)
    modo_val = bool(payload.get("modo_validacao_usuario"))
    refs = json.dumps(
        [] if modo_val else (payload.get("calculos_proporcionais", [])[:3]),
        ensure_ascii=False,
        indent=2,
    )
    fio_txt = payload.get("sugestao_fio_texto") or payload.get("sugestao_fio_awg")
    limites = payload.get("limites") or {
        "b_tesla": 1.5,
        "j_a_mm2": "3-7",
        "ff_pct": "25-45",
    }
    if payload.get("calculo_abortado"):
        motivos = json.dumps(payload.get("motivos_abort") or [], ensure_ascii=False, indent=2)
        cenarios = json.dumps(payload.get("cenarios_reprovados") or [], ensure_ascii=False, indent=2)
        return (
            SYSTEM_PROMPT_DIGITAL_TWIN
            + "\n\nCÁLCULO ABORTADO — nenhum cenário A/B/C passou nos hard limits (B≤1.5 T, ff≤45%, J≤7 A/mm²).\n"
            "NAO valide nem sugira espiras/bitola do acervo proporcional ou gêmeo digital.\n"
            "Explique por que o projeto é inviável com base nos motivos listados.\n\n"
            f"ENTRADA:\n{entrada}\n\n"
            f"MOTIVOS DO ABORT:\n{motivos}\n\n"
            f"CENARIOS REPROVADOS (referencia tecnica apenas):\n{cenarios}\n\n"
            "Responda APENAS JSON:\n"
            "{\n"
            '  "validacao_magnetica": "REVISAR",\n'
            '  "comentario_validacao": "<por que inviavel: saturacao, ff, J>",\n'
            '  "alerta_risco": "<nao bobinar com estas configuracoes>"\n'
            "}\n"
        )
    resultado = (
        "RESULTADO FIXO (valide coerencia magnetica apenas):\n"
        f"  Cenario: {payload.get('cenario_id', 'B')}\n"
        f"  Espiras (finais, pos-FEM): {payload.get('sugestao_espira')}\n"
        f"  Fio (final, pos-ff cap): {fio_txt}\n"
        f"  Enchimento ranhura: {payload.get('slot_fill_actual')} / limite {payload.get('slot_fill_limit')}\n"
        f"  Ocupacao ranhura %: {payload.get('fator_ocupacao_ranhura_pct')}\n"
        f"  ff final: {payload.get('fill_factor_ff')}\n"
        f"  J estimado: {payload.get('current_density_j')} A/mm²\n"
        f"  Confianca fisica %: {payload.get('physics_confidence')}\n"
        f"  Base do calculo: {payload.get('calculo_baseado_em', '')}\n"
    )
    if payload.get("valores_finais_pos_fem_ff"):
        resultado += (
            "\nATENCAO: use APENAS os numeros acima (ja corrigidos por FEM e ff<=45%). "
            "Ignore medias proporcionais/historicas brutas do acervo.\n"
        )
    if modo_val:
        resultado += (
            "\nMODO VALIDACAO HUMANA: critique SOMENTE espiras/fio/ff/J listados em RESULTADO FIXO. "
            "NAO cite media historica, proporcional nem baseline do acervo (ex.: 36.4 espiras).\n"
        )
    refs_block = (
        "REFERENCIAS (amostra — NAO usar como alvo de validacao neste modo):\n"
        if modo_val
        else "REFERENCIAS (amostra):\n"
    )
    return (
        SYSTEM_PROMPT_DIGITAL_TWIN
        + "\n\nTarefa: validar resultado deterministico (NAO recalcular espiras/AWG).\n\n"
        "LIMITES FISICOS OBRIGATORIOS:\n"
        f"  B_max = {limites.get('b_tesla', 1.5)} T\n"
        f"  J = {limites.get('j_a_mm2', '3-7')} A/mm²\n"
        f"  ff = {limites.get('ff_pct', '25-45')} %\n\n"
        "FORMULA JA APLICADA (fonte da verdade):\n"
        "  N = V / (4.44 × f × B × A_fe × k_w)  e proporcional L/A do acervo.\n"
        "  Lei da ranhura: (Espiras × Secao_Fio) <= limite fisico.\n\n"
        f"ENTRADA:\n{entrada}\n\n"
        + resultado
        + "\n"
        + f"{refs_block}{refs}\n\n"
        "Responda APENAS JSON:\n"
        "{\n"
        '  "validacao_magnetica": "OK" ou "REVISAR",\n'
        '  "comentario_validacao": "<1-3 frases: B, J, ff, ranhura>",\n'
        '  "alerta_risco": "<vazio se OK; senao alerta fisico sem alterar numeros>"\n'
        "}\n"
    )


def _prompt_audit_suspeito(payload: dict[str, Any]) -> str:
    entrada = json.dumps(payload.get("entrada", {}), ensure_ascii=False, indent=2)
    aud_u = json.dumps(payload.get("auditoria_usuario", {}), ensure_ascii=False, indent=2)
    aud_c = json.dumps(payload.get("auditoria_corrigida", {}), ensure_ascii=False, indent=2)
    limites = json.dumps(payload.get("limites", {}), ensure_ascii=False)
    alvo = payload.get("alvo_validacao") or {}
    alvo_txt = json.dumps(alvo, ensure_ascii=False, indent=2) if alvo else ""
    bloco_alvo = (
        f"ALVO DE VALIDACAO (valores informados pelo usuario — unica referencia):\n{alvo_txt}\n\n"
        if alvo_txt
        else ""
    )
    return (
        SYSTEM_PROMPT_DIGITAL_TWIN
        + "\n\nMODO AUDITORIA — calculo suspeito (motor queimando, sem forca).\n"
        "Engenharia reversa critica: compare SOMENTE o calculo do usuario (espiras/fio/ff abaixo) "
        "vs limites fisicos. NAO valide nem cite medias historicas do acervo.\n\n"
        f"LIMITES: {limites}\n\n"
        f"ENTRADA MOTOR:\n{entrada}\n\n"
        + bloco_alvo
        + f"AUDITORIA USUARIO (suspeito):\n{aud_u}\n\n"
        f"PROPOSTA CORRIGIDA (motor deterministico):\n{aud_c}\n\n"
        "Responda APENAS JSON:\n"
        "{\n"
        '  "status_auditoria": "APROVADO" | "REPROVADO" | "CORRIGIR",\n'
        '  "nota_confianca_0_100": <int nota do calculo do usuario>,\n'
        '  "comentario": "<parecer tecnico: ff, J, saturacao, causa provavel queima>",\n'
        '  "alerta_risco": "<acao imediata na bancada>"\n'
        "}\n"
    )


def _prompt_caixa_preta(payload: dict[str, Any]) -> str:
    entrada = json.dumps(payload.get("entrada", {}), ensure_ascii=False, indent=2)
    cands = json.dumps(payload.get("candidatos", [])[:5], ensure_ascii=False, indent=2)
    return (
        SYSTEM_PROMPT_DIGITAL_TWIN
        + "\n\nMODO CAIXA PRETA — comentar candidatos gerados por FEM + algoritmo genetico.\n"
        "NAO invente novos numeros; ranqueie coerencia fisica dos candidatos listados.\n\n"
        f"ENTRADA:\n{entrada}\n\n"
        f"CANDIDATOS:\n{cands}\n\n"
        "Responda APENAS JSON:\n"
        "{\n"
        '  "candidato_recomendado": "<letra A-E>",\n'
        '  "comentario": "<2-4 frases>",\n'
        '  "alerta_risco": "<se houver>"\n'
        "}\n"
    )


def build_magnetic_validation_abort_payload(
    *,
    entrada: dict[str, Any],
    cenarios: list[dict[str, Any]],
    base: dict[str, Any] | Any,
    slot_fill_limit: Any = None,
) -> dict[str, Any]:
    """Payload quando o gate físico reprovou todos os cenários A/B/C."""
    base_d: dict[str, Any]
    if hasattr(base, "__dataclass_fields__"):
        from dataclasses import asdict

        base_d = asdict(base)
    elif isinstance(base, dict):
        base_d = base
    else:
        base_d = {}

    motivos: list[str] = []
    for cen in cenarios:
        cid = cen.get("cenario_id", "?")
        for alerta in cen.get("alertas") or []:
            sa = str(alerta).strip()
            if sa and sa not in motivos:
                motivos.append(f"[{cid}] {sa}")
        ff = cen.get("fill_factor_ff")
        if ff is not None:
            try:
                if float(ff) > 0.45:
                    motivos.append(
                        f"[{cid}] ff={float(ff):.1%} > 45% "
                        f"({cen.get('espiras')} esp, {cen.get('fio_texto', '')})"
                    )
            except (TypeError, ValueError):
                pass

    return {
        "entrada": entrada,
        "calculo_abortado": True,
        "cenarios_reprovados": cenarios,
        "motivos_abort": motivos[:12],
        "media_proporcional_espiras": base_d.get("media_proporcional_espiras")
        or base_d.get("espiras_media_top5"),
        "media_historica_espiras": base_d.get("media_historica_espiras"),
        "slot_fill_limit": slot_fill_limit,
        "validation_status": "ABORTADO",
        "calculo_baseado_em": base_d.get("calculo_baseado_em"),
        "sugestao_espira": None,
        "sugestao_fio_texto": None,
        "fill_factor_ff": None,
    }


def build_magnetic_validation_payload_final(
    *,
    entrada: dict[str, Any],
    cen: dict[str, Any],
    base: dict[str, Any] | Any,
    slot_fill_limit: Any = None,
    modo_validacao_usuario: bool = False,
    espiras_validacao_usuario: float | None = None,
) -> dict[str, Any]:
    """
    Payload da validação magnética com valores FINAIS do cenário recomendado
    (pós veto FEM + select_awg_for_ff_cap), não N_hist / proporcional bruto.
    """
    from app.fio_paralelo import WireConfig, format_wire_suggestion

    base_d: dict[str, Any]
    if hasattr(base, "__dataclass_fields__"):
        from dataclasses import asdict

        base_d = asdict(base)
    elif isinstance(base, dict):
        base_d = base
    else:
        base_d = {}

    esp = cen.get("espiras")
    wire_raw = cen.get("wire")
    if isinstance(wire_raw, dict):
        wire = WireConfig(
            parallel_count=int(wire_raw.get("parallel_count") or 1),
            awg=float(wire_raw.get("awg") or 19),
        )
    else:
        wire = WireConfig(parallel_count=1, awg=19.0)

    fio_txt = cen.get("fio_texto") or format_wire_suggestion(float(esp or 0), wire)
    from engine.physics_audit import normalize_fill_factor_ff

    ff_raw = cen.get("fill_factor_ff")
    occ_pct = cen.get("fator_ocupacao_ranhura")
    ff = normalize_fill_factor_ff(occ_pct if occ_pct is not None else ff_raw)
    if modo_validacao_usuario and espiras_validacao_usuario:
        esp = round(float(espiras_validacao_usuario), 1)
    slot_actual = cen.get("slot_fill_units")
    if slot_actual is None and slot_fill_limit and esp and wire.awg:
        from app.search_lib import slot_fill_units

        slot_actual = slot_fill_units(float(esp), float(wire.awg))

    entrada_out = dict(entrada)
    if modo_validacao_usuario:
        entrada_out["espiras_validacao_usuario"] = esp
        stator_fio = entrada.get("fio_engenheiro") or entrada.get("fio_awg")
        if stator_fio is not None:
            entrada_out["fio_validacao_usuario"] = stator_fio

    return {
        "entrada": entrada_out,
        "modo_validacao_usuario": modo_validacao_usuario,
        "calculos_proporcionais": [] if modo_validacao_usuario else (base_d.get("top_matches") or []),
        "media_proporcional_espiras": None
        if modo_validacao_usuario
        else (base_d.get("media_proporcional_espiras") or base_d.get("espiras_media_top5")),
        "media_historica_espiras": None if modo_validacao_usuario else base_d.get("media_historica_espiras"),
        "sugestao_espira": esp,
        "sugestao_fio_awg": wire.awg,
        "sugestao_fio_texto": fio_txt,
        "slot_fill_limit": slot_fill_limit or cen.get("slot_fill_limite"),
        "slot_fill_actual": slot_actual,
        "fill_factor_ff": ff,
        "fill_factor_ff_pct": round(float(ff or 0) * 100, 1) if ff is not None else None,
        "current_density_j": cen.get("current_density_j"),
        "fator_ocupacao_ranhura_pct": occ_pct if occ_pct is not None else cen.get("fator_ocupacao_ranhura"),
        "cenario_id": cen.get("cenario_id"),
        "physics_confidence": cen.get("physics_confidence") or cen.get("confidence_score"),
        "validation_status": base_d.get("validation_status"),
        "calculo_baseado_em": (
            "Validação humana — espiras/bitola informadas pelo usuário"
            if modo_validacao_usuario
            else base_d.get("calculo_baseado_em")
        ),
        "is_estimativa": base_d.get("is_estimativa"),
        "forcar_gemini": base_d.get("forcar_gemini"),
        "interpolacao_proporcional": False if modo_validacao_usuario else base_d.get("forcar_gemini"),
        "valores_finais_pos_fem_ff": True,
    }


_GEMINI_ABORT_COMENTARIO = (
    "O cálculo foi abortado por violação de limites físicos "
    "(Risco de saturação ou fio não cabe na ranhura). Não analise o dado histórico."
)


def validate_magnetic_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Gemini como validador tecnico — temperatura 0.1 no api_manager."""
    if payload.get("calculo_abortado"):
        return {
            "validacao_magnetica": "REVISAR",
            "comentario_validacao": _GEMINI_ABORT_COMENTARIO,
            "alerta_risco": (
                "Não bobinar: projeto reprovado por saturação magnética ou fator de enchimento."
            ),
        }

    from config.api_manager import get_gemini_api_manager

    if "limites" not in payload:
        payload = dict(payload)
        payload["limites"] = {"b_tesla": 1.5, "j_a_mm2": "3-7", "ff_pct": "25-45"}
    mgr = get_gemini_api_manager()
    raw = mgr.call_json(_prompt_validacao_magnetica(payload))
    status = str(raw.get("validacao_magnetica") or "OK").strip().upper()
    if status not in ("OK", "REVISAR"):
        status = "REVISAR"
    return {
        "validacao_magnetica": status,
        "comentario_validacao": str(raw.get("comentario_validacao") or "").strip(),
        "alerta_risco": str(raw.get("alerta_risco") or "").strip(),
    }


def validate_audit_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Modo 2: auditoria de calculo suspeito."""
    from config.api_manager import get_gemini_api_manager

    mgr = get_gemini_api_manager()
    raw = mgr.call_json(_prompt_audit_suspeito(payload))
    status = str(raw.get("status_auditoria") or "CORRIGIR").strip().upper()
    return {
        "status_auditoria": status,
        "nota_confianca_0_100": int(raw.get("nota_confianca_0_100") or 0),
        "comentario": str(raw.get("comentario") or "").strip(),
        "alerta_risco": str(raw.get("alerta_risco") or "").strip(),
    }


def comment_caixa_preta_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Parecer IA sobre candidatos caixa preta (opcional)."""
    from config.api_manager import get_gemini_api_manager

    mgr = get_gemini_api_manager()
    return mgr.call_json(_prompt_caixa_preta(payload))


def justify_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Compat: delega para validacao magnetica."""
    gem = validate_magnetic_with_gemini(payload)
    return {
        "justificativa_tecnica": gem.get("comentario_validacao", ""),
        "alerta_risco": gem.get("alerta_risco", ""),
        "validacao_magnetica": gem.get("validacao_magnetica", ""),
    }


def validate_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_magnetic_with_gemini(payload)


def get_agent_system_prompt() -> str:
    """System prompt exportado para agente do site / documentacao."""
    return get_system_prompt_digital_twin()


def _prompt_topologia_base_engenharia(payload: dict[str, Any]) -> str:
    estator = json.dumps(payload.get("estator_entrada", {}), ensure_ascii=False, indent=2)
    norte = json.dumps(payload.get("norte_validacao_usuario", {}), ensure_ascii=False, indent=2)
    resumo = json.dumps(payload.get("resumo_acervo", {}), ensure_ascii=False, indent=2)
    amostra = json.dumps(payload.get("amostra_registros", []), ensure_ascii=False, indent=2)
    n_amostra = payload.get("n_amostra", 0)
    return (
        SYSTEM_PROMPT_DIGITAL_TWIN
        + "\n\nCAMADA 1 — TOPOLOGIA DE BASE (contexto acervo; priorize fisica sobre media contaminada):\n\n"
        f"ENTRADA DO ESTATOR:\n{estator}\n\n"
        f"mediana proporcional: {payload.get('media_proporcional')}\n"
        f"mediana historica: {payload.get('media_historica')}\n\n"
        "NORTE USUARIO (prioridade absoluta se existir):\n"
        f"{norte}\n\n"
        f"RESUMO ACERVO:\n{resumo}\n\n"
        f"AMOSTRA ({n_amostra} linhas):\n{amostra}\n\n"
        "Responda APENAS JSON:\n"
        "{\n"
        '  "espiras_topologia_base": <float>,\n'
        '  "awg_principal_sugerido": <numero ou null>,\n'
        '  "tipo_bobinagem_reconhecido": "<texto>",\n'
        '  "comentario_topologia": "<2-4 frases>",\n'
        '  "confianca_0_100": <int>\n'
        "}\n"
    )


def propose_topology_base_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Camada 1: IA propoe topologia base a partir de contexto bruto + estator.
    O motor determinístico aplica depois as travas em winding_sanity.
    """
    from config.api_manager import get_gemini_api_manager

    mgr = get_gemini_api_manager()
    raw = mgr.call_json(_prompt_topologia_base_engenharia(payload))
    if not isinstance(raw, dict):
        raise ValueError("Resposta Gemini topologia nao e objeto JSON.")
    esp = raw.get("espiras_topologia_base")
    try:
        if esp is None:
            raise ValueError("espiras_topologia_base ausente")
        fe = float(esp)
        if fe <= 0:
            raise ValueError("espiras invalidas")
    except (TypeError, ValueError):
        raise ValueError("Campo espiras_topologia_base invalido na resposta.")
    raw["espiras_topologia_base"] = fe
    return raw

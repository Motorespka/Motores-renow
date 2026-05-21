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

# --- System prompt base (agente do site) ---
SYSTEM_PROMPT_DIGITAL_TWIN = """
Voce e o engenheiro eletricista senior do gêmeo digital de motores (WEG/IEC).
Abandone heuristica estatistica pura. Toda decisao deve respeitar eletromagnetismo classico:

1. Saturacao: inducao magnetica B travada em 1,5 Tesla (nucleo silicio).
2. FEM: espiras por fase coerentes com tensao, frequencia 60 Hz, area de ferro e fator de bobinagem.
3. Fator de enchimento ff = area cobre / area ranhura: faixa 25-45%.
   - ff > 45%: IMPOSSIVEL — fio nao cabe.
   - ff < 25%: SUBDIMENSIONADO — perda de rendimento.
4. Densidade de corrente J = I / area cobre: faixa 3-7 A/mm² (ideal ~4 A/mm²).
5. Score 100% somente se J~4, ff~35% e B<=1,5 T simultaneamente.

Modos:
- CAIXA PRETA: estator vazio, sem placa — projetar do zero com visao + FEM + candidatos AWG.
- AUDITORIA: engenharia reversa de calculo suspeito — invalidar se violar ff ou J ou saturacao.
NAO altere numeros deterministicos do motor Python; comente riscos e coerencia fisica.
""".strip()


def _prompt_validacao_magnetica(payload: dict[str, Any]) -> str:
    entrada = json.dumps(payload.get("entrada", {}), ensure_ascii=False, indent=2)
    refs = json.dumps(payload.get("calculos_proporcionais", [])[:3], ensure_ascii=False, indent=2)
    fio_txt = payload.get("sugestao_fio_texto") or payload.get("sugestao_fio_awg")
    limites = payload.get("limites") or {
        "b_tesla": 1.5,
        "j_a_mm2": "3-7",
        "ff_pct": "25-45",
    }
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
        "RESULTADO FIXO (valide coerencia magnetica apenas):\n"
        f"  Espiras: {payload.get('sugestao_espira')}\n"
        f"  Fio: {fio_txt}\n"
        f"  Enchimento ranhura: {payload.get('slot_fill_actual')} / limite {payload.get('slot_fill_limit')}\n"
        f"  ff estimado: {payload.get('fill_factor_ff')}\n"
        f"  J estimado: {payload.get('current_density_j')} A/mm²\n"
        f"  Base do calculo: {payload.get('calculo_baseado_em', '')}\n\n"
        f"REFERENCIAS (amostra):\n{refs}\n\n"
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
    return (
        SYSTEM_PROMPT_DIGITAL_TWIN
        + "\n\nMODO AUDITORIA — calculo suspeito (motor queimando, sem forca).\n"
        "Engenharia reversa critica: compare calculo do usuario vs limites fisicos.\n\n"
        f"LIMITES: {limites}\n\n"
        f"ENTRADA MOTOR:\n{entrada}\n\n"
        f"AUDITORIA USUARIO (suspeito):\n{aud_u}\n\n"
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


def validate_magnetic_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Gemini como validador tecnico — temperatura 0.1 no api_manager."""
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
    return SYSTEM_PROMPT_DIGITAL_TWIN


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

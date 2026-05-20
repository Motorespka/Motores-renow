#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validador magnético via Gemini — nunca altera espiras nem fio calculados."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _prompt_validacao_magnetica(payload: dict[str, Any]) -> str:
    return f"""Voce e um engenheiro eletricista especialista em rebobinagem de motores.
Sua funcao e APENAS validar se o resultado deterministico faz sentido magnetico.
NAO altere, NAO recalcule e NAO sugira novos numeros de espiras ou AWG.

FORMULA JA APLICADA (fonte da verdade):
  N_novo = N_hist * (L_novo/L_hist) * (A_novo/A_hist)
  Lei da ranhura: (Espiras * Secao_Fio) <= limite historico; se espiras sobem, bitola deve cair.

ENTRADA:
{json.dumps(payload.get("entrada", {}), ensure_ascii=False, indent=2)}

RESULTADO FIXO (valide coerencia magnetica apenas):
  Espiras: {payload.get("sugestao_espira")}
  Fio: {payload.get("sugestao_fio_texto") or payload.get("sugestao_fio_awg")}
  Media proporcional: {payload.get("media_proporcional_espiras")}
  Media historica: {payload.get("media_historica_espiras")}
  Enchimento ranhura: {payload.get("slot_fill_actual')} / limite {payload.get("slot_fill_limit")}
  Base do calculo: {payload.get("calculo_baseado_em", "")}
  Estimativa (referencia parcial): {payload.get("is_estimativa", False)}
  Interpolacao proporcional solicitada: {payload.get("interpolacao_proporcional", False)}

REFERENCIAS (amostra):
{json.dumps(payload.get("calculos_proporcionais", [])[:3], ensure_ascii=False, indent=2)}

Responda APENAS JSON:
{{
  "validacao_magnetica": "OK" ou "REVISAR",
  "comentario_validacao": "<1-3 frases: densidade de fluxo, relacao espiras/fio, ranhura>",
  "alerta_risco": "<vazio se OK; senao alerta fisico sem alterar numeros>"
}}
"""


def validate_magnetic_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Gemini como validador tecnico — temperatura 0.1 no api_manager."""
    from config.api_manager import get_gemini_api_manager

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


def _prompt_topologia_base_engenharia(payload: dict[str, Any]) -> str:
    return f"""Voce e engenheiro eletrico senior em rebobinagem reversa.

CAMADA 1 — TOPOLOGIA DE BASE (proposta primaria antes de travar em leis fisicas locais):

Tarefa principal: ler o CONTEXTO BRUTO DO ACERVO amostrad abaixo (subconjunto estratificado).
Ignore medias contaminadas baixas (ex.: registros duvidosos com ~8 espiras em motores grandes de 4/6 polos).
De prioridade aos padroes de bobinagem plausivelmente corretos (ex.: familia ~40-45 esp em carcaca ~80 tipo 80A,
4 ou 6 polos; para 2 polos em ferro medio a tendencia pode ser menor MAS deve ser fisicamente plausivel — nunca
aceite outliers obvios de cadastro se o cluster principal do acervo sugere bem mais espiras equivalentes por ranhura).

ENTRADA DO ESTATOR QUE SE DESEJA PROJETAR:
{json.dumps(payload.get("estator_entrada", {}), ensure_ascii=False, indent=2)}

METADADOS ESTATISTICOS (nao usar como obrigacao literal; apenas triagem rapida — confie mais no padrao observado nas linhas crus):
mediana proporcional atual: {payload.get('media_proporcional')}
mediana historica atual (podera estar contaminada): {payload.get('media_historica')}

NORTE PARA CALCULO (se existir é prioridade ABSOLUTA para espiras-base e deve orientar escolha de bitola e enchimento de ranhura coerente):
{json.dumps(payload.get("norte_validacao_usuario", {}), ensure_ascii=False, indent=2)}

RESUMO DO ACERVO:
{json.dumps(payload.get("resumo_acervo", {}), ensure_ascii=False, indent=2)}

AMOSTRA DE REGISTROS (contexto bruto — max {payload.get('n_amostra', 0)} linhas):
{json.dumps(payload.get("amostra_registros", []), ensure_ascii=False, indent=2)}

Responda APENAS JSON valido com:
{{
  "espiras_topologia_base": <numero float plausivel para camada 1 — se houver NORTE do usuario, use exatamente esse valor>,
  "awg_principal_sugerido": <numero ou null>,
  "tipo_bobinagem_reconhecido": "<texto curto ou vazio>",
  "comentario_topologia": "<2-4 frases: por que escolheu esse padrao em relacao ao contexto bruto>",
  "confianca_0_100": <int 0-100>
}}
"""


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

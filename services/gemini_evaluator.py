#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Juiz neuro-simbólico — escolhe o candidato de rebobinagem menos pior via Gemini.

A física (J, ff, B) é calculada deterministicamente; o LLM apenas pondera trade-offs.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

SYSTEM_PROMPT_ENGINEERING_JUDGE = """\
Você é um Engenheiro Eletricista Sênior especialista em rebobinagem de motores elétricos.
Sua tarefa é analisar uma lista de configurações candidatas para um estator e escolher a 'menos pior' ou a mais viável para a bancada, baseando-se nestas regras de ouro:

1. Densidade de Corrente (J): Ideal é ~4.0 A/mm². Acima de 6.0 A/mm² o motor sofre risco crítico de superaquecimento (Efeito Joule). É o limite mais perigoso.
2. Fator de Enchimento (ff): Ideal é 30-40%. Acima de 45%, o fio fisicamente não cabe na ranhura. Um bobinador excepcional consegue até 48%, mas é risco de produção.
3. Saturação Magnética (B): Acima de 1.5T o núcleo satura, derrubando o rendimento.

Trade-offs permitidos:
- É preferível ter um 'ff' levemente alto (ex: 46% - difícil de colocar na ranhura) do que um 'J' alto (ex: 6.8 - vai queimar o motor).
- Fios em paralelo podem ser sugeridos na justificativa se o AWG ideal for grosso demais.

Analise os candidatos e retorne um JSON com a seguinte estrutura:
{
  "status": "APROVADO" | "APROVADO_COM_RESSALVAS" | "INVIÁVEL",
  "best_candidate_index": int (índice da lista fornecida),
  "engineering_justification": "Explicação técnica sucinta do porquê esta foi a melhor escolha ou por que todas falham (ex: pacote pequeno para a potência)."
}
"""

_VALID_STATUSES = frozenset({"APROVADO", "APROVADO_COM_RESSALVAS", "INVIÁVEL"})


def _api_key() -> str:
    try:
        import streamlit as st

        for name in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
            try:
                val = st.secrets.get(name) if hasattr(st.secrets, "get") else st.secrets[name]
            except (KeyError, TypeError, AttributeError):
                val = None
            if val:
                return str(val).strip()
    except Exception:
        pass
    return (
        os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or ""
    ).strip()


def _model_name() -> str:
    return (os.environ.get("GEMINI_MODEL") or "gemini-2.0-flash").strip()


def combined_j_ff_error(candidate: dict[str, Any]) -> float:
    """Erro combinado J + ff para fallback determinístico (menor = melhor)."""
    j = float(candidate.get("j_a_mm2") or 99.0)
    ff_raw = candidate.get("ff")
    ff = float(ff_raw) if ff_raw is not None else 0.99
    if ff > 1.0:
        ff = ff / 100.0
    j_penalty = max(0.0, j - 4.0) * 2.0 + max(0.0, 6.0 - j) * 0.05
    if j > 6.0:
        j_penalty += (j - 6.0) * 3.0
    ff_penalty = max(0.0, ff - 0.40) * 1.5 + max(0.0, ff - 0.45) * 4.0
    b = candidate.get("b_tesla")
    b_penalty = max(0.0, float(b or 0) - 1.5) * 5.0 if b is not None else 0.0
    return round(j_penalty + ff_penalty + b_penalty, 6)


def deterministic_candidate_fallback(
    candidates: list[dict[str, Any]],
    *,
    reason: str = "",
) -> dict[str, Any]:
    """Escolhe o candidato com menor erro combinado J/ff quando Gemini falha."""
    if not candidates:
        return {
            "status": "INVIÁVEL",
            "best_candidate_index": -1,
            "engineering_justification": reason or "Nenhum candidato físico gerado para o estator.",
            "source": "deterministic_fallback",
            "fallback": True,
        }
    ranked = sorted(
        enumerate(candidates),
        key=lambda item: combined_j_ff_error(item[1]),
    )
    best_idx, best = ranked[0]
    err = combined_j_ff_error(best)
    j = float(best.get("j_a_mm2") or 0)
    ff_raw = best.get("ff")
    ff_pct = float(ff_raw) * 100 if ff_raw is not None and float(ff_raw) <= 1 else float(ff_raw or 0)

    if err > 8.0 or j > 8.0:
        status = "APROVADO_COM_RESSALVAS"
        just = (
            reason
            or f"Todas as configurações excedem limites críticos. "
            f"Melhor tentativa: {best.get('espiras')} esp × AWG {best.get('awg')} "
            f"(J={j:.2f} A/mm², ff={ff_pct:.1f}%)."
        )
    elif err > 2.5 or j > 6.0 or (ff_raw is not None and float(ff_raw) > 0.45):
        status = "APROVADO_COM_RESSALVAS"
        just = (
            reason
            or f"Fallback determinístico: candidato {best_idx} "
            f"({best.get('espiras')} esp, AWG {best.get('awg')}) com menor penalidade J/ff."
        )
    else:
        status = "APROVADO"
        just = (
            reason
            or f"Fallback determinístico: candidato {best_idx} dentro da faixa operacional."
        )

    return {
        "status": status,
        "best_candidate_index": best_idx,
        "engineering_justification": just,
        "source": "deterministic_fallback",
        "fallback": True,
        "combined_error": err,
    }


def _extract_json(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}
    return {}


def _normalize_evaluation(
    data: dict[str, Any],
    *,
    n_candidates: int,
    source: str,
    fallback: bool = False,
) -> dict[str, Any]:
    status = str(data.get("status") or "INVIÁVEL").upper().replace(" ", "_")
    if status not in _VALID_STATUSES:
        if "RESSALV" in status:
            status = "APROVADO_COM_RESSALVAS"
        elif "APROV" in status:
            status = "APROVADO"
        else:
            status = "INVIÁVEL"
    try:
        idx = int(data.get("best_candidate_index", -1))
    except (TypeError, ValueError):
        idx = -1
    if status != "INVIÁVEL" and (idx < 0 or idx >= n_candidates):
        idx = 0 if n_candidates else -1
    if status == "INVIÁVEL":
        idx = -1
    return {
        "status": status,
        "best_candidate_index": idx,
        "engineering_justification": str(
            data.get("engineering_justification") or ""
        ).strip(),
        "source": source,
        "fallback": fallback,
    }


def evaluate_candidate_pool_with_gemini(
    candidates: list[dict[str, Any]],
    stator_info: dict[str, Any],
    *,
    timeout_s: float = 25.0,
) -> dict[str, Any]:
    """
    Etapa 2 — Juiz LLM sobre candidatos já calculados deterministicamente.
    Fallback robusto para menor erro J/ff se API indisponível.
    """
    if not candidates:
        return deterministic_candidate_fallback(candidates)

    api_key = _api_key()
    if not api_key:
        return deterministic_candidate_fallback(
            candidates, reason="API Key ausente (GOOGLE_API_KEY / GEMINI_API_KEY)."
        )

    payload = {
        "stator": stator_info,
        "candidates": [
            {
                "index": c.get("index", i),
                "espiras": c.get("espiras"),
                "awg": c.get("awg"),
                "parallel_count": c.get("parallel_count", 1),
                "fio_texto": c.get("fio_texto"),
                "j_a_mm2": c.get("j_a_mm2"),
                "ff_pct": round(float(c.get("ff") or 0) * 100, 2)
                if c.get("ff") is not None and float(c.get("ff") or 0) <= 1
                else c.get("ff"),
                "b_tesla": c.get("b_tesla"),
                "physics_confidence": c.get("physics_confidence"),
                "violations": c.get("violations") or [],
            }
            for i, c in enumerate(candidates)
        ],
    }
    user_prompt = (
        "Analise os candidatos abaixo e responda SOMENTE com JSON válido.\n\n"
        f"DADOS DO ESTATOR:\n{json.dumps(stator_info, ensure_ascii=False, indent=2)}\n\n"
        f"CANDIDATOS:\n{json.dumps(payload['candidates'], ensure_ascii=False, indent=2)}"
    )

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        gen_cfg: dict[str, Any] = {
            "temperature": 0.15,
            "response_mime_type": "application/json",
        }
        model = genai.GenerativeModel(
            _model_name(),
            system_instruction=SYSTEM_PROMPT_ENGINEERING_JUDGE,
            generation_config=gen_cfg,
        )
        response = model.generate_content(user_prompt, request_options={"timeout": timeout_s})
        text = getattr(response, "text", None) or ""
        parsed = _extract_json(text)
        if not parsed:
            return deterministic_candidate_fallback(
                candidates, reason="Gemini retornou JSON inválido."
            )
        return _normalize_evaluation(
            parsed, n_candidates=len(candidates), source="gemini", fallback=False
        )
    except Exception as exc:
        return deterministic_candidate_fallback(
            candidates,
            reason=f"Gemini indisponível ({type(exc).__name__}): fallback determinístico.",
        )

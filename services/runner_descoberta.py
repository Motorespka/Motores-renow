from __future__ import annotations

import logging
from typing import Any, Dict

import streamlit as st
from supabase import create_client

from services.descoberta_automatica import executar_descoberta_automatica

logger = logging.getLogger(__name__)


def _init_supabase() -> Any:
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL/SUPABASE_KEY não configurados em st.secrets")
    return create_client(url, key)


def executar_runner_descoberta() -> Dict[str, Any]:
    """
    Runner manual e seguro para atualização da inteligência técnica.

    Fluxo:
      1) conecta ao Supabase
      2) executa descoberta automática
      3) registra logs das descobertas encontradas

    Este runner não é executado automaticamente na inicialização do site.
    """
    try:
        supabase = _init_supabase()
        resumo = executar_descoberta_automatica(supabase)

        total = resumo.get("total_descobertas", 0)
        logger.info("[descoberta_runner] total_descobertas=%s", total)

        for item in resumo.get("descobertas", []):
            logger.info(
                "[descoberta_runner] padrao=%s | confianca=%s | amostras=%s | calculo=%s",
                item.get("padrao"),
                item.get("nivel_confianca"),
                item.get("amostras"),
                item.get("calculo_inferido"),
            )

        return {"ok": True, "resumo": resumo}
    except Exception as exc:
        logger.exception("[descoberta_runner] erro ao executar descoberta automática")
        return {"ok": False, "erro": str(exc)}

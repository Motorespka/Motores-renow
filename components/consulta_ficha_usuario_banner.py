"""Banner único: ficha pronta para consulta pública (view Supabase) vs. incompleta."""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st


def _to_bool(value: Any) -> bool | None:
    if value is True or value is False:
        return bool(value)
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
        return None
    txt = str(value).strip().lower()
    if txt in {"true", "t", "1", "yes", "y", "sim"}:
        return True
    if txt in {"false", "f", "0", "no", "n", "nao", "não"}:
        return False
    return None


def pick_consulta_validacao(row: Dict[str, Any]) -> tuple[bool | None, str]:
    """
    Lê colunas da view ``vw_motores_para_site_validacao`` / ``vw_motores_consulta_enriquecida``.
    Retorna (pronto_ou_none, mensagem_ou_vazio).
    """
    pronto = _to_bool(row.get("consulta_pronto_usuario"))
    if pronto is None:
        pronto = _to_bool(row.get("ConsultaProntoUsuario"))

    msg = ""
    for key in ("ConsultaMensagemUsuarioPt", "consulta_mensagem_usuario_pt"):
        raw = row.get(key)
        if raw is not None and str(raw).strip():
            msg = str(raw).strip()
            break

    return pronto, msg


def render_consulta_ficha_usuario_banner(row: Dict[str, Any]) -> None:
    """
    Mostra aviso/sucesso alinhado ao SQL do Supabase. Se as colunas não existem, não renderiza.
    """
    pronto, msg = pick_consulta_validacao(row)
    if pronto is None and not msg:
        return

    if pronto is True:
        st.success(msg or "Ficha com dados mínimos verificados para esta consulta.")
        return

    if pronto is False:
        st.warning(msg or "Ficha incompleta: confira os valores na oficina antes de usar como referência.")
        return

    if msg:
        st.info(msg)

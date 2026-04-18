"""UI read-only — rebobinagem (linha leve na consulta; painel completo opcional)."""

from __future__ import annotations

import html
import json
from typing import Any, Dict

import streamlit as st

from services.motor_inteligencia.coercion import coerce_supabase_motor_row
from services.motor_rebobinagem import analyze_rewinding_coherence, rebobinagem_status_color
from services.motor_rebobinagem.serialization import prepare_fastapi_rebobinagem_payload


def _payload(raw_or_row: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(raw_or_row, dict) and (
        "dados_tecnicos_json" in raw_or_row
        or "rpm_nominal" in raw_or_row
        or "potencia_hp_cv" in raw_or_row
    ):
        return coerce_supabase_motor_row(raw_or_row)
    return raw_or_row


def _badge(status: str) -> str:
    color = rebobinagem_status_color(status)
    fg = "#ffffff" if status in ("critico", "alerta", "ok") else "#f8fafc"
    return (
        f'<span style="display:inline-block;margin:2px 8px 0 0;padding:4px 10px;'
        f"border-radius:999px;background:{color};color:{fg};font-weight:600;font-size:0.78rem;"
        f'">Rebob.: {html.escape(status)}</span>'
    )


def render_rebobinagem_consulta_inline(raw_or_row: Dict[str, Any], *, key_prefix: str = "rbq") -> None:
    try:
        rep = analyze_rewinding_coherence(_payload(raw_or_row))
    except Exception:
        return
    val = rep.get("validation") or {}
    status = str(val.get("status") or "insuficiente")
    line = str(rep.get("summary_one_liner") or "")[:130]
    st.markdown(f'<div class="rebob-inline">{_badge(status)}</div>', unsafe_allow_html=True)
    if line:
        st.caption(line)


def render_rebobinagem_json_download_button(
    raw_or_row: Dict[str, Any],
    *,
    key_prefix: str = "rb",
    label: str = "Baixar análise rebobinagem (JSON)",
) -> None:
    """Fora de `st.form()` — Streamlit não permite `st.download_button` dentro de forms."""
    try:
        rep = analyze_rewinding_coherence(_payload(raw_or_row))
    except Exception as exc:
        st.warning(f"Análise de rebobinagem indisponível: {exc}")
        return
    st.download_button(
        label,
        data=json.dumps(prepare_fastapi_rebobinagem_payload(rep), ensure_ascii=False, indent=2),
        file_name=f"{key_prefix}_rebobinagem.json",
        mime="application/json",
        key=f"{key_prefix}_dl_rb",
    )


def render_rebobinagem_panel(
    raw_or_row: Dict[str, Any],
    *,
    key_prefix: str = "rb",
    title: str = "Inteligência de rebobinagem (read-only)",
    expanded_json: bool = False,
    show_download: bool = True,
) -> None:
    try:
        rep = analyze_rewinding_coherence(_payload(raw_or_row))
    except Exception as exc:
        st.warning(f"Análise de rebobinagem indisponível: {exc}")
        return
    st.subheader(title)
    val = rep.get("validation") or {}
    status = str(val.get("status") or "insuficiente")
    st.markdown(f'<div>{_badge(status)}</div>', unsafe_allow_html=True)
    st.caption(rep.get("summary_one_liner") or "")
    st.write(rep.get("summary") or "")
    with st.expander("Detalhe (JSON)", expanded=expanded_json):
        slim = {
            "validation": val,
            "signature": rep.get("signature"),
            "similarity_query": rep.get("similarity_query"),
            "future_calculations": rep.get("future_calculations"),
        }
        st.json(slim, expanded=False)
        if show_download:
            st.download_button(
                "Baixar análise rebobinagem (JSON)",
                data=json.dumps(prepare_fastapi_rebobinagem_payload(rep), ensure_ascii=False, indent=2),
                file_name=f"{key_prefix}_rebobinagem.json",
                mime="application/json",
                key=f"{key_prefix}_dl_rb",
            )
        else:
            st.caption(
                "Use o botao 'Baixar JSON rebobinagem' abaixo do formulario "
                "(Streamlit nao permite download dentro do form)."
            )

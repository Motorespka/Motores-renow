#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo calculo proporcional + Gemini sobre acervo OFICIAL (Streamlit)."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from app.oficial_engine import suggest_calculation
from app.search_lib import DEFAULT_DB, connect, load_all_motors
from core.access_control import require_admin_access
from core.navigation import Route
from core.streamlit_perf import maybe_fragment, pop_page_ctx_pack, stash_page_ctx
from core.ui_feedback import mrw_render_banner_zone
from services.acervo_oficial_stats import load_acervo_stats
from services.demo_calculo_report import build_report_html


@st.dialog("Prévia do Relatório de Engenharia", width="large")
def _report_preview_dialog() -> None:
    entrada = st.session_state.get("demo_calculo_entrada") or {}
    res = st.session_state.get("demo_calculo_result") or {}
    html_doc = st.session_state.get("demo_calculo_report_html") or build_report_html(
        entrada=entrada, result=res
    )
    ref = datetime.now(timezone.utc).strftime("PRE-%Y%m%d-%H%M%S")
    st.caption(
        "Somente visualização — não grava cadastro, manifesto nem banco. "
        "Use **Imprimir / Salvar PDF** no documento abaixo ou baixe o HTML."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Baixar HTML",
            data=html_doc,
            file_name=f"previa-rebobinagem-{ref}.html",
            mime="text/html",
            use_container_width=True,
            key="demo_report_download",
        )
    with c2:
        if st.button("Fechar", use_container_width=True, key="demo_report_close"):
            st.rerun()
    components.html(html_doc, height=780, scrolling=True)


@st.cache_resource
def _catalog():
    conn = connect(DEFAULT_DB)
    motors = load_all_motors(conn)
    meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM index_meta").fetchall()}
    conn.close()
    return motors, meta


def _render_stats_bar() -> None:
    acervo = load_acervo_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("OFICIAIS (manifest)", acervo.get("oficial_manifest", 0))
    c2.metric("No indice SQLite", acervo.get("indexed_total", 0))
    c3.metric("Registros completos (file)", acervo.get("file_complete", 0))
    c4.metric("Indice gerado em", acervo.get("index_generated_at", "—")[:10] or "—")
    if not Path(DEFAULT_DB).is_file():
        st.error(
            "Indice local ausente. No servidor, rode: `python scripts/index_for_search.py` "
            "ou confirme que `data/oficial_search.sqlite` esta no deploy."
        )


def _render_form(ctx) -> None:
    st.markdown("### Entrada do motor")
    c1, c2, c3 = st.columns(3)
    with c1:
        diametro = st.text_input("Diametro estator (mm)", value="80", key="demo_diam")
    with c2:
        pacote = st.text_input("Comprimento pacote (mm)", value="70", key="demo_pac")
    with c3:
        carcaca = st.text_input("Carcaça NEMA/IEC", value="80A", key="demo_carc")
    c4, c5 = st.columns(2)
    with c4:
        passo = st.text_input("Passos bobinagem", value="1:7", key="demo_passo")
    with c5:
        ligacao = st.text_input("Tipo de ligacao", value="Estrela", key="demo_lig")

    st.markdown("### Seu calculo (validacao)")
    e1, e2 = st.columns(2)
    with e1:
        fio_eng = st.text_input("Fio AWG", value="23", key="demo_fio")
    with e2:
        esp_eng = st.text_input("Espiras", value="", key="demo_esp")

    if st.button("Gerar Sugestao de Calculo", type="primary", use_container_width=True):
        try:
            d = float(str(diametro).replace(",", "."))
            p = float(str(pacote).replace(",", "."))
        except ValueError:
            st.warning("Informe diametro e pacote numericos.")
            return
        if d <= 0 or p <= 0:
            st.warning("Diametro e pacote devem ser maiores que zero.")
            return
        try:
            motors, _ = _catalog()
        except FileNotFoundError as exc:
            st.error(str(exc))
            return
        with st.spinner("Calculando proporcao e consultando Gemini..."):
            sug = suggest_calculation(
                motors,
                diametro_mm=d,
                pacote_mm=p,
                carcaca=carcaca,
                passo=passo,
                ligacao=ligacao,
                fio_engenheiro=fio_eng,
                espiras_engenheiro=esp_eng,
                top_k=5,
                use_gemini=True,
            )
        st.session_state["demo_calculo_result"] = asdict(sug)
        st.session_state["demo_calculo_entrada"] = {
            "diametro_mm": d,
            "pacote_mm": p,
            "carcaca": carcaca,
            "passo": passo,
            "ligacao": ligacao,
            "fio_engenheiro": fio_eng,
            "espiras_engenheiro": esp_eng,
        }

    res = st.session_state.get("demo_calculo_result")
    if not res:
        return

    st.divider()
    st.markdown("### Prévia de relatório (bancada)")
    if st.button(
        "Visualizar Relatório",
        type="secondary",
        use_container_width=True,
        key="demo_btn_visualizar_relatorio",
        help="Abre documento A4 para impressão ou print — não salva no banco.",
    ):
        entrada = st.session_state.get("demo_calculo_entrada") or {
            "diametro_mm": diametro,
            "pacote_mm": pacote,
            "carcaca": carcaca,
            "passo": passo,
            "ligacao": ligacao,
            "fio_engenheiro": fio_eng,
            "espiras_engenheiro": esp_eng,
        }
        st.session_state["demo_calculo_report_html"] = build_report_html(
            entrada=entrada, result=res
        )
        _report_preview_dialog()

    a, b, c = st.columns(3)
    with a:
        st.markdown("#### Sugestao do Sistema")
        st.metric("Espiras (IA + proporcional)", res.get("sugestao_espira", "—"))
        st.metric("Fio AWG sugerido", res.get("sugestao_fio_awg", "—"))
        st.caption(f"Modo: **{res.get('modo_processamento', '')}** · Gemini: **{'Sim' if res.get('gemini_usado') else 'Nao'}**")
        st.write(res.get("justificativa_tecnica") or "")
        if res.get("alerta_risco"):
            st.warning(res.get("alerta_risco"))
        st.caption(f"Media proporcional (ref.): {res.get('espiras_media_top5', '—')} espiras")
    with b:
        st.markdown("#### Sua Entrada")
        st.write(f"Estator: **{diametro}** x **{pacote}** mm")
        st.write(f"Carcaça: **{carcaca}** · Passo: **{passo}** · Ligacao: **{ligacao}**")
        st.write(f"Fio: **{fio_eng or '—'}** · Espiras: **{esp_eng or '—'}**")
    with c:
        st.markdown("#### Validacao")
        st.markdown(f"**{res.get('validation_status', '—')}**")
        st.write(res.get("validation_message") or "")

    matches = res.get("top_matches") or []
    if matches:
        st.markdown("#### Top 5 — formula proporcional aplicada")
        st.caption(
            "Espiras_calc = Espiras_hist × (Pacote_in/Pacote_hist) × (Area_in/Area_hist). "
            "**Nunca** copia espiras do historico sem recalcular."
        )
        st.dataframe(
            [
                {
                    "arquivo": (m.get("arquivo_rel") or "")[:48],
                    "diam_hist": m.get("diametro_mm"),
                    "pac_hist": m.get("pacote_mm"),
                    "esp_hist": m.get("espiras_historico"),
                    "esp_calc": m.get("espiras_calculadas"),
                    "R_pacote": m.get("pacote_ratio"),
                    "R_area": m.get("area_ratio"),
                    "score": round(float(m.get("score", 0)), 3),
                }
                for m in matches
            ],
            use_container_width=True,
            hide_index=True,
        )

    if st.button("Salvar Novo Calculo Oficial", use_container_width=True):
        from app.oficial_engine import save_official_calculation

        try:
            d_save = float(str(diametro).replace(",", "."))
            p_save = float(str(pacote).replace(",", "."))
            saved = save_official_calculation(
                {
                    "diametro_mm": d_save,
                    "pacote_mm": p_save,
                    "carcaca": carcaca,
                    "passo": passo,
                    "ligacao": ligacao,
                    "fio_principal": fio_eng or str(res.get("sugestao_fio_awg") or ""),
                    "espiras_principal": esp_eng or str(res.get("sugestao_espira") or ""),
                    "observacoes": "Salvo via Streamlit demo-calculo",
                }
            )
            st.success(f"Gravado no manifesto OFICIAL. SHA: {saved['sha256_arquivo'][:16]}…")
            _catalog.clear()
        except Exception as exc:
            st.error(f"Falha ao salvar: {exc}")


@maybe_fragment
def _demo_calculo_fragment() -> None:
    mrw_render_banner_zone()
    ctx = pop_page_ctx_pack().get("ctx")
    if ctx is None:
        return
    _render_stats_bar()
    _render_form(ctx)


def show(ctx) -> None:
    if not require_admin_access("Demo calculo (acervo oficial)", client=ctx.supabase):
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return
    stash_page_ctx(ctx)
    _demo_calculo_fragment()


def render(ctx) -> None:
    show(ctx)

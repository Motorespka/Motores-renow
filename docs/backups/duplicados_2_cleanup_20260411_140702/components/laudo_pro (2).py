from __future__ import annotations

import streamlit as st

from services.laudo_pro import LaudoTecnico


def _text(value: str | None) -> str:
    return str(value or "-").strip() or "-"


def render_laudo_tecnico(laudo: LaudoTecnico) -> None:
    st.markdown(f"## {laudo.titulo}")
    st.caption(f"Emitido em: {laudo.emitido_em}")

    if laudo.empresa_nome:
        st.info(f"Empresa: {laudo.empresa_nome}")

    with st.container(border=True):
        st.markdown("### Identificacao do motor")
        col1, col2, col3 = st.columns(3)
        col1.write(f"**Fabricante:** {_text(laudo.identificacao.fabricante)}")
        col1.write(f"**Modelo:** {_text(laudo.identificacao.modelo)}")
        col1.write(f"**Potencia:** {_text(laudo.identificacao.potencia)}")
        col2.write(f"**RPM:** {_text(laudo.identificacao.rpm)}")
        col2.write(f"**Tensao:** {_text(laudo.identificacao.tensao)}")
        col2.write(f"**Corrente:** {_text(laudo.identificacao.corrente)}")
        col3.write(f"**Polos:** {_text(laudo.identificacao.polos)}")
        col3.write(f"**Frequencia:** {_text(laudo.identificacao.frequencia)}")
        col3.write(f"**Fase:** {_text(laudo.identificacao.fase)}")

    with st.container(border=True):
        st.markdown("### Resumo executivo")
        st.write(f"**Status geral:** {_text(laudo.status_geral)}")
        if laudo.nivel_confianca:
            st.write(f"**Nivel de confianca:** {_text(laudo.nivel_confianca)}")
        st.write(_text(laudo.resumo_executivo))

    if laudo.pontos_atencao:
        with st.container(border=True):
            st.markdown("### Pontos de atencao")
            for item in laudo.pontos_atencao:
                st.write(f"- {item}")

    with st.container(border=True):
        st.markdown("### Analise tecnica")
        if laudo.analise_bobinagem:
            st.write(f"**Bobinagem:** {_text(laudo.analise_bobinagem)}")
        if laudo.analise_tensao_corrente:
            st.write(f"**Tensao/Corrente:** {_text(laudo.analise_tensao_corrente)}")
        if laudo.analise_compatibilidade:
            st.write(f"**Compatibilidade:** {_text(laudo.analise_compatibilidade)}")
        if laudo.analise_incoerencias:
            st.write(f"**Incoerencias:** {_text(laudo.analise_incoerencias)}")

    if laudo.acoes_recomendadas:
        with st.container(border=True):
            st.markdown("### Acao recomendada")
            for acao in laudo.acoes_recomendadas:
                st.write(f"- {acao}")

    st.caption(_text(laudo.observacao_final))


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo local: comparar calculo do engenheiro com sugestao do acervo OFICIAL (1.062+).

Uso (na raiz Motores-renow):
  python scripts/index_for_search.py
  streamlit run app/demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.search_lib import (  # noqa: E402
    DEFAULT_DB,
    build_suggestion,
    connect,
    find_similar,
    load_all_motors,
    parse_mm,
    validate_calculation,
)

st.set_page_config(
    page_title="Demo — Calculo vs Acervo Oficial",
    page_icon="⚡",
    layout="wide",
)

STATUS_COLORS = {
    "APROVADO": "green",
    "REVISAR": "orange",
    "ATENCAO": "red",
    "SEM_REFERENCIA": "gray",
    "INCOMPLETO": "gray",
}


@st.cache_resource
def _load_motors():
    conn = connect(DEFAULT_DB)
    motors = load_all_motors(conn)
    meta = {
        r["key"]: r["value"]
        for r in conn.execute("SELECT key, value FROM index_meta").fetchall()
    }
    conn.close()
    return motors, meta


def main() -> None:
    st.title("Demo — Sugestao de calculo vs acervo oficial")
    st.caption(
        "Compara geometria (estator + carcaca + passo) com motores OFICIAIS indexados "
        "e valida fio/espiras do seu calculo diario."
    )

    try:
        motors, meta = _load_motors()
    except FileNotFoundError as e:
        st.error(str(e))
        st.code("python scripts/index_for_search.py", language="bash")
        return

    st.sidebar.markdown("### Acervo indexado")
    st.sidebar.metric("Motores no indice", len(motors))
    st.sidebar.metric("OFICIAIS (manifest)", meta.get("oficial_manifest_rows", "?"))
    st.sidebar.metric("Com geometria", meta.get("with_geometry", "?"))
    st.sidebar.caption(f"Indice: `{DEFAULT_DB.name}` · {meta.get('generated_at', '')}")

    col_geo, col_calc = st.columns(2)

    with col_geo:
        st.subheader("Geometria de referencia")
        c1, c2 = st.columns(2)
        with c1:
            diam_in = st.text_input("Estator — diametro (mm)", placeholder="Ex: 80")
        with c2:
            comp_in = st.text_input("Estator — comprimento pacote (mm)", placeholder="Ex: 70")
        carcaca_in = st.text_input("Carcaça (NEMA / IEC)", placeholder="Ex: 80A, 56, IEC90")
        passo_in = st.text_input("Passos de bobinagem", placeholder="Ex: 10-12 ou 1:7")

    with col_calc:
        st.subheader("Seu calculo (entrada)")
        fio_in = st.text_input("Fio principal (AWG)", placeholder="Ex: 23")
        esp_in = st.text_input("Espiras principal", placeholder="Ex: 35")
        passo_calc_in = st.text_input(
            "Passo no seu calculo (opcional se ja preencheu acima)",
            placeholder="Ex: 1:7",
        )

    gerar = st.button("Gerar Sugestao de Calculo", type="primary", use_container_width=True)

    if not gerar:
        st.info(
            "Preencha estator (diametro x comprimento), carcaca e passos, "
            "depois clique em **Gerar Sugestao de Calculo**."
        )
        return

    d_mm = parse_mm(diam_in)
    p_mm = parse_mm(comp_in)
    passo_query = (passo_in or passo_calc_in).strip()

    if d_mm is None and p_mm is None:
        st.warning("Informe ao menos diametro ou comprimento do estator em mm.")
        return

    matches = find_similar(
        motors,
        diametro_mm=d_mm,
        pacote_mm=p_mm,
        carcaca=carcaca_in,
        passo=passo_query,
    )
    suggestion = build_suggestion(matches)
    passo_user = passo_calc_in or passo_in
    validation = validate_calculation(
        suggestion,
        user_fio=fio_in,
        user_espiras=esp_in,
        user_passo=passo_user,
        diametro_mm=d_mm,
        pacote_mm=p_mm,
    )

    st.divider()
    c_sys, c_user, c_val = st.columns(3)

    with c_sys:
        st.subheader("Sugestao do Sistema")
        if not suggestion.matches:
            st.warning("Nenhum motor similar encontrado com os criterios informados.")
        else:
            st.markdown(
                f"**{len(suggestion.matches)}** registro(s) similar(es) "
                f"({suggestion.n_geom} com geometria completa)"
            )
            st.markdown(
                f"- Estator: **{suggestion.diametro_mm or '—'}** x "
                f"**{suggestion.pacote_mm or '—'}** mm"
            )
            st.markdown(f"- Carcaca (moda): **{suggestion.carcaca_mode or '—'}**")
            st.markdown(f"- Passo (moda): **{suggestion.passo_label or '—'}**")
            st.markdown(
                f"- Fio principal (mediana AWG): **{suggestion.fio_principal or '—'}**"
            )
            st.markdown(
                f"- Espiras principal (mediana): **{suggestion.espiras_principal or '—'}**"
            )
            if suggestion.fio_auxiliar:
                st.markdown(
                    f"- Fio auxiliar: **{suggestion.fio_auxiliar}** · "
                    f"Espiras: **{suggestion.espiras_auxiliar or '—'}**"
                )

    with c_user:
        st.subheader("Sua Entrada")
        st.markdown(f"- Estator: **{diam_in or '—'}** x **{comp_in or '—'}** mm")
        st.markdown(f"- Carcaca: **{carcaca_in or '—'}**")
        st.markdown(f"- Passos: **{passo_user or '—'}**")
        st.markdown(f"- Fio: **{fio_in or '—'}**")
        st.markdown(f"- Espiras: **{esp_in or '—'}**")

    with c_val:
        st.subheader("Status de Validacao")
        color = STATUS_COLORS.get(validation.status, "gray")
        st.markdown(
            f":{color}[**{validation.status}**]"
        )
        st.write(validation.message)
        for line in validation.details:
            st.caption(f"• {line}")

    if suggestion.matches:
        with st.expander("Motores oficiais mais proximos (top 15)"):
            rows = []
            for i, m in enumerate(suggestion.matches[:15], 1):
                mot = m.motor
                rows.append(
                    {
                        "#": i,
                        "score": round(m.score, 3),
                        "diam_mm": mot.diametro_mm,
                        "pacote_mm": mot.pacote_mm,
                        "carcaca": mot.carcaca,
                        "passo": mot.passo_principal,
                        "fio": mot.fio_principal,
                        "espiras": mot.espiras_principal,
                        "arquivo": mot.arquivo_rel[:60] + ("…" if len(mot.arquivo_rel) > 60 else ""),
                    }
                )
            st.dataframe(rows, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

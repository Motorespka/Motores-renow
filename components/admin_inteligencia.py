from __future__ import annotations

import streamlit as st

from services.runner_descoberta import executar_runner_descoberta


def render_admin_inteligencia_sidebar() -> None:
    """
    Painel admin opcional para disparo manual do runner de descoberta.
    """
    with st.sidebar.expander("Painel Admin", expanded=False):
        clicked = st.button(
            "Atualizar Inteligência Técnica",
            key="admin_atualizar_inteligencia_tecnica",
            use_container_width=True,
        )

        if clicked:
            with st.spinner("Atualizando inteligência técnica..."):
                st.session_state["admin_descoberta_resultado"] = executar_runner_descoberta()

        resultado = st.session_state.get("admin_descoberta_resultado")
        if not resultado:
            st.caption("Nenhuma execução manual realizada ainda.")
            return

        if not resultado.get("ok"):
            st.error(f"Falha ao executar runner: {resultado.get('erro', 'erro desconhecido')}")
            return

        resumo = resultado.get("resumo", {})
        st.success("Inteligência técnica atualizada com sucesso.")
        st.caption(f"Motores lidos: {resumo.get('total_motores_lidos', 0)}")
        st.caption(f"Descobertas encontradas: {resumo.get('total_descobertas', 0)}")

        for item in resumo.get("descobertas", []):
            st.markdown(
                "- **{padrao}** | confiança: `{conf}` | amostras: `{amostras}`\\n"
                "  cálculo: `{calc}`".format(
                    padrao=item.get("padrao", "n/d"),
                    conf=item.get("nivel_confianca", "n/d"),
                    amostras=item.get("amostras", "n/d"),
                    calc=item.get("calculo_inferido", "n/d"),
                )
            )

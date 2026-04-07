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
        st.caption(f"Motores Supabase: {resumo.get('total_motores_supabase', 0)}")
        st.caption(f"Registros extraídos de pastas/docs: {resumo.get('total_registros_docs', 0)}")
        st.caption(f"Imagens localizadas: {resumo.get('total_imagens_localizadas', 0)}")
        st.caption(f"Registros extraídos das imagens: {resumo.get('total_registros_imagens', 0)}")
        st.caption(f"Total analisado: {resumo.get('total_motores_lidos', 0)}")
        st.caption(f"Descobertas encontradas: {resumo.get('total_descobertas', 0)}")
        st.caption(f"Descobertas persistidas: {resumo.get('total_persistidas', 0)}")

        if resumo.get("tabela_descobertas_ausente"):
            st.warning("Tabela public.descobertas_ia não encontrada no Supabase. A análise foi feita, mas não foi persistida.")


        arquivos = resultado.get("arquivos_exportados", {})
        json_path = arquivos.get("json")
        csv_path = arquivos.get("csv")

        if json_path:
            with open(json_path, "rb") as jf:
                st.download_button(
                    "Baixar descobertas (JSON)",
                    data=jf.read(),
                    file_name=json_path.split("/")[-1],
                    mime="application/json",
                    use_container_width=True,
                    key="download_descobertas_json",
                )

        if csv_path:
            with open(csv_path, "rb") as cf:
                st.download_button(
                    "Baixar descobertas (CSV)",
                    data=cf.read(),
                    file_name=csv_path.split("/")[-1],
                    mime="text/csv",
                    use_container_width=True,
                    key="download_descobertas_csv",
                )

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

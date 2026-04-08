import math

import streamlit as st


def _estimate_current(cv: float, tensao: float, rendimento: float, fp: float, fases: str) -> float:
    if cv <= 0 or tensao <= 0:
        return 0.0

    watts = cv * 735.5
    rendimento = max(0.1, min(rendimento, 1.0))
    fp = max(0.1, min(fp, 1.0))

    if fases == "Monofasico":
        return watts / (tensao * rendimento * fp)
    return watts / (math.sqrt(3) * tensao * rendimento * fp)


def render(ctx):
    st.markdown(
        """
        <div class="diag-hero">
            <div class="diag-hero__tag">LAB TECNICO</div>
            <h1>Diagnostico de Motor</h1>
            <p>Painel rapido para triagem, leitura de sintomas e previsao de corrente.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="diag-grid">
            <div class="diag-card">
                <strong>Identificacao rapida</strong>
                <p>Giro leve tende a 2 polos, giro firme tende a 4 polos.</p>
            </div>
            <div class="diag-card">
                <strong>Teste de resistencia</strong>
                <p>Bobinas muito diferentes entre fases sugerem falha.</p>
            </div>
            <div class="diag-card">
                <strong>Regra de corrente</strong>
                <p>Diferenca entre fases acima de 10% pede investigacao.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Simulador", "Checklist", "Alertas"])

    with tabs[0]:
        st.markdown("### Simulador de carga")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tensao = st.number_input("Tensao (V)", min_value=1.0, value=380.0, step=10.0)
        with c2:
            potencia_cv = st.number_input("Potencia (CV)", min_value=0.1, value=10.0, step=0.5)
        with c3:
            rendimento = st.number_input("Rendimento", min_value=0.1, max_value=1.0, value=0.90, step=0.01)
        with c4:
            fp = st.number_input("Fator de potencia", min_value=0.1, max_value=1.0, value=0.86, step=0.01)

        fases = st.radio("Tipo de alimentacao", ["Trifasico", "Monofasico"], horizontal=True)

        if st.button("Analisar corrente esperada", use_container_width=True):
            corrente = _estimate_current(potencia_cv, tensao, rendimento, fp, fases)
            faixa_min = corrente * 0.9
            faixa_max = corrente * 1.1
            st.markdown(
                f"""
                <div class="result-box">
                    <h3>Resultado previsto</h3>
                    <div class="result-big">{corrente:.2f} A</div>
                    <p>Faixa recomendada para comparacao: {faixa_min:.2f} A ate {faixa_max:.2f} A</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tabs[1]:
        st.markdown("### Checklist de bancada")
        st.checkbox("Inspecao visual de terminais e isolacao")
        st.checkbox("Medicao de resistencia entre fases")
        st.checkbox("Megger para isolamento")
        st.checkbox("Conferencia de rolamentos e alinhamento")
        st.checkbox("Teste com carga progressiva")

    with tabs[2]:
        st.markdown("### Alertas criticos")
        st.markdown(
            """
            <div class="diag-alert">Corrente alta com RPM baixa pode indicar enrolamento errado ou tensao incorreta.</div>
            <div class="diag-alert">Aquecimento rapido no teste sem carga pode indicar curto entre espiras.</div>
            <div class="diag-alert">Vibracao com corrente normal pode ser causa mecanica (rolamento, eixo ou balanceamento).</div>
            """,
            unsafe_allow_html=True,
        )


def show(ctx):
    return render(ctx)

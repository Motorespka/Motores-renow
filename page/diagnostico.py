import streamlit as st


def render(ctx):
    st.title("🧠 Diagnóstico Técnico")
    st.markdown(
        """
### ⚡ Identificação rápida
- Girou leve → 2 polos
- Girou firme → 4 polos
- Pesado → 6 ou 8 polos

### ⚡ Teste de resistência
- Bobinas iguais = OK
- Uma diferente = defeito

### ⚡ Corrente
- Diferença máxima entre fases: 10%
"""
    )

    st.subheader("Simulador de Carga")
    v = st.number_input("Tensão (V)", value=220)
    p = st.number_input("Potência (CV)", value=1.0)
    if st.button("Analisar Corrente Esperada"):
        st.info(f"Para um motor de {p}CV em {v}V, a corrente deve estar próxima ao cadastrado no banco.")

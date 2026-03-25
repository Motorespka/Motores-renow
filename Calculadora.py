import streamlit as st

def show():
    st.markdown("### Calculadora de Apoio: Motores de Indução")
    
    # Organizando as entradas em colunas para uma interface mais limpa
    col1, col2 = st.columns(2)
    
    with col1:
        volts = st.number_input("Tensão (V)", value=220, step=10)
        frequencia = st.number_input("Frequência (Hz)", value=60)
        
    with col2:
        polos = st.selectbox("Quantidade de Polos", [2, 4, 6, 8])
        potencia = st.number_input("Potência (cv)", value=1.0)

    # Cálculo da Velocidade Síncrona: ns = (120 * f) / P
    velocidade_sincrona = (120 * frequencia) / polos

    st.divider()
    
    # Exibição dos Resultados
    st.subheader("Resultados Estimados")
    st.success(f"Velocidade Síncrona: **{velocidade_sincrona:.0f} RPM**")
    
    st.info(f"Sugestão para motor de {polos} polos em {volts}V operando a {frequencia}Hz.")

    # Dica técnica: O escorregamento real fará a rotação ser levemente menor (ex: 1750 RPM para 4 polos)
    st.caption("Nota: A rotação nominal real será menor devido ao escorregamento do motor.")
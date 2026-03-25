import streamlit as st
import pandas as pd
# Certifique-se de que esses imports apontam para arquivos existentes
# from database.db import buscar_motor 

def show():
    st.title("⚡ Consulta de Motores")
    
    # Campo de busca único
    busca = st.text_input(
        "Digite o modelo, marca ou potência do motor...",
        placeholder="Ex: Weg 50cv 4 polos"
    )

    if busca:
        st.subheader(f"Resultados para: '{busca}'")
        
        # --- OPÇÃO A: Usando Banco de Dados Real ---
        # resultados = buscar_motor(busca)
        
        # --- OPÇÃO B: Usando DataFrame (Dados de Exemplo) ---
        # Simulando o filtro no DataFrame 'dados_exemplo'
        # resultado_df = dados_exemplo[dados_exemplo['motor'].str.contains(busca, case=False)]
        
        # Exemplo de como exibir os resultados de uma lista/tupla (Banco de Dados)
        # Se buscar_motor retornar uma lista de tuplas:
        try:
            # Simulando o loop que você escreveu com correções
            resultados = [] # Aqui viria o retorno de buscar_motor(busca)
            
            if not resultados:
                st.warning("Nenhum motor encontrado com esses termos.")
            else:
                for motor in resultados:
                    with st.expander(f"Motor: {motor[1]} - {motor[2]}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Marca:** {motor[1]}")
                            st.write(f"**Modelo:** {motor[2]}")
                        with col2:
                            st.write(f"**Potência:** {motor[5]} {motor[6]}")
                            st.write(f"**RPM:** {motor[11]}")
                        st.divider()
        except Exception as e:
            st.error(f"Erro ao buscar no banco: {e}")
            
    else:
        st.info("Digite algo acima para iniciar a pesquisa.")

# Para testar localmente
if __name__ == "__main__":
    show()
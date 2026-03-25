import streamlit as st # Corrigido o erro de digitação
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Rebobinagem Pro", layout="wide")

# CSS para estilização (corrigido as chaves e fechamento)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        background-color: #004a99;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Moto-Renow: Sistema Técnico de Rebobinagem")
st.subheader("Gestão de cálculos e Motores Elétricos")

# Corrigido: Aspas e vírgulas nas abas
aba1, aba2, aba3 = st.tabs([
    "Cadastrar Novo Cálculo", 
    "Consultar Cálculos", 
    "Calcular"
])

# Importante: Verifique se seus arquivos estão na pasta 'pages' 
# ou no mesmo diretório. Ajuste os imports conforme necessário.
with aba1:
    import Cadastro
    Cadastro.show()
with aba2:
    import Consulta
    Consulta.show()
with aba3:
    import Calculadora
    Calculadora.show()
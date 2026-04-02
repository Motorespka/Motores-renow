import streamlit as st
from auth.session import criar_sessao, sessao_valida

def check_login():
    # Se sessão válida → entra direto, nada é mostrado
    if sessao_valida():
        return True  # Retorna True para sinalizar que o usuário está logado

    # Formulário de login
    st.title("🔐 Moto-Renow • Acesso Técnico")
    senha = st.text_input("Chave técnica", type="password")

    if st.button("Entrar"):
        if senha == st.secrets["APP_PASSWORD"]:
            criar_sessao()
            st.experimental_rerun()  # reinicia a página para refletir a sessão
        else:
            st.error("Senha incorreta")

    st.stop()  # bloqueia qualquer execução adicional até login

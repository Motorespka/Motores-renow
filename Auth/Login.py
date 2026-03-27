import streamlit as st

def check_login():

    if "logado" not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:

        senha = st.text_input("Senha", type="password")

        if senha == "1234":
            st.session_state.logado = True
            st.rerun()

        st.stop()

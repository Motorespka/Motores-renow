import streamlit as st
from datetime import datetime, timedelta

TEMPO_SESSAO = 8  # horas


def criar_sessao():
    st.session_state.logado = True
    st.session_state.expira_em = (
        datetime.now() + timedelta(hours=TEMPO_SESSAO)
    )


def sessao_valida():

    if "logado" not in st.session_state:
        return False

    if not st.session_state.logado:
        return False

    if "expira_em" not in st.session_state:
        return False

    if datetime.now() > st.session_state.expira_em:
        limpar_sessao()
        return False

    return True


def limpar_sessao():
    for k in list(st.session_state.keys()):
        del st.session_state[k]

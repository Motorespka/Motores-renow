import streamlit as st


def perform_logout(session, client=None):
    try:
        if client is not None:
            try:
                client.auth.sign_out()
            except Exception:
                pass

        session.logout()
        st.success("Sessão encerrada com sucesso.")
        st.rerun()

    except Exception as exc:
        st.error(f"Erro ao sair: {exc}")

import streamlit as st

def carregar_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def card(titulo, conteudo):

    st.markdown(f"""
    <div class="card">
        <h3>{titulo}</h3>
        <p>{conteudo}</p>
    </div>
    """, unsafe_allow_html=True)

import streamlit as st
import pytesseract
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="Moto-Renow", layout="wide")

st.title("Moto-Renow: Sistema de Rebobinagem")

# Criando as abas
aba1, aba2, aba3 = st.tabs(["Cadastro", "Consulta", "Calculadora"])

with aba1:
    try:
        import Cadastro
        Cadastro.show()
    except Exception as e:
        st.error(f"Erro ao carregar Cadastro: {e}")

with aba2:
    try:
        import Consulta
        Consulta.show()
    except Exception as e:
        st.error(f"Erro ao carregar Consulta: {e}")

with aba3:
    try:
        import Calculadora
        Calculadora.show()
    except Exception as e:
        st.error(f"Erro ao carregar Calculadora: {e}")

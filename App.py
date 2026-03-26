import streamlit as st
import pytesseract
import cv2
import numpy as np
from PIL import Image

# Isso evita que o app carregue a IA toda vez que você clica em um botão
@st.cache_resource
def carregar_leitor():
    # 'gpu=False' é obrigatório no Streamlit Cloud (não há GPU gratuita)
    return easyocr.Reader(['pt', 'en'], gpu=False)

def ler_placa_motor(upload_imagem):
    imagem = Image.open(upload_imagem)
    # Converte para escala de cinza para melhorar a leitura da placa
    imagem_cv = cv2.cvtColor(np.array(imagem), cv2.COLOR_RGB2GRAY)
    texto = pytesseract.image_to_string(imagem_cv, lang='por')
    return texto

# Exemplo de uso na aba de calcular
# foto = st.file_uploader("Tire foto da placa do motor", type=['jpg', 'png'])
# if foto:
#     dados = extrair_dados_da_placa(foto)
#     st.write(f"Dados detectados: {dados}")

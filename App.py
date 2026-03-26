import streamlit as st
import easyocr
import numpy as np
from PIL import Image

# Isso evita que o app carregue a IA toda vez que você clica em um botão
@st.cache_resource
def carregar_leitor():
    # 'gpu=False' é obrigatório no Streamlit Cloud (não há GPU gratuita)
    return easyocr.Reader(['pt', 'en'], gpu=False)

def extrair_dados_da_placa(imagem):
    reader = carregar_leitor()
    # Converte imagem do Streamlit para o formato que a IA aceita
    img_array = np.array(Image.open(imagem))
    resultado = reader.readtext(img_array, detail=0)
    return " ".join(resultado)

# Exemplo de uso na aba de calcular
# foto = st.file_uploader("Tire foto da placa do motor", type=['jpg', 'png'])
# if foto:
#     dados = extrair_dados_da_placa(foto)
#     st.write(f"Dados detectados: {dados}")

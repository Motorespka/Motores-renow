import easyocr
import cv2
import re
import numpy as np
import streamlit as st
import os  # Adicionado para manipular pastas
from PIL import Image

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="OCR Motor Expert", layout="centered")

# --- FUNÇÕES DE PROCESSAMENTO ---

@st.cache_resource
def carregar_modelo():
    """Carrega o modelo EasyOCR apenas uma vez (Cache)"""
    return easyocr.Reader(['pt', 'en'], gpu=False)

def preprocessar_imagem(imagem_array):
    """Melhora o contraste para o OCR ler melhor"""
    gray = cv2.cvtColor(imagem_array, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGrid_size=(8,8))
    res = clahe.apply(gray)
    _, thresh = cv2.threshold(res, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extrair_dados_especificos(texto):
    """Usa Expressões Regulares (Regex) para encontrar padrões técnicos"""
    dados = {
        "Marca": "Não detectada",
        "Tensão (V)": "Não detectada",
        "Potência (kW/HP)": "Não detectada",
        "Rotação (RPM)": "Não detectada",
        "Frequência (Hz)": "Não detectada",
        "Corrente (A)": "Não detectada"
    }

    if "WEG" in texto.upper(): dados["Marca"] = "WEG"
    elif "SIEMENS" in texto.upper(): dados["Marca"] = "SIEMENS"
    elif "VOGES" in texto.upper(): dados["Marca"] = "VOGES"

    tensoes = re.findall(r'\b(220|380|440|760)\b', texto)
    if tensoes: dados["Tensão (V)"] = " / ".join(list(set(tensoes)))

    rpm = re.search(r'(\d{3,4})\s?(?:RPM|min-1|min)', texto, re.IGNORECASE)
    if rpm: dados["Rotação (RPM)"] = rpm.group(1)

    freq = re.search(r'(50|60)\s?Hz', texto, re.IGNORECASE)
    if freq: dados["Frequência (Hz)"] = freq.group(1)

    pot = re.search(r'(\d+[.,]\d+)\s?(?:kW|HP|cv)', texto, re.IGNORECASE)
    if pot: dados["Potência (kW/HP)"] = pot.group(1)

    return dados

# --- FUNÇÃO PARA COMPATIBILIDADE DE IMPORTAÇÃO ---
def ler_placa_motor(imagem_input):
    """Função ponte para chamadas externas via import"""
    reader = carregar_modelo()
    if isinstance(imagem_input, str):
        imagem_input = cv2.imread(imagem_input)
    
    resultado = reader.readtext(imagem_input)
    texto_total = " ".join([res[1] for res in resultado])
    return extrair_dados_especificos(texto_total)

# --- INTERFACE STREAMLIT ---

st.title("🔌 Extrator de Dados de Placa de Motor")
st.write("Faça upload da foto da placa para converter em dados estruturados.")

arquivo = st.file_uploader("Selecione a imagem", type=['jpg', 'jpeg', 'png'])

if arquivo:
    # --- CORREÇÃO DO ERRO 'TEMP' ---
    # Garante que a pasta temp existe sem causar erro se ela já estiver lá
    if not os.path.exists("temp"):
        os.makedirs("temp", exist_ok=True)

    # 1. Carregar imagem
    img_pil = Image.open(arquivo)
    img_array = np.array(img_pil)
    
    col1, col2 = st.columns(2)
    with col1:
        st.image(img_pil, caption="Imagem Original", use_container_width=True)
    
    # 2. Processar OCR
    reader = carregar_modelo()
    
    with st.spinner('🤖 Inteligência Artificial processando a imagem...'):
        # Leitura OCR
        resultado = reader.readtext(img_array)
        texto_completo = " ".join([res[1] for res in resultado])
        
        # Extração inteligente
        dados_finais = extrair_dados_especificos(texto_completo)

    with col2:
        st.success("Dados Extraídos!")
        for chave, valor in dados_finais.items():
            st.markdown(f"**{chave}:** `{valor}`")

    with st.expander("Ver texto bruto detectado"):
        st.write(texto_completo)
        
    csv = f"Campo,Valor\n" + "\n".join([f"{k},{v}" for k, v in dados_finais.items()])
    st.download_button("Baixar Dados (CSV)", csv, "dados_motor.csv", "text/csv")

else:
    st.info("Aguardando imagem para iniciar a análise.")

import easyocr
import cv2
import re
import numpy as np
import streamlit as st
import os
from PIL import Image

@st.cache_resource
def carregar_modelo():
    """Carrega o modelo EasyOCR apenas uma vez"""
    return easyocr.Reader(['pt', 'en'], gpu=False)

def extrair_dados_especificos(texto):
    """
    Usa Regex flexível para encontrar os dados. 
    Mesmo que o texto venha 'sujo', tentamos extrair apenas os números.
    """
    # Transformamos tudo em uma string única para facilitar a busca
    texto_limpo = " ".join(texto) if isinstance(texto, list) else texto
    
    dados = {
        "Marca": "",
        "Tensão (V)": "",
        "Potência (kW/HP)": "",
        "Rotação (RPM)": "",
        "Frequência (Hz)": "",
        "Corrente (A)": ""
    }

    # 1. MARCA (Busca simples por palavras-chave)
    if "WEG" in texto_limpo.upper(): dados["Marca"] = "WEG"
    elif "SIEMENS" in texto_limpo.upper(): dados["Marca"] = "SIEMENS"
    elif "VOGES" in texto_limpo.upper(): dados["Marca"] = "VOGES"

    # 2. TENSÃO (Busca números de 3 dígitos comuns em placas)
    tensoes = re.findall(r'\b(110|127|220|380|440|460|760)\b', texto_limpo)
    if tensoes:
        dados["Tensão (V)"] = " / ".join(sorted(list(set(tensoes))))

    # 3. ROTAÇÃO (Busca números entre 700 e 3650 que costumam ser RPM)
    # Filtramos números de 3 ou 4 dígitos perto da palavra RPM ou min
    rpm = re.search(r'(\d{3,4})\s?(?:RPM|min|RPM|MIN)', texto_limpo, re.IGNORECASE)
    if rpm:
        dados["Rotação (RPM)"] = rpm.group(1)
    else:
        # Busca genérica por valores comuns de RPM se a palavra RPM não aparecer
        rpms_comuns = re.findall(r'\b(8[0-9]{2}|11[0-9]{2}|17[0-9]{2}|34[0-9]{2}|35[0-9]{2})\b', texto_limpo)
        if rpms_comuns: dados["Rotação (RPM)"] = rpms_comuns[0]

    # 4. FREQUÊNCIA
    freq = re.search(r'(50|60)\s?Hz', texto_limpo, re.IGNORECASE)
    if freq: dados["Frequência (Hz)"] = freq.group(1)

    # 5. POTÊNCIA (Busca números seguidos de KW, HP ou CV)
    # Ex: 1.5kW, 10 CV, 0,75HP
    pot = re.search(r'(\d+[\.,]\d+|\d+)\s?(?:kW|HP|cv|CV)', texto_limpo, re.IGNORECASE)
    if pot:
        dados["Potência (kW/HP)"] = pot.group(1).replace(",", ".")

    # 6. CORRENTE (A)
    # Busca um número antes da letra A isolada (Ex: 4.5 A ou 10A)
    corrente = re.search(r'(\d+[\.,]\d+|\d+)\s?A\b', texto_limpo)
    if corrente:
        dados["Corrente (A)"] = corrente.group(1).replace(",", ".")

    return dados

def ler_placa_motor(imagem_input):
    """Lê a imagem e retorna o dicionário com os dados encontrados"""
    reader = carregar_modelo()
    
    # Se receber caminho (string) ou objeto PIL, converte para array que o EasyOCR entende
    if isinstance(imagem_input, str):
        imagem_input = cv2.imread(imagem_input)
    elif not isinstance(imagem_input, np.ndarray):
        imagem_input = np.array(imagem_input)
    
    # Converte para tons de cinza para melhorar a detecção
    if len(imagem_input.shape) == 3:
        gray = cv2.cvtColor(imagem_input, cv2.COLOR_BGR2GRAY)
    else:
        gray = imagem_input

    # Executa a leitura
    resultado = reader.readtext(gray)
    
    # Junta todas as frases detectadas em um texto só
    texto_total = " ".join([res[1] for res in resultado])
    
    # Retorna o dicionário processado
    return extrair_dados_especificos(texto_total)

if __name__ == "__main__":
    # Mantém sua interface original para testes rápidos
    st.title("Teste de OCR Local")
    arquivo = st.file_uploader("Suba uma placa", type=['jpg', 'png'])
    if arquivo:
        img = Image.open(arquivo)
        st.image(img)
        res = ler_placa_motor(img)
        st.write(res)

import easyocr
import cv2
import re
import numpy as np
import streamlit as st


# =========================
# 🚀 CARREGA MODELO (CACHE)
# =========================
@st.cache_resource
def carregar_modelo():
    return easyocr.Reader(['pt', 'en'], gpu=False)


# =========================
# 🧹 PRÉ-PROCESSAMENTO
# =========================
def preprocessar_imagem(img):
    """
    Melhora a qualidade da imagem para OCR
    """
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Aumenta contraste
    img = cv2.equalizeHist(img)

    # Remove ruído
    img = cv2.GaussianBlur(img, (3, 3), 0)

    # Threshold (binarização)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return img


# =========================
# 🧠 NORMALIZA TEXTO
# =========================
def normalizar_texto(texto):
    texto = texto.upper()

    # Corrige erros comuns do OCR
    substituicoes = {
        "O": "0",
        "I": "1",
        "L": "1",
        "S": "5",
        "B": "8"
    }

    for k, v in substituicoes.items():
        texto = texto.replace(k, v)

    return texto


# =========================
# 🔍 EXTRAÇÃO INTELIGENTE
# =========================
def extrair_dados_especificos(texto):
    texto = normalizar_texto(texto)

    dados = {
        "Marca": "",
        "Tensão": "",
        "Potência": "",
        "Rotação": "",
        "Frequência": "",
        "Corrente": ""
    }

    # =========================
    # 🏭 MARCA
    # =========================
    if "WEG" in texto:
        dados["Marca"] = "WEG"
    elif "SIEMENS" in texto:
        dados["Marca"] = "SIEMENS"
    elif "VOGES" in texto:
        dados["Marca"] = "VOGES"

    # =========================
    # ⚡ TENSÃO
    # =========================
    tensoes = re.findall(r'\b(110|127|220|380|440|460|480|760)\b', texto)
    if tensoes:
        dados["Tensão"] = " / ".join(sorted(set(tensoes)))

    # =========================
    # 🔄 ROTAÇÃO (RPM)
    # =========================
    rpm = re.search(r'(\d{3,4})\s?(RPM|MIN)', texto)
    if rpm:
        dados["Rotação"] = rpm.group(1)
    else:
        candidatos = re.findall(r'\b(8\d{2}|11\d{2}|17\d{2}|34\d{2}|35\d{2})\b', texto)
        if candidatos:
            dados["Rotação"] = candidatos[0]

    # =========================
    # 🔌 FREQUÊNCIA
    # =========================
    freq = re.search(r'(50|60)\s?HZ', texto)
    if freq:
        dados["Frequência"] = freq.group(1)

    # =========================
    # ⚙️ POTÊNCIA
    # =========================
    pot = re.search(r'(\d+[\.,]?\d*)\s?(KW|CV|HP)', texto)
    if pot:
        dados["Potência"] = pot.group(1).replace(",", ".")

    # =========================
    # 🔋 CORRENTE
    # =========================
    corrente = re.search(r'(\d+[\.,]?\d*)\s?A\b', texto)
    if corrente:
        dados["Corrente"] = corrente.group(1).replace(",", ".")

    return dados


# =========================
# 📸 FUNÇÃO PRINCIPAL OCR
# =========================
def ler_placa_motor(imagem_input, debug=False):
    reader = carregar_modelo()

    # =========================
    # 📥 ENTRADA FLEXÍVEL
    # =========================
    if isinstance(imagem_input, str):
        img = cv2.imread(imagem_input)
    elif isinstance(imagem_input, np.ndarray):
        img = imagem_input
    else:
        img = np.array(imagem_input)

    # =========================
    # 🔧 PRÉ-PROCESSAMENTO
    # =========================
    img_proc = preprocessar_imagem(img)

    # =========================
    # 🤖 OCR
    # =========================
    resultado = reader.readtext(img_proc)

    textos = [res[1] for res in resultado]
    texto_total = " ".join(textos)

    # =========================
    # 🧠 EXTRAÇÃO
    # =========================
    dados = extrair_dados_especificos(texto_total)

    # =========================
    # 🐞 DEBUG
    # =========================
    if debug:
        return {
            "texto_detectado": textos,
            "texto_total": texto_total,
            "dados_extraidos": dados
        }

    return dados


# =========================
# 🧪 TESTE LOCAL
# =========================
if __name__ == "__main__":
    st.title("Teste OCR Motor (PRO)")

    arquivo = st.file_uploader("Envie imagem", type=["jpg", "png", "jpeg"])

    if arquivo:
        from PIL import Image

        img = Image.open(arquivo)
        st.image(img)

        if st.button("Rodar OCR"):
            resultado = ler_placa_motor(img, debug=True)

            st.subheader("🧾 Texto Detectado")
            st.write(resultado["texto_detectado"])

            st.subheader("🧠 Texto Completo")
            st.write(resultado["texto_total"])

            st.subheader("📊 Dados Extraídos")
            st.json(resultado["dados_extraidos"])

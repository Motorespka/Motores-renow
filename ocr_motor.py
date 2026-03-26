import easyocr

# inicia leitor (português + inglês)
reader = easyocr.Reader(['pt','en'])

def ler_placa_motor(caminho_imagem):

    resultado = reader.readtext(caminho_imagem)

    texto_total = " ".join([r[1] for r in resultado])

    dados = {}

    # EXTRAÇÕES SIMPLES (vamos melhorar depois)
    if "WEG" in texto_total.upper():
        dados["marca"] = "WEG"

    if "220" in texto_total:
        dados["tensao"] = 220

    if "380" in texto_total:
        dados["tensao"] = 380

    if "4" in texto_total:
        dados["polos"] = 4

    dados["texto_detectado"] = texto_total

    return dados

dados_ocr = ler_placa_motor(caminho_imagem)
st.sucess("Dados encontrados!")
st.write(dados_ocr)

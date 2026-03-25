import easyocr

# carrega modelo UMA vez só
reader = easyocr.Reader(['pt','en'])

def ler_placa_motor(caminho):

    resultado = reader.readtext(caminho)

    texto = " ".join([item[1] for item in resultado])

    return {
        "texto_extraido": texto
    }
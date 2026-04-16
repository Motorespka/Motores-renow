import numpy as np
from PIL import Image

try:
    import easyocr
<<<<<<< Updated upstream
except Exception:
    easyocr = None

reader = None
if easyocr is not None:
    try:
        reader = easyocr.Reader(["pt", "en"], gpu=False)
    except Exception:
        reader = None


def _ensure_ocr_runtime() -> None:
    if reader is None:
        raise RuntimeError(
            "Visao industrial indisponivel: instale/valide dependencia 'easyocr'."
        )


def analisar_enrolamento(imagem):
    _ensure_ocr_runtime()
=======
except ImportError:  # pragma: no cover - depends on optional package
    easyocr = None

reader = easyocr.Reader(["pt", "en"], gpu=False) if easyocr else None


def _ensure_ocr_dependencies() -> None:
    if easyocr is None:
        raise RuntimeError("Dependencia OCR ausente: easyocr")


def analisar_enrolamento(imagem):
    _ensure_ocr_dependencies()
>>>>>>> Stashed changes

    img = Image.open(imagem)
    img = np.array(img)

    texto = reader.readtext(img, detail=0)

    texto_total = " ".join(texto).lower()

    diagnostico = []

    if "queim" in texto_total:
        diagnostico.append("Bobina queimada detectada")

    if "escuro" in texto_total:
        diagnostico.append("Possivel sobreaquecimento")

    if not diagnostico:
        diagnostico.append("Nenhuma falha visual clara")

    return diagnostico

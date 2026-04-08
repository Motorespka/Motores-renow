from __future__ import annotations

import io
import os
from typing import Dict, List, Tuple

import google.generativeai as genai
from PIL import Image

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_SUPPORTED = True
except Exception:
    HEIF_SUPPORTED = False

from services.oficina_parser import normalize_extracted_data, parse_json_response

PROMPT_OFICINA = """
Você é especialista em rebobinagem e manutenção de motores elétricos.
Analise uma ou mais fotos de oficina (escrita manual, desenhos técnicos, abreviações e dados incompletos).

Objetivo:
1) Extraia todos os campos técnicos possíveis.
2) Não invente valores: quando não souber, deixe vazio.
3) Entenda variações de nomenclatura (RPM/rpm, CV/HP/kW, AMP/A, passo/passos, fio/fios, espira/espiras).
4) Identifique blocos principal e auxiliar quando houver.
5) Interprete desenho manual como texto técnico resumido.

Responda APENAS JSON válido com o formato:
{
  "arquivo_origem": "",
  "texto_ocr": "",
  "texto_normalizado": "",
  "motor": {
    "marca": "", "modelo": "", "potencia": "", "cv": "", "rpm": "", "polos": "",
    "tensao": [], "corrente": [], "frequencia": "", "isolacao": "", "ip": "", "fator_servico": "",
    "tipo_motor": "", "fases": "", "numero_serie": "", "data_anotacao": ""
  },
  "bobinagem_principal": {
    "passos": [], "espiras": [], "fios": [], "ligacao": "", "observacoes": "", "quantidade_grupos": "", "quantidade_bobinas": ""
  },
  "bobinagem_auxiliar": {
    "passos": [], "espiras": [], "fios": [], "capacitor": "", "ligacao": "", "observacoes": ""
  },
  "mecanica": {
    "rolamentos": [], "eixo": "", "carcaca": "", "medidas": [], "comprimento_ponta": "", "observacoes": ""
  },
  "esquema": {
    "descricao_desenho": "", "distribuicao_bobinas": "", "ligacao": "", "ranhuras": "", "camadas": "", "observacoes": ""
  },
  "observacoes_gerais": "",
  "campos_extras": [],
  "confianca": {}
}
"""


def _gemini_keys() -> List[str]:
    keys = []
    env = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if env:
        keys.append(env)

    try:
        import streamlit as st

        secret = st.secrets.get("GEMINI_API_KEY", None)
        if isinstance(secret, list):
            keys.extend([str(k).strip() for k in secret if str(k).strip()])
        elif isinstance(secret, str) and secret.strip():
            keys.append(secret.strip())
    except Exception:
        pass

    # ordem estável e sem repetição
    uniq = []
    for k in keys:
        if k not in uniq:
            uniq.append(k)
    return uniq


def _to_supported_image_bytes(file_name: str, raw_bytes: bytes) -> Tuple[bytes, str]:
    lower = file_name.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return raw_bytes, "image/jpeg"
    if lower.endswith(".png"):
        return raw_bytes, "image/png"

    if lower.endswith(".heic"):
        if not HEIF_SUPPORTED:
            raise RuntimeError("Arquivo HEIC enviado, mas suporte HEIC não está disponível neste ambiente.")
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=95)
        return out.getvalue(), "image/jpeg"

    img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=95)
    return out.getvalue(), "image/jpeg"


def extract_motor_data_with_gemini(files: List[Dict[str, bytes]]) -> Dict:
    keys = _gemini_keys()
    if not keys:
        raise RuntimeError("GEMINI_API_KEY não configurada em variáveis de ambiente ou st.secrets.")

    parts = [PROMPT_OFICINA]
    file_names = []
    for f in files:
        normalized_bytes, mime = _to_supported_image_bytes(f["name"], f["bytes"])
        parts.append({"mime_type": mime, "data": normalized_bytes})
        file_names.append(f["name"])

    model_name = (os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash").strip()
    last_error = None
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(parts)
            data = normalize_extracted_data(parse_json_response(response.text or ""))
            if not data.get("arquivo_origem"):
                data["arquivo_origem"] = ", ".join(file_names)
            return data
        except Exception as exc:
            last_error = exc
            if any(flag in str(exc).lower() for flag in ["quota", "limit", "429"]):
                continue
            break

    raise RuntimeError(f"Falha ao analisar imagens com Gemini: {last_error}")

from __future__ import annotations

import io
import os
import re
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
3) Entenda variações de nomenclatura (RPM/rpm, CV/HP/kW/kVA/kVW, AMP/A, passo/passos, fio/fios, espira/espiras).
4) Identifique blocos principal e auxiliar quando houver.
5) Interprete desenho manual como texto técnico resumido.
6) Mantenha unidade da potência exatamente como estiver (ex.: "230 kVA", "75 kVW", "7,5 CV", "5.5 kW").
7) Em bobinagem, capture sequências de caderno/oficina:
   - "passos 6 8 10 12" -> passos: ["6","8","10","12"]
   - "espiras 5 5 5 5" -> espiras: ["5","5","5","5"]
   - "8x17 e 1x18 fios" -> fios: ["8x17","1x18"]

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


def _looks_like_jpeg(raw_bytes: bytes) -> bool:
    return raw_bytes[:3] == b"\xff\xd8\xff"


def _looks_like_png(raw_bytes: bytes) -> bool:
    return raw_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def _looks_like_heif_family(raw_bytes: bytes) -> bool:
    if len(raw_bytes) < 12:
        return False
    if raw_bytes[4:8] != b"ftyp":
        return False
    brand = raw_bytes[8:12]
    return brand in {b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1", b"avif", b"avis"}


def _to_supported_image_bytes(file_name: str, raw_bytes: bytes, mime_type: str = "") -> Tuple[bytes, str]:
    """
    Normaliza imagens para envio ao Gemini.
    Observação importante: fotos de telefone podem chegar com extensão errada
    (ou sem extensão), então priorizamos assinatura binária e fazemos fallback em PIL.
    """
    lower = (file_name or "").lower().strip()
    mime = (mime_type or "").lower().strip()

    if _looks_like_jpeg(raw_bytes) or lower.endswith((".jpg", ".jpeg", ".jfif")) or mime in {"image/jpeg", "image/jpg"}:
        return raw_bytes, "image/jpeg"
    if _looks_like_png(raw_bytes) or lower.endswith(".png") or mime == "image/png":
        return raw_bytes, "image/png"

    is_heif_name = lower.endswith((".heic", ".heif", ".avif"))
    is_heif_mime = mime in {"image/heic", "image/heif", "image/heic-sequence", "image/heif-sequence", "image/avif"}
    is_heif_bytes = _looks_like_heif_family(raw_bytes)

    if (is_heif_name or is_heif_mime or is_heif_bytes) and not HEIF_SUPPORTED:
        raise RuntimeError(
            "Arquivo HEIC/HEIF enviado, mas suporte HEIF não está disponível neste ambiente. "
            "Instale pillow-heif para habilitar conversão automática."
        )

    img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=95, optimize=True)
    return out.getvalue(), "image/jpeg"


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _extract_potencia_with_unit(text: str) -> str:
    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(kva|kv\s*a|kvw|kv\s*w|kw|k\s*w|cv|hp|w)\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""

    value = match.group(1).replace(",", ".")
    unit_raw = match.group(2).lower().replace(" ", "")
    unit_map = {"kva": "kVA", "kvw": "kVW", "kw": "kW", "cv": "CV", "hp": "HP", "w": "W"}
    unit = unit_map.get(unit_raw, unit_raw.upper())
    return f"{value} {unit}"


def _extract_numeric_list_after_label(text: str, label_pattern: str) -> List[str]:
    match = re.search(
        rf"(?:{label_pattern})\s*[:=-]?\s*([0-9\s,;/\\.-]{{2,80}})",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return []
    nums = re.findall(r"\d+(?:[.,]\d+)?", match.group(1))
    return [n.replace(",", ".") for n in nums]


def _extract_fios_list(text: str) -> List[str]:
    block_match = re.search(
        r"(?:fios?|fio)\s*[:=-]?\s*([0-9xX\s,;/\\.+-eE]{2,120})",
        text,
        flags=re.IGNORECASE,
    )
    scope = block_match.group(1) if block_match else text

    tokens = re.findall(r"\d+\s*[xX]\s*\d+(?:[.,]\d+)?", scope)
    out: List[str] = []
    for token in tokens:
        norm = re.sub(r"\s+", "", token).lower().replace("x", "x")
        if norm not in out:
            out.append(norm)
    return out


def _extract_tensao_list(text: str) -> List[str]:
    chunks: List[str] = []

    for match in re.finditer(
        r"(?:tens[aã]o|voltagem)\s*[:=-]?\s*([0-9vV\s/.,-]{2,40})",
        text,
        flags=re.IGNORECASE,
    ):
        chunks.append(match.group(1))

    # fallback: padrões "220/380V" no texto geral
    for match in re.finditer(r"(\d{2,4}\s*/\s*\d{2,4}\s*(?:v)?)", text, flags=re.IGNORECASE):
        chunks.append(match.group(1))

    values: List[str] = []
    for chunk in chunks:
        nums = re.findall(r"\d{2,4}(?:[.,]\d+)?", chunk)
        for raw in nums:
            num = raw.replace(",", ".")
            try:
                val = float(num)
            except Exception:
                continue
            # Faixa ampla para tensão industrial
            if 80 <= val <= 20000:
                out = str(int(val)) if val.is_integer() else num
                if out not in values:
                    values.append(out)
    return values


def _extract_rpm(text: str) -> str:
    match = re.search(r"(?:rpm)\s*[:=-]?\s*(\d{3,5})", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r"\b(\d{3,5})\s*rpm\b", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def _extract_frequencia(text: str) -> str:
    match = re.search(r"(\d{2,3})\s*hz\b", text, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def _extract_marca(text: str) -> str:
    for brand in ["WEG", "ABB", "SIEMENS", "SCHNEIDER", "SEW", "DANCOR"]:
        if re.search(rf"\b{brand}\b", text, flags=re.IGNORECASE):
            return brand
    return ""


def _extract_fases(text: str) -> str:
    # Primeiro tenta por palavras explícitas.
    if re.search(r"\btri\s*f[aá]sico\b|\btrif[aá]sico\b", text, flags=re.IGNORECASE):
        return "Trifásico"
    if re.search(r"\bmono\s*f[aá]sico\b|\bmonof[aá]sico\b", text, flags=re.IGNORECASE):
        return "Monofásico"

    # Padrões comuns de placa: "3~", "1~", "3-280L", "1 - 90S", "3F", "1F".
    if re.search(r"(?<!\d)3\s*([~\-]|f\b)", text, flags=re.IGNORECASE):
        return "Trifásico"
    if re.search(r"(?<!\d)1\s*([~\-]|f\b)", text, flags=re.IGNORECASE):
        return "Monofásico"

    return ""


def _enrich_with_text_heuristics(data: Dict) -> Dict:
    text = _normalize_spaces(
        " ".join(
            [
                str(data.get("texto_ocr") or ""),
                str(data.get("texto_normalizado") or ""),
                str(data.get("observacoes_gerais") or ""),
            ]
        )
    )
    if not text:
        return data

    motor = data.get("motor") if isinstance(data.get("motor"), dict) else {}
    principal = (
        data.get("bobinagem_principal")
        if isinstance(data.get("bobinagem_principal"), dict)
        else {}
    )

    potencia_atual = str(motor.get("potencia") or "").strip()
    potencia_texto = _extract_potencia_with_unit(text)
    if potencia_texto and (
        not potencia_atual or re.fullmatch(r"\d+(?:[.,]\d+)?", potencia_atual)
    ):
        motor["potencia"] = potencia_texto

    tensao_atual = motor.get("tensao")
    if not tensao_atual:
        motor["tensao"] = _extract_tensao_list(text)

    if not str(motor.get("rpm") or "").strip():
        motor["rpm"] = _extract_rpm(text)

    if not str(motor.get("frequencia") or "").strip():
        motor["frequencia"] = _extract_frequencia(text)

    if not str(motor.get("marca") or "").strip():
        motor["marca"] = _extract_marca(text)

    if not str(motor.get("fases") or "").strip():
        motor["fases"] = _extract_fases(text)

    if not principal.get("passos"):
        principal["passos"] = _extract_numeric_list_after_label(text, r"passos?|passo")

    if not principal.get("espiras"):
        principal["espiras"] = _extract_numeric_list_after_label(
            text, r"espiras?|espira"
        )

    if not principal.get("fios"):
        principal["fios"] = _extract_fios_list(text)

    if motor:
        data["motor"] = motor
    if principal:
        data["bobinagem_principal"] = principal
    return data


def extract_motor_data_with_gemini(files: List[Dict[str, bytes]]) -> Dict:
    keys = _gemini_keys()
    if not keys:
        raise RuntimeError("GEMINI_API_KEY não configurada em variáveis de ambiente ou st.secrets.")

    parts = [PROMPT_OFICINA]
    file_names = []
    for f in files:
        normalized_bytes, content_type = _to_supported_image_bytes(
            f["name"], f["bytes"], f.get("mime_type", "")
        )
        parts.append({"mime_type": content_type, "data": normalized_bytes})
        file_names.append(f["name"])

    model_name = (os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash").strip()
    last_error = None
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(parts)
            data = normalize_extracted_data(parse_json_response(response.text or ""))
            data = normalize_extracted_data(_enrich_with_text_heuristics(data))
            if not data.get("arquivo_origem"):
                data["arquivo_origem"] = ", ".join(file_names)
            return data
        except Exception as exc:
            last_error = exc
            if any(flag in str(exc).lower() for flag in ["quota", "limit", "429"]):
                continue
            break

    raise RuntimeError(f"Falha ao analisar imagens com Gemini: {last_error}")

import json
import os
import re
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _modelo_gemini() -> str:
    return (os.environ.get("GEMINI_MODEL") or "gemini-2.0-flash").strip()


CAMPOS_PLACA = [
    "marca", "modelo", "potencia", "tensao", "corrente",
    "rpm", "frequencia", "fp", "carcaca", "ip",
    "isolacao", "regime", "rolamento_dianteiro",
    "rolamento_traseiro", "peso", "diametro_eixo",
    "comprimento_pacote", "numero_ranhuras",
    "ligacao", "fabricacao",
]

PROMPT_PLACA = """Você é um especialista em placas de identificação de motores elétricos industriais.
Analise a imagem da placa (pode estar em português ou inglês) e extraia os dados técnicos visíveis.

Responda APENAS com um objeto JSON válido, sem markdown, sem texto antes ou depois.
Use exatamente estas chaves (string vazia "" se o dado não existir na placa):
marca, modelo, potencia, tensao, corrente, rpm, frequencia, fp, carcaca, ip,
isolacao, regime, rolamento_dianteiro, rolamento_traseiro, peso, diametro_eixo,
comprimento_pacote, numero_ranhuras, ligacao, fabricacao

Regras:
- potencia: como na placa (ex: "5,5 kW", "7,5 CV").
- tensao: valores em V (ex: "220/380 V" ou "380").
- corrente: como na placa (ex: "12,5/7,2 A").
- fp ou cos φ: em "fp".
- carcaca: número IEC (63, 71, 80, 90, 112, 132, etc.) se existir.
"""

PROMPT_CALCULOS = """Com base nos dados abaixo de um motor elétrico (podem estar incompletos),
faça estimativas úteis para manutenção e dimensionamento.

Dados (JSON):
{json_dados}

Responda APENAS com JSON válido, sem markdown, com as chaves:
corrente_nominal_estimada_a (string, explicação se estimativa),
potencia_kw_estimada (string),
potencia_hp_estimada (string),
relacao_tensao_corrente (string, breve observação),
observacoes (string, 2 a 4 frases em português sobre cálculos típicos: I = P/(√3·U·cosφ·η) trifásico, conversões HP/kW, etc., aplicando ao que for possível inferir).

Se faltar dado essencial, indique na observação o que falta e não invente números sem base.
"""


def obter_chave_gemini():
    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if key:
        return key
    try:
        import streamlit as st

        sec = getattr(st, "secrets", None)
        if sec is not None and "GEMINI_API_KEY" in sec:
            return str(sec["GEMINI_API_KEY"]).strip()
    except Exception as exc:
        raise RuntimeError("Falha ao ler GEMINI_API_KEY em st.secrets") from exc
    return ""


def _texto_resposta_gemini(r) -> str:
    try:
        return (r.text or "").strip()
    except Exception:
        return ""


def _extrair_json(texto: str) -> dict:
    if not texto:
        raise ValueError("Resposta vazia do modelo.")
    t = texto.strip()
    bloco = re.search(r"\{[\s\S]*\}", t)
    if not bloco:
        raise ValueError("Não foi possível localizar JSON na resposta.")
    return json.loads(bloco.group(0))


def _normalizar_placa(d: dict) -> dict:
    out = {k: "" for k in CAMPOS_PLACA}
    if not isinstance(d, dict):
        return out
    for k in CAMPOS_PLACA:
        v = d.get(k)
        if v is None:
            continue
        out[k] = str(v).strip()
    return out


def ler_placa_gemini(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    key = obter_chave_gemini()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada. Defina a variável de ambiente "
            "ou adicione GEMINI_API_KEY em .streamlit/secrets.toml"
        )
    genai.configure(api_key=key)
    model = genai.GenerativeModel(_modelo_gemini())
    part = {"mime_type": mime_type, "data": image_bytes}
    r = model.generate_content([PROMPT_PLACA, part])
    text = _texto_resposta_gemini(r)
    raw = _extrair_json(text)
    return _normalizar_placa(raw)


def calcular_motor_gemini(dados_motor: dict) -> dict:
    key = obter_chave_gemini()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada. Defina a variável de ambiente "
            "ou adicione GEMINI_API_KEY em .streamlit/secrets.toml"
        )
    genai.configure(api_key=key)
    model = genai.GenerativeModel(_modelo_gemini())
    payload = json.dumps(dados_motor, ensure_ascii=False, indent=2)
    r = model.generate_content(PROMPT_CALCULOS.format(json_dados=payload))
    text = _texto_resposta_gemini(r)
    return _extrair_json(text)

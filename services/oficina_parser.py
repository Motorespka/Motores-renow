from __future__ import annotations

import json
import re
from typing import Any, Dict, List

DEFAULT_EXTRACTED: Dict[str, Any] = {
    "arquivo_origem": "",
    "texto_ocr": "",
    "texto_normalizado": "",
    "motor": {
        "marca": "",
        "modelo": "",
        "potencia": "",
        "cv": "",
        "rpm": "",
        "polos": "",
        "tensao": [],
        "corrente": [],
        "frequencia": "",
        "isolacao": "",
        "ip": "",
        "fator_servico": "",
        "tipo_motor": "",
        "fases": "",
        "numero_serie": "",
        "data_anotacao": "",
    },
    "bobinagem_principal": {
        "passos": [],
        "espiras": [],
        "fios": [],
        "ligacao": "",
        "observacoes": "",
        "quantidade_grupos": "",
        "quantidade_bobinas": "",
    },
    "bobinagem_auxiliar": {
        "passos": [],
        "espiras": [],
        "fios": [],
        "capacitor": "",
        "ligacao": "",
        "observacoes": "",
    },
    "mecanica": {
        "rolamentos": [],
        "eixo": "",
        "carcaca": "",
        "medidas": [],
        "comprimento_ponta": "",
        "observacoes": "",
    },
    "esquema": {
        "descricao_desenho": "",
        "distribuicao_bobinas": "",
        "ligacao": "",
        "ranhuras": "",
        "camadas": "",
        "observacoes": "",
    },
    "observacoes_gerais": "",
    "campos_extras": [],
    "confianca": {},
}


def _clone_default() -> Dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_EXTRACTED))


def parse_json_response(raw_text: str) -> Dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Resposta vazia do Gemini.")
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("JSON não encontrado na resposta do Gemini.")
    return json.loads(match.group(0))


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_to_text(v) for v in value if _to_text(v)]
    if isinstance(value, (int, float)):
        return [str(value)]

    text = _to_text(value)
    if not text:
        return []

    parts = re.split(r"\s*[;,|/\\]\s*|\s+-\s+|\s+\be\b\s+", text, flags=re.IGNORECASE)
    values = []
    for p in parts:
        p = p.strip()
        if p:
            values.append(p)
    if not values:
        return [text]

    # Caso comum em anotações de bobinagem: "6 8 10 12"
    if len(values) == 1 and re.fullmatch(r"\d+(?:\s+\d+)+", values[0]):
        return values[0].split()

    # Caso comum de fio: "8x17 1x18" (se vier sem vírgula)
    if len(values) == 1 and re.search(r"\d+\s*[xX]\s*\d+", values[0]):
        fio_tokens = re.findall(r"\d+\s*[xX]\s*\d+(?:[.,]\d+)?", values[0])
        if len(fio_tokens) > 1:
            return [t.replace(" ", "").lower().replace("x", "x") for t in fio_tokens]

    return values


def normalize_extracted_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    out = _clone_default()
    if not isinstance(payload, dict):
        return out

    out["arquivo_origem"] = _to_text(payload.get("arquivo_origem"))
    out["texto_ocr"] = _to_text(payload.get("texto_ocr"))
    out["texto_normalizado"] = _to_text(payload.get("texto_normalizado"))
    out["observacoes_gerais"] = _to_text(payload.get("observacoes_gerais"))

    motor = payload.get("motor") or {}
    for key in out["motor"].keys():
        if key in {"tensao", "corrente"}:
            out["motor"][key] = _to_list(motor.get(key))
        else:
            out["motor"][key] = _to_text(motor.get(key))

    for bloco in ["bobinagem_principal", "bobinagem_auxiliar"]:
        src = payload.get(bloco) or {}
        for key in out[bloco].keys():
            if key in {"passos", "espiras", "fios"}:
                out[bloco][key] = _to_list(src.get(key))
            else:
                out[bloco][key] = _to_text(src.get(key))

    mecanica = payload.get("mecanica") or {}
    for key in out["mecanica"].keys():
        if key in {"rolamentos", "medidas"}:
            out["mecanica"][key] = _to_list(mecanica.get(key))
        else:
            out["mecanica"][key] = _to_text(mecanica.get(key))

    esquema = payload.get("esquema") or {}
    for key in out["esquema"].keys():
        out["esquema"][key] = _to_text(esquema.get(key))

    confianca = payload.get("confianca")
    out["confianca"] = confianca if isinstance(confianca, dict) else {}

    extras = payload.get("campos_extras")
    if isinstance(extras, list):
        out["campos_extras"] = [
            {"chave": _to_text(e.get("chave")), "valor": _to_text(e.get("valor"))}
            for e in extras
            if isinstance(e, dict)
        ]

    return out


def to_supabase_payload(normalized: Dict[str, Any], image_paths: List[str], image_names: List[str]) -> Dict[str, Any]:
    motor = normalized.get("motor", {})
    return {
        "marca": motor.get("marca", ""),
        "modelo": motor.get("modelo", ""),
        "potencia": motor.get("potencia") or motor.get("cv") or "",
        "rpm": motor.get("rpm", ""),
        "tensao": ", ".join(motor.get("tensao", [])),
        "corrente": ", ".join(motor.get("corrente", [])),
        "observacoes": normalized.get("observacoes_gerais", ""),
        "dados_tecnicos_json": normalized,
        "leitura_gemini_json": normalized,
        "texto_bruto_extraido": normalized.get("texto_ocr", ""),
        "arquivo_origem": ", ".join(image_names),
        "imagens_origem": image_names,
        "imagens_urls": image_paths,
        "bobinagem_principal_json": normalized.get("bobinagem_principal", {}),
        "bobinagem_auxiliar_json": normalized.get("bobinagem_auxiliar", {}),
        "mecanica_json": normalized.get("mecanica", {}),
        "esquema_json": normalized.get("esquema", {}),
    }

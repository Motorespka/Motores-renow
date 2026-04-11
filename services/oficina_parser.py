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
    "oficina": {
        "dados_placa": {},
        "diagnostico": {
            "avisos": [],
            "alertas_validacao": [],
            "fonte": "",
            "data": "",
        },
        "servico_executado": {
            "descricao": "",
            "responsavel": "",
            "status": "",
            "data": "",
        },
        "calculos_aplicados": {
            "engenharia_automatica": {},
            "analise_fabrica": {},
        },
        "resultado_pos_servico": {
            "status": "",
            "observacoes": "",
            "data": "",
        },
        "aprendizado": {
            "sugestao_oficina": {},
            "sugestao_aprendizado": {},
            "ultima_atualizacao": "",
        },
        "parser_tecnico": {
            "espiras_bruto": [],
            "passo_bruto": [],
            "espiras_normalizado": [],
            "passo_normalizado": [],
            "confianca_dados": "baixa",
            "ligacao_tipo_eletrico": "",
            "ligacao_estrutura": "",
            "ligacao_observacao": "",
            "candidate_alternatives": [],
            "parse_note": "",
            "ambiguous": False,
            "needs_review": False,
            "status_revisao": "ok",
        },
        "sugestao_historica": {
            "ativo": False,
            "motivo": "",
            "confianca": "n/a",
            "amostra": 0,
            "sugestao": {},
        },
        "status_revisao": "ok",
        "historico_tecnico": [],
        "fluxo_fechado": [],
    },
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


def _to_list_from_any(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_to_text(v) for v in value if _to_text(v)]
    return _to_list(value)


def _first_numeric_text(value: Any) -> str:
    text = _to_text(value)
    if not text:
        return ""
    match = re.search(r"\d+(?:[.,]\d+)?", text)
    if not match:
        return ""
    return match.group(0).replace(",", ".")


def _join_slash(values: List[str]) -> str:
    cleaned = [v.strip() for v in values if _to_text(v)]
    return "/".join(cleaned)


def _normalize_rpm(value: Any) -> str:
    digits = "".join(ch for ch in _to_text(value) if ch.isdigit())
    if len(digits) < 3 or len(digits) > 5:
        return ""
    return digits


def _normalize_polos(value: Any) -> str:
    text = _to_text(value).upper().replace(" ", "")
    if not text:
        return ""
    if text.endswith("P") and text[:-1].isdigit():
        base = text[:-1]
    elif text.isdigit():
        base = text
    else:
        return ""
    if base not in {"2", "4", "6", "8", "10", "12"}:
        return ""
    return f"{base}P"


def _normalize_tensao(value: Any) -> str:
    if isinstance(value, list):
        text = _join_slash([_first_numeric_text(v) for v in value if _first_numeric_text(v)])
    else:
        nums = re.findall(r"\d{2,4}", _to_text(value))
        text = "/".join(nums[:3]) if nums else ""
    if not text:
        return ""
    return text if re.fullmatch(r"^[0-9]{2,4}(/[0-9]{2,4}){0,2}$", text) else ""


def _normalize_corrente(value: Any) -> str:
    if isinstance(value, list):
        items = []
        for v in value:
            n = _first_numeric_text(v)
            if n:
                items.append(n)
        text = "/".join(items[:2])
    else:
        nums = re.findall(r"\d+(?:[.,]\d+)?", _to_text(value))
        text = "/".join(n.replace(",", ".") for n in nums[:2])
    if not text:
        return ""
    return text if re.fullmatch(r"^[0-9]+([.][0-9]+)?(/[0-9]+([.][0-9]+)?)?$", text) else ""


def _normalize_frequencia(value: Any) -> str:
    text = _to_text(value).lower().replace(" ", "")
    if not text:
        return ""
    if text in {"50", "50hz"}:
        return "50Hz"
    if text in {"60", "60hz"}:
        return "60Hz"
    if text in {"50/60", "50/60hz"}:
        return "50/60Hz"
    return ""


def _normalize_potencia(value: Any) -> str:
    text = _to_text(value)
    if not text:
        return ""
    match = re.search(
        r"(\d+(?:[.,/]\d+)?)\s*(kva|kv\s*a|kvw|kv\s*w|kw|k\s*w|cv|hp|w)\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    number = match.group(1).replace(",", ".")
    unit_raw = match.group(2).lower().replace(" ", "")
    unit_map = {
        "kva": "kVA",
        "kvw": "kVW",
        "kw": "kW",
        "cv": "CV",
        "hp": "HP",
        "w": "W",
    }
    unit = unit_map.get(unit_raw, unit_raw.upper())
    return f"{number} {unit}"


def _confidence_level(conf: Dict[str, Any]) -> str:
    if not isinstance(conf, dict) or not conf:
        return "baixa"
    nums: List[float] = []
    for value in conf.values():
        if isinstance(value, (float, int)):
            nums.append(float(value))
    if not nums:
        return "baixa"
    avg = sum(nums) / len(nums)
    if avg >= 0.8:
        return "alta"
    if avg >= 0.6:
        return "media"
    return "baixa"


def _normalize_status_revisao(value: Any) -> str:
    text = _to_text(value).lower()
    if text == "revisar":
        return "revisar"
    # TODO: evoluir status_revisao na Fase 2 (validator)
    # incluir: incompleto, inconsistente, etc
    return "ok"


def _normalize_parser_tecnico(value: Any) -> Dict[str, Any]:
    src = value if isinstance(value, dict) else {}
    out = {
        "espiras_bruto": _to_list_from_any(src.get("espiras_bruto")),
        "passo_bruto": _to_list_from_any(src.get("passo_bruto")),
        "espiras_normalizado": _to_list_from_any(src.get("espiras_normalizado")),
        "passo_normalizado": _to_list_from_any(src.get("passo_normalizado")),
        "confianca_dados": _to_text(src.get("confianca_dados")) or "baixa",
        "ligacao_tipo_eletrico": _to_text(src.get("ligacao_tipo_eletrico")),
        "ligacao_estrutura": _to_text(src.get("ligacao_estrutura")),
        "ligacao_observacao": _to_text(src.get("ligacao_observacao")),
        "candidate_alternatives": _to_list_from_any(src.get("candidate_alternatives")),
        "parse_note": _to_text(src.get("parse_note")),
        "ambiguous": bool(src.get("ambiguous")),
        "needs_review": bool(src.get("needs_review")),
        "status_revisao": _normalize_status_revisao(src.get("status_revisao")),
    }
    return out


def _pick_row_value(row: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return None


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

    oficina_payload = payload.get("oficina")
    if isinstance(oficina_payload, dict):
        default_oficina = out["oficina"]
        merged = json.loads(json.dumps(default_oficina))
        for key in default_oficina.keys():
            src_value = oficina_payload.get(key)
            if isinstance(default_oficina[key], dict) and isinstance(src_value, dict):
                merged[key].update(src_value)
            elif isinstance(default_oficina[key], list) and isinstance(src_value, list):
                merged[key] = src_value
            elif src_value is not None:
                merged[key] = src_value
        out["oficina"] = merged

    oficina = out.get("oficina")
    if isinstance(oficina, dict):
        oficina["status_revisao"] = _normalize_status_revisao(oficina.get("status_revisao"))
        oficina["parser_tecnico"] = _normalize_parser_tecnico(oficina.get("parser_tecnico"))
        sugestao = oficina.get("sugestao_historica")
        if not isinstance(sugestao, dict):
            sugestao = {}
        try:
            amostra = int(sugestao.get("amostra") or 0)
        except Exception:
            amostra = 0
        oficina["sugestao_historica"] = {
            "ativo": bool(sugestao.get("ativo")),
            "motivo": _to_text(sugestao.get("motivo")),
            "confianca": _to_text(sugestao.get("confianca")) or "n/a",
            "amostra": amostra,
            "sugestao": sugestao.get("sugestao") if isinstance(sugestao.get("sugestao"), dict) else {},
        }
        out["oficina"] = oficina

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


def to_motores_schema_payload(normalized: Dict[str, Any], image_paths: List[str], image_names: List[str]) -> Dict[str, Any]:
    motor = normalized.get("motor", {}) if isinstance(normalized.get("motor"), dict) else {}
    principal = normalized.get("bobinagem_principal", {}) if isinstance(normalized.get("bobinagem_principal"), dict) else {}
    auxiliar = normalized.get("bobinagem_auxiliar", {}) if isinstance(normalized.get("bobinagem_auxiliar"), dict) else {}
    mecanica = normalized.get("mecanica", {}) if isinstance(normalized.get("mecanica"), dict) else {}
    esquema = normalized.get("esquema", {}) if isinstance(normalized.get("esquema"), dict) else {}

    ligacoes = []
    for item in [principal.get("ligacao"), auxiliar.get("ligacao"), esquema.get("ligacao")]:
        text = _to_text(item)
        if text:
            ligacoes.extend(_to_list(text))

    camadas = _to_list(esquema.get("camadas"))
    fios = _to_list_from_any(principal.get("fios"))
    espiras = _to_list_from_any(principal.get("espiras"))
    passos = _to_list_from_any(principal.get("passos"))

    arquivo_origem = ", ".join([n for n in image_names if _to_text(n)]).strip()
    if not arquivo_origem:
        arquivo_origem = _to_text(normalized.get("arquivo_origem")) or "upload_manual"

    payload = {
        "arquivo_origem": arquivo_origem,
        "marca": _to_text(motor.get("marca")) or None,
        "tipo_motor": _to_text(motor.get("tipo_motor")) or None,
        "potencia": _normalize_potencia(motor.get("potencia") or motor.get("cv")) or None,
        "rpm": _normalize_rpm(motor.get("rpm")) or None,
        "tensao": _normalize_tensao(motor.get("tensao")) or None,
        "corrente": _normalize_corrente(motor.get("corrente")) or None,
        "frequencia": _normalize_frequencia(motor.get("frequencia")) or None,
        "polos": _normalize_polos(motor.get("polos")) or None,
        "carcaca": _to_text(mecanica.get("carcaca")) or None,
        "ranhuras": _to_text(esquema.get("ranhuras")) or None,
        "pacote_mm": None,
        "diametro_mm": None,
        "capacitor": _to_text(auxiliar.get("capacitor")) or None,
        "fio": fios,
        "espiras": espiras,
        "passo": passos,
        "ligacao": ligacoes,
        "camada": camadas,
        "tem_principal": bool(passos or espiras or fios or _to_text(principal.get("ligacao"))),
        "tem_auxiliar": bool(
            _to_list_from_any(auxiliar.get("passos"))
            or _to_list_from_any(auxiliar.get("espiras"))
            or _to_list_from_any(auxiliar.get("fios"))
            or _to_text(auxiliar.get("capacitor"))
            or _to_text(auxiliar.get("ligacao"))
        ),
        "confianca_extracao": _confidence_level(normalized.get("confianca") or {}),
    }

    return payload


def build_normalized_from_motor_row(row: Dict[str, Any]) -> Dict[str, Any]:
    out = _clone_default()
    variaveis = _pick_row_value(row, "VariaveisSite", "variaveis_site")
    if isinstance(variaveis, str):
        try:
            variaveis = json.loads(variaveis)
        except Exception:
            variaveis = {}
    if not isinstance(variaveis, dict):
        variaveis = {}

    out["arquivo_origem"] = _to_text(
        _pick_row_value(row, "arquivo_origem", "ArquivoOrigem")
        or variaveis.get("ArquivoOrigem")
    )

    motor = out["motor"]
    motor["marca"] = _to_text(_pick_row_value(row, "marca", "Marca") or variaveis.get("Marca"))
    motor["modelo"] = _to_text(_pick_row_value(row, "modelo", "Modelo") or variaveis.get("Modelo"))
    motor["potencia"] = _to_text(_pick_row_value(row, "potencia", "Potencia") or variaveis.get("Potencia"))
    motor["cv"] = motor["potencia"]
    motor["rpm"] = _to_text(_pick_row_value(row, "rpm", "Rpm") or variaveis.get("Rpm"))
    motor["tensao"] = _to_list_from_any(_pick_row_value(row, "tensao", "Tensao") or variaveis.get("Tensao"))
    motor["corrente"] = _to_list_from_any(_pick_row_value(row, "corrente", "Corrente") or variaveis.get("Corrente"))
    motor["frequencia"] = _to_text(_pick_row_value(row, "frequencia", "Frequencia") or variaveis.get("Frequencia"))
    polos_raw = _to_text(_pick_row_value(row, "polos", "Polos") or variaveis.get("Polos"))
    motor["polos"] = polos_raw[:-1] if polos_raw.upper().endswith("P") else polos_raw
    motor["tipo_motor"] = _to_text(_pick_row_value(row, "tipo_motor", "TipoMotor") or variaveis.get("TipoMotor"))
    motor["fases"] = _to_text(_pick_row_value(row, "fases", "Fases") or variaveis.get("Fases"))

    out["bobinagem_principal"]["fios"] = _to_list_from_any(_pick_row_value(row, "fio", "Fio"))
    out["bobinagem_principal"]["espiras"] = _to_list_from_any(_pick_row_value(row, "espiras", "Espiras"))
    out["bobinagem_principal"]["passos"] = _to_list_from_any(_pick_row_value(row, "passo", "Passo"))
    ligacoes = _to_list_from_any(_pick_row_value(row, "ligacao", "Ligacao"))
    out["bobinagem_principal"]["ligacao"] = ", ".join(ligacoes)
    out["esquema"]["ligacao"] = ", ".join(ligacoes)
    out["esquema"]["ranhuras"] = _to_text(_pick_row_value(row, "ranhuras", "Ranhuras") or variaveis.get("Ranhuras"))
    out["esquema"]["camadas"] = ", ".join(_to_list_from_any(_pick_row_value(row, "camada", "Camada")))
    out["mecanica"]["carcaca"] = _to_text(_pick_row_value(row, "carcaca", "Carcaca") or variaveis.get("Carcaca"))
    out["bobinagem_auxiliar"]["capacitor"] = _to_text(_pick_row_value(row, "capacitor", "Capacitor") or variaveis.get("Capacitor"))

    out["observacoes_gerais"] = _to_text(_pick_row_value(row, "observacoes", "Observacoes"))
    out["texto_ocr"] = _to_text(_pick_row_value(row, "texto_bruto_extraido", "TextoBrutoExtraido"))
    return out

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Dict, Iterable

NOT_INFORMED = "Não informado"

MOTOR_IMAGE_FALLBACKS = [
    "https://images.unsplash.com/photo-1763952626662-419b004e1783?auto=format&fit=crop&fm=jpg&q=55&w=1800",
    "https://images.unsplash.com/photo-1763952626662-419b004e1783?auto=format&fit=crop&fm=jpg&q=45&w=1200",
]

# Aliases orientados pelo schema real da tabela public.motores.
ALIASES = {
    "marca": ["marca", "Marca", "fabricante", "Fabricante", "brand", "manufacturer"],
    "modelo": ["modelo", "Modelo", "num_serie", "codigo_interno", "modelo_motor", "nome"],
    "potencia": ["potencia_hp_cv", "potencia_kw", "potencia", "potencia_cv", "potencia_hp", "cv", "cavalaria"],
    "rpm": ["rpm_nominal", "rpm", "rotacao", "rotacao_nominal"],
    "corrente": ["corrente_nominal_a", "corrente", "amperagem", "corrente_nominal"],
    "polos": ["polos", "numero_polos", "poles", "n_polos"],
    "fases": ["fases", "fase", "tipo_fase", "tipo_enrolamento"],
    "tensao": ["tensao_v", "tensao", "voltagem", "voltage", "v"],
    "frequencia": ["frequencia_hz", "frequencia", "hz"],
    "imagem": [
        "url_foto_placa",
        "url_desenho_tecnico",
        "imagem_url",
        "image_url",
        "foto_url",
        "url_imagem",
        "motor_image",
        "photo_url",
        "imagem",
        "foto",
    ],
}


def _to_dict_json(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip().startswith("{"):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def dados_tecnicos_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """JSON técnico na linha (snake_case ou PascalCase)."""
    for key in (
        "dados_tecnicos_json",
        "DadosTecnicosJson",
        "DadosTecnicosJSON",
        "leitura_gemini_json",
        "LeituraGeminiJson",
    ):
        raw = row.get(key)
        if raw:
            data = _to_dict_json(raw)
            if data:
                return data
    return {}


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        raw = value.strip().lower()
        return raw in {"", "-", "none", "nan", "null", "n/d", "na", "n.a."}
    return False


def friendly(value: Any) -> str:
    if is_empty(value):
        return NOT_INFORMED
    return str(value).strip()


def normalize_key(key: Any) -> str:
    txt = unicodedata.normalize("NFKD", str(key).strip().lower())
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    txt = re.sub(r"[^a-z0-9]+", "_", txt).strip("_")
    return txt


def build_normalized_index(row: Dict[str, Any]) -> Dict[str, Any]:
    idx: Dict[str, Any] = {}
    for raw_key, raw_value in row.items():
        norm = normalize_key(raw_key)
        if not norm:
            continue
        if norm not in idx or (is_empty(idx.get(norm)) and not is_empty(raw_value)):
            idx[norm] = raw_value
    return idx


def pick_value(row: Dict[str, Any], aliases: Iterable[str]) -> Any:
    norm_idx = row.get("_norm_index")
    if not isinstance(norm_idx, dict):
        norm_idx = build_normalized_index(row)

    for alias in aliases:
        if alias in row and not is_empty(row.get(alias)):
            return row.get(alias)
        val = norm_idx.get(normalize_key(alias))
        if not is_empty(val):
            return val
    return None


def normalize_motor_record(row: Dict[str, Any]) -> Dict[str, Any]:
    motor = dict(row)
    if motor.get("id") in (None, "") and motor.get("Id") not in (None, ""):
        motor["id"] = motor.get("Id")
    motor["_norm_index"] = build_normalized_index(motor)

    motor["marca"] = pick_value(motor, ALIASES["marca"])
    motor["modelo"] = pick_value(motor, ALIASES["modelo"])
    motor["potencia_hp_cv"] = pick_value(motor, ALIASES["potencia"])
    motor["rpm_nominal"] = pick_value(motor, ALIASES["rpm"])
    motor["corrente_nominal_a"] = pick_value(motor, ALIASES["corrente"])
    motor["polos"] = pick_value(motor, ALIASES["polos"])
    motor["fases"] = pick_value(motor, ALIASES["fases"])
    motor["tensao_v"] = pick_value(motor, ALIASES["tensao"])
    motor["frequencia_hz"] = pick_value(motor, ALIASES["frequencia"])
    motor["imagem_motor_url"] = resolve_motor_image_url(motor)

    if is_empty(motor.get("modelo")):
        seq = motor.get("cadastro_seq")
        if not is_empty(seq):
            try:
                motor["modelo"] = f"Registro #{int(seq)}"
            except (TypeError, ValueError):
                motor["modelo"] = f"Registro #{friendly(seq)}"
        else:
            motor["modelo"] = f"Registro #{friendly(motor.get('id'))}"
    return motor


def resolve_motor_image_url(motor: Dict[str, Any]) -> str:
    image = pick_value(motor, ALIASES["imagem"])
    if not is_empty(image):
        url = str(image).strip()
        if url.startswith("http://") or url.startswith("https://"):
            return url

    raw_id = str(motor.get("id", "0"))
    only_digits = "".join(ch for ch in raw_id if ch.isdigit()) or "0"
    idx = int(only_digits) % len(MOTOR_IMAGE_FALLBACKS)
    return MOTOR_IMAGE_FALLBACKS[idx]


def display_title(motor: Dict[str, Any]) -> str:
    for aliases in [ALIASES["marca"], ["fabricante"], ALIASES["modelo"], ["codigo_interno"]]:
        value = pick_value(motor, aliases)
        if not is_empty(value):
            return str(value).strip().upper()
    return f"REGISTRO #{friendly(motor.get('id'))}"


def display_subtitle(motor: Dict[str, Any]) -> str:
    codigo = pick_value(motor, ["codigo_interno"])
    if not is_empty(codigo):
        return f"ID: {friendly(codigo)}"
    return f"ID: {friendly(motor.get('id'))}"

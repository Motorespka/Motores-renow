from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable

NOT_INFORMED = "Não informado"

MOTOR_IMAGE_FALLBACKS = [
    "https://images.unsplash.com/photo-1763952626662-419b004e1783?auto=format&fit=crop&fm=jpg&q=60&w=1600",
    "https://images.unsplash.com/photo-1763952626662-419b004e1783?auto=format&fit=crop&fm=jpg&q=50&w=2000",
]

ALIASES = {
    "marca": ["marca", "fabricante", "brand", "manufacturer", "marca_motor"],
    "modelo": ["modelo", "modelo_motor", "nome", "linha", "num_serie", "codigo_interno", "codigo"],
    "potencia": [
        "potencia_hp_cv",
        "potencia",
        "potencia_kw",
        "potencia_cv",
        "potencia_hp",
        "cv",
        "cavalaria",
        "horsepower",
    ],
    "rpm": ["rpm_nominal", "rpm", "rotacao", "rotacao_nominal", "velocidade_nominal"],
    "corrente": ["corrente_nominal_a", "corrente", "amperagem", "corrente_nominal", "current"],
    "polos": ["polos", "numero_polos", "poles", "n_polos", "qtd_polos"],
    "fases": ["fases", "fase", "tipo_fase", "tipo_enrolamento", "phases"],
    "tensao": ["tensao_v", "tensao", "voltagem", "voltage", "v"],
    "imagem": ["imagem_url", "image_url", "foto_url", "url_imagem", "motor_image", "photo_url", "imagem", "foto"],
}


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        raw = value.strip().lower()
        return raw in {"", "none", "nan", "null", "n/d", "na", "n.a."}
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
    motor["_norm_index"] = build_normalized_index(motor)

    motor["marca"] = pick_value(motor, ALIASES["marca"])
    motor["modelo"] = pick_value(motor, ALIASES["modelo"])
    motor["potencia_hp_cv"] = pick_value(motor, ALIASES["potencia"])
    motor["rpm_nominal"] = pick_value(motor, ALIASES["rpm"])
    motor["corrente_nominal_a"] = pick_value(motor, ALIASES["corrente"])
    motor["polos"] = pick_value(motor, ALIASES["polos"])
    motor["fases"] = pick_value(motor, ALIASES["fases"])
    motor["tensao_v"] = pick_value(motor, ALIASES["tensao"])
    motor["imagem_motor_url"] = resolve_motor_image_url(motor)

    if is_empty(motor.get("modelo")):
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

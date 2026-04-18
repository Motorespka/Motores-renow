"""
Presets visuais do holograma (consulta/cadastro) mapeados por IP/carcaca ou escolha explicita.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# (id interno, rotulo na UI)
HOLOGRAM_CHOICES: List[Tuple[str, str]] = [
    ("auto", "Automatico (IP + carcaca)"),
    ("generico", "Generico IEC"),
    ("ip55_iso", "IP55 fechado (aleta padrao)"),
    ("ip21_aberto", "IP21 / gotejamento"),
    ("nema_mono", "NEMA monofásico compacto"),
    ("iec_w22", "IEC ferro W22 / aletas densas"),
    ("trif_grande", "Trifasico grande porte"),
    ("servo_compacto", "IP66 / servo compacto"),
]

HOLOGRAM_LABELS = {k: v for k, v in HOLOGRAM_CHOICES}


def _txt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(str(x).strip() for x in v if str(x).strip())
    return str(v).strip()


def _motor_block(m: Dict[str, Any]) -> Dict[str, Any]:
    data = m.get("dados_tecnicos_json") if isinstance(m.get("dados_tecnicos_json"), dict) else {}
    return data.get("motor") if isinstance(data.get("motor"), dict) else {}


def _mec_block(m: Dict[str, Any]) -> Dict[str, Any]:
    data = m.get("dados_tecnicos_json") if isinstance(m.get("dados_tecnicos_json"), dict) else {}
    return data.get("mecanica") if isinstance(data.get("mecanica"), dict) else {}


def _infer_preset(m: Dict[str, Any]) -> str:
    motor = _motor_block(m)
    mec = _mec_block(m)
    ui = m.get("_consulta_ui") if isinstance(m.get("_consulta_ui"), dict) else {}

    ip_raw = _txt(motor.get("ip") or m.get("ip") or m.get("Ip"))
    car = _txt(
        mec.get("carcaca")
        or motor.get("carcaca")
        or ui.get("carcaca")
        or m.get("carcaca")
    ).upper()
    fases = _txt(
        motor.get("fases") or m.get("fases") or (ui.get("fases") if isinstance(ui, dict) else None)
    ).lower()
    tipo = _txt(
        motor.get("tipo_motor")
        or m.get("tipo_motor")
        or (ui.get("tipo_motor") if isinstance(ui, dict) else None)
    ).lower()
    cap = _txt((m.get("dados_tecnicos_json") or {}).get("bobinagem_auxiliar", {}).get("capacitor") if isinstance(m.get("dados_tecnicos_json"), dict) else "")

    if "IPW" in ip_raw.upper() or "IP66" in ip_raw.upper() or "IP 66" in ip_raw.upper():
        return "servo_compacto"
    m_ip = re.search(r"IP\s*W?\s*([0-9]{2})", ip_raw, re.I)
    if m_ip:
        code = m_ip.group(1)
        if code in {"66", "65"}:
            return "servo_compacto"
        if code in {"55", "54", "56"}:
            return "ip55_iso"
        if code in {"21", "20", "22", "23"}:
            return "ip21_aberto"
    if "NEMA" in car or "Nema" in car:
        return "nema_mono"
    if "W22" in car or "W21" in car or "WEG" in car:
        return "iec_w22"

    if "mono" in fases or "mono" in tipo or cap:
        return "nema_mono"

    pot = _txt(m.get("potencia") or motor.get("potencia"))
    nums = re.findall(r"\d+", pot)
    if nums and int(nums[0]) >= 40:
        return "trif_grande"

    return "generico"


def resolve_hologram_preset(m: Dict[str, Any]) -> str:
    """
    Retorna id do preset. Se motor.holograma_preset == 'auto' ou vazio, infere.
    """
    motor = _motor_block(m)
    explicit = _txt(motor.get("holograma_preset")).lower().replace(" ", "_")
    if explicit and explicit != "auto" and explicit in HOLOGRAM_LABELS:
        return explicit
    return _infer_preset(m)


def hologram_choice_label(preset_id: str) -> str:
    return HOLOGRAM_LABELS.get(preset_id, preset_id)

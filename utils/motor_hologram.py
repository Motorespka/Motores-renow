"""
Presets visuais do holograma (consulta/cadastro) mapeados por IP/carcaca ou escolha explicita.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple, Optional

from utils.motor_hologram_glb import (
    iec63_etiqueta_na_carcaca_sem_ne_ma,
    infer_hologram_preset_familia_nema_silueta,
    motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha,
    nema_56_somente_ficha_mecanica,
    _is_nema_42_frame,
)

# (id interno, rotulo na UI)
HOLOGRAM_CHOICES: List[Tuple[str, str]] = [
    ("auto", "Automatico (IP + carcaca)"),
    ("generico", "Generico IEC"),
    ("ip55_iso", "IP55 fechado (aleta padrao)"),
    ("ip21_aberto", "IP21 / gotejamento"),
    ("liso_56", "Liso, peq., c/ pes (42, 48, 56, 56H-D-L-Y, mesma silh. 3D)"),
    ("cface_56", "NEMA 56C / 48C / C-face (flange)"),
    ("pump_56j", "Bomba / 56J (montagem diametro)"),
    ("nema_footless", "Sem pes / so face (silhueta distinta)"),
    ("nema_mono", "NEMA monofasico compacto (legado)"),
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
        or mec.get("Carcaca")
        or motor.get("carcaca")
        or motor.get("Carcaca")
        or ui.get("carcaca")
        or ui.get("Carcaca")
        or m.get("carcaca")
        or m.get("Carcaca")
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
    car_cmp = re.sub(r"[\s._\-/]+", "", car)
    if "IEC63" in car_cmp and "NEMA" not in car and not nema_56_somente_ficha_mecanica(m):
        if motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha(m) or iec63_etiqueta_na_carcaca_sem_ne_ma(m):
            return "generico"
    pr_nema: Optional[str] = infer_hologram_preset_familia_nema_silueta(m)
    if pr_nema:
        return pr_nema
    if "W22" in car or "W21" in car or "WEG" in car:
        return "iec_w22"
    if "TEFC" in car and ("ALET" in car or "ALETA" in car or "W22" in car or "W21" in car):
        return "iec_w22"
    if "NEMA" in car:
        return "liso_56"
    if ("mono" in fases or "mono" in tipo or cap) and "IEC63" not in car_cmp:
        return "liso_56"

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
        if (
            explicit in ("nema_mono", "liso_56")
            and not nema_56_somente_ficha_mecanica(m)
            and not _is_nema_42_frame(m)
        ):
            if motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha(m) or iec63_etiqueta_na_carcaca_sem_ne_ma(
                m
            ):
                return "generico"
        return explicit
    return _infer_preset(m)


def hologram_choice_label(preset_id: str) -> str:
    return HOLOGRAM_LABELS.get(preset_id, preset_id)

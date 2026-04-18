"""
URLs de modelos GLB para o holograma 3D (<model-viewer>).
Prioridade: motor.holograma_glb_url no JSON > env por preset > HOLOGRAM_GLB_DEFAULT > demo (opcional).
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

# Modelo de demonstração (Google); serve para validar viewer + rede sem teus ficheiros.
DEMO_GLB_URL = "https://modelviewer.dev/shared-assets/models/Astronaut.glb"


def _read_secret_or_env(*names: str) -> str:
    for name in names:
        try:
            import streamlit as st

            try:
                v = st.secrets.get(name)
                if v:
                    return str(v).strip()
            except Exception:
                pass
        except Exception:
            pass
        v = os.environ.get(name)
        if v:
            return str(v).strip()
    return ""


def _motor_json(m: Dict[str, Any]) -> Dict[str, Any]:
    data = m.get("dados_tecnicos_json") if isinstance(m.get("dados_tecnicos_json"), dict) else {}
    motor = data.get("motor") if isinstance(data.get("motor"), dict) else {}
    return motor if isinstance(motor, dict) else {}


def _path_looks_glb(u: str) -> bool:
    base = u.strip().split("?", 1)[0].split("#", 1)[0].lower()
    return base.endswith(".glb")


def resolve_model_glb_url(m: Dict[str, Any], preset: str) -> Optional[str]:
    """
    Retorna URL absoluta https para .glb, ou None para usar holograma CSS.
    """
    motor = _motor_json(m)
    for key in ("holograma_glb_url", "holograma_glb", "HologramaGlbUrl"):
        raw = motor.get(key)
        if raw:
            u = str(raw).strip()
            if u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
                return u

    preset_u = preset.upper().replace("-", "_")
    preset_l = preset.lower()
    for name in (
        f"HOLOGRAM_GLB_{preset_u}",
        f"HOLOGRAM_GLB_{preset_l}",
        "HOLOGRAM_GLB_DEFAULT",
        "MOTORES_HOLOGRAM_GLB_DEFAULT",
    ):
        u = _read_secret_or_env(name)
        if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
            return u

    demo = _read_secret_or_env("HOLOGRAM_DEMO", "MOTORES_HOLOGRAM_DEMO").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if demo:
        return DEMO_GLB_URL

    return None

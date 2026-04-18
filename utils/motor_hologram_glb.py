"""
URLs de modelos GLB para o holograma 3D (<model-viewer>).
Prioridade: motor.holograma_glb_url no JSON > HOLOGRAM_GLB_MOTOR_<id> > env por preset >
HOLOGRAM_GLB_DEFAULT > HOLOGRAM_GLB_NEMA48 (se carcaca NEMA 48) > demo (opcional).

Sem URL valida: UI usa malha procedural aproximada em Three.js (no browser) ou, com
`HOLOGRAM_LEGACY_CSS=1`, a silhueta CSS antiga. GLB real continua a ser o unico desenho tecnico fiel.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional

# Modelo de demonstração (Google); só com HOLOGRAM_DEMO=1 — nunca confundir com carcaça real.
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


def _mecanica_json(m: Dict[str, Any]) -> Dict[str, Any]:
    data = m.get("dados_tecnicos_json") if isinstance(m.get("dados_tecnicos_json"), dict) else {}
    mec = data.get("mecanica") if isinstance(data.get("mecanica"), dict) else {}
    return mec if isinstance(mec, dict) else {}


def _motor_id_str(m: Dict[str, Any]) -> str:
    for k in ("id", "Id", "motor_id"):
        v = m.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def _carcaca_blob(m: Dict[str, Any]) -> str:
    parts = [
        str(m.get("carcaca") or ""),
        str(_mecanica_json(m).get("carcaca") or ""),
        str(_motor_json(m).get("carcaca") or ""),
    ]
    ui = m.get("_consulta_ui") if isinstance(m.get("_consulta_ui"), dict) else {}
    parts.append(str(ui.get("carcaca") or ""))
    return " ".join(parts)


def hologram_carcaca_context(m: Dict[str, Any]) -> str:
    """Texto agregado da carcaça (NEMA/IEC) para heurísticas do holograma procedural."""
    return _carcaca_blob(m).strip()[:260]


def _is_nema_48_frame(m: Dict[str, Any]) -> bool:
    s = _carcaca_blob(m).upper()
    if not s.strip():
        return False
    if re.search(r"NEMA\s*[-_]?\s*48\b", s):
        return True
    return "NEMA" in s and "48" in s


def _path_looks_glb(u: str) -> bool:
    base = u.strip().split("?", 1)[0].split("#", 1)[0].lower()
    return base.endswith(".glb")


def resolve_model_glb_url(m: Dict[str, Any], preset: str) -> Optional[str]:
    """
    Retorna URL absoluta https para .glb, ou None para holograma procedural (Three.js) / CSS legado.
    """
    motor = _motor_json(m)
    for key in ("holograma_glb_url", "holograma_glb", "HologramaGlbUrl"):
        raw = motor.get(key)
        if raw:
            u = str(raw).strip()
            if u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
                return u

    mid = _motor_id_str(m)
    if mid:
        u = _read_secret_or_env(f"HOLOGRAM_GLB_MOTOR_{mid}", f"MOTORES_HOLOGRAM_GLB_MOTOR_{mid}")
        if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
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

    if _is_nema_48_frame(m):
        u = _read_secret_or_env("HOLOGRAM_GLB_NEMA48", "MOTORES_HOLOGRAM_GLB_NEMA48")
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

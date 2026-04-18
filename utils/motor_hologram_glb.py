"""
URLs de modelos GLB para o holograma 3D (<model-viewer>).
Prioridade: motor.holograma_glb_url no JSON > HOLOGRAM_GLB_MOTOR_<id> > env por preset >
HOLOGRAM_GLB_DEFAULT > HOLOGRAM_GLB_NEMA48 (se carcaca NEMA 48) >
ficheiros em static/glb (starter pack, embutidos em data URL base64 por defeito) > demo (opcional).
Desligar pack: HOLOGRAM_USE_STARTER_PACK=0. HTTP em vez de data: HOLOGRAM_STARTER_PACK_HTTP=1 (+ static serving).

Sem URL valida: UI usa malha procedural aproximada em Three.js (no browser) ou, com
`HOLOGRAM_LEGACY_CSS=1`, a silhueta CSS antiga. GLB real continua a ser o unico desenho tecnico fiel.
"""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path
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


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _starter_glb_path(name: str) -> Path:
    return _repo_root() / "static" / "glb" / name


def _app_public_base() -> str:
    """Base URL do app (para /app/static/... no model-viewer dentro do iframe)."""
    try:
        import streamlit as st

        h = dict(getattr(st.context, "headers", {}) or {})
        host = str(h.get("Host") or h.get("host") or "").strip()
        if not host:
            return ""
        xf = str(h.get("X-Forwarded-Proto") or h.get("x-forwarded-proto") or "").strip().lower()
        if xf == "https":
            proto = "https"
        elif xf == "http":
            proto = "http"
        else:
            proto = "https" if "streamlit.app" in host else "http"
        return f"{proto}://{host}".rstrip("/")
    except Exception:
        return ""


def _starter_pack_http_url(filename: str) -> Optional[str]:
    path = _starter_glb_path(filename)
    if not path.is_file():
        return None
    base = _app_public_base() or "http://localhost:8501"
    return f"{base}/app/static/glb/{filename}"


def _starter_pack_embedded_src(filename: str) -> Optional[str]:
    """
    data:...base64 para o model-viewer dentro do iframe srcdoc (evita /app/static/ bloqueado ou origem opaca).
    """
    path = _starter_glb_path(filename)
    if not path.is_file():
        return None
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if len(raw) > 1_500_000:
        return None
    b64 = base64.standard_b64encode(raw).decode("ascii")
    return f"data:model/gltf-binary;base64,{b64}"


def _starter_pack_disabled() -> bool:
    """Desligar com HOLOGRAM_USE_STARTER_PACK=0 (vazio = ligado se existirem ficheiros)."""
    v = _read_secret_or_env("HOLOGRAM_USE_STARTER_PACK", "MOTORES_HOLOGRAM_USE_STARTER_PACK").strip().lower()
    if not v:
        return False
    return v in ("0", "false", "no", "off")


def _pick_starter_pack_filename(m: Dict[str, Any], preset: str) -> str:
    """Mapeia carcaça / preset → ficheiro em static/glb/."""
    car = _carcaca_blob(m).upper()
    compact = re.sub(r"\s+", "", car)

    if "FREIO" in car or "MOTOFREIO" in compact or "BRAKE" in car:
        return "motor_freio_iec.glb"
    if "BOMBA" in car or "MONOBLOC" in car or "JP" in car:
        return "bomba_jp.glb"

    if re.search(r"NEMA\s*[-_]?\s*48\b", car) or (
        "NEMA" in car and re.search(r"\b48\b", car) and not re.search(r"\b56\b", car)
    ):
        return "monofasico_48.glb"
    if "NEMA" in car and "56C" in compact:
        return "nema_56c.glb"
    if re.search(r"NEMA\s*[-_]?\s*56\b", car) or ("NEMA" in car and "56" in car):
        return "nema_56.glb"

    if "B35" in car or "90L" in car:
        return "iec_90l_b35.glb"
    if "B14" in car or ("71" in car and "IEC" in car):
        return "iec_71_b14.glb"
    if "B5" in car and "63" in car:
        return "iec_63_b5.glb"
    if "B3" in car and "63" in car:
        return "iec_63_b3.glb"
    if "IEC" in car and "63" in car:
        return "iec_63_b3.glb"

    if preset == "nema_mono":
        return "nema_56.glb"
    if preset in ("iec_w22", "ip55_iso", "generico"):
        return "iec_90l_b35.glb"
    if preset == "trif_grande":
        return "iec_90l_b35.glb"
    if preset == "servo_compacto":
        return "iec_71_b14.glb"
    if preset == "ip21_aberto":
        return "iec_63_b5.glb"
    return "iec_63_b3.glb"


def _resolve_starter_pack_url(m: Dict[str, Any], preset: str) -> Optional[str]:
    if _starter_pack_disabled():
        return None
    name = _pick_starter_pack_filename(m, preset)
    if _read_secret_or_env("HOLOGRAM_STARTER_PACK_HTTP", "MOTORES_HOLOGRAM_STARTER_PACK_HTTP").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return _starter_pack_http_url(name)
    return _starter_pack_embedded_src(name)


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
    Retorna URL https/http, data URL (starter pack), ou None para Three.js / CSS legado.
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

    sp = _resolve_starter_pack_url(m, preset)
    if sp:
        return sp

    demo = _read_secret_or_env("HOLOGRAM_DEMO", "MOTORES_HOLOGRAM_DEMO").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if demo:
        return DEMO_GLB_URL

    return None

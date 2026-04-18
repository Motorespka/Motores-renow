"""
URLs de modelos GLB para o holograma 3D (<model-viewer>).
NEMA 56: deteção so em **Mecanica (carcaca) e quadro/NEMA** na ficha (sem texto OCR). >
Prioridade: motor.holograma_glb_url no JSON > HOLOGRAM_GLB_MOTOR_<id> >
`HOLOGRAM_CARCACA_NEMA56_STRICT=1` → nada alem de JSON/MOTOR/NEMA56 (carcaca) + secret NEMA56; nao starter, nao default. Senao, fluxo completo. >
HOLOGRAM_GLB_NEMA56 (URL .glb para familia 56, 56C, 56H, 56J, 56Y) >
GLB por tipo de carcaça (HOLOGRAM_GLB_WEG_STYLE_HOUSING + match); o mesmo URL entra na cadeia DEFAULT
se HOLOGRAM_GLB_WEG_STYLE_ONLY_MATCHED nao estiver ligado (URL global no Cloud sem regra de carcaca).
HOLOGRAM_CARCACA_GLB_CONTAINS / HOLOGRAM_CARCACA_GLB_RULE: ver motor_matches_weg_style_carcaca_for_glb. >
HOLOGRAM_GLB_DEFAULT (global Cloud; antes dos presets para nao ficar preso a GLB antigo por preset) >
env HOLOGRAM_GLB_<PRESET> > HOLOGRAM_GLB_NEMA48 (se carcaca NEMA 48) >
GLB em disco opt-in (HOLOGRAM_TEST_DISK_GLB=1; HOLOGRAM_TEST_DISK_GLB_FILE) >
ficheiros em static/glb (starter pack; pequenos em data URL) > demo (opcional).
Pack: HOLOGRAM_USE_STARTER_PACK=0. HTTP pack: HOLOGRAM_STARTER_PACK_HTTP=1.

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
    """Lê Streamlit secrets ou os.environ; remove aspas TOML à volta de URLs por engano."""

    def _normalize(val: str) -> str:
        s = str(val).strip()
        if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
            s = s[1:-1].strip()
        return s

    for name in names:
        try:
            import streamlit as st

            try:
                sec = getattr(st, "secrets", None)
                if sec is not None:
                    try:
                        v = sec[name]
                    except Exception:
                        v = None
                    if v is not None and str(v).strip():
                        return _normalize(v)
            except Exception:
                pass
        except Exception:
            pass
        v = os.environ.get(name)
        if v and str(v).strip():
            return _normalize(v)
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
    Ficheiros > ~1.4MB nao embutimos (limite pratico); usar _starter_resolved_src.
    """
    path = _starter_glb_path(filename)
    if not path.is_file():
        return None
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if len(raw) > 1_400_000:
        return None
    b64 = base64.standard_b64encode(raw).decode("ascii")
    return f"data:model/gltf-binary;base64,{b64}"


# GLB opcional em static/glb/ — só com HOLOGRAM_TEST_DISK_GLB=1 (nome: HOLOGRAM_TEST_DISK_GLB_FILE ou electric_motor_3d_model.glb).
TEST_DISK_GLB_DEFAULT = "electric_motor_3d_model.glb"


def _starter_resolved_src(filename: str) -> Optional[str]:
    """Ficheiros pequenos: data URL; grandes: URL /app/static/ (requer enableStaticServing)."""
    path = _starter_glb_path(filename)
    if not path.is_file():
        return None
    try:
        sz = path.stat().st_size
    except OSError:
        return None
    if sz <= 1_400_000:
        return _starter_pack_embedded_src(filename)
    return _starter_pack_http_url(filename)


def _resolve_opt_in_disk_test_glb() -> Optional[str]:
    """GLB em static/glb/ só com HOLOGRAM_TEST_DISK_GLB=1 (compat: HOLOGRAM_TEST_DOWNLOAD_GLB)."""
    on = _read_secret_or_env(
        "HOLOGRAM_TEST_DISK_GLB",
        "HOLOGRAM_TEST_DOWNLOAD_GLB",
        "MOTORES_HOLOGRAM_TEST_DISK_GLB",
    ).strip().lower()
    if on not in ("1", "true", "yes", "on"):
        return None
    raw = _read_secret_or_env("HOLOGRAM_TEST_DISK_GLB_FILE", "MOTORES_HOLOGRAM_TEST_DISK_GLB_FILE").strip()
    name = os.path.basename(raw) if raw else TEST_DISK_GLB_DEFAULT
    if not name.lower().endswith(".glb"):
        return None
    return _starter_resolved_src(name)


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
    return _starter_resolved_src(name)


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


def _carcaca_ficha_mecanica_motor_ui_upper(m: Dict[str, Any]) -> str:
    """
    Só ficha: carcaca (Mecanica, motor, coluna) + quadro/NEMA do JSON (sem texto OCR / bruto).
    Criterio para NEMA 56: o que o utilizador regista em Mecanica > carcaca (e similares).
    """
    parts: list[str] = [_carcaca_blob(m)]
    for d in (_mecanica_json(m), _motor_json(m)):
        for k in (
            "carcaca",
            "quadro",
            "quadro_nema",
            "nema",
            "nema_frame",
            "frame",
            "envelope",
        ):
            v = d.get(k) if isinstance(d, dict) else None
            if v is not None and str(v).strip():
                parts.append(str(v).strip())
    return " ".join(parts).upper()


def _nema_56_in_plate_string(plate_upper: str) -> bool:
    b = (plate_upper or "").strip()
    if not b:
        return False
    s = b.strip()
    if re.match(r"^56[CHJYZH]?\s*$", s) or re.match(
        r"^NEMA\W*56[CHJYZH]?\s*$", s, re.IGNORECASE
    ):
        return True
    bc = re.sub(r"[\s._\-]+", "", b)
    for suf in ("C", "H", "J", "Y"):
        t = f"56{suf}"
        if t in bc or t in b.replace(" ", ""):
            return True
    if re.search(r"NEMA\W*56(?!-)(?![0-9])\b", b) or re.search(
        r"NEMA\W*56[CHJYZH]\b", b
    ):
        return True
    if re.search(r"QUADRO\W*56[CHJYZH]?\b", b) or re.search(
        r"FRAME\W*56[CHJYZH]?\b", b
    ):
        return True
    if re.search(
        r"CARCA\W*56(?!-)(?![0-9]{2,})[CHJYZH]?(?:\b|[^0-9A-Z])", b
    ) or re.search(
        r"CARCA\W*56(?!-)(?![0-9])", b
    ):
        return True
    return False


def nema_56_somente_ficha_mecanica(m: Dict[str, Any]) -> bool:
    return _nema_56_in_plate_string(_carcaca_ficha_mecanica_motor_ui_upper(m))


def mecanica_nema56_modo_restrito() -> bool:
    return _read_secret_or_env("HOLOGRAM_CARCACA_NEMA56_STRICT", "MOTORES_HOLOGRAM_CARCACA_NEMA56_STRICT").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


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


def _is_nema_56_plate_family(m: Dict[str, Any]) -> bool:
    """
    NEMA 56, 56C, 56H, 56J, 56Y, etc. apenas a partir de **dados de ficha**
    (Mecanica > carcaca, motor, quadro…), nao a partir de OCR.
    """
    return nema_56_somente_ficha_mecanica(m)


def is_motor_nema_56_plate(m: Dict[str, Any]) -> bool:
    """True se a carcaca/quadro na ficha (Mecanica) for familia NEMA 56 — criterio de ``HOLOGRAM_GLB_NEMA56``."""
    return nema_56_somente_ficha_mecanica(m)


def _path_looks_glb(u: str) -> bool:
    base = u.strip().split("?", 1)[0].split("#", 1)[0].lower()
    return base.endswith(".glb")


def _motor_identity_blob_upper(m: Dict[str, Any]) -> str:
    """Marca, modelo e carcaça agregados (linha + JSON + UI) para heurísticas."""
    motor = _motor_json(m)
    parts = [
        _carcaca_blob(m),
        str(m.get("marca") or ""),
        str(m.get("modelo") or ""),
        str(motor.get("marca") or ""),
        str(motor.get("modelo") or ""),
        str(motor.get("carcaca") or ""),
    ]
    ui = m.get("_consulta_ui") if isinstance(m.get("_consulta_ui"), dict) else {}
    parts.extend(
        [
            str(ui.get("marca") or ""),
            str(ui.get("modelo") or ""),
            str(ui.get("carcaca") or ""),
        ]
    )
    return " ".join(parts).upper()


def _read_carcaca_glb_rule() -> str:
    """
    weg_or_nema48 (defeito): WEG, NEMA 48, ou NEMA 56 (56, 56C, 56H, 56J, 56Y…).
    weg_only | nema48_only | nema56_only | ip21_only
    nema48_or_n56 — 48 ou familia 56, sem exigir WEG.
    """
    r = _read_secret_or_env("HOLOGRAM_CARCACA_GLB_RULE", "MOTORES_HOLOGRAM_CARCACA_GLB_RULE").strip().lower()
    if r in (
        "weg_only",
        "nema48_only",
        "nema56_only",
        "weg_or_nema48",
        "ip21_only",
        "nema48_or_n56",
    ):
        return r
    return "weg_or_nema48"


def _carcaca_glb_contains_tokens() -> list[str]:
    raw = _read_secret_or_env("HOLOGRAM_CARCACA_GLB_CONTAINS", "MOTORES_HOLOGRAM_CARCACA_GLB_CONTAINS").strip()
    if not raw:
        return []
    return [t.strip().upper() for t in raw.split(",") if t.strip()]


def _blob_for_carcaca_match(m: Dict[str, Any]) -> tuple[str, str]:
    blob = _motor_identity_blob_upper(m)
    compact = re.sub(r"[\s._\-]+", "", blob)
    return blob, compact


def _token_matches_blob(tok: str, blob: str, blob_c: str) -> bool:
    t = tok.strip().upper()
    if not t:
        return False
    if t in blob:
        return True
    tc = re.sub(r"[\s._\-]+", "", t)
    return bool(tc) and tc in blob_c


def _is_ip21_carcaca(m: Dict[str, Any]) -> bool:
    blob, blob_c = _blob_for_carcaca_match(m)
    if "IP21" in blob_c or "IPW21" in blob_c:
        return True
    return bool(re.search(r"IP\s*W?\s*21\b", blob))


def motor_matches_weg_style_carcaca_for_glb(m: Dict[str, Any]) -> bool:
    """
    True → usar URL em HOLOGRAM_GLB_WEG_STYLE_HOUSING (ou alias).

    1) Se HOLOGRAM_CARCACA_GLB_CONTAINS estiver definido (ex.: IP21 ou texto da placa),
       qualquer token (separado por virgula) que apareca em marca/modelo/carcaca conta como match.
       HOLOGRAM_CARCACA_GLB_MATCH_ALL=1 exige que todos os tokens apareçam.
    2) Senao, HOLOGRAM_CARCACA_GLB_RULE: weg_or_nema48 | weg_only | nema48_only |
       nema56_only | nema48_or_n56 | ip21_only.
    """
    tokens = _carcaca_glb_contains_tokens()
    blob, blob_c = _blob_for_carcaca_match(m)
    if tokens:
        match_all = _read_secret_or_env(
            "HOLOGRAM_CARCACA_GLB_MATCH_ALL", "MOTORES_HOLOGRAM_CARCACA_GLB_MATCH_ALL"
        ).strip().lower() in ("1", "true", "yes", "on")
        checks = [_token_matches_blob(t, blob, blob_c) for t in tokens]
        if match_all:
            return all(checks)
        return any(checks)

    rule = _read_carcaca_glb_rule()
    has_weg = "WEG" in blob
    has_n48 = _is_nema_48_frame(m)
    has_n56 = _is_nema_56_plate_family(m)
    if rule == "weg_only":
        return has_weg
    if rule == "nema48_only":
        return has_n48
    if rule == "nema56_only":
        return has_n56
    if rule == "nema48_or_n56":
        return has_n48 or has_n56
    if rule == "ip21_only":
        return _is_ip21_carcaca(m)
    return has_weg or has_n48 or has_n56


def motor_has_json_hologram_glb_url(m: Dict[str, Any]) -> bool:
    """True se dados_tecnicos_json.motor tiver URL https/http a um .glb (holograma no cadastro)."""
    motor = _motor_json(m)
    for key in ("holograma_glb_url", "holograma_glb", "HologramaGlbUrl"):
        raw = motor.get(key)
        if not raw:
            continue
        u = str(raw).strip()
        if u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
            return True
    return False


def motor_has_hologram_motor_id_secret(m: Dict[str, Any]) -> bool:
    """True se houver `HOLOGRAM_GLB_MOTOR_<id>` (ou `MOTORES_`...) com URL .glb."""
    mid = _motor_id_str(m)
    if not mid:
        return False
    for name in (f"HOLOGRAM_GLB_MOTOR_{mid}", f"MOTORES_HOLOGRAM_GLB_MOTOR_{mid}"):
        u = _read_secret_or_env(name)
        if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
            return True
    return False


def consulta_lista_somente_familia_56_activa() -> bool:
    """
    Lista (consulta): nao mostrar silhueta CSS falsa; so NEMA 56 ficha, JSON, ou per-motor.
    Liga com `HOLOGRAM_CARCACA_NEMA56_STRICT` ou com `HOLOGRAM_CONSULTA_SOMENTE_56=1`.
    """
    if mecanica_nema56_modo_restrito():
        return True
    v = _read_secret_or_env(
        "HOLOGRAM_CONSULTA_SOMENTE_56",
        "MOTORES_HOLOGRAM_CONSULTA_SOMENTE_56",
        "HOLOGRAM_LISTA_SOMENTE_FAMILIA_56",
        "MOTORES_HOLOGRAM_LISTA_SOMENTE_FAMILIA_56",
    )
    return v.strip().lower() in ("1", "true", "yes", "on")


def hologram_nema56_glb_secret_configurado() -> bool:
    """True se o secret/ENV `HOLOGRAM_GLB_NEMA56` existir, for http(s) e fizer referencia a .glb."""
    u = _read_secret_or_env("HOLOGRAM_GLB_NEMA56", "MOTORES_HOLOGRAM_GLB_NEMA56")
    if not u or not u.lower().startswith(("http://", "https://")) or not _path_looks_glb(u):
        return False
    return True


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

    if mecanica_nema56_modo_restrito():
        if nema_56_somente_ficha_mecanica(m):
            u = _read_secret_or_env("HOLOGRAM_GLB_NEMA56", "MOTORES_HOLOGRAM_GLB_NEMA56")
            if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
                return u
        return None

    if nema_56_somente_ficha_mecanica(m):
        u = _read_secret_or_env("HOLOGRAM_GLB_NEMA56", "MOTORES_HOLOGRAM_GLB_NEMA56")
        if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
            return u

    if motor_matches_weg_style_carcaca_for_glb(m):
        for name in (
            "HOLOGRAM_GLB_WEG_STYLE_HOUSING",
            "HOLOGRAM_GLB_CARCACA_FRACIONARIO",
            "MOTORES_HOLOGRAM_GLB_WEG_STYLE",
        ):
            u = _read_secret_or_env(name)
            if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
                return u

    # DEFAULT (+ fallback): muitos utilizadores colocam o URL so em HOLOGRAM_GLB_WEG_STYLE_HOUSING;
    # sem match de carcaca isso nunca era lido. Incluir aqui salvo HOLOGRAM_GLB_WEG_STYLE_ONLY_MATCHED=1.
    only_matched = _read_secret_or_env(
        "HOLOGRAM_GLB_WEG_STYLE_ONLY_MATCHED", "MOTORES_HOLOGRAM_GLB_WEG_STYLE_ONLY_MATCHED"
    ).strip().lower() in ("1", "true", "yes", "on")
    default_chain = [
        "HOLOGRAM_GLB_DEFAULT",
        "MOTORES_HOLOGRAM_GLB_DEFAULT",
        "HOLOGRAM_DEFAULT_GLB",
    ]
    if not only_matched:
        default_chain.extend(
            (
                "HOLOGRAM_GLB_WEG_STYLE_HOUSING",
                "HOLOGRAM_GLB_CARCACA_FRACIONARIO",
                "MOTORES_HOLOGRAM_GLB_WEG_STYLE",
            )
        )
    for name in default_chain:
        u = _read_secret_or_env(name)
        if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
            return u

    preset_u = preset.upper().replace("-", "_")
    preset_l = preset.lower()
    for name in (f"HOLOGRAM_GLB_{preset_u}", f"HOLOGRAM_GLB_{preset_l}"):
        u = _read_secret_or_env(name)
        if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
            return u

    if _is_nema_48_frame(m):
        u = _read_secret_or_env("HOLOGRAM_GLB_NEMA48", "MOTORES_HOLOGRAM_GLB_NEMA48")
        if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
            return u

    u_disk = _resolve_opt_in_disk_test_glb()
    if u_disk:
        return u_disk

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

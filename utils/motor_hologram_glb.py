"""
URLs de modelos GLB para o holograma 3D (<model-viewer>).
NEMA 56: deteção so em **Mecanica (carcaca) e quadro/NEMA** na ficha (sem texto OCR). >
Uma so silhueta 3D para carcaças com a mesma leitura visual (p.ex. 56, 56H, L56, 56D, 56Y): GLB
`Nema56.glb` / `nema_56.glb` — nao ficheiro distinto por so codigo de letras, salvo 56C (C-face),
56J (bomba/pump) ou aletas TEFC / sem pés, etc. NEMA 48: por defeito funde com a mesma base
liso; desligar com `HOLOGRAM_48_SAME_LISO_56=0` (distingue `monofasico_48.glb` no pack). >
Prioridade: motor.holograma_glb_url no JSON > HOLOGRAM_GLB_MOTOR_<id> > NEMA mono 1 cap (PSC)
(`HOLOGRAM_GLB_NEMA_MONO_1CAP` / embed) > NEMA pequeno convencional liso
(`HOLOGRAM_GLB_NEMA_PEQUENO_CONV_LISO` / embed; senao `HOLOGRAM_GLB_NEMA56` / Nema56.glb) >
NEMA 42 (quadro na ficha) `HOLOGRAM_GLB_NEMA42` / embed `HOLOGRAM_DEFAULT_NEMA42_GLB_URL`; `HOLOGRAM_BAKED_NEMA42_GLB=0` desliga >
familia bomba close-coupled
(`pump_close_coupled`: BOMBA/MONOBLOC/PUMP, JM/JP/56J, …) `HOLOGRAM_GLB_PUMP_CLOSE_COUPLED` / embed >
familia Ex / prova de explosao com pes (`explosion_proof_footed`) `HOLOGRAM_GLB_EXPLOSION_PROOF_FOOTED` / embed >
familia IEC TEFC B3 (catalogo
IEC63, 63S/M/L, 90S/L, 100L, 112M, 132S + B3/B3T/B3D/B3L; sem B5/B14/B35) `HOLOGRAM_GLB_IEC_TEFC_B3_CATALOGO` / embed;
GLB embebido `HOLOGRAM_DEFAULT_IEC63_CATALOG_SILHUETA_GLB_URL` (= `105%20a.glb`) >
familia **IEC 132** (etiqueta IEC132 / 132S / 132M + mesmas exclusoes que TEFC B3) `HOLOGRAM_GLB_IEC132` / embed `HOLOGRAM_DEFAULT_IEC132_GLB_URL` >
familia IEC 100L (so carcaca 100L sem essa silhueta B3+TEFC) `HOLOGRAM_GLB_IEC100L` / `HOLOGRAM_DEFAULT_IEC100L_GLB_URL` >
`HOLOGRAM_CARCACA_NEMA56_STRICT=1` -> nada alem de JSON/MOTOR/NEMA56 (carcaca) + URL NEMA56 (Cloud ou embed `HOLOGRAM_DEFAULT_NEMA56_GLB_URL`), NEMA 42 (`HOLOGRAM_GLB_NEMA42` / embed), catalogo IEC/100L; nao starter, nao DEFAULT geral. Senao, fluxo completo. >
`HOLOGRAM_GLB_NEMA56` (Cloud) > fallback `HOLOGRAM_DEFAULT_NEMA56_GLB_URL` (Supabase no repo) > `NEMA_56_CARCACA_LEGENDA_COMPLETA` (56 + sufixos); `HOLOGRAM_BAKED_NEMA56_GLB=0` desliga o embed. >
GLB por tipo de carcaça (HOLOGRAM_GLB_WEG_STYLE_HOUSING + match); o mesmo URL entra na cadeia DEFAULT
se HOLOGRAM_GLB_WEG_STYLE_ONLY_MATCHED nao estiver ligado (URL global no Cloud sem regra de carcaca).
HOLOGRAM_CARCACA_GLB_CONTAINS / HOLOGRAM_CARCACA_GLB_RULE: ver motor_matches_weg_style_carcaca_for_glb. >
HOLOGRAM_GLB_DEFAULT (global Cloud; antes dos presets para nao ficar preso a GLB antigo por preset) >
env HOLOGRAM_GLB_<PRESET> > HOLOGRAM_GLB_NEMA48 (carcaca 48 sem silhueta fundida a 56) >
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

# Público (Supabase Storage): NEMA 56 se `HOLOGRAM_GLB_NEMA56` nao estiver no Cloud.
# `HOLOGRAM_BAKED_NEMA56_GLB=0` desactiva o fallback (so secrets).
HOLOGRAM_DEFAULT_NEMA56_GLB_URL = (
    "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/Nema56.glb"
)
# NEMA pequeno convencional liso com pes (48 merge + W56,56,A56,B56,D56,56H,F56H; sem 56C/56J/C-face).
# `HOLOGRAM_GLB_NEMA_PEQUENO_CONV_LISO` / embed; `HOLOGRAM_BAKED_NEMA_PEQUENO_CONV_LISO_GLB=0` desliga; senao usa `HOLOGRAM_GLB_NEMA56` / Nema56.glb.
HOLOGRAM_DEFAULT_NEMA_PEQUENO_CONVENCIONAL_LISO_GLB_URL = (
    "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/nema%202%20cap.glb"
)
# NEMA monofasico convencional PSC / 1 capacitor, pes, sem flange (W56,56,B56,D56,…); `HOLOGRAM_GLB_NEMA_MONO_1CAP` / embed;
# `HOLOGRAM_BAKED_NEMA_MONO_1CAP_GLB=0` desliga o embed.
HOLOGRAM_DEFAULT_NEMA_SINGLE_PHASE_ONE_CAP_SMALL_GLB_URL = (
    "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/1%20cap.glb"
)
# Apenas carcaça IEC 100L (dados de ficha); trocar URL: secret `HOLOGRAM_GLB_IEC100L` / `MOTORES_...`
# ou alterar a constante abaixo. `HOLOGRAM_BAKED_IEC100L_GLB=0` desactiva o embed padrão.
HOLOGRAM_DEFAULT_IEC100L_GLB_URL = (
    "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/Motor%20100l.glb"
)
# Carcaca IEC63 (etiqueta) e familia IEC TEFC B3 catalogo (63S–132S) usam o MESMO GLB Supabase `105%20a.glb`.
# URL: secret `HOLOGRAM_GLB_IEC_TEFC_B3_CATALOGO` / `MOTORES_...` ou constantes abaixo; `HOLOGRAM_BAKED_IEC_TEFC_B3_CATALOGO_GLB=0` desliga embed.
HOLOGRAM_DEFAULT_IEC63_CATALOG_SILHUETA_GLB_URL = (
    "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/105%20a.glb"
)
HOLOGRAM_DEFAULT_IEC_TEFC_B3_CATALOGO_SILHUETA_GLB_URL = HOLOGRAM_DEFAULT_IEC63_CATALOG_SILHUETA_GLB_URL
# Bomba / monobloco / close-coupled (JM, JP, 56J, …): `HOLOGRAM_GLB_PUMP_CLOSE_COUPLED` / embed; `HOLOGRAM_BAKED_PUMP_CLOSE_COUPLED_GLB=0` desliga.
HOLOGRAM_DEFAULT_PUMP_CLOSE_COUPLED_GLB_URL = (
    "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/pump.glb"
)
# Motor Ex / blindado industrial com pes (B3) + TEFC/aletas + frames medios; nao por carcaca exacta.
# URL: `HOLOGRAM_GLB_EXPLOSION_PROOF_FOOTED` / embed; substituir constante por GLB Ex dedicado se existir.
HOLOGRAM_DEFAULT_EXPLOSION_PROOF_FOOTED_GLB_URL = (
    "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/pump.glb"
)
# NEMA 42 (carcaca fechada); `HOLOGRAM_GLB_NEMA42` / `MOTORES_...`; `HOLOGRAM_BAKED_NEMA42_GLB=0` desliga o embed.
HOLOGRAM_DEFAULT_NEMA42_GLB_URL = (
    "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/nema%2042%20closed%20(1).glb"
)
# IEC 132 (carcaça dedicada); `HOLOGRAM_GLB_IEC132` / `MOTORES_...`; `HOLOGRAM_BAKED_IEC132_GLB=0` desliga o embed.
HOLOGRAM_DEFAULT_IEC132_GLB_URL = (
    "https://rpdbothdubddwltsdwlj.supabase.co/storage/v1/object/public/holograms/269c0156-2633-44cf-9d80-98c14483011c.glb"
)


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

    n48_48_block = re.search(
        r"NEMA\s*[-_]?\s*48\b", car
    ) or ("NEMA" in car and re.search(r"\b48\b", car) and not re.search(r"\b56\b", car))
    if n48_48_block and n48_aceita_mesma_silueta_motor_liso_nema_56(m):
        return "nema_56.glb"
    if n48_48_block:
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

    if preset in ("liso_56", "cface_56", "nema_footless", "nema_mono", "pump_56j"):
        if preset == "cface_56":
            return "nema_56c.glb"
        if preset == "pump_56j":
            return "bomba_jp.glb"
        if preset == "nema_footless":
            return "iec_63_b5.glb"
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
    if not motor and isinstance(data.get("Motor"), dict):
        motor = data["Motor"]
    return motor if isinstance(motor, dict) else {}


def _mecanica_json(m: Dict[str, Any]) -> Dict[str, Any]:
    data = m.get("dados_tecnicos_json") if isinstance(m.get("dados_tecnicos_json"), dict) else {}
    mec = data.get("mecanica") if isinstance(data.get("mecanica"), dict) else {}
    if not mec and isinstance(data.get("Mecanica"), dict):
        mec = data["Mecanica"]
    return mec if isinstance(mec, dict) else {}


def _motor_id_str(m: Dict[str, Any]) -> str:
    for k in ("id", "Id", "motor_id"):
        v = m.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def _carcaca_blob(m: Dict[str, Any]) -> str:
    def _car(d: Any) -> str:
        if not isinstance(d, dict):
            return ""
        return str(d.get("carcaca") or d.get("Carcaca") or "")

    parts = [
        str(m.get("carcaca") or m.get("Carcaca") or ""),
        _car(_mecanica_json(m)),
        _car(_motor_json(m)),
    ]
    ui = m.get("_consulta_ui") if isinstance(m.get("_consulta_ui"), dict) else {}
    parts.append(_car(ui))
    return " ".join(parts)


def carcaca_ficha_mecanica_motor_hologram_upper(m: Dict[str, Any]) -> str:
    return _carcaca_ficha_mecanica_motor_ui_upper(m)


def _hologram_silueta_ficha_mais_carcaca(m: Dict[str, Any]) -> str:
    """Ficha (quadro, NEMA, carcaça) + colunas extra para regras de silhueta 3D."""
    return (_carcaca_ficha_mecanica_motor_ui_upper(m) + " " + _carcaca_blob(m).upper()).strip()


def _carcaca_ficha_mecanica_motor_ui_upper(m: Dict[str, Any]) -> str:
    """
    Só ficha: carcaca (Mecanica, motor, coluna) + quadro/NEMA do JSON (sem texto OCR / bruto).
    Criterio para NEMA 56: o que o utilizador regista em Mecanica > carcaca (e similares).
    """
    parts: list[str] = [_carcaca_blob(m)]
    for d in (_mecanica_json(m), _motor_json(m)):
        for k in (
            "carcaca",
            "Carcaca",
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


# Legenda (UI) — família de quadro NEMA 56 (1–2 letras; inclui 56, 56YZ, 56C, 56H, 56J, 56J/J…).
# Deteção real: `_nema_56_in_plate_string` (regex 56 + até 2 letras, sem colar a 256/560).
NEMA_56_CARCACA_LEGENDA_COMPLETA = (
    "56, 56C, 56D, 56E, 56F, 56G, 56H, 56J, 56K, 56L, 56M, 56N, 56P, 56Q, 56R, 56S, 56T, 56U, 56V, 56W, 56X, 56Y, 56Z, 56YZ"
)

_NEMA_56_CARCACA = re.compile(
    r"""(?ix)
    (?<![0-9])        # nao 256, 1560, etc.
    56
    [A-Z]{0,2}        # 56, 56C, 56H, 56YZ, …
    (?![A-Z0-9])      # fim de token; nao 56C-200
    (?!\.[0-9])       # nao medidas tipo 56.4 mm (diametro de eixo)
    """,
    re.VERBOSE,
)


def _ficha_iec63_sem_ne_ma_explicito(plate_upper: str) -> bool:
    """Quadro IEC 63 na ficha sem mencao NEMA — nao tratar como carcaca NEMA 56."""
    u = (plate_upper or "").strip()
    if not u or re.search(r"\bNEMA\b", u, re.IGNORECASE):
        return False
    c = re.sub(r"[\s._\-/]+", "", u.upper())
    return "IEC63" in c


def _nema_56_in_plate_string(plate_upper: str) -> bool:
    b = (plate_upper or "").strip()
    if not b:
        return False
    s = b.strip()
    if re.match(
        r"^56[A-Z]{0,2}\s*$",
        s,
        re.IGNORECASE,
    ) or re.match(
        r"^NEMA\W*56[A-Z]{0,2}\s*$", s, re.IGNORECASE
    ):
        return True
    if _NEMA_56_CARCACA.search(b) is not None:
        return True
    if re.search(r"NEMA\W*56(?!-)(?![0-9])(?!\.[0-9])\b", b) or re.search(
        r"NEMA\W*56[A-Z]{1,2}\b", b, re.IGNORECASE
    ):
        return True
    if re.search(
        r"QUADRO\W*56[A-Z]{0,2}(?![A-Z0-9])(?!\.[0-9])", b, re.IGNORECASE
    ) or re.search(
        r"FRAME\W*56[A-Z]{0,2}(?![A-Z0-9])(?!\.[0-9])", b, re.IGNORECASE
    ):
        return True
    if re.search(
        r"CARCA\W*56(?!-)(?![0-9]{2,})[A-Z]{0,2}(?![A-Z0-9])(?!\.[0-9])", b, re.IGNORECASE
    ) or re.search(
        r"CARCA\W*56(?!-)(?![0-9])(?!\.[0-9])", b, re.IGNORECASE
    ):
        return True
    return False


def nema_56_somente_ficha_mecanica(m: Dict[str, Any]) -> bool:
    u = _carcaca_ficha_mecanica_motor_ui_upper(m)
    if _ficha_iec63_sem_ne_ma_explicito(u):
        return False
    return _nema_56_in_plate_string(u)


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
    s = _carcaca_ficha_mecanica_motor_ui_upper(m)
    if not s.strip():
        return False
    if re.search(r"NEMA(?:\s*[-_]?\s*)?48\b", s):
        return True
    return "NEMA" in s and "48" in s


def _texto_modelo_identificacao_para_hologram(m: Dict[str, Any]) -> str:
    """Modelo / modelo NEMA na placa — muitas fichas trazem o quadro aqui em vez de Carcaça."""
    mo = _motor_json(m)
    bits: list[str] = []
    if isinstance(mo, dict):
        for k in ("modelo", "modelo_nema", "modelo_iec", "Modelo", "ModeloNema"):
            v = mo.get(k)
            if v is not None and str(v).strip():
                bits.append(str(v).strip())
    if isinstance(m, dict):
        for k in ("modelo", "Modelo"):
            v = m.get(k)
            if v is not None and str(v).strip():
                bits.append(str(v).strip())
    return " ".join(bits).upper()


def _is_nema_42_frame(m: Dict[str, Any]) -> bool:
    """NEMA 42, NEMA-42, NEMA42 (sem espaço entre letras e número).

    Usa ficha completa (quadro/frame/nema no JSON), nao so o campo carcaca — evita falhar quando
    o quadro esta em ``mecanica.quadro`` / ``motor.quadro``. Inclui ``motor.modelo`` / ``modelo_nema``
    e JSON com ``Mecanica`` / ``Motor`` em PascalCase.
    """
    s = (_carcaca_ficha_mecanica_motor_ui_upper(m) + " " + _texto_modelo_identificacao_para_hologram(m)).strip()
    if not s:
        return False
    return bool(re.search(r"NEMA(?:\s*[-_]?\s*)?42\b", s))


def n48_mesma_silueta_que_motor_liso_56_activa() -> bool:
    """`HOLOGRAM_48_SAME_LISO_56=0` distingue `monofasico_48` no pack; vazio/1 = NEMA 48 = mesma base liso 56."""
    v = _read_secret_or_env("HOLOGRAM_48_SAME_LISO_56", "MOTORES_HOLOGRAM_48_SAME_LISO_56").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def n48_aceita_mesma_silueta_motor_liso_nema_56(m: Dict[str, Any]) -> bool:
    if not _is_nema_48_frame(m) or not n48_mesma_silueta_que_motor_liso_56_activa():
        return False
    s = _hologram_silueta_ficha_mais_carcaca(m).upper()
    c = re.sub(r"[\s._\-/]+", "", s)
    if re.search(r"\bBOMBA\b", s) or re.search(
        r"\bMONOBLOC", s
    ):
        return False
    if "48C" in c or "56C" in c or re.search(
        r"SEM\W*P(E|Ê)S", s
    ) or re.search(
        r"FOOTLESS|NO\W*FOOT", s
    ):
        return False
    if re.search(
        r"C-?\s*FACE", s, re.IGNORECASE
    ) and re.search(
        r"\b48\b", s
    ):
        return False
    if re.search(
        r"(?<![0-9A-Z])56J(?![0-9A-Z])", s
    ) or re.search(
        r"JET\W*PUMP|PUMP\W*MOT", s, re.IGNORECASE
    ):
        return False
    if re.search(
        r"\bW22\b|\bW21\b", s
    ) or re.search(
        r"\bWEG\b", s
    ) or re.search(
        r"\bTEFC\b", s, re.IGNORECASE
    ) and re.search(
        r"ALET|ALETAS|FIN\W*ROST", s, re.IGNORECASE
    ):
        return False
    return True


def infer_hologram_preset_familia_nema_silueta(
    m: Dict[str, Any]
) -> Optional[str]:
    """
    Preset por aparência (56C, 56J, TEFC/aletas, sem pés, 48, liso 56-48-56H-D…).
    """
    if motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha(m):
        return None
    if iec63_etiqueta_na_carcaca_sem_ne_ma(m) and not nema_56_somente_ficha_mecanica(m):
        return None
    s = _hologram_silueta_ficha_mais_carcaca(m)
    fup = s.upper()
    c = re.sub(r"[\s._\-/]+", "", fup)
    ficha_u = _carcaca_ficha_mecanica_motor_ui_upper(m)
    nema_56_plate = nema_56_somente_ficha_mecanica(m)
    n48 = _is_nema_48_frame(m)
    n42 = _is_nema_42_frame(m)
    if not fup.strip() or not (
        re.search(r"\bNEMA\b", fup) or nema_56_plate or n48 or n42 or re.search(
            r"\bD56\b|L56\b|56D\b|56H\b|56L\b|56Y\b|56Z\b", fup, re.IGNORECASE
        )
    ):
        return None
    if re.search(
        r"SEM\W*P(E|Ê)S", fup
    ) or re.search(
        r"\bFOOTLESS\b", fup
    ) or re.search(
        r"NO\W*FOOT", fup
    ):
        return "nema_footless"
    is_cface = bool(
        re.search(
            r"(?<![0-9])56C(?!-?[0-9A-Z/]{2,})", c, re.IGNORECASE
        )
        or re.search(
            r"(?<![0-9])48C(?!-?[0-9A-Z/]{2,})", c, re.IGNORECASE
        )
    )
    if is_cface:
        return "cface_56"
    if re.search(
        r"(?<![0-9A-Z])56J(?![0-9A-Z])", fup
    ) or re.search(
        r"JET\W*PUMP|56J\b|PUMP\W*MOT", fup, re.IGNORECASE
    ):
        return "pump_56j"
    if re.search(
        r"\bBOMBA\b", fup
    ) and re.search(
        r"\b56J\b|JP\W*56|56\W*J", fup, re.IGNORECASE
    ):
        return "pump_56j"
    if re.search(
        r"\bW22\b|\bW21\b", fup
    ) or re.search(
        r"\bWEG\b", fup
    ) or (
        re.search(
        r"\bTEFC\b", fup, re.IGNORECASE
    ) and re.search(
        r"ALET|ALETAS|DENS\w*\s*FIN", fup, re.IGNORECASE
    )):
        return "iec_w22"
    if n48:
        if n48_aceita_mesma_silueta_motor_liso_nema_56(m):
            return "liso_56"
        return "nema_mono"
    if n42:
        return "liso_56"
    if nema_56_plate and "56C" not in c and "48C" not in c and "56J" not in c and not re.search(
        r"(?<![0-9A-Z])56J", fup
    ):
        return "liso_56"
    if re.search(
        r"\bNEMA\b", fup
    ) and re.search(
        r"56(?!-)(?![0-9]{2})[A-Z0-9]{0,2}", c, re.IGNORECASE
    ) and "56C" not in c and "48C" not in c and "56J" not in c and not re.search(
        r"(?<![0-9A-Z])56J", fup
    ):
        return "liso_56"
    return None


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
        str(motor.get("carcaca") or motor.get("Carcaca") or ""),
    ]
    ui = m.get("_consulta_ui") if isinstance(m.get("_consulta_ui"), dict) else {}
    parts.extend(
        [
            str(ui.get("marca") or ""),
            str(ui.get("modelo") or ""),
            str(ui.get("carcaca") or ui.get("Carcaca") or ""),
        ]
    )
    return " ".join(parts).upper()


def _read_carcaca_glb_rule() -> str:
    """
    weg_or_nema48 (defeito): WEG, NEMA 48, NEMA 42, ou NEMA 56 (56, 56C, 56H, 56J, 56Y…).
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
       nema56_only | nema48_or_n56 | ip21_only. No defeito weg_or_nema48 conta tambem NEMA 42 na ficha.
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
    has_n42 = _is_nema_42_frame(m)
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
    return has_weg or has_n48 or has_n56 or has_n42


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
    Lista (consulta): por defeito nao mostra silhueta CSS falsa; so familia com GLB dedicado na ficha
    (NEMA 56, IEC TEFC B3 / IEC63, IEC 100L, bomba close-coupled, Ex com pes — ver
    `consulta_lista_motor_tem_familia_glb_dedicada_na_ficha`), `holograma_glb_url` no JSON,
    ou `HOLOGRAM_GLB_MOTOR_<id>`.
    - `HOLOGRAM_LISTA_SILHUETA_TODOS=1`: reactiva silhueta generica em todos (comportamento antigo).
    - `HOLOGRAM_CONSULTA_SOMENTE_56=0` (explicito): desactiva o filtro da lista.
    - `HOLOGRAM_CARCACA_NEMA56_STRICT=1`: inclui a logica de resolucao GLB; o filtro da lista vem
      desta funcao, nao so do STRICT.
    """
    if _read_secret_or_env("HOLOGRAM_LISTA_SILHUETA_TODOS", "MOTORES_HOLOGRAM_LISTA_SILHUETA_TODOS").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return False
    if mecanica_nema56_modo_restrito():
        return True
    v = _read_secret_or_env(
        "HOLOGRAM_CONSULTA_SOMENTE_56",
        "MOTORES_HOLOGRAM_CONSULTA_SOMENTE_56",
        "HOLOGRAM_LISTA_SOMENTE_FAMILIA_56",
        "MOTORES_HOLOGRAM_LISTA_SOMENTE_FAMILIA_56",
    ).strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    if v in ("1", "true", "yes", "on"):
        return True
    return True


def _baked_nema56_glb_activo() -> bool:
    v = _read_secret_or_env("HOLOGRAM_BAKED_NEMA56_GLB", "MOTORES_HOLOGRAM_BAKED_NEMA56_GLB").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def nema56_glb_url_efectiva() -> str:
    """Secret/ENV `HOLOGRAM_GLB_NEMA56` se definido, senao `HOLOGRAM_DEFAULT_NEMA56_GLB_URL` (Supabase) se activo."""
    u = _read_secret_or_env("HOLOGRAM_GLB_NEMA56", "MOTORES_HOLOGRAM_GLB_NEMA56")
    if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
        return u.strip()
    if _baked_nema56_glb_activo() and HOLOGRAM_DEFAULT_NEMA56_GLB_URL:
        s = str(HOLOGRAM_DEFAULT_NEMA56_GLB_URL).strip()
        if s.lower().startswith(("http://", "https://")) and _path_looks_glb(s):
            return s
    return ""


def _baked_iec100l_glb_activo() -> bool:
    v = _read_secret_or_env("HOLOGRAM_BAKED_IEC100L_GLB", "MOTORES_HOLOGRAM_BAKED_IEC100L_GLB").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def _baked_iec_tefc_b3_catalogo_glb_activo() -> bool:
    v = _read_secret_or_env(
        "HOLOGRAM_BAKED_IEC_TEFC_B3_CATALOGO_GLB",
        "MOTORES_HOLOGRAM_BAKED_IEC_TEFC_B3_CATALOGO_GLB",
    ).strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def _carcaca_somente_compact_upper(m: Dict[str, Any]) -> str:
    """Apenas campos de carcaca (Mecanica, motor, coluna consulta) — para B5/B14/B35 sem falsos de quadro/frame."""
    parts = [
        str(m.get("carcaca") or ""),
        str(_mecanica_json(m).get("carcaca") or ""),
        str(_motor_json(m).get("carcaca") or ""),
    ]
    ui = m.get("_consulta_ui") if isinstance(m.get("_consulta_ui"), dict) else {}
    parts.append(str(ui.get("carcaca") or ""))
    return re.sub(r"[\s._\-/]+", "", " ".join(parts).upper())


def iec63_etiqueta_na_carcaca_sem_ne_ma(m: Dict[str, Any]) -> bool:
    """Carcaca IEC63 sem NEMA na ficha — nao aplicar presets/heuristicas da familia NEMA 56."""
    if "IEC63" not in _carcaca_somente_compact_upper(m):
        return False
    return re.search(r"\bNEMA\b", _carcaca_ficha_mecanica_motor_ui_upper(m), re.IGNORECASE) is None


def motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha(m: Dict[str, Any]) -> bool:
    """
    Familia visual unica: IEC TEFC, montagem B3 (B3/B3T/B3D/B3L), pes, corpo aletado, sem flange B5/B14/B35.
    Quadros: IEC63 (etiqueta compacta), 63S, 63M, 63L, 90S, 90L, 100L, 112M, 132S (dados de ficha).
    Para IEC63 sem texto B3/TEFC na ficha, assume-se mesma silhueta de catalogo (GLB 105 a.glb).
    Nao aplica com ambiguidade (bomba/J, NEMA, sem pes).
    B5/B14/B35: so na string de carcaca (evita rejeitar IEC63 quando `frame`/`quadro` trazem letras B5 noutro contexto).
    """
    raw_u = f"{_carcaca_ficha_mecanica_motor_ui_upper(m)} {_carcaca_blob(m).upper()}"
    if not raw_u.strip():
        return False
    c = re.sub(r"[\s._\-/]+", "", raw_u)
    c_carc = _carcaca_somente_compact_upper(m)
    if nema_56_somente_ficha_mecanica(m) or _is_nema_48_frame(m) or _is_nema_42_frame(m):
        return False
    if "B35" in c_carc or "B14" in c_carc or "B5" in c_carc:
        return False
    if re.search(r"SEM\W*P(E|Ê)S|FOOTLESS|NO\W*FOOT", raw_u):
        return False
    if re.search(
        r"(?<![0-9A-Z])56J(?![0-9A-Z])|JET\W*PUMP|PUMP\W*MOT|MONOBLOC|\bBOMBA\b",
        raw_u,
        re.IGNORECASE,
    ):
        return False
    if "IEC63" in c.upper():
        return True
    b3_ok = (
        "B3T" in c
        or "B3D" in c
        or "B3L" in c
        or re.search(r"(?<=[0-9LMSm])B3(?![0-9])", c, re.IGNORECASE) is not None
    )
    if not b3_ok:
        return False
    if "TEFC" not in c and re.search(r"ALET|ALETADO|ALETAS", raw_u, re.IGNORECASE) is None:
        return False
    for fr in ("63S", "63M", "63L", "90S", "90L", "100L", "112M", "132S", "132M"):
        if re.search(rf"(?<![0-9.]){re.escape(fr)}(?![0-9])", c, re.IGNORECASE):
            return True
    return False


def _baked_iec132_glb_activo() -> bool:
    v = _read_secret_or_env("HOLOGRAM_BAKED_IEC132_GLB", "MOTORES_HOLOGRAM_BAKED_IEC132_GLB").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def motor_familia_iec132_silhueta_somente_ficha(m: Dict[str, Any]) -> bool:
    """
    Carcaça IEC 132 (etiqueta ``IEC 132`` / ``IEC132`` ou quadro ``132S`` / ``132M`` com B3+TEFC/aletas).
    Prioridade em ``resolve_model_glb_url`` acima do catálogo genérico ``105 a.glb``.
    """
    raw_u = f"{_carcaca_ficha_mecanica_motor_ui_upper(m)} {_carcaca_blob(m).upper()}"
    if not raw_u.strip():
        return False
    c = re.sub(r"[\s._\-/]+", "", raw_u)
    c_carc = _carcaca_somente_compact_upper(m)
    if nema_56_somente_ficha_mecanica(m) or _is_nema_48_frame(m) or _is_nema_42_frame(m):
        return False
    if "B35" in c_carc or "B14" in c_carc or "B5" in c_carc:
        return False
    if re.search(r"SEM\W*P(E|Ê)S|FOOTLESS|NO\W*FOOT", raw_u):
        return False
    if re.search(
        r"(?<![0-9A-Z])56J(?![0-9A-Z])|JET\W*PUMP|PUMP\W*MOT|MONOBLOC|\bBOMBA\b",
        raw_u,
        re.IGNORECASE,
    ):
        return False
    if re.search(r"\bIEC\W*132\b", raw_u, re.IGNORECASE) or "IEC132" in c:
        return True
    b3_ok = (
        "B3T" in c
        or "B3D" in c
        or "B3L" in c
        or re.search(r"(?<=[0-9LMSm])B3(?![0-9])", c, re.IGNORECASE) is not None
    )
    if not b3_ok:
        return False
    if "TEFC" not in c and re.search(r"ALET|ALETADO|ALETAS", raw_u, re.IGNORECASE) is None:
        return False
    for fr in ("132S", "132M"):
        if re.search(rf"(?<![0-9.]){re.escape(fr)}(?![0-9])", c, re.IGNORECASE):
            return True
    return False


def iec132_glb_url_efectiva() -> str:
    """Secret ``HOLOGRAM_GLB_IEC132`` / ``MOTORES_`` ou embed ``HOLOGRAM_DEFAULT_IEC132_GLB_URL``."""
    u = _read_secret_or_env("HOLOGRAM_GLB_IEC132", "MOTORES_HOLOGRAM_GLB_IEC132")
    if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
        return u.strip()
    if _baked_iec132_glb_activo() and HOLOGRAM_DEFAULT_IEC132_GLB_URL:
        s = str(HOLOGRAM_DEFAULT_IEC132_GLB_URL).strip()
        if s.lower().startswith(("http://", "https://")) and _path_looks_glb(s):
            return s
    return ""


def iec_tefc_b3_catalogo_silhueta_glb_url_efectiva() -> str:
    """Secret `HOLOGRAM_GLB_IEC_TEFC_B3_CATALOGO` ou embed `HOLOGRAM_DEFAULT_IEC63_CATALOG_SILHUETA_GLB_URL` (= 105 a.glb, alias TEFC B3)."""
    u = _read_secret_or_env(
        "HOLOGRAM_GLB_IEC_TEFC_B3_CATALOGO",
        "MOTORES_HOLOGRAM_GLB_IEC_TEFC_B3_CATALOGO",
    )
    if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
        return u.strip()
    if _baked_iec_tefc_b3_catalogo_glb_activo() and HOLOGRAM_DEFAULT_IEC_TEFC_B3_CATALOGO_SILHUETA_GLB_URL:
        s = str(HOLOGRAM_DEFAULT_IEC_TEFC_B3_CATALOGO_SILHUETA_GLB_URL).strip()
        if s.lower().startswith(("http://", "https://")) and _path_looks_glb(s):
            return s
    return ""


def motor_familia_iec_100l_somente_ficha(m: Dict[str, Any]) -> bool:
    """
    True se a ficha (Mecânica / carcaça, quadro, frame, colunas) indicar a família IEC 100L.
    Conservador: nao aplica com ambiguidade (p.ex. 100L e 90L/112L na mesma string de carcaça).
    """
    raw = f"{_carcaca_ficha_mecanica_motor_ui_upper(m)} {_carcaca_blob(m).upper()}"
    c = re.sub(r"[\s._\-/]+", "", raw)
    if not c:
        return False
    if re.search(r"(?<![0-9.])100L", c) is None:
        return False
    for t in ("63S", "63M", "63L", "90L", "90S", "112M", "112L", "100M", "100S"):
        if t in c:
            return False
    if motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha(m):
        return False
    return True


def iec_100l_glb_url_efectiva() -> str:
    """`HOLOGRAM_GLB_IEC100L` / `MOTORES_` ou `HOLOGRAM_DEFAULT_IEC100L_GLB_URL` (Supabase) se `HOLOGRAM_BAKED_IEC100L_GLB` activo."""
    u = _read_secret_or_env("HOLOGRAM_GLB_IEC100L", "MOTORES_HOLOGRAM_GLB_IEC100L")
    if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
        return u.strip()
    if _baked_iec100l_glb_activo() and HOLOGRAM_DEFAULT_IEC100L_GLB_URL:
        s = str(HOLOGRAM_DEFAULT_IEC100L_GLB_URL).strip()
        if s.lower().startswith(("http://", "https://")) and _path_looks_glb(s):
            return s
    return ""


def _pump_close_coupled_identity_blob_upper(m: Dict[str, Any]) -> str:
    """Ficha carcaça/quadro + motor/mecânica (tipo, linha, aplicação) para sinais de bomba."""
    motor = _motor_json(m)
    mec = _mecanica_json(m)
    parts: list[str] = [
        _carcaca_ficha_mecanica_motor_ui_upper(m),
        _carcaca_blob(m).upper(),
    ]
    for d in (motor, mec):
        if not isinstance(d, dict):
            continue
        for k in (
            "tipo_motor",
            "tipo",
            "linha",
            "aplicacao",
            "aplicação",
            "construcao",
            "forma",
            "categoria",
            "posicao_montagem",
        ):
            v = d.get(k)
            if v is not None and str(v).strip():
                parts.append(str(v).strip())
    return " ".join(parts).upper()


def motor_familia_pump_close_coupled_somente_ficha(m: Dict[str, Any]) -> bool:
    """
    Familia visual bomba / monobloco / close-coupled (JM, JP, NEMA 56J, …).
    Exige pelo menos um sinal forte; evita `JP` isolado sem contexto de motor.
    """
    raw_u = _pump_close_coupled_identity_blob_upper(m)
    if not raw_u.strip():
        return False
    c = re.sub(r"[\s._\-/]+", "", raw_u)
    strong = bool(
        re.search(r"\bBOMBA\b", raw_u)
        or "MONOBLOC" in c
        or re.search(r"\bPUMP\b", raw_u)
        or ("CLOSE" in raw_u and re.search(r"COUPL|COUPLED", raw_u) is not None)
        or re.search(r"\bJET\s*PUMP\b", raw_u, re.IGNORECASE)
        or re.search(r"JP\s*[-_]?\s*56|56\s*[-_]?\s*JP", raw_u, re.IGNORECASE)
    )
    if strong:
        return True
    if re.search(r"(?<![0-9A-Z])56J(?![0-9A-Z])", raw_u):
        return True
    if re.search(r"(?<=[0-9LSM])JM(?![0-9A-Z])", c, re.IGNORECASE):
        return True
    if "JP" in c and re.search(r"56|NEMA|IEC", raw_u, re.IGNORECASE):
        return True
    return False


def _baked_pump_close_coupled_glb_activo() -> bool:
    v = _read_secret_or_env(
        "HOLOGRAM_BAKED_PUMP_CLOSE_COUPLED_GLB",
        "MOTORES_HOLOGRAM_BAKED_PUMP_CLOSE_COUPLED_GLB",
    ).strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def pump_close_coupled_glb_url_efectiva() -> str:
    """Secret `HOLOGRAM_GLB_PUMP_CLOSE_COUPLED` / `MOTORES_` ou `HOLOGRAM_DEFAULT_PUMP_CLOSE_COUPLED_GLB_URL`."""
    u = _read_secret_or_env(
        "HOLOGRAM_GLB_PUMP_CLOSE_COUPLED",
        "MOTORES_HOLOGRAM_GLB_PUMP_CLOSE_COUPLED",
    )
    if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
        return u.strip()
    if _baked_pump_close_coupled_glb_activo() and HOLOGRAM_DEFAULT_PUMP_CLOSE_COUPLED_GLB_URL:
        s = str(HOLOGRAM_DEFAULT_PUMP_CLOSE_COUPLED_GLB_URL).strip()
        if s.lower().startswith(("http://", "https://")) and _path_looks_glb(s):
            return s
    return ""


def _explosion_proof_footed_identity_blob_upper(m: Dict[str, Any]) -> str:
    """Ficha + descricao/observacoes para Ex / prova de explosao / ATEX."""
    motor = _motor_json(m)
    mec = _mecanica_json(m)
    parts: list[str] = [
        _carcaca_ficha_mecanica_motor_ui_upper(m),
        _carcaca_blob(m).upper(),
    ]
    for d in (motor, mec):
        if not isinstance(d, dict):
            continue
        for k in (
            "tipo_motor",
            "tipo",
            "linha",
            "categoria",
            "construcao",
            "forma",
            "aplicacao",
            "aplicação",
            "descricao",
            "descricao_longa",
            "observacoes",
            "notas",
            "nome_comercial",
        ):
            v = d.get(k)
            if v is not None and str(v).strip():
                parts.append(str(v).strip())
    ui = m.get("_consulta_ui") if isinstance(m.get("_consulta_ui"), dict) else {}
    for k in ("carcaca", "descricao", "tipo_motor"):
        v = ui.get(k)
        if v is not None and str(v).strip():
            parts.append(str(v).strip())
    return " ".join(parts).upper()


def motor_familia_explosion_proof_footed_somente_ficha(m: Dict[str, Any]) -> bool:
    """
    Familia visual `explosion_proof_footed`: Ex / prova de explosao / ATEX + pes (B3) + TEFC ou aletas
    + frame medio (90S–180M). Nao liga a carcaca exacta; exclui bomba, freio, B5/B14/B35, NEMA liso sem Ex.
    """
    if motor_familia_pump_close_coupled_somente_ficha(m):
        return False
    raw_u = _explosion_proof_footed_identity_blob_upper(m)
    if not raw_u.strip():
        return False
    c = re.sub(r"[\s._\-/]+", "", raw_u)
    if nema_56_somente_ficha_mecanica(m) and not re.search(
        r"\bEX\b|EXD|EXDB|EXE|EXPLOSION|PROVA\s+D|ATEX|ANTIDEFLAGR", raw_u, re.IGNORECASE
    ):
        return False
    ex_signal = bool(
        re.search(r"\bEX\s*-?\s*(D|DB|E)\b", raw_u, re.IGNORECASE)
        or re.search(r"\bEXD\b|\bEXDB\b|\bEXE\b", c, re.IGNORECASE)
        or re.search(r"EXPLOSION\s*PROOF|EXPLOSION-?\s*PROOF", raw_u, re.IGNORECASE)
        or re.search(r"PROVA\s+D[EUÊO]?\s*EXPLOS", raw_u, re.IGNORECASE)
        or re.search(r"[ÀA]\s*PROVA\s+D[EUÊO]?\s*EXPLOS", raw_u, re.IGNORECASE)
        or "ANTIDEFLAGR" in c
        or (
            re.search(r"\bATEX\b", raw_u, re.IGNORECASE)
            and re.search(r"\b(EX|II\s*2G|ZONE)", raw_u, re.IGNORECASE)
        )
    )
    if not ex_signal:
        return False
    if "B35" in c or "B14" in c or "B5" in c:
        return False
    if re.search(r"SEM\W*P(E|Ê)S|FOOTLESS|NO\W*FOOT", raw_u):
        return False
    if "FREIO" in c or "BRAKE" in c or "MOTOFREIO" in c:
        return False
    b3_ok = (
        "B3T" in c
        or "B3D" in c
        or "B3L" in c
        or re.search(r"(?<=[0-9LMSm])B3(?![0-9])", c, re.IGNORECASE) is not None
    )
    if not b3_ok:
        return False
    if "TEFC" not in c and re.search(r"ALET|ALETADO|ALETAS", raw_u, re.IGNORECASE) is None:
        return False
    for fr in (
        "90S",
        "90L",
        "100L",
        "112M",
        "132S",
        "132M",
        "160M",
        "160L",
        "180M",
        "180L",
    ):
        if re.search(rf"(?<![0-9.]){re.escape(fr)}(?![0-9])", c, re.IGNORECASE):
            return True
    return False


def _baked_explosion_proof_footed_glb_activo() -> bool:
    v = _read_secret_or_env(
        "HOLOGRAM_BAKED_EXPLOSION_PROOF_FOOTED_GLB",
        "MOTORES_HOLOGRAM_BAKED_EXPLOSION_PROOF_FOOTED_GLB",
    ).strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def explosion_proof_footed_glb_url_efectiva() -> str:
    """Secret `HOLOGRAM_GLB_EXPLOSION_PROOF_FOOTED` / `MOTORES_` ou `HOLOGRAM_DEFAULT_EXPLOSION_PROOF_FOOTED_GLB_URL`."""
    u = _read_secret_or_env(
        "HOLOGRAM_GLB_EXPLOSION_PROOF_FOOTED",
        "MOTORES_HOLOGRAM_GLB_EXPLOSION_PROOF_FOOTED",
    )
    if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
        return u.strip()
    if _baked_explosion_proof_footed_glb_activo() and HOLOGRAM_DEFAULT_EXPLOSION_PROOF_FOOTED_GLB_URL:
        s = str(HOLOGRAM_DEFAULT_EXPLOSION_PROOF_FOOTED_GLB_URL).strip()
        if s.lower().startswith(("http://", "https://")) and _path_looks_glb(s):
            return s
    return ""


def _baked_nema_pequeno_conv_liso_glb_activo() -> bool:
    v = _read_secret_or_env(
        "HOLOGRAM_BAKED_NEMA_PEQUENO_CONV_LISO_GLB",
        "MOTORES_HOLOGRAM_BAKED_NEMA_PEQUENO_CONV_LISO_GLB",
    ).strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def nema_pequeno_convencional_liso_glb_url_efectiva() -> str:
    """URL da silhueta NEMA pequeno convencional (liso, pes); secret `HOLOGRAM_GLB_NEMA_PEQUENO_CONV_LISO` / `MOTORES_`."""
    u = _read_secret_or_env(
        "HOLOGRAM_GLB_NEMA_PEQUENO_CONV_LISO",
        "MOTORES_HOLOGRAM_GLB_NEMA_PEQUENO_CONV_LISO",
    )
    if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
        return u.strip()
    if _baked_nema_pequeno_conv_liso_glb_activo() and HOLOGRAM_DEFAULT_NEMA_PEQUENO_CONVENCIONAL_LISO_GLB_URL:
        s = str(HOLOGRAM_DEFAULT_NEMA_PEQUENO_CONVENCIONAL_LISO_GLB_URL).strip()
        if s.lower().startswith(("http://", "https://")) and _path_looks_glb(s):
            return s
    return ""


def _dados_tecnicos_root(m: Dict[str, Any]) -> Dict[str, Any]:
    d = m.get("dados_tecnicos_json")
    return d if isinstance(d, dict) else {}


def _bobinagem_auxiliar_json(m: Dict[str, Any]) -> Dict[str, Any]:
    b = _dados_tecnicos_root(m).get("bobinagem_auxiliar")
    return b if isinstance(b, dict) else {}


def _motor_eletrico_ficha_upper(m: Dict[str, Any]) -> str:
    """Fases, tipo, capacitor auxiliar e notas (sem OCR bruto) para regras mono / PSC."""
    parts: list[str] = []
    mj = _motor_json(m)
    for k in ("fases", "tipo_motor", "observacoes"):
        v = mj.get(k)
        if v is not None and str(v).strip():
            parts.append(str(v).strip())
    root = _dados_tecnicos_root(m)
    v = root.get("observacoes_gerais")
    if v is not None and str(v).strip():
        parts.append(str(v).strip())
    ba = _bobinagem_auxiliar_json(m)
    for k in ("capacitor", "ligacao", "observacoes"):
        v = ba.get(k)
        if v is not None and str(v).strip():
            parts.append(str(v).strip())
    for k in ("fases", "tipo_motor"):
        v = m.get(k)
        if v is not None and str(v).strip():
            parts.append(str(v).strip())
    return " ".join(parts).upper()


def _nema_pequeno_convencional_liso_mecanica_somente_ficha(m: Dict[str, Any]) -> bool:
    """
    Silhueta mecanica NEMA pequeno liso com pes (48 merge + W56…56 nu), sem bomba/Ex/IEC/56C/56J/C-face/TEFC aletado.
    Parte comum entre familia `nema_pequeno_conv_liso` e mono PSC 1 cap.
    """
    raw_u = _hologram_silueta_ficha_mais_carcaca(m).upper()
    c = re.sub(r"[\s._\-/]+", "", raw_u)
    if not c.strip():
        return False
    if motor_familia_pump_close_coupled_somente_ficha(m):
        return False
    if motor_familia_explosion_proof_footed_somente_ficha(m):
        return False
    if motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha(m):
        return False
    if re.search(r"SEM\W*P(E|Ê)S|FOOTLESS|NO\W*FOOT", raw_u):
        return False
    if "TEFC" in c and re.search(r"ALET|ALETAS", raw_u, re.IGNORECASE):
        return False
    if "56HC" in c or "56C" in c or "48C" in c:
        return False
    if re.search(r"(?<![0-9A-Z])56J(?![0-9A-Z])", raw_u):
        return False
    if re.search(r"C-?\s*FACE", raw_u, re.IGNORECASE) and ("56C" in c or "48C" in c):
        return False
    if _is_nema_48_frame(m) and n48_aceita_mesma_silueta_motor_liso_nema_56(m):
        return True
    if not nema_56_somente_ficha_mecanica(m):
        return False
    if re.search(r"(?<![0-9A-Z])W56(?![0-9A-Z])", c, re.IGNORECASE):
        return True
    if re.search(r"(?<![0-9A-Z])A56(?![0-9A-Z])", c, re.IGNORECASE):
        return True
    if re.search(r"(?<![0-9A-Z])B56(?![0-9A-Z])", c, re.IGNORECASE):
        return True
    if re.search(r"(?<![0-9A-Z])D56(?![0-9A-Z])", c, re.IGNORECASE):
        return True
    if re.search(r"(?<![0-9.])56D(?![0-9A-Z])", c, re.IGNORECASE):
        return True
    if "F56H" in c:
        return True
    if re.search(r"(?<![0-9.])56H(?![A-Z])", c, re.IGNORECASE):
        return True
    if re.search(r"NEMA\W*56(?![A-Z])", raw_u, re.IGNORECASE):
        return True
    if re.search(r"(?<![0-9.])56(?![A-Z0-9])", c):
        return True
    return False


def motor_familia_nema_single_phase_one_capacitor_small_somente_ficha(m: Dict[str, Any]) -> bool:
    """
    NEMA monofasico convencional PSC / um capacitor permanente, pes, sem flange (56 nu, W56, B56, D56, …).
    Exclui CS-CR, 2 caps, split-phase sem PSC, trifasico declarado.
    """
    if not _nema_pequeno_convencional_liso_mecanica_somente_ficha(m):
        return False
    ele = _motor_eletrico_ficha_upper(m)
    raw_u = f"{_hologram_silueta_ficha_mais_carcaca(m).upper()} {ele}"
    if re.search(r"TRIF[AÁ]S|TRIFASIC|\b3\W*FASES\b|\b3\W*PH\b", ele):
        return False
    if re.search(
        r"2\s*CAP|DOIS\s*CAP|DUAL\s*CAP|CS\s*[-]?\s*CR|CSCR|CAP\s*START|START\s*CAP|"
        r"CAPACITOR\s*DE\s*PARTIDA|PARTIDA\s*E\s*ARRANQUE|ARRANQUE.*RUN",
        raw_u,
        re.IGNORECASE,
    ):
        return False
    if re.search(r"SPLIT\s*[- ]?PHASE", raw_u, re.IGNORECASE) and not re.search(r"\bPSC\b", raw_u):
        return False
    if re.search(r"\d+\s*/\s*\d+\s*[µU\u00B5]?\s*F\b", raw_u, re.IGNORECASE):
        return False
    mono = bool(
        re.search(
            r"MONOF[AÁ]S|MONO\W*FASE|SINGLE\W*PHASE|\b1\W*PH\b|\b1-[\s]?PH\b|\b1F\b",
            ele,
            re.IGNORECASE,
        )
    )
    psc = bool(
        re.search(
            r"\bPSC\b|PERMANENT\s*CAP|CAPACITOR\s*PERM|CAP\s*RUN\b|CAP\s*FIXO|"
            r"PERM\.?\s*CAP|CAP\s*PERMAN",
            raw_u,
            re.IGNORECASE,
        )
    )
    um_cap_txt = bool(re.search(r"\b1\s*CAP|UM\s*CAP|ÚNICO\s*CAP|UNICO\s*CAP", raw_u, re.IGNORECASE))
    cap_campo = str(_bobinagem_auxiliar_json(m).get("capacitor") or "").strip()
    cap_campo_ok = bool(cap_campo) and not re.search(r"\d+\s*/\s*\d+", cap_campo)
    cap_evidence = psc or um_cap_txt or cap_campo_ok
    if not cap_evidence:
        return False
    if not mono:
        if not (psc and cap_campo_ok):
            return False
    return True


def motor_familia_nema_pequeno_convencional_liso_somente_ficha(m: Dict[str, Any]) -> bool:
    """
    Familia visual unica: NEMA pequeno convencional com pes, corpo liso (rolled steel), sem 56C/56HC/56J/C-face.
    Inclui NEMA 48 quando `n48_aceita_mesma_silueta_motor_liso_nema_56`; quadros W56, A56, B56, D56, 56H, F56H, 56 nu.
    Exclui monofasico PSC 1 cap (`motor_familia_nema_single_phase_one_capacitor_small_somente_ficha`).
    """
    if not _nema_pequeno_convencional_liso_mecanica_somente_ficha(m):
        return False
    if motor_familia_nema_single_phase_one_capacitor_small_somente_ficha(m):
        return False
    return True


def _baked_nema_mono_um_cap_small_glb_activo() -> bool:
    v = _read_secret_or_env(
        "HOLOGRAM_BAKED_NEMA_MONO_1CAP_GLB",
        "MOTORES_HOLOGRAM_BAKED_NEMA_MONO_1CAP_GLB",
    ).strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def nema_single_phase_one_cap_small_glb_url_efectiva() -> str:
    """Secret `HOLOGRAM_GLB_NEMA_MONO_1CAP` / `MOTORES_` ou URL embebida `HOLOGRAM_DEFAULT_NEMA_SINGLE_PHASE_ONE_CAP_SMALL_GLB_URL`."""
    u = _read_secret_or_env("HOLOGRAM_GLB_NEMA_MONO_1CAP", "MOTORES_HOLOGRAM_GLB_NEMA_MONO_1CAP")
    if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
        return u.strip()
    if _baked_nema_mono_um_cap_small_glb_activo() and HOLOGRAM_DEFAULT_NEMA_SINGLE_PHASE_ONE_CAP_SMALL_GLB_URL:
        s = str(HOLOGRAM_DEFAULT_NEMA_SINGLE_PHASE_ONE_CAP_SMALL_GLB_URL).strip()
        if s.lower().startswith(("http://", "https://")) and _path_looks_glb(s):
            return s
    return ""


def nema56_glb_url_efectiva_para_motor(m: Dict[str, Any]) -> str:
    """NEMA mono 1 cap > pequeno convencional liso (mesma silhueta) > URL NEMA 56 classica (`nema56_glb_url_efectiva`)."""
    if motor_familia_nema_single_phase_one_capacitor_small_somente_ficha(m):
        u = nema_single_phase_one_cap_small_glb_url_efectiva()
        if u:
            return u
    if motor_familia_nema_pequeno_convencional_liso_somente_ficha(m):
        u = nema_pequeno_convencional_liso_glb_url_efectiva()
        if u:
            return u
    return nema56_glb_url_efectiva()


def hologram_nema56_glb_secret_configurado() -> bool:
    """True se houver URL NEMA 56, pequeno liso, mono 1 cap, NEMA 42 ou IEC132 (secret, ENV ou embeds activos)."""
    return bool(
        nema56_glb_url_efectiva()
        or nema_pequeno_convencional_liso_glb_url_efectiva()
        or nema_single_phase_one_cap_small_glb_url_efectiva()
        or nema42_glb_url_efectiva()
        or iec132_glb_url_efectiva()
    )


def consulta_lista_motor_tem_familia_glb_dedicada_na_ficha(m: Dict[str, Any]) -> bool:
    """
    Criterio alinhado com `resolve_model_glb_url`: na consulta (list_mode), mostrar o mesmo stack
    de GLB que no detalhe — nao apenas NEMA 56 na ficha, para nao esconder IEC63, bomba, etc.
    """
    if nema_56_somente_ficha_mecanica(m):
        return True
    if iec63_etiqueta_na_carcaca_sem_ne_ma(m):
        return True
    if motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha(m):
        return True
    if motor_familia_iec132_silhueta_somente_ficha(m):
        return True
    if motor_familia_iec_100l_somente_ficha(m):
        return True
    if motor_familia_pump_close_coupled_somente_ficha(m):
        return True
    if motor_familia_explosion_proof_footed_somente_ficha(m):
        return True
    if _is_nema_42_frame(m):
        return True
    return False


def _baked_nema42_glb_activo() -> bool:
    v = _read_secret_or_env("HOLOGRAM_BAKED_NEMA42_GLB", "MOTORES_HOLOGRAM_BAKED_NEMA42_GLB").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def nema42_glb_url_efectiva() -> str:
    """Secret `HOLOGRAM_GLB_NEMA42` / `MOTORES_` ou URL embebida `HOLOGRAM_DEFAULT_NEMA42_GLB_URL`."""
    u = _read_secret_or_env("HOLOGRAM_GLB_NEMA42", "MOTORES_HOLOGRAM_GLB_NEMA42")
    if u and u.lower().startswith(("http://", "https://")) and _path_looks_glb(u):
        return u.strip()
    if _baked_nema42_glb_activo() and HOLOGRAM_DEFAULT_NEMA42_GLB_URL:
        s = str(HOLOGRAM_DEFAULT_NEMA42_GLB_URL).strip()
        if s.lower().startswith(("http://", "https://")) and _path_looks_glb(s):
            return s
    return ""


def _glb_url_catalogo_iec_tefc_b3_se_ficha(m: Dict[str, Any]) -> str:
    """
    URL do catalogo IEC (105 a.glb) quando a ficha nao e NEMA 56 e ha IEC63 na carcaca
    ou familia TEFC B3 completa (63S–132S, B3, TEFC/aletas, …).
    """
    if nema_56_somente_ficha_mecanica(m):
        return ""
    if iec63_etiqueta_na_carcaca_sem_ne_ma(m) or motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha(m):
        return iec_tefc_b3_catalogo_silhueta_glb_url_efectiva()
    return ""


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

    if motor_familia_pump_close_coupled_somente_ficha(m):
        u = pump_close_coupled_glb_url_efectiva()
        if u:
            return u

    if motor_familia_explosion_proof_footed_somente_ficha(m):
        u = explosion_proof_footed_glb_url_efectiva()
        if u:
            return u

    if mecanica_nema56_modo_restrito():
        if nema_56_somente_ficha_mecanica(m):
            u = nema56_glb_url_efectiva_para_motor(m)
            if u:
                return u
        if _is_nema_42_frame(m):
            u = nema42_glb_url_efectiva()
            if u:
                return u
        if motor_familia_iec132_silhueta_somente_ficha(m):
            u = iec132_glb_url_efectiva()
            if u:
                return u
        u = _glb_url_catalogo_iec_tefc_b3_se_ficha(m)
        if u:
            return u
        if motor_familia_iec_100l_somente_ficha(m):
            u = iec_100l_glb_url_efectiva()
            if u:
                return u
        return None

    if nema_56_somente_ficha_mecanica(m):
        u = nema56_glb_url_efectiva_para_motor(m)
        if u:
            return u

    if _is_nema_42_frame(m):
        u = nema42_glb_url_efectiva()
        if u:
            return u

    if motor_familia_iec132_silhueta_somente_ficha(m):
        u = iec132_glb_url_efectiva()
        if u:
            return u

    u = _glb_url_catalogo_iec_tefc_b3_se_ficha(m)
    if u:
        return u

    if motor_familia_iec_100l_somente_ficha(m):
        u = iec_100l_glb_url_efectiva()
        if u:
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

    if n48_aceita_mesma_silueta_motor_liso_nema_56(m):
        u_56 = nema56_glb_url_efectiva_para_motor(m)
        if u_56:
            return u_56

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

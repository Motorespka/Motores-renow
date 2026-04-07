from __future__ import annotations

from html import escape
import re
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import streamlit as st

from utils.motor_view import ALIASES, NOT_INFORMED, friendly, pick_value, resolve_motor_image_url

try:
    from utils.configuracoes_motor import obter_configuracoes_ligacao
except Exception:

    def obter_configuracoes_ligacao(_motor_data: Dict[str, Any]) -> str:
        return "Sugestao tecnica indisponivel."


FieldSpec = Tuple[str, Sequence[str]]

IDENTIFICACAO_FIELDS: List[FieldSpec] = [
    ("Arquivo", ["arquivo"]),
    ("Codigo interno", ["codigo_interno"]),
    ("Origem registro", ["origem_registro"]),
    ("Usuario responsavel", ["usuario_responsavel"]),
    ("Fabricante", ["fabricante"]),
    ("Marca", ["marca"]),
    ("Modelo", ["modelo"]),
    ("Numero serie", ["num_serie"]),
    ("Norma", ["norma"]),
    ("Data fabricacao", ["data_fabricacao"]),
    ("Data cadastro", ["data_cadastro"]),
    ("Localizacao oficina", ["localizacao_oficina"]),
]

ELETRICA_FIELDS: List[FieldSpec] = [
    ("Fases", ["fases"]),
    ("Potencia HP/CV", ["potencia_hp_cv"]),
    ("Potencia kW", ["potencia_kw"]),
    ("Tensao", ["tensao_v"]),
    ("Corrente nominal", ["corrente_nominal_a"]),
    ("RPM nominal", ["rpm_nominal"]),
    ("Frequencia", ["frequencia_hz"]),
    ("Polos", ["polos"]),
    ("Rendimento", ["rendimento_perc"]),
    ("Fator potencia", ["fator_potencia_cos_phi"]),
    ("Fator servico", ["fator_servico"]),
    ("Categoria torque", ["categoria_torque"]),
    ("IP/IN ratio", ["ip_in_ratio"]),
    ("IS/IN ratio", ["is_in_ratio"]),
    ("TP/TN ratio", ["tp_tn_ratio"]),
    ("TMAX/TN ratio", ["tmax_tn_ratio"]),
    ("Tempo rotor bloqueado (s)", ["tempo_rotor_bloqueado_s"]),
    ("Escorregamento", ["escorregamento_perc"]),
]

BOBINAGEM_FIELDS: List[FieldSpec] = [
    ("Numero ranhuras", ["numero_ranhuras"]),
    ("Tipo enrolamento", ["tipo_enrolamento"]),
    ("Fios paralelos", ["fios_paralelos"]),
    ("Ligacao interna", ["ligacao_interna"]),
    ("Numero pontas", ["numero_pontas"]),
    ("Resistencia fase", ["resistencia_ohm_fase"]),
    ("Resistencia isolamento", ["resistencia_isolamento_megohmetro"]),
    ("Tipo fio", ["tipo_fio"]),
    ("Passo principal", ["passo_principal"]),
    ("Espiras principal", ["espiras_principal"]),
    ("Bitola principal", ["bitola_fio_principal"]),
    ("Peso cobre principal", ["peso_cobre_principal_kg"]),
    ("Passo auxiliar", ["passo_auxiliar"]),
    ("Espiras auxiliar", ["espiras_auxiliar"]),
    ("Bitola auxiliar", ["bitola_fio_auxiliar"]),
    ("Peso cobre auxiliar", ["peso_cobre_auxiliar_kg"]),
    ("Capacitor partida", ["capacitor_partida"]),
    ("Capacitor permanente", ["capacitor_permanente"]),
]

MECANICA_FIELDS: List[FieldSpec] = [
    ("Tipo centrifugo/platinado", ["tipo_centrifugo_platinado"]),
    ("Protecao termica", ["protecao_termica"]),
    ("Carcaca", ["carcaca"]),
    ("Diametro interno estator", ["diametro_interno_estator_mm"]),
    ("Diametro externo estator", ["diametro_externo_estator_mm"]),
    ("Comprimento pacote", ["comprimento_pacote_mm"]),
    ("Material nucleo", ["material_nucleo"]),
    ("Rolamento dianteiro", ["rolamento_dianteiro"]),
    ("Rolamento traseiro", ["rolamento_traseiro"]),
    ("Tipo graxa", ["tipo_graxa"]),
    ("Grau protecao", ["grau_protecao_ip"]),
    ("Classe isolacao", ["classe_isolacao"]),
    ("Regime servico", ["regime_servico"]),
    ("Sentido rotacao", ["sentido_rotacao"]),
    ("Peso total", ["peso_total_kg"]),
]

ARQUIVOS_FIELDS: List[FieldSpec] = [
    ("URL foto placa", ["url_foto_placa"]),
    ("URL desenho tecnico", ["url_desenho_tecnico"]),
    ("Especificacoes extra", ["especificacoes_extra"]),
    ("Observacoes", ["observacoes"]),
]

BRAND_HINTS = {
    "WEG",
    "HERCULES",
    "SCHNEIDER",
    "SIEMENS",
    "TOSHIBA",
    "ELETROPLAS",
    "JET",
    "JETPUMP",
    "DANCOR",
    "BOSCH",
    "TRAMONTINA",
    "LEAO",
    "METAL",
    "BOMBAS",
}

TITLE_STOPWORDS = {
    "MOTOR",
    "MOTORES",
    "MONOFASICOS",
    "TRIFASICOS",
    "DADOS",
    "BOBINAGEM",
    "CAPACITOR",
    "PARTIDA",
    "ARQUIVO",
    "REGISTRO",
    "PDF",
    "ID",
}


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Rajdhani:wght@500;700&display=swap');

        .motor-card-click-wrap {
            position: relative;
            margin: 0.95rem 0 1.35rem 0;
            cursor: pointer;
        }
        .motor-card-visual {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(0, 242, 255, 0.34);
            border-radius: 14px;
            background:
                radial-gradient(circle at 20% 0%, rgba(0, 242, 255, 0.08), transparent 50%),
                linear-gradient(160deg, rgba(3, 13, 24, 0.96), rgba(2, 9, 17, 0.96)),
                repeating-linear-gradient(0deg, rgba(0, 242, 255, 0.03) 0px, rgba(0, 242, 255, 0.03) 1px, transparent 1px, transparent 20px);
            min-height: 108px;
            box-shadow: 0 0 0 rgba(0, 242, 255, 0);
            padding: 0.74rem 0.95rem 0.78rem 0.95rem;
            transition: all 180ms ease-in-out;
        }
        .motor-card-visual::before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, transparent, rgba(0, 242, 255, 0.05), transparent);
            opacity: 0;
            transition: opacity 180ms ease-in-out;
            pointer-events: none;
        }
        .motor-card-visual.is-open,
        .motor-card-click-wrap:hover .motor-card-visual {
            border-color: rgba(0, 242, 255, 0.92);
            box-shadow: 0 0 24px rgba(0, 242, 255, 0.24), inset 0 0 16px rgba(0, 242, 255, 0.08);
        }
        .motor-card-visual.is-open::before,
        .motor-card-click-wrap:hover .motor-card-visual::before {
            opacity: 1;
        }
        .motor-card-title {
            text-align: center;
            color: #00f2ff;
            font-family: "Orbitron", "Rajdhani", monospace;
            font-size: 1.04rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-top: 0.06rem;
            line-height: 1.1;
        }
        .motor-card-id {
            text-align: center;
            color: #7f9baa;
            font-family: "Rajdhani", "Consolas", monospace;
            font-size: 0.67rem;
            letter-spacing: 0.08em;
            margin-top: 0.2rem;
        }
        .motor-card-metrics {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin-top: 0.64rem;
            gap: 0.2rem;
        }
        .motor-card-metric {
            text-align: center;
            font-family: "Orbitron", "Rajdhani", monospace;
            font-size: 0.99rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            line-height: 1.1;
            text-transform: uppercase;
        }
        .metric-power { color: #53f7ff; }
        .metric-rpm { color: #4cffb1; }
        .metric-current { color: #ffba5c; }

        .motor-card-click-wrap div[data-testid="stButton"] {
            position: absolute;
            inset: 0;
            margin: 0 !important;
            z-index: 3;
        }
        .motor-card-click-wrap div[data-testid="stButton"] > button {
            width: 100%;
            height: 100%;
            opacity: 0;
            border: none !important;
            background: transparent !important;
            color: transparent !important;
            box-shadow: none !important;
            margin: 0 !important;
            padding: 0 !important;
            font-size: 0 !important;
            min-height: 100% !important;
        }

        .motor-details-shell {
            margin-top: 0.05rem;
            margin-bottom: 1.05rem;
            border-radius: 14px;
            border: 1px solid rgba(0, 242, 255, 0.32);
            background: linear-gradient(155deg, rgba(5, 14, 26, 0.96), rgba(2, 8, 16, 0.96));
            padding: 12px;
            font-family: "Rajdhani", "Consolas", monospace;
        }

        .motor-head {
            border: 1px solid rgba(0, 242, 255, 0.20);
            border-radius: 10px;
            background: rgba(0, 242, 255, 0.05);
            padding: 0.62rem 0.72rem;
            margin-bottom: 0.55rem;
        }
        .motor-head h4 {
            margin: 0;
            color: #d7f8ff;
            font-family: "Orbitron", monospace;
            font-size: 0.98rem;
            letter-spacing: 0.04em;
        }
        .motor-head p {
            margin: 0.1rem 0 0 0;
            color: #8bb2c3;
            font-size: 0.8rem;
        }

        .motor-metrics {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.38rem;
            margin-bottom: 0.58rem;
        }
        .motor-metric {
            border: 1px solid rgba(0, 242, 255, 0.18);
            background: rgba(0, 242, 255, 0.04);
            border-radius: 10px;
            padding: 0.42rem 0.5rem;
        }
        .motor-metric .k {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: #7ba4b7;
            margin-bottom: 0.08rem;
        }
        .motor-metric .v {
            font-size: 0.9rem;
            font-weight: 700;
            color: #f2fbff;
        }

        .motor-panel {
            border: 1px solid rgba(0, 242, 255, 0.18);
            border-radius: 10px;
            background: rgba(0, 242, 255, 0.04);
            padding: 0.58rem;
            margin-bottom: 0.58rem;
        }
        .motor-panel-title {
            font-family: "Orbitron", "Rajdhani", monospace;
            color: #95eaff;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            font-size: 0.74rem;
            margin-bottom: 0.38rem;
        }

        .motor-kv {
            border-radius: 9px;
            border: 1px solid rgba(0, 242, 255, 0.14);
            background: rgba(0, 242, 255, 0.03);
            padding: 0.45rem 0.55rem;
            margin-bottom: 0.35rem;
        }
        .motor-kv-label {
            font-size: 0.66rem;
            color: #7aa5b7;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.14rem;
        }
        .motor-kv-value {
            font-size: 0.87rem;
            color: #f3fbff;
            font-weight: 600;
            word-break: break-word;
        }

        .motor-holo-frame {
            position: relative;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid rgba(0, 242, 255, 0.22);
            box-shadow: 0 0 14px rgba(0, 242, 255, 0.16);
            min-height: 180px;
        }
        .motor-holo-img {
            width: 100%;
            height: 210px;
            object-fit: cover;
            filter: saturate(1.03) contrast(1.0) brightness(0.92);
            display: block;
        }
        .motor-holo-scan {
            position: absolute;
            inset: 0;
            background:
                linear-gradient(125deg, rgba(0, 242, 255, 0.08), rgba(22, 13, 52, 0.08)),
                repeating-linear-gradient(0deg, rgba(0, 242, 255, 0.10) 0px, rgba(0, 242, 255, 0.10) 1px, transparent 1px, transparent 16px);
            pointer-events: none;
        }
        .motor-holo-hud {
            position: absolute;
            left: 8px;
            right: 8px;
            bottom: 8px;
            border: 1px solid rgba(0, 242, 255, 0.28);
            border-radius: 8px;
            background: rgba(2, 12, 20, 0.76);
            padding: 0.38rem 0.5rem;
        }
        .motor-holo-title {
            color: #7ae8ff;
            font-weight: 700;
            letter-spacing: 0.08em;
            font-size: 0.68rem;
            margin-bottom: 0.14rem;
            text-transform: uppercase;
        }
        .motor-holo-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #dff7ff;
            font-size: 0.78rem;
            border-top: 1px solid rgba(0, 242, 255, 0.1);
            padding-top: 0.13rem;
            margin-top: 0.13rem;
        }
        .motor-holo-line span {
            color: #74d4ec;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.66rem;
        }

        @media (max-width: 768px) {
            .motor-card-visual {
                min-height: 102px;
                padding: 0.64rem 0.66rem 0.68rem 0.66rem;
            }
            .motor-card-title { font-size: 0.95rem; }
            .motor-card-id { font-size: 0.63rem; }
            .motor-card-metric { font-size: 0.92rem; }
            .motor-metrics {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .motor-holo-img {
                height: 185px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _tipo_fase(motor: Dict[str, Any]) -> str:
    fase_raw = str(pick_value(motor, ALIASES["fases"]) or "").strip().lower()
    if not fase_raw:
        return NOT_INFORMED

    if "mono" in fase_raw:
        return "Monofasico"
    if "tri" in fase_raw:
        return "Trifasico"

    try:
        fase_num = int(float(fase_raw.replace(",", ".")))
        if fase_num == 1:
            return "Monofasico"
        if fase_num == 3:
            return "Trifasico"
    except Exception:
        pass

    return friendly(pick_value(motor, ["fases"]))


def _is_monofasico(motor: Dict[str, Any]) -> bool:
    return _tipo_fase(motor) == "Monofasico"


def _render_pairs_grid(motor: Dict[str, Any], fields: Iterable[FieldSpec], columns: int = 2) -> None:
    cols = st.columns(columns)
    for idx, (label, aliases) in enumerate(fields):
        value = friendly(pick_value(motor, aliases))
        with cols[idx % columns]:
            st.markdown(
                f"""
                <div class="motor-kv">
                    <div class="motor-kv-label">{escape(label)}</div>
                    <div class="motor-kv-value">{escape(value)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_hologram_panel(motor: Dict[str, Any]) -> None:
    image_url = resolve_motor_image_url(motor)
    hud_lines = [
        ("Marca", friendly(pick_value(motor, ["marca", "fabricante"]))),
        ("Modelo", friendly(pick_value(motor, ["modelo", "codigo_interno"]))),
        ("Potencia", friendly(pick_value(motor, ["potencia_hp_cv", "potencia_kw"]))),
        ("RPM", friendly(pick_value(motor, ["rpm_nominal"]))),
    ]
    lines_html = "".join(
        f'<div class="motor-holo-line"><span>{escape(label)}</span><b>{escape(value)}</b></div>'
        for label, value in hud_lines
    )

    st.markdown(
        f"""
        <div class="motor-holo-frame">
            <img src="{escape(image_url, quote=True)}" class="motor-holo-img" alt="Foto do motor" />
            <div class="motor-holo-scan"></div>
            <div class="motor-holo-hud">
                <div class="motor-holo-title">Painel tecnico</div>
                {lines_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_header(motor: Dict[str, Any]) -> None:
    title = _display_title(motor)
    subtitle = _display_id(motor)
    tipo = _tipo_fase(motor)
    st.markdown(
        f"""
        <div class="motor-head">
            <h4>{escape(title)}</h4>
            <p>{escape(subtitle)} | Tipo: {escape(tipo)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_kpis(motor: Dict[str, Any]) -> None:
    metrics = [
        ("Potencia", _display_power(motor)),
        ("RPM", _display_rpm(motor)),
        ("Tensao", friendly(pick_value(motor, ["tensao_v"]))),
        ("Corrente", _display_current(motor)),
    ]
    items = "".join(
        f'<div class="motor-metric"><div class="k">{escape(k)}</div><div class="v">{escape(v)}</div></div>'
        for k, v in metrics
    )
    st.markdown(f'<div class="motor-metrics">{items}</div>', unsafe_allow_html=True)


def _blob(motor: Dict[str, Any]) -> str:
    parts = []
    for key in [
        "arquivo",
        "modelo",
        "marca",
        "fabricante",
        "num_serie",
        "codigo_interno",
        "observacoes",
        "potencia_hp_cv",
        "potencia_kw",
        "rpm_nominal",
        "corrente_nominal_a",
    ]:
        raw = motor.get(key)
        if raw is not None:
            parts.append(str(raw))
    return " | ".join(parts)


def _regex_first(pattern: str, txt: str) -> str | None:
    m = re.search(pattern, txt, flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(0).strip()


def _compact_text(value: Any) -> str:
    if value is None:
        return ""
    txt = str(value).upper()
    txt = re.sub(r"\.PDF\b", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"[_|]+", " ", txt)
    txt = re.sub(r"[^A-Z0-9/\-., ]+", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _pick_short_candidate(candidates: List[str]) -> str:
    for raw in candidates:
        cleaned = _compact_text(raw)
        if not cleaned:
            continue
        if len(cleaned) <= 22 and not re.search(r"\d{2,}.*\d{2,}", cleaned):
            return cleaned
    return ""


def _detect_brand_token(txt: str) -> str:
    cleaned = _compact_text(txt)
    if not cleaned:
        return ""

    for hint in BRAND_HINTS:
        if re.search(rf"\b{re.escape(hint)}\b", cleaned):
            return hint

    for token in cleaned.split():
        if token in TITLE_STOPWORDS:
            continue
        if not re.fullmatch(r"[A-Z0-9/-]{3,18}", token):
            continue
        if any(ch.isdigit() for ch in token):
            continue
        return token
    return ""


def _clip_metric(value: str, max_chars: int = 14) -> str:
    txt = re.sub(r"\s+", " ", str(value)).strip()
    if not txt:
        return NOT_INFORMED
    if len(txt) <= max_chars:
        return txt

    token = re.search(r"\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?", txt)
    if token:
        maybe = token.group(0)
        if "RPM" in txt.upper():
            return f"{maybe} RPM"
        if " A" in txt.upper():
            return f"{maybe} A"
        if re.search(r"\b(CV|HP|KW)\b", txt.upper()):
            unit = re.search(r"\b(CV|HP|KW)\b", txt.upper())
            if unit:
                return f"{maybe} {unit.group(1)}"
    return txt[:max_chars].rstrip() + "..."


def _display_title(motor: Dict[str, Any]) -> str:
    raw_candidates: List[str] = []
    for aliases in (["marca"], ["fabricante"], ["modelo"], ["codigo_interno"], ["arquivo"]):
        value = pick_value(motor, aliases)
        if value:
            raw_candidates.append(str(value))

    direct = _pick_short_candidate(raw_candidates)
    if direct and direct not in TITLE_STOPWORDS:
        token = _detect_brand_token(direct)
        return token if token else direct[:20].rstrip()

    merged = " ".join(raw_candidates + [_blob(motor)])
    token = _detect_brand_token(merged)
    if token:
        return token

    return "MOTOR"


def _display_id(motor: Dict[str, Any]) -> str:
    raw = pick_value(motor, ["codigo_interno", "num_serie"])
    if raw:
        return f"ID: {_clip_metric(friendly(raw), max_chars=18)}"

    txt = _blob(motor)
    m = re.search(r"\bID\s*[:#-]?\s*([A-Za-z0-9.-]+)", txt, flags=re.IGNORECASE)
    if m:
        return f"ID: {m.group(1)}"

    return f"ID: {friendly(motor.get('id'))}"


def _display_power(motor: Dict[str, Any]) -> str:
    raw = pick_value(motor, ["potencia_hp_cv", "potencia_kw"])
    if raw:
        val = friendly(raw).upper()
        if re.fullmatch(r"\d+(?:[.,]\d+)?", val):
            return f"{val} CV"
        return _clip_metric(val, max_chars=14)
    txt = _blob(motor)
    found = _regex_first(r"\b\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?\s*(?:CV|HP|KW)\b", txt)
    if found:
        return _clip_metric(found.upper(), max_chars=14)
    return NOT_INFORMED


def _display_rpm(motor: Dict[str, Any]) -> str:
    raw = pick_value(motor, ["rpm_nominal"])
    if raw:
        val = friendly(raw)
        if re.fullmatch(r"\d{3,5}", val):
            return f"{val} RPM"
        rpm_num = _regex_first(r"\d{3,5}", val)
        if rpm_num:
            return f"{rpm_num} RPM"
        return _clip_metric(val.upper(), max_chars=14)
    txt = _blob(motor)
    found = _regex_first(r"\b\d{3,5}\s*RPM\b", txt)
    if found:
        return _clip_metric(found.upper(), max_chars=14)
    return NOT_INFORMED


def _display_current(motor: Dict[str, Any]) -> str:
    raw = pick_value(motor, ["corrente_nominal_a"])
    if raw:
        val = friendly(raw)
        if re.fullmatch(r"\d+(?:[.,]\d+)?", val):
            return f"{val} A"
        amps = _regex_first(r"\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?", val)
        if amps:
            return f"{amps} A"
        return _clip_metric(val.upper(), max_chars=14)
    txt = _blob(motor)
    found = _regex_first(r"\b\d+(?:[.,]\d+)?(?:/\d+(?:[.,]\d+)?)?\s*A\b", txt)
    if found:
        return _clip_metric(found.upper(), max_chars=14)
    return NOT_INFORMED


def motor_card(motor: Dict[str, Any], card_id: str, is_expanded: bool) -> bool:
    _inject_styles()

    title = _display_title(motor)
    subtitle = _display_id(motor)
    power = _display_power(motor)
    rpm = _display_rpm(motor)
    current = _display_current(motor)

    visual_cls = "motor-card-visual is-open" if is_expanded else "motor-card-visual"
    st.markdown('<div class="motor-card-click-wrap">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="{visual_cls}">
            <div class="motor-card-title">{escape(title)}</div>
            <div class="motor-card-id">{escape(subtitle)}</div>
            <div class="motor-card-metrics">
                <div class="motor-card-metric metric-power">{escape(power)}</div>
                <div class="motor-card-metric metric-rpm">{escape(rpm)}</div>
                <div class="motor-card-metric metric-current">{escape(current)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    toggle_label = "Fechar detalhes" if is_expanded else "Abrir detalhes"
    clicked = st.button(toggle_label, key=f"motor_btn_{card_id}", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if is_expanded:
        st.markdown('<div class="motor-details-shell">', unsafe_allow_html=True)
        _render_header(motor)
        _render_kpis(motor)

        col_l, col_r = st.columns([1.25, 1])
        with col_l:
            st.markdown('<div class="motor-panel"><div class="motor-panel-title">Ligacao tecnica</div>', unsafe_allow_html=True)
            st.info(obter_configuracoes_ligacao(motor))
            st.markdown('</div>', unsafe_allow_html=True)
        with col_r:
            _render_hologram_panel(motor)

        t1, t2, t3, t4, t5 = st.tabs(["Identificacao", "Eletrica", "Bobinagem", "Mecanica", "Arquivos"])

        with t1:
            _render_pairs_grid(motor, IDENTIFICACAO_FIELDS, columns=3)
        with t2:
            _render_pairs_grid(motor, ELETRICA_FIELDS, columns=3)
        with t3:
            _render_pairs_grid(motor, BOBINAGEM_FIELDS, columns=2)
            if _is_monofasico(motor):
                st.markdown("##### Enrolamento auxiliar")
                _render_pairs_grid(
                    motor,
                    [
                        ("Passo auxiliar", ["passo_auxiliar"]),
                        ("Espiras auxiliar", ["espiras_auxiliar"]),
                        ("Bitola auxiliar", ["bitola_fio_auxiliar"]),
                        ("Peso cobre auxiliar", ["peso_cobre_auxiliar_kg"]),
                    ],
                    columns=2,
                )
        with t4:
            _render_pairs_grid(motor, MECANICA_FIELDS, columns=3)
        with t5:
            _render_pairs_grid(motor, ARQUIVOS_FIELDS, columns=2)

        st.markdown("</div>", unsafe_allow_html=True)

    return clicked

from __future__ import annotations

from html import escape
from typing import Any, Dict, Iterable, List, Tuple

import streamlit as st

from utils.motor_view import ALIASES, NOT_INFORMED, friendly, is_empty, normalize_key, pick_value, resolve_motor_image_url

try:
    from utils.configuracoes_motor import obter_configuracoes_ligacao
except Exception:

    def obter_configuracoes_ligacao(_motor_data: Dict[str, Any]) -> str:
        return "Sugestao tecnica indisponivel."


FieldSpec = Tuple[str, List[str]]

SUMMARY_FIELDS: List[List[str]] = [
    ALIASES["marca"],
    ALIASES["modelo"],
    ALIASES["potencia"],
    ALIASES["rpm"],
    ALIASES["corrente"],
    ALIASES["polos"],
    ALIASES["fases"],
    ALIASES["tensao"],
]

BOBINAGEM_FIELDS: List[FieldSpec] = [
    ("Passo principal", ["passo_principal", "passo_princ", "passo principal"]),
    ("Bobina principal", ["espiras_principal", "bobina_principal", "espiras principal", "espiras"]),
    ("Fio principal", ["bitola_fio_principal", "fio_principal", "bitola fio principal"]),
    ("Ligacao interna", ["ligacao_interna", "ligacao interna", "esquema", "ligacao"]),
    ("Tipo de bobinagem", ["tipo_enrolamento", "tipo_bobinagem", "tipo bobinagem", "enrolamento"]),
    ("Fios em paralelo", ["fios_paralelos", "fios em paralelo", "fios_paralelo"]),
    ("Resistencia por fase", ["resistencia_ohm_fase", "resistencia_fase", "resistencia por fase"]),
    ("Numero de ranhuras", ["numero_ranhuras", "n_ranhuras", "ranhuras"]),
    ("Capacitor partida", ["capacitor_partida", "capacitor de partida"]),
    ("Capacitor permanente", ["capacitor_permanente", "capacitor permanente"]),
]

AUX_BOBINAGEM_FIELDS: List[FieldSpec] = [
    ("Passo auxiliar", ["passo_auxiliar", "passo auxiliar"]),
    ("Bobina auxiliar", ["espiras_auxiliar", "bobina_auxiliar", "espiras auxiliar"]),
    ("Fio auxiliar", ["bitola_fio_auxiliar", "fio_auxiliar", "bitola fio auxiliar"]),
]

MECANICA_FIELDS: List[FieldSpec] = [
    ("Rolamento dianteiro", ["rolamento_dianteiro", "rolamento dianteiro"]),
    ("Rolamento traseiro", ["rolamento_traseiro", "rolamento traseiro"]),
    ("Tamanho do eixo", ["tamanho_eixo", "tamanho do eixo"]),
    ("Diametro do eixo (mm)", ["diametro_eixo_mm", "diametro do eixo", "diametro eixo"]),
    ("Carcaca", ["carcaca", "carcaca motor"]),
    ("Comprimento pacote (mm)", ["comprimento_pacote_mm", "comprimento pacote"]),
    ("Diametro interno estator (mm)", ["diametro_interno_estator_mm", "diametro interno estator"]),
    ("Diametro externo estator (mm)", ["diametro_externo_estator_mm", "diametro externo estator"]),
    ("Material do nucleo", ["material_nucleo", "material do nucleo"]),
    ("Tipo de graxa", ["tipo_graxa", "graxa"]),
    ("Peso total (kg)", ["peso_total_kg", "peso total", "peso"]),
]


def _inject_styles() -> None:
    if st.session_state.get("_motor_card_styles_loaded"):
        return

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Rajdhani:wght@500;700&display=swap');

        .motor-card-btn div[data-testid="stButton"] > button {
            width: 100%;
            min-height: 130px;
            border-radius: 14px;
            border: 1px solid rgba(0, 242, 255, 0.42) !important;
            background:
                linear-gradient(155deg, rgba(3, 14, 28, 0.95), rgba(2, 10, 20, 0.95)),
                repeating-linear-gradient(0deg, rgba(0, 242, 255, 0.06) 0px, rgba(0, 242, 255, 0.06) 1px, transparent 1px, transparent 22px);
            color: #e9f8ff !important;
            box-shadow: 0 6px 18px rgba(0, 242, 255, 0.14) !important;
            padding: 1.15rem 1.15rem;
            text-align: left;
            white-space: pre-line;
            line-height: 1.5;
            font-size: 1rem;
            font-family: "Rajdhani", "Orbitron", "Consolas", monospace !important;
            letter-spacing: 0.02em;
            transition: all 150ms ease-in-out;
        }
        .motor-card-btn div[data-testid="stButton"] > button:hover {
            border-color: rgba(0, 242, 255, 0.9) !important;
            box-shadow: 0 0 22px rgba(0, 242, 255, 0.32) !important;
            transform: translateY(-1px);
        }
        .motor-card-open div[data-testid="stButton"] > button {
            border-color: #00f2ff !important;
            box-shadow: 0 0 26px rgba(0, 242, 255, 0.36) !important;
        }

        .motor-details-shell {
            margin-top: 0.05rem;
            margin-bottom: 1.2rem;
            border-radius: 14px;
            border: 1px solid rgba(0, 242, 255, 0.33);
            background: linear-gradient(155deg, rgba(5, 14, 26, 0.96), rgba(2, 8, 16, 0.96));
            padding: 14px;
            font-family: "Rajdhani", "Consolas", monospace;
        }
        .motor-section-title {
            font-family: "Orbitron", "Rajdhani", monospace;
            color: #93eaff;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            font-size: 0.82rem;
            margin-bottom: 0.45rem;
        }
        .motor-head {
            border: 1px solid rgba(0, 242, 255, 0.2);
            border-radius: 10px;
            background: rgba(0, 242, 255, 0.05);
            padding: 0.7rem 0.82rem;
            margin-bottom: 0.75rem;
        }
        .motor-head h4 {
            margin: 0;
            color: #d6f8ff;
            font-family: "Orbitron", monospace;
            font-size: 1.03rem;
            letter-spacing: 0.04em;
        }
        .motor-head p {
            margin: 0.16rem 0 0 0;
            color: #8cb6c6;
            font-size: 0.86rem;
        }
        .motor-metrics {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.45rem;
            margin-bottom: 0.7rem;
        }
        .motor-metric {
            border: 1px solid rgba(0, 242, 255, 0.2);
            background: rgba(0, 242, 255, 0.04);
            border-radius: 10px;
            padding: 0.45rem 0.55rem;
        }
        .motor-metric .k {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #7ba4b7;
            margin-bottom: 0.12rem;
        }
        .motor-metric .v {
            font-size: 0.98rem;
            font-weight: 700;
            color: #f2fbff;
        }

        .motor-kv {
            border-radius: 10px;
            border: 1px solid rgba(0, 242, 255, 0.16);
            background: rgba(0, 242, 255, 0.04);
            padding: 0.52rem 0.62rem;
            margin-bottom: 0.46rem;
        }
        .motor-kv-label {
            font-size: 0.72rem;
            color: #7aa5b7;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 0.18rem;
        }
        .motor-kv-value {
            font-size: 0.95rem;
            color: #f4fbff;
            font-weight: 600;
            word-break: break-word;
        }

        .motor-holo-frame {
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(0, 242, 255, 0.25);
            box-shadow: 0 0 18px rgba(0, 242, 255, 0.18);
            min-height: 220px;
        }
        .motor-holo-img {
            width: 100%;
            height: 250px;
            object-fit: cover;
            filter: saturate(1.04) contrast(1.01) brightness(0.92);
            display: block;
        }
        .motor-holo-scan {
            position: absolute;
            inset: 0;
            background:
                linear-gradient(125deg, rgba(0, 242, 255, 0.08), rgba(22, 13, 52, 0.08)),
                repeating-linear-gradient(0deg, rgba(0, 242, 255, 0.11) 0px, rgba(0, 242, 255, 0.11) 1px, transparent 1px, transparent 17px);
            pointer-events: none;
        }
        .motor-holo-hud {
            position: absolute;
            left: 9px;
            right: 9px;
            bottom: 9px;
            border: 1px solid rgba(0, 242, 255, 0.3);
            border-radius: 9px;
            background: rgba(2, 12, 20, 0.74);
            padding: 0.45rem 0.58rem;
        }
        .motor-holo-title {
            color: #7ae8ff;
            font-weight: 700;
            letter-spacing: 0.08em;
            font-size: 0.74rem;
            margin-bottom: 0.2rem;
            text-transform: uppercase;
        }
        .motor-holo-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #dff7ff;
            font-size: 0.83rem;
            border-top: 1px solid rgba(0, 242, 255, 0.1);
            padding-top: 0.17rem;
            margin-top: 0.17rem;
        }
        .motor-holo-line span {
            color: #74d4ec;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.7rem;
        }

        @media (max-width: 768px) {
            .motor-card-btn div[data-testid="stButton"] > button {
                min-height: 116px;
                font-size: 0.94rem;
                padding: 0.95rem 0.9rem;
            }
            .motor-details-shell {
                padding: 11px;
            }
            .motor-metrics {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .motor-holo-img {
                height: 215px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_motor_card_styles_loaded"] = True


def _format_label(raw_key: str) -> str:
    return raw_key.replace("_", " ").strip().title()


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

    return friendly(pick_value(motor, ALIASES["fases"]))


def _is_monofasico(motor: Dict[str, Any]) -> bool:
    return _tipo_fase(motor) == "Monofasico"


def _field_pairs(motor: Dict[str, Any], fields: Iterable[FieldSpec]) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for label, aliases in fields:
        pairs.append((label, friendly(pick_value(motor, aliases))))
    return pairs


def _all_known_normalized_keys() -> set[str]:
    known: set[str] = set()
    for alias_group in SUMMARY_FIELDS:
        known.update(normalize_key(alias) for alias in alias_group)
    for _label, aliases in BOBINAGEM_FIELDS + AUX_BOBINAGEM_FIELDS + MECANICA_FIELDS:
        known.update(normalize_key(alias) for alias in aliases)
    known.update(normalize_key(alias) for alias in ALIASES["imagem"])
    return known


def _general_pairs(motor: Dict[str, Any]) -> List[Tuple[str, str]]:
    excluded = _all_known_normalized_keys()
    pairs: List[Tuple[str, str]] = []

    for raw_key in sorted(motor.keys()):
        if raw_key.startswith("_"):
            continue
        if normalize_key(raw_key) in excluded:
            continue
        pairs.append((_format_label(raw_key), friendly(motor.get(raw_key))))

    return pairs


def _render_pairs_grid(pairs: List[Tuple[str, str]], columns: int = 3) -> None:
    if not pairs:
        st.info("Nenhum dado disponivel.")
        return

    cols = st.columns(columns)
    for idx, (label, value) in enumerate(pairs):
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
        ("Marca", friendly(pick_value(motor, ALIASES["marca"]))),
        ("Modelo", friendly(pick_value(motor, ALIASES["modelo"]))),
        ("Potencia", friendly(pick_value(motor, ALIASES["potencia"]))),
        ("RPM", friendly(pick_value(motor, ALIASES["rpm"]))),
        ("Corrente", friendly(pick_value(motor, ALIASES["corrente"]))),
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


def _render_dashboard_header(motor: Dict[str, Any]) -> None:
    marca = friendly(pick_value(motor, ALIASES["marca"]))
    modelo = friendly(pick_value(motor, ALIASES["modelo"]))
    registro = friendly(motor.get("id"))

    st.markdown(
        f"""
        <div class="motor-head">
            <h4>{escape(marca)} | {escape(modelo)}</h4>
            <p>ID #{escape(registro)} | Tipo: {escape(_tipo_fase(motor))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_dashboard_metrics(motor: Dict[str, Any]) -> None:
    metrics = [
        ("Potencia", friendly(pick_value(motor, ALIASES["potencia"]))),
        ("RPM", friendly(pick_value(motor, ALIASES["rpm"]))),
        ("Tensao", friendly(pick_value(motor, ALIASES["tensao"]))),
        ("Corrente", friendly(pick_value(motor, ALIASES["corrente"]))),
    ]
    items = "".join(
        f'<div class="motor-metric"><div class="k">{escape(k)}</div><div class="v">{escape(v)}</div></div>'
        for k, v in metrics
    )
    st.markdown(f'<div class="motor-metrics">{items}</div>', unsafe_allow_html=True)


def motor_card(motor: Dict[str, Any], card_id: str, is_expanded: bool) -> bool:
    _inject_styles()

    marca = friendly(pick_value(motor, ALIASES["marca"]))
    modelo = friendly(pick_value(motor, ALIASES["modelo"]))
    potencia = friendly(pick_value(motor, ALIASES["potencia"]))
    rpm = friendly(pick_value(motor, ALIASES["rpm"]))
    amperagem = friendly(pick_value(motor, ALIASES["corrente"]))
    registro = friendly(motor.get("id"))

    if is_empty(modelo):
        modelo = f"Registro #{registro}"

    card_title = f"{marca}" if not is_empty(marca) else modelo
    label = (
        f"{card_title}\n"
        f"ID: {registro}\n"
        f"{potencia}    |    {rpm}    |    {amperagem}"
    )

    wrapper_class = "motor-card-btn motor-card-open" if is_expanded else "motor-card-btn"
    st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
    clicked = st.button(
        label,
        key=f"motor_btn_{card_id}",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if is_expanded:
        st.markdown('<div class="motor-details-shell">', unsafe_allow_html=True)
        _render_dashboard_header(motor)
        _render_dashboard_metrics(motor)

        col_left, col_right = st.columns([1.2, 1])
        with col_left:
            st.markdown('<div class="motor-section-title">Ligacao tecnica</div>', unsafe_allow_html=True)
            st.info(obter_configuracoes_ligacao(motor))
        with col_right:
            _render_hologram_panel(motor)

        tab_geral, tab_bob, tab_mec = st.tabs(["Identificacao", "Bobinagem", "Mecanica"])

        with tab_geral:
            _render_pairs_grid(_general_pairs(motor), columns=3)

        with tab_bob:
            _render_pairs_grid(_field_pairs(motor, BOBINAGEM_FIELDS), columns=2)
            if _is_monofasico(motor):
                st.markdown("##### Enrolamento auxiliar (monofasico)")
                _render_pairs_grid(_field_pairs(motor, AUX_BOBINAGEM_FIELDS), columns=2)

        with tab_mec:
            _render_pairs_grid(_field_pairs(motor, MECANICA_FIELDS), columns=2)

        st.markdown("</div>", unsafe_allow_html=True)

    return clicked

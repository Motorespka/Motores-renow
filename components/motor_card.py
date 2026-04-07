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
            min-height: 250px;
            border-radius: 20px;
            border: 1px solid rgba(0, 242, 255, 0.62) !important;
            background-image:
                linear-gradient(140deg, rgba(2, 10, 22, 0.95), rgba(2, 5, 14, 0.95)),
                repeating-linear-gradient(0deg, rgba(0, 242, 255, 0.08) 0px, rgba(0, 242, 255, 0.08) 1px, transparent 1px, transparent 24px),
                url('https://images.unsplash.com/photo-1763952626662-419b004e1783?auto=format&fit=crop&fm=jpg&q=50&w=1200') !important;
            background-size: cover, auto, cover !important;
            background-position: center;
            background-blend-mode: normal, screen, luminosity;
            color: #effbff !important;
            box-shadow: 0 16px 44px rgba(0, 242, 255, 0.24) !important;
            padding: 1.45rem 1.5rem;
            text-align: left;
            white-space: pre-line;
            line-height: 1.65;
            font-size: 1.14rem;
            font-family: "Rajdhani", "Orbitron", "Consolas", monospace !important;
            letter-spacing: 0.02em;
            text-shadow: 0 0 10px rgba(0, 242, 255, 0.28);
            transition: all 180ms ease-in-out;
        }
        .motor-card-btn div[data-testid="stButton"] > button:hover {
            border-color: rgba(0, 242, 255, 0.95) !important;
            box-shadow: 0 20px 58px rgba(0, 242, 255, 0.38) !important;
            transform: translateY(-2px);
        }
        .motor-card-open div[data-testid="stButton"] > button {
            border-color: #00f2ff !important;
            box-shadow: 0 20px 60px rgba(0, 242, 255, 0.45) !important;
        }
        .motor-details-shell {
            margin-top: -0.2rem;
            margin-bottom: 1.35rem;
            border-radius: 14px;
            border: 1px solid rgba(0, 242, 255, 0.35);
            background: linear-gradient(155deg, rgba(6, 15, 26, 0.95), rgba(2, 7, 14, 0.95));
            padding: 16px;
            font-family: "Rajdhani", "Consolas", monospace;
        }
        .motor-kv {
            border-radius: 10px;
            border: 1px solid rgba(0, 242, 255, 0.18);
            background: rgba(0, 242, 255, 0.04);
            padding: 0.6rem 0.72rem;
            margin-bottom: 0.55rem;
        }
        .motor-kv-label {
            font-size: 0.76rem;
            color: #7aa5b7;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 0.22rem;
        }
        .motor-kv-value {
            font-size: 1rem;
            color: #f4fbff;
            font-weight: 600;
            word-break: break-word;
        }
        .motor-holo-frame {
            position: relative;
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid rgba(0, 242, 255, 0.3);
            box-shadow: 0 0 24px rgba(0, 242, 255, 0.2);
            margin-bottom: 0.9rem;
            min-height: 260px;
        }
        .motor-holo-img {
            width: 100%;
            height: 300px;
            object-fit: cover;
            filter: saturate(1.05) contrast(1.02) brightness(0.94);
            display: block;
        }
        .motor-holo-scan {
            position: absolute;
            inset: 0;
            background:
                linear-gradient(120deg, rgba(0, 242, 255, 0.09), rgba(61, 0, 98, 0.08)),
                repeating-linear-gradient(0deg, rgba(0, 242, 255, 0.12) 0px, rgba(0, 242, 255, 0.12) 1px, transparent 1px, transparent 18px);
            pointer-events: none;
        }
        .motor-holo-hud {
            position: absolute;
            left: 10px;
            right: 10px;
            bottom: 10px;
            border: 1px solid rgba(0, 242, 255, 0.35);
            border-radius: 10px;
            background: rgba(2, 12, 20, 0.72);
            backdrop-filter: blur(2px);
            padding: 0.6rem 0.75rem;
        }
        .motor-holo-title {
            color: #7ae8ff;
            font-weight: 700;
            letter-spacing: 0.08em;
            font-size: 0.82rem;
            margin-bottom: 0.3rem;
            text-transform: uppercase;
        }
        .motor-holo-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #dff7ff;
            font-size: 0.92rem;
            border-top: 1px solid rgba(0, 242, 255, 0.12);
            padding-top: 0.22rem;
            margin-top: 0.22rem;
        }
        .motor-holo-line span {
            color: #74d4ec;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.78rem;
        }
        @media (max-width: 768px) {
            .motor-card-btn div[data-testid="stButton"] > button {
                min-height: 220px;
                font-size: 1.02rem;
            }
            .motor-details-shell {
                padding: 12px;
            }
            .motor-holo-img {
                height: 230px;
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
        ("Polos", friendly(pick_value(motor, ALIASES["polos"]))),
        ("Tensao", friendly(pick_value(motor, ALIASES["tensao"]))),
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
                <div class="motor-holo-title">Painel Holografico do Motor</div>
                {lines_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def motor_card(motor: Dict[str, Any], card_id: str, is_expanded: bool) -> bool:
    _inject_styles()

    marca = friendly(pick_value(motor, ALIASES["marca"]))
    modelo = friendly(pick_value(motor, ALIASES["modelo"]))
    potencia = friendly(pick_value(motor, ALIASES["potencia"]))
    rpm = friendly(pick_value(motor, ALIASES["rpm"]))
    amperagem = friendly(pick_value(motor, ALIASES["corrente"]))
    polos = friendly(pick_value(motor, ALIASES["polos"]))
    tipo_fase = _tipo_fase(motor)
    registro = friendly(motor.get("id"))

    if is_empty(modelo):
        modelo = f"Registro #{registro}"

    label = (
        f"{marca} | {modelo}\n"
        f"Potencia/CV: {potencia}    |    RPM: {rpm}\n"
        f"Amperagem: {amperagem}    |    Polos: {polos}    |    Tipo: {tipo_fase}\n"
        f"Registro: {registro}"
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
        tab_geral, tab_bob, tab_mec = st.tabs(["Dados gerais", "Bobinagem", "Mecanica"])

        with tab_geral:
            _render_hologram_panel(motor)
            st.markdown("##### Ligacao tecnica sugerida")
            st.info(obter_configuracoes_ligacao(motor))
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

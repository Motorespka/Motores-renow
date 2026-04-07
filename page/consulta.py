from __future__ import annotations

from typing import Any, Dict, Iterable, List

import streamlit as st

from components.motor_card import motor_card
from services.supabase_data import fetch_motores_cached
from utils.motor_view import ALIASES, friendly, is_empty, normalize_motor_record, pick_value


def _inject_consulta_styles() -> None:
    if st.session_state.get("_consulta_styles_loaded"):
        return

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Rajdhani:wght@500;700&display=swap');
        h1, h2, h3 {
            font-family: "Orbitron", "Rajdhani", "Consolas", monospace !important;
            letter-spacing: 0.04em;
        }
        .stTextInput label, .stSidebar label, .stCaption, .stMarkdown, .stInfo, .stWarning {
            font-family: "Rajdhani", "Consolas", monospace !important;
        }
        .consulta-hud {
            margin: 0.3rem 0 1rem 0;
            border: 1px solid rgba(0, 242, 255, 0.28);
            border-radius: 12px;
            background: linear-gradient(140deg, rgba(6,18,29,0.85), rgba(2,8,15,0.85));
            padding: 0.7rem 0.9rem;
            color: #86d6ed;
            font-family: "Rajdhani", "Consolas", monospace !important;
            letter-spacing: 0.04em;
            box-shadow: inset 0 0 20px rgba(0,242,255,0.08);
        }
        .consulta-wrap {
            max-width: 1060px;
            margin: 0 auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_consulta_styles_loaded"] = True


def _rerun() -> None:
    rerun_fn = getattr(st, "rerun", None)
    if callable(rerun_fn):
        rerun_fn()
        return

    rerun_fn = getattr(st, "experimental_rerun", None)
    if callable(rerun_fn):
        rerun_fn()
        return


def _to_text(value: Any) -> str:
    if is_empty(value):
        return ""
    return str(value).strip()


def _unique_values(rows: Iterable[Dict[str, Any]], aliases: List[str]) -> List[str]:
    values = set()
    for row in rows:
        val = _to_text(pick_value(row, aliases))
        if val:
            values.add(val)
    return sorted(values)


def _search_blob(motor: Dict[str, Any]) -> str:
    return " ".join(
        [
            friendly(pick_value(motor, ALIASES["marca"])),
            friendly(pick_value(motor, ALIASES["modelo"])),
            friendly(pick_value(motor, ALIASES["potencia"])),
            friendly(pick_value(motor, ALIASES["rpm"])),
            friendly(pick_value(motor, ALIASES["corrente"])),
            friendly(pick_value(motor, ALIASES["polos"])),
            friendly(pick_value(motor, ALIASES["fases"])),
            friendly(pick_value(motor, ALIASES["tensao"])),
        ]
    ).lower()


def _motor_card_id(motor: Dict[str, Any], index: int) -> str:
    raw_id = _to_text(motor.get("id"))
    if raw_id:
        return raw_id
    return f"idx-{index}"


def show(supabase):
    _inject_consulta_styles()
    st.markdown('<div class="consulta-wrap">', unsafe_allow_html=True)
    st.title("Central de Motores")
    st.markdown(
        '<div class="consulta-hud">PAINEL TECNICO ONLINE | DADOS SINCRONIZADOS COM SUPABASE</div>',
        unsafe_allow_html=True,
    )
    busca_texto = st.text_input("Pesquisar motor...", placeholder="Pesquisar por marca, modelo, RPM, potencia ou corrente")

    try:
        motores_raw = fetch_motores_cached(supabase)
    except Exception as e:
        st.error(f"Erro ao consultar motores no banco: {e}")
        return

    if not motores_raw:
        st.info("Nenhum motor cadastrado no sistema.")
        return

    motores = [normalize_motor_record(m) for m in motores_raw]
    motores_filtrados = motores

    if busca_texto:
        query = busca_texto.lower().strip()
        motores_filtrados = [m for m in motores_filtrados if query in _search_blob(m)]

    marcas = _unique_values(motores, ALIASES["marca"])
    potencias = _unique_values(motores, ALIASES["potencia"])
    tensoes = _unique_values(motores, ALIASES["tensao"])
    rpms = _unique_values(motores, ALIASES["rpm"])
    polos = _unique_values(motores, ALIASES["polos"])

    st.sidebar.markdown("### Filtros")

    marca_sel = st.sidebar.selectbox("Marca", ["Todas"] + marcas, key="filtro_marca")
    if marca_sel != "Todas":
        motores_filtrados = [m for m in motores_filtrados if _to_text(pick_value(m, ALIASES["marca"])) == marca_sel]

    potencia_sel = st.sidebar.selectbox("Potencia/CV", ["Todas"] + potencias, key="filtro_potencia")
    if potencia_sel != "Todas":
        motores_filtrados = [m for m in motores_filtrados if _to_text(pick_value(m, ALIASES["potencia"])) == potencia_sel]

    tensao_sel = st.sidebar.selectbox("Tensao (V)", ["Todas"] + tensoes, key="filtro_tensao")
    if tensao_sel != "Todas":
        motores_filtrados = [m for m in motores_filtrados if _to_text(pick_value(m, ALIASES["tensao"])) == tensao_sel]

    rpm_sel = st.sidebar.selectbox("RPM", ["Todas"] + rpms, key="filtro_rpm")
    if rpm_sel != "Todas":
        motores_filtrados = [m for m in motores_filtrados if _to_text(pick_value(m, ALIASES["rpm"])) == rpm_sel]

    polos_sel = st.sidebar.selectbox("Polos", ["Todos"] + polos, key="filtro_polos")
    if polos_sel != "Todos":
        motores_filtrados = [m for m in motores_filtrados if _to_text(pick_value(m, ALIASES["polos"])) == polos_sel]

    if st.sidebar.button("Limpar filtros", key="limpar_filtros_btn"):
        for k in ["filtro_marca", "filtro_potencia", "filtro_tensao", "filtro_rpm", "filtro_polos"]:
            st.session_state.pop(k, None)
        _rerun()

    if not motores_filtrados:
        st.info("Nenhum motor encontrado com os filtros aplicados.")
        return

    if "motor_expandido_id" not in st.session_state:
        st.session_state.motor_expandido_id = None

    visible_ids = {_motor_card_id(m, i) for i, m in enumerate(motores_filtrados)}
    if st.session_state.motor_expandido_id not in visible_ids:
        st.session_state.motor_expandido_id = None

    for i, motor in enumerate(motores_filtrados):
        card_id = _motor_card_id(motor, i)
        expanded = st.session_state.motor_expandido_id == card_id
        clicked = motor_card(motor, card_id=card_id, is_expanded=expanded)

        if clicked:
            st.session_state.motor_expandido_id = None if expanded else card_id
            _rerun()

        if expanded:
            c1, _c2 = st.columns([1, 3])
            with c1:
                if st.button("Editar motor", key=f"editar_motor_{card_id}", use_container_width=True):
                    st.session_state.motor_editando = motor
                    st.session_state.pagina = "edit"
                    _rerun()

    st.markdown("</div>", unsafe_allow_html=True)

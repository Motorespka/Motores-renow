from __future__ import annotations

from typing import Any, Dict, Iterable, List

import streamlit as st

from components.motor_card import motor_card
from services.supabase_data import fetch_motores_cached

NOT_INFORMED = "Não informado"


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        v = value.strip().lower()
        return v in {"", "none", "nan", "null"}
    return False


def _to_text(value: Any) -> str:
    if _is_empty(value):
        return ""
    return str(value).strip()


def _friendly(value: Any) -> str:
    if _is_empty(value):
        return NOT_INFORMED
    return str(value).strip()


def _unique_values(rows: Iterable[Dict[str, Any]], keys: List[str]) -> List[str]:
    values = set()
    for row in rows:
        for key in keys:
            val = _to_text(row.get(key))
            if val:
                values.add(val)
                break
    return sorted(values)


def _motor_card_id(motor: Dict[str, Any], index: int) -> str:
    raw_id = _to_text(motor.get("id"))
    if raw_id:
        return raw_id
    return f"idx-{index}"


def show(supabase):
    st.title("Central de Motores")
    busca_texto = st.text_input("Pesquisar motor...", placeholder="Ex: Weg 2cv 4 polos")

    try:
        motores = fetch_motores_cached(supabase)
    except Exception as e:
        st.error(f"Erro ao consultar motores: {e}")
        return

    if not motores:
        st.info("Nenhum motor cadastrado no sistema.")
        return

    motores_filtrados = motores

    if busca_texto:
        query = busca_texto.lower().strip()
        motores_filtrados = [
            m
            for m in motores_filtrados
            if query
            in (
                f"{_friendly(m.get('marca'))} "
                f"{_friendly(m.get('modelo'))} "
                f"{_friendly(m.get('potencia_hp_cv') or m.get('potencia_kw'))}"
            ).lower()
        ]

    marcas = _unique_values(motores, ["marca"])
    potencias = _unique_values(motores, ["potencia_hp_cv", "potencia_kw"])
    tensoes = _unique_values(motores, ["tensao_v"])
    rpms = _unique_values(motores, ["rpm_nominal"])
    polos = _unique_values(motores, ["polos", "numero_polos"])

    st.sidebar.markdown("### Filtros")

    marca_sel = st.sidebar.selectbox("Marca", ["Todas"] + marcas, key="filtro_marca")
    if marca_sel != "Todas":
        motores_filtrados = [m for m in motores_filtrados if _to_text(m.get("marca")) == marca_sel]

    potencia_sel = st.sidebar.selectbox("Potência/CV", ["Todas"] + potencias, key="filtro_potencia")
    if potencia_sel != "Todas":
        motores_filtrados = [
            m
            for m in motores_filtrados
            if _to_text(m.get("potencia_hp_cv") or m.get("potencia_kw")) == potencia_sel
        ]

    tensao_sel = st.sidebar.selectbox("Tensão (V)", ["Todas"] + tensoes, key="filtro_tensao")
    if tensao_sel != "Todas":
        motores_filtrados = [m for m in motores_filtrados if _to_text(m.get("tensao_v")) == tensao_sel]

    rpm_sel = st.sidebar.selectbox("RPM", ["Todas"] + rpms, key="filtro_rpm")
    if rpm_sel != "Todas":
        motores_filtrados = [m for m in motores_filtrados if _to_text(m.get("rpm_nominal")) == rpm_sel]

    polos_sel = st.sidebar.selectbox("Polos", ["Todos"] + polos, key="filtro_polos")
    if polos_sel != "Todos":
        motores_filtrados = [
            m
            for m in motores_filtrados
            if _to_text(m.get("polos") or m.get("numero_polos")) == polos_sel
        ]

    if st.sidebar.button("Limpar filtros", key="limpar_filtros_btn"):
        for k in ["filtro_marca", "filtro_potencia", "filtro_tensao", "filtro_rpm", "filtro_polos"]:
            st.session_state.pop(k, None)
        st.experimental_rerun()

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
            st.experimental_rerun()

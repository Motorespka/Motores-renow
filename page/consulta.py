import streamlit as st

from components.motor_card import motor_card
from services.supabase_data import fetch_motores_cached


def _to_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _unique_values(rows, keys):
    values = set()
    for row in rows:
        for key in keys:
            val = _to_text(row.get(key))
            if val:
                values.add(val)
                break
    return sorted(values)


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
            if query in f"{m.get('marca', '')} {m.get('modelo', '')} {m.get('potencia_hp_cv', '')}".lower()
        ]

    marcas = _unique_values(motores, ["marca"])
    potencias = _unique_values(motores, ["potencia_hp_cv"])
    tensoes = _unique_values(motores, ["tensao_v"])
    rpms = _unique_values(motores, ["rpm_nominal"])
    polos = _unique_values(motores, ["polos", "numero_polos"])

    st.sidebar.markdown("### Filtros")

    marca_sel = st.sidebar.selectbox("Marca", ["Todas"] + marcas, key="filtro_marca")
    if marca_sel != "Todas":
        motores_filtrados = [m for m in motores_filtrados if _to_text(m.get("marca")) == marca_sel]

    potencia_sel = st.sidebar.selectbox("Potencia", ["Todas"] + potencias, key="filtro_potencia")
    if potencia_sel != "Todas":
        motores_filtrados = [m for m in motores_filtrados if _to_text(m.get("potencia_hp_cv")) == potencia_sel]

    tensao_sel = st.sidebar.selectbox("Tensao (V)", ["Todas"] + tensoes, key="filtro_tensao")
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

    cols = st.columns(3)
    for i, motor in enumerate(motores_filtrados):
        with cols[i % 3]:
            motor_card(motor)

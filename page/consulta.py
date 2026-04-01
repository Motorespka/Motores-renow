import streamlit as st
from services.database import listar_motores, excluir_motor

# ===============================
# CAMPOS IMPORTANTES (TOPO)
# ===============================
CAMPOS_PRINCIPAIS = [
    "marca",
    "modelo",
    "potencia",      # CV
    "corrente",      # AMP
    "tensao",
    "polos",
    "rpm",
    "isolacao",
    "amp_teste"
]

# ===============================
# MOSTRAR MOTOR
# ===============================
def mostrar_motor(motor):

    titulo = f"{motor.get('marca','')} {motor.get('modelo','')}".strip()

    if not titulo:
        titulo = f"Motor #{motor['id']}"

    with st.expander(f"🔧 {titulo}", expanded=False):

        # -------- PRINCIPAIS --------
        st.subheader("📌 Informações principais")

        col1, col2, col3, col4 = st.columns(4)

        dados = {
            "Marca": motor.get("marca"),
            "Modelo": motor.get("modelo"),
            "CV": motor.get("potencia"),
            "AMP": motor.get("corrente"),
            "Tensão": motor.get("tensao"),
            "Polos": motor.get("polos"),
            "RPM": motor.get("rpm"),
            "Isol": motor.get("isolacao"),
            "Amp Teste": motor.get("amp_teste")
        }

        for i, (label, valor) in enumerate(dados.items()):
            if valor:
                col = [col1, col2, col3, col4][i % 4]
                with col:
                    st.metric(label=label, value=valor)

        # -------- DETALHES --------
        with st.expander("⬇️ Ver todos os dados"):

            for chave, valor in motor.items():

                if chave in CAMPOS_PRINCIPAIS or chave == "id":
                    continue

                if valor:
                    st.write(f"**{chave.replace('_',' ').capitalize()}:** {valor}")

        # -------- AÇÕES --------
        st.divider()
        col1, col2, col3 = st.columns(3)

        # EDITAR
        with col1:
            if st.button("✏️ Editar", key=f"edit_{motor['id']}"):
                st.session_state["motor_id"] = motor["id"]
                st.session_state["pagina"] = "editar"
                st.rerun()

        # EXCLUIR
        with col2:
            if st.button("🗑️ Excluir", key=f"del_{motor['id']}"):
                excluir_motor(motor["id"])
                st.success("Motor excluído!")
                st.rerun()

        # DUPLICAR
        with col3:
            if st.button("📄 Duplicar", key=f"dup_{motor['id']}"):
                st.session_state["motor_duplicar"] = motor
                st.session_state["pagina"] = "cadastro"
                st.rerun()


# ===============================
# PAGE SHOW
# ===============================
def show():

    st.title("🔎 Consulta de Motores")

    # -------- FILTROS --------
    col1, col2, col3 = st.columns(3)

    with col1:
        busca = st.text_input("🔍 Pesquisa geral")

    with col2:
        filtro_marca = st.text_input("Filtrar por marca")

    with col3:
        filtro_potencia = st.text_input("Filtrar por potência")

    motores = listar_motores()

    # -------- FILTRO --------
    if busca:
        motores = [
            m for m in motores
            if busca.lower() in str(m).lower()
        ]

    if filtro_marca:
        motores = [
            m for m in motores
            if filtro_marca.lower() in str(m.get("marca", "")).lower()
        ]

    if filtro_potencia:
        motores = [
            m for m in motores
            if filtro_potencia.lower() in str(m.get("potencia", "")).lower()
        ]

    # -------- CONTADOR --------
    st.caption(f"📊 {len(motores)} motor(es) encontrado(s)")

    if not motores:
        st.info("Nenhum motor encontrado.")
        return

    # -------- LISTAGEM --------
    for motor in motores:
        mostrar_motor(motor)

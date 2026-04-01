import streamlit as st
from services.database import listar_motores, excluir_motor

# ===============================
# CAMPOS IMPORTANTES (TOPO)
# ===============================
CAMPOS_PRINCIPAIS = [
    "nome",
    "potencia",
    "tensao",
    "rpm",
    "corrente",
    "origem"
]


# ===============================
# MOSTRAR MOTOR
# ===============================
def mostrar_motor(motor):

    titulo = motor.get("nome") or f"Motor #{motor['id']}"

    with st.expander(f"🔧 {titulo}", expanded=False):

        # -------- PRINCIPAIS --------
        st.subheader("📌 Informações principais")

        for campo in CAMPOS_PRINCIPAIS:
            valor = motor.get(campo, "")
            if valor:
                st.write(f"**{campo.capitalize()}:** {valor}")

        # -------- DETALHES --------
        with st.expander("⬇️ Ver todos os dados"):

            for chave, valor in motor.items():

                if chave in CAMPOS_PRINCIPAIS or chave == "id":
                    continue

                if valor:
                    st.write(f"**{chave.capitalize()}:** {valor}")

        # -------- BOTÕES --------
        col1, col2 = st.columns(2)

        # EDITAR
        with col1:
            if st.button("✏️ Editar", key=f"edit_{motor['id']}"):
                st.session_state["motor_editar"] = motor["id"]
                st.session_state["pagina"] = "edit"
                st.rerun()

        # EXCLUIR
        with col2:
            if st.button("🗑️ Excluir", key=f"del_{motor['id']}"):
                excluir_motor(motor["id"])
                st.success("Motor excluído!")
                st.rerun()


# ===============================
# PAGE SHOW
# ===============================
def show():

    st.title("🔎 Consulta de Motores")

    busca = st.text_input("Pesquisar")

    motores = listar_motores()

    if busca:
        motores = [
            m for m in motores
            if busca.lower() in str(m).lower()
        ]

    if not motores:
        st.info("Nenhum motor encontrado.")
        return

    for motor in motores:
        mostrar_motor(motor)

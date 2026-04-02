import streamlit as st
import sqlite3
import os
import importlib

# ------------------------------
# Conexão com banco
# ------------------------------
def get_connection():
    os.makedirs("data", exist_ok=True)
    db_path = "data/calculos.db"
    return sqlite3.connect(db_path)

# ------------------------------
# Cria tabela caso não exista
# ------------------------------
def criar_tabela():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS motores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marca TEXT,
        modelo TEXT,
        fabricante TEXT,
        potencia TEXT,
        tensao TEXT,
        corrente TEXT,
        rpm TEXT,
        frequencia TEXT,
        rendimento TEXT,
        polos TEXT,
        carcaca TEXT,
        montagem TEXT,
        isolacao TEXT,
        ip TEXT,
        regime TEXT,
        fator_servico TEXT,
        temperatura TEXT,
        altitude TEXT,
        rolamento_d TEXT,
        rolamento_t TEXT,
        eixo_diametro TEXT,
        comprimento_eixo TEXT,
        peso TEXT,
        ventilacao TEXT,
        tipo_enrolamento TEXT,
        passo_bobina TEXT,
        numero_ranhuras TEXT,
        fios_paralelos TEXT,
        diametro_fio TEXT,
        tipo_fio TEXT,
        ligacao TEXT,
        esquema TEXT,
        resistencia TEXT,
        diametro_interno TEXT,
        diametro_externo TEXT,
        comprimento_pacote TEXT,
        material_nucleo TEXT,
        tipo_chapa TEXT,
        empilhamento TEXT,
        observacoes TEXT,
        origem_calculo TEXT,
        data_cadastro TEXT
    )
    """)
    conn.commit()
    conn.close()

# ------------------------------
# Operações no banco
# ------------------------------
def listar_motores():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM motores ORDER BY id DESC")
    motores = cursor.fetchall()
    conn.close()
    return motores

def excluir_motor(id_motor):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM motores WHERE id = ?", (id_motor,))
    conn.commit()
    conn.close()

# ------------------------------
# Função principal
# ------------------------------
def show():
    st.title("🔍 Consulta de Motores Cadastrados")

    criar_tabela()

    # Inicializa sessão
    if "motor_editando" not in st.session_state:
        st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state:
        st.session_state.abrir_edit = False

    # Se estiver em modo edição, chama a página edit diretamente
    if st.session_state.abrir_edit and st.session_state.motor_editando:
        edit_module = importlib.import_module("page.edit")
        edit_module.show()
        # Botão para fechar edição
        if st.button("🔙 Fechar Edição"):
            st.session_state.abrir_edit = False
            st.session_state.motor_editando = None
            st.experimental_rerun()
        return

    motores = listar_motores()
    if not motores:
        st.info("Nenhum motor cadastrado ainda.")
        return

    st.subheader("📋 Lista de Motores")

    for m in motores:
        id_motor = m[0]
        marca = m[1]
        modelo = m[2]
        cv_kw = m[4] or "N/A"
        polos = m[10] or "N/A"
        rpm = m[7] or "N/A"
        amp = m[6] or "N/A"
        tensao = m[5] or "N/A"
        data_cadastro = m[-1] or "N/A"

        titulo_expander = (
            f"🆔 ID: {id_motor}     "
            f"⚡ Potência: {cv_kw}     "
            f"🎯 Polos: {polos}     "
            f"🔄 RPM: {rpm}     "
            f"🔌 Amp: {amp}     "
            f"🔋 Tensão: {tensao}     "
            f"🗓️ Cadastrado: {data_cadastro}"
        )

        with st.expander(titulo_expander):
            col1, col2 = st.columns(2)

            # Botão Editar
            with col1:
                if st.button("✏️ Editar", key=f"editar_{id_motor}"):
                    # Seta motor para edição e abre modo edit
                    st.session_state.motor_editando = {i: m[i] for i in range(len(m))}
                    st.session_state.abrir_edit = True
                    st.experimental_rerun()

            # Botão Excluir
            with col2:
                if st.button("🗑️ Excluir", key=f"excluir_{id_motor}"):
                    excluir_motor(id_motor)
                    st.success(f"Motor ID {id_motor} excluído com sucesso.")
                    st.experimental_rerun()

            # Detalhes do motor
            with st.expander("ℹ️ Ver todos os detalhes do motor"):
                st.write(f"Marca: {marca}")
                st.write(f"Modelo: {modelo}")
                st.write(f"Fabricante: {m[3]}")
                st.write(f"Potência: {cv_kw}")
                st.write(f"Tensão: {tensao}")
                st.write(f"Corrente: {amp}")
                st.write(f"RPM: {rpm}")
                st.write(f"Frequência: {m[8]}")
                st.write(f"Rendimento: {m[9]}")

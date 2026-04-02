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

    # Modo edição temporário
    if st.session_state.abrir_edit and st.session_state.motor_editando:
        edit_module = importlib.import_module("page.edit")
        edit_module.show()
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
                    st.session_state.motor_editando = {i: m[i] for i in range(len(m))}
                    st.session_state.abrir_edit = True
                    st.experimental_rerun()

            # Botão Excluir
            with col2:
                if st.button("🗑️ Excluir", key=f"excluir_{id_motor}"):
                    excluir_motor(id_motor)
                    st.success(f"Motor ID {id_motor} excluído com sucesso.")
                    st.experimental_rerun()

            # ------------------------------
            # Dados completos em colunas
            # ------------------------------
            st.markdown("## ⚙️ Cadastro Completo de Motor")

            # 📌 Dados Gerais
            st.markdown("### 📌 Dados Gerais")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"Marca: {m[1]}")
                st.write(f"Modelo: {m[2]}")
                st.write(f"Fabricante: {m[3]}")
                st.write(f"Potência (CV/kW): {m[4]}")
            with c2:
                st.write(f"Tensão (V): {m[5]}")
                st.write(f"Corrente (A): {m[6]}")
                st.write(f"RPM: {m[7]}")
                st.write(f"Frequência (Hz): {m[8]}")
            with c3:
                st.write(f"Rendimento (%): {m[9]}")
                st.write(f"Número de Polos: {m[10]}")
                st.write(f"Carcaça: {m[11]}")
                st.write(f"Tipo de Montagem: {m[12]}")

            # ⚙️ Características Construtivas
            st.markdown("### ⚙️ Características Construtivas")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"Classe de Isolação: {m[13]}")
                st.write(f"Grau de Proteção (IP): {m[14]}")
                st.write(f"Regime de Serviço: {m[15]}")
            with c2:
                st.write(f"Fator de Serviço: {m[16]}")
                st.write(f"Classe de Temperatura: {m[17]}")
                st.write(f"Altitude Máx. de Operação: {m[18]}")
            with c3:
                st.write(f"Rolamento Dianteiro: {m[19]}")
                st.write(f"Rolamento Traseiro: {m[20]}")
                st.write(f"Diâmetro do Eixo (mm): {m[21]}")
                st.write(f"Comprimento do Eixo (mm): {m[22]}")

            # 🔩 Rolamentos e Mecânica
            st.markdown("### 🔩 Rolamentos e Mecânica")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"Peso (kg): {m[23]}")
                st.write(f"Tipo de Ventilação: {m[24]}")
            with c2:
                st.write(f"Tipo de Enrolamento: {m[25]}")
                st.write(f"Passo da Bobina: {m[26]}")
                st.write(f"Número de Ranhuras: {m[27]}")
                st.write(f"Fios em Paralelo: {m[28]}")
                st.write(f"Diâmetro do Fio (mm): {m[29]}")
                st.write(f"Tipo de Fio: {m[30]}")
                st.write(f"Ligação: {m[31]}")
                st.write(f"Esquema de Ligação: {m[32]}")
                st.write(f"Resistência (Ω): {m[33]}")

            # 🧲 Dados do Induzido / Estator
            st.markdown("### 🧲 Dados do Induzido / Estator")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"Diâmetro Interno do Estator (mm): {m[34]}")
                st.write(f"Diâmetro Externo (mm): {m[35]}")
                st.write(f"Comprimento do Pacote (mm): {m[36]}")
            with c2:
                st.write(f"Material do Núcleo: {m[37]}")
                st.write(f"Tipo de Chapa: {m[38]}")
                st.write(f"Empilhamento (mm): {m[39]}")

            # 📝 Informações Adicionais
            st.markdown("### 📝 Informações Adicionais")
            st.write(f"Observações Gerais: {m[40]}")
            st.write(f"Origem do cálculo: {m[41]}")

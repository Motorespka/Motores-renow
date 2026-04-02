import streamlit as st
import sqlite3
import os

# ------------------------------
# Conexão com banco
# ------------------------------
def get_connection():
    os.makedirs("data", exist_ok=True)
    db_path = "data/calculos.db"
    return sqlite3.connect(db_path)

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

    # Inicializa variáveis de sessão
    if "motor_editando" not in st.session_state:
        st.session_state.motor_editando = None
    if "motor_para_excluir" not in st.session_state:
        st.session_state.motor_para_excluir = None

    motores = listar_motores()
    if not motores:
        st.info("Nenhum motor cadastrado ainda.")
        return

    st.subheader("📋 Lista de Motores")

    editar_flag = None
    excluir_flag = None

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

            # ------------------------------
            # Botão editar
            # ------------------------------
            with col1:
                if st.button("✏️ Editar", key=f"editar_{id_motor}"):
                    # Salva o motor na sessão para edição
                    st.session_state.motor_editando = {
                        "id": m[0], "marca": m[1], "modelo": m[2], "fabricante": m[3],
                        "potencia": m[4], "tensao": m[5], "corrente": m[6], "rpm": m[7],
                        "frequencia": m[8], "rendimento": m[9], "polos": m[10],
                        "carcaca": m[11], "montagem": m[12], "isolacao": m[13],
                        "ip": m[14], "regime": m[15], "fator_servico": m[16],
                        "temperatura": m[17], "altitude": m[18], "rolamento_d": m[19],
                        "rolamento_t": m[20], "eixo_diametro": m[21], "comprimento_eixo": m[22],
                        "peso": m[23], "ventilacao": m[24], "tipo_enrolamento": m[25],
                        "passo_bobina": m[26], "numero_ranhuras": m[27], "fios_paralelos": m[28],
                        "diametro_fio": m[29], "tipo_fio": m[30], "ligacao": m[31],
                        "esquema": m[32], "resistencia": m[33], "diametro_interno": m[34],
                        "diametro_externo": m[35], "comprimento_pacote": m[36],
                        "material_nucleo": m[37], "tipo_chapa": m[38], "empilhamento": m[39],
                        "observacoes": m[40], "origem_calculo": m[41]
                    }
                    editar_flag = True  # sinal para rerun

            # ------------------------------
            # Botão excluir
            # ------------------------------
            with col2:
                if st.button("🗑️ Excluir", key=f"excluir_{id_motor}"):
                    excluir_flag = id_motor

            # ------------------------------
            # Detalhes do motor
            # ------------------------------
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

    # ------------------------------
    # Ações fora do loop
    # ------------------------------
    if excluir_flag:
        excluir_motor(excluir_flag)
        st.success(f"Motor ID {excluir_flag} excluído com sucesso.")
        st.experimental_rerun()

    if editar_flag:
        st.session_state.pagina = "edit"  # Muda para página de edição
        st.experimental_rerun()

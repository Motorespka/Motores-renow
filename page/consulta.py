import streamlit as st
import sqlite3
import os

# ===============================
# FUNÇÃO PARA CONECTAR AO BANCO
# ===============================
def get_connection():
    os.makedirs("data", exist_ok=True)
    db_path = "data/calculos.db"
    return sqlite3.connect(db_path)

# ===============================
# FUNÇÃO PARA LISTAR MOTORES
# ===============================
def listar_motores():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM motores ORDER BY id DESC")
    motores = cursor.fetchall()
    conn.close()
    return motores

# ===============================
# FUNÇÃO PARA EXCLUIR MOTOR
# ===============================
def excluir_motor(id_motor):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM motores WHERE id = ?", (id_motor,))
    conn.commit()
    conn.close()

# ===============================
# ABA DE CONSULTA DE MOTORES
# ===============================
def show():
    st.title("🔍 Consulta de Motores Cadastrados")

    # Flag para atualização da lista
    if 'update_list' not in st.session_state:
        st.session_state['update_list'] = False

    # Se botão de excluir foi clicado, processar exclusão
    if st.session_state['update_list']:
        st.experimental_rerun()

    motores = listar_motores()

    if not motores:
        st.info("Nenhum motor cadastrado ainda.")
        return

    st.subheader("📋 Lista de Motores")

    for m in motores:
        id_motor = m[0]
        marca = m[1]
        modelo = m[2]
        cv_kw = m[4] or "N/A"  # Potência
        polos = m[10] or "N/A"  # Polos
        rpm = m[7] or "N/A"
        amp = m[6] or "N/A"  # Corrente
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

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✏️ Editar", key=f"editar_{id_motor}"):
                    # Redireciona para /edit passando o id via query params
                    st.experimental_set_query_params(page="edit", id=id_motor)
                    st.experimental_rerun()
            with col2:
                if st.button("🗑️ Excluir", key=f"excluir_{id_motor}"):
                    if st.confirm(f"Você tem certeza que deseja excluir o motor ID {id_motor}?"):
                        excluir_motor(id_motor)
                        st.success(f"Motor ID {id_motor} excluído com sucesso.")
                        # Atualiza a lista removendo o motor excluído
                        st.session_state['update_list'] = True
                        st.experimental_rerun()

            with st.expander("ℹ️ Ver todos os detalhes do motor"):
                st.markdown("**📌 Dados Gerais**")
                st.write(f"Marca: {marca}")
                st.write(f"Modelo: {modelo}")
                st.write(f"Fabricante: {m[3]}")
                st.write(f"Potência: {cv_kw}")
                st.write(f"Tensão: {tensao}")
                st.write(f"Corrente: {amp}")
                st.write(f"RPM: {rpm}")
                st.write(f"Frequência: {m[8]}")
                st.write(f"Rendimento: {m[9]}")

                st.markdown("**⚙️ Características Construtivas**")
                st.write(f"Número de Polos: {polos}")
                st.write(f"Carcaça: {m[11]}")
                st.write(f"Montagem: {m[12]}")
                st.write(f"Classe de Isolação: {m[13]}")
                st.write(f"Grau de Proteção (IP): {m[14]}")
                st.write(f"Regime de Serviço: {m[15]}")
                st.write(f"Fator de Serviço: {m[16]}")
                st.write(f"Classe de Temperatura: {m[17]}")
                st.write(f"Altitude Máx. de Operação: {m[18]}")

                st.markdown("**🔩 Rolamentos e Mecânica**")
                st.write(f"Rolamento Dianteiro: {m[19]}")
                st.write(f"Rolamento Traseiro: {m[20]}")
                st.write(f"Diâmetro do Eixo: {m[21]}")
                st.write(f"Comprimento do Eixo: {m[22]}")
                st.write(f"Peso: {m[23]}")
                st.write(f"Tipo de Ventilação: {m[24]}")

                st.markdown("**⚡ Dados Elétricos do Enrolamento**")
                st.write(f"Tipo de Enrolamento: {m[25]}")
                st.write(f"Passo da Bobina: {m[26]}")
                st.write(f"Número de Ranhuras: {m[27]}")
                st.write(f"Fios em Paralelo: {m[28]}")
                st.write(f"Diâmetro do Fio: {m[29]}")
                st.write(f"Tipo de Fio: {m[30]}")
                st.write(f"Ligação: {m[31]}")
                st.write(f"Esquema de Ligação: {m[32]}")
                st.write(f"Resistência: {m[33]}")

                st.markdown("**🧲 Dados do Induzido / Estator**")
                st.write(f"Diâmetro Interno: {m[34]}")
                st.write(f"Diâmetro Externo: {m[35]}")
                st.write(f"Comprimento do Pacote: {m[36]}")
                st.write(f"Material do Núcleo: {m[37]}")
                st.write(f"Tipo de Chapa: {m[38]}")
                st.write(f"Empilhamento: {m[39]}")

                st.markdown("**📝 Informações Adicionais**")
                st.write(f"Observações: {m[40]}")
                st.write(f"Origem do Cálculo: {m[41]}")
                st.write(f"Data de Cadastro: {data_cadastro}")

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

    motores = listar_motores()

    if not motores:
        st.info("Nenhum motor cadastrado ainda.")
        return

    st.subheader("📋 Lista de Motores")
    
    for m in motores:
        id_motor = m[0]
        marca = m[1]
        modelo = m[2]
        cv_kw = m[4] or "N/A"        # Potência
        polos = m[10] or "N/A"       # Polos
        rpm = m[7] or "N/A"
        amp = m[6] or "N/A"          # Corrente
        tensao = m[5] or "N/A"
        data_cadastro = m[-1] or "N/A"

        # Expander resumido com informações principais
        titulo_expander = (
            f"🆔 ID: {id_motor}   "
            f"⚡ Potência: {cv_kw}   "
            f"🎯 Polos: {polos}   "
            f"🔄 RPM: {rpm}   "
            f"🔌 Amp: {amp}   "
            f"🔋 Tensão: {tensao}   "
            f"🗓️ Cadastrado: {data_cadastro}"
        )

        with st.expander(titulo_expander):
            
            # Botões Editar e Excluir na mesma linha
            col_edit, col_delete = st.columns(2)
            with col_edit:
                if st.button("✏️ Editar", key=f"editar_{id_motor}"):
                    motor_data = {
                        "id": m[0],
                        "marca": m[1],
                        "modelo": m[2],
                        "fabricante": m[3],
                        "potencia": m[4],
                        "tensao": m[5],
                        "corrente": m[6],
                        "rpm": m[7],
                        "frequencia": m[8],
                        "rendimento": m[9],
                        "polos": m[10],
                        "carcaca": m[11],
                        "montagem": m[12],
                        "isolacao": m[13],
                        "ip": m[14],
                        "regime": m[15],
                        "fator_servico": m[16],
                        "temperatura": m[17],
                        "altitude": m[18],
                        "rolamento_d": m[19],
                        "rolamento_t": m[20],
                        "eixo_diametro": m[21],
                        "comprimento_eixo": m[22],
                        "peso": m[23],
                        "ventilacao": m[24],
                        "tipo_enrolamento": m[25],
                        "passo_bobina": m[26],
                        "numero_ranhuras": m[27],
                        "fios_paralelos": m[28],
                        "diametro_fio": m[29],
                        "tipo_fio": m[30],
                        "ligacao": m[31],
                        "esquema": m[32],
                        "resistencia": m[33],
                        "diametro_interno": m[34],
                        "diametro_externo": m[35],
                        "comprimento_pacote": m[36],
                        "material_nucleo": m[37],
                        "tipo_chapa": m[38],
                        "empilhamento": m[39],
                        "observacoes": m[40],
                        "origem_calculo": m[41],
                    }
                    st.session_state.motor_editando = motor_data
                    st.session_state.pagina = "edit"
                    st.experimental_rerun()

            with col_delete:
                if st.button("🗑️ Excluir", key=f"excluir_{id_motor}"):
                    if st.confirm(f"Confirma exclusão do motor ID {id_motor}?"):
                        excluir_motor(id_motor)
                        st.success(f"Motor ID {id_motor} excluído!")
                        st.experimental_rerun()

            # Segunda expander para detalhes completos
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
                st.write(f"Esquema: {m[32]}")
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

import streamlit as st
import sqlite3
import os
from datetime import datetime

# ===============================
# FUNÇÃO PARA CONECTAR AO BANCO
# ===============================
def get_connection():
    os.makedirs("data", exist_ok=True)
    db_path = "data/calculos.db"
    return sqlite3.connect(db_path)

# ===============================
# FUNÇÃO PARA SALVAR MOTOR
# ===============================
def salvar_motor(motor):
    conn = get_connection()
    cursor = conn.cursor()

    # Criar tabela se não existir
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

    # Adicionar data de cadastro
    motor["data_cadastro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Inserir motor
    cursor.execute("""
    INSERT INTO motores (
        marca, modelo, fabricante, potencia, tensao, corrente, rpm, frequencia, rendimento,
        polos, carcaca, montagem, isolacao, ip, regime, fator_servico, temperatura, altitude,
        rolamento_d, rolamento_t, eixo_diametro, comprimento_eixo, peso, ventilacao,
        tipo_enrolamento, passo_bobina, numero_ranhuras, fios_paralelos, diametro_fio, tipo_fio,
        ligacao, esquema, resistencia, diametro_interno, diametro_externo, comprimento_pacote,
        material_nucleo, tipo_chapa, empilhamento, observacoes, origem_calculo, data_cadastro
    ) VALUES (
        :marca, :modelo, :fabricante, :potencia, :tensao, :corrente, :rpm, :frequencia, :rendimento,
        :polos, :carcaca, :montagem, :isolacao, :ip, :regime, :fator_servico, :temperatura, :altitude,
        :rolamento_d, :rolamento_t, :eixo_diametro, :comprimento_eixo, :peso, :ventilacao,
        :tipo_enrolamento, :passo_bobina, :numero_ranhuras, :fios_paralelos, :diametro_fio, :tipo_fio,
        :ligacao, :esquema, :resistencia, :diametro_interno, :diametro_externo, :comprimento_pacote,
        :material_nucleo, :tipo_chapa, :empilhamento, :observacoes, :origem_calculo, :data_cadastro
    )
    """, motor)

    conn.commit()
    conn.close()

# ===============================
# FUNÇÃO PARA LISTAR MOTORES
# ===============================
def listar_motores():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, marca, modelo, fabricante, data_cadastro FROM motores ORDER BY id DESC")
    motores = cursor.fetchall()
    conn.close()
    return motores

# ===============================
# CADASTRO COMPLETO DE MOTOR NO STREAMLIT
# ===============================
def show():
    st.title("⚙️ Cadastro Completo de Motor")

    with st.form("cadastro_motor"):

        st.subheader("📌 Dados Gerais")
        col1, col2, col3 = st.columns(3)

        with col1:
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            fabricante = st.text_input("Fabricante")

        with col2:
            potencia = st.text_input("Potência (CV/kW)")
            tensao = st.text_input("Tensão (V)")
            corrente = st.text_input("Corrente (A)")

        with col3:
            rpm = st.text_input("RPM")
            frequencia = st.text_input("Frequência (Hz)")
            rendimento = st.text_input("Rendimento (%)")

        st.divider()
        st.subheader("⚙️ Características Construtivas")
        col4, col5, col6 = st.columns(3)

        with col4:
            polos = st.text_input("Número de Polos")
            carcaca = st.text_input("Carcaça")
            montagem = st.text_input("Tipo de Montagem")

        with col5:
            isolacao = st.text_input("Classe de Isolação")
            ip = st.text_input("Grau de Proteção (IP)")
            regime = st.text_input("Regime de Serviço")

        with col6:
            fator_servico = st.text_input("Fator de Serviço")
            temperatura = st.text_input("Classe de Temperatura")
            altitude = st.text_input("Altitude Máx. de Operação")

        st.divider()
        st.subheader("🔩 Rolamentos e Mecânica")
        col7, col8 = st.columns(2)

        with col7:
            rolamento_d = st.text_input("Rolamento Dianteiro")
            eixo_diametro = st.text_input("Diâmetro do Eixo (mm)")
            comprimento_eixo = st.text_input("Comprimento do Eixo (mm)")

        with col8:
            rolamento_t = st.text_input("Rolamento Traseiro")
            peso = st.text_input("Peso (kg)")
            ventilacao = st.text_input("Tipo de Ventilação")

        st.divider()
        st.subheader("⚡ Dados Elétricos do Enrolamento")
        col9, col10, col11 = st.columns(3)

        with col9:
            tipo_enrolamento = st.text_input("Tipo de Enrolamento")
            passo_bobina = st.text_input("Passo da Bobina")
            numero_ranhuras = st.text_input("Número de Ranhuras")

        with col10:
            fios_paralelos = st.text_input("Fios em Paralelo")
            diametro_fio = st.text_input("Diâmetro do Fio (mm)")
            tipo_fio = st.text_input("Tipo de Fio (Esmaltado, etc)")

        with col11:
            ligacao = st.selectbox("Ligação", ["Estrela", "Triângulo", "Série", "Paralelo"])
            esquema = st.text_input("Esquema de Ligação")
            resistencia = st.text_input("Resistência (Ω)")

        st.divider()
        st.subheader("🧲 Dados do Induzido / Estator")
        col12, col13 = st.columns(2)

        with col12:
            diametro_interno = st.text_input("Diâmetro Interno do Estator (mm)")
            diametro_externo = st.text_input("Diâmetro Externo (mm)")
            comprimento_pacote = st.text_input("Comprimento do Pacote (mm)")

        with col13:
            material_nucleo = st.text_input("Material do Núcleo")
            tipo_chapa = st.text_input("Tipo de Chapa")
            empilhamento = st.text_input("Empilhamento (mm)")

        st.divider()
        st.subheader("📝 Informações Adicionais")
        observacoes = st.text_area("Observações Gerais")

        origem = st.selectbox(
            "Origem do cálculo",
            ["União", "Rebobinador", "Próprio"]
        )

        salvar = st.form_submit_button("💾 Salvar Motor")

    if salvar:
        motor = {
            "marca": marca,
            "modelo": modelo,
            "fabricante": fabricante,
            "potencia": potencia,
            "tensao": tensao,
            "corrente": corrente,
            "rpm": rpm,
            "frequencia": frequencia,
            "rendimento": rendimento,
            "polos": polos,
            "carcaca": carcaca,
            "montagem": montagem,
            "isolacao": isolacao,
            "ip": ip,
            "regime": regime,
            "fator_servico": fator_servico,
            "temperatura": temperatura,
            "altitude": altitude,
            "rolamento_d": rolamento_d,
            "rolamento_t": rolamento_t,
            "eixo_diametro": eixo_diametro,
            "comprimento_eixo": comprimento_eixo,
            "peso": peso,
            "ventilacao": ventilacao,
            "tipo_enrolamento": tipo_enrolamento,
            "passo_bobina": passo_bobina,
            "numero_ranhuras": numero_ranhuras,
            "fios_paralelos": fios_paralelos,
            "diametro_fio": diametro_fio,
            "tipo_fio": tipo_fio,
            "ligacao": ligacao,
            "esquema": esquema,
            "resistencia": resistencia,
            "diametro_interno": diametro_interno,
            "diametro_externo": diametro_externo,
            "comprimento_pacote": comprimento_pacote,
            "material_nucleo": material_nucleo,
            "tipo_chapa": tipo_chapa,
            "empilhamento": empilhamento,
            "observacoes": observacoes,
            "origem_calculo": origem
        }

        salvar_motor(motor)
        st.success("✅ Motor salvo com sucesso em data/calculos.db!")

    # ===============================
    # MOSTRAR MOTORES CADASTRADOS
    # ===============================
    st.divider()
    st.subheader("📋 Motores Cadastrados")
    motores = listar_motores()
    if motores:
        for m in motores:
            st.write(f"ID {m[0]} | Marca: {m[1]} | Modelo: {m[2]} | Fabricante: {m[3]} | Cadastrado em: {m[4]}")
    else:
        st.info("Nenhum motor cadastrado ainda.")
        

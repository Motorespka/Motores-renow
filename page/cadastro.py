import streamlit as st
from services.database import salvar_motor

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

        st.success("✅ Motor salvo com sucesso!")

import streamlit as st
from services.database import atualizar_motor

def show():

    motor = st.session_state.motor_editando

    st.title("✏️ Editar Motor")

    with st.form("editar_motor"):

        st.subheader("📌 Dados Gerais")
        col1, col2, col3 = st.columns(3)

        with col1:
            marca = st.text_input("Marca", motor.get("marca",""))
            modelo = st.text_input("Modelo", motor.get("modelo",""))
            fabricante = st.text_input("Fabricante", motor.get("fabricante",""))

        with col2:
            potencia = st.text_input("Potência (CV/kW)", motor.get("potencia",""))
            tensao = st.text_input("Tensão (V)", motor.get("tensao",""))
            corrente = st.text_input("Corrente (A)", motor.get("corrente",""))

        with col3:
            rpm = st.text_input("RPM", motor.get("rpm",""))
            frequencia = st.text_input("Frequência (Hz)", motor.get("frequencia",""))
            rendimento = st.text_input("Rendimento (%)", motor.get("rendimento",""))

        st.divider()

        st.subheader("⚙️ Características Construtivas")
        col4, col5, col6 = st.columns(3)

        with col4:
            polos = st.text_input("Número de Polos", motor.get("polos",""))
            carcaca = st.text_input("Carcaça", motor.get("carcaca",""))
            montagem = st.text_input("Tipo de Montagem", motor.get("montagem",""))

        with col5:
            isolacao = st.text_input("Classe de Isolação", motor.get("isolacao",""))
            ip = st.text_input("Grau de Proteção (IP)", motor.get("ip",""))
            regime = st.text_input("Regime de Serviço", motor.get("regime",""))

        with col6:
            fator_servico = st.text_input("Fator de Serviço", motor.get("fator_servico",""))
            temperatura = st.text_input("Classe de Temperatura", motor.get("temperatura",""))
            altitude = st.text_input("Altitude Máx.", motor.get("altitude",""))

        st.divider()

        st.subheader("🔩 Rolamentos e Mecânica")
        col7, col8 = st.columns(2)

        with col7:
            rolamento_d = st.text_input("Rolamento Dianteiro", motor.get("rolamento_d",""))
            eixo_diametro = st.text_input("Diâmetro do Eixo", motor.get("eixo_diametro",""))
            comprimento_eixo = st.text_input("Comprimento do Eixo", motor.get("comprimento_eixo",""))

        with col8:
            rolamento_t = st.text_input("Rolamento Traseiro", motor.get("rolamento_t",""))
            peso = st.text_input("Peso", motor.get("peso",""))
            ventilacao = st.text_input("Ventilação", motor.get("ventilacao",""))

        st.divider()

        st.subheader("⚡ Enrolamento")
        col9, col10, col11 = st.columns(3)

        with col9:
            tipo_enrolamento = st.text_input("Tipo de Enrolamento", motor.get("tipo_enrolamento",""))
            passo_bobina = st.text_input("Passo da Bobina", motor.get("passo_bobina",""))
            numero_ranhuras = st.text_input("Ranhuras", motor.get("numero_ranhuras",""))

        with col10:
            fios_paralelos = st.text_input("Fios em Paralelo", motor.get("fios_paralelos",""))
            diametro_fio = st.text_input("Diâmetro do Fio", motor.get("diametro_fio",""))
            tipo_fio = st.text_input("Tipo de Fio", motor.get("tipo_fio",""))

        with col11:
            ligacao = st.selectbox(
                "Ligação",
                ["Estrela", "Triângulo", "Série", "Paralelo"],
                index=["Estrela", "Triângulo", "Série", "Paralelo"].index(
                    motor.get("ligacao","Estrela")
                ) if motor.get("ligacao") in ["Estrela", "Triângulo", "Série", "Paralelo"] else 0
            )
            esquema = st.text_input("Esquema", motor.get("esquema",""))
            resistencia = st.text_input("Resistência", motor.get("resistencia",""))

        st.divider()

        st.subheader("🧲 Estator / Núcleo")
        col12, col13 = st.columns(2)

        with col12:
            diametro_interno = st.text_input("Diâmetro Interno", motor.get("diametro_interno",""))
            diametro_externo = st.text_input("Diâmetro Externo", motor.get("diametro_externo",""))
            comprimento_pacote = st.text_input("Comprimento Pacote", motor.get("comprimento_pacote",""))

        with col13:
            material_nucleo = st.text_input("Material Núcleo", motor.get("material_nucleo",""))
            tipo_chapa = st.text_input("Tipo de Chapa", motor.get("tipo_chapa",""))
            empilhamento = st.text_input("Empilhamento", motor.get("empilhamento",""))

        st.divider()

        st.subheader("📝 Observações")
        observacoes = st.text_area("Observações", motor.get("observacoes",""))

        origem = st.selectbox(
            "Origem",
            ["União","Rebobinador","Próprio"],
            index=["União","Rebobinador","Próprio"].index(
                motor.get("origem_calculo","Próprio")
            )
        )

        salvar = st.form_submit_button("💾 Salvar Alterações")
        fechar = st.form_submit_button("❌ Cancelar")

    if salvar:

        motor.update({
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
        })

        atualizar_motor(motor["id"], motor)

        st.success("✅ Motor atualizado com sucesso!")
        st.session_state.pagina = "consulta"
        st.rerun()

    if fechar:
        st.session_state.pagina = "consulta"
        st.rerun()

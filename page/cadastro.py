import streamlit as st
from services.database import salvar_motor


def show():

    st.title("⚙️ Cadastro Completo de Motor")

    with st.form("cadastro_motor"):

        # ================= IDENTIFICAÇÃO =================
        st.subheader("🔎 Identificação")

        col1, col2, col3 = st.columns(3)

        with col1:
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            numero_serie = st.text_input("Número de Série")

        with col2:
            cliente = st.text_input("Cliente")
            equipamento = st.text_input("Equipamento")
            data_entrada = st.date_input("Data Entrada")

        with col3:
            tecnico = st.text_input("Técnico Responsável")
            ordem_servico = st.text_input("Ordem de Serviço")

        # ================= DADOS ELÉTRICOS =================
        st.subheader("⚡ Dados Elétricos")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            potencia = st.text_input("Potência (CV/kW)")
            tensao = st.text_input("Tensão")
            corrente = st.text_input("Corrente")

        with c2:
            frequencia = st.text_input("Frequência")
            rpm = st.text_input("RPM")
            polos = st.text_input("Polos")

        with c3:
            fp = st.text_input("Fator de Potência")
            rendimento = st.text_input("Rendimento (%)")
            fs = st.text_input("Fator Serviço")

        with c4:
            regime = st.text_input("Regime")
            ligacao = st.text_input("Ligação")
            classe_isolacao = st.text_input("Classe Isolação")

        # ================= CONSTRUÇÃO =================
        st.subheader("🏭 Construção")

        c1, c2, c3 = st.columns(3)

        with c1:
            carcaca = st.text_input("Carcaça")
            ip = st.text_input("Grau IP")
            peso = st.text_input("Peso")

        with c2:
            rol_dianteiro = st.text_input("Rolamento Dianteiro")
            rol_traseiro = st.text_input("Rolamento Traseiro")

        with c3:
            diametro_eixo = st.text_input("Diâmetro Eixo")
            comprimento_pacote = st.text_input("Comprimento Pacote")
            numero_ranhuras = st.text_input("Número Ranhuras")

        # ================= REBOBINAGEM =================
        st.subheader("🧵 Dados de Rebobinagem")

        c1, c2 = st.columns(2)

        with c1:
            passo_principal = st.text_input("Passo Principal")
            espiras_principal = st.text_input("Espiras Principal")
            fio_principal = st.text_input("Fio Principal")
            paralelo_principal = st.text_input("Paralelos Principal")

        with c2:
            passo_aux = st.text_input("Passo Auxiliar")
            espiras_aux = st.text_input("Espiras Auxiliar")
            fio_aux = st.text_input("Fio Auxiliar")
            paralelo_aux = st.text_input("Paralelos Auxiliar")

        esquema = st.text_area("Esquema de Ligação / Observações Técnicas")

        # ================= DIAGNÓSTICO =================
        st.subheader("🩺 Diagnóstico")

        defeito = st.text_area("Defeito Encontrado")
        servico_realizado = st.text_area("Serviço Realizado")

        observacoes = st.text_area("Observações Gerais")

        # ================= SALVAR =================
        salvar = st.form_submit_button("💾 Salvar Motor")

        if salvar:

            motor = {
                "marca": marca,
                "modelo": modelo,
                "numero_serie": numero_serie,
                "cliente": cliente,
                "equipamento": equipamento,
                "data_entrada": str(data_entrada),
                "tecnico": tecnico,
                "ordem_servico": ordem_servico,

                "potencia": potencia,
                "tensao": tensao,
                "corrente": corrente,
                "frequencia": frequencia,
                "rpm": rpm,
                "polos": polos,
                "fp": fp,
                "rendimento": rendimento,
                "fs": fs,
                "regime": regime,
                "ligacao": ligacao,
                "classe_isolacao": classe_isolacao,

                "carcaca": carcaca,
                "ip": ip,
                "peso": peso,
                "rol_dianteiro": rol_dianteiro,
                "rol_traseiro": rol_traseiro,
                "diametro_eixo": diametro_eixo,
                "comprimento_pacote": comprimento_pacote,
                "numero_ranhuras": numero_ranhuras,

                "passo_principal": passo_principal,
                "espiras_principal": espiras_principal,
                "fio_principal": fio_principal,
                "paralelo_principal": paralelo_principal,

                "passo_aux": passo_aux,
                "espiras_aux": espiras_aux,
                "fio_aux": fio_aux,
                "paralelo_aux": paralelo_aux,

                "esquema": esquema,
                "defeito": defeito,
                "servico_realizado": servico_realizado,
                "observacoes": observacoes,
            }

            salvar_motor(motor)

            st.success("✅ Motor cadastrado com sucesso!")

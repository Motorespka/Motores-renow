import streamlit as st

from services.supabase_database import salvar_motor_supabase


def show(supabase):
    st.title("⚙️ Cadastro de Motores - Moto-Renow")
    st.markdown("---")

    with st.form("cadastro_motor", clear_on_submit=True):
        # =========================
        # CARD 1: IDENTIFICAÇÃO
        # =========================
        st.markdown('<div class="motor-card">', unsafe_allow_html=True)
        st.markdown("#### 📌 Identificação e Placa")

        marca = st.text_input("Marca", help="Ex: WEG, Voges, Eberle")
        modelo = st.text_input("Modelo")
        fabricante = st.text_input("Fabricante")

        st.divider()

        potencia = st.text_input("Potência (CV/kW)")
        tensao = st.text_input("Tensão (V)")
        corrente = st.text_input("Corrente (A)")

        st.divider()

        rpm = st.text_input("RPM")
        frequencia = st.text_input("Frequência (Hz)")
        rendimento = st.text_input("Rendimento (%)")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # =========================
        # CARD 2: MECÂNICA
        # =========================
        st.markdown('<div class="motor-card">', unsafe_allow_html=True)
        st.markdown("#### 🛠️ Mecânica")

        polos = st.text_input("Pólos")
        carcaca = st.text_input("Carcaça")
        montagem = st.text_input("Montagem")

        st.divider()

        isolacao = st.text_input("Isolação")
        ip = st.text_input("Grau Proteção (IP)")
        regime = st.text_input("Regime")

        st.divider()

        fator_servico = st.text_input("Fator de Serviço")
        peso = st.text_input("Peso (kg)")
        ventilacao = st.text_input("Ventilação")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # =========================
        # CARD 3: BOBINAGEM
        # =========================
        st.markdown('<div class="motor-card">', unsafe_allow_html=True)
        st.markdown("#### 🌀 Bobinagem")

        st.markdown("**Enrolamento Principal**")
        passo_principal = st.text_input("Passo Principal")
        fio_principal = st.text_input("Fio Principal")
        espira_principal = st.text_input("Espiras Principal")

        st.divider()

        st.markdown("**Enrolamento Auxiliar**")
        passo_auxiliar = st.text_input("Passo Auxiliar")
        fio_auxiliar = st.text_input("Fio Auxiliar")
        espira_auxiliar = st.text_input("Espiras Auxiliar")

        st.divider()

        st.markdown("#### ⚡ Dados Elétricos e Núcleo")
        tipo_enrolamento = st.text_input("Tipo Enrolamento")
        numero_ranhuras = st.text_input("Nº Ranhuras")
        resistencia = st.text_input("Resistência (Ω)")

        st.divider()

        diametro_fio = st.text_input("Diâmetro Fio (mm)")
        tipo_fio = st.text_input("Tipo de Fio")
        ligacao = st.selectbox("Ligação", ["Estrela", "Triângulo", "Série", "Paralelo"])

        st.divider()

        diametro_interno = st.text_input("Ø Interno (mm)")
        comprimento_pacote = st.text_input("Comp. Pacote (mm)")
        empilhamento = st.text_input("Empilhamento (mm)")

        st.divider()

        st.markdown("#### 📝 Observações")
        observacoes = st.text_area("Notas técnicas adicionais")

        st.markdown("#### 📍 Origem do Cálculo")
        origem = st.selectbox("Origem do Cálculo", ["União", "Rebobinador", "Próprio"])

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        salvar = st.form_submit_button("💾 SALVAR NO BANCO DE DADOS", use_container_width=True)

    if salvar:
        # Mapeamento do Dicionário respeitando o seu schema atual
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
            "peso": peso,
            "ventilacao": ventilacao,
            # Salvando nos dois nomes de campos (OCR e Manual) para garantir compatibilidade
            "passo_principal": passo_principal,
            "passo_princ": passo_principal,
            "fio_principal": fio_principal,
            "fio_princ": fio_principal,
            "espira_principal": espira_principal,
            "espiras_princ": espira_principal,
            "passo_auxiliar": passo_auxiliar,
            "passo_aux": passo_auxiliar,
            "fio_auxiliar": fio_auxiliar,
            "fio_aux": fio_auxiliar,
            "espira_auxiliar": espira_auxiliar,
            "espiras_aux": espira_auxiliar,
            # Restante dos dados técnicos
            "tipo_enrolamento": tipo_enrolamento,
            "numero_ranhuras": numero_ranhuras,
            "resistencia": resistencia,
            "diametro_fio": diametro_fio,
            "tipo_fio": tipo_fio,
            "ligacao": ligacao,
            "diametro_interno": diametro_interno,
            "comprimento_pacote": comprimento_pacote,
            "empilhamento": empilhamento,
            "observacoes": observacoes,
            "origem_calculo": origem,
        }

        sucesso, mensagem = salvar_motor_supabase(supabase, motor)
        if sucesso:
            st.success(mensagem)
            st.balloons()
        else:
            st.error(mensagem)

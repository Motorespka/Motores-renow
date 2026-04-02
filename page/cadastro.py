import streamlit as st
from datetime import datetime

# ===============================
# FUNÇÃO PARA SALVAR NO SUPABASE
# ===============================
def salvar_motor_supabase(supabase, motor):
    try:
        motor["data_cadastro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res = supabase.table("motores").insert(motor).execute()
        
        if res.data:
            return True, "✅ Motor salvo com sucesso no Supabase!"
        else:
            return False, f"⚠️ O banco não retornou confirmação: {res}"
            
    except Exception as e:
        return False, f"❌ Erro ao salvar no Supabase: {str(e)}"

# ===============================
# CADASTRO COMPLETO DE MOTOR
# ===============================
def show(supabase):
    st.title("⚙️ Cadastro de Motores - Moto-Renow")
    st.markdown("---")

    with st.form("cadastro_motor", clear_on_submit=True):
        
        # --- SEÇÃO 1: IDENTIFICAÇÃO ---
        st.subheader("📌 Identificação e Placa")
        col1, col2, col3 = st.columns(3)
        with col1:
            marca = st.text_input("Marca", help="Ex: WEG, Voges, Eberle")
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

        # --- SEÇÃO 2: CONSTRUÇÃO E MECÂNICA ---
        st.subheader("🛠️ Construção e Mecânica")
        col4, col5, col6 = st.columns(3)
        with col4:
            polos = st.text_input("Pólos")
            carcaca = st.text_input("Carcaça")
            montagem = st.text_input("Montagem")
        with col5:
            isolacao = st.text_input("Isolação")
            ip = st.text_input("Grau Proteção (IP)")
            regime = st.text_input("Regime")
        with col6:
            fator_servico = st.text_input("Fator de Serviço")
            peso = st.text_input("Peso (kg)")
            ventilacao = st.text_input("Ventilação")

        st.divider()

        # --- SEÇÃO 3: DETALHES DE BOBINAGEM (NOVA!) ---
        st.subheader("🌀 Detalhes do Enrolamento (Bobinagem)")
        
        col_princ, col_aux = st.columns(2)
        
        with col_princ:
            st.markdown("**Enrolamento Principal**")
            passo_principal = st.text_input("Passo Principal")
            fio_principal = st.text_input("Fio Principal")
            espira_principal = st.text_input("Espiras Principal")

        with col_aux:
            st.markdown("**Enrolamento Auxiliar**")
            passo_auxiliar = st.text_input("Passo Auxiliar")
            fio_auxiliar = st.text_input("Fio Auxiliar")
            espira_auxiliar = st.text_input("Espiras Auxiliar")

        st.divider()

        # --- SEÇÃO 4: DADOS TÉCNICOS ADICIONAIS ---
        st.subheader("⚡ Dados Elétricos e Núcleo")
        c1, c2, c3 = st.columns(3)
        with c1:
            tipo_enrolamento = st.text_input("Tipo Enrolamento")
            numero_ranhuras = st.text_input("Nº Ranhuras")
            resistencia = st.text_input("Resistência (Ω)")
        with c2:
            diametro_fio = st.text_input("Diâmetro Fio (mm)")
            tipo_fio = st.text_input("Tipo de Fio")
            ligacao = st.selectbox("Ligação", ["Estrela", "Triângulo", "Série", "Paralelo"])
        with c3:
            diametro_interno = st.text_input("Ø Interno (mm)")
            comprimento_pacote = st.text_input("Comp. Pacote (mm)")
            empilhamento = st.text_input("Empilhamento (mm)")

        st.divider()

        # --- SEÇÃO 5: FINALIZAÇÃO ---
        st.subheader("📝 Observações")
        observacoes = st.text_area("Notas técnicas adicionais")
        
        col_fim1, col_fim2 = st.columns(2)
        with col_fim1:
            origem = st.selectbox("Origem do Cálculo", ["União", "Rebobinador", "Próprio"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        salvar = st.form_submit_button("💾 SALVAR NO BANCO DE DADOS", use_container_width=True)

    if salvar:
        # Dicionário mapeado para o Supabase
        motor = {
            "marca": marca, "modelo": modelo, "fabricante": fabricante,
            "potencia": potencia, "tensao": tensao, "corrente": corrente,
            "rpm": rpm, "frequencia": frequencia, "rendimento": rendimento,
            "polos": polos, "carcaca": carcaca, "montagem": montagem,
            "isolacao": isolacao, "ip": ip, "regime": regime,
            "fator_servico": fator_servico, "peso": peso, "ventilacao": ventilacao,
            # Novos campos de bobinagem
            "passo_principal": passo_principal,
            "fio_principal": fio_principal,
            "espira_principal": espira_principal,
            "passo_auxiliar": passo_auxiliar,
            "fio_auxiliar": fio_auxiliar,
            "espira_auxiliar": espira_auxiliar,
            # Restante dos dados
            "tipo_enrolamento": tipo_enrolamento, "numero_ranhuras": numero_ranhuras,
            "resistencia": resistencia, "diametro_fio": diametro_fio,
            "tipo_fio": tipo_fio, "ligacao": ligacao,
            "diametro_interno": diametro_interno, "comprimento_pacote": comprimento_pacote,
            "empilhamento": empilhamento, "observacoes": observacoes,
            "origem_calculo": origem
        }

        sucesso, mensagem = salvar_motor_supabase(supabase, motor)
        if sucesso:
            st.success(mensagem)
            st.balloons()
        else:
            st.error(mensagem)

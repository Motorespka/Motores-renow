import streamlit as st
from datetime import datetime
from pathlib import Path

# --- PROTEÇÃO DE IMPORTAÇÃO ---
try:
    from core.calculadora import alertas_validacao_projeto, sugerir_equivalentes_paralelos
    from services.supabase_data import clear_motores_cache
except ImportError as e:
    st.error(f"⚠️ Erro de estrutura: Não encontrei o arquivo ou pasta: {e.name}")
    st.info("Verifique se as pastas 'core' e 'services' possuem o arquivo __init__.py vazio.")
    # Funções de "estepe" para o código não travar se os arquivos acima faltarem
    def alertas_validacao_projeto(m): return []
    def sugerir_equivalentes_paralelos(t): return []
    def clear_motores_cache(): pass

def _load_css() -> None:
    css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

def salvar_motor_supabase(supabase, motor):
    try:
        motor["data_cadastro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res = supabase.table("motores").insert(motor).execute()
        if res.data:
            return True, "✅ Motor salvo com sucesso no Supabase!"
        return False, f"⚠️ Erro ao salvar: {res}"
    except Exception as e:
        return False, f"❌ Erro de conexão: {str(e)}"

def show(supabase):
    _load_css()
    st.title("⚙️ Cadastro de Motores - Moto-Renow")
    st.markdown("---")

    # Tabela de Cores para consulta rápida (ajuda para o seu pai)
    TABELA_CORES = {
        "Azul": "1", "Branco": "2", "Laranja": "3", 
        "Amarelo": "4", "Preto": "5", "Vermelho": "6",
        "Verde": "Terra"
    }

    with st.form("cadastro_motor", clear_on_submit=True):
        # --- SEÇÃO 1: PLACA ---
        with st.expander("📌 Identificação e Placa", expanded=True):
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

        # --- SEÇÃO 2: MECÂNICA ---
        with st.expander("🛠️ Dados mecânicos", expanded=False):
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

        # --- SEÇÃO 3: BOBINAGEM ---
        with st.expander("🌀 Dados de bobinagem e núcleo", expanded=False):
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
            c1, c2, c3 = st.columns(3)
            with c1:
                tipo_enrolamento = st.text_input("Tipo Enrolamento")
                numero_ranhuras = st.text_input("Nº Ranhuras")
            with c2:
                diametro_fio = st.text_input("Diâmetro Fio (mm)")
                ligacao = st.selectbox("Ligação", ["Estrela", "Triângulo", "Série", "Paralelo"])
            with c3:
                diametro_interno = st.text_input("Ø Interno (mm)")
                comprimento_pacote = st.text_input("Comp. Pacote (mm)")

        # --- NOVA SEÇÃO: GUIA DE LIGAÇÃO (CORES E ESQUEMA) ---
        with st.expander("⚡ Esquema de Ligação e Cores", expanded=True):
            st.info("Consulte as cores abaixo para preencher o esquema se os fios não tiverem números.")
            
            # Tradutor visual de cores para o seu pai
            cols_cores = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                cols_cores[i].metric(label=cor, value=num)
            
            st.divider()
            esquema = st.text_area(
                "Esquema de Ligação", 
                placeholder="Ex: 110V: (1,3,5) e (2,4,6) | 220V: 1-(2,3,5)-4,6\nCores: 1-Az, 2-Br, 3-La, 4-Am, 5-Pr, 6-Vm"
            )

        origem = st.selectbox("Origem do Cálculo", ["União", "Rebobinador", "Próprio"])
        observacoes = st.text_area("Observações")
        
        salvar = st.form_submit_button("💾 SALVAR NO BANCO DE DADOS", use_container_width=True)

    if salvar:
        motor = {
            "marca": marca, "modelo": modelo, "fabricante": fabricante,
            "potencia": potencia, "tensao": tensao, "corrente": corrente,
            "rpm": rpm, "frequencia": frequencia, "rendimento": rendimento,
            "polos": polos, "carcaca": carcaca, "montagem": montagem,
            "isolacao": isolacao, "ip": ip, "regime": regime,
            "fator_servico": fator_servico, "peso": peso, "ventilacao": ventilacao,
            "passo_principal": passo_principal, "passo_princ": passo_principal,
            "fio_principal": fio_principal, "fio_princ": fio_principal,
            "espira_principal": espira_principal, "espiras_princ": espira_principal,
            "passo_auxiliar": passo_auxiliar, "fio_auxiliar": fio_auxiliar,
            "espira_auxiliar": espira_auxiliar, "tipo_enrolamento": tipo_enrolamento,
            "numero_ranhuras": numero_ranhuras, "ligacao": ligacao,
            "diametro_interno": diametro_interno, "comprimento_pacote": comprimento_pacote,
            "esquema": esquema, # ADICIONADO AO DICIONÁRIO
            "observacoes": observacoes, "origem_calculo": origem
        }

        # Rodar lógica da calculadora (se os arquivos existirem)
        for msg in alertas_validacao_projeto(motor):
            st.warning(msg)

        sucesso, mensagem = salvar_motor_supabase(supabase, motor)
        if sucesso:
            clear_motores_cache()
            st.success(mensagem)
            st.balloons()
        else:
            st.error(mensagem)

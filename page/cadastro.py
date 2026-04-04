import streamlit as st
from datetime import datetime
from pathlib import Path
import sys
import os

# --- CONFIGURAÇÃO DE CAMINHO DO SISTEMA (REFORÇADO) ---
file_path = Path(__file__).resolve()
root_path = file_path.parents[1] 

if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# --- PROTEÇÃO DE IMPORTAÇÃO ---
try:
    from core.calculadora import alertas_validacao_projeto, sugerir_equivalentes_paralelos
    from services.supabase_data import clear_motores_cache
except ImportError as e:
    st.error(f"⚠️ Erro de estrutura: Não encontrei o módulo: {e.name}")
    st.info("Certifique-se de que está rodando o app a partir da raiz do projeto.")
    def alertas_validacao_projeto(m): return []
    def sugerir_equivalentes_paralelos(t): return []
    def clear_motores_cache(): pass

def _load_css() -> None:
    css_path = root_path / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

def salvar_motor_supabase(supabase, motor):
    try:
        # data_cadastro agora usa o formato ISO que o Supabase prefere para timestamptz
        motor["data_cadastro"] = datetime.now().isoformat()
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

    TABELA_CORES = {
        "Azul": "1", "Branco": "2", "Laranja": "3", 
        "Amarelo": "4", "Preto": "5", "Vermelho": "6",
        "Verde": "Terra"
    }

    with st.form("cadastro_motor", clear_on_submit=False):
        # --- SEÇÃO 1: PLACA ---
        with st.expander("📌 Identificação e Placa", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                marca = st.text_input("Marca")
                modelo = st.text_input("Modelo")
                fabricante = st.text_input("Fabricante")
                num_serie = st.text_input("Nº de Série") # Adicionado para bater com o banco
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
                norma = st.text_input("Norma", value="ABNT/IEC")
            with col5:
                isolacao = st.text_input("Classe Isolação", value="F")
                ip = st.text_input("Grau Proteção (IP)", value="IP55")
                regime = st.text_input("Regime", value="S1")
            with col6:
                fator_servico = st.text_input("Fator de Serviço", value="1.0")
                peso = st.text_input("Peso Total (kg)")
                tipo_graxa = st.text_input("Tipo de Graxa")

        # --- SEÇÃO 3: BOBINAGEM ---
        with st.expander("🌀 Dados de bobinagem e núcleo", expanded=False):
            col_princ, col_aux = st.columns(2)
            with col_princ:
                st.markdown("**Enrolamento Principal**")
                passo_principal = st.text_input("Passo Principal")
                fio_principal = st.text_input("Bitola Fio Principal")
                espira_principal = st.text_input("Espiras Principal")
            with col_aux:
                st.markdown("**Enrolamento Auxiliar**")
                passo_auxiliar = st.text_input("Passo Auxiliar")
                fio_auxiliar = st.text_input("Bitola Fio Auxiliar")
                espira_auxiliar = st.text_input("Espiras Auxiliar")
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            with c1:
                tipo_enrolamento = st.text_input("Tipo Enrolamento")
                numero_ranhuras = st.text_input("Nº Ranhuras")
                fios_paralelos = st.text_input("Fios em Paralelo") # Novo campo para bater com erro corrigido
            with c2:
                ligacao_interna = st.text_input("Ligação Interna")
                ligacao = st.selectbox("Ligação Placa", ["Estrela", "Triângulo", "Série", "Paralelo"])
            with c3:
                diametro_interno = st.text_input("Ø Interno Estator (mm)")
                comprimento_pacote = st.text_input("Comp. Pacote (mm)")

        # --- NOVA SEÇÃO: GUIA DE LIGAÇÃO ---
        with st.expander("⚡ Esquema de Ligação e Cores", expanded=True):
            st.info("Consulte as cores abaixo para preencher o esquema se os fios não tiverem números.")
            cols_cores = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                cols_cores[i].metric(label=cor, value=num)
            
            st.divider()
            esquema = st.text_area(
                "Esquema de Ligação", 
                placeholder="Ex: 110V: (1,3,5) e (2,4,6) | Cores: 1-Az, 2-Br..."
            )

        origem = st.selectbox("Origem do Registro", ["União", "Rebobinador", "OCR", "Manual"])
        observacoes = st.text_area("Observações")
        
        # --- CÁLCULO DE FIOS EM PARALELO ---
        with st.expander("⚖️ Equivalência de Fios (Cálculo Rápido)"):
            fio_alvo = st.text_input("Se não tiver o fio original, digite o AWG aqui:")
            if fio_alvo:
                sugestoes = sugerir_equivalentes_paralelos(fio_alvo)
                st.write(f"Opções para substituir o fio {fio_alvo}:", sugestoes)

        salvar = st.form_submit_button("💾 SALVAR NO BANCO DE DADOS", use_container_width=True)

    if salvar:
        # Mapeamento exato com as colunas do seu SQL
        motor = {
            "marca": marca, 
            "modelo": modelo, 
            "fabricante": fabricante,
            "num_serie": num_serie,
            "potencia_hp_cv": potencia, 
            "tensao_v": tensao, 
            "corrente_nominal_a": corrente,
            "rpm_nominal": rpm, 
            "frequencia_hz": frequencia, 
            "rendimento_perc": rendimento,
            "polos": polos, 
            "carcaca": carcaca, 
            "norma": norma,
            "classe_isolacao": isolacao, 
            "grau_protecao_ip": ip, 
            "regime_servico": regime,
            "fator_servico": fator_servico, 
            "peso_total_kg": peso, 
            "tipo_graxa": tipo_graxa,
            "passo_principal": passo_principal, 
            "bitola_fio_principal": fio_principal, 
            "espiras_principal": espira_principal,
            "passo_auxiliar": passo_auxiliar, 
            "bitola_fio_auxiliar": fio_auxiliar, 
            "espiras_auxiliar": espira_auxiliar, 
            "tipo_enrolamento": tipo_enrolamento,
            "numero_ranhuras": numero_ranhuras, 
            "fios_paralelos": fios_paralelos,
            "ligacao_interna": ligacao_interna,
            "diametro_interno_estator_mm": diametro_interno, 
            "comprimento_pacote_mm": comprimento_pacote,
            "observacoes": f"{observacoes} \nEsquema: {esquema}", 
            "origem_registro": origem
        }

        # --- LIMPEZA DE DADOS VAZIOS ---
        motor = {k: (v if (v != "" and v is not None) else None) for k, v in motor.items()}

        # Rodar lógica da calculadora (alerta apenas visual, não impede salvar)
        alertas = alertas_validacao_projeto(motor)
        if alertas:
            for msg in alertas:
                st.warning(msg)

        sucesso, mensagem = salvar_motor_supabase(supabase, motor)
        if sucesso:
            clear_motores_cache()
            st.success(mensagem)
            st.balloons()
        else:
            st.error(mensagem)

import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS (VERSÃO FINAL)
# =============================
def aplicar_estilo():
    st.markdown("""
        <style>
        /* 1. Reset e Fundo */
        .stApp {
            background: transparent !important;
            max-width: 1000px;
            margin: 0 auto;
        }
        body {
            background: #05070d !important;
            color: white !important;
            font-family: 'Courier New', monospace;
        }

        /* 2. Container Relativo (Onde a mágica acontece) */
        .motor-wrapper {
            position: relative;
            margin-bottom: 20px;
        }

        /* 3. O Card Visual */
        .tech-card {
            background: linear-gradient(145deg, #081018, #05070d);
            border: 2px solid #00ffff33;
            border-radius: 18px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 0 20px #00ffff11;
            transition: all 0.3s ease;
            position: relative;
            z-index: 1; /* Fica atrás do botão */
        }

        .motor-wrapper:hover .tech-card {
            border-color: #00ffff;
            box-shadow: 0 0 40px #00ffff33;
            transform: translateY(-2px);
        }

        /* 4. Botão Streamlit Invisível (Cobrindo tudo) */
        .motor-wrapper div.stButton {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10; /* Fica na frente de tudo para capturar o clique */
        }

        .motor-wrapper div.stButton > button {
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            width: 100% !important;
            height: 100% !important; /* Ocupa a altura total do card */
            cursor: pointer !important;
            padding: 0 !important;
        }

        /* Remove efeitos de clique padrão do Streamlit */
        .motor-wrapper div.stButton > button:focus, 
        .motor-wrapper div.stButton > button:active {
            background: transparent !important;
            box-shadow: none !important;
            outline: none !important;
        }

        /* 5. Estilo dos Textos */
        .card-title { font-size: 1.6rem; color: #00ffff; font-weight: 800; letter-spacing: 2px; margin: 0; }
        .card-id { color: #8b949e; font-size: 0.85rem; margin-top: 5px; }
        .card-metrics { display: flex; justify-content: space-around; margin-top: 20px; }
        .metric-item { display: flex; flex-direction: column; }
        .metric-value { font-size: 1.2rem; font-weight: bold; }
        .metric-label { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; }

        /* Evita que o conteúdo do card bloqueie o clique */
        .tech-card * {
            pointer-events: none;
        }

        /* Ajuste das Tabs para o Modo Dark */
        .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
        .stTabs [data-baseweb="tab"] { color: #8b949e; }
        .stTabs [data-baseweb="tab--active"] { color: #00ffff !important; border-bottom-color: #00ffff !important; }
        </style>
    """, unsafe_allow_html=True)

# =============================
# 🛠️ FUNÇÕES AUXILIARES
# =============================
def limpar_passo(passo_raw):
    if not passo_raw: return "---"
    s = str(passo_raw).strip()
    return re.sub(r"^[1][\s?:\-]*", "", s).replace(":", " ").replace("-", " ").strip()

def obter_configuracoes_ligacao(m):
    fases = 3 if "TRI" in str(m.get('fases', '')).upper() else 1
    tensao = str(m.get('tensao_v', ''))
    if fases == 3:
        if "220" in tensao and "380" in tensao:
            return "⚡ 220V: Triângulo (Δ) | 380V: Estrela (Y)"
        return f"⚡ Tensão: {tensao}"
    return "🔌 Monofásico: Verifique esquema Série/Paralelo"

# =============================
# 🚀 PÁGINA DE CONSULTA
# =============================
def show(supabase):
    aplicar_estilo()
    
    st.title("🔍 Central de Motores")
    busca = st.text_input("", placeholder="Ex: Weg 2cv 4 polos", label_visibility="collapsed")
    
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except Exception:
        st.error("Erro ao conectar com o banco de dados.")
        return

    # Filtro de Busca
    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in f"{str(m.get('marca',''))} {str(m.get('modelo',''))} {str(m.get('potencia_hp_cv',''))}".lower()]

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        aberto = st.session_state.detalhes_visiveis.get(key_det, False)

        # Tratamento de dados nulos (Prevenção do erro 'upper')
        marca = str(m.get('marca') or "---").upper()
        modelo = m.get('modelo') or "S/N"
        potencia = m.get('potencia_hp_cv') or "-"
        rpm = m.get('rpm_nominal') or "-"
        corrente = m.get('corrente_nominal_a') or "-"

        # --- ESTRUTURA DO MOTOR ---
        # Usamos um container de marcação para agrupar o HTML e o Botão
        with st.container():
            st.markdown(f'<div class="motor-wrapper">', unsafe_allow_html=True)
            
            # 1. O Design do Card (HTML)
            st.markdown(f"""
                <div class="tech-card">
                    <div class="card-title">{marca}</div>
                    <div class="card-id">ID: {modelo}</div>
                    <div class="card-metrics">
                        <div class="metric-item">
                            <span class="metric-value" style="color: #00ffff;">{potencia}</span>
                            <span class="metric-label">CV HP</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value" style="color: #10b981;">{rpm}</span>
                            <span class="metric-label">RPM</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-value" style="color: #f59e0b;">{corrente}</span>
                            <span class="metric-label">AMPERES</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # 2. O Botão Invisível (Captura o clique no card inteiro)
            if st.button("Abrir", key=f"btn_{id_m}"):
                st.session_state.detalhes_visiveis[key_det] = not aberto
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # --- ÁREA DE DETALHES (EXPANSÍVEL) ---
        if aberto:
            with st.container():
                st.markdown(f"""
                    <div style="background: rgba(0,255,255,0.03); border: 2px solid #00ffff44; 
                                border-top:none; border-radius: 0 0 15px 15px; padding: 20px; 
                                margin: -25px auto 30px auto; width: 95%;">
                """, unsafe_allow_html=True)
                
                t1, t2, t3 = st.tabs(["🔌 Ligações", "🌀 Bobinagem", "⚙️ Mecânica"])
                
                with t1:
                    st.info(obter_configuracoes_ligacao(m))
                    st.write(f"**Tensão:** {m.get('tensao_v','-')} V")
                    st.write(f"**Fases:** {m.get('fases','-')}")
                
                with t2:
                    col1, col2 = st.columns(2)
                    col1.metric("Passo Principal", limpar_passo(m.get("passo_principal")))
                    col2.metric("Bitola Fio", m.get("bitola_fio_principal", "---"))
                    st.divider()
                    st.write(f"**Esquema de Ligação:** {m.get('esquema_ligacao','Não informado')}")

                with t3:
                    st.markdown(f"**Rolamento Dianteiro:** `{m.get('rolamento_dianteiro','-')}`")
                    st.markdown(f"**Rolamento Traseiro:** `{m.get('rolamento_traseiro','-')}`")
                
                st.markdown('</div>', unsafe_allow_html=True)

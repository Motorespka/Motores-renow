import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS (COMPLETA)
# =============================
def aplicar_estilo():
    st.markdown("""
        <style>
        /* BACKGROUND TECNOLÓGICO */
        .stApp {
            background: transparent !important;
            max-width: 1000px;
            margin: 0 auto;
        }
        body {
            background:
                radial-gradient(circle at 20% 20%, #00ffff11 0%, transparent 40%),
                radial-gradient(circle at 80% 60%, #0099ff11 0%, transparent 40%),
                #05070d !important;
            color: white !important;
            overflow-x: hidden;
            font-family: 'Courier New', monospace;
        }
        body::before {
            content: "";
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(#00ffff11 1px, transparent 1px),
                linear-gradient(90deg, #00ffff11 1px, transparent 1px);
            background-size: 60px 60px;
            animation: gridMove 25s linear infinite;
            pointer-events: none;
            z-index: -1;
        }
        @keyframes gridMove {
            from { transform: translateY(0); }
            to { transform: translateY(60px); }
        }

        /* CARD ÚNICO */
        .tech-card {
            background: linear-gradient(145deg, #081018, #05070d);
            border: 2px solid #00ffff33;
            border-radius: 18px;
            padding: 35px;
            box-shadow: 0 0 30px #00ffff22;
            transition: all 0.35s ease;
            margin: 30px auto;
            width: 90%;
            cursor: pointer;
            text-align: center;
            position: relative; /* ESSENCIAL PARA O CLIQUE */
            z-index: 1;
        }
        .tech-card:hover {
            transform: scale(1.02);
            box-shadow: 0 0 60px #00ffff44;
            border-color: #00ffff;
        }

        /* INPUTS E BOTÕES DO SISTEMA */
        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(0, 255, 255, 0.05) !important;
            border: 1px solid #00ffff33 !important;
            color: #00ffff !important;
            border-radius: 8px !important;
        }

        /* RESPONSIVO */
        @media (max-width: 768px) {
            .tech-card { padding: 20px; width: 95%; }
        }

        /* =============================
           🖱️ CLICK LAYER (CAMADA FANTASMA)
        ============================= */
        div.stButton {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10;
        }
        div.stButton > button {
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            width: 100% !important;
            height: 100% !important;
            min-height: 120px;
            padding: 0 !important;
            margin: 0 !important;
            cursor: pointer !important;
            box-shadow: none !important;
            transform: none !important; 
        }
        div.stButton > button:hover, 
        div.stButton > button:active, 
        div.stButton > button:focus {
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            box-shadow: none !important;
            outline: none !important;
        }
        
        /* Impede que o texto ou divs internas bloqueiem o clique no botão fantasma */
        .tech-card h2, .tech-card p, .tech-card div {
            pointer-events: none;
        }
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
    busca = st.text_input("", placeholder="Pesquisar por Marca ou Modelo...", label_visibility="collapsed")
    
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except Exception:
        st.error("Falha na conexão com o Banco de Dados.")
        return

    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in f"{m.get('marca','')} {m.get('modelo','')} {m.get('potencia_hp_cv','')}".lower()]

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        aberto = st.session_state.detalhes_visiveis.get(key_det, False)

        # PREVENÇÃO DE ERRO: Garante que variáveis nulas virem texto seguro antes do layout
        marca_raw = m.get('marca')
        marca = str(marca_raw).upper() if marca_raw else "---"
        modelo = m.get('modelo') or "-"
        potencia = m.get('potencia_hp_cv') or "-"
        rpm = m.get('rpm_nominal') or "-"
        corrente = m.get('corrente_nominal_a') or "-"

        # 1. ABRE A DIV DO CARD (Note que o botão fica DENTRO do markdown)
        st.markdown(f'''
        <div class="tech-card">
            <h2 style="color: #00ffff; margin-bottom: 5px; font-weight: 800; letter-spacing: 2px;">{marca}</h2>
            <p style="color: #8b949e; font-size: 0.9rem; margin-bottom: 15px;">ID: {modelo}</p>
            <div style="display: flex; justify-content: space-around; gap: 10px;">
                <div style="color: white;"><span style="color: #00ffff; font-size: 1.1rem; font-weight: bold;">{potencia}</span> CV HP</div>
                <div style="color: white;"><span style="color: #10b981; font-size: 1.1rem; font-weight: bold;">{rpm}</span> RPM</div>
                <div style="color: white;"><span style="color: #f59e0b; font-size: 1.1rem; font-weight: bold;">{corrente}</span> A</div>
            </div>
        ''', unsafe_allow_html=True)
        
        # 2. O BOTÃO INVISÍVEL
        if st.button(" ", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not aberto
            st.rerun()

        # 3. FECHA A DIV DO CARD
        st.markdown('</div>', unsafe_allow_html=True)

        # --- ÁREA DE INFORMAÇÕES EXPANSÍVEIS ---
        if aberto:
            with st.container():
                st.markdown("""
                <div style="background: rgba(0,255,255,0.03); border: 2px solid #00ffff44; 
                            border-top:none; border-radius: 0 0 15px 15px; padding: 20px; 
                            margin: -35px auto 20px auto; max-width: 88%;">
                """, unsafe_allow_html=True)
                
                t1, t2, t3 = st.tabs(["🔌 Ligações", "🌀 Bobinagem", "⚙️ Mecânica"])
                
                with t1:
                    st.info(obter_configuracoes_ligacao(m))
                    st.write(f"**Fases:** {m.get('fases') or '-'} | **Tensão:** {m.get('tensao_v') or '-'} V")
                
                with t2:
                    c1, c2 = st.columns(2)
                    c1.metric("Passo Principal", limpar_passo(m.get("passo_principal")))
                    c2.metric("Bitola Fio", m.get("bitola_fio_principal") or "---")

                with t3:
                    st.markdown(f"**Rolamento Dianteiro:** `{m.get('rolamento_dianteiro') or '-'}`")
                    st.markdown(f"**Rolamento Traseiro:** `{m.get('rolamento_traseiro') or '-'}`")
                
                st.markdown('</div>', unsafe_allow_html=True)

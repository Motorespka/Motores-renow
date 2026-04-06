import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS (TURBINADO)
# =============================
def aplicar_estilo():
    st.markdown("""
        <style>
        /* BACKGROUND E GRID */
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
            font-family: 'Courier New', monospace;
        }

        /* CONTAINER DO MOTOR (Agrupa Card + Botão) */
        .motor-container {
            position: relative;
            margin-bottom: 20px;
        }

        /* CARD VISUAL */
        .tech-card {
            background: linear-gradient(145deg, #081018, #05070d);
            border: 2px solid #00ffff33;
            border-radius: 18px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 0 30px #00ffff22;
            transition: all 0.3s ease;
            position: relative;
            z-index: 1; /* Fica atrás do botão */
        }

        .motor-container:hover .tech-card {
            border-color: #00ffff;
            box-shadow: 0 0 50px #00ffff44;
            transform: translateY(-2px);
        }

        /* BOTÃO INVISÍVEL (A CAMADA DE CLIQUE) */
        /* Ocupa 100% da área do motor-container */
        div.stButton {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10; /* Fica na frente para receber o clique */
        }

        div.stButton > button {
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            width: 100% !important;
            height: 160px !important; /* Ajuste para cobrir a altura do card */
            cursor: pointer !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Remove brilho e bordas ao focar/clicar */
        div.stButton > button:focus, 
        div.stButton > button:active,
        div.stButton > button:hover {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: transparent !important;
        }

        /* ELEMENTOS INTERNOS */
        .card-title { font-size: 1.5rem; color: #00ffff; font-weight: 800; letter-spacing: 2px; }
        .card-subtitle { color: #8b949e; font-size: 0.9rem; margin-bottom: 15px; }
        .metric-unit { font-size: 1.1rem; font-weight: bold; }

        /* Faz o texto ignorar o mouse para não atrapalhar o clique do botão */
        .tech-card * {
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
        motores = [m for m in motores if q in f"{str(m.get('marca',''))} {str(m.get('modelo',''))} {str(m.get('potencia_hp_cv',''))}".lower()]

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        aberto = st.session_state.detalhes_visiveis.get(key_det, False)

        # Dados seguros (Previne erro de NoneType)
        marca = str(m.get('marca') or "---").upper()
        modelo = m.get('modelo') or "-"
        potencia = m.get('potencia_hp_cv') or "-"
        rpm = m.get('rpm_nominal') or "-"
        corrente = m.get('corrente_nominal_a') or "-"

        # --- ESTRUTURA DO CARD ---
        # Criamos um container manual para agrupar o HTML e o Botão
        st.markdown(f'<div class="motor-container">', unsafe_allow_html=True)
        
        # 1. O Desenho Visual (HTML)
        st.markdown(f'''
            <div class="tech-card">
                <div class="card-title">{marca}</div>
                <div class="card-subtitle">ID: {modelo}</div>
                <div style="display: flex; justify-content: space-around; gap: 10px;">
                    <div style="color: white;"><span style="color: #00ffff;" class="metric-unit">{potencia}</span> CV HP</div>
                    <div style="color: white;"><span style="color: #10b981;" class="metric-unit">{rpm}</span> RPM</div>
                    <div style="color: white;"><span style="color: #f59e0b;" class="metric-unit">{corrente}</span> A</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

        # 2. O Botão (Fica por cima devido ao CSS position: absolute)
        if st.button(" ", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not aberto
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

        # --- ÁREA DE DETALHES (SÓ APARECE SE "ABERTO" FOR TRUE) ---
        if aberto:
            with st.container():
                st.markdown("""
                <div style="background: rgba(0,255,255,0.03); border: 2px solid #00ffff44; 
                            border-top:none; border-radius: 0 0 15px 15px; padding: 20px; 
                            margin: -25px auto 30px auto; max-width: 90%;">
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

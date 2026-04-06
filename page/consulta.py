import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS (TURBINADO)
# =============================
def aplicar_estilo():
    st.markdown(f"""
        <style>
        .stApp {{
            background: transparent !important;
            max-width: 1000px;
            margin: 0 auto;
        }}
        body {{
            background:
                radial-gradient(circle at 20% 20%, #00ffff11 0%, transparent 40%),
                radial-gradient(circle at 80% 60%, #0099ff11 0%, transparent 40%),
                #05070d !important;
            color: white !important;
            font-family: 'Courier New', monospace;
        }}
        
        /* Container Principal do Card */
        .tech-card-container {{
            background: linear-gradient(145deg, #081018, #05070d);
            border: 2px solid #00ffff33;
            border-radius: 18px;
            box-shadow: 0 0 30px #00ffff22;
            margin: 15px auto;
            transition: all 0.3s ease;
            overflow: hidden;
        }}
        .tech-card-container:hover {{
            border-color: #00ffff;
            box-shadow: 0 0 50px #00ffff44;
            transform: translateY(-2px);
        }}

        /* Reset do Botão Streamlit para ocupar o card todo */
        div.stButton > button {{
            background: transparent !important;
            border: none !important;
            color: white !important;
            width: 100% !important;
            height: auto !important;
            padding: 0px !important;
            margin: 0px !important;
            display: block !important;
        }}
        
        /* Estilização interna do conteúdo do card */
        .card-content {{
            padding: 25px;
            pointer-events: none; /* Deixa o clique passar para o botão */
        }}
        .card-title {{ font-size: 1.5rem; color: #00ffff; font-weight: 800; letter-spacing: 2px; margin-bottom: 5px; }}
        .card-subtitle {{ color: #8b949e; font-size: 0.9rem; margin-bottom: 15px; }}
        .card-metrics {{ display: flex; justify-content: space-around; gap: 10px; }}
        .metric-unit {{ font-size: 1.1rem; font-weight: bold; }}
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
    except:
        st.error("Erro de conexão com o banco.")
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

        # 1. DESIGN DO CARD (HTML)
        # O botão do Streamlit será colocado "dentro" dessa estrutura visual
        st.markdown(f"""
        <div class="tech-card-container">
            <div class="card-content">
                <div class="card-title">{m.get('marca','---').upper()}</div>
                <div class="card-subtitle">ID: {m.get('modelo','-')}</div>
                <div class="card-metrics">
                    <div style="color: #00ffff;"><span class="metric-unit">{m.get('potencia_hp_cv','-')}</span> CV HP</div>
                    <div style="color: #10b981;"><span class="metric-unit">{m.get('rpm_nominal','-')}</span> RPM</div>
                    <div style="color: #f59e0b;"><span class="metric-unit">{m.get('corrente_nominal_a','-')}</span> A</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 2. O BOTÃO INVISÍVEL (OCUPA O CARD TODO)
        # O texto do botão é apenas um espaço vazio ou ícone discreto, pois o HTML acima já mostra tudo
        if st.button("⠀", key=f"btn_{id_m}", use_container_width=True):
            st.session_state.detalhes_visiveis[key_det] = not aberto
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

        # 3. ÁREA DE INFORMAÇÕES (EXPANSÍVEL)
        if aberto:
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(0,255,255,0.03); border: 2px solid #00ffff44; 
                            border-top:none; border-radius: 0 0 15px 15px; padding: 20px; 
                            margin: -15px auto 20px auto; max-width: 98%;">
                """, unsafe_allow_html=True)
                
                t1, t2, t3 = st.tabs(["🔌 Ligações", "🌀 Bobinagem", "⚙️ Mecânica"])
                
                with t1:
                    st.info(obter_configuracoes_ligacao(m))
                    st.write(f"**Tensão Cadastrada:** {m.get('tensao_v','-')} V")
                
                with t2:
                    c1, c2 = st.columns(2)
                    c1.metric("Passo Principal", limpar_passo(m.get("passo_principal")))
                    c2.metric("Bitola Fio", m.get("bitola_fio_principal", "---"))

                with t3:
                    st.markdown(f"**Rolamento Dianteiro:** `{m.get('rolamento_dianteiro','-')}`")
                    st.markdown(f"**Rolamento Traseiro:** `{m.get('rolamento_traseiro','-')}`")
                
                st.markdown('</div>', unsafe_allow_html=True)

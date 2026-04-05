import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS
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
        body::before {{
            content: "";
            position: fixed; inset: 0;
            background-image:
                linear-gradient(#00ffff11 1px, transparent 1px),
                linear-gradient(90deg, #00ffff11 1px, transparent 1px);
            background-size: 60px 60px;
            animation: gridMove 25s linear infinite;
            pointer-events: none; z-index: -1;
        }}
        @keyframes gridMove {{
            from {{ transform: translateY(0); }}
            to {{ transform: translateY(60px); }}
        }}
        
        /* Ajuste para o Card abrigar o botão de ponta a ponta */
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
        }}

        /* Estilização do botão para parecer o card */
        div.stButton > button {{
            background: transparent !important;
            border: none !important;
            color: white !important;
            height: auto !important;
            padding: 25px !important;
            text-align: center !important;
        }}
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
# 🚀 EXECUÇÃO DA PÁGINA
# =============================
def show(supabase):
    aplicar_estilo()
    
    st.title("🔍 Central de Motores")
    busca = st.text_input("", placeholder="Pesquisar motor...", label_visibility="collapsed")
    
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except:
        st.error("Erro de conexão.")
        return

    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in f"{m.get('marca','')} {m.get('modelo','')}".lower()]

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        aberto = st.session_state.detalhes_visiveis.get(key_det, False)

        # CARD INTEIRO COMO BOTÃO
        st.markdown('<div class="tech-card-container">', unsafe_allow_html=True)
        
        # O label do botão agora carrega as informações principais
        label_btn = f"""
            {m.get('marca','').upper()} 
            \n {m.get('modelo','-')}
            \n {m.get('potencia_hp_cv','-')} HP  |  {m.get('rpm_nominal','-')} RPM  |  {m.get('corrente_nominal_a','-')} A
        """
        
        if st.button(label_btn, key=f"btn_{id_m}", use_container_width=True):
            st.session_state.detalhes_visiveis[key_det] = not aberto
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

        # ABA DE INFORMAÇÕES (EXPANSÍVEL)
        if aberto:
            with st.container():
                st.markdown('<div style="background: rgba(0,255,255,0.05); border: 2px solid #00ffff44; border-top:none; border-radius: 0 0 15px 15px; padding: 20px; margin: -15px auto 20px auto; max-width: 98%;">', unsafe_allow_html=True)
                
                t1, t2, t3 = st.tabs(["🔌 Ligações", "🌀 Bobinagem", "⚙️ Mecânica"])
                
                with t1:
                    st.info(obter_configuracoes_ligacao(m))
                    st.write(f"**Tensão:** {m.get('tensao_v','-')}")
                
                with t2:
                    c1, c2 = st.columns(2)
                    c1.metric("Passo", limpar_passo(m.get("passo_principal")))
                    c2.metric("Fio", m.get("bitola_fio_principal", "---"))

                with t3:
                    st.write(f"**Rolamento Dianteiro:** {m.get('rolamento_dianteiro','-')}")
                    st.write(f"**Rolamento Traseiro:** {m.get('rolamento_traseiro','-')}")
                
                st.markdown('</div>', unsafe_allow_html=True)

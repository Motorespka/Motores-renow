import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS (DESIGN ORIGINAL + CLIQUE INTEGRADO)
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
        
        /* SEU CARD ORIGINAL REFORMULADO */
        .tech-card-wrapper {{
            position: relative;
            background: linear-gradient(145deg, #081018, #05070d);
            border: 2px solid #00ffff33;
            border-radius: 18px;
            padding: 25px;
            box-shadow: 0 0 30px #00ffff22;
            margin-bottom: 10px;
            text-align: center;
            transition: 0.3s;
        }}
        
        .tech-card-wrapper:hover {{
            border-color: #00ffff;
            transform: translateY(-2px);
            box-shadow: 0 0 40px #00ffff33;
        }}

        /* TRUQUE: BOTÃO INVISÍVEL QUE COBRE O CARD */
        div[data-testid="stVerticalBlock"] > div:has(button.card-overlay) {{
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 10;
            opacity: 0;
        }}
        
        button.card-overlay {{
            width: 100% !important;
            height: 140px !important; /* Ajuste conforme a altura do seu card */
            background: transparent !important;
            border: none !important;
            cursor: pointer !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# =============================
# 🛠️ FUNÇÕES DE APOIO
# =============================
def limpar_passo(passo_raw):
    if not passo_raw: return "---"
    s = str(passo_raw).strip()
    return re.sub(r"^[1][\s?:\-]*", "", s).replace(":", " ").replace("-", " ").strip()

# =============================
# 🚀 PÁGINA DE CONSULTA
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

        # CONTAINER DO CARD
        with st.container():
            # 1. O Visual do Card (Exatamente como você queria)
            st.markdown(f"""
            <div class="tech-card-wrapper">
                <div style="font-size: 1.5rem; color: #00ffff; font-weight: 800; letter-spacing: 2px;">{m.get('marca','---').upper()}</div>
                <div style="color: #8b949e; margin-bottom: 10px;">ID: {m.get('modelo','-')}</div>
                <div style="display: flex; justify-content: space-around; font-weight: bold;">
                    <div style="color: #00ffff;">{m.get('potencia_hp_cv','-')} HP</div>
                    <div style="color: #10b981;">{m.get('rpm_nominal','-')} RPM</div>
                    <div style="color: #f59e0b;">{m.get('corrente_nominal_a','-')} A</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 2. O Botão Invisível (Sobreposto ao card)
            # Ele não aparece, mas captura o clique em qualquer lugar do card acima
            if st.button(" ", key=f"overlay_{id_m}", help=f"Ver detalhes de {m.get('marca')}"):
                st.session_state.detalhes_visiveis[key_det] = not aberto
                st.rerun()

        # 3. AREA DE DETALHES (Aparece logo abaixo sem "quebrar" o card)
        if aberto:
            with st.expander("🛠️ DETALHES TÉCNICOS EM EXIBIÇÃO", expanded=True):
                t1, t2, t3 = st.tabs(["🔌 Ligações", "🌀 Bobinagem", "⚙️ Mecânica"])
                with t1:
                    st.write(f"**Tensão:** {m.get('tensao_v','-')}")
                with t2:
                    c1, c2 = st.columns(2)
                    c1.metric("Passo", limpar_passo(m.get("passo_principal")))
                    c2.metric("Fio", m.get("bitola_fio_principal", "---"))
                with t3:
                    st.write(f"**Rolamento Dianteiro:** {m.get('rolamento_dianteiro','-')}")
                    st.write(f"**Rolamento Traseiro:** {m.get('rolamento_traseiro','-')}")
        
        st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

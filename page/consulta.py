import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS (SEU CÓDIGO)
# =============================
def aplicar_estilo():
    # Nota: No Python, usamos {{ }} para chaves de CSS não darem conflito
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
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(#00ffff11 1px, transparent 1px),
                linear-gradient(90deg, #00ffff11 1px, transparent 1px);
            background-size: 60px 60px;
            animation: gridMove 25s linear infinite;
            pointer-events: none;
            z-index: -1;
        }}
        @keyframes gridMove {{
            from {{ transform: translateY(0); }}
            to {{ transform: translateY(60px); }}
        }}
        .tech-card {{
            background: linear-gradient(145deg, #081018, #05070d);
            border: 2px solid #00ffff33;
            border-radius: 18px;
            padding: 25px;
            box-shadow: 0 0 30px #00ffff22;
            margin: 10px auto;
            text-align: center;
        }}
        .metric-box {{
            display: flex;
            justify-content: space-around;
            margin-top: 15px;
        }}
        .metric-item {{
            text-align: center;
        }}
        .metric-label {{ font-size: 0.7rem; color: #8b949e; text-transform: uppercase; }}
        .metric-value {{ font-size: 1.1rem; font-weight: bold; color: #00ffff; }}
        </style>
    """, unsafe_allow_html=True)

# =============================
# 🛠️ FUNÇÕES DE APOIO
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
        return f"⚡ Tensão: {tensao} (Consulte Placa)"
    return "🔌 Monofásico: Verifique esquema Série/Paralelo"

# =============================
# 🚀 PÁGINA DE CONSULTA
# =============================
def show(supabase):
    aplicar_estilo()
    
    st.title("🔍 Central de Motores")
    
    # Barra de Busca Estilizada
    busca = st.text_input("", placeholder="Pesquisar por Marca ou Modelo...", label_visibility="collapsed")
    
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except:
        st.error("Falha na conexão com o Banco de Dados.")
        return

    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in f"{m.get('marca','')} {m.get('modelo','')}".lower()]

    if not motores:
        st.info("Nenhum motor encontrado no sistema.")
        return

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    # LOOP DE MOTORES
    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        aberto = st.session_state.detalhes_visiveis.get(key_det, False)

        # 1. Card Visual Principal (Usando sua classe .tech-card)
        st.markdown(f"""
        <div class="tech-card">
            <div style="font-size: 1.5rem; color: #00ffff; font-weight: 800; letter-spacing: 2px;">{m.get('marca','---').upper()}</div>
            <div style="color: #8b949e; margin-bottom: 15px;">ID: {m.get('modelo','-')}</div>
            <div class="metric-box">
                <div class="metric-item">
                    <div class="metric-label">Potência</div>
                    <div class="metric-value">{m.get('potencia_hp_cv','-')} HP</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Rotação</div>
                    <div class="metric-value" style="color: #10b981;">{m.get('rpm_nominal','-')} RPM</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Corrente</div>
                    <div class="metric-value" style="color: #f59e0b;">{m.get('corrente_nominal_a','-')} A</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Botão Médio/Grande de Ação
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            label = "🔼 RECOLHER INFORMAÇÕES" if aberto else "🔽 EXPANDIR DETALHES TÉCNICOS"
            if st.button(label, key=f"btn_{id_m}", use_container_width=True):
                st.session_state.detalhes_visiveis[key_det] = not aberto
                st.rerun()

        # 3. Área de Informações (Só aparece se clicado)
        if aberto:
            with st.container():
                st.markdown('<div style="background: rgba(0,255,255,0.05); border: 1px solid #00ffff44; border-radius: 15px; padding: 20px; margin-top: -10px;">', unsafe_allow_html=True)
                
                tab_liga, tab_bobina, tab_mecanica = st.tabs(["🔌 Ligações", "🌀 Bobinagem", "⚙️ Mecânica"])
                
                with tab_liga:
                    st.success(obter_configuracoes_ligacao(m))
                    st.caption(f"Fases: {m.get('fases','-')} | Tensão Cadastrada: {m.get('tensao_v','-')}")

                with tab_bobina:
                    c1, c2 = st.columns(2)
                    c1.metric("Passo Principal", limpar_passo(m.get("passo_principal")))
                    c2.metric("Bitola do Fio", m.get("bitola_fio_principal", "---"))

                with tab_mecanica:
                    st.write(f"**Rolamento Dianteiro:** {m.get('rolamento_dianteiro','-')}")
                    st.write(f"**Rolamento Traseiro:** {m.get('rolamento_traseiro','-')}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<hr style='opacity: 0.1;'>", unsafe_allow_html=True)

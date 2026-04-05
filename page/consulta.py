import streamlit as st
import re

# =================================================================
# 1. FUNÇÕES DE APOIO (LIMPAGEM E FORMATAÇÃO)
# =================================================================
def limpar_passo(passo_raw):
    if not passo_raw: return "---"
    s = str(passo_raw).strip()
    s = re.sub(r"^[1][\s?:\-]*", "", s)
    return s.replace(":", " ").replace("-", " ").strip()

def render_dado(label, valor, unidade="", highlight=False):
    color = "#00ffff" if not highlight else "#f59e0b"
    val = valor if valor and str(valor).lower() not in ["none", "nan", ""] else "---"
    st.markdown(f"""
        <div style="background: rgba(0,255,255,0.03); border:1px solid rgba(0,255,255,0.1);
        border-radius:6px; padding:10px; margin-bottom:5px;">
            <div style="font-size:0.65rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">{label}</div>
            <div style="font-size:0.9rem; color:white; font-family:monospace; font-weight:bold;">
            {val} <span style="color:{color}; font-size:0.7rem;">{unidade}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# =================================================================
# 2. LÓGICA DE LIGAÇÃO (CABOS, CORES E PLACAS)
# =================================================================
def render_esquemas_completos(motor):
    fases = str(motor.get("fases", "")).lower()
    tensao_raw = str(motor.get("tensao_v", ""))
    tensoes = [t.strip() for t in tensao_raw.split('/') if t.strip()]
    
    st.markdown("### 🔌 Esquemas de Ligação e Cabos")
    
    # Tabela de Identificação (O que o usuário pediu: Cor + Número + Placa)
    st.markdown("""
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:0.8rem;">
            <div><b>1:</b> <span style="color:#4d4dff">AZUL</span> (U1)</div>
            <div><b>2:</b> <span style="color:#ffffff">BRANCO</span> (V1)</div>
            <div><b>3:</b> <span style="color:#ff8c00">LARANJA</span> (W1)</div>
            <div><b>4:</b> <span style="color:#ffff00">AMARELO</span> (U2)</div>
            <div><b>5:</b> <span style="color:#888888">PRETO</span> (V2)</div>
            <div><b>6:</b> <span style="color:#ff4d4d">VERMELHO</span> (W2)</div>
        </div>
    """, unsafe_allow_html=True)

    if "mono" in fases:
        aba1, aba2 = st.tabs(["5 CABOS", "6 CABOS"])
        with aba1:
            st.info("Ligação Monofásica com 5 Cabos (Sentido de Rotação)")
            st.code("Horário: L1(1,5) - L2(4) | Unir: 2,3\nAnti-Horário: L1(1,4) - L2(5) | Unir: 2,3")
        with aba2:
            st.info("Ligação Monofásica com 6 Cabos (Dupla Tensão)")
            st.code("110V/127V: L1(1,3,5) - L2(2,4,6)\n220V/254V: L1(1) - L2(4) | Unir: 2+3+5+6")
    else:
        aba_tri = st.tabs(["6 CABOS", "12 CABOS"])
        with aba_tri[0]:
            for i, t in enumerate(tensoes):
                st.write(f"**Ligação {t}V:**")
                if i == 0: st.code(f"Triângulo (∆): L1(1,6) - L2(2,4) - L3(3,5)")
                else: st.code(f"Estrela (Y): L1(1) - L2(2) - L3(3) | Unir: 4,5,6")
        with aba_tri[1]:
            st.warning("Motor de 12 Cabos: Permite até 4 tensões (220/380/440/760V)")
            st.code("Consulte o diagrama interno para ligação em Série/Paralelo (U1-U6).")

# =================================================================
# 3. TELA DE CONSULTA
# =================================================================
def show(supabase):
    # CSS para o Botão "Card"
    st.markdown("""
        <style>
        div.stButton > button {
            width: 100% !important; min-height: 230px !important;
            background: linear-gradient(135deg, rgba(0,40,65,0.9) 0%, rgba(0,15,30,1) 100%) !important;
            border: 1px solid rgba(0, 255, 255, 0.2) !important;
            border-left: 6px solid #10b981 !important; border-radius: 12px !important;
            margin-bottom: 25px !important; transition: all 0.3s ease !important;
        }
        div.stButton > button:hover { border-color: #00ffff !important; transform: scale(1.01); }
        div.stButton > button p { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 🔍 Consulta de Motores")
    busca = st.text_input("🔎 Pesquisar...", placeholder="Ex: Weg 2cv 4 polos")
    
    # Busca no Banco
    res = supabase.table("motores").select("*").order("id", desc=True).execute()
    motores = res.data if res.data else []

    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in f"{m.get('marca')} {m.get('modelo')} {m.get('potencia_hp_cv')}".lower()]

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"

        # Botão Invisível (O Card Clicável)
        if st.button(" ", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()

        # --- CAPA DO CARD (O HUD COM TODAS AS INFOS) ---
        # ESTE BLOCO ABAIXO DEVE TER 'unsafe_allow_html=True'
        st.markdown(f"""
        <div style="margin-top:-235px; margin-bottom:45px; padding:20px; pointer-events:none; position:relative; z-index:5;">
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <small style="color:#00ffff; font-family:monospace; letter-spacing:1px;">ID #{id_m}</small>
                    <div style="font-size:1.5rem; color:white; font-weight:bold;">{(m.get('marca') or '---').upper()}</div>
                    <div style="color:#aaa; font-size:0.9rem;">{m.get('modelo') or ''}</div>
                </div>
                <div style="background:rgba(16,185,129,0.2); color:#10b981; padding:4px 12px; border-radius:20px; font-size:0.7rem; font-weight:bold; border:1px solid #10b981; height:fit-content;">
                    {str(m.get('fases','')).upper()}
                </div>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px; margin-top:20px; border-top:1px solid rgba(255,255,255,0.1); padding-top:15px;">
                <div style="text-align:center;">
                    <div style="font-size:0.55rem; color:#8b949e;">POTÊNCIA</div>
                    <div style="color:#00f2ff; font-weight:bold; font-size:1.1rem;">{m.get('potencia_hp_cv','-')}</div>
                </div>
                <div style="text-align:center; border-left:1px solid #333; border-right:1px solid #333;">
                    <div style="font-size:0.55rem; color:#8b949e;">ROTAÇÃO</div>
                    <div style="color:#10b981; font-weight:bold; font-size:1.1rem;">{m.get('rpm_nominal','-')}</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.55rem; color:#8b949e;">AMPERAGEM</div>
                    <div style="color:#f59e0b; font-weight:bold; font-size:1.1rem;">{m.get('corrente_nominal_a','-')}A</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.55rem; color:#8b949e;">TENSÃO</div>
                    <div style="color:#a855f7; font-weight:bold; font-size:1rem;">{m.get('tensao_v','-')}V</div>
                </div>
                <div style="text-align:center; border-left:1px solid #333; border-right:1px solid #333;">
                    <div style="font-size:0.55rem; color:#8b949e;">POLOS</div>
                    <div style="color:white; font-weight:bold; font-size:1rem;">{m.get('polos','-')}P</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.55rem; color:#8b949e;">FREQ.</div>
                    <div style="color:#8b949e; font-weight:bold; font-size:1rem;">{m.get('frequencia_hz','-')}Hz</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- SEÇÃO EXPANDIDA (ABRE AO CLICAR) ---
        if st.session_state.detalhes_visiveis.get(key_det):
            st.markdown("<div style='background:rgba(0,10,20,0.9); border:1px solid #00ffff44; border-radius:0 0 12px 12px; padding:20px; margin-top:-45px; margin-bottom:40px;'>", unsafe_allow_html=True)
            
            # Aba de Ligações Dinâmicas
            render_esquemas_completos(m)

            # Abas de Dados do CSV
            t_bobina, t_mecanica = st.tabs(["🌀 BOBINAGEM", "⚙️ MECÂNICA"])
            with t_bobina:
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("PRINCIPAL")
                    render_dado("Passo", limpar_passo(m.get("passo_principal")))
                    render_dado("Fio", m.get("bitola_fio_principal"))
                    render_dado("Espiras", m.get("espiras_principal"))
                with c2:
                    st.caption("AUXILIAR")
                    render_dado("Passo", limpar_passo(m.get("passo_auxiliar")))
                    render_dado("Fio", m.get("bitola_fio_auxiliar"))
                    render_dado("Espiras", m.get("espiras_auxiliar"))
                render_dado("Ligação Interna", m.get("ligacao_interna"), highlight=True)

            with t_mecanica:
                c1, c2 = st.columns(2)
                with c1:
                    render_dado("Rolamento Dianteiro", m.get("rolamento_dianteiro"))
                    render_dado("Rolamento Traseiro", m.get("rolamento_traseiro"))
                with c2:
                    render_dado("Comprimento Pacote", m.get("comprimento_pacote_mm"), "mm")
                    render_dado("Nº Ranhuras", m.get("numero_ranhuras"))
            
            st.markdown("</div>", unsafe_allow_html=True)

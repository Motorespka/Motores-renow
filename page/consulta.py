import streamlit as st
import re

# =================================================================
# 1. FUNÇÕES DE FORMATAÇÃO E SUPORTE
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
            <div style="font-size:0.65rem; color:#8b949e; text-transform:uppercase;">{label}</div>
            <div style="font-size:0.95rem; color:white; font-family:monospace; font-weight:bold;">
            {val} <span style="color:{color}; font-size:0.75rem;">{unidade}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# =================================================================
# 2. LÓGICA DE LIGAÇÃO (MONO/TRI E CABOS)
# =================================================================

def render_esquema_detalhado(motor):
    fases = str(motor.get("fases", "")).lower()
    tensao_raw = str(motor.get("tensao_v", ""))
    tensoes = [t.strip() for t in tensao_raw.split('/') if t.strip()]
    
    # Mapeamento técnico de cabos
    mapa = [
        {"n": "1", "cor": "Azul", "sigla": "U1", "hex": "#4d4dff"},
        {"n": "2", "cor": "Branco", "sigla": "V1", "hex": "#ffffff"},
        {"n": "3", "cor": "Laranja", "sigla": "W1", "hex": "#ff8c00"},
        {"n": "4", "cor": "Amarelo", "sigla": "U2", "hex": "#ffff00"},
        {"n": "5", "cor": "Preto", "sigla": "V2", "hex": "#555555"},
        {"n": "6", "cor": "Vermelho", "sigla": "W2", "hex": "#ff4d4d"},
        {"n": "10", "cor": "B. Amarelo", "sigla": "U6", "hex": "#ffffcc"},
        {"n": "11", "cor": "B. Preto", "sigla": "V6", "hex": "#cccccc"},
        {"n": "12", "cor": "B. Vermelho", "sigla": "W6", "hex": "#ffcccc"},
    ]

    st.markdown("### 🔌 Esquema de Ligação")
    
    # Tabela de referência de cores
    cols = st.columns(3)
    max_cabos = 12 if "trif" in fases else 6
    for i, item in enumerate([m for m in mapa if int(m['n']) <= max_cabos]):
        with cols[i % 3]:
            st.markdown(f"<small><span style='color:{item['hex']}'>●</span> <b>{item['n']}</b>: {item['cor']} ({item['sigla']})</small>", unsafe_allow_html=True)

    st.divider()

    # Diferenciação Mono vs Tri
    if "mono" in fases:
        aba1, aba2 = st.tabs(["5 Cabos", "6 Cabos"])
        with aba1:
            st.code("Sentido Horário: L1(1,5) + L2(4) | Unir: 2+3\nAnti-Horário: L1(1,4) + L2(5) | Unir: 2+3")
        with aba2:
            st.code("110V/127V: L1(1,3,5) + L2(2,4,6)\n220V/254V: L1(1) + L2(4) | Unir: 2+3+5+6")
    else:
        # Trifásico - Gera abas baseadas no número de tensões
        nomes_abas = [f"Ligação {t}V" for t in tensoes]
        if not nomes_abas: nomes_abas = ["Ligação Padrão"]
        
        abas_tri = st.tabs(nomes_abas)
        for idx, t in enumerate(tensoes):
            with abas_tri[idx]:
                if idx == 0: # Menor tensão
                    st.write("**Fechamento Triângulo (∆)**")
                    st.code(f"L1(1,6) | L2(2,4) | L3(3,5)")
                elif idx == 1: # Tensão média
                    st.write("**Fechamento Estrela (Y)**")
                    st.code(f"L1(1) | L2(2) | L3(3) | Unir: 4+5+6")
                else: # Terceira tensão (440V ou 12 cabos)
                    st.write("**Fechamento Série (Y/∆ Alta)**")
                    st.code("Consultar diagrama de 12 cabos no motor.")

# =================================================================
# 3. INTERFACE PRINCIPAL
# =================================================================

def show(supabase):
    # CSS para o Card Grande
    st.markdown("""
        <style>
        div.stButton > button {
            width: 100% !important; min-height: 220px !important;
            background: linear-gradient(135deg, rgba(0,40,60,0.9) 0%, rgba(0,20,30,1) 100%) !important;
            border: 1px solid rgba(0, 255, 255, 0.2) !important;
            border-left: 6px solid #10b981 !important; border-radius: 12px !important;
            margin-bottom: 20px !important; transition: all 0.3s ease !important;
        }
        div.stButton > button:hover { border-color: #00ffff !important; transform: scale(1.01); }
        div.stButton > button p { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 🔍 Central de Motores")
    busca = st.text_input("🔎 Pesquisar...", placeholder="Ex: Weg 2cv 4p")
    
    # Busca dados
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

        # Botão de Clique (Toggle)
        if st.button(" ", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()

        # --- O CARD VISÍVEL (RAIO-X) ---
        # ATENÇÃO: O 'unsafe_allow_html=True' no final deste st.markdown é o que resolve o erro!
        st.markdown(f"""
        <div style="margin-top:-225px; margin-bottom:40px; padding:20px; pointer-events:none; position:relative; z-index:5;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <small style="color:#00ffff; font-family:monospace;">REGISTRO #{id_m}</small>
                    <div style="font-size:1.5rem; color:white; font-weight:bold;">{(m.get('marca') or '---').upper()}</div>
                    <div style="color:#aaa;">{m.get('modelo') or ''}</div>
                </div>
                <div style="background:rgba(16,185,129,0.15); color:#10b981; padding:5px 15px; border-radius:30px; font-size:0.8rem; border:1px solid #10b981;">
                    {str(m.get('fases','')).upper()}
                </div>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px; margin-top:20px; border-top:1px solid rgba(255,255,255,0.1); padding-top:15px;">
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e;">POTÊNCIA</div>
                    <div style="color:#00f2ff; font-weight:bold; font-size:1.1rem;">{m.get('potencia_hp_cv','-')}</div>
                </div>
                <div style="text-align:center; border-left:1px solid #ffffff11; border-right:1px solid #ffffff11;">
                    <div style="font-size:0.6rem; color:#8b949e;">ROTAÇÃO</div>
                    <div style="color:#10b981; font-weight:bold; font-size:1.1rem;">{m.get('rpm_nominal','-')}</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e;">AMPERAGEM</div>
                    <div style="color:#f59e0b; font-weight:bold; font-size:1.1rem;">{m.get('corrente_nominal_a','-')}A</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e;">TENSÃO</div>
                    <div style="color:#a855f7; font-weight:bold; font-size:1rem;">{m.get('tensao_v','-')}V</div>
                </div>
                <div style="text-align:center; border-left:1px solid #ffffff11; border-right:1px solid #ffffff11;">
                    <div style="font-size:0.6rem; color:#8b949e;">POLARIDADE</div>
                    <div style="color:white; font-weight:bold; font-size:1rem;">{m.get('polos','-')} P</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e;">FREQ.</div>
                    <div style="color:#aaa; font-weight:bold; font-size:1rem;">{m.get('frequencia_hz','-')}Hz</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- DETALHES EXPANDIDOS ---
        if st.session_state.detalhes_visiveis.get(key_det):
            st.markdown("<div style='background:rgba(0,20,30,0.95); border:1px solid #00ffff44; border-radius:0 0 12px 12px; padding:20px; margin-top:-40px; margin-bottom:40px;'>", unsafe_allow_html=True)
            
            render_esquema_detalhado(m)

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
                    render_dado("Rolamento Diant.", m.get("rolamento_dianteiro"))
                    render_dado("Rolamento Tras.", m.get("rolamento_traseiro"))
                with c2:
                    render_dado("Pacote", m.get("comprimento_pacote_mm"), "mm")
                    render_dado("Ranhuras", m.get("numero_ranhuras"))
            
            st.markdown("</div>", unsafe_allow_html=True)

import streamlit as st
import re

# =================================================================
# 1. FUNÇÕES DE SUPORTE
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
# 2. TELA PRINCIPAL (CONSULTA)
# =================================================================
def show(supabase):
    # CSS para forçar o botão a ser o fundo do card
    st.markdown("""
        <style>
        div.stButton > button {
            width: 100% !important;
            min-height: 220px !important;
            background: linear-gradient(135deg, rgba(0,40,60,0.9) 0%, rgba(0,15,30,1) 100%) !important;
            border: 1px solid rgba(0, 255, 255, 0.2) !important;
            border-left: 6px solid #10b981 !important;
            border-radius: 12px !important;
            margin-bottom: 20px !important;
            transition: all 0.3s ease !important;
        }
        div.stButton > button:hover { border-color: #00ffff !important; transform: scale(1.01); }
        div.stButton > button p { display: none !important; } /* Esconde o texto original do botão */
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 🔍 Consulta de Motores")
    busca = st.text_input("🔎 Pesquisar...", placeholder="Ex: Weg 2cv 4 polos")

    # Busca no Banco de Dados
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

        # 1. BOTÃO (A camada que recebe o clique)
        if st.button(" ", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()

        # 2. O CARD VISUAL (HUD) - Sobreposto ao botão com margem negativa
        fases = str(m.get('fases','')).upper()
        st.markdown(f"""
        <div style="margin-top:-230px; margin-bottom:50px; padding:20px; pointer-events:none; position:relative; z-index:5;">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <small style="color:#00ffff; font-family:monospace;">ID #{id_m}</small>
                    <div style="font-size:1.5rem; color:white; font-weight:bold; line-height:1.1;">{(m.get('marca') or '---').upper()}</div>
                    <div style="color:#aaa; font-size:0.9rem;">{m.get('modelo') or ''}</div>
                </div>
                <div style="background:rgba(16,185,129,0.2); color:#10b981; padding:4px 12px; border-radius:20px; font-size:0.7rem; font-weight:bold; border:1px solid #10b981;">
                    {fases}
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

        # 3. SEÇÃO EXPANDIDA (ABRE AO CLICAR)
        if st.session_state.detalhes_visiveis.get(key_det):
            st.markdown("<div style='background:rgba(0,10,20,0.9); border:1px solid #00ffff44; border-radius:0 0 12px 12px; padding:20px; margin-top:-50px; margin-bottom:40px;'>", unsafe_allow_html=True)
            
            # --- Tabela de Cabos (Cabo - Cor - Placa) ---
            st.markdown("### 🏷️ Identificação de Cabos")
            st.markdown("""
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; background:rgba(255,255,255,0.05); padding:12px; border-radius:8px; font-size:0.85rem; font-family:monospace;">
                    <div><span style="color:#4d4dff">●</span> 1: AZUL (U1)</div>
                    <div><span style="color:#ffffff">●</span> 2: BRANCO (V1)</div>
                    <div><span style="color:#ff8c00">●</span> 3: LARANJA (W1)</div>
                    <div><span style="color:#ffff00">●</span> 4: AMARELO (U2)</div>
                    <div><span style="color:#888888">●</span> 5: PRETO (V2)</div>
                    <div><span style="color:#ff4d4d">●</span> 6: VERMELHO (W2)</div>
                </div>
            """, unsafe_allow_html=True)

            t_liga, t_bobina, t_mecanica = st.tabs(["🔌 LIGAÇÃO", "🌀 BOBINAGEM", "⚙️ MECÂNICA"])
            
            with t_liga:
                if "MONO" in fases:
                    st.write("**Esquemas Monofásicos:**")
                    st.code("5 Cabos: L1(1,5) L2(4) | Unir: 2,3\n6 Cabos (110V): L1(1,3,5) L2(2,4,6)\n6 Cabos (220V): L1(1) L2(4) | Unir: 2,3,5,6")
                else:
                    st.write("**Esquemas Trifásicos:**")
                    st.code("6 Cabos (∆): L1(1,6) L2(2,4) L3(3,5)\n6 Cabos (Y): L1(1) L2(2) L3(3) | Unir: 4,5,6\n12 Cabos: Consultar Placa (Série/Paralelo)")

            with t_bobina:
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("PRINCIPAL")
                    render_dado("Passo", limpar_passo(m.get("passo_principal")))
                    render_dado("Fio", m.get("bitola_fio_principal"))
                with c2:
                    st.caption("AUXILIAR")
                    render_dado("Passo", limpar_passo(m.get("passo_auxiliar")))
                    render_dado("Fio", m.get("bitola_fio_auxiliar"))
                render_dado("Ligação Interna", m.get("ligacao_interna"), highlight=True)

            with t_mecanica:
                render_dado("Rolamentos", f"{m.get('rolamento_dianteiro')} / {m.get('rolamento_traseiro')}")
                render_dado("Pacote", m.get("comprimento_pacote_mm"), "mm")
            
            st.markdown("</div>", unsafe_allow_html=True)

import streamlit as st
import re

# =================================================================
# 1. FUNÇÕES DE APOIO
# =================================================================
def limpar_passo(passo_raw):
    if not passo_raw: 
        return "---"
    s = str(passo_raw).strip()
    s = re.sub(r"^\d+[\s?:\-]*", "", s)
    return s.replace(":", " ").replace("-", " ").strip()

def render_dado(label, valor, unidade="", highlight=False):
    color = "#00ffff" if not highlight else "#f59e0b"
    val = valor if valor is not None and str(valor).lower() not in ["none", "nan", ""] else "---"
    st.markdown(f"""
        <div style="background: rgba(0,255,255,0.03); border:1px solid rgba(0,255,255,0.1);
        border-radius:6px; padding:10px; margin-bottom:5px;">
            <div style="font-size:0.65rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">{label}</div>
            <div style="font-size:0.95rem; color:white; font-family:monospace; font-weight:bold;">
            {val} <span style="color:{color}; font-size:0.75rem;">{unidade}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# =================================================================
# 2. DETALHES DO MOTOR
# =================================================================
def render_detalhes_motor(m):
    fases = str(m.get('fases') or '').upper()
    
    # Tabulação principal
    t_liga, t_bobina, t_mecanica = st.tabs(["🔌 LIGAÇÕES", "🌀 BOBINAGEM", "⚙️ MECÂNICA"])
    
    with t_liga:
        if "MONO" in fases:
            st.subheader("Esquemas Monofásicos")
            aba_m1, aba_m2 = st.tabs(["5 Cabos", "6 Cabos"])
            with aba_m1:
                st.code("Sentido Horário: L1(1,5) - L2(4) | Unir: 2,3\n"
                        "Sentido Anti-Horário: L1(1,4) - L2(5) | Unir: 2,3", language="text")
            with aba_m2:
                st.code("110V/127V: L1(1,3,5) - L2(2,4,6)\n"
                        "220V/254V: L1(1) - L2(4) | Unir: 2,3,5,6", language="text")
        else:
            st.subheader("Esquemas Trifásicos")
            aba_t1, aba_t2 = st.tabs(["6 Cabos", "12 Cabos"])
            with aba_t1:
                st.code("Triângulo (∆) 220V: L1(1,6) - L2(2,4) - L3(3,5)\n"
                        "Estrela (Y) 380V: L1(1) - L2(2) - L3(3) | Unir: 4,5,6", language="text")
            with aba_t2:
                st.info("Configuração para 4 tensões (220/380/440/760V)")
                st.code("Série/Paralelo: Ver diagrama U1-U6 no motor.", language="text")
    
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
        render_dado("Rolamentos (D/T)", f"{m.get('rolamento_dianteiro') or '-'} / {m.get('rolamento_traseiro') or '-'}")
        render_dado("Comprimento Pacote", m.get("comprimento_pacote_mm"), "mm")
        render_dado("Ranhuras", m.get("numero_ranhuras"))

# =================================================================
# 3. TELA PRINCIPAL
# =================================================================
def show(supabase):
    # CSS compatível
    st.markdown("""
        <style>
        .btn_card { width: 100% !important; min-height: 230px !important;
                    background: linear-gradient(135deg, rgba(0,40,60,0.95) 0%, rgba(0,15,30,1) 100%) !important;
                    border: 1px solid rgba(0,255,255,0.2) !important;
                    border-left: 6px solid #10b981 !important;
                    border-radius: 12px !important; margin-bottom:25px !important;
                    transition: all 0.3s ease !important; display:block !important; }
        .btn_card:hover { border-color:#00ffff !important; transform: translateY(-2px); }
        .btn_card p { display:none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 🔍 Central de Motores")
    busca = st.text_input("🔎 Pesquisar motor...", placeholder="Ex: Weg 2cv 4 polos")
    
    # Consulta banco
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except:
        st.error("Erro ao conectar ao banco.")
        return

    # Busca segura
    if busca:
        q = busca.lower()
        motores = [
            m for m in motores
            if q in f"{m.get('marca') or ''} {m.get('modelo') or ''} {m.get('potencia_hp_cv') or ''}".lower()
        ]

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    # Renderização de cards
    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        btn_key = f"btn_card_{id_m}"

        # BOTÃO PARA MOSTRAR DETALHES
        if st.button(" ", key=btn_key):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.experimental_rerun()

        # CAPA DO CARD
        fases = str(m.get('fases') or '').upper()
        st.markdown(f"""
        <div style="margin-top:-245px; margin-bottom:50px; padding:20px; pointer-events:none; position:relative; z-index:5;">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <small style="color:#00ffff; font-family:monospace; letter-spacing:1px;">ID #{id_m}</small>
                    <div style="font-size:1.5rem; color:white; font-weight:800; line-height:1.1;">{(m.get('marca') or '---').upper()}</div>
                    <div style="color:#aaa; font-size:0.95rem;">{m.get('modelo') or ''}</div>
                </div>
                <div style="background:rgba(16,185,129,0.2); color:#10b981; padding:4px 12px; border-radius:20px; font-size:0.75rem; font-weight:bold; border:1px solid #10b981;">
                    {fases}
                </div>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px; margin-top:22px; border-top:1px solid rgba(255,255,255,0.1); padding-top:18px;">
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

        # DETALHES EXPANDIDOS
        if st.session_state.detalhes_visiveis.get(key_det):
            st.markdown("<div style='background:rgba(0,10,20,0.95); border:1px solid #00ffff44; border-radius:0 0 12px 12px; padding:20px; margin-top:-50px; margin-bottom:40px;'>", unsafe_allow_html=True)
            
            st.markdown("### 🏷️ Identificação de Cabos (Cores e Placas)")
            st.markdown("""
                <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; background:rgba(255,255,255,0.05); padding:15px; border-radius:8px; font-family:monospace; font-size:0.85rem;">
                    <div><span style="color:#4d4dff">●</span> 1: AZUL (U1)</div>
                    <div><span style="color:#ffffff">●</span> 2: BRANCO (V1)</div>
                    <div><span style="color:#ff8c00">●</span> 3: LARANJA (W1)</div>
                    <div><span style="color:#ffff00">●</span> 4: AMARELO (U2)</div>
                    <div><span style="color:#888888">●</span> 5: PRETO (V2)</div>
                    <div><span style="color:#ff4d4d">●</span> 6: VERMELHO (W2)</div>
                </div>
            """, unsafe_allow_html=True)

            render_detalhes_motor(m)
            st.markdown("</div>", unsafe_allow_html=True)

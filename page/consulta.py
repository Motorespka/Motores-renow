import streamlit as st
import re

# =============================
# FUNÇÕES AUXILIARES
# =============================
def limpar_passo(passo_raw):
    if not passo_raw: 
        return "---"
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
            <div style="font-size:0.95rem; color:white; font-family:monospace; font-weight:bold;">
            {val} <span style="color:{color}; font-size:0.75rem;">{unidade}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# NOVA FUNÇÃO DE LÓGICA DE LIGAÇÃO INTEGRADA
def obter_configuracoes_ligacao(m):
    fases = 3 if "TRI" in str(m.get('fases', '')).upper() else 1
    tensao_v_str = str(m.get('tensao_v', ''))
    
    # Simplificação da lógica que a IA te mandou para caber no card
    if fases == 3:
        if "220" in tensao_v_str and "380" in tensao_v_str:
            return "220V: Triângulo (Δ) | 380V: Estrela (Y)"
        return f"Consulte placa para {tensao_v_str}"
    else:
        return "Monofásico: Verifique série/paralelo conforme voltagem."

# =============================
# TELA PRINCIPAL
# =============================
def show(supabase):
    # Removido set_page_config daqui para evitar erro se rodar em multiplas paginas
    
    # SIDEBAR
    st.sidebar.title("Menu Moto-Renow")
    pagina = st.sidebar.radio("Escolha a página:", ["Consulta", "Cadastro"])
    st.session_state['pagina'] = pagina 

    # BUSCA
    st.title("🔍 Central de Motores")
    busca = st.text_input("🔎 Pesquisar motor...", placeholder="Ex: Weg 2cv 4 polos")
    
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except:
        st.error("Erro ao conectar ao banco.")
        return

    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in f"{m.get('marca','')} {m.get('modelo','')} {m.get('potencia_hp_cv','')}".lower()]

    if not motores:
        st.info("Nenhum motor encontrado.")
        return

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    # RENDERIZAÇÃO
    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"

        # Ajuste no botão invisível (posicionamento para não quebrar o layout)
        if st.button(f"Abrir/Fechar {m.get('marca','')} {m.get('modelo','')}", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun() # CORRIGIDO: de experimental_rerun para rerun

        # CARD VISUAL
        card_html = f"""
        <div style="
            background: linear-gradient(145deg,#081018,#05070d);
            border: 2px solid #00ffff33;
            border-radius:18px; padding:25px;
            box-shadow:0 0 30px #00ffff22; margin:10px auto;
            max-width:600px; text-align:center;">
            <div style="font-size:1.5rem; color:#00ffff; font-weight:800;">{m.get('marca','---').upper()}</div>
            <div style="color:#aaa; font-size:1rem; margin-bottom:10px;">{m.get('modelo','-')}</div>
            <div style="display:flex; justify-content:space-around; margin-top:15px; font-weight:bold;">
                <div style="color:#00ffff;">{m.get('potencia_hp_cv','-')} HP</div>
                <div style="color:#10b981;">{m.get('rpm_nominal','-')} RPM</div>
                <div style="color:#f59e0b;">{m.get('corrente_nominal_a','-')} A</div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        # DETALHES
        if st.session_state.detalhes_visiveis.get(key_det):
            with st.container():
                st.markdown("<div style='background:rgba(0,10,20,0.95); border:1px solid #00ffff44; border-radius:12px; padding:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
                st.markdown("### 🛠️ Detalhes Técnicos")
                
                t_liga, t_bobina, t_mecanica = st.tabs(["🔌 Ligações", "🌀 Bobinagem", "⚙️ Mecânica"])

                with t_liga:
                    info_ligacao = obter_configuracoes_ligacao(m)
                    st.info(info_ligacao)
                    st.caption(f"Fases: {m.get('fases','-')} | Tensão: {m.get('tensao_v','-')}")

                with t_bobina:
                    col1, col2 = st.columns(2)
                    with col1:
                        render_dado("Passo", limpar_passo(m.get("passo_principal")))
                    with col2:
                        render_dado("Fio", m.get("bitola_fio_principal"))

                with t_mecanica:
                    render_dado("Rolamento Diant.", m.get('rolamento_dianteiro','-'))
                    render_dado("Rolamento Tras.", m.get('rolamento_traseiro','-'))

                st.markdown("</div>", unsafe_allow_html=True)

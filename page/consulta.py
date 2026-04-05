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

# =============================
# TELA PRINCIPAL
# =============================
def show(supabase):
    st.set_page_config(page_title="Consulta Motores", layout="wide")
    
    # =============================
    # SIDEBAR
    # =============================
    st.sidebar.title("Menu Moto-Renow")
    pagina = st.sidebar.radio("Escolha a página:", ["Consulta", "Cadastro"])
    
    st.session_state['pagina'] = pagina  # mantém o estado
    
    # =============================
    # BUSCA DE MOTORES
    # =============================
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

    # =============================
    # RENDERIZAÇÃO DE CARDS
    # =============================
    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"

        # BOTÃO INVISÍVEL PARA TOGGLE DO CARD
        if st.button("", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.experimental_rerun()

        # CARD GRANDE CLICÁVEL
        card_html = f"""
        <div style="
            background: linear-gradient(145deg,#081018,#05070d);
            border: 2px solid #00ffff33;
            border-radius:18px; padding:25px;
            box-shadow:0 0 30px #00ffff22; margin:20px auto;
            max-width:600px; text-align:center; cursor:pointer;
            transition: 0.3s; 
        " 
        onmouseover="this.style.boxShadow='0 0 60px #00ffff44'" 
        onmouseout="this.style.boxShadow='0 0 30px #00ffff22'">
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

        # =============================
        # DETALHES EXPANDIDOS
        # =============================
        if st.session_state.detalhes_visiveis.get(key_det):
            st.markdown("<div style='background:rgba(0,10,20,0.95); border:1px solid #00ffff44; border-radius:12px; padding:20px; margin-bottom:40px;'>", unsafe_allow_html=True)
            st.markdown("### 🛠️ Detalhes do Motor")

            fases = str(m.get('fases','')).upper()
            t_liga, t_bobina, t_mecanica = st.tabs(["🔌 Ligações", "🌀 Bobinagem", "⚙️ Mecânica"])

            with t_liga:
                if "MONO" in fases:
                    st.code("5 e 6 cabos monofásicos...", language="text")
                else:
                    st.code("6 e 12 cabos trifásicos...", language="text")

            with t_bobina:
                render_dado("Passo Principal", limpar_passo(m.get("passo_principal")))
                render_dado("Fio Principal", m.get("bitola_fio_principal"))

            with t_mecanica:
                render_dado("Rolamentos", f"{m.get('rolamento_dianteiro','-')} / {m.get('rolamento_traseiro','-')}")

            st.markdown("</div>", unsafe_allow_html=True)

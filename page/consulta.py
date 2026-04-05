import streamlit as st
import importlib
import re
import os

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS
# =================================================================
try:
    from core.engenheiro_ia import engenheiro_busca_v4
    from core.aprendizado import aprender
    from core.ligacao_motor import gerar_ligacoes_motor 
    from page import diagnostico 
except Exception as e:
    pass 

# =================================================================
# 2. FUNÇÕES DE SUPORTE
# =================================================================
def listar_motores(supabase):
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).limit(1000).execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Erro ao listar motores: {e}")
        return []

def excluir_motor(supabase, id_motor):
    try:
        supabase.table("motores").delete().eq("id", id_motor).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir motor: {e}")
        return False

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
            <div style="font-size:1rem; color:white; font-family:monospace; font-weight:bold;">
            {val} <span style="color:{color}; font-size:0.8rem;">{unidade}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# =================================================================
# 3. TELA PRINCIPAL (SHOW)
# =================================================================
def show(supabase):
    # CSS para forçar o botão a ser o card grande
    st.markdown("""
        <style>
        div.stButton > button {
            width: 100% !important;
            min-height: 170px !important;
            background: linear-gradient(135deg, rgba(0,45,65,0.9) 0%, rgba(0,25,40,1) 100%) !important;
            border: 1px solid rgba(0, 255, 255, 0.3) !important;
            border-left: 6px solid #10b981 !important;
            border-radius: 12px !important;
            padding: 0px !important;
            transition: all 0.2s ease !important;
        }
        div.stButton > button:hover { border-color: #00ffff !important; }
        div.stButton > button p { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 🔍 Consulta de Motores")  

    busca = st.text_input("🧠 Engenheiro IA / Busca", placeholder="Ex: weg 2cv 4 polos")  
    motores_db = listar_motores(supabase)  

    # Lógica de Busca IA ou Simples
    if busca:  
        try:
            motores, sugestoes = engenheiro_busca_v4(motores_db, busca)
        except:
            q = busca.lower()
            motores = [m for m in motores_db if q in str(m).lower()]
    else:  
        motores = motores_db  

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    st.caption(f"Motores encontrados: {len(motores)}")  

    # Loop de Renderização
    for m in motores:  
        id_m = m.get("id")  
        key_det = f"vis_{id_m}"  

        # 1. O BOTÃO (Invisível mas ocupa o espaço do card)
        if st.button(" ", key=f"btn_m_{id_m}", use_container_width=True):  
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)  
            st.rerun()  

        # 2. O DESENHO DO CARD (HTML RENDERIZADO)
        st.markdown(f"""  
        <div style="margin-top:-165px; margin-bottom:20px; padding:18px; pointer-events:none; position:relative; z-index:5;">  
            <small style="color:#00ffff; font-family:monospace;">ID: #{id_m}</small>  
            <div style="font-size:1.35rem; color:white; font-weight:bold;">
                {(m.get('marca') or '---').upper()} <span style="color:#aaa; font-size:1.1rem;">{m.get('modelo') or ''}</span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-top:15px; border-top:1px solid rgba(255,255,255,0.1); padding-top:10px;">  
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e;">Potência</div>
                    <div style="color:#00f2ff; font-weight:bold;">{m.get('potencia_hp_cv','-')}</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e;">Rotação</div>
                    <div style="color:#10b981; font-weight:bold;">{m.get('rpm_nominal','-')}</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e;">Tensão</div>
                    <div style="color:#a855f7; font-weight:bold;">{m.get('tensao_v','-')}V</div>
                </div>
            </div>
        </div>  
        """, unsafe_allow_html=True)  

        # 3. CONTEÚDO EXPANSÍVEL (ABAS DO CSV)
        if st.session_state.detalhes_visiveis.get(key_det):  
            with st.container():
                st.markdown("<div style='background:rgba(0,20,30,0.95); padding:15px; border-radius:0 0 10px 10px; margin-top:-20px; border:1px solid #00ffff44;'>", unsafe_allow_html=True)
                
                t1, t2, t3 = st.tabs(["📋 CONEXÃO", "🌀 BOBINAGEM", "⚙️ MECÂNICA"])
                with t1:
                    st.code("1:AZ | 2:BR | 3:LA | 4:AM | 5:PR | 6:VM")
                    render_dado("Amperagem", m.get("corrente_nominal_a"), "A")
                    render_dado("Capacitores", f"{m.get('capacitor_permanente') or ''} / {m.get('capacitor_partida') or ''}")
                with t2:
                    col1, col2 = st.columns(2)
                    with col1:
                        render_dado("Passo (P)", limpar_passo(m.get("passo_principal")))
                        render_dado("Fio (P)", m.get("bitola_fio_principal"))
                    with col2:
                        render_dado("Passo (A)", limpar_passo(m.get("passo_auxiliar")))
                        render_dado("Fio (A)", m.get("bitola_fio_auxiliar"))
                    render_dado("Ligação Interna", m.get("ligacao_interna"), highlight=True)
                with t3:
                    render_dado("Rolamentos", f"{m.get('rolamento_dianteiro')} / {m.get('rolamento_traseiro')}")
                    render_dado("Pacote", m.get("comprimento_pacote_mm"), "mm")
                
                st.markdown("</div>", unsafe_allow_html=True)

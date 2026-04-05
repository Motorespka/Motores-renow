import streamlit as st
import importlib
import re
import os

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS (PROTEGIDAS)
# =================================================================
try:
    from core.engenheiro_ia import engenheiro_busca_v4
    from core.aprendizado import aprender
    from core.ligacao_motor import gerar_ligacoes_motor 
    from page import diagnostico 
except Exception as e:
    pass # Falha silenciosa para não quebrar a tela se o arquivo não existir

# =================================================================
# 2. BANCO SUPABASE E BUSCA
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

def buscar_motores(motores_db, search_query):
    if not search_query: return motores_db
    q = search_query.strip().lower()  
    return [m for m in motores_db if q in f"{m.get('marca','')} {m.get('modelo','')} {m.get('potencia_hp_cv','')}".lower()]

# =================================================================
# 3. FORMATAÇÃO TÉCNICA
# =================================================================
def limpar_passo(passo_raw):
    if not passo_raw: return "---"
    s = str(passo_raw).strip()
    s = re.sub(r"^[1][\s?:\-]*", "", s) # Limpa o '1:' do banco
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
# 4. TELA PRINCIPAL
# =================================================================
def show(supabase):
    st.markdown("## 🔍 Consulta de Motores")  

    # --- CSS MESTRE PARA O CARD GRANDE CLICÁVEL ---
    st.markdown("""
        <style>
        div.stButton { margin-bottom: -10px !important; }
        div.stButton > button {
            width: 100% !important;
            min-height: 170px !important;
            background: linear-gradient(135deg, rgba(0,45,65,0.9) 0%, rgba(0,25,40,1) 100%) !important;
            border: 1px solid rgba(0, 255, 255, 0.3) !important;
            border-left: 6px solid #10b981 !important;
            border-radius: 12px !important;
            padding: 0px !important;
            display: flex !important;
            flex-direction: column !important;
            transition: all 0.2s ease !important;
        }
        div.stButton > button:hover {
            border-color: #00ffff !important;
            background: rgba(0, 60, 80, 1) !important;
        }
        div.stButton > button p { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}
    if "abrir_edit" not in st.session_state:
        st.session_state.abrir_edit = False

    # Lógica do Editor de Motor
    if st.session_state.abrir_edit and st.session_state.get("motor_editando"):
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Voltar"):
                st.session_state.abrir_edit = False
                st.rerun()
            return
        except: st.error("Módulo de edição não encontrado.")

    # --- CAMPO DE BUSCA & IA ---
    busca = st.text_input("🧠 Engenheiro IA", placeholder="Ex: weg 2cv 4 polos 220v")  
    motores_db = listar_motores(supabase)  

    sugestoes = []  
    if busca:  
        try:
            motores, sugestoes = engenheiro_busca_v4(motores_db, busca)
        except:
            motores = buscar_motores(motores_db, busca)
    else:  
        motores = motores_db  

    if sugestoes:
        cols = st.columns(len(sugestoes))
        for i, s in enumerate(sugestoes):
            if cols[i].button(f"💡 {s}", key=f"sug_{i}"):
                st.session_state["busca_auto"] = s
                st.rerun()  

    st.caption(f"Motores na base: {len(motores)}")  

    # --- RENDERIZAÇÃO DOS CARDS ---
    for m in motores:  
        id_m = m.get("id")  
        key_det = f"vis_{id_m}"  

        # 1. BOTÃO INVISÍVEL (ESTRUTURA DO CARD)
        if st.button(" ", key=f"btn_m_{id_m}", use_container_width=True):  
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)  
            st.rerun()  

        # 2. VISUAL HUD INJETADO POR CIMA DO BOTÃO
        st.markdown(f"""  
        <div style="margin-top:-165px; margin-bottom:20px; padding:18px; pointer-events:none; position:relative; z-index:5;">  
            <small style="color:#00ffff; font-family:monospace; letter-spacing: 2px;">REGISTRO TÉCNICO ID: #{id_m}</small>  
            <div style="font-size:1.35rem; color:white; font-weight:bold; margin-top:5px;">
                {(m.get('marca') or '---').upper()} <span style="color:#aaa; font-weight:300; font-size:1.1rem;">{m.get('modelo') or ''}</span>
            </div>
            <div style="font-size:0.7rem; color:#8b949e;">MOTORES {str(m.get('fases','')).upper()}</div>
            
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-top:15px; border-top:1px solid rgba(255,255,255,0.1); padding-top:12px;">  
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e; text-transform:uppercase;">Potência</div>
                    <div style="color:#00f2ff; font-weight:bold; font-size:1.05rem;">{m.get('potencia_hp_cv','-')}</div>
                </div>
                <div style="text-align:center; border-left:1px solid rgba(255,255,255,0.1); border-right:1px solid rgba(255,255,255,0.1);">
                    <div style="font-size:0.6rem; color:#8b949e; text-transform:uppercase;">Rotação</div>
                    <div style="color:#10b981; font-weight:bold; font-size:1.05rem;">{m.get('rpm_nominal','-')} <small style="font-size:0.6rem;">RPM</small></div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e; text-transform:uppercase;">Tensão</div>
                    <div style="color:#a855f7; font-weight:bold; font-size:1.05rem;">{m.get('tensao_v','-')}V</div>
                </div>
            </div>
        </div>  
        """, unsafe_allow_html=True)  

        # --- 3. ABA EXPANDIDA COM DADOS COMPLETOS E IA ---
        if st.session_state.detalhes_visiveis.get(key_det):  
            
            # IA Aprendizado em background
            if busca: 
                try: aprender(busca, m)
                except: pass

            st.markdown("<div style='background: rgba(0,25,35,0.98); border: 1px solid #00ffff44; border-radius: 0 0 12px 12px; padding: 20px; margin-top: -20px; margin-bottom: 30px;'>", unsafe_allow_html=True)
            
            # --- Diagnóstico e Ações ---
            with st.expander("🧠 Diagnóstico Rápido e Dicas"):
                try: diagnostico.show() # Chama o seu módulo diagnostico.py
                except: st.write("Módulo de diagnóstico indisponível no momento.")
            
            c_ed, c_del = st.columns(2)
            if c_ed.button("✏️ EDITAR", key=f"ed_{id_m}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if c_del.button("🗑️ EXCLUIR", key=f"ex_{id_m}", use_container_width=True):
                if excluir_motor(supabase, id_m): st.rerun()

            # --- Abas de Dados (CSV) ---
            t1, t2, t3 = st.tabs(["📋 CONEXÃO", "🌀 BOBINAGEM", "⚙️ MECÂNICA"])
            
            with t1:
                st.markdown("<small style='color:#8b949e;'>LIGAÇÃO DE CABOS</small>", unsafe_allow_html=True)
                st.code("1:AZ | 2:BR | 3:LA | 4:AM | 5:PR | 6:VM", language="")
                render_dado("Amperagem Nominal", m.get("corrente_nominal_a"), "A")
                render_dado("Capacitores", f"{m.get('capacitor_permanente') or ''} / {m.get('capacitor_partida') or ''}")

            with t2:
                col_p, col_a = st.columns(2)
                with col_p:
                    render_dado("Passo (P)", limpar_passo(m.get("passo_principal")))
                    render_dado("Fio (P)", m.get("bitola_fio_principal"))
                    render_dado("Espiras (P)", m.get("espiras_principal"))
                with col_a:
                    render_dado("Passo (A)", limpar_passo(m.get("passo_auxiliar")))
                    render_dado("Fio (A)", m.get("bitola_fio_auxiliar"))
                    render_dado("Espiras (A)", m.get("espiras_auxiliar"))
                render_dado("Ligação Interna", m.get("ligacao_interna"), highlight=True)

            with t3:
                render_dado("Ranhuras", m.get("numero_ranhuras"))
                render_dado("Pacote (mm)", m.get("comprimento_pacote_mm"))
                render_dado("Rolamentos", f"{m.get('rolamento_dianteiro')} / {m.get('rolamento_traseiro')}")
            
            if m.get('observacoes'):
                st.divider()
                st.markdown(f"**Observações:** {m.get('observacoes')}")

            st.markdown("</div>", unsafe_allow_html=True)

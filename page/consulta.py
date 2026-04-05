import streamlit as st
import importlib
import re

# ------------------------------
# BANCO SUPABASE
# ------------------------------
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

# ------------------------------
# BUSCA
# ------------------------------
def buscar_motores(motores_db, search_query):
    if not search_query: return motores_db
    q = search_query.strip().lower()
    return [m for m in motores_db if q in f"{m.get('marca','')} {m.get('modelo','')} {m.get('potencia_hp_cv','')}".lower()]

# ------------------------------
# FORMATAÇÃO TÉCNICA
# ------------------------------
def limpar_passo(passo_raw):
    if not passo_raw: return "---"
    s = str(passo_raw).strip()
    s = re.sub(r"^[1][\s?:\-]*", "", s)
    return s.replace(":", " ").replace("-", " ").strip()

def render_dado(label, valor, unidade="", highlight=False):
    color = "#00ffff" if not highlight else "#f59e0b"
    val = valor if valor and str(valor).lower() not in ["none", "nan", ""] else "---"
    st.markdown(f"""
        <div style="background: rgba(0, 255, 255, 0.03); border: 1px solid rgba(0, 255, 255, 0.1); border-radius: 6px; padding: 10px; margin-bottom: 5px;">
            <div style="font-size: 0.65rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
            <div style="font-size: 1rem; color: white; font-family: monospace; font-weight: bold;">{val} <span style="color: {color}; font-size: 0.8rem;">{unidade}</span></div>
        </div>
    """, unsafe_allow_html=True)

# ------------------------------
# TELA PRINCIPAL
# ------------------------------
def show(supabase):
    st.markdown("## 🔍 Consulta de Motores")

    # CSS MESTRE: Faz o botão ser uma película invisível sobre o card
    st.markdown("""
        <style>
        .stButton > button {
            width: 100% !important;
            height: 180px !important; /* Altura total do card */
            background: transparent !important;
            color: transparent !important;
            border: none !important;
            position: absolute !important;
            z-index: 99 !important;
            margin-top: -180px !important;
        }
        .stButton > button:active, .stButton > button:focus {
            background: rgba(0, 255, 255, 0.1) !important;
            border: none !important;
            box-shadow: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    if "detalhes_visiveis" not in st.session_state: st.session_state.detalhes_visiveis = {}
    if "motor_editando" not in st.session_state: st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state: st.session_state.abrir_edit = False

    if st.session_state.abrir_edit and st.session_state.motor_editando:
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Voltar", key="voltar_lista"):
                st.session_state.abrir_edit = False
                st.rerun()
            return
        except: st.error("Erro ao carregar editor.")

    search_query = st.text_input("🔎 Pesquisar", placeholder="Ex: WEG 1/2 cv...")
    
    motores_db = listar_motores(supabase)
    motores = buscar_motores(motores_db, search_query)
    
    st.caption(f"Registros encontrados: {len(motores)}")

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        
        # --- O CARD VISUAL (GRANDE E LIMPO) ---
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(0,40,60,0.7) 0%, rgba(0,20,30,0.8) 100%);
                border: 1px solid rgba(0, 255, 255, 0.2);
                border-left: 6px solid #10b981;
                border-radius: 12px;
                padding: 20px;
                height: 180px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                position: relative;
                margin-bottom: 10px;
            ">
                <div>
                    <small style="color: #00ffff; font-family: monospace; letter-spacing: 2px;">REGISTRO TÉCNICO ID: #{id_m}</small>
                    <div style="font-size: 1.5rem; color: white; font-weight: bold; margin-top: 5px;">
                        {(m.get('marca') or '---').upper()} 
                        <span style="font-weight: 300; color: #8b949e; font-size: 1.2rem;">{m.get('modelo') or ''}</span>
                    </div>
                    <div style="font-size: 0.75rem; color: #8b949e; margin-top: 2px;">MOTORES {str(m.get('fases','')).upper()}</div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                    <div style="text-align: center;">
                        <div style="font-size: 0.6rem; color: #8b949e; text-transform: uppercase;">Potência</div>
                        <div style="font-size: 1.1rem; font-weight: bold; color: #00f2ff;">{m.get('potencia_hp_cv','-')}</div>
                    </div>
                    <div style="text-align: center; border-left: 1px solid rgba(255,255,255,0.1); border-right: 1px solid rgba(255,255,255,0.1);">
                        <div style="font-size: 0.6rem; color: #8b949e; text-transform: uppercase;">Rotação</div>
                        <div style="font-size: 1.1rem; font-weight: bold; color: #10b981;">{m.get('rpm_nominal','-')} <small style="font-size:0.6rem;">RPM</small></div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.6rem; color: #8b949e; text-transform: uppercase;">Tensão</div>
                        <div style="font-size: 1.1rem; font-weight: bold; color: #a855f7;">{m.get('tensao_v','-')}V</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # O BOTÃO INVISÍVEL (ESTICA SOBRE O CARD)
        if st.button("", key=f"click_{id_m}", use_container_width=True):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()

        # ESPAÇADOR
        st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)

        # --- CONTEÚDO AO ABRIR ---
        if st.session_state.detalhes_visiveis.get(key_det):
            st.markdown("<div style='background: rgba(0,30,45,0.95); border: 1px solid #00ffff44; border-radius: 8px; padding: 20px; margin-top: -15px; margin-bottom: 30px;'>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("✏️ EDITAR", key=f"ed_{id_m}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if c2.button("🗑️ EXCLUIR", key=f"ex_{id_m}", use_container_width=True):
                if excluir_motor(supabase, id_m): st.rerun()

            t1, t2, t3 = st.tabs(["📋 CONEXÃO", "🌀 REBOBINAGEM", "⚙️ MECÂNICA"])
            with t1:
                st.markdown("<p style='font-size:0.7rem; color:#00ffff;'>LIGAÇÃO DE CABOS</p>", unsafe_allow_html=True)
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
                render_dado("Rolamentos", f"D: {m.get('rolamento_dianteiro')} / T: {m.get('rolamento_traseiro')}")

            st.markdown("</div>", unsafe_allow_html=True)


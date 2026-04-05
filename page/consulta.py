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

    # CSS REFORÇADO PARA TRANSFORMAR O BOTÃO NO CARD
    st.markdown("""
        <style>
        /* Estiliza o botão para ele ter a aparência do card */
        div.stButton > button {
            background: linear-gradient(135deg, rgba(0,45,65,0.8) 0%, rgba(0,25,40,0.9) 100%) !important;
            border: 1px solid rgba(0, 255, 255, 0.3) !important;
            border-left: 6px solid #10b981 !important;
            border-radius: 12px !important;
            padding: 0px !important; /* Tiramos o padding do botão para o HTML interno mandar */
            width: 100% !important;
            height: auto !important;
            min-height: 160px !important;
            transition: all 0.2s ease !important;
            display: block !important;
        }

        div.stButton > button:hover {
            border-color: #00ffff !important;
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.1) !important;
        }
        
        /* Remove o efeito cinza padrão do Streamlit ao clicar */
        div.stButton > button:active {
            background: rgba(0, 60, 85, 0.9) !important;
        }

        /* Container interno para organizar o texto dentro do botão */
        .inner-card {
            padding: 18px;
            text-align: left;
            width: 100%;
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
            if st.button("🔙 Voltar", key="btn_voltar"):
                st.session_state.abrir_edit = False
                st.rerun()
            return
        except: st.error("Erro ao carregar editor.")

    search_query = st.text_input("🔎 Pesquisar", placeholder="Ex: WEG 2cv...")
    
    motores_db = listar_motores(supabase)
    motores = buscar_motores(motores_db, search_query)
    
    st.caption(f"Motores encontrados: {len(motores)}")

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        
        marca = (m.get('marca') or '---').upper()
        modelo = m.get('modelo') or ''
        fases = str(m.get('fases','')).upper()
        pot = m.get('potencia_hp_cv','-')
        rpm = m.get('rpm_nominal','-')
        tensao = m.get('tensao_v','-')

        # Criamos o HTML do conteúdo
        # IMPORTANTE: O clique agora é no botão que envolve este conteúdo
        card_html = f"""
            <div class="inner-card">
                <small style="color: #00ffff; font-family: monospace; letter-spacing: 2px;">REGISTRO TÉCNICO ID: #{id_m}</small>
                <div style="font-size: 1.3rem; color: white; font-weight: bold; margin-top: 4px;">
                    {marca} <span style="font-weight: 300; color: #aaa; font-size: 1.1rem;">{modelo}</span>
                </div>
                <div style="font-size: 0.7rem; color: #8b949e; margin-top: 2px;">MOTORES {fases}</div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; margin-top: 12px;">
                    <div style="text-align: center;">
                        <div style="font-size: 0.55rem; color: #8b949e; text-transform: uppercase;">Potência</div>
                        <div style="font-size: 1rem; font-weight: bold; color: #00f2ff;">{pot}</div>
                    </div>
                    <div style="text-align: center; border-left: 1px solid rgba(255,255,255,0.1); border-right: 1px solid rgba(255,255,255,0.1);">
                        <div style="font-size: 0.55rem; color: #8b949e; text-transform: uppercase;">Rotação</div>
                        <div style="font-size: 1rem; font-weight: bold; color: #10b981;">{rpm} <span style="font-size:0.6rem;">RPM</span></div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.55rem; color: #8b949e; text-transform: uppercase;">Tensão</div>
                        <div style="font-size: 1rem; font-weight: bold; color: #a855f7;">{tensao}V</div>
                    </div>
                </div>
            </div>
        """

        # BOTÃO ÚNICO (O card inteiro)
        # O truque aqui é usar markdown para colocar o visual e o botão no mesmo lugar
        if st.button(f"Clique para ver detalhes do motor {id_m}", key=f"btn_full_{id_m}", use_container_width=True):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()
            
        # Injetamos o visual por cima do botão
        st.markdown(f"""
            <div style="margin-top: -175px; pointer-events: none; position: relative; z-index: 5;">
                {card_html}
            </div>
            <div style="margin-top: 25px;"></div>
        """, unsafe_allow_html=True)

        # --- SEÇÃO DETALHADA ---
        if st.session_state.detalhes_visiveis.get(key_det):
            st.markdown("<div style='background: rgba(0,20,30,0.95); border: 1px solid #00ffff44; border-radius: 8px; padding: 18px; margin-bottom: 25px;'>", unsafe_allow_html=True)
            
            c_edit, c_del = st.columns(2)
            if c_edit.button("✏️ EDITAR", key=f"ed_{id_m}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if c_del.button("🗑️ EXCLUIR", key=f"ex_{id_m}", use_container_width=True):
                if excluir_motor(supabase, id_m): st.rerun()

            tab1, tab2, tab3 = st.tabs(["📋 CONEXÃO", "🌀 BOBINAGEM", "⚙️ MECÂNICA"])
            with tab1:
                st.markdown("<small style='color:#8b949e;'>LIGAÇÃO DE CABOS (PADRÃO)</small>", unsafe_allow_html=True)
                st.code("1:AZ | 2:BR | 3:LA | 4:AM | 5:PR | 6:VM", language="")
                render_dado("Amperagem Nominal", m.get("corrente_nominal_a"), "A")
                render_dado("Capacitores", f"{m.get('capacitor_permanente') or ''} / {m.get('capacitor_partida') or ''}")

            with tab2:
                col_p, col_a = st.columns(2)
                with col_p:
                    render_dado("Passo (P)", limpar_passo(m.get("passo_principal")))
                    render_dado("Fio (P)", m.get("bitola_fio_principal"))
                with col_a:
                    render_dado("Passo (A)", limpar_passo(m.get("passo_auxiliar")))
                    render_dado("Fio (A)", m.get("bitola_fio_auxiliar"))
                render_dado("Ligação Interna", m.get("ligacao_interna"), highlight=True)

            with tab3:
                render_dado("Ranhuras", m.get("numero_ranhuras"))
                render_dado("Pacote (mm)", m.get("comprimento_pacote_mm"))
                render_dado("Rolamentos", f"D: {m.get('rolamento_dianteiro')} / T: {m.get('rolamento_traseiro')}")

            st.markdown("</div>", unsafe_allow_html=True)


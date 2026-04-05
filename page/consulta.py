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

    # CSS para o Botão de Sobreposição Invisível
    st.markdown("""
        <style>
        .stButton > button {
            width: 100% !important;
            height: 160px !important; /* Altura exata do card */
            background-color: transparent !important;
            color: transparent !important;
            border: none !important;
            position: absolute !important;
            z-index: 10 !important;
            cursor: pointer !important;
        }
        .stButton > button:hover {
            border: none !important;
            background-color: rgba(0, 255, 255, 0.05) !important;
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
            if st.button("🔙 Voltar", key="voltar_btn"):
                st.session_state.abrir_edit = False
                st.rerun()
            return
        except: st.error("Erro no editor.")

    search_query = st.text_input("🔎 Pesquisar", placeholder="Marca, modelo...")
    
    motores_db = listar_motores(supabase)
    motores = buscar_motores(motores_db, search_query)
    
    st.caption(f"Motores encontrados: {len(motores)}")

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        
        st_color = "#10b981" # Verde padrão
        
        # --- ESTRUTURA DO CARD GRANDE ---
        # Usamos uma div relativa para que o botão invisível fique por cima dela
        st.markdown(f"""
            <div style="position: relative; margin-bottom: 20px;">
                <div style="
                    background: rgba(0, 40, 60, 0.5); 
                    border: 1px solid rgba(0, 255, 255, 0.2); 
                    border-left: 6px solid {st_color}; 
                    border-radius: 10px; 
                    padding: 20px;
                    height: 160px;
                ">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <small style="color: #00ffff; font-family: monospace; letter-spacing: 2px;">REGISTRO TÉCNICO ID: #{id_m}</small>
                            <div style="font-size: 1.4rem; color: white; font-weight: bold; margin: 5px 0;">
                                {(m.get('marca') or '---').upper()} <span style="font-weight: 300; color: #ccc;">{m.get('modelo') or ''}</span>
                            </div>
                            <div style="font-size: 0.75rem; color: #8b949e; letter-spacing: 1px;">MOTOR {str(m.get('fases','')).upper()}</div>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                        <div style="text-align: center;">
                            <div style="font-size: 0.65rem; color: #8b949e; margin-bottom: 4px;">POTÊNCIA</div>
                            <div style="font-size: 1.1rem; font-weight: bold; color: #00f2ff;">{m.get('potencia_hp_cv','-')}</div>
                        </div>
                        <div style="text-align: center; border-left: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05);">
                            <div style="font-size: 0.65rem; color: #8b949e; margin-bottom: 4px;">ROTAÇÃO</div>
                            <div style="font-size: 1.1rem; font-weight: bold; color: #10b981;">{m.get('rpm_nominal','-')} <small>RPM</small></div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.65rem; color: #8b949e; margin-bottom: 4px;">TENSÃO</div>
                            <div style="font-size: 1.1rem; font-weight: bold; color: #a855f7;">{m.get('tensao_v','-')}V</div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Botão Invisível por cima de tudo
        # O margin-top negativo "puxa" o botão para cima do HTML anterior
        st.markdown('<div style="margin-top: -180px;">', unsafe_allow_html=True)
        if st.button("", key=f"overlay_{id_m}", use_container_width=True):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Espaçador para o próximo card não grudar
        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)

        # --- SEÇÃO EXPANDIDA ---
        if st.session_state.detalhes_visiveis.get(key_det):
            st.markdown("<div style='background: rgba(0,20,30,0.9); border: 1px solid #00ffff44; border-radius: 8px; padding: 20px; margin-bottom: 30px;'>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("✏️ EDITAR", key=f"ed_{id_m}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if c2.button("🗑️ EXCLUIR", key=f"ex_{id_m}", use_container_width=True):
                if excluir_motor(supabase, id_m): st.rerun()

            t1, t2, t3 = st.tabs(["📋 CONEXÃO", "🌀 REBOBINAGEM", "⚙️ MECÂNICA"])
            with t1:
                st.code("MAPA: 1:AZ | 2:BR | 3:LA | 4:AM | 5:PR | 6:VM", language="")
                render_dado("Amperagem Nominal", m.get("corrente_nominal_a"), "A")
                render_dado("Capacitores", f"{m.get('capacitor_permanente') or ''} / {m.get('capacitor_partida') or ''}")

            with t2:
                col_p, col_a = st.columns(2)
                with col_p:
                    render_dado("Passo (P)", limpar_passo(m.get("passo_principal")))
                    render_dado("Fio (P)", m.get("bitola_fio_principal"))
                with col_a:
                    render_dado("Passo (A)", limpar_passo(m.get("passo_auxiliar")))
                    render_dado("Fio (A)", m.get("bitola_fio_auxiliar"))
                render_dado("Ligação Interna", m.get("ligacao_interna"), highlight=True)

            with t3:
                render_dado("Ranhuras", m.get("numero_ranhuras"))
                render_dado("Pacote", m.get("comprimento_pacote_mm"), "mm")
                render_dado("Rolamentos", f"D: {m.get('rolamento_dianteiro')} / T: {m.get('rolamento_traseiro')}")

            st.markdown("</div>", unsafe_allow_html=True)


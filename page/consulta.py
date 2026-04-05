import streamlit as st
import importlib
import re

# ------------------------------
# BANCO SUPABASE
# ------------------------------
def listar_motores(supabase):
    try:
        # Limitado a 1000 para garantir que suas 272 linhas apareçam sempre
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
# BUSCA RÁPIDA
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
    s = re.sub(r"^[1][\s?:\-]*", "", s) # Remove "1:"
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

    # Estilos CSS para tornar o botão IDÊNTICO a um card e rápido
    st.markdown("""
        <style>
        div[data-testid="stButton"] > button {
            width: 100% !important;
            height: auto !important;
            padding: 15px !important;
            background: rgba(0, 40, 60, 0.4) !important;
            border: 1px solid rgba(0, 255, 255, 0.2) !important;
            border-left: 5px solid #10b981 !important;
            border-radius: 8px !important;
            text-align: left !important;
            transition: all 0.2s ease;
        }
        div[data-testid="stButton"] > button:hover {
            border-color: #00ffff !important;
            background: rgba(0, 60, 80, 0.6) !important;
        }
        /* Ajuste para o texto dentro do botão parecer um card técnico */
        .btn-text { color: white; font-family: sans-serif; }
        .btn-header { font-size: 0.6rem; color: #00ffff; font-family: monospace; }
        .btn-title { font-size: 1.1rem; font-weight: bold; display: block; margin: 4px 0; }
        .btn-grid { display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 10px; padding-top: 10px; }
        .btn-col { text-align: center; flex: 1; }
        .btn-label { font-size: 0.55rem; color: #8b949e; }
        .btn-val { font-size: 0.85rem; font-weight: bold; color: #00f2ff; }
        </style>
    """, unsafe_allow_html=True)

    if "detalhes_visiveis" not in st.session_state: st.session_state.detalhes_visiveis = {}
    if "motor_editando" not in st.session_state: st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state: st.session_state.abrir_edit = False

    if st.session_state.abrir_edit and st.session_state.motor_editando:
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Voltar para Lista"):
                st.session_state.abrir_edit = False
                st.rerun()
            return
        except: st.error("Erro no editor.")

    search_query = st.text_input("🔎 Pesquisar", placeholder="Marca, modelo...")
    
    motores_db = listar_motores(supabase)
    motores = buscar_motores(motores_db, search_query)
    
    st.caption(f"Motores encontrados: {len(motores)} / {len(motores_db)}")

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        
        # Montamos o conteúdo visual que irá DENTRO do botão
        conteudo_botao = f"""
            <div class="btn-text">
                <div class="btn-header">REGISTRO TÉCNICO ID: #{id_m}</div>
                <div class="btn-title">{(m.get('marca') or '---').upper()} {m.get('modelo') or ''}</div>
                <div style="font-size: 0.65rem; color: #8b949e;">MOTOR {str(m.get('fases','')).upper()}</div>
                <div class="btn-grid">
                    <div class="btn-col"><div class="btn-label">POTÊNCIA</div><div class="btn-val">{m.get('potencia_hp_cv','-')}</div></div>
                    <div class="btn-col"><div class="btn-label">ROTAÇÃO</div><div class="btn-val" style="color:#10b981;">{m.get('rpm_nominal','-')} RPM</div></div>
                    <div class="btn-col"><div class="btn-label">TENSÃO</div><div class="btn-val" style="color:#a855f7;">{m.get('tensao_v','-')}V</div></div>
                </div>
            </div>
        """

        # O botão agora contém o HTML (usamos unsafe_allow_html não funciona direto no label do st.button, 
        # então usamos um truque de CSS para injetar o visual no botão)
        if st.button(f"{m.get('marca')} {m.get('modelo')} #{id_m}", key=f"btn_{id_m}", use_container_width=True):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()

        # Injetamos o visual por cima do botão (pointer-events: none permite que o clique passe para o botão abaixo)
        st.markdown(f"""
            <div style="margin-top: -120px; margin-bottom: 25px; pointer-events: none;">
                {conteudo_botao}
            </div>
        """, unsafe_allow_html=True)

        # SEÇÃO EXPANDIDA
        if st.session_state.detalhes_visiveis.get(key_det):
            st.markdown("<div style='background: rgba(0,30,45,0.9); border: 1px solid #00ffff44; border-radius: 8px; padding: 15px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            
            c_ed, c_ex = st.columns(2)
            if c_ed.button("✏️ EDITAR", key=f"ed_{id_m}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if c_ex.button("🗑️ EXCLUIR", key=f"ex_{id_m}", use_container_width=True):
                if excluir_motor(supabase, id_m): st.rerun()

            t1, t2, t3 = st.tabs(["📋 PLACA", "🌀 BOBINAGEM", "⚙️ MECÂNICA"])
            with t1:
                st.markdown("<p style='font-size:0.6rem; color:#8b949e;'>MAPA DE SAÍDAS</p>", unsafe_allow_html=True)
                # Mapa de cores simplificado para carregar rápido
                st.code("1:AZ | 2:BR | 3:LA | 4:AM | 5:PR | 6:VM", language="")
                render_dado("Amperagem Nominal", m.get("corrente_nominal_a"), "A")
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
                render_dado("Ranhuras", m.get("numero_ranhuras"))
                render_dado("Pacote", m.get("comprimento_pacote_mm"), "mm")
                render_dado("Rolamentos", f"D: {m.get('rolamento_dianteiro')} / T: {m.get('rolamento_traseiro')}")

            st.markdown("</div>", unsafe_allow_html=True)


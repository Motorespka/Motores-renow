import streamlit as st
import importlib
import re
from core.calculadora import alertas_validacao_projeto

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
# BUSCA FLEXÍVEL
# ------------------------------
def buscar_motores(motores_db, search_query):
    if not search_query: return motores_db
    query = search_query.strip().lower()
    return [m for m in motores_db if query in f"{m.get('marca','')} {m.get('modelo','')} {m.get('fabricante','')} {m.get('potencia_hp_cv','')}".lower()]

# ------------------------------
# FORMATAÇÃO TÉCNICA
# ------------------------------
def limpar_passo(passo_raw):
    if not passo_raw: return "---"
    s = str(passo_raw).strip()
    s = re.sub(r"^[1][\s?:\-]*", "", s) # Remove o "1:" inicial
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

def render_fio_tech(bitola, material_tipo=""):
    if not bitola: return "---"
    mat = f" <span style='color: #f59e0b; font-size: 0.7rem;'>({str(material_tipo).upper()})</span>" if material_tipo else ""
    clean_bitola = str(bitola).upper().replace("AWG", "").replace("FIO", "").strip()
    return f"{clean_bitola} AWG{mat}"

# ------------------------------
# TELA PRINCIPAL
# ------------------------------
def show(supabase):
    st.markdown("## 🔍 Consulta de Motores")

    TABELA_CORES = {"Azul": "1", "Branco": "2", "Laranja": "3", "Amarelo": "4", "Preto": "5", "Vermelho": "6", "Verde": "Terra"}

    if "detalhes_visiveis" not in st.session_state: st.session_state.detalhes_visiveis = {}
    if "motor_editando" not in st.session_state: st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state: st.session_state.abrir_edit = False

    if st.session_state.abrir_edit and st.session_state.motor_editando:
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Voltar", use_container_width=True):
                st.session_state.abrir_edit = False
                st.rerun()
            return
        except: st.error("Erro ao carregar editor.")

    search_query = st.text_input("🔎 Pesquisar", placeholder="Marca, modelo ou potência...")
    
    motores_db = listar_motores(supabase)
    motores = buscar_motores(motores_db, search_query)
    
    st.caption(f"Motores ativos: {len(motores)} de {len(motores_db)}")

    for m in motores:
        id_motor = m.get("id")
        key_det = f"vis_{id_motor}"
        if key_det not in st.session_state.detalhes_visiveis: st.session_state.detalhes_visiveis[key_det] = False

        marca = (m.get("marca") or "---").upper()
        modelo = m.get("modelo") or ""
        fases = (m.get("fases") or "---").upper()
        
        alertas = alertas_validacao_projeto(m)
        st_color = "#ef4444" if any("risco" in a.lower() for a in alertas) else "#10b981"

        # --- CONTAINER DO CARD CLICÁVEL ---
        with st.container():
            # 1. O Visual (Exatamente como estava)
            st.markdown(f"""
                <div class="tech-card" style="border-left: 4px solid {st_color}; position: relative; margin-bottom: -45px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <small style="color: #00ffff; font-family: monospace; letter-spacing: 2px;">REGISTRO TÉCNICO ID: #{id_motor}</small>
                            <h3 style="margin:0; color:white;">{marca} <span style="font-weight:300;">{modelo}</span></h3>
                            <span style="font-size: 0.7rem; color: #8b949e;">MOTORES {fases}</span>
                        </div>
                        <div style="font-size: 0.6rem; color: {st_color}; border: 1px solid {st_color}44; padding: 2px 8px; border-radius: 10px;">
                            { "ESTÁVEL" if st_color == "#10b981" else "ALERTA" }
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 15px; border-top: 1px solid #00ffff11; padding-top: 10px; text-align: center;">
                        <div><small style="color:#8b949e;">POT</small><br><b style="color:#00f2ff; font-size:0.9rem;">{m.get('potencia_hp_cv','-')}</b></div>
                        <div><small style="color:#8b949e;">RPM</small><br><b style="color:#10b981; font-size:0.9rem;">{m.get('rpm_nominal','-')}</b></div>
                        <div><small style="color:#8b949e;">VOLTS</small><br><b style="color:#a855f7; font-size:0.9rem;">{m.get('tensao_v','-')}V</b></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # 2. O Botão Transparente que cobre tudo (Faz o card ser clicável)
            if st.button("", key=f"overlay_{id_motor}", use_container_width=True):
                st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis[key_det]
                st.rerun()

        # --- SEÇÃO EXPANDIDA (TELEMETRIA) ---
        if st.session_state.detalhes_visiveis[key_det]:
            st.markdown("<div style='background: rgba(0,25,35,0.8); border: 1px solid #00ffff33; border-top:none; border-radius: 0 0 8px 8px; padding: 20px; margin-top: -10px; margin-bottom: 30px;'>", unsafe_allow_html=True)
            
            col_act1, col_act2 = st.columns(2)
            if col_act1.button("✏️ EDITAR", key=f"ed_{id_motor}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if col_act2.button("🗑️ EXCLUIR", key=f"ex_{id_motor}", use_container_width=True):
                if excluir_motor(supabase, id_motor): st.rerun()

            tabs = st.tabs(["📋 CONEXÃO / PLACA", "🌀 REBOBINAGEM", "⚙️ MECÂNICA"])
            
            with tabs[0]:
                st.markdown("<p style='font-size:0.65rem; color:#8b949e; letter-spacing:2px; margin-bottom:10px;'>MAPA TÉCNICO DE CORES (SAÍDAS)</p>", unsafe_allow_html=True)
                cols_c = st.columns(len(TABELA_CORES))
                for i, (cor, num) in enumerate(TABELA_CORES.items()):
                    cols_c[i].markdown(f"<div style='text-align:center; background:#000; border-radius:4px; padding:4px;'><small style='color:#8b949e; font-size:0.5rem;'>{cor[:3].upper()}</small><br><b style='color:#00ffff; font-size:0.8rem;'>{num}</b></div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    render_dado("Amperagem Nominal", m.get("corrente_nominal_a"), "A")
                    render_dado("Amperagem Teste", m.get("corrente_vazio_a"), "A", highlight=True)
                with c2:
                    cap = f"{m.get('capacitor_permanente') or ''} {m.get('capacitor_partida') or ''}".strip()
                    render_dado("Capacitores", cap if cap else "N/A")
                    render_dado("Fator de Serviço", m.get("fator_servico"))

            with tabs[1]:
                c1, c2 = st.columns(2)
                with c1:
                    render_dado("Passo Principal", limpar_passo(m.get("passo_principal")))
                    render_dado("Fio Principal", render_fio_tech(m.get("bitola_fio_principal"), m.get("tipo_fio")))
                    render_dado("Espiras (P)", m.get("espiras_principal"))
                with c2:
                    render_dado("Passo Auxiliar", limpar_passo(m.get("passo_auxiliar")))
                    render_dado("Fio Auxiliar", render_fio_tech(m.get("bitola_fio_auxiliar"), m.get("tipo_fio")))
                    render_dado("Espiras (A)", m.get("espiras_auxiliar"))
                render_dado("Ligação Interna", m.get("ligacao_interna"), highlight=True)

            with tabs[2]:
                c1, c2 = st.columns(2)
                with c1:
                    render_dado("Ranhuras", m.get("numero_ranhuras"))
                    render_dado("Comp. Pacote", m.get("comprimento_pacote_mm"), "mm")
                with c2:
                    render_dado("Rolamento (D)", m.get("rolamento_dianteiro"))
                    render_dado("Rolamento (T)", m.get("rolamento_traseiro"))
                render_dado("Carcaça", m.get("carcaca"))

            st.markdown("</div>", unsafe_allow_html=True)


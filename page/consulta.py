import streamlit as st
import importlib
import re
from core.calculadora import alertas_validacao_projeto

# ------------------------------
# BANCO SUPABASE
# ------------------------------
def listar_motores(supabase):
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
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
# BUSCA INTELIGENTE CONTEXTUAL
# ------------------------------
def buscar_motores(motores_db, search_query):
    if not search_query: return motores_db
    query = search_query.strip().lower().replace(",", ".")
    
    valor_numerico = None
    match_fracao = re.search(r"(\d+)/(\d+)", query)
    match_decimal = re.search(r"(\d+\.?\d*)", query)

    if match_fracao:
        valor_numerico = float(match_fracao.group(1)) / float(match_fracao.group(2))
    elif match_decimal:
        try: valor_numerico = float(match_decimal.group(1))
        except: valor_numerico = None

    termos_texto = re.sub(r"(\d+/\d+|\d+\.?\d*)", "", query).strip().split()
    motores_filtrados = []

    def limpar_num_blindado(val):
        if val is None: return 0.0
        try:
            s = str(val).replace(",", ".")
            match = re.search(r"(\d+\.?\d*)", s)
            return float(match.group(1)) if match else 0.0
        except: return 0.0

    for m in motores_db:
        match_contexto = False
        pot_motor = limpar_num_blindado(m.get("potencia_hp_cv") or m.get("potencia"))
        rpm_motor = limpar_num_blindado(m.get("rpm_nominal") or m.get("rpm"))
        amp_motor = limpar_num_blindado(m.get("corrente_nominal_a") or m.get("corrente"))

        if valor_numerico is not None:
            if 800 <= valor_numerico <= 4000:
                if abs(rpm_motor - valor_numerico) < 50: match_contexto = True
            elif 0.1 <= valor_numerico <= 500 or match_fracao:
                if pot_motor == valor_numerico: match_contexto = True
                elif valor_numerico <= 50.0 and abs(amp_motor - valor_numerico) < 0.1: match_contexto = True
        
        texto_motor = f"{str(m.get('marca') or '')} {str(m.get('modelo') or '')}".lower()
        match_texto = all(termo in texto_motor for termo in termos_texto) if termos_texto else True

        if valor_numerico is not None:
            if match_contexto and match_texto: motores_filtrados.append(m)
        elif match_texto: motores_filtrados.append(m)

    return motores_filtrados

# ------------------------------
# COMPONENTES DE UI TECH (HUD MINI)
# ------------------------------
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
    """Formata bitola e material com destaque visual."""
    if not bitola: return "---"
    # Remove textos repetitivos caso existam no banco
    clean_bitola = str(bitola).upper().replace("AWG", "").replace("FIO", "").strip()
    mat = f" <span style='color: #f59e0b; font-size: 0.7rem;'>({str(material_tipo).upper()})</span>" if material_tipo else ""
    return f"{clean_bitola} AWG{mat}"

# ------------------------------
# TELA PRINCIPAL
# ------------------------------
def show(supabase):
    st.markdown("## 🔍 Consulta de Motores")

    TABELA_CORES = {
        "Azul": "1", "Branco": "2", "Laranja": "3",
        "Amarelo": "4", "Preto": "5", "Vermelho": "6", "Verde": "Terra",
    }

    if "detalhes_visiveis" not in st.session_state: st.session_state.detalhes_visiveis = {}
    if "motor_editando" not in st.session_state: st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state: st.session_state.abrir_edit = False

    # Lógica de Navegação para Edição
    if st.session_state.abrir_edit and st.session_state.motor_editando:
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Cancelar e Voltar", use_container_width=True):
                st.session_state.abrir_edit = False
                st.rerun()
            return
        except Exception as e:
            st.error(f"Erro ao carregar módulo de edição: {e}")

    search_query = st.text_input("🔎 Pesquisar motor", placeholder="Ex: 1/2, 1750, WEG, HERCULES...")
    
    motores_db = listar_motores(supabase)
    if not motores_db:
        st.info("Nenhum motor cadastrado.")
        return

    motores = buscar_motores(motores_db, search_query)
    st.caption(f"Sistemas detectados: {len(motores)}")

    for m in motores:
        id_motor = m.get("id")
        marca = (m.get("marca") or "---").upper()
        modelo = m.get("modelo") or ""
        fases = (m.get("fases") or "---").upper()
        
        # Alertas de validação
        alertas = alertas_validacao_projeto(m)
        st_color = "#ef4444" if any("risco" in a.lower() for a in alertas) else "#10b981"
        label_status = "🔴 CRÍTICO" if st_color == "#ef4444" else "🟢 NOMINAL"

        # --- CARD PRINCIPAL (TECH STYLE) ---
        st.markdown(f"""
            <div class="tech-card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <small style="color: #00ffff; font-family: monospace;">NODE_ID: #{id_motor}</small>
                        <h3 style="margin:0; color:white;">{marca} <span style="font-weight:300; font-size:1.1rem;">{modelo}</span></h3>
                        <span style="font-size: 0.7rem; color: #8b949e; letter-spacing: 1px;">{fases}</span>
                    </div>
                    <div class="hud-status" style="border-color: {st_color}55; color: {st_color};">
                        {label_status}
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 15px; border-top: 1px solid #00ffff22; padding-top: 15px; text-align: center;">
                    <div>
                        <div style="font-size: 0.6rem; color: #8b949e;">POTÊNCIA</div>
                        <div style="color: #00f2ff; font-weight: bold;">{m.get('potencia_hp_cv', '---')}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.6rem; color: #8b949e;">ROTAÇÃO</div>
                        <div style="color: #10b981; font-weight: bold;">{m.get('rpm_nominal', '---')} RPM</div>
                    </div>
                    <div>
                        <div style="font-size: 0.6rem; color: #8b949e;">TENSÃO</div>
                        <div style="color: #a855f7; font-weight: bold;">{m.get('tensao_v', '---')} V</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Controle de visibilidade dos detalhes
        key_det = f"vis_{id_motor}"
        if key_det not in st.session_state.detalhes_visiveis:
            st.session_state.detalhes_visiveis[key_det] = False

        btn_label = "📊 FECHAR RELATÓRIO" if st.session_state.detalhes_visiveis[key_det] else "🔍 ACESSAR TELEMETRIA TÉCNICA"
        if st.button(btn_label, key=f"btn_{id_motor}", use_container_width=True):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis[key_det]
            st.rerun()

        # --- SEÇÃO DE DETALHES EXPANDIDA ---
        if st.session_state.detalhes_visiveis[key_det]:
            st.markdown("<div style='background: rgba(0,20,30,0.5); border: 1px solid #00ffff22; border-radius: 8px; padding: 15px; margin-top: -10px; margin-bottom: 25px;'>", unsafe_allow_html=True)
            
            if alertas:
                for a in alertas: st.warning(a)

            # Ações Rápidas
            ca1, ca2 = st.columns(2)
            if ca1.button("✏️ EDITAR", key=f"ed_{id_motor}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if ca2.button("🗑️ EXCLUIR", key=f"ex_{id_motor}", use_container_width=True):
                if excluir_motor(supabase, id_motor): st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            t1, t2, t3 = st.tabs(["📋 DADOS PLACA", "🌀 REBOBINAGEM", "⚙️ MECÂNICA"])
            
            with t1:
                c1, c2 = st.columns(2)
                with c1:
                    render_dado("Amperagem (In)", m.get("corrente_nominal_a"), "A")
                    render_dado("Frequência", m.get("frequencia_hz"), "Hz")
                    render_dado("Polos", m.get("polos"))
                with c2:
                    render_dado("Capacitor", m.get("capacitor_permanente") or m.get("capacitor_partida"))
                    render_dado("Fator de Serviço", m.get("fator_servico"))
                    render_dado("Amperagem (Vazio)", m.get("corrente_vazio_a"), "A", highlight=True)

            with t2:
                st.markdown("<h5 style='color:#00ffff; font-size:0.75rem; margin-bottom:10px;'>ESTRUTURA DO ENROLAMENTO</h5>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    render_dado("Passo Principal", m.get("passo_principal"), " (P)")
                    render_dado("Fio Principal", render_fio_tech(m.get("bitola_fio_principal"), m.get("tipo_fio")))
                    render_dado("Espiras (Princ.)", m.get("espiras_principal"))
                with c2:
                    render_dado("Passo Auxiliar", m.get("passo_auxiliar"), " (A)")
                    render_dado("Fio Auxiliar", render_fio_tech(m.get("bitola_fio_auxiliar"), m.get("tipo_fio")))
                    render_dado("Espiras (Aux.)", m.get("espiras_auxiliar"))
                
                render_dado("Esquema de Ligação", m.get("ligacao_interna"), highlight=True)

            with t3:
                c1, c2 = st.columns(2)
                with c1:
                    render_dado("Ranhuras", m.get("numero_ranhuras"))
                    render_dado("Pacote (Compr.)", m.get("comprimento_pacote_mm"), "mm")
                with c2:
                    render_dado("Rol. Dianteiro", m.get("rolamento_dianteiro"))
                    render_dado("Rol. Traseiro", m.get("rolamento_traseiro"))
                render_dado("Carcaça", m.get("carcaca"))

            # Mapa de Cores Estilizado
            st.markdown("<hr style='border-color: rgba(0,255,255,0.1);'>", unsafe_allow_html=True)
            st.markdown("#### ⚡ MAPA DE CABOS")
            cols_c = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                with cols_c[i]:
                    st.markdown(f"""
                        <div style="text-align: center; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 5px; background: rgba(0,0,0,0.3);">
                            <div style="font-size: 0.55rem; color: #8b949e;">{cor[:3].upper()}</div>
                            <div style="font-size: 1rem; color: #00ffff; font-weight: bold;">{num}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            if m.get("observacoes"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.info(f"📝 **OBSERVAÇÕES:** {m.get('observacoes')}")
            
            st.markdown("</div>", unsafe_allow_html=True)


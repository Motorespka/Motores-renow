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
# COMPONENTE DE DADO TÉCNICO (HUD MINI)
# ------------------------------
def render_dado(label, valor, unidade=""):
    st.markdown(f"""
        <div style="background: rgba(0, 255, 255, 0.03); border: 1px solid rgba(0, 255, 255, 0.1); border-radius: 6px; padding: 10px; margin-bottom: 5px;">
            <div style="font-size: 0.65rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
            <div style="font-size: 1rem; color: white; font-family: monospace; font-weight: bold;">{valor} <span style="color: #00ffff; font-size: 0.8rem;">{unidade}</span></div>
        </div>
    """, unsafe_allow_html=True)

# ------------------------------
# TELA PRINCIPAL
# ------------------------------
def show(supabase):
    st.markdown("## 🔍 Consulta de Motores")

    TABELA_CORES = {
        "Azul": "1", "Branco": "2", "Laranja": "3",
        "Amarelo": "4", "Preto": "5", "Vermelho": "6", "Verde": "Terra",
    }

    if "motor_editando" not in st.session_state: st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state: st.session_state.abrir_edit = False

    if st.session_state.abrir_edit and st.session_state.motor_editando:
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Voltar para Lista", use_container_width=True):
                st.session_state.abrir_edit = False
                st.rerun()
            return
        except: st.error("Erro ao carregar edição.")

    search_query = st.text_input("🔎 Pesquisar motor", placeholder="Ex: 1/2, 1750, WEG 10cv...")
    
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
        potencia = m.get("potencia_hp_cv") or m.get("potencia") or "---"
        rpm = m.get("rpm_nominal") or m.get("rpm") or "---"
        tensao = m.get("tensao_v") or m.get("tensao") or "---"

        alertas = alertas_validacao_projeto(m)
        if any("risco" in a.lower() for a in alertas):
            st_color = "#ef4444"; label = "🔴 CRÍTICO"
        elif alertas:
            st_color = "#f59e0b"; label = "🟡 ATENÇÃO"
        else:
            st_color = "#10b981"; label = "🟢 NOMINAL"

        # Card Principal (Seu CSS)
        st.markdown(f"""
            <div class="tech-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <small style="color: #00ffff; font-family: monospace;">SYS_ID: {id_motor}</small>
                        <h3 style="margin:0; color:white;">{marca} <span style="font-weight:300;">{modelo}</span></h3>
                    </div>
                    <div class="hud-status" style="color: {st_color}; border-color: {st_color}55;">
                        {label}
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 15px; border-top: 1px solid #00ffff22; padding-top: 15px; text-align: center;">
                    <div>
                        <div style="font-size: 0.6rem; color: #8b949e;">POTÊNCIA</div>
                        <div style="color: #00f2ff; font-weight: bold;">{potencia} CV</div>
                    </div>
                    <div>
                        <div style="font-size: 0.6rem; color: #8b949e;">ROTAÇÃO</div>
                        <div style="color: #10b981; font-weight: bold;">{rpm} RPM</div>
                    </div>
                    <div>
                        <div style="font-size: 0.6rem; color: #8b949e;">TENSÃO</div>
                        <div style="color: #a855f7; font-weight: bold;">{tensao}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("📊 TELEMETRIA E DADOS TÉCNICOS"):
            if alertas:
                for a in alertas: st.warning(a)

            # Botões de Ação
            ca1, ca2 = st.columns(2)
            if ca1.button("✏️ EDITAR REGISTRO", key=f"ed_{id_motor}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if ca2.button("🗑️ ELIMINAR DADOS", key=f"ex_{id_motor}", use_container_width=True):
                if excluir_motor(supabase, id_motor): st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            t1, t2, t3 = st.tabs(["📋 ESPECIFICAÇÕES", "🛠️ CONSTRUÇÃO", "🚀 PERFORMANCE"])
            
            with t1:
                st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                col_pl1, col_pl2 = st.columns(2)
                with col_pl1:
                    render_dado("Marca", m.get("marca"))
                    render_dado("Modelo", m.get("modelo"))
                    render_dado("Fabricante", m.get("fabricante"))
                with col_pl2:
                    render_dado("Tensão", tensao, "V")
                    render_dado("Corrente", m.get("corrente_nominal_a"), "A")
                    render_dado("Frequência", m.get("frequencia_hz"), "Hz")

            with t2:
                st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                col_of1, col_of2 = st.columns(2)
                with col_of1:
                    st.markdown("<h5 style='color:#00ffff; font-size:0.8rem;'>🌀 ENROLAMENTO</h5>", unsafe_allow_html=True)
                    render_dado("Ranhuras", m.get("numero_ranhuras"))
                    render_dado("Fio Principal", m.get("bitola_fio_principal"))
                    render_dado("Espiras", m.get("espiras_principal"))
                with col_of2:
                    st.markdown("<h5 style='color:#00ffff; font-size:0.8rem;'>⚙️ MECÂNICA</h5>", unsafe_allow_html=True)
                    render_dado("Rol. Dianteiro", m.get("rolamento_dianteiro"))
                    render_dado("Rol. Traseiro", m.get("rolamento_traseiro"))
                    render_dado("Carcaça", m.get("carcaca"))

            with t3:
                st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                col_pf1, col_pf2 = st.columns(2)
                with col_pf1:
                    render_dado("Rendimento", m.get("rendimento_perc"), "%")
                    render_dado("Fator de Serviço", m.get("fator_servico"))
                with col_pf2:
                    render_dado("Classe Isolação", m.get("classe_isolacao"))
                    render_dado("Grau Proteção", m.get("grau_protecao_ip"))

            # Seção de Cores (Estilizada)
            st.markdown("<hr style='border-color: rgba(0,255,255,0.1);'>", unsafe_allow_html=True)
            st.markdown("#### ⚡ MAPA DE CONEXÃO (CABOS)")
            cols_c = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                with cols_c[i]:
                    st.markdown(f"""
                        <div style="text-align: center; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 5px; background: rgba(255,255,255,0.02);">
                            <div style="font-size: 0.6rem; color: #8b949e;">{cor.upper()}</div>
                            <div style="font-size: 1.1rem; color: #00ffff; font-weight: bold;">{num}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            if m.get("observacoes"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.info(f"📝 **NOTAS DE CAMPO:** {m.get('observacoes')}")

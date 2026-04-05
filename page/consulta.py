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
# BUSCA INTELIGENTE CONTEXTUAL 🔥
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

        # --- INTERFACE HUD UTILIZANDO SEU CSS ---
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

        with st.expander("ACESSO AOS DADOS TÉCNICOS"):
            if alertas:
                for a in alertas: st.warning(a)

            c1, c2 = st.columns(2)
            if c1.button("✏️ EDITAR", key=f"ed_{id_motor}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if c2.button("🗑️ DELETAR", key=f"ex_{id_motor}", use_container_width=True):
                if excluir_motor(supabase, id_motor): st.rerun()

            st.divider()
            t1, t2, t3 = st.tabs(["📋 PLACA", "🛠️ OFICINA", "🚀 PERFORMANCE"])
            with t1:
                col_a, col_b = st.columns(2)
                col_a.write(f"**Marca:** {m.get('marca')}\n\n**Modelo:** {m.get('modelo')}")
                col_b.write(f"**Tensão:** {tensao}\n\n**Corrente:** {m.get('corrente_nominal_a')}")
            with t2:
                st.markdown(f"**Ranhuras:** {m.get('numero_ranhuras')} | **Fio:** {m.get('bitola_fio_principal')}")
            with t3:
                st.write(f"**Rendimento:** {m.get('rendimento_perc')}%")

            st.markdown("#### ⚡ CORES DOS CABOS")
            cols = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                cols[i].metric(label=cor, value=num)


import streamlit as st
import importlib
import re
from core.calculadora import alertas_validacao_projeto

# ------------------------------
# BANCO SUPABASE
# ------------------------------
def listar_motores(supabase):
    try:
        res = supabase.table("motores") \
            .select("*") \
            .order("id", desc=True) \
            .execute()
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
# TELA PRINCIPAL
# ------------------------------
def show(supabase):
    # Injeta Tailwind para os cards
    st.markdown('<script src="https://cdn.tailwindcss.com"></script>', unsafe_allow_html=True)
    
    st.title("🔍 Consulta de Motores")

    TABELA_CORES = {
        "Azul": "1", "Branco": "2", "Laranja": "3",
        "Amarelo": "4", "Preto": "5", "Vermelho": "6", "Verde": "Terra",
    }

    if "motor_editando" not in st.session_state: st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state: st.session_state.abrir_edit = False

    # Logica de Edição
    if st.session_state.abrir_edit and st.session_state.motor_editando:
        edit_module = importlib.import_module("page.edit")
        edit_module.show(supabase)
        if st.button("🔙 Voltar para Lista", use_container_width=True):
            st.session_state.abrir_edit = False
            st.rerun()
        return

    search_query = st.text_input("🔎 Pesquisar motor", placeholder="Ex: 1/2, 1750, WEG 10cv, 1.5")
    motores_db = listar_motores(supabase)
    if not motores_db:
        st.info("Nenhum motor cadastrado.")
        return

    motores = buscar_motores(motores_db, search_query)
    st.caption(f"Exibindo {len(motores)} motor(es)")

    for m in motores:
        id_motor = m.get("id")
        marca = (m.get("marca") or "---").upper() 
        modelo = m.get("modelo") or ""
        potencia = m.get("potencia_hp_cv") or m.get("potencia") or "---"
        rpm = m.get("rpm_nominal") or m.get("rpm") or "---"
        tensao = m.get("tensao_v") or m.get("tensao") or "---"
        amperagem = m.get("corrente_nominal_a") or m.get("corrente") or "---"
        fases = m.get("fases") or "---"

        # Define cores e status baseados nos alertas
        alertas = alertas_validacao_projeto(m)
        if any("risco" in a.lower() for a in alertas):
            status_label, border_color, bg_color = "🔴 RISCO", "#ef4444", "rgba(239, 68, 68, 0.1)"
        elif alertas:
            status_label, border_color, bg_color = "🟡 ATENÇÃO", "#f59e0b", "rgba(245, 158, 11, 0.1)"
        else:
            status_label, border_color, bg_color = "🟢 OK", "#10b981", "rgba(16, 185, 129, 0.1)"

        # --- CARD ESTILIZADO (HTML/CSS) ---
        st.markdown(f"""
            <div style="background: {bg_color}; border-left: 5px solid {border_color}; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border-top: 1px solid rgba(255,255,255,0.1); border-right: 1px solid rgba(255,255,255,0.1); border-bottom: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <span style="color: #8b949e; font-size: 0.75rem; font-weight: bold; letter-spacing: 0.05em;">#{id_motor}</span>
                        <h3 style="color: white; margin: 0; font-size: 1.25rem; font-weight: 800;">{marca} {modelo}</h3>
                    </div>
                    <span style="background: rgba(0,0,0,0.3); padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 900; color: {border_color}; border: 1px solid {border_color};">
                        {status_label}
                    </span>
                </div>
                <div style="display: grid; grid-template-cols: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
                    <div style="text-align: center;">
                        <p style="color: #8b949e; font-size: 0.7rem; margin: 0;">POTÊNCIA</p>
                        <p style="color: #00f2ff; font-weight: bold; margin: 0;">{potencia} CV</p>
                    </div>
                    <div style="text-align: center;">
                        <p style="color: #8b949e; font-size: 0.7rem; margin: 0;">ROTAÇÃO</p>
                        <p style="color: #10b981; font-weight: bold; margin: 0;">{rpm} RPM</p>
                    </div>
                    <div style="text-align: center;">
                        <p style="color: #8b949e; font-size: 0.7rem; margin: 0;">TENSÃO</p>
                        <p style="color: #a855f7; font-weight: bold; margin: 0;">{tensao}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Expander padrão para as ações e detalhes técnicos
        with st.expander("Expandir Detalhes e Ações"):
            if alertas:
                for a in alertas: st.warning(a)
            
            c1, c2 = st.columns(2)
            if c1.button("✏️ Editar", key=f"ed_{id_motor}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if c2.button("🗑️ Excluir", key=f"ex_{id_motor}", use_container_width=True):
                if excluir_motor(supabase, id_motor):
                    st.success("Motor excluído!")
                    st.rerun()

            st.divider()
            t_placa, t_oficina, t_perf = st.tabs(["📋 Placa", "🛠️ Oficina", "🚀 Performance"])
            
            with t_placa:
                cp1, cp2, cp3 = st.columns(3)
                cp1.write(f"**Marca:** {m.get('marca')}\n\n**Modelo:** {m.get('modelo')}")
                cp2.write(f"**Potência:** {potencia}\n\n**Tensão:** {tensao}")
                cp3.write(f"**RPM:** {rpm}\n\n**Fases:** {fases}")

            with t_oficina:
                co1, co2 = st.columns(2)
                co1.markdown(f"**🌀 Rebobinagem**\n\n**Ranhuras:** {m.get('numero_ranhuras')}\n\n**Fio:** {m.get('bitola_fio_principal')}")
                co2.markdown(f"**⚙️ Mecânica**\n\n**Rol. Dianteiro:** {m.get('rolamento_dianteiro')}\n\n**Rol. Traseiro:** {m.get('rolamento_traseiro')}")

            with t_perf:
                st.write(f"**Rendimento:** {m.get('rendimento_perc')}%")
                st.write(f"**Classe Isolação:** {m.get('classe_isolacao')}")

            st.markdown("### ⚡ Cores dos Cabos")
            cols_c = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                cols_c[i].metric(label=cor, value=num)
            
            if m.get("observacoes"):
                st.info(f"📝 **Obs:** {m.get('observacoes')}")
import streamlit as st
import importlib
import re
from core.calculadora import alertas_validacao_projeto

# ------------------------------
# BANCO SUPABASE
# ------------------------------
def listar_motores(supabase):
    try:
        res = supabase.table("motores") \
            .select("*") \
            .order("id", desc=True) \
            .execute()
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
# TELA PRINCIPAL
# ------------------------------
def show(supabase):
    # Injeta Tailwind para os cards
    st.markdown('<script src="https://cdn.tailwindcss.com"></script>', unsafe_allow_html=True)
    
    st.title("🔍 Consulta de Motores")

    TABELA_CORES = {
        "Azul": "1", "Branco": "2", "Laranja": "3",
        "Amarelo": "4", "Preto": "5", "Vermelho": "6", "Verde": "Terra",
    }

    if "motor_editando" not in st.session_state: st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state: st.session_state.abrir_edit = False

    # Logica de Edição
    if st.session_state.abrir_edit and st.session_state.motor_editando:
        edit_module = importlib.import_module("page.edit")
        edit_module.show(supabase)
        if st.button("🔙 Voltar para Lista", use_container_width=True):
            st.session_state.abrir_edit = False
            st.rerun()
        return

    search_query = st.text_input("🔎 Pesquisar motor", placeholder="Ex: 1/2, 1750, WEG 10cv, 1.5")
    motores_db = listar_motores(supabase)
    if not motores_db:
        st.info("Nenhum motor cadastrado.")
        return

    motores = buscar_motores(motores_db, search_query)
    st.caption(f"Exibindo {len(motores)} motor(es)")

    for m in motores:
        id_motor = m.get("id")
        marca = (m.get("marca") or "---").upper() 
        modelo = m.get("modelo") or ""
        potencia = m.get("potencia_hp_cv") or m.get("potencia") or "---"
        rpm = m.get("rpm_nominal") or m.get("rpm") or "---"
        tensao = m.get("tensao_v") or m.get("tensao") or "---"
        amperagem = m.get("corrente_nominal_a") or m.get("corrente") or "---"
        fases = m.get("fases") or "---"

        # Define cores e status baseados nos alertas
        alertas = alertas_validacao_projeto(m)
        if any("risco" in a.lower() for a in alertas):
            status_label, border_color, bg_color = "🔴 RISCO", "#ef4444", "rgba(239, 68, 68, 0.1)"
        elif alertas:
            status_label, border_color, bg_color = "🟡 ATENÇÃO", "#f59e0b", "rgba(245, 158, 11, 0.1)"
        else:
            status_label, border_color, bg_color = "🟢 OK", "#10b981", "rgba(16, 185, 129, 0.1)"

        # --- CARD ESTILIZADO (HTML/CSS) ---
        st.markdown(f"""
            <div style="background: {bg_color}; border-left: 5px solid {border_color}; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border-top: 1px solid rgba(255,255,255,0.1); border-right: 1px solid rgba(255,255,255,0.1); border-bottom: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <span style="color: #8b949e; font-size: 0.75rem; font-weight: bold; letter-spacing: 0.05em;">#{id_motor}</span>
                        <h3 style="color: white; margin: 0; font-size: 1.25rem; font-weight: 800;">{marca} {modelo}</h3>
                    </div>
                    <span style="background: rgba(0,0,0,0.3); padding: 4px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 900; color: {border_color}; border: 1px solid {border_color};">
                        {status_label}
                    </span>
                </div>
                <div style="display: grid; grid-template-cols: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
                    <div style="text-align: center;">
                        <p style="color: #8b949e; font-size: 0.7rem; margin: 0;">POTÊNCIA</p>
                        <p style="color: #00f2ff; font-weight: bold; margin: 0;">{potencia} CV</p>
                    </div>
                    <div style="text-align: center;">
                        <p style="color: #8b949e; font-size: 0.7rem; margin: 0;">ROTAÇÃO</p>
                        <p style="color: #10b981; font-weight: bold; margin: 0;">{rpm} RPM</p>
                    </div>
                    <div style="text-align: center;">
                        <p style="color: #8b949e; font-size: 0.7rem; margin: 0;">TENSÃO</p>
                        <p style="color: #a855f7; font-weight: bold; margin: 0;">{tensao}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Expander padrão para as ações e detalhes técnicos
        with st.expander("Expandir Detalhes e Ações"):
            if alertas:
                for a in alertas: st.warning(a)
            
            c1, c2 = st.columns(2)
            if c1.button("✏️ Editar", key=f"ed_{id_motor}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if c2.button("🗑️ Excluir", key=f"ex_{id_motor}", use_container_width=True):
                if excluir_motor(supabase, id_motor):
                    st.success("Motor excluído!")
                    st.rerun()

            st.divider()
            t_placa, t_oficina, t_perf = st.tabs(["📋 Placa", "🛠️ Oficina", "🚀 Performance"])
            
            with t_placa:
                cp1, cp2, cp3 = st.columns(3)
                cp1.write(f"**Marca:** {m.get('marca')}\n\n**Modelo:** {m.get('modelo')}")
                cp2.write(f"**Potência:** {potencia}\n\n**Tensão:** {tensao}")
                cp3.write(f"**RPM:** {rpm}\n\n**Fases:** {fases}")

            with t_oficina:
                co1, co2 = st.columns(2)
                co1.markdown(f"**🌀 Rebobinagem**\n\n**Ranhuras:** {m.get('numero_ranhuras')}\n\n**Fio:** {m.get('bitola_fio_principal')}")
                co2.markdown(f"**⚙️ Mecânica**\n\n**Rol. Dianteiro:** {m.get('rolamento_dianteiro')}\n\n**Rol. Traseiro:** {m.get('rolamento_traseiro')}")

            with t_perf:
                st.write(f"**Rendimento:** {m.get('rendimento_perc')}%")
                st.write(f"**Classe Isolação:** {m.get('classe_isolacao')}")

            st.markdown("### ⚡ Cores dos Cabos")
            cols_c = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                cols_c[i].metric(label=cor, value=num)
            
            if m.get("observacoes"):
                st.info(f"📝 **Obs:** {m.get('observacoes')}")


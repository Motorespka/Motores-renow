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
# BUSCA INTELIGENTE CONTEXTUAL 🔥
# ------------------------------
def buscar_motores(motores_db, search_query):
    if not search_query:
        return motores_db

    # Normalização inicial
    query = search_query.strip().lower().replace(",", ".")
    
    # 1. Tenta extrair valor numérico (Fração ou Decimal)
    valor_numerico = None
    match_fracao = re.search(r"(\d+)/(\d+)", query)
    match_decimal = re.search(r"(\d+\.?\d*)", query)

    if match_fracao:
        valor_numerico = float(match_fracao.group(1)) / float(match_fracao.group(2))
    elif match_decimal:
        valor_numerico = float(match_decimal.group(1))

    # 2. Extrai termos de texto (ex: "WEG", "Eberle") removendo os números da busca
    termos_texto = re.sub(r"(\d+/\d+|\d+\.?\d*)", "", query).strip().split()
    
    motores_filtrados = []

    for m in motores_db:
        match_contexto = False
        
        # Extração de dados do motor para comparação
        def limpar_num(val):
            if val is None: return 0.0
            # Remove unidades e limpa pontuação
            n = re.sub(r"[^\d.]", "", str(val).replace(",", "."))
            return float(n) if n else 0.0

        pot_motor = limpar_num(m.get("potencia_hp_cv") or m.get("potencia"))
        rpm_motor = limpar_num(m.get("rpm_nominal") or m.get("rpm"))
        amp_motor = limpar_num(m.get("corrente_nominal_a") or m.get("corrente"))

        # --- LÓGICA DE INTELIGÊNCIA POR FAIXAS ---
        if valor_numerico is not None:
            # ROTAÇÃO: Se buscou entre 800 e 4000
            if 800 <= valor_numerico <= 4000:
                if abs(rpm_motor - valor_numerico) < 50: # Tolerância de 50 RPM
                    match_contexto = True
            
            # POTÊNCIA (CV/HP): Se buscou entre 0.1 e 500 (ou fração)
            # Obs: Incluímos frações aqui (1/2, 1/3, etc)
            elif 0.1 <= valor_numerico <= 500 or match_fracao:
                # Se o valor for muito baixo (ex: 0.5), testamos Amperagem e CV
                if valor_numerico == pot_motor:
                    match_contexto = True
                elif valor_numerico <= 20.0 and valor_numerico == amp_motor:
                    match_contexto = True
        
        # --- BUSCA POR TEXTO (MARCA/MODELO) ---
        # Ignoramos o ID para não confundir busca por "1" com motor #1
        texto_motor = f"{str(m.get('marca') or '')} {str(m.get('modelo') or '')}".lower()
        match_texto = all(termo in texto_motor for termo in termos_texto) if termos_texto else True

        # --- FILTRO FINAL ---
        # Se digitou número, o número PRECISA bater no contexto. Se digitou texto, o texto PRECISA bater.
        if valor_numerico is not None:
            if match_contexto and match_texto:
                motores_filtrados.append(m)
        elif match_texto:
            motores_filtrados.append(m)

    return motores_filtrados


# ------------------------------
# TELA PRINCIPAL
# ------------------------------
def show(supabase):

    st.title("🔍 Consulta de Motores")

    TABELA_CORES = {
        "Azul": "1", "Branco": "2", "Laranja": "3",
        "Amarelo": "4", "Preto": "5", "Vermelho": "6", "Verde": "Terra",
    }

    if "motor_editando" not in st.session_state:
        st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state:
        st.session_state.abrir_edit = False

    if st.session_state.abrir_edit and st.session_state.motor_editando:
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Voltar para Lista", use_container_width=True):
                st.session_state.abrir_edit = False
                st.session_state.motor_editando = None
                st.rerun()
            return
        except Exception as e:
            st.error(f"Erro ao carregar edição: {e}")

    # BUSCA
    search_query = st.text_input(
        "🔎 Pesquisar motor",
        placeholder="Ex: 1/2, 1750, WEG 10cv, 1.5",
        help="Números baixos (0.1-500) buscam CV. Números altos (800+) buscam RPM. Frações (1/2) buscam CV.",
    )

    motores_db = listar_motores(supabase)

    if not motores_db:
        st.info("Nenhum motor cadastrado.")
        return

    motores = buscar_motores(motores_db, search_query)

    # Avisos de busca vazia
    if not motores and search_query:
        st.warning(f"Nenhum motor encontrado para '{search_query}' nas faixas técnicas.")
        return

    if not motores: return

    st.caption(f"Exibindo {len(motores)} motor(es)")

    # LISTAGEM
    for m in motores:
        id_motor = m.get("id")
        marca = (m.get("marca") or "---").upper() 
        modelo = m.get("modelo") or ""
        potencia = m.get("potencia_hp_cv") or m.get("potencia") or "---"
        rpm = m.get("rpm_nominal") or m.get("rpm") or "---"
        tensao = m.get("tensao_v") or m.get("tensao") or "---"
        amperagem = m.get("corrente_nominal_a") or m.get("corrente") or "---"
        fases = m.get("fases") or "---"

        alertas = alertas_validacao_projeto(m)
        if any("risco" in a.lower() for a in alertas): status = "🔴 RISCO"
        elif alertas: status = "🟡 ATENÇÃO"
        else: status = "🟢 OK"

        st.markdown(f"**#{id_motor} · {marca} {modelo} — {status}** {potencia} ({fases}) · {rpm} RPM · {tensao} · {amperagem}")

        with st.expander("Ver detalhes"):
            if alertas:
                for a in alertas: st.warning(a)
            else:
                st.success("Projeto validado.")

            col1, col2 = st.columns(2)
            if col1.button("✏️ Editar", key=f"ed_{id_motor}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()

            if col2.button("🗑️ Excluir", key=f"ex_{id_motor}", use_container_width=True):
                if excluir_motor(supabase, id_motor):
                    st.success("Motor excluído!")
                    st.rerun()

            st.divider()
            tab_placa, tab_oficina, tab_avancado = st.tabs(["📋 Placa", "🛠️ Oficina", "🚀 Performance"])

            with tab_placa:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write("**Marca:**", m.get("marca"))
                    st.write("**Modelo:**", m.get("modelo"))
                    st.write("**Carcaça:**", m.get("carcaca"))
                with c2:
                    st.write("**Potência:**", potencia)
                    st.write("**Tensão:**", tensao)
                    st.write("**Corrente:**", amperagem)
                with c3:
                    st.write("**RPM:**", rpm)
                    st.write("**Frequência:**", m.get("frequencia_hz"))
                    st.write("**Fases:**", fases)
                st.info(f"📏 **Pacote:** {m.get('comprimento_pacote_mm', '---')} mm")

            with tab_oficina:
                col_reb, col_mec = st.columns(2)
                with col_reb:
                    st.markdown("#### 🌀 Rebobinagem")
                    st.write("**Ranhuras:**", m.get("numero_ranhuras"))
                    st.write("**Ligação:**", m.get("ligacao_interna"))
                    st.write("**Principal:**", f"P: {m.get('passo_principal')} | F: {m.get('bitola_fio_principal')} | E: {m.get('espiras_principal')}")
                with col_mec:
                    st.markdown("#### ⚙️ Mecânica")
                    st.write("**Rol. Dianteiro:**", m.get("rolamento_dianteiro"))
                    st.write("**Rol. Traseiro:**", m.get("rolamento_traseiro"))
                    st.write("**Peso:**", m.get("peso_total_kg"), "kg")

            with tab_avancado:
                st.markdown("### 🔬 Performance")
                a1, a2 = st.columns(2)
                with a1:
                    st.write("**Rendimento:**", m.get("rendimento_perc"))
                    st.write("**Fator de Potência:**", m.get("fator_potencia_cos_phi"))
                with a2:
                    st.write("**Classe Isolação:**", m.get("classe_isolacao"))
                    st.write("**IP:**", m.get("grau_protecao_ip"))

            st.divider()
            st.markdown("### ⚡ Cores dos Cabos")
            cols_cores = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                cols_cores[i].metric(label=cor, value=num)

            if m.get("observacoes"):
                st.write("📝 **Obs:**", m.get("observacoes"))

            st.caption(f"📅 {m.get('data_cadastro')} | Origem: {m.get('origem_registro') or 'Manual'}")

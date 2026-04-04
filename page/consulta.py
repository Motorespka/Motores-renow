import streamlit as st
import importlib
import re  # Import necessário para a busca inteligente
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
# BUSCA INTELIGENTE 🔥 (MODIFICADA: IGNORA O #ID NA PESQUISA)
# ------------------------------
def buscar_motores(motores_db, search_query):
    if not search_query:
        return motores_db

    # Normaliza a query: minúsculo e troca vírgula por ponto (ex: 10,5 -> 10.5)
    query = search_query.strip().lower().replace(",", ".")
    
    # Identifica se o usuário digitou um número (ex: 10)
    match_numero = re.search(r"(\d+\.?\d*)", query)
    filtro_valor_puro = match_numero.group(1) if match_numero else None

    # Remove as unidades da busca geral para não dar conflito
    termos_busca = query.replace("cv", "").replace("kw", "").replace("hp", "").replace("rpm", "").split()

    motores_filtrados = []

    for m in motores_db:
        # Extração e normalização: ignoramos o campo "id" propositalmente aqui
        marca = str(m.get("marca") or "").lower()
        modelo = str(m.get("modelo") or "").lower()
        
        # Pegamos a potência e removemos espaços para comparar
        potencia_orig = str(m.get("potencia_hp_cv") or m.get("potencia") or "").lower().replace(",", ".").replace(" ", "")

        # Criamos o texto de busca excluindo o ID para que a busca por número não o encontre
        dados_tecnicos = [str(v).lower().replace(",", ".") for k, v in m.items() if k != "id" and v is not None]
        texto_motor = " ".join(dados_tecnicos)

        # LÓGICA DE MATCH:
        match_prioritario = False
        if filtro_valor_puro:
            # Se o número digitado for o início da potência (ex: usuário digitou 10, motor é 10cv)
            if potencia_orig.startswith(filtro_valor_puro):
                match_prioritario = True

        # Verifica se todos os termos digitados (ex: "weg") estão nos dados técnicos
        match_geral = all(termo in texto_motor for termo in termos_busca)

        if match_prioritario or match_geral:
            # Score 1 para quem tem a potência batendo, garantindo que fiquem no topo
            m["_score"] = 1 if match_prioritario else 0
            motores_filtrados.append(m)

    # Ordena pelo Score (Potência) e depois pela ordem de cadastro
    motores_filtrados.sort(key=lambda x: (x.get("_score", 0), x.get("id", 0)), reverse=True)
    return motores_filtrados


# ------------------------------
# TELA PRINCIPAL
# ------------------------------
def show(supabase):

    st.title("🔍 Consulta de Motores")

    # --- cores para o rebobinador ---
    TABELA_CORES = {
        "Azul": "1",
        "Branco": "2",
        "Laranja": "3",
        "Amarelo": "4",
        "Preto": "5",
        "Vermelho": "6",
        "Verde": "Terra",
    }

    # ------------------------------
    # CONTROLE DE EDIÇÃO
    # ------------------------------
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

    # ------------------------------
    # BUSCA
    # ------------------------------
    search_query = st.text_input(
        "🔎 Pesquisar motor",
        placeholder="Ex: WEG 12.5 1750 132M estrela",
        help="A busca agora prioriza potência. O número do motor (#ID) não é mais usado na pesquisa.",
    )

    motores_db = listar_motores(supabase)

    if motores_db is None or len(motores_db) == 0:
        st.info("Nenhum motor cadastrado.")
        return

    motores = buscar_motores(motores_db, search_query)

    if not motores:
        st.warning(f"Nenhum resultado encontrado para: '{search_query}'")
        return

    st.caption(f"Exibindo {len(motores)} motor(es)")

    # ------------------------------
    # LISTAGEM
    # ------------------------------
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

        if any("risco" in a.lower() for a in alertas):
            status = "🔴 RISCO"
        elif alertas:
            status = "🟡 ATENÇÃO"
        else:
            status = "🟢 OK"

        st.markdown(
            f"""
            **#{id_motor} · {marca} {modelo} — {status}** {potencia} ({fases}) · {rpm} RPM · {tensao} · {amperagem}
            """
        )

        with st.expander("Ver detalhes"):

            if alertas:
                for a in alertas:
                    st.warning(a)
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

            tab_placa, tab_oficina, tab_avancado = st.tabs([
                "📋 Placa (Principal)", 
                "🛠️ Rebobinagem & Mecânica", 
                "🚀 Avançado & Performance"
            ])

            with tab_placa:
                st.markdown("### 📋 Informações da Placa")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write("**Marca:**", m.get("marca"))
                    st.write("**Modelo:**", m.get("modelo"))
                    st.write("**Fabricante:**", m.get("fabricante"))
                    st.write("**Carcaça:**", m.get("carcaca"))
                with c2:
                    st.write("**Potência:**", potencia)
                    st.write("**Tensão:**", tensao)
                    st.write("**Amperagem (In):**", amperagem)
                with c3:
                    st.write("**RPM:**", rpm)
                    st.write("**Frequência:**", m.get("frequencia_hz") or m.get("frequencia"))
                    st.write("**Fases:**", fases)

                st.info(f"📏 **Tamanho do Induzido (Pacote):** {m.get('comprimento_pacote_mm', '---')} mm")

            with tab_oficina:
                col_reb, col_mec = st.columns(2)
                with col_reb:
                    st.markdown("#### 🌀 Rebobinagem")
                    st.write("**Número de Ranhuras:**", m.get("numero_ranhuras"))
                    st.write("**Tipo de Enrolamento:**", m.get("tipo_enrolamento"))
                    st.write("**Ligação:**", m.get("ligacao_interna") or m.get("ligacao"))
                    
                    st.markdown("---")
                    st.write("**Principal:**")
                    st.write(f"P: {m.get('passo_principal')} | F: {m.get('bitola_fio_principal') or m.get('fio_principal')} | E: {m.get('espiras_principal') or m.get('espira_principal')}")
                    
                    st.write("**Auxiliar:**")
                    st.write(f"P: {m.get('passo_auxiliar')} | F: {m.get('bitola_fio_auxiliar') or m.get('fio_auxiliar')} | E: {m.get('espiras_auxiliar') or m.get('espira_auxiliar')}")

                with col_mec:
                    st.markdown("#### ⚙️ Mecânica")
                    st.write("**Rolamento Dianteiro:**", m.get("rolamento_dianteiro"))
                    st.write("**Rolamento Traseiro:**", m.get("rolamento_traseiro"))
                    st.write("**Peso Total:**", m.get("peso_total_kg"), "kg")
                    st.write("**Graxa:**", m.get("tipo_graxa"))
                    
                    st.markdown("---")
                    st.write("**Capacitores:**")
                    st.write(f"Partida: {m.get('capacitor_partida_mfd') or m.get('capacitor_partida', '---')}")
                    st.write(f"Perm.: {m.get('capacitor_permanente_mfd') or m.get('capacitor_permanente', '---')}")

            with tab_avancado:
                st.markdown("### 🔬 Dados de Performance & Engenharia")
                a1, a2 = st.columns(2)
                with a1:
                    st.write("**Rendimento (%):**", m.get("rendimento_perc"))
                    st.write("**Fator de Potência (cos φ):**", m.get("fator_potencia_cos_phi"))
                    st.write("**Fator de Serviço (FS):**", m.get("fator_servico"))
                with a2:
                    st.write("**Relação Ip/In:**", m.get("ip_in_ratio"))
                    st.write("**Classe de Isolação:**", m.get("classe_isolacao"))
                    st.write("**Grau de Proteção (IP):**", m.get("grau_protecao_ip"))
                
                if m.get("especificacoes_extra"):
                    st.markdown("---")
                    st.write("**📋 Atributos Adicionais:**")
                    st.json(m.get("especificacoes_extra"))

            st.divider()

            st.markdown("### ⚡ Cores dos Cabos")
            cols_cores = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                cols_cores[i].metric(label=cor, value=num)

            if m.get("observacoes"):
                st.markdown("---")
                st.write("📝 Obs:", m.get("observacoes"))

            st.caption(
                f"📅 {m.get('data_cadastro')} | Origem: {m.get('origem_registro') or m.get('origem_calculo')}"
            )

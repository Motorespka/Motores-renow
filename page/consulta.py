import streamlit as st
import importlib
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
# BUSCA INTELIGENTE 🔥
# ------------------------------
def buscar_motores(motores_db, search_query):

    if not search_query:
        return motores_db

    query = search_query.strip().lower()

    def normalizar(valor):
        return (
            str(valor)
            .lower()
            .replace("cv", "")
            .replace("kw", "")
            .replace("rpm", "")
            .replace("hz", "")
            .strip()
        )

    palavras = query.split()

    motores_filtrados = []

    for m in motores_db:
        texto_motor = " ".join(
            normalizar(v) for v in m.values() if v is not None
        )

        if all(p in texto_motor for p in palavras):
            motores_filtrados.append(m)

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
        help="Você pode digitar várias palavras como no Google.",
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
        marca = m.get("marca") or "---"
        modelo = m.get("modelo") or ""
        potencia = m.get("potencia") or "---"
        rpm = m.get("rpm") or "---"

        alertas = alertas_validacao_projeto(m)

        if any("risco" in a.lower() for a in alertas):
            status = "🔴 RISCO"
        elif alertas:
            status = "🟡 ATENÇÃO"
        else:
            status = "🟢 OK"

        st.markdown(
            f"""
            **#{id_motor} · {marca} {modelo} — {status}**  
            {potencia} · {rpm} RPM
            """
        )

        with st.expander("Ver detalhes"):

            # ALERTAS
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

            # DADOS GERAIS
            st.markdown("### 📋 Dados do Motor")
            c1, c2, c3 = st.columns(3)

            with c1:
                st.write("Marca:", m.get("marca"))
                st.write("Modelo:", m.get("modelo"))
                st.write("Fabricante:", m.get("fabricante"))

            with c2:
                st.write("Potência:", m.get("potencia"))
                st.write("Tensão:", m.get("tensao"))
                st.write("Corrente:", m.get("corrente"))

            with c3:
                st.write("RPM:", m.get("rpm"))
                st.write("Frequência:", m.get("frequencia"))
                st.write("Rendimento:", m.get("rendimento"))

            st.divider()

            # BOBINAGEM
            st.markdown("### 🌀 Bobinagem")

            b1, b2 = st.columns(2)

            with b1:
                st.write("Passo Principal:", m.get("passo_principal"))
                st.write("Fio Principal:", m.get("fio_principal"))
                st.write("Espiras Principal:", m.get("espira_principal"))

            with b2:
                st.write("Passo Auxiliar:", m.get("passo_auxiliar"))
                st.write("Fio Auxiliar:", m.get("fio_auxiliar"))
                st.write("Espiras Auxiliar:", m.get("espira_auxiliar"))

            st.divider()

            # TRADUTOR DE CORES
            st.markdown("### ⚡ Cores dos Cabos")

            cols_cores = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                cols_cores[i].metric(label=cor, value=num)

            if m.get("observacoes"):
                st.markdown("---")
                st.write("📝 Obs:", m.get("observacoes"))

            st.caption(
                f"📅 {m.get('data_cadastro')} | Origem: {m.get('origem_calculo')}"
            )

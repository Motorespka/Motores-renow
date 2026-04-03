import streamlit as st
import importlib

# ------------------------------
# Operações no banco (SUPABASE)
# ------------------------------
def listar_motores(supabase):
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        return res.data 
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
# Função principal
# ------------------------------
def show(supabase): 
    st.title("🔍 Consulta de Motores")

    if "motor_editando" not in st.session_state:
        st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state:
        st.session_state.abrir_edit = False

    # Modo edição
    if st.session_state.abrir_edit and st.session_state.motor_editando:
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Voltar para Lista"):
                st.session_state.abrir_edit = False
                st.session_state.motor_editando = None
                st.rerun()
            return
        except Exception as e:
            st.error(f"Erro ao carregar edição: {e}")

    motores = listar_motores(supabase)
    
    if not motores:
        st.info("Nenhum motor cadastrado.")
        return

    # Estilo CSS para melhorar espaçamento no mobile
    st.markdown("""
        <style>
        [data-testid="stExpander"] { border: 1px solid #444; border-radius: 10px; margin-bottom: 10px; }
        .stMarkdown p { font-size: 14px; margin-bottom: 5px; }
        </style>
    """, unsafe_allow_html=True)

    for m in motores:
        id_motor = m.get('id')
        marca = m.get('marca') or "WEG"
        pot = m.get('potencia') or "---"
        
        # Cabeçalho otimizado para telas pequenas
        titulo_card = f"🆔 {id_motor} | {marca} | {pot}"

        with st.expander(titulo_card):
            # Ações rápidas (Botões grandes para facilitar o toque)
            c1, c2 = st.columns(2)
            if c1.button("✏️ Editar", key=f"ed_{id_motor}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if c2.button("🗑️ Excluir", key=f"ex_{id_motor}", use_container_width=True):
                if excluir_motor(supabase, id_motor):
                    st.success("Excluído!")
                    st.rerun()

            st.divider()

            # --- SEÇÃO 1: PLACA (2 colunas para não esmagar no celular) ---
            st.markdown("#### 📋 Dados de Placa")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Marca:**\n{m.get('marca') or '---'}")
                st.markdown(f"**Potência:**\n{m.get('potencia') or '---'}")
                st.markdown(f"**Tensão:**\n{m.get('tensao') or '---'}")
            with col2:
                st.markdown(f"**RPM:**\n{m.get('rpm') or '---'}")
                st.markdown(f"**Corrente:**\n{m.get('corrente') or '---'}")
                st.markdown(f"**Freq:**\n{m.get('frequencia') or '---'}")

            st.divider()

            # --- SEÇÃO 2: BOBINAGEM (Cards coloridos) ---
            st.markdown("#### 🌀 Bobinagem")
            
            st.info(f"**Principal**\n\n**Passo:** {m.get('passo_principal') or m.get('passo_princ') or '---'}  \n"
                    f"**Fio:** {m.get('fio_principal') or m.get('fio_princ') or '---'}  \n"
                    f"**Espiras:** {m.get('espira_principal') or m.get('espiras_princ') or '---'}")
            
            st.warning(f"**Auxiliar**\n\n**Passo:** {m.get('passo_auxiliar') or m.get('passo_aux') or '---'}  \n"
                       f"**Fio:** {m.get('fio_auxiliar') or m.get('fio_aux') or '---'}  \n"
                       f"**Espiras:** {m.get('espira_auxiliar') or m.get('espiras_aux') or '---'}")

            st.divider()

            # --- SEÇÃO 3: MECÂNICA E NÚCLEO (Compacto) ---
            st.markdown("#### ⚙️ Técnica e Núcleo")
            col3, col4 = st.columns(2)
            with col3:
                st.markdown(f"**Carcaça:**\n{m.get('carcaca') or '---'}")
                st.markdown(f"**IP:** {m.get('ip') or '---'}")
                st.markdown(f"**Ranhuras:** {m.get('numero_ranhuras') or '---'}")
                st.markdown(f"**Ø Fio:** {m.get('diametro_fio') or '---'}")
            with col4:
                st.markdown(f"**Polos:** {m.get('polos') or '---'}")
                st.markdown(f"**Ligação:** {m.get('ligacao') or '---'}")
                st.markdown(f"**Pacote:** {m.get('comprimento_pacote') or '---'}mm")
                st.markdown(f"**Ø Int:** {m.get('diametro_interno') or '---'}mm")

            # --- SEÇÃO 4: OBSERVAÇÕES ---
            if m.get('observacoes'):
                st.markdown("---")
                st.markdown(f"**📝 Obs:** {m.get('observacoes')}")

            st.caption(f"📅 {m.get('data_cadastro')} | Origem: {m.get('origem_calculo')}")

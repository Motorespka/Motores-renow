import streamlit as st
import importlib

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

def show(supabase): 
    st.title("🔍 Consulta de Motores Cadastrados")

    if "motor_editando" not in st.session_state:
        st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state:
        st.session_state.abrir_edit = False

    # Verificação de Modo Edição
    if st.session_state.abrir_edit and st.session_state.motor_editando:
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Fechar Edição"):
                st.session_state.abrir_edit = False
                st.session_state.motor_editando = None
                st.rerun()
            return
        except Exception as e:
            st.error(f"Erro ao carregar página de edição: {e}")

    motores = listar_motores(supabase)
    
    if not motores:
        st.info("Nenhum motor encontrado.")
        return

    for m in motores:
        id_motor = m.get('id')
        
        # Título do card com informações vitais
        titulo = f"🆔 {id_motor} | {m.get('marca') or 'S/M'} | {m.get('potencia') or '---'} | {m.get('rpm') or '---'} RPM"

        with st.expander(titulo):
            # Botões de Controle
            c_edit, c_excl, _ = st.columns([1, 1, 4])
            if c_edit.button("✏️ Editar", key=f"ed_{id_motor}"):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()
            if c_excl.button("🗑️ Excluir", key=f"ex_{id_motor}"):
                if excluir_motor(supabase, id_motor):
                    st.success("Excluído!")
                    st.rerun()

            st.markdown("---")

            # --- SEÇÃO 1: PLACA E IDENTIFICAÇÃO ---
            st.markdown("### 📌 Identificação da Placa")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Marca:** {m.get('marca') or '---'}")
                st.write(f"**Modelo:** {m.get('modelo') or '---'}")
                st.write(f"**Fabricante:** {m.get('fabricante') or '---'}")
            with col2:
                st.write(f"**Potência:** {m.get('potencia') or '---'}")
                st.write(f"**Tensão:** {m.get('tensao') or '---'}")
                st.write(f"**Corrente:** {m.get('corrente') or '---'}")
            with col3:
                st.write(f"**RPM:** {m.get('rpm') or '---'}")
                st.write(f"**Frequência:** {m.get('frequencia') or '---'}")
                st.write(f"**Rendimento:** {m.get('rendimento') or '---'}%")

            st.divider()

            # --- SEÇÃO 2: BOBINAGEM (Lógica de busca em dois campos) ---
            st.markdown("### 🌀 Detalhes do Enrolamento")
            col_p, col_a = st.columns(2)
            with col_p:
                st.info("**Enrolamento Principal**")
                # Busca no campo manual OU no campo OCR
                passo_p = m.get('passo_principal') or m.get('passo_princ') or "---"
                fio_p = m.get('fio_principal') or m.get('fio_princ') or "---"
                esp_p = m.get('espira_principal') or m.get('espiras_princ') or "---"
                st.write(f"**Passo:** {passo_p}")
                st.write(f"**Fio:** {fio_p}")
                st.write(f"**Espiras:** {esp_p}")
            
            with col_a:
                st.warning("**Enrolamento Auxiliar**")
                passo_a = m.get('passo_auxiliar') or m.get('passo_aux') or "---"
                fio_a = m.get('fio_auxiliar') or m.get('fio_aux') or "---"
                esp_a = m.get('espira_auxiliar') or m.get('espiras_aux') or "---"
                st.write(f"**Passo:** {passo_a}")
                st.write(f"**Fio:** {fio_a}")
                st.write(f"**Espiras:** {esp_a}")

            st.divider()

            # --- SEÇÃO 3: MECÂNICA E PROTEÇÃO ---
            st.markdown("### ⚙️ Características Mecânicas")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.write(f"**Carcaça:** {m.get('carcaca') or '---'}")
                st.write(f"**Polos:** {m.get('polos') or '---'}")
                st.write(f"**Montagem:** {m.get('montagem') or '---'}")
            with m2:
                st.write(f"**Isolação:** {m.get('isolacao') or '---'}")
                st.write(f"**IP:** {m.get('ip') or '---'}")
                st.write(f"**Regime:** {m.get('regime') or '---'}")
            with m3:
                st.write(f"**Rolamento D:** {m.get('rolamento_d') or '---'}")
                st.write(f"**Rolamento T:** {m.get('rolamento_t') or '---'}")
                st.write(f"**Peso:** {m.get('peso') or '---'} kg")

            st.divider()

            # --- SEÇÃO 4: DADOS TÉCNICOS DO NÚCLEO E LIGAÇÃO ---
            st.markdown("### 🧲 Dados Elétricos e Núcleo")
            d1, d2, d3 = st.columns(3)
            with d1:
                st.write(f"**Tipo Enrol.:** {m.get('tipo_enrolamento') or '---'}")
                st.write(f"**Nº Ranhuras:** {m.get('numero_ranhuras') or '---'}")
                st.write(f"**Ligação:** {m.get('ligacao') or '---'}")
            with d2:
                st.write(f"**Ø Fio:** {m.get('diametro_fio') or '---'} mm")
                st.write(f"**Tipo Fio:** {m.get('tipo_fio') or '---'}")
                st.write(f"**Resistência:** {m.get('resistencia') or '---'} Ω")
            with d3:
                st.write(f"**Ø Interno:** {m.get('diametro_interno') or '---'} mm")
                st.write(f"**Ø Externo:** {m.get('diametro_externo') or '---'} mm")
                st.write(f"**Pacote/Empilh.:** {m.get('comprimento_pacote') or '---'} / {m.get('empilhamento') or '---'} mm")

            # --- SEÇÃO 5: OBSERVAÇÕES E METADADOS ---
            st.markdown("---")
            st.info(f"**📝 Observações:** {m.get('observacoes') or 'Sem notas adicionais.'}")
            
            # Rodapé com informações de sistema
            st.caption(f"📍 Origem: {m.get('origem_calculo')} | 📂 Arquivo: {m.get('arquivo') or 'Manual'} | 📅 Cadastro: {m.get('data_cadastro')}")

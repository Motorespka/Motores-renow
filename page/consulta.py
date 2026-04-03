import streamlit as st
import importlib

# ------------------------------
# Operações no banco (SUPABASE)
# ------------------------------
def listar_motores(supabase):
    try:
        # Busca todos os campos da tabela motores
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
    st.title("🔍 Consulta de Motores Cadastrados")

    if "motor_editando" not in st.session_state:
        st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state:
        st.session_state.abrir_edit = False

    # Modo edição
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
        st.info("Nenhum motor cadastrado no banco de dados.")
        return

    st.subheader("📋 Lista de Motores")

    for m in motores:
        id_motor = m.get('id')
        cv_kw = m.get('potencia') or "---"
        polos = m.get('polos') or "---"
        rpm = m.get('rpm') or "---"
        amp = m.get('corrente') or "---"
        tensao = m.get('tensao') or "---"
        data_cadastro = m.get('data_cadastro') or "---"

        # Cabeçalho do Card
        titulo_expander = (
            f"🆔 {id_motor} | ⚡ {cv_kw} | 🎯 {polos}P | 🔄 {rpm} RPM | 🔌 {amp}A | 🔋 {tensao}V"
        )

        with st.expander(titulo_expander):
            # Ações rápidas
            col_btn1, col_btn2 = st.columns([1, 5])
            with col_btn1:
                if st.button("✏️ Editar", key=f"editar_{id_motor}"):
                    st.session_state.motor_editando = m
                    st.session_state.abrir_edit = True
                    st.rerun()
            with col_btn2:
                if st.button("🗑️ Excluir", key=f"excluir_{id_motor}"):
                    if excluir_motor(supabase, id_motor):
                        st.success(f"Motor ID {id_motor} excluído.")
                        st.rerun()

            st.markdown("---")

            # --- SEÇÃO 1: DADOS GERAIS ---
            st.markdown("### 📌 Dados Gerais e Placa")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**Marca:** {m.get('marca') or '---'}")
                st.write(f"**Modelo:** {m.get('modelo') or '---'}")
                st.write(f"**Fabricante:** {m.get('fabricante') or '---'}")
            with c2:
                st.write(f"**Potência:** {m.get('potencia') or '---'}")
                st.write(f"**Tensão:** {m.get('tensao') or '---'}")
                st.write(f"**Corrente:** {m.get('corrente') or '---'}")
            with c3:
                st.write(f"**RPM:** {m.get('rpm') or '---'}")
                st.write(f"**Frequência:** {m.get('frequencia') or '---'}")
                st.write(f"**Rendimento:** {m.get('rendimento') or '---'}%")

            st.divider()

            # --- SEÇÃO 2: BOBINAGEM (Lógica Dupla para os novos campos do SQL) ---
            st.markdown("### 🌀 Detalhes do Enrolamento")
            col_princ, col_aux = st.columns(2)
            
            with col_princ:
                st.info("**Enrolamento Principal**")
                # Tenta pegar do formulário (passo_principal), se não houver, pega do OCR (passo_princ)
                passo_p = m.get('passo_principal') or m.get('passo_princ') or "---"
                fio_p = m.get('fio_principal') or m.get('fio_princ') or "---"
                esp_p = m.get('espira_principal') or m.get('espiras_princ') or "---"
                
                st.write(f"**Passo:** {passo_p}")
                st.write(f"**Fio:** {fio_p}")
                st.write(f"**Espiras:** {esp_p}")

            with col_aux:
                st.warning("**Enrolamento Auxiliar**")
                passo_a = m.get('passo_auxiliar') or m.get('passo_aux') or "---"
                fio_a = m.get('fio_auxiliar') or m.get('fio_aux') or "---"
                esp_a = m.get('espira_auxiliar') or m.get('espiras_aux') or "---"
                
                st.write(f"**Passo:** {passo_a}")
                st.write(f"**Fio:** {fio_a}")
                st.write(f"**Espiras:** {esp_a}")

            st.divider()

            # --- SEÇÃO 3: CARACTERÍSTICAS MECÂNICAS ---
            st.markdown("### ⚙️ Características Técnicas e Mecânicas")
            c4, c5, c6 = st.columns(3)
            with c4:
                st.write(f"**Carcaça:** {m.get('carcaca') or '---'}")
                st.write(f"**Montagem:** {m.get('montagem') or '---'}")
                st.write(f"**Ventilação:** {m.get('ventilacao') or '---'}")
            with c5:
                st.write(f"**Isolação:** {m.get('isolacao') or '---'}")
                st.write(f"**IP:** {m.get('ip') or '---'}")
                st.write(f"**Regime:** {m.get('regime') or '---'}")
            with c6:
                st.write(f"**Fator Serviço:** {m.get('fator_servico') or '---'}")
                st.write(f"**Peso:** {m.get('peso') or '---'} kg")
                st.write(f"**Rolamento D/T:** {m.get('rolamento_d') or '-'}/{m.get('rolamento_t') or '-'}")

            st.divider()

            # --- SEÇÃO 4: DADOS DO NÚCLEO E ELÉTRICOS ---
            st.markdown("### 🧲 Dados Elétricos e Núcleo")
            c7, c8, c9 = st.columns(3)
            with c7:
                st.write(f"**Tipo Enrolamento:** {m.get('tipo_enrolamento') or '---'}")
                st.write(f"**Nº Ranhuras:** {m.get('numero_ranhuras') or '---'}")
                st.write(f"**Ligação:** {m.get('ligacao') or '---'}")
            with c8:
                st.write(f"**Ø Fio:** {m.get('diametro_fio') or '---'} mm")
                st.write(f"**Tipo Fio:** {m.get('tipo_fio') or '---'}")
                st.write(f"**Resistência:** {m.get('resistencia') or '---'} Ω")
            with c9:
                st.write(f"**Ø Interno:** {m.get('diametro_interno') or '---'} mm")
                st.write(f"**Comp. Pacote:** {m.get('comprimento_pacote') or '---'} mm")
                st.write(f"**Empilhamento:** {m.get('empilhamento') or '---'} mm")

            # --- SEÇÃO 5: OBSERVAÇÕES ---
            st.markdown("---")
            st.markdown(f"**Observações:** {m.get('observacoes') or 'Sem observações.'}")
            st.caption(f"Arquivo: {m.get('arquivo') or 'N/A'} | Origem: {m.get('origem_calculo')} | Cadastrado em: {data_cadastro}")

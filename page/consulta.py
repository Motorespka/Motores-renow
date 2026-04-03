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
        st.info("Nenhum motor cadastrado ainda no Supabase.")
        return

    st.subheader("📋 Lista de Motores")

    for m in motores:
        id_motor = m.get('id')
        cv_kw = m.get('potencia') or "N/A"
        polos = m.get('polos') or "N/A"
        rpm = m.get('rpm') or "N/A"
        amp = m.get('corrente') or "N/A"
        tensao = m.get('tensao') or "N/A"
        data_cadastro = m.get('data_cadastro') or "N/A"

        # Cabeçalho do card (Resumo rápido)
        titulo_expander = (
            f"🆔 {id_motor} | ⚡ {cv_kw} | 🎯 {polos}P | 🔄 {rpm} RPM | 🔌 {amp}A | 🔋 {tensao}V"
        )

        with st.expander(titulo_expander):
            # Botões de Ação
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

            # 📌 Seção 1: Dados Gerais (Principais)
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

            # 🌀 Seção 2: Bobinagem (CHAVES CORRIGIDAS PARA O SEU CADASTRO)
            st.markdown("### 🌀 Detalhes do Enrolamento")
            col_princ, col_aux = st.columns(2)
            with col_princ:
                st.info("**Enrolamento Principal**")
                st.write(f"**Passo:** {m.get('passo_principal') or 'N/A'}")
                st.write(f"**Fio:** {m.get('fio_principal') or 'N/A'}")
                st.write(f"**Espiras:** {m.get('espira_principal') or 'N/A'}")
            with col_aux:
                st.warning("**Enrolamento Auxiliar**")
                st.write(f"**Passo:** {m.get('passo_auxiliar') or 'N/A'}")
                st.write(f"**Fio:** {m.get('fio_auxiliar') or 'N/A'}")
                st.write(f"**Espiras:** {m.get('espira_auxiliar') or 'N/A'}")

            st.divider()

            # ⚙️ Seção 3: Características Técnicas (Acrescentado Montagem, Regime, etc)
            st.markdown("### ⚙️ Características Técnicas e Mecânicas")
            c4, c5, c6 = st.columns(3)
            with c4:
                st.write(f"**Polos:** {m.get('polos') or '---'}")
                st.write(f"**Carcaça:** {m.get('carcaca') or '---'}")
                st.write(f"**Montagem:** {m.get('montagem') or '---'}")
            with c5:
                st.write(f"**Isolação:** {m.get('isolacao') or '---'}")
                st.write(f"**IP:** {m.get('ip') or '---'}")
                st.write(f"**Regime:** {m.get('regime') or '---'}")
            with c6:
                st.write(f"**Fator Serviço:** {m.get('fator_servico') or '---'}")
                st.write(f"**Peso:** {m.get('peso') or '---'} kg")
                st.write(f"**Ventilação:** {m.get('ventilacao') or '---'}")

            st.divider()

            # 🧲 Seção 4: Dados Elétricos e Núcleo (Acrescentado Diâmetro e Tipo de Fio)
            st.markdown("### 🧲 Dados Elétricos e Núcleo")
            c7, c8, c9 = st.columns(3)
            with c7:
                st.write(f"**Tipo Enrolamento:** {m.get('tipo_enrolamento') or '---'}")
                st.write(f"**Nº Ranhuras:** {m.get('numero_ranhuras') or '---'}")
                st.write(f"**Resistência:** {m.get('resistencia') or '---'} Ω")
            with c8:
                st.write(f"**Ø Fio:** {m.get('diametro_fio') or '---'} mm")
                st.write(f"**Tipo Fio:** {m.get('tipo_fio') or '---'}")
                st.write(f"**Ligação:** {m.get('ligacao') or '---'}")
            with c9:
                st.write(f"**Ø Interno:** {m.get('diametro_interno') or '---'} mm")
                st.write(f"**Comp. Pacote:** {m.get('comprimento_pacote') or '---'} mm")
                st.write(f"**Empilhamento:** {m.get('empilhamento') or '---'} mm")

            # 📝 Seção 5: Observações
            st.markdown("---")
            st.markdown(f"**Observações:** {m.get('observacoes') or 'Sem observações.'}")
            st.caption(f"Origem do cálculo: {m.get('origem_calculo') or 'N/A'} | Cadastrado em: {data_cadastro}")

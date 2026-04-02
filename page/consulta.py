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

            # 📌 Seção 1: Dados Gerais
            st.markdown("### 📌 Dados Gerais")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**Marca:** {m.get('marca', '')}")
                st.write(f"**Modelo:** {m.get('modelo', '')}")
                st.write(f"**Fabricante:** {m.get('fabricante', '')}")
            with c2:
                st.write(f"**Potência:** {m.get('potencia', '')}")
                st.write(f"**Tensão:** {m.get('tensao', '')}")
                st.write(f"**Corrente:** {m.get('corrente', '')}")
            with c3:
                st.write(f"**RPM:** {m.get('rpm', '')}")
                st.write(f"**Frequência:** {m.get('frequencia', '')}")
                st.write(f"**Rendimento:** {m.get('rendimento', '')}%")

            st.divider()

            # 🌀 Seção 2: Bobinagem (CAMPOS NOVOS)
            st.markdown("### 🌀 Detalhes do Enrolamento")
            col_princ, col_aux = st.columns(2)
            with col_princ:
                st.info("**Enrolamento Principal**")
                st.write(f"**Passo:** {m.get('passo_principal', 'N/A')}")
                st.write(f"**Fio:** {m.get('fio_principal', 'N/A')}")
                st.write(f"**Espiras:** {m.get('espira_principal', 'N/A')}")
            with col_aux:
                st.warning("**Enrolamento Auxiliar**")
                st.write(f"**Passo:** {m.get('passo_auxiliar', 'N/A')}")
                st.write(f"**Fio:** {m.get('fio_auxiliar', 'N/A')}")
                st.write(f"**Espiras:** {m.get('espira_auxiliar', 'N/A')}")

            st.divider()

            # ⚙️ Seção 3: Características Técnicas
            st.markdown("### ⚙️ Características Técnicas e Mecânicas")
            c4, c5, c6 = st.columns(3)
            with c4:
                st.write(f"**Polos:** {m.get('polos', '')}")
                st.write(f"**Carcaça:** {m.get('carcaca', '')}")
                st.write(f"**Isolação:** {m.get('isolacao', '')}")
            with c5:
                st.write(f"**IP:** {m.get('ip', '')}")
                st.write(f"**Fator Serviço:** {m.get('fator_servico', '')}")
                st.write(f"**Peso:** {m.get('peso', '')} kg")
            with c6:
                st.write(f"**Rolamento D:** {m.get('rolamento_d', '')}")
                st.write(f"**Rolamento T:** {m.get('rolamento_t', '')}")
                st.write(f"**Ventilação:** {m.get('ventilacao', '')}")

            st.divider()

            # 🧲 Seção 4: Dados do Estator e Elétricos
            st.markdown("### 🧲 Dados do Estator e Ligação")
            c7, c8 = st.columns(2)
            with c7:
                st.write(f"**Tipo Enrolamento:** {m.get('tipo_enrolamento', '')}")
                st.write(f"**Nº Ranhuras:** {m.get('numero_ranhuras', '')}")
                st.write(f"**Ligação:** {m.get('ligacao', '')}")
                st.write(f"**Resistência:** {m.get('resistencia', '')} Ω")
            with c8:
                st.write(f"**Ø Interno:** {m.get('diametro_interno', '')} mm")
                st.write(f"**Comp. Pacote:** {m.get('comprimento_pacote', '')} mm")
                st.write(f"**Empilhamento:** {m.get('empilhamento', '')} mm")

            # 📝 Seção 5: Observações
            st.markdown("---")
            st.markdown(f"**Observações:** {m.get('observacoes', 'Sem observações.')}")
            st.caption(f"Origem do cálculo: {m.get('origem_calculo', 'N/A')} | Cadastrado em: {data_cadastro}")

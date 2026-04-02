import streamlit as st
import importlib

# ------------------------------
# Operações no banco (AGORA COM SUPABASE)
# ------------------------------
def listar_motores(supabase):
    try:
        # Busca todos os motores ordenados pelo ID decrescente
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        return res.data # Retorna uma lista de dicionários
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
def show(supabase): # Recebe o cliente supabase do app.py
    st.title("🔍 Consulta de Motores Cadastrados")

    # Inicializa sessão para edição
    if "motor_editando" not in st.session_state:
        st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state:
        st.session_state.abrir_edit = False

    # Modo edição temporário
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

    # Busca os dados no Supabase
    motores = listar_motores(supabase)
    
    if not motores:
        st.info("Nenhum motor cadastrado ainda no Supabase.")
        return

    st.subheader("📋 Lista de Motores")

    for m in motores:
        # No Supabase os dados vêm como Dicionário, então usamos chaves ['nome']
        id_motor = m.get('id')
        cv_kw = m.get('potencia') or "N/A"
        polos = m.get('polos') or "N/A"
        rpm = m.get('rpm') or "N/A"
        amp = m.get('corrente') or "N/A"
        tensao = m.get('tensao') or "N/A"
        data_cadastro = m.get('data_cadastro') or "N/A"

        titulo_expander = (
            f"🆔 ID: {id_motor}     "
            f"⚡ Potência: {cv_kw}     "
            f"🎯 Polos: {polos}     "
            f"🔄 RPM: {rpm}     "
            f"🔌 Amp: {amp}     "
            f"🔋 Tensão: {tensao}     "
            f"🗓️ Cadastrado: {data_cadastro}"
        )

        with st.expander(titulo_expander):
            col1, col2 = st.columns(2)

            # Botão Editar
            with col1:
                if st.button("✏️ Editar", key=f"editar_{id_motor}"):
                    st.session_state.motor_editando = m # Salva o dicionário completo
                    st.session_state.abrir_edit = True
                    st.rerun()

            # Botão Excluir
            with col2:
                if st.button("🗑️ Excluir", key=f"excluir_{id_motor}"):
                    if excluir_motor(supabase, id_motor):
                        st.success(f"Motor ID {id_motor} excluído com sucesso.")
                        st.rerun()

            # ------------------------------
            # Dados completos em colunas (Usando chaves do dicionário)
            # ------------------------------
            st.markdown("## ⚙️ Cadastro Completo de Motor")

            # 📌 Dados Gerais
            st.markdown("### 📌 Dados Gerais")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"Marca: {m.get('marca', '')}")
                st.write(f"Modelo: {m.get('modelo', '')}")
                st.write(f"Fabricante: {m.get('fabricante', '')}")
                st.write(f"Potência (CV/kW): {m.get('potencia', '')}")
            with c2:
                st.write(f"Tensão (V): {m.get('tensao', '')}")
                st.write(f"Corrente (A): {m.get('corrente', '')}")
                st.write(f"RPM: {m.get('rpm', '')}")
                st.write(f"Frequência (Hz): {m.get('frequencia', '')}")
            with c3:
                st.write(f"Rendimento (%): {m.get('rendimento', '')}")
                st.write(f"Número de Polos: {m.get('polos', '')}")
                st.write(f"Carcaça: {m.get('carcaca', '')}")
                st.write(f"Tipo de Montagem: {m.get('montagem', '')}")

            # ⚙️ Características Construtivas
            st.markdown("### ⚙️ Características Construtivas")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"Classe de Isolação: {m.get('isolacao', '')}")
                st.write(f"Grau de Proteção (IP): {m.get('ip', '')}")
                st.write(f"Regime de Serviço: {m.get('regime', '')}")
            with c2:
                st.write(f"Fator de Serviço: {m.get('fator_servico', '')}")
                st.write(f"Classe de Temperatura: {m.get('temperatura', '')}")
                st.write(f"Altitude Máx. de Operação: {m.get('altitude', '')}")
            with c3:
                st.write(f"Rolamento Dianteiro: {m.get('rolamento_d', '')}")
                st.write(f"Rolamento Traseiro: {m.get('rolamento_t', '')}")
                st.write(f"Diâmetro do Eixo (mm): {m.get('eixo_diametro', '')}")
                st.write(f"Comprimento do Eixo (mm): {m.get('comprimento_eixo', '')}")

            # 🔩 Rolamentos e Mecânica
            st.markdown("### 🔩 Rolamentos e Mecânica")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"Peso (kg): {m.get('peso', '')}")
                st.write(f"Tipo de Ventilação: {m.get('ventilacao', '')}")
            with c2:
                st.write(f"Tipo de Enrolamento: {m.get('tipo_enrolamento', '')}")
                st.write(f"Passo da Bobina: {m.get('passo_bobina', '')}")
                st.write(f"Número de Ranhuras: {m.get('numero_ranhuras', '')}")
                st.write(f"Fios em Paralelo: {m.get('fios_paralelos', '')}")
                st.write(f"Diâmetro do Fio (mm): {m.get('diametro_fio', '')}")
                st.write(f"Tipo de Fio: {m.get('tipo_fio', '')}")
                st.write(f"Ligação: {m.get('ligacao', '')}")
                st.write(f"Esquema de Ligação: {m.get('esquema', '')}")
                st.write(f"Resistência (Ω): {m.get('resistencia', '')}")

            # 🧲 Dados do Induzido / Estator
            st.markdown("### 🧲 Dados do Induzido / Estator")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"Diâmetro Interno do Estator (mm): {m.get('diametro_interno', '')}")
                st.write(f"Diâmetro Externo (mm): {m.get('diametro_externo', '')}")
                st.write(f"Comprimento do Pacote (mm): {m.get('comprimento_pacote', '')}")
            with c2:
                st.write(f"Material do Núcleo: {m.get('material_nucleo', '')}")
                st.write(f"Tipo de Chapa: {m.get('tipo_chapa', '')}")
                st.write(f"Empilhamento (mm): {m.get('empilhamento', '')}")

            # 📝 Informações Adicionais
            st.markdown("### 📝 Informações Adicionais")
            st.write(f"Observações Gerais: {m.get('observacoes', '')}")
            st.write(f"Origem do cálculo: {m.get('origem_calculo', '')}")
            

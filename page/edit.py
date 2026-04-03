import streamlit as st

from use_cases.listar_motores import consultar_motores


def _update_motor_supabase(supabase, id_motor: int, payload: dict) -> None:
    supabase.table("motores").update(payload).eq("id", id_motor).execute()


def show(supabase):
    st.title("✏️ Editar Motor")

    motor = st.session_state.get("motor_editando")
    if not motor:
        st.warning("Nenhum motor selecionado para edição.")
        if st.button("🔙 Voltar para Consulta", use_container_width=True):
            st.session_state.pagina = "consulta"
            st.rerun()
        return

    id_motor = motor.get("id")
    if not id_motor:
        st.error("Motor sem ID. Não é possível editar.")
        if st.button("🔙 Voltar para Consulta", use_container_width=True):
            st.session_state.pagina = "consulta"
            st.rerun()
        return

    # Card header (mesmo padrão estético)
    marca_hdr = motor.get("marca") or "---"
    modelo_hdr = motor.get("modelo") or ""
    st.markdown('<div class="motor-card">', unsafe_allow_html=True)
    st.markdown(f"#### 🆔 #{id_motor} • {marca_hdr} {modelo_hdr}")
    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("edit_motor_form"):
        st.markdown('<div class="motor-card">', unsafe_allow_html=True)
        st.markdown("#### 📌 Identificação e Placa")

        marca = st.text_input("Marca", value=motor.get("marca") or "")
        modelo = st.text_input("Modelo", value=motor.get("modelo") or "")
        fabricante = st.text_input("Fabricante", value=motor.get("fabricante") or "")

        st.divider()

        potencia = st.text_input("Potência (CV/kW)", value=motor.get("potencia") or "")
        tensao = st.text_input("Tensão (V)", value=motor.get("tensao") or "")
        corrente = st.text_input("Corrente (A)", value=motor.get("corrente") or "")

        st.divider()

        rpm = st.text_input("RPM", value=motor.get("rpm") or "")
        frequencia = st.text_input("Frequência (Hz)", value=motor.get("frequencia") or "")
        rendimento = st.text_input("Rendimento (%)", value=motor.get("rendimento") or "")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="motor-card">', unsafe_allow_html=True)
        st.markdown("#### 🛠️ Mecânica")

        polos = st.text_input("Pólos", value=motor.get("polos") or "")
        carcaca = st.text_input("Carcaça", value=motor.get("carcaca") or "")
        montagem = st.text_input("Montagem", value=motor.get("montagem") or "")

        st.divider()

        isolacao = st.text_input("Isolação", value=motor.get("isolacao") or "")
        ip = st.text_input("Grau Proteção (IP)", value=motor.get("ip") or "")
        regime = st.text_input("Regime", value=motor.get("regime") or "")

        st.divider()

        fator_servico = st.text_input("Fator de Serviço", value=motor.get("fator_servico") or "")
        peso = st.text_input("Peso (kg)", value=motor.get("peso") or "")
        ventilacao = st.text_input("Ventilação", value=motor.get("ventilacao") or "")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="motor-card">', unsafe_allow_html=True)
        st.markdown("#### 🌀 Bobinagem")

        st.markdown("**Enrolamento Principal**")
        passo_principal = st.text_input(
            "Passo Principal",
            value=motor.get("passo_principal") or motor.get("passo_princ") or "",
        )
        fio_principal = st.text_input(
            "Fio Principal",
            value=motor.get("fio_principal") or motor.get("fio_princ") or "",
        )
        espira_principal = st.text_input(
            "Espiras Principal",
            value=motor.get("espira_principal") or motor.get("espiras_princ") or "",
        )

        st.divider()

        st.markdown("**Enrolamento Auxiliar**")
        passo_auxiliar = st.text_input(
            "Passo Auxiliar",
            value=motor.get("passo_auxiliar") or motor.get("passo_aux") or "",
        )
        fio_auxiliar = st.text_input(
            "Fio Auxiliar",
            value=motor.get("fio_auxiliar") or motor.get("fio_aux") or "",
        )
        espira_auxiliar = st.text_input(
            "Espiras Auxiliar",
            value=motor.get("espira_auxiliar") or motor.get("espiras_aux") or "",
        )

        st.divider()

        st.markdown("#### ⚡ Dados Elétricos e Núcleo")
        tipo_enrolamento = st.text_input("Tipo Enrolamento", value=motor.get("tipo_enrolamento") or "")
        numero_ranhuras = st.text_input("Nº Ranhuras", value=motor.get("numero_ranhuras") or "")
        resistencia = st.text_input("Resistência (Ω)", value=motor.get("resistencia") or "")

        st.divider()

        diametro_fio = st.text_input("Diâmetro Fio (mm)", value=motor.get("diametro_fio") or "")
        tipo_fio = st.text_input("Tipo de Fio", value=motor.get("tipo_fio") or "")
        ligacao = st.selectbox(
            "Ligação",
            ["Estrela", "Triângulo", "Série", "Paralelo"],
            index=["Estrela", "Triângulo", "Série", "Paralelo"].index(motor.get("ligacao"))
            if motor.get("ligacao") in ["Estrela", "Triângulo", "Série", "Paralelo"]
            else 0,
        )

        st.divider()

        diametro_interno = st.text_input("Ø Interno (mm)", value=motor.get("diametro_interno") or "")
        comprimento_pacote = st.text_input("Comp. Pacote (mm)", value=motor.get("comprimento_pacote") or "")
        empilhamento = st.text_input("Empilhamento (mm)", value=motor.get("empilhamento") or "")

        st.divider()

        st.markdown("#### 📝 Observações")
        observacoes = st.text_area("Notas técnicas adicionais", value=motor.get("observacoes") or "")

        st.markdown("#### 📍 Origem do Cálculo")
        origem = st.selectbox(
            "Origem do Cálculo",
            ["União", "Rebobinador", "Próprio"],
            index=["União", "Rebobinador", "Próprio"].index(motor.get("origem_calculo"))
            if motor.get("origem_calculo") in ["União", "Rebobinador", "Próprio"]
            else 0,
        )

        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            salvar = st.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True)
        with c2:
            voltar = st.form_submit_button("🔙 VOLTAR", use_container_width=True)

    if voltar:
        st.session_state.motor_editando = None
        st.session_state.pagina = "consulta"
        st.rerun()

    if salvar:
        payload = {
            "marca": marca,
            "modelo": modelo,
            "fabricante": fabricante,
            "potencia": potencia,
            "tensao": tensao,
            "corrente": corrente,
            "rpm": rpm,
            "frequencia": frequencia,
            "rendimento": rendimento,
            "polos": polos,
            "carcaca": carcaca,
            "montagem": montagem,
            "isolacao": isolacao,
            "ip": ip,
            "regime": regime,
            "fator_servico": fator_servico,
            "peso": peso,
            "ventilacao": ventilacao,
            "passo_principal": passo_principal,
            "passo_princ": passo_principal,
            "fio_principal": fio_principal,
            "fio_princ": fio_principal,
            "espira_principal": espira_principal,
            "espiras_princ": espira_principal,
            "passo_auxiliar": passo_auxiliar,
            "passo_aux": passo_auxiliar,
            "fio_auxiliar": fio_auxiliar,
            "fio_aux": fio_auxiliar,
            "espira_auxiliar": espira_auxiliar,
            "espiras_aux": espira_auxiliar,
            "tipo_enrolamento": tipo_enrolamento,
            "numero_ranhuras": numero_ranhuras,
            "resistencia": resistencia,
            "diametro_fio": diametro_fio,
            "tipo_fio": tipo_fio,
            "ligacao": ligacao,
            "diametro_interno": diametro_interno,
            "comprimento_pacote": comprimento_pacote,
            "empilhamento": empilhamento,
            "observacoes": observacoes,
            "origem_calculo": origem,
        }

        try:
            _update_motor_supabase(supabase, id_motor, payload)
            try:
                consultar_motores.clear()
            except Exception:
                pass

            st.success("✅ Alterações salvas!")
            # Atualiza o estado local pra refletir o que foi salvo
            st.session_state.motor_editando = {"id": id_motor, **payload}
            st.session_state.pagina = "consulta"
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao salvar alterações: {e}")

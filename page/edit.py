from __future__ import annotations

import streamlit as st

from services.supabase_data import clear_motores_cache, fetch_motor_by_id_cached
from use_cases.listar_motores import consultar_motores


def _txt(value) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in {"none", "nan", "null"}:
        return ""
    return s


def _update_motor_supabase(supabase, id_motor: int, payload: dict) -> None:
    supabase.table("motores").update(payload).eq("id", id_motor).execute()


def _build_payload(motor_atual: dict, values: dict) -> dict:
    payload = {}
    # Atualiza apenas campos existentes no registro retornado pelo banco
    for key, val in values.items():
        if key in motor_atual:
            payload[key] = val if val != "" else None
    return payload


def show(supabase):
    st.title("Editar Motor")

    motor = st.session_state.get("motor_editando")
    if not motor:
        st.warning("Nenhum motor selecionado para edicao.")
        if st.button("Voltar para consulta", use_container_width=True):
            st.session_state.pagina = "consulta"
            st.rerun()
        return

    id_motor = motor.get("id")
    if not id_motor:
        st.error("Motor sem ID. Nao e possivel editar.")
        if st.button("Voltar para consulta", use_container_width=True):
            st.session_state.pagina = "consulta"
            st.rerun()
        return

    # Recarrega do banco para garantir dados atuais.
    try:
        motor_db = fetch_motor_by_id_cached(supabase, int(id_motor))
        if motor_db:
            motor = motor_db
            st.session_state.motor_editando = motor_db
    except Exception:
        pass

    st.caption(f"ID #{id_motor} | {_txt(motor.get('marca'))} {_txt(motor.get('modelo'))}")

    with st.form("edit_motor_form"):
        st.markdown("### Identificacao")
        col1, col2, col3 = st.columns(3)
        with col1:
            marca = st.text_input("Marca", value=_txt(motor.get("marca")))
            modelo = st.text_input("Modelo", value=_txt(motor.get("modelo")))
            fabricante = st.text_input("Fabricante", value=_txt(motor.get("fabricante")))
        with col2:
            num_serie = st.text_input("Numero de serie", value=_txt(motor.get("num_serie")))
            norma = st.text_input("Norma", value=_txt(motor.get("norma")))
            origem_registro = st.text_input("Origem do registro", value=_txt(motor.get("origem_registro")))
        with col3:
            fases = st.text_input("Fases", value=_txt(motor.get("fases")))
            polos = st.text_input("Polos", value=_txt(motor.get("polos") or motor.get("numero_polos")))
            carcaca = st.text_input("Carcaca", value=_txt(motor.get("carcaca")))

        st.markdown("### Dados eletricos")
        col4, col5, col6 = st.columns(3)
        with col4:
            potencia_hp_cv = st.text_input("Potencia (HP/CV)", value=_txt(motor.get("potencia_hp_cv")))
            potencia_kw = st.text_input("Potencia (kW)", value=_txt(motor.get("potencia_kw")))
            tensao_v = st.text_input("Tensao (V)", value=_txt(motor.get("tensao_v")))
        with col5:
            corrente_nominal_a = st.text_input("Corrente nominal (A)", value=_txt(motor.get("corrente_nominal_a")))
            rpm_nominal = st.text_input("RPM nominal", value=_txt(motor.get("rpm_nominal")))
            frequencia_hz = st.text_input("Frequencia (Hz)", value=_txt(motor.get("frequencia_hz")))
        with col6:
            fator_servico = st.text_input("Fator de servico", value=_txt(motor.get("fator_servico")))
            rendimento_perc = st.text_input("Rendimento (%)", value=_txt(motor.get("rendimento_perc")))
            classe_isolacao = st.text_input("Classe de isolacao", value=_txt(motor.get("classe_isolacao")))

        st.markdown("### Bobinagem")
        col7, col8 = st.columns(2)
        with col7:
            passo_principal = st.text_input("Passo principal", value=_txt(motor.get("passo_principal")))
            bitola_fio_principal = st.text_input("Bitola fio principal", value=_txt(motor.get("bitola_fio_principal")))
            espiras_principal = st.text_input("Espiras principal", value=_txt(motor.get("espiras_principal")))
            passo_auxiliar = st.text_input("Passo auxiliar", value=_txt(motor.get("passo_auxiliar")))
            bitola_fio_auxiliar = st.text_input("Bitola fio auxiliar", value=_txt(motor.get("bitola_fio_auxiliar")))
            espiras_auxiliar = st.text_input("Espiras auxiliar", value=_txt(motor.get("espiras_auxiliar")))
        with col8:
            tipo_enrolamento = st.text_input("Tipo de enrolamento", value=_txt(motor.get("tipo_enrolamento")))
            fios_paralelos = st.text_input("Fios em paralelo", value=_txt(motor.get("fios_paralelos")))
            ligacao_interna = st.text_input("Ligacao interna", value=_txt(motor.get("ligacao_interna")))
            numero_ranhuras = st.text_input("Numero de ranhuras", value=_txt(motor.get("numero_ranhuras")))
            capacitor_partida = st.text_input("Capacitor de partida", value=_txt(motor.get("capacitor_partida")))
            capacitor_permanente = st.text_input("Capacitor permanente", value=_txt(motor.get("capacitor_permanente")))

        st.markdown("### Mecanica")
        col9, col10, col11 = st.columns(3)
        with col9:
            rolamento_dianteiro = st.text_input("Rolamento dianteiro", value=_txt(motor.get("rolamento_dianteiro")))
            rolamento_traseiro = st.text_input("Rolamento traseiro", value=_txt(motor.get("rolamento_traseiro")))
            tipo_graxa = st.text_input("Tipo de graxa", value=_txt(motor.get("tipo_graxa")))
        with col10:
            diametro_interno_estator_mm = st.text_input(
                "Diametro interno estator (mm)", value=_txt(motor.get("diametro_interno_estator_mm"))
            )
            diametro_externo_estator_mm = st.text_input(
                "Diametro externo estator (mm)", value=_txt(motor.get("diametro_externo_estator_mm"))
            )
            comprimento_pacote_mm = st.text_input("Comprimento pacote (mm)", value=_txt(motor.get("comprimento_pacote_mm")))
        with col11:
            grau_protecao_ip = st.text_input("Grau de protecao (IP)", value=_txt(motor.get("grau_protecao_ip")))
            regime_servico = st.text_input("Regime de servico", value=_txt(motor.get("regime_servico")))
            peso_total_kg = st.text_input("Peso total (kg)", value=_txt(motor.get("peso_total_kg")))

        observacoes = st.text_area("Observacoes", value=_txt(motor.get("observacoes")))

        c1, c2 = st.columns(2)
        with c1:
            salvar = st.form_submit_button("Salvar alteracoes", use_container_width=True)
        with c2:
            voltar = st.form_submit_button("Voltar", use_container_width=True)

    if voltar:
        st.session_state.motor_editando = None
        st.session_state.pagina = "consulta"
        st.rerun()

    if salvar:
        valores = {
            "marca": marca,
            "modelo": modelo,
            "fabricante": fabricante,
            "num_serie": num_serie,
            "norma": norma,
            "origem_registro": origem_registro,
            "fases": fases,
            "polos": polos,
            "carcaca": carcaca,
            "potencia_hp_cv": potencia_hp_cv,
            "potencia_kw": potencia_kw,
            "tensao_v": tensao_v,
            "corrente_nominal_a": corrente_nominal_a,
            "rpm_nominal": rpm_nominal,
            "frequencia_hz": frequencia_hz,
            "fator_servico": fator_servico,
            "rendimento_perc": rendimento_perc,
            "classe_isolacao": classe_isolacao,
            "passo_principal": passo_principal,
            "bitola_fio_principal": bitola_fio_principal,
            "espiras_principal": espiras_principal,
            "passo_auxiliar": passo_auxiliar,
            "bitola_fio_auxiliar": bitola_fio_auxiliar,
            "espiras_auxiliar": espiras_auxiliar,
            "tipo_enrolamento": tipo_enrolamento,
            "fios_paralelos": fios_paralelos,
            "ligacao_interna": ligacao_interna,
            "numero_ranhuras": numero_ranhuras,
            "capacitor_partida": capacitor_partida,
            "capacitor_permanente": capacitor_permanente,
            "rolamento_dianteiro": rolamento_dianteiro,
            "rolamento_traseiro": rolamento_traseiro,
            "tipo_graxa": tipo_graxa,
            "diametro_interno_estator_mm": diametro_interno_estator_mm,
            "diametro_externo_estator_mm": diametro_externo_estator_mm,
            "comprimento_pacote_mm": comprimento_pacote_mm,
            "grau_protecao_ip": grau_protecao_ip,
            "regime_servico": regime_servico,
            "peso_total_kg": peso_total_kg,
            "observacoes": observacoes,
        }

        payload = _build_payload(motor, valores)
        if not payload:
            st.warning("Nenhum campo elegivel para atualizacao foi encontrado.")
            return

        try:
            _update_motor_supabase(supabase, int(id_motor), payload)
            try:
                consultar_motores.clear()
            except Exception:
                pass
            clear_motores_cache()

            st.success("Alteracoes salvas com sucesso.")
            st.session_state.motor_editando = {"id": id_motor, **motor, **payload}
            st.session_state.pagina = "consulta"
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar alteracoes: {e}")

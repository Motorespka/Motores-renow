import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# --- Config de caminho ---
file_path = Path(__file__).resolve()
root_path = file_path.parents[1]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# --- Import seguro ---
try:
    from core.calculadora import alertas_validacao_projeto, sugerir_equivalentes_paralelos
    from services.supabase_data import clear_motores_cache
except ImportError as e:
    st.error(f"Erro de estrutura: modulo ausente: {e.name}")
    st.info("Rode o app a partir da raiz do projeto.")

    def alertas_validacao_projeto(_m):
        return []

    def sugerir_equivalentes_paralelos(_t):
        return []

    def clear_motores_cache():
        pass


def _load_css() -> None:
    css_path = root_path / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def salvar_motor_supabase(supabase, motor):
    try:
        motor["data_cadastro"] = datetime.now().isoformat()
        res = supabase.table("motores").insert(motor).execute()
        if res.data:
            return True, "Motor salvo com sucesso no Supabase."
        return False, f"Erro ao salvar: {res}"
    except Exception as e:
        return False, f"Erro de conexao: {str(e)}"


def _safe_rerun() -> None:
    rerun_fn = getattr(st, "rerun", None)
    if callable(rerun_fn):
        rerun_fn()
        return

    rerun_fn = getattr(st, "experimental_rerun", None)
    if callable(rerun_fn):
        rerun_fn()
        return


def _camera_capture_panel() -> None:
    if "abrir_camera_placa" not in st.session_state:
        st.session_state.abrir_camera_placa = False

    with st.expander("Captura da placa (sob demanda)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Abrir camera", key="btn_abrir_camera_placa", use_container_width=True):
                st.session_state.abrir_camera_placa = True
        with c2:
            if st.button("Fechar camera", key="btn_fechar_camera_placa", use_container_width=True):
                st.session_state.abrir_camera_placa = False
                st.session_state.pop("foto_placa_capturada", None)

        if st.session_state.abrir_camera_placa:
            st.info(
                "A camera so fica ativa nesta secao. Em celular, selecione a camera traseira "
                "no seletor do navegador/sistema."
            )
            foto = st.camera_input("Tirar foto da placa", key="foto_placa_capturada")
            if foto is not None:
                try:
                    st.session_state.foto_placa_bytes = foto.getvalue()
                except Exception:
                    st.session_state.foto_placa_bytes = None
                st.success("Foto capturada.")
                st.session_state.abrir_camera_placa = False
                _safe_rerun()
        else:
            st.caption("Camera desligada. Clique em 'Abrir camera' para capturar.")


def show(supabase):
    _load_css()
    st.title("Cadastro de Motores - Moto-Renow")
    st.markdown("---")

    _camera_capture_panel()

    tabela_cores = {
        "Azul": "1",
        "Branco": "2",
        "Laranja": "3",
        "Amarelo": "4",
        "Preto": "5",
        "Vermelho": "6",
        "Verde": "Terra",
    }

    with st.form("cadastro_motor", clear_on_submit=False):
        with st.expander("Identificacao e placa", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                marca = st.text_input("Marca")
                modelo = st.text_input("Modelo")
                fabricante = st.text_input("Fabricante")
                num_serie = st.text_input("Numero de serie")
            with col2:
                potencia = st.text_input("Potencia (CV/kW)")
                tensao = st.text_input("Tensao (V)")
                corrente = st.text_input("Corrente (A)")
            with col3:
                rpm = st.text_input("RPM")
                frequencia = st.text_input("Frequencia (Hz)")
                rendimento = st.text_input("Rendimento (%)")

        with st.expander("Dados mecanicos", expanded=False):
            col4, col5, col6 = st.columns(3)
            with col4:
                polos = st.text_input("Polos")
                carcaca = st.text_input("Carcaca")
                norma = st.text_input("Norma", value="ABNT/IEC")
            with col5:
                isolacao = st.text_input("Classe isolacao", value="F")
                ip = st.text_input("Grau protecao (IP)", value="IP55")
                regime = st.text_input("Regime", value="S1")
            with col6:
                fator_servico = st.text_input("Fator de servico", value="1.0")
                peso = st.text_input("Peso total (kg)")
                tipo_graxa = st.text_input("Tipo de graxa")

        with st.expander("Dados de bobinagem e nucleo", expanded=False):
            col_princ, col_aux = st.columns(2)
            with col_princ:
                st.markdown("**Enrolamento principal**")
                passo_principal = st.text_input("Passo principal")
                fio_principal = st.text_input("Bitola fio principal")
                espira_principal = st.text_input("Espiras principal")
            with col_aux:
                st.markdown("**Enrolamento auxiliar**")
                passo_auxiliar = st.text_input("Passo auxiliar")
                fio_auxiliar = st.text_input("Bitola fio auxiliar")
                espira_auxiliar = st.text_input("Espiras auxiliar")

            st.divider()
            c1, c2, c3 = st.columns(3)
            with c1:
                tipo_enrolamento = st.text_input("Tipo enrolamento")
                numero_ranhuras = st.text_input("Numero ranhuras")
                fios_paralelos = st.text_input("Fios em paralelo")
            with c2:
                ligacao_interna = st.text_input("Ligacao interna")
                ligacao = st.selectbox("Ligacao placa", ["Estrela", "Triangulo", "Serie", "Paralelo"])
            with c3:
                diametro_interno = st.text_input("Diametro interno estator (mm)")
                comprimento_pacote = st.text_input("Comprimento pacote (mm)")

        with st.expander("Esquema de ligacao e cores", expanded=True):
            st.info("Consulte as cores abaixo para preencher o esquema se os fios nao tiverem numeros.")
            cols_cores = st.columns(len(tabela_cores))
            for i, (cor, num) in enumerate(tabela_cores.items()):
                cols_cores[i].metric(label=cor, value=num)

            st.divider()
            esquema = st.text_area(
                "Esquema de ligacao",
                placeholder="Ex: 110V: (1,3,5) e (2,4,6) | Cores: 1-Az, 2-Br...",
            )

        origem = st.selectbox("Origem do registro", ["Uniao", "Rebobinador", "OCR", "Manual"])
        observacoes = st.text_area("Observacoes")

        with st.expander("Equivalencia de fios (calculo rapido)"):
            fio_alvo = st.text_input("Se nao tiver o fio original, digite o AWG aqui:")
            if fio_alvo:
                sugestoes = sugerir_equivalentes_paralelos(fio_alvo)
                st.write(f"Opcoes para substituir o fio {fio_alvo}:", sugestoes)

        salvar = st.form_submit_button("Salvar no banco de dados", use_container_width=True)

    if salvar:
        motor = {
            "marca": marca,
            "modelo": modelo,
            "fabricante": fabricante,
            "num_serie": num_serie,
            "potencia_hp_cv": potencia,
            "tensao_v": tensao,
            "corrente_nominal_a": corrente,
            "rpm_nominal": rpm,
            "frequencia_hz": frequencia,
            "rendimento_perc": rendimento,
            "polos": polos,
            "carcaca": carcaca,
            "norma": norma,
            "classe_isolacao": isolacao,
            "grau_protecao_ip": ip,
            "regime_servico": regime,
            "fator_servico": fator_servico,
            "peso_total_kg": peso,
            "tipo_graxa": tipo_graxa,
            "passo_principal": passo_principal,
            "bitola_fio_principal": fio_principal,
            "espiras_principal": espira_principal,
            "passo_auxiliar": passo_auxiliar,
            "bitola_fio_auxiliar": fio_auxiliar,
            "espiras_auxiliar": espira_auxiliar,
            "tipo_enrolamento": tipo_enrolamento,
            "numero_ranhuras": numero_ranhuras,
            "fios_paralelos": fios_paralelos,
            "ligacao_interna": ligacao_interna,
            "diametro_interno_estator_mm": diametro_interno,
            "comprimento_pacote_mm": comprimento_pacote,
            "observacoes": f"{observacoes}\nEsquema: {esquema}",
            "origem_registro": origem,
        }

        motor = {k: (v if (v != "" and v is not None) else None) for k, v in motor.items()}

        alertas = alertas_validacao_projeto(motor)
        if alertas:
            for msg in alertas:
                st.warning(msg)

        sucesso, mensagem = salvar_motor_supabase(supabase, motor)
        if sucesso:
            clear_motores_cache()
            st.success(mensagem)
            st.balloons()
        else:
            st.error(mensagem)

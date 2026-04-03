import streamlit as st
import importlib
from pathlib import Path

from use_cases.listar_motores import consultar_motores, excluir_motor


def load_css() -> None:
    """
    Carrega o CSS do arquivo `assets/style.css` no Streamlit.
    (Obs: seu `App.py` já faz isso, mas aqui fica exatamente como você pediu.)
    """
    css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def show(supabase):
    load_css()
    st.title("🔍 Consulta de Motores")

    # --- LÓGICA DE NAVEGAÇÃO DE EDIÇÃO ---
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
                try:
                    consultar_motores.clear()  # garante lista fresca ao voltar
                except Exception:
                    pass
                st.rerun()
            return
        except Exception as e:
            st.error(f"Erro ao carregar edição: {e}")

    # --- BARRA DE PESQUISA ---
    search_query = st.text_input(
        "🔎 Pesquisar motor",
        placeholder="Ex: WEG, 12.5, 1750, 132M, 3:5:7...",
        help="Procure por marca, potência, RPM, carcaça ou qualquer detalhe.",
    )

    try:
        motores_db = consultar_motores(supabase)
    except Exception as e:
        st.error(f"Erro ao listar motores: {e}")
        motores_db = []

    if not motores_db:
        st.info("Nenhum motor cadastrado.")
        return

    # --- LÓGICA DE FILTRO DINÂMICO ---
    if search_query:
        query = search_query.lower()
        motores = [
            m
            for m in motores_db
            if any(query in str(valor).lower() for valor in m.values() if valor is not None)
        ]
    else:
        motores = motores_db

    if not motores:
        st.warning(f"Nenhum resultado encontrado para: '{search_query}'")
        return

    st.caption(f"Exibindo {len(motores)} motor(es)")

    # --- RENDERIZAÇÃO DOS CARDS ---
    for m in motores:
        id_motor = m.get("id")
        marca = m.get("marca") or "---"
        pot = m.get("potencia") or "---"
        rpm = m.get("rpm") or "---"
        modelo = m.get("modelo") or ""

        st.markdown('<div class="motor-card">', unsafe_allow_html=True)

        # Header acima do expander (fica com cara de card no celular)
        st.markdown(
            f"""
            <div class="motor-card__header">
              <div class="motor-card__title">#{id_motor} • {marca} {modelo}</div>
              <div class="motor-card__meta">{pot} • {rpm} RPM</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Ver detalhes", expanded=False):
            # Ações rápidas
            c1, c2 = st.columns(2)
            if c1.button("✏️ Editar", key=f"ed_{id_motor}", use_container_width=True):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()

            if c2.button("🗑️ Excluir", key=f"ex_{id_motor}", use_container_width=True):
                try:
                    if excluir_motor(supabase, id_motor):
                        st.success("Excluído!")
                        try:
                            consultar_motores.clear()  # garante lista fresca após deletar
                        except Exception:
                            pass
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir motor: {e}")

            st.divider()

            # --- SEÇÃO 1: IDENTIFICAÇÃO (EXTENDIDA) ---
            st.markdown("#### 📋 Dados de Placa e Identificação")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Marca:** {m.get('marca') or '---'}")
                st.markdown(f"**Modelo:** {m.get('modelo') or '---'}")
                st.markdown(f"**Fabricante:** {m.get('fabricante') or '---'}")
            with col2:
                st.markdown(f"**Potência:** {m.get('potencia') or '---'}")
                st.markdown(f"**Tensão:** {m.get('tensao') or '---'}")
                st.markdown(f"**Corrente:** {m.get('corrente') or '---'}")
            with col3:
                st.markdown(f"**RPM:** {m.get('rpm') or '---'}")
                st.markdown(f"**Freq:** {m.get('frequencia') or '---'}")
                st.markdown(f"**Rendimento:** {m.get('rendimento') or '---'}")

            st.divider()

            # --- SEÇÃO 2: CONSTRUÇÃO E MECÂNICA ---
            st.markdown("#### 🛠️ Construção e Mecânica")
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.markdown(f"**Carcaça:** {m.get('carcaca') or '---'}")
                st.markdown(f"**Montagem:** {m.get('montagem') or '---'}")
                st.markdown(f"**Pólos:** {m.get('polos') or '---'}")
            with mc2:
                st.markdown(f"**Isolação:** {m.get('isolacao') or '---'}")
                st.markdown(f"**IP:** {m.get('ip') or '---'}")
                st.markdown(f"**Regime:** {m.get('regime') or '---'}")
            with mc3:
                st.markdown(f"**Fator Serv.:** {m.get('fator_servico') or '---'}")
                st.markdown(f"**Peso:** {m.get('peso') or '---'}")
                st.markdown(f"**Ventilação:** {m.get('ventilacao') or '---'}")

            st.divider()

            # --- SEÇÃO 3: BOBINAGEM ---
            st.markdown("#### 🌀 Bobinagem")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.info(
                    f"**Principal** \n"
                    f"**Passo:** {m.get('passo_principal') or m.get('passo_princ') or '---'} \n"
                    f"**Fio:** {m.get('fio_principal') or m.get('fio_princ') or '---'} \n"
                    f"**Espiras:** {m.get('espira_principal') or m.get('espiras_princ') or '---'}"
                )
            with col_b2:
                st.warning(
                    f"**Auxiliar** \n"
                    f"**Passo:** {m.get('passo_auxiliar') or m.get('passo_aux') or '---'} \n"
                    f"**Fio:** {m.get('fio_auxiliar') or m.get('fio_aux') or '---'} \n"
                    f"**Espiras:** {m.get('espira_auxiliar') or m.get('espiras_aux') or '---'}"
                )

            st.divider()

            # --- SEÇÃO 4: DADOS ELÉTRICOS E NÚCLEO (NOVO) ---
            st.markdown("#### ⚡ Elétrica e Núcleo")
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                st.markdown(f"**Tipo Enrol.:** {m.get('tipo_enrolamento') or '---'}")
                st.markdown(f"**Nº Ranhuras:** {m.get('numero_ranhuras') or '---'}")
                st.markdown(f"**Resistência:** {m.get('resistencia') or '---'}")
            with ec2:
                st.markdown(f"**Diâm. Fio:** {m.get('diametro_fio') or '---'}")
                st.markdown(f"**Tipo Fio:** {m.get('tipo_fio') or '---'}")
                st.markdown(f"**Ligação:** {m.get('ligacao') or '---'}")
            with ec3:
                st.markdown(f"**Ø Interno:** {m.get('diametro_interno') or '---'}mm")
                st.markdown(f"**Comp. Pacote:** {m.get('comprimento_pacote') or '---'}mm")
                st.markdown(f"**Empilhamento:** {m.get('empilhamento') or '---'}mm")

            # --- OBSERVAÇÕES E RODAPÉ ---
            if m.get("observacoes"):
                st.markdown("---")
                st.markdown(f"**📝 Obs:** {m.get('observacoes')}")

            st.caption(f"📅 {m.get('data_cadastro')} | Origem: {m.get('origem_calculo')}")

        st.markdown("</div>", unsafe_allow_html=True)

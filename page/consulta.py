import streamlit as st
import importlib
from core.calculadora import alertas_validacao_projeto  # Importando a inteligência

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

    # --- DICIONÁRIO DE CORES PARA CONSULTA ---
    TABELA_CORES = {
        "Azul": "1", "Branco": "2", "Laranja": "3", 
        "Amarelo": "4", "Preto": "5", "Vermelho": "6",
        "Verde": "Terra"
    }

    # --- LÓGICA DE NAVEGAÇÃO DE EDIÇÃO ---
    if "motor_editando" not in st.session_state:
        st.session_state.motor_editando = None
    if "abrir_edit" not in st.session_state:
        st.session_state.abrir_edit = False

    if st.session_state.abrir_edit and st.session_state.motor_editando:
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Voltar para Lista", key="btn_voltar_lista", use_container_width=True):
                st.session_state.abrir_edit = False
                st.session_state.motor_editando = None
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

    motores_db = listar_motores(supabase)

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

    # --- ESTILO VISUAL ---
    st.markdown(
        """
        <style>
        [data-testid="stExpander"] { border: 1px solid #444; border-radius: 10px; margin-bottom: 10px; }
        .stMarkdown p { font-size: 14px; margin-bottom: 5px; }
        .status-badge { padding: 2px 8px; border-radius: 5px; font-weight: bold; font-size: 12px; }
        .status-red { background-color: #ff4b4b; color: white; }
        .status-yellow { background-color: #ffa500; color: black; }
        .status-green { background-color: #00c853; color: white; }
        
        .bobinagem-box { border: 1px solid #555; padding: 10px; border-radius: 5px; background: #262730; margin-bottom: 5px; }
        .bobinagem-titulo { font-weight: bold; color: #ff4b4b; border-bottom: 1px solid #555; margin-bottom: 5px; padding-bottom: 2px; }
        .bobinagem-linha { display: flex; justify-content: space-between; font-size: 13px; }
        .bobinagem-k { color: #888; }
        
        .consulta-motor-resumo {
            background-color: #1e1e1e; 
            padding: 12px; 
            border-radius: 10px 10px 0 0; 
            border: 1px solid #444; 
            border-bottom: none;
        }
        .consulta-motor-resumo .titulo { font-weight: bold; font-size: 16px; margin-bottom: 4px; }
        .consulta-motor-resumo .meta { color: #888; font-size: 13px; }

        .alerta-5-cabos {
            background-color: #3e2723;
            border-left: 5px solid #ffab40;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            color: #ffcc80;
        }

        .alerta-6-cabos {
            background-color: #1a237e;
            border-left: 5px solid #2979ff;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            color: #e3f2fd;
        }

        .card-voltagem {
            background: #111;
            border: 1px solid #333;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            margin-bottom: 10px;
        }
        .voltagem-header { color: #ff4b4b; font-weight: bold; margin-bottom: 5px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- RENDERIZAÇÃO DOS CARDS ---
    for m in motores:
        id_motor = m.get("id")
        marca = m.get("marca") or "---"
        pot = m.get("potencia") or "---"
        rpm = m.get("rpm") or "---"
        modelo = m.get("modelo") or ""

        lista_alertas = alertas_validacao_projeto(m)
        
        if any("Risco" in a or "alta" in a.lower() for a in lista_alertas):
            status_html = '<span class="status-badge status-red">🔴 RISCO ALTO</span>'
        elif lista_alertas:
            status_html = '<span class="status-badge status-yellow">🟡 ATENÇÃO</span>'
        else:
            status_html = '<span class="status-badge status-green">🟢 DADOS OK</span>'

        st.markdown(
            f"""
            <div class="consulta-motor-resumo">
              <div class="titulo">#{id_motor} · {marca} {modelo} {status_html}</div>
              <div class="meta">{pot} · {rpm} RPM</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Ver detalhes"):
            if lista_alertas:
                for alerta in lista_alertas:
                    if "Risco" in alerta or "alta" in alerta.lower():
                        st.error(alerta)
                    else:
                        st.warning(alerta)
            else:
                st.success("✅ Projeto validado: Densidade de corrente e espiras coerentes.")

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

            # --- SEÇÃO 1: IDENTIFICAÇÃO ---
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

            principal_passo = m.get("passo_principal") or m.get("passo_princ") or "---"
            principal_fio = m.get("fio_principal") or m.get("fio_princ") or "---"
            principal_esp = m.get("espira_principal") or m.get("espiras_princ") or "---"

            aux_passo = m.get("passo_auxiliar") or m.get("passo_aux") or "---"
            aux_fio = m.get("fio_auxiliar") or m.get("fio_aux") or "---"
            aux_esp = m.get("espira_auxiliar") or m.get("espiras_aux") or "---"

            with col_b1:
                st.markdown(f"""<div class="bobinagem-box"><div class="bobinagem-titulo">Principal</div>
                    <div class="bobinagem-linha"><div class="bobinagem-k">Passo</div><div>{principal_passo}</div></div>
                    <div class="bobinagem-linha"><div class="bobinagem-k">Fio</div><div>{principal_fio}</div></div>
                    <div class="bobinagem-linha"><div class="bobinagem-k">Espiras</div><div>{principal_esp}</div></div></div>""", unsafe_allow_html=True)

            with col_b2:
                st.markdown(f"""<div class="bobinagem-box"><div class="bobinagem-titulo">Auxiliar</div>
                    <div class="bobinagem-linha"><div class="bobinagem-k">Passo</div><div>{aux_passo}</div></div>
                    <div class="bobinagem-linha"><div class="bobinagem-k">Fio</div><div>{aux_fio}</div></div>
                    <div class="bobinagem-linha"><div class="bobinagem-k">Espiras</div><div>{aux_esp}</div></div></div>""", unsafe_allow_html=True)

            st.divider()

            # --- SEÇÃO: ESQUEMA DE LIGAÇÃO E TRADUTOR DE CORES ---
            st.markdown("#### ⚡ Esquema de Ligação e Cores")
            
            esquema_texto = str(m.get("esquema") or "").lower()
            ligacao_texto = str(m.get("ligacao") or "").lower()
            obs_texto = str(m.get("observacoes") or "").lower()
            modelo_completo = (str(m.get("modelo") or "") + str(m.get("fase") or "")).lower()

            is_monofasico = any(x in modelo_completo or x in ligacao_texto or x in obs_texto for x in ["mono", "monofasico", "1~", "1 f"])

            # --- CORREÇÃO DE LÓGICA DE EXIBIÇÃO (Removendo identação fantasma) ---
            if any(x in esquema_texto or x in ligacao_texto or x in obs_texto for x in ["6 cabos", "6 fios", "6 pontas"]) or "220/380" in str(m.get("tensao")):
                
                texto_6_fios = (
                    "<b>🔌 FECHAMENTO 6 FIOS (PADRÃO):</b><br><br>"
                    "<b>Triângulo (Δ) - Menor Tensão:</b> (1-6), (2-4), (3-5) ligados à rede.<br>"
                    "<b>Estrela (Y) - Maior Tensão:</b> (1, 2, 3) à rede e (4-5-6) unidos entre si."
                )
                
                if is_monofasico:
                    texto_5_fios += (
                        "<hr style='border: 0.5px solid #2979ff; margin: 10px 0;'>"
                        "<b>🔄 ROTAÇÃO (MONOFÁSICO 6 FIOS):</b><br>"
                        "<b>Sentido Horário:</b> Ligar (1 e 5) em um cabo da rede, e (4 e 6) no outro cabo.<br>"
                        "<b>Sentido Anti-Horário:</b> Ligar (1 e 6) em um cabo da rede, e (4 e 5) no outro cabo."
                    )
                
                st.markdown(f'<div class="alerta-6-cabos">{texto_6_fios}</div>', unsafe_allow_html=True)

            elif any(x in esquema_texto or x in ligacao_texto or x in obs_texto for x in ["5 cabos", "5 fios", "5 pontas"]):
                texto_5_fios = (
                    "<b>📌 ESQUEMA DE LIGAÇÃO 5 FIOS (SIMPLIFICADO):</b><br><br>"
                    "<b>Como ligar na rede elétrica:</b><br>"
                    "1. Pegue o <b>Fio 1</b> e ligue direto em um cabo da rede.<br>"
                    "2. Junte o <b>Fio 4 e o Fio 5</b> e ligue no outro cabo da rede.<br>"
                    "3. Junte o <b>Fio 2 e o Fio 3</b> e isole-os (unidos entre si).<br><br>"
                    "<i>Nota: O fio 5 é o auxiliar. Para inverter rotação, inverta internamente.</i>"
                )
                st.markdown(f'<div class="alerta-5-cabos">{texto_5_fios}</div>', unsafe_allow_html=True)

            # 2. LIGAÇÕES DINÂMICAS POR TENSÃO
            tensao_val = str(m.get("tensao") or "").lower()
            cols_liga = st.columns(4) 
            
            if "110" in tensao_val:
                with cols_liga[0]:
                    st.markdown('<div class="card-voltagem"><div class="voltagem-header">110V</div>1-3 com L1<br>2-4 com L2</div>', unsafe_allow_html=True)
            if "220" in tensao_val:
                with cols_liga[1]:
                    st.markdown('<div class="card-voltagem"><div class="voltagem-header">220V</div>1 com L1<br>4 com L2<br>Unir 2-3</div>', unsafe_allow_html=True)
            if "380" in tensao_val:
                with cols_liga[2]:
                    st.markdown('<div class="card-voltagem"><div class="voltagem-header">380V</div>Estrela (Y)<br>1-2-3 Linha<br>Unir 4-5-6</div>', unsafe_allow_html=True)
            if "440" in tensao_val:
                with cols_liga[3]:
                    st.markdown('<div class="card-voltagem"><div class="voltagem-header">440V</div>Série<br>Conforme Placa</div>', unsafe_allow_html=True)

            # 3. Tradutor de Cores
            cols_cores = st.columns(len(TABELA_CORES))
            for i, (cor, num) in enumerate(TABELA_CORES.items()):
                cols_cores[i].metric(label=cor, value=num)

            st.divider()

            # --- SEÇÃO 4: DADOS ELÉTRICOS E NÚCLEO ---
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

            if m.get("observacoes"):
                st.markdown("---")
                st.markdown(f"**📝 Obs:** {m.get('observacoes')}")

            st.caption(f"📅 {m.get('data_cadastro')} | Origem: {m.get('origem_calculo')}")

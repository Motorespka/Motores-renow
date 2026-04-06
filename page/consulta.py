import streamlit as st

# =============================
# 🎨 CSS LOCAL
# =============================
def aplicar_estilo():
    st.markdown("""
        <style>
        /* Container app */
        .stApp { max-width: 1000px; margin: 0 auto; }

        /* Cards */
        div.stButton > button {
            width: 100%;
            text-align: left;
            background: linear-gradient(145deg, #081018, #05070d);
            border: 2px solid #00ffff33;
            border-radius: 15px;
            padding: 18px;
            margin-bottom: 10px;
            color: white;
            font-family: 'Courier New', monospace;
            box-shadow: 0 0 20px #00ffff11;
            transition: all 0.25s ease;
        }
        div.stButton > button:hover {
            border-color: #00ffff;
            box-shadow: 0 0 30px #00ffff55;
            transform: scale(1.01);
        }
        div.stButton > button:active {
            transform: scale(0.99);
        }

        /* Gaveta */
        .gaveta-detalhes {
            background: rgba(8, 16, 24, 0.95);
            border: 2px solid #00ffff;
            border-radius: 0 0 15px 15px;
            padding: 20px;
            margin-top: -5px;
            margin-bottom: 25px;
        }

        /* Resumo grid */
        .info-grid { display: grid; grid-template-columns: repeat(4,1fr); gap:10px; text-align:center; margin-top:10px; }
        .label { color:#8b949e; font-size:0.7rem; text-transform:uppercase; }
        .valor { color:#00f2ff; font-weight:bold; font-size:1rem; }

        /* Inputs */
        .stTextInput input {
            background-color: rgba(0,255,255,0.05) !important;
            border: 1px solid #00ffff33 !important;
            color: #00ffff !important;
            border-radius: 8px !important;
            padding: 10px !important;
        }
        .stTextInput input:focus {
            border-color: #00ffff !important;
            box-shadow: 0 0 10px #00ffff33 !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab"] { background-color:#1f2937; color:white; border-radius:6px 6px 0 0; padding:8px 16px; }
        .stTabs [aria-selected="true"] { background-color:#00f2ff !important; color:black !important; }

        </style>
    """, unsafe_allow_html=True)

# =============================
# 🚀 MAIN
# =============================
def show(supabase):
    aplicar_estilo()

    st.markdown('<h2 style="color:#00f2ff; text-align:center;">🔍 Consulta Inteligente</h2>', unsafe_allow_html=True)

    busca = st.text_input("", placeholder="Pesquisar 5 CV, WEG, Trifásico...", label_visibility="collapsed")

    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except Exception:
        st.error("Erro ao conectar com o banco de dados.")
        return

    if busca:
        motores = [m for m in motores if busca.lower() in str(m).lower()]

    if "card_selecionado" not in st.session_state:
        st.session_state.card_selecionado = None

    for m in motores:
        mid = m.get("id")
        aberto = st.session_state.card_selecionado == mid

        # 🔥 card como botão do streamlit
        card_text = f"""
        {str(m.get('marca','S/M')).upper()} | MODELO: {m.get('modelo','---')}

        Potência: {m.get('potencia_hp_cv','---')} | RPM: {m.get('rpm_nominal','---')}
        Fases: {m.get('fases','---')} | Polos: {m.get('polos','---')}
        """
        if st.button(card_text, key=f"btn_{mid}", use_container_width=True):
            st.session_state.card_selecionado = None if aberto else mid
            st.rerun()

        # gaveta
        if aberto:
            st.markdown('<div class="gaveta-detalhes">', unsafe_allow_html=True)
            tab_placa, tab_bob, tab_mec, tab_adv = st.tabs(["🏷️ Placa","🌀 Bobinagem","⚙️ Mecânica","🚀 Avançado"])

            with tab_placa:
                col1, col2 = st.columns(2)
                col1.write(f"**Cliente:** {m.get('cliente','---')}")
                col1.write(f"**Tensão:** {m.get('tensao_v','---')} V")
                col1.write(f"**Corrente:** {m.get('corrente_nominal_a','---')} A")
                col2.write(f"**Carcaça:** {m.get('carcaca','---')}")
                col2.write(f"**Frequência:** {m.get('frequencia_hz','---')} Hz")
                col2.write(f"**Fator de Serviço:** {m.get('fator_servico','---')}")

            with tab_bob:
                col1, col2 = st.columns(2)
                col1.write("**Principal**")
                col1.write(f"Bitola: {m.get('bitola_fio_principal','---')}")
                col1.write(f"Passo: {m.get('passo_principal','---')}")
                col1.write(f"Espiras: {m.get('espiras_principal','---')}")
                col2.write("**Auxiliar**")
                col2.write(f"Bitola: {m.get('bitola_fio_auxiliar','---')}")
                col2.write(f"Passo: {m.get('passo_auxiliar','---')}")
                col2.write(f"Ligação: {m.get('ligacao_interna','---')}")

            with tab_mec:
                col1, col2 = st.columns(2)
                col1.write(f"**Rol. Dianteiro:** {m.get('rolamento_dianteiro','---')}")
                col1.write(f"**Rol. Traseiro:** {m.get('rolamento_traseiro','---')}")
                col2.write(f"**Cap. Partida:** {m.get('capacitor_partida','---')}")
                col2.write(f"**Cap. Permanente:** {m.get('capacitor_permanente','---')}")

            with tab_adv:
                st.write(f"**Resistência Isolamento:** {m.get('resistencia_isolamento_megohmetro','---')} MΩ")
                st.write(f"**Observações:** {m.get('observacoes','Nenhuma')}")
                with st.expander("Dados Técnicos Completos (JSON)"):
                    st.json(m)

            st.markdown('</div>', unsafe_allow_html=True)

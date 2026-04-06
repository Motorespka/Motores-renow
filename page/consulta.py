import streamlit as st

# =============================
# 🎨 CSS LOCAL (CYBERPUNK)
# =============================
def aplicar_estilo():
    st.markdown("""
        <style>
        /* Grid de resumo */
        .resumo-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 10px;
            text-align: center;
            margin-top: 10px;
            pointer-events: none;
        }

        .label-resumo { 
            color: #8b949e; 
            font-size: 0.7rem; 
            text-transform: uppercase; 
        }

        .valor-resumo { 
            color: #00f2ff; 
            font-weight: bold; 
            font-size: 1rem; 
        }

        /* Tabs estilo cyber */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }

        .stTabs [data-baseweb="tab"] {
            background-color: #1f2937;
            border-radius: 5px 5px 0 0;
            color: white;
            padding: 8px 16px;
        }

        .stTabs [aria-selected="true"] { 
            background-color: #00f2ff !important; 
            color: black !important; 
        }
        </style>
    """, unsafe_allow_html=True)


# =============================
# 🚀 MAIN
# =============================
def show(supabase):
    aplicar_estilo()

    st.markdown(
        '<h2 style="color: #00f2ff; text-align: center;">🔍 Consulta Inteligente</h2>',
        unsafe_allow_html=True
    )

    # 🔍 Campo de busca
    busca = st.text_input(
        "",
        placeholder="Pesquisar 5 CV, WEG, Trifásico...",
        label_visibility="collapsed"
    )

    # 🔗 Buscar dados
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except Exception:
        st.error("Erro ao conectar com o banco de dados.")
        return

    # 🔎 Filtro
    if busca:
        motores = [m for m in motores if busca.lower() in str(m).lower()]

    # 📌 Estado
    if "card_selecionado" not in st.session_state:
        st.session_state.card_selecionado = None

    # =============================
    # 🔁 LOOP DOS CARDS
    # =============================
    for m in motores:
        mid = m.get("id")
        aberto = st.session_state.card_selecionado == mid
        classe_extra = "card-ativo" if aberto else ""

        # 🔲 Container do card
        with st.container():
            # 🔳 Card com estilo
            st.markdown(f"""
                <div class="motor-container" style="position: relative;">
                    <div class="tech-card {classe_extra}" style="position: relative;">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="card-title">{str(m.get('marca', 'S/M')).upper()}</span>
                            <span class="card-subtitle">MODELO: {m.get('modelo', '---')}</span>
                        </div>

                        <div class="resumo-grid">
                            <div>
                                <div class="label-resumo">Potência</div>
                                <div class="valor-resumo">{m.get('potencia_hp_cv', '---')}</div>
                            </div>
                            <div>
                                <div class="label-resumo">RPM</div>
                                <div class="valor-resumo">{m.get('rpm_nominal', '---')}</div>
                            </div>
                            <div>
                                <div class="label-resumo">Fases</div>
                                <div class="valor-resumo">{m.get('fases', '---')}</div>
                            </div>
                            <div>
                                <div class="label-resumo">Polos</div>
                                <div class="valor-resumo">{m.get('polos', '---')}</div>
                            </div>
                        </div>
                    </div>
            """, unsafe_allow_html=True)

            # 🔥 Botão invisível que cobre todo o card
            if st.button("abrir_card", key=f"btn_{mid}", use_container_width=True):
                st.session_state.card_selecionado = None if aberto else mid
                st.rerun()

        # =============================
        # 📂 GAVETA
        # =============================
        if aberto:
            st.markdown('<div class="gaveta-detalhes">', unsafe_allow_html=True)

            tab_placa, tab_bob, tab_mec, tab_adv = st.tabs([
                "🏷️ Placa", "🌀 Bobinagem", "⚙️ Mecânica", "🚀 Avançado"
            ])

            # 🏷️ PLACA
            with tab_placa:
                col1, col2 = st.columns(2)
                col1.write(f"**Cliente:** {m.get('cliente', '---')}")
                col1.write(f"**Tensão:** {m.get('tensao_v', '---')} V")
                col1.write(f"**Corrente:** {m.get('corrente_nominal_a', '---')} A")
                col2.write(f"**Carcaça:** {m.get('carcaca', '---')}")
                col2.write(f"**Frequência:** {m.get('frequencia_hz', '---')} Hz")
                col2.write(f"**Fator de Serviço:** {m.get('fator_servico', '---')}")

            # 🌀 BOBINAGEM
            with tab_bob:
                col1, col2 = st.columns(2)
                col1.write("**Principal**")
                col1.write(f"Bitola: {m.get('bitola_fio_principal', '---')}")
                col1.write(f"Passo: {m.get('passo_principal', '---')}")
                col1.write(f"Espiras: {m.get('espiras_principal', '---')}")
                col2.write("**Auxiliar**")
                col2.write(f"Bitola: {m.get('bitola_fio_auxiliar', '---')}")
                col2.write(f"Passo: {m.get('passo_auxiliar', '---')}")
                col2.write(f"Ligação: {m.get('ligacao_interna', '---')}")

            # ⚙️ MECÂNICA
            with tab_mec:
                col1, col2 = st.columns(2)
                col1.write(f"**Rol. Dianteiro:** {m.get('rolamento_dianteiro', '---')}")
                col1.write(f"**Rol. Traseiro:** {m.get('rolamento_traseiro', '---')}")
                col2.write(f"**Cap. Partida:** {m.get('capacitor_partida', '---')}")
                col2.write(f"**Cap. Permanente:** {m.get('capacitor_permanente', '---')}")

            # 🚀 AVANÇADO
            with tab_adv:
                st.write(f"**Resistência Isolamento:** {m.get('resistencia_isolamento_megohmetro', '---')} MΩ")
                st.write(f"**Observações:** {m.get('observacoes', 'Nenhuma')}")
                with st.expander("Dados Técnicos Completos (JSON)"):
                    st.json(m)

            st.markdown('</div>', unsafe_allow_html=True)

import streamlit as st

# =============================
# 🎨 CSS PERSONALIZADO (GAVETA E TABS)
# =============================
def aplicar_estilo():
    st.markdown("""
        <style>
        /* Container Principal do Card */
        .motor-container {
            position: relative;
            margin-bottom: 10px;
        }

        /* O Card-Botão (Resumo) */
        .card-botao {
            background: linear-gradient(145deg, #0d1117, #07090e);
            border: 2px solid #00f2ff33;
            border-radius: 12px;
            padding: 15px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .motor-container:hover .card-botao {
            border-color: #00f2ffaa;
            box-shadow: 0 0 15px #00f2ff22;
        }

        /* Classe para quando o card está ativo/aberto */
        .card-ativo {
            border-color: #00f2ff !important;
            border-bottom-left-radius: 0px !important;
            border-bottom-right-radius: 0px !important;
            background: #161b22 !important;
        }

        /* Estilização das métricas rápidas */
        .resumo-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 10px;
            text-align: center;
            margin-top: 10px;
        }
        
        .label-resumo { color: #8b949e; font-size: 0.7rem; text-transform: uppercase; }
        .valor-resumo { color: #00f2ff; font-weight: bold; font-size: 1rem; }

        /* A Gaveta de Informações (Sub-caixa) */
        .gaveta-detalhes {
            background: #0d1117;
            border: 2px solid #00f2ff;
            border-top: none;
            border-radius: 0 0 12px 12px;
            padding: 20px;
            margin-bottom: 20px;
            animation: slideDown 0.3s ease-out;
        }

        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Botão invisível que cobre o card */
        div.stButton > button:first-child {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 85px; /* Ajuste conforme altura do card */
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            z-index: 10;
        }
        
        /* Ajuste das Tabs do Streamlit para o tema Dark/Cyber */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #1f2937;
            border-radius: 5px 5px 0 0;
            color: white;
            padding: 8px 16px;
        }
        .stTabs [aria-selected="true"] { background-color: #00f2ff !important; color: black !important; }
        </style>
    """, unsafe_allow_html=True)

def show(supabase):
    aplicar_estilo()
    
    st.markdown('<h2 style="color: #00f2ff;">🔍 Consulta Inteligente</h2>', unsafe_allow_html=True)
    
    busca = st.text_input("", placeholder="Pesquisar 5 CV, WEG, Trifásico...", label_visibility="collapsed")
    
    # Busca dados no Supabase
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except Exception:
        st.error("Erro ao conectar com o banco de dados.")
        return

    # Filtro simples
    if busca:
        motores = [m for m in motores if busca.lower() in str(m).lower()]

    # Estado para controlar qual card está aberto
    if "card_selecionado" not in st.session_state:
        st.session_state.card_selecionado = None

    for m in motores:
        mid = m.get("id")
        aberto = st.session_state.card_selecionado == mid
        
        # --- UI DO CARD-BOTÃO (RESUMO) ---
        classe_status = "card-ativo" if aberto else ""
        
        st.markdown(f"""
            <div class="motor-container">
                <div class="card-botao {classe_status}">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: white; font-weight: bold;">{m.get('marca', 'S/M').upper()}</span>
                        <span style="color: #8b949e; font-size: 0.8rem;">ID: {m.get('modelo', '---')}</span>
                    </div>
                    <div class="resumo-grid">
                        <div><div class="label-resumo">Potência</div><div class="valor-resumo">{m.get('potencia_hp_cv', '---')}</div></div>
                        <div><div class="label-resumo">RPM</div><div class="valor-resumo">{m.get('rpm_nominal', '---')}</div></div>
                        <div><div class="label-resumo">Fases</div><div class="valor-resumo">{m.get('fases', '---')}</div></div>
                        <div><div class="label-resumo">Polos</div><div class="valor-resumo">{m.get('polos', '---')}</div></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Botão invisível sobre o card para detectar o clique
        if st.button(f"Abrir {mid}", key=f"btn_{mid}"):
            if st.session_state.card_selecionado == mid:
                st.session_state.card_selecionado = None
            else:
                st.session_state.card_selecionado = mid
            st.rerun()

        # --- GAVETA DE DETALHES (SUB-CAIXA) ---
        if aberto:
            with st.container():
                st.markdown('<div class="gaveta-detalhes">', unsafe_allow_html=True)
                
                tab_placa, tab_bob, tab_mec, tab_adv = st.tabs([
                    "🏷️ Placa", "🌀 Bobinagem", "⚙️ Mecânica", "🚀 Avançado"
                ])
                
                with tab_placa:
                    col1, col2 = st.columns(2)
                    col1.write(f"**Cliente:** {m.get('cliente', '---')}")
                    col1.write(f"**Tensão:** {m.get('tensao_v', '---')} V")
                    col1.write(f"**Corrente:** {m.get('corrente_nominal_a', '---')} A")
                    col2.write(f"**Carcaça:** {m.get('carcaca', '---')}")
                    col2.write(f"**Frequência:** {m.get('frequencia_hz', '---')} Hz")
                    col2.write(f"**Fator de Serviço:** {m.get('fator_servico', '---')}")

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

                with tab_mec:
                    col1, col2 = st.columns(2)
                    col1.write(f"**Rol. Dianteiro:** {m.get('rolamento_dianteiro', '---')}")
                    col1.write(f"**Rol. Traseiro:** {m.get('rolamento_traseiro', '---')}")
                    col2.write(f"**Cap. Partida:** {m.get('capacitor_partida', '---')}")
                    col2.write(f"**Cap. Permanente:** {m.get('capacitor_permanente', '---')}")

                with tab_adv:
                    st.write(f"**Resistência Isolamento:** {m.get('resistencia_isolamento_megohmetro', '---')} MΩ")
                    st.write(f"**Observações:** {m.get('observacoes', 'Nenhuma')}")
                    st.json(m) # Opcional: exibe tudo do banco caso falte algum campo acima
                
                st.markdown('</div>', unsafe_allow_html=True)

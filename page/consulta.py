import streamlit as st
import re

# =============================
# 🎨 CSS AVANÇADO (BOTÃO GIGANTE + ANIMAÇÃO)
# =============================
def aplicar_estilo():
    st.markdown("""
        <style>
        /* CONTAINER DO CARD */
        .motor-container { 
            position: relative; 
            margin-bottom: 5px; 
            transition: all 0.3s ease;
        }

        /* O CARD EM SI (O retângulo que você vê) */
        .tech-card {
            background: linear-gradient(145deg, #0d1117, #07090e);
            border: 2px solid #00ffff33;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            z-index: 1;
        }

        /* EFEITO DE HOVER (Quando passa o mouse) */
        .motor-container:hover .tech-card {
            border-color: #00ffffaa;
            box-shadow: 0 0 25px #00ffff22;
            transform: scale(1.01);
            background: #0d161f;
        }

        /* ESTADO ATIVO (Quando a caixa está aberta) */
        .card-aberto-estilo {
            border-color: #00ffff !important;
            box-shadow: 0 0 30px #00ffff44 !important;
            background: #0a1929 !important;
            border-bottom-left-radius: 0px !important;
            border-bottom-right-radius: 0px !important;
        }

        /* BOTÃO INVISÍVEL (Ocupa 100% do card) */
        div.stButton {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10;
        }

        div.stButton > button {
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            width: 100% !important;
            height: 100% !important;
            cursor: pointer !important;
            display: block !important;
        }

        /* SUB-CAIXA DE DETALHES (A caixa que "abre") */
        .sub-caixa-detalhes {
            background: rgba(0, 255, 255, 0.02);
            border: 2px solid #00ffff;
            border-top: none;
            border-radius: 0 0 12px 12px;
            padding: 20px;
            margin-bottom: 30px;
            animation: expandir 0.4s ease-out;
            box-shadow: 0 10px 20px rgba(0,0,0,0.4);
        }

        @keyframes expandir {
            from { opacity: 0; transform: translateY(-15px); max-height: 0; }
            to { opacity: 1; transform: translateY(0); max-height: 1000px; }
        }

        /* Títulos e Métricas */
        .card-title { font-size: 1.4rem; color: #00ffff; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; }
        .card-subtitle { color: #8b949e; font-size: 0.9rem; margin-bottom: 15px; }
        .metric-val { font-size: 1.2rem; font-weight: bold; color: #ffffff; }
        
        /* Protege o texto para o clique passar para o botão */
        .tech-card * { pointer-events: none; }
        </style>
    """, unsafe_allow_html=True)

def limpar(v): return str(v) if v and str(v).lower() not in ["none", "null", ""] else "---"

# =============================
# 🚀 PÁGINA DE CONSULTA
# =============================
def show(supabase):
    aplicar_estilo()
    
    st.markdown('<h1 style="color: #00f2ff; text-align: center;">🔍 Consultar Base de Dados</h1>', unsafe_allow_html=True)
    
    busca = st.text_input("", placeholder="Pesquise por marca, cliente ou modelo...", label_visibility="collapsed")
    
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except:
        st.error("Erro ao conectar com Supabase.")
        return

    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in str(m.values()).lower()]

    # Estado para saber qual card está aberto
    if "aberto_id" not in st.session_state:
        st.session_state.aberto_id = None

    for m in motores:
        mid = m.get("id")
        esta_aberto = st.session_state.aberto_id == mid
        
        # Adiciona classe CSS extra se o card estiver aberto
        classe_extra = "card-aberto-estilo" if esta_aberto else ""

        # Desenho do Card Principal (Botão Gigante)
        st.markdown(f'''
            <div class="motor-container">
                <div class="tech-card {classe_extra}">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="text-align: left;">
                            <div class="card-title">{limpar(m.get("marca"))}</div>
                            <div class="card-subtitle">👤 Cliente: {limpar(m.get("cliente"))} | Mod: {limpar(m.get("modelo"))}</div>
                        </div>
                        <div style="background: #ff00ff22; color: #ff00ff; padding: 4px 10px; border-radius: 5px; font-weight: bold; font-size: 0.8rem; border: 1px solid #ff00ff;">
                            📍 {limpar(m.get("localizacao_oficina"))}
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-around; margin-top: 15px; border-top: 1px solid #ffffff11; padding-top: 15px;">
                        <div><span style="color: #00ffff;" class="metric-val">{limpar(m.get("potencia_hp_cv"))}</span><br><small>CV/HP</small></div>
                        <div><span style="color: #10b981;" class="metric-val">{limpar(m.get("rpm_nominal"))}</span><br><small>RPM</small></div>
                        <div><span style="color: #f59e0b;" class="metric-unit">{limpar(m.get("corrente_nominal_a"))}</span><br><small>AMP</small></div>
                    </div>
                </div>
        ''', unsafe_allow_html=True)

        # O botão invisível que detecta o clique em QUALQUER LUGAR do retângulo
        if st.button(" ", key=f"btn_{mid}"):
            st.session_state.aberto_id = None if esta_aberto else mid
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # SUB-CAIXA QUE GERA AS INFORMAÇÕES (Só aparece se clicado)
        if esta_aberto:
            with st.container():
                st.markdown('<div class="sub-caixa-detalhes">', unsafe_allow_html=True)
                
                # Divisão por abas para organizar o excesso de dados do Supabase
                tab1, tab2, tab3, tab4 = st.tabs(["⚡ ELÉTRICA", "🌀 REBOBINAGEM", "📏 MEDIDAS", "🛠️ MECÂNICA"])
                
                with tab1:
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Tensão:** `{m.get('tensao_v')} V`")
                    c1.markdown(f"**Nº Pontas:** `{m.get('numero_pontas')}`")
                    c1.markdown(f"**Frequência:** `{m.get('frequencia_hz')} Hz`")
                    c2.markdown(f"**Isolamento (Megômetro):** `{m.get('resistencia_isolamento_megohmetro')} MΩ`")
                    c2.markdown(f"**Resistência Ôhmica:** `{m.get('resistencia_ohm_fase')} Ω`")
                    c2.markdown(f"**Fator de Serviço:** `{m.get('fator_servico')}`")

                with tab2:
                    st.markdown("##### Dados do Enrolamento Principal")
                    st.write(f"**Fio:** {m.get('bitola_fio_principal')} | **Passo:** {m.get('passo_principal')} | **Espiras:** {m.get('espiras_principal')}")
                    st.write(f"**Peso Cobre:** {m.get('peso_cobre_principal_kg')} kg | **Ligação:** {m.get('ligacao_interna')}")
                    st.divider()
                    st.markdown("##### Dados do Enrolamento Auxiliar")
                    st.write(f"**Fio Aux:** {m.get('bitola_fio_auxiliar')} | **Passo Aux:** {m.get('passo_auxiliar')}")

                with tab3:
                    st.markdown("##### Geometria do Estator")
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Ø Interno", f"{m.get('diametro_interno_estator_mm')} mm")
                    col_b.metric("Ø Externo", f"{m.get('diametro_externo_estator_mm')} mm")
                    col_c.metric("Pacote", f"{m.get('comprimento_pacote_mm')} mm")
                    st.write(f"**Número de Ranhuras:** {m.get('numero_ranhuras')}")

                with tab4:
                    st.markdown("##### Peças e Rolamentos")
                    st.write(f"**Rolamento Dianteiro:** `{m.get('rolamento_dianteiro')}`")
                    st.write(f"**Rolamento Traseiro:** `{m.get('rolamento_traseiro')}`")
                    st.write(f"**Capacitor Partida:** {m.get('capacitor_partida')}")
                    st.write(f"**Capacitor Permanente:** {m.get('capacitor_permanente')}")

                # Botão para editar ou ver observações
                if m.get('observacoes'):
                    st.warning(f"📝 **OBSERVAÇÕES:** {m.get('observacoes')}")

                st.markdown('</div>', unsafe_allow_html=True)

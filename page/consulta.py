import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS (EFEITO DE EXPANSÃO)
# =============================
def aplicar_estilo():
    st.markdown("""
        <style>
        .motor-container { position: relative; margin-bottom: 12px; }
        
        .tech-card {
            background: linear-gradient(145deg, #081018, #05070d);
            border: 2px solid #00ffff33;
            border-radius: 15px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 0 20px #00ffff11;
            transition: all 0.3s ease;
            position: relative;
            z-index: 1;
        }
        
        /* Efeito visual ao passar o mouse */
        .motor-container:hover .tech-card {
            border-color: #00ffff;
            box-shadow: 0 0 40px #00ffff33;
            transform: translateY(-2px);
        }

        /* Camada do botão invisível que cobre o card todo */
        div.stButton { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 10; }
        div.stButton > button {
            background: transparent !important; border: none !important;
            color: transparent !important; width: 100% !important;
            height: 100% !important; cursor: pointer !important;
        }

        .card-title { font-size: 1.3rem; color: #00ffff; font-weight: 800; letter-spacing: 1.5px; }
        .metric-unit { font-size: 1.1rem; font-weight: bold; }
        .loc-badge { color: #ff00ff; font-size: 0.75rem; font-weight: bold; border: 1px solid #ff00ff; padding: 2px 5px; border-radius: 4px; }
        
        /* Estilo da "caixa aberta" */
        .detalhes-abertos {
            background: rgba(0,255,255,0.03); 
            border: 2px solid #00ffff44; 
            border-top: none; 
            border-radius: 0 0 15px 15px; 
            padding: 25px; 
            margin: -15px auto 25px auto; 
            max-width: 95%;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .info-label { color: #8b949e; font-size: 0.8rem; text-transform: uppercase; }
        .info-value { color: #ffffff; font-weight: bold; font-family: 'Consolas', monospace; }
        
        /* Impede que o texto bloqueie o clique do botão */
        .tech-card * { pointer-events: none; }
        </style>
    """, unsafe_allow_html=True)

def limpar(valor):
    return str(valor) if valor and str(valor).strip() not in ["None", "null", ""] else "---"

# =============================
# 🚀 PÁGINA DE CONSULTA
# =============================
def show(supabase):
    aplicar_estilo()
    st.markdown('<h1 style="color: #00ffff;">🔍 Base de Dados Completa</h1>', unsafe_allow_html=True)
    
    busca = st.text_input("", placeholder="Pesquisar...", label_visibility="collapsed")
    
    # Busca os dados
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except:
        st.error("Erro ao conectar com o banco.")
        return

    # Filtro de busca
    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in str(m.values()).lower()]

    # CONTROLE DE ESTADO: Isso é o que faz a "caixa" abrir e fechar
    if "card_aberto" not in st.session_state:
        st.session_state.card_aberto = None

    for m in motores:
        id_m = m.get("id")
        
        # Desenha o Card
        st.markdown(f'''
            <div class="motor-container">
                <div class="tech-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="text-align: left;">
                            <div class="card-title">{limpar(m.get("marca")).upper()}</div>
                            <div class="card-subtitle">👤 {limpar(m.get("cliente"))} | Mod: {limpar(m.get("modelo"))}</div>
                        </div>
                        <span class="loc-badge">📍 {limpar(m.get("localizacao_oficina"))}</span>
                    </div>
                    <div style="display: flex; justify-content: space-around; margin-top: 10px;">
                        <div style="color: white;"><span style="color: #00ffff;" class="metric-unit">{limpar(m.get("potencia_hp_cv"))}</span> HP</div>
                        <div style="color: white;"><span style="color: #10b981;" class="metric-unit">{limpar(m.get("rpm_nominal"))}</span> RPM</div>
                        <div style="color: white;"><span style="color: #f59e0b;" class="metric-unit">{limpar(m.get("corrente_nominal_a"))}</span> A</div>
                    </div>
                </div>
        ''', unsafe_allow_html=True)

        # Lógica do Botão Invisível
        if st.button(" ", key=f"btn_{id_m}"):
            if st.session_state.card_aberto == id_m:
                st.session_state.card_aberto = None # Fecha se clicar de novo
            else:
                st.session_state.card_aberto = id_m # Abre este ID
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # SE O CARD ESTIVER ABERTO, MOSTRA A "CAIXA" COM TUDO
        if st.session_state.card_aberto == id_m:
            with st.container():
                st.markdown('<div class="detalhes-abertos">', unsafe_allow_html=True)
                
                t1, t2, t3, t4 = st.tabs(["⚡ ELÉTRICA", "🌀 REBOBINAGEM", "📏 NÚCLEO", "📝 TUDO"])
                
                with t1:
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Tensão:** {m.get('tensao_v')}V")
                    c1.markdown(f"**Pontas:** {m.get('numero_pontas')}")
                    c2.markdown(f"**Fases:** {m.get('fases')}")
                    c2.markdown(f"**Polos:** {m.get('polos')}")
                    c3.markdown(f"**Megômetro:** `{m.get('resistencia_isolamento_megohmetro')} MΩ`")
                    c3.markdown(f"**R. Ohm:** {m.get('resistencia_ohm_fase')} Ω")

                with t2:
                    st.write(f"**Fio Principal:** {m.get('bitola_fio_principal')} | **Fio Aux:** {m.get('bitola_fio_auxiliar')}")
                    st.write(f"**Passo:** {m.get('passo_principal')} | **Espiras:** {m.get('espiras_principal')}")
                    st.write(f"**Ligação Interna:** {m.get('ligacao_interna')}")
                    st.write(f"**Peso Cobre:** {m.get('peso_cobre_principal_kg')} kg")

                with t3:
                    st.write(f"**Ø Interno:** {m.get('diametro_interno_estator_mm')} mm")
                    st.write(f"**Ø Externo:** {m.get('diametro_externo_estator_mm')} mm")
                    st.write(f"**Pacote:** {m.get('comprimento_pacote_mm')} mm")
                    st.write(f"**Ranhuras:** {m.get('numero_ranhuras')}")

                with t4:
                    # Aqui ele varre TUDO que sobrou no banco
                    st.json(m) 

                st.markdown('</div>', unsafe_allow_html=True)

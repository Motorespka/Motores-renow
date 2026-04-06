import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS (CYBERPUNK DINÂMICO)
# =============================
def aplicar_estilo():
    st.markdown("""
        <style>
        .motor-container {
            position: relative;
            margin-bottom: 12px;
        }

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

        .motor-container:hover .tech-card {
            border-color: #00ffff;
            box-shadow: 0 0 40px #00ffff33;
            transform: translateY(-2px);
        }

        /* BOTÃO INVISÍVEL PARA CLIQUE NO CARD */
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
            padding: 0 !important;
            margin: 0 !important;
            cursor: pointer !important;
        }

        .card-title { font-size: 1.3rem; color: #00ffff; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 2px; }
        .card-subtitle { color: #8b949e; font-size: 0.85rem; margin-bottom: 10px; }
        .metric-unit { font-size: 1.1rem; font-weight: bold; }
        .loc-badge { color: #ff00ff; font-size: 0.75rem; font-weight: bold; border: 1px solid #ff00ff; padding: 2px 5px; border-radius: 4px; }

        .tech-card * { pointer-events: none; }
        </style>
    """, unsafe_allow_html=True)

# =============================
# 🛠️ FUNÇÕES DE TRATAMENTO
# =============================
def limpar_unidade(valor, unidade_fixa):
    if not valor: return "-"
    valor_str = str(valor).upper()
    limpo = valor_str.replace(unidade_fixa.upper(), "").strip()
    return limpo

def limpar_passo(passo_raw):
    if not passo_raw: return "---"
    s = str(passo_raw).strip()
    return re.sub(r"^[1][\s?:\-]*", "", s).replace(":", " ").replace("-", " ").strip()

def obter_configuracoes_ligacao(m):
    tensao = str(m.get('tensao_v', ''))
    pontas = str(m.get('numero_pontas', ''))
    fases = str(m.get('fases', '')).upper()
    
    resumo = f"⚡ Tensão: {tensao}V"
    if pontas: resumo += f" | {pontas} Pontas"
    
    if "TRI" in fases:
        if "220" in tensao and "380" in tensao:
            return f"{resumo} (Δ / Y)"
    return resumo

# =============================
# 🚀 PÁGINA DE CONSULTA
# =============================
def show(supabase):
    aplicar_estilo()
    
    st.markdown('<h1 style="color: #00ffff;">🔍 Inteligência de Matrizes</h1>', unsafe_allow_html=True)
    
    # Campo de busca ampliado (Busca em Cliente, Marca, Modelo ou Carcaça)
    busca = st.text_input("", placeholder="Pesquisar por Cliente, Marca, Modelo ou Carcaça...", label_visibility="collapsed")
    
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except Exception:
        st.error("Conexão falhou. Verifique sua rede ou credenciais.")
        return

    # Lógica de Filtro Multivariável
    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in 
                  f"{str(m.get('marca',''))} {str(m.get('modelo',''))} {str(m.get('cliente',''))} {str(m.get('carcaca',''))} {str(m.get('potencia_hp_cv',''))}".lower()]

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        aberto = st.session_state.detalhes_visiveis.get(key_det, False)

        # Dados para o Card Principal
        potencia = limpar_unidade(m.get('potencia_hp_cv'), "CV")
        rpm = limpar_unidade(m.get('rpm_nominal'), "RPM")
        corrente = limpar_unidade(m.get('corrente_nominal_a'), "A")
        marca = str(m.get('marca') or "---").upper()
        cliente = m.get('cliente') or "N/D"
        loc = m.get('localizacao_oficina') or "OFICINA"

        # HTML do Card
        st.markdown(f'''
            <div class="motor-container">
                <div class="tech-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="text-align: left;">
                            <div class="card-title">{marca}</div>
                            <div class="card-subtitle">👤 {cliente}</div>
                        </div>
                        <span class="loc-badge">📍 {loc}</span>
                    </div>
                    <div style="display: flex; justify-content: space-around; margin-top: 10px;">
                        <div style="color: white;"><span style="color: #00ffff;" class="metric-unit">{potencia}</span> CV</div>
                        <div style="color: white;"><span style="color: #10b981;" class="metric-unit">{rpm}</span> RPM</div>
                        <div style="color: white;"><span style="color: #f59e0b;" class="metric-unit">{corrente}</span> A</div>
                    </div>
                </div>
        ''', unsafe_allow_html=True)

        if st.button(" ", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not aberto
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Detalhes Expandidos (Ouro Técnico)
        if aberto:
            with st.container():
                st.markdown("""<div style="background: rgba(0,255,255,0.03); border: 2px solid #00ffff44; 
                                border-top:none; border-radius: 0 0 15px 15px; padding: 20px; 
                                margin: -15px auto 25px auto; max-width: 95%;">""", unsafe_allow_html=True)
                
                t1, t2, t3, t4 = st.tabs(["🔌 Ligações", "🌀 Bobinagem", "📏 Estator/Pacote", "⚙️ Mecânica"])
                
                with t1:
                    st.info(obter_configuracoes_ligacao(m))
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Fases:** {m.get('fases') or '-'}")
                    c2.write(f"**Carcaça:** {m.get('carcaca') or '-'}")
                    c3.write(f"**Megômetro:** {m.get('resistencia_isolamento_megohmetro') or '-'} MΩ")
                
                with t2:
                    st.markdown("#### Dados do Enrolamento")
                    col_b1, col_b2, col_b3 = st.columns(3)
                    col_b1.metric("Fio Principal", m.get("bitola_fio_principal") or "---")
                    col_b2.metric("Passo", limpar_passo(m.get("passo_principal")))
                    col_b3.metric("Espiras", m.get("espiras_principal") or "---")
                    
                    st.write(f"**Ligação Interna:** {m.get('ligacao_interna') or '-'}")
                    st.write(f"**Observações:** {m.get('observacoes') or '-'}")
                
                with t3:
                    st.markdown("#### Medidas do Núcleo (mm)")
                    cp1, cp2, cp3 = st.columns(3)
                    cp1.write(f"**Ø Interno:** {m.get('diametro_interno_estator_mm') or '-'} mm")
                    cp2.write(f"**Ø Externo:** {m.get('diametro_externo_estator_mm') or '-'} mm")
                    cp3.write(f"**Comp. Pacote:** {m.get('comprimento_pacote_mm') or '-'} mm")
                    st.write(f"**Nº Ranhuras:** {m.get('numero_ranhuras') or '-'}")

                with t4:
                    st.markdown("#### Componentes e Rolamentos")
                    cm1, cm2 = st.columns(2)
                    cm1.write(f"**Rol. Dianteiro:** `{m.get('rolamento_dianteiro') or '-'}`")
                    cm1.write(f"**Rol. Traseiro:** `{m.get('rolamento_traseiro') or '-'}`")
                    cm2.write(f"**Peso Total:** {m.get('peso_total_kg') or '-'} kg")
                    cm2.write(f"**Sentido Rotação:** {m.get('sentido_rotacao') or 'Ambos'}")
                
                st.markdown('</div>', unsafe_allow_html=True)

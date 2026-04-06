import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS (CYBERPUNK INDUSTRIAL)
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
        .motor-container:hover .tech-card {
            border-color: #00ffff;
            box-shadow: 0 0 40px #00ffff33;
            transform: translateY(-2px);
        }
        div.stButton { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 10; }
        div.stButton > button {
            background: transparent !important; border: none !important;
            color: transparent !important; width: 100% !important;
            height: 100% !important; cursor: pointer !important;
        }
        .card-title { font-size: 1.3rem; color: #00ffff; font-weight: 800; letter-spacing: 1.5px; }
        .card-subtitle { color: #8b949e; font-size: 0.85rem; }
        .metric-unit { font-size: 1.1rem; font-weight: bold; }
        .loc-badge { color: #ff00ff; font-size: 0.75rem; font-weight: bold; border: 1px solid #ff00ff; padding: 2px 5px; border-radius: 4px; }
        
        /* Estilo para detalhes internos */
        .info-label { color: #8b949e; font-size: 0.8rem; text-transform: uppercase; }
        .info-value { color: #ffffff; font-weight: bold; font-family: 'Consolas', monospace; }
        .tech-card * { pointer-events: none; }
        </style>
    """, unsafe_allow_html=True)

# =============================
# 🛠️ FUNÇÕES DE TRATAMENTO
# =============================
def limpar(valor):
    return str(valor) if valor and str(valor).strip() not in ["None", "null", ""] else "---"

def obter_configuracoes_ligacao(m):
    tensao = limpar(m.get('tensao_v'))
    pontas = limpar(m.get('numero_pontas'))
    fases = limpar(m.get('fases')).upper()
    esquema = limpar(m.get('ligacao_interna'))
    return f"⚡ {tensao}V | {pontas} Pontas | {fases} | Ligação: {esquema}"

# =============================
# 🚀 PÁGINA DE CONSULTA
# =============================
def show(supabase):
    aplicar_estilo()
    st.markdown('<h1 style="color: #00ffff; text-shadow: 0 0 10px #00ffff;">🔍 Base de Dados Técnica</h1>', unsafe_allow_html=True)
    
    busca = st.text_input("", placeholder="Busca por Marca, Modelo, Cliente, Fio ou Carcaça...", label_visibility="collapsed")
    
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except Exception:
        st.error("Erro de conexão com a matriz de dados.")
        return

    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in f"{m.values()}".lower()]

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        aberto = st.session_state.detalhes_visiveis.get(key_det, False)

        # Card Principal (Visual Compacto)
        st.markdown(f'''
            <div class="motor-container">
                <div class="tech-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="text-align: left;">
                            <div class="card-title">{limpar(m.get("marca")).upper()}</div>
                            <div class="card-subtitle">ID: {limpar(m.get("modelo"))} | 👤 {limpar(m.get("cliente"))}</div>
                        </div>
                        <span class="loc-badge">📍 {limpar(m.get("localizacao_oficina"))}</span>
                    </div>
                    <div style="display: flex; justify-content: space-around; margin-top: 10px;">
                        <div style="color: white;"><span style="color: #00ffff;" class="metric-unit">{limpar(m.get("potencia_hp_cv"))}</span> HP/CV</div>
                        <div style="color: white;"><span style="color: #10b981;" class="metric-unit">{limpar(m.get("rpm_nominal"))}</span> RPM</div>
                        <div style="color: white;"><span style="color: #f59e0b;" class="metric-unit">{limpar(m.get("corrente_nominal_a"))}</span> AMP</div>
                    </div>
                </div>
        ''', unsafe_allow_html=True)

        if st.button(" ", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not aberto
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

        # ÁREA DE DETALHES PROFUNDOS (Tudo que tem no Supabase)
        if aberto:
            with st.container():
                st.markdown('<div style="background: rgba(0,255,255,0.03); border: 2px solid #00ffff44; border-top:none; border-radius: 0 0 15px 15px; padding: 25px; margin: -15px auto 25px auto; max-width: 95%;">', unsafe_allow_html=True)
                
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ ELÉTRICA", "🌀 REBOBINAGEM", "📏 NÚCLEO", "⚙️ MECÂNICA", "📝 NOTAS"])
                
                with tab1:
                    st.info(obter_configuracoes_ligacao(m))
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f'<span class="info-label">Freq:</span> <br><span class="info-value">{m.get("frequencia_hz")} Hz</span>', unsafe_allow_html=True)
                        st.markdown(f'<span class="info-label">Polos:</span> <br><span class="info-value">{m.get("polos")}</span>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f'<span class="info-label">F.S:</span> <br><span class="info-value">{m.get("fator_servico")}</span>', unsafe_allow_html=True)
                        st.markdown(f'<span class="info-label">Cos φ:</span> <br><span class="info-value">{m.get("fator_potencia_cos_phi")}</span>', unsafe_allow_html=True)
                    with c3:
                        st.markdown(f'<span class="info-label">Isolação:</span> <br><span class="info-value">Classe {m.get("classe_isolacao")}</span>', unsafe_allow_html=True)
                        st.markdown(f'<span class="info-label">IP:</span> <br><span class="info-value">{m.get("grau_protecao_ip")}</span>', unsafe_allow_html=True)
                    with c4:
                        st.markdown(f'<span class="info-label">Megômetro:</span> <br><span class="info-value" style="color:#00ff00;">{m.get("resistencia_isolamento_megohmetro")} MΩ</span>', unsafe_allow_html=True)
                        st.markdown(f'<span class="info-label">R. Ohm:</span> <br><span class="info-value">{m.get("resistencia_ohm_fase")} Ω</span>', unsafe_allow_html=True)

                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Principal")
                        st.write(f"**Fio:** {m.get('bitola_fio_principal')} ({m.get('tipo_fio')})")
                        st.write(f"**Passo:** {m.get('passo_principal')} | **Espiras:** {m.get('espiras_principal')}")
                        st.write(f"**Peso Cobre:** {m.get('peso_cobre_principal_kg')} kg")
                        st.write(f"**Fios Paralelos:** {m.get('fios_paralelos')}")
                    with col2:
                        st.subheader("Auxiliar / Outros")
                        st.write(f"**Passo Aux:** {m.get('passo_auxiliar')}")
                        st.write(f"**Espiras Aux:** {m.get('espiras_auxiliar')}")
                        st.write(f"**Peso Aux:** {m.get('peso_cobre_auxiliar_kg')} kg")
                        st.write(f"**Tipo Enrolamento:** {m.get('tipo_enrolamento')}")

                with tab3:
                    st.markdown("#### Dimensões Físicas do Estator")
                    cp1, cp2, cp3, cp4 = st.columns(4)
                    cp1.metric("Ø Interno", f"{m.get('diametro_interno_estator_mm')} mm")
                    cp2.metric("Ø Externo", f"{m.get('diametro_externo_estator_mm')} mm")
                    cp3.metric("Comprimento", f"{m.get('comprimento_pacote_mm')} mm")
                    cp4.metric("Ranhuras", m.get('numero_ranhuras'))
                    st.write(f"**Material Núcleo:** {m.get('material_nucleo')}")

                with tab4:
                    cm1, cm2, cm3 = st.columns(3)
                    with cm1:
                        st.write(f"**Rol. Diant:** `{m.get('rolamento_dianteiro')}`")
                        st.write(f"**Rol. Tras:** `{m.get('rolamento_traseiro')}`")
                    with cm2:
                        st.write(f"**Cap. Partida:** {m.get('capacitor_partida')}")
                        st.write(f"**Cap. Perm:** {m.get('capacitor_permanente')}")
                    with cm3:
                        st.write(f"**Graxa:** {m.get('tipo_graxa')}")
                        st.write(f"**Peso Total:** {m.get('peso_total_kg')} kg")

                with tab5:
                    st.write(f"**Data Cadastro:** {m.get('data_cadastro')}")
                    st.write(f"**Origem:** {m.get('origem_registro')}")
                    st.warning(f"**Observações:** {m.get('observacoes') or 'Sem observações adicionais.'}")
                    if m.get('url_foto_placa'):
                        st.image(m.get('url_foto_placa'), caption="Foto da Placa Original", use_container_width=True)

                st.markdown('</div>', unsafe_allow_html=True)

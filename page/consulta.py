import streamlit as st
import re

# =================================================================
# 1. FUNÇÕES DE APOIO TÉCNICO
# =================================================================

def limpar_passo(passo_raw):
    if not passo_raw: return "---"
    s = str(passo_raw).strip()
    s = re.sub(r"^[1][\s?:\-]*", "", s)
    return s.replace(":", " ").replace("-", " ").strip()

def render_dado(label, valor, unidade="", highlight=False):
    color = "#00ffff" if not highlight else "#f59e0b"
    val = valor if valor and str(valor).lower() not in ["none", "nan", ""] else "---"
    st.markdown(f"""
        <div style="background: rgba(0,255,255,0.03); border:1px solid rgba(0,255,255,0.1);
        border-radius:6px; padding:10px; margin-bottom:5px;">
            <div style="font-size:0.65rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">{label}</div>
            <div style="font-size:0.95rem; color:white; font-family:monospace; font-weight:bold;">
            {val} <span style="color:{color}; font-size:0.75rem;">{unidade}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# =================================================================
# 2. LÓGICA DINÂMICA DE LIGAÇÕES (BASEADA NO SEU PEDIDO)
# =================================================================

def render_esquema_ligacao(motor):
    fases = str(motor.get("fases", "")).lower()
    tensao_raw = str(motor.get("tensao_v", ""))
    tensoes = [t.strip() for t in tensao_raw.split('/') if t.strip()]
    
    # Mapa de Identificação de Cabos (Cabo - Cor - Placa)
    mapa_cabos = {
        "1": {"cor": "AZUL", "sigla": "U1", "hex": "#4d4dff"},
        "2": {"cor": "BRANCO", "sigla": "V1", "hex": "#ffffff"},
        "3": {"cor": "LARANJA", "sigla": "W1", "hex": "#ff8c00"},
        "4": {"cor": "AMARELO", "sigla": "U2", "hex": "#ffff00"},
        "5": {"cor": "PRETO", "sigla": "V2", "hex": "#555555"},
        "6": {"cor": "VERMELHO", "sigla": "W2", "hex": "#ff4d4d"},
        "7": {"cor": "BRANCO/AZUL", "sigla": "U5", "hex": "#add8e6"},
        "8": {"cor": "BRANCO/BRANCO", "sigla": "V5", "hex": "#f0f0f0"},
        "9": {"cor": "BRANCO/LARANJA", "sigla": "W5", "hex": "#ffcc80"},
        "10": {"cor": "BRANCO/AMARELO", "sigla": "U6", "hex": "#ffffcc"},
        "11": {"cor": "BRANCO/PRETO", "sigla": "V6", "hex": "#cccccc"},
        "12": {"cor": "BRANCO/VERMELHO", "sigla": "W6", "hex": "#ffcccc"},
    }

    with st.expander("🔌 ESQUEMAS DE LIGAÇÃO (CABOS E PLACAS)", expanded=True):
        # 1. Tabela de Identificação
        st.markdown("#### 🏷️ Identificação de Cores e Terminais")
        cols = st.columns(3)
        for i, (num, dados) in enumerate(mapa_cabos.items()):
            if int(num) <= (12 if "trif" in fases else 6):
                with cols[i % 3]:
                    st.markdown(f"""
                        <div style="font-size:0.8rem; margin-bottom:5px;">
                            <span style="color:{dados['hex']};">●</span> 
                            <b>{num}</b>: {dados['cor']} ({dados['sigla']})
                        </div>
                    """, unsafe_allow_html=True)

        st.divider()

        # 2. Ligações por Voltagem
        st.markdown(f"#### ⚡ Ligações para {len(tensoes)} Voltagem(ns)")
        
        # Se for Monofásico
        if "mono" in fases:
            abas = st.tabs(["5 Cabos", "6 Cabos"])
            with abas[0]: 
                st.info("Ligação padrão para 5 cabos (Principal + Auxiliar)")
                st.code("Sentido Horário: L1(1,5) - L2(4) | Unir: (2,3)\nAnti-Horário: L1(1,4) - L2(5) | Unir: (2,3)")
            with abas[1]:
                st.info("Ligação para 6 cabos (Dupla Tensão)")
                for t in tensoes:
                    st.write(f"**Para {t}V:**")
                    if "110" in t or "127" in t: st.code("L1(1,3,5) - L2(2,4,6)")
                    else: st.code("L1(1) - L2(4) | Unir: (2,3,5,6)")

        # Se for Trifásico
        else:
            qtd_cabos = "12 Cabos" if motor.get("espiras_auxiliar") else "6 Cabos" # Exemplo de lógica
            abas = st.tabs([f"Esquema {len(tensoes)} Tensões"])
            with abas[0]:
                for t in tensoes:
                    st.markdown(f"**Ligação em {t}V:**")
                    if t == tensoes[0]: # Menor tensão (Triângulo)
                        st.code(f"∆ Triângulo: L1(1,6) - L2(2,4) - L3(3,5)")
                    elif len(tensoes) > 1 and t == tensoes[1]: # Tensão média (Estrela)
                        st.code(f"Y Estrela: L1(1) - L2(2) - L3(3) | Unir: (4,5,6)")
                    else: # Alta tensão (Ex: 440V ou 12 cabos)
                        st.code(f"Série/Paralelo: Consultar Placa ID#{motor.get('id')}")

# =================================================================
# 3. TELA PRINCIPAL
# =================================================================

def show(supabase):
    st.markdown("""
        <style>
        div.stButton > button {
            width: 100% !important; min-height: 210px !important;
            background: linear-gradient(135deg, rgba(0,40,60,0.95) 0%, rgba(0,20,35,1) 100%) !important;
            border: 1px solid rgba(0, 255, 255, 0.2) !important;
            border-left: 6px solid #10b981 !important; border-radius: 12px !important;
            margin-bottom: 15px !important; transition: all 0.3s ease !important;
        }
        div.stButton > button:hover { border-color: #00ffff !important; transform: translateY(-3px); }
        div.stButton > button p { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 🔍 Central de Motores")
    busca = st.text_input("🔎 Buscar por Marca, Modelo ou Potência...", placeholder="Ex: Weg 2cv 4 polos")
    
    # Carregamento de dados
    res = supabase.table("motores").select("*").order("id", desc=True).execute()
    motores = res.data if res.data else []

    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in f"{m.get('marca')} {m.get('modelo')} {m.get('potencia_hp_cv')}".lower()]

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    st.caption(f"Registros: {len(motores)}")

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"

        # Clique para Toggle (Abrir/Fechar)
        if st.button(" ", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()

        # --- CARD DE RAIO-X (O QUE APARECE ANTES DE ABRIR) ---
        fase_color = "#10b981" if "trif" in str(m.get("fases")).lower() else "#3b82f6"
        st.markdown(f"""
        <div style="margin-top:-215px; margin-bottom:35px; padding:20px; pointer-events:none; position:relative; z-index:5;">
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <small style="color:#00ffff; font-family:monospace;">ID #{id_m}</small>
                    <div style="font-size:1.4rem; color:white; font-weight:800;">{(m.get('marca') or '---').upper()}</div>
                    <div style="font-size:0.9rem; color:#aaa;">{m.get('modelo') or ''}</div>
                </div>
                <div style="background:{fase_color}22; color:{fase_color}; padding:5px 15px; border-radius:20px; font-size:0.75rem; font-weight:bold; border:1px solid {fase_color};">
                    {str(m.get('fases','')).upper()}
                </div>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; margin-top:20px; border-top:1px solid rgba(255,255,255,0.1); padding-top:15px;">
                <div style="text-align:center;">
                    <div style="font-size:0.55rem; color:#8b949e;">POTÊNCIA</div>
                    <div style="color:#00f2ff; font-weight:bold; font-size:1.1rem;">{m.get('potencia_hp_cv','-')}</div>
                </div>
                <div style="text-align:center; border-left:1px solid #ffffff11; border-right:1px solid #ffffff11;">
                    <div style="font-size:0.55rem; color:#8b949e;">ROTAÇÃO</div>
                    <div style="color:#10b981; font-weight:bold; font-size:1.1rem;">{m.get('rpm_nominal','-')}</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.55rem; color:#8b949e;">AMPERAGEM</div>
                    <div style="color:#f59e0b; font-weight:bold; font-size:1.1rem;">{m.get('corrente_nominal_a','-')}A</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.55rem; color:#8b949e;">TENSÃO</div>
                    <div style="color:#a855f7; font-weight:bold; font-size:1rem;">{m.get('tensao_v','-')}V</div>
                </div>
                <div style="text-align:center; border-left:1px solid #ffffff11; border-right:1px solid #ffffff11;">
                    <div style="font-size:0.55rem; color:#8b949e;">POLARIDADE</div>
                    <div style="color:white; font-weight:bold; font-size:1rem;">{m.get('polos','-')} P</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.55rem; color:#8b949e;">FREQ.</div>
                    <div style="color:#aaa; font-weight:bold; font-size:1rem;">{m.get('frequencia_hz','-')}Hz</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- CONTEÚDO EXPANDIDO ---
        if st.session_state.detalhes_visiveis.get(key_det):
            st.markdown("<div style='background:rgba(0,15,25,0.9); border:1px solid #00ffff44; border-radius:0 0 12px 12px; padding:20px; margin-top:-35px; margin-bottom:40px;'>", unsafe_allow_html=True)
            
            # 1. ABA DE LIGAÇÕES DINÂMICAS
            render_esquema_ligacao(m)

            # 2. OUTRAS ABAS TÉCNICAS
            t_bobina, t_mecanica = st.tabs(["🌀 BOBINAGEM", "⚙️ MECÂNICA"])
            
            with t_bobina:
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("PRINCIPAL")
                    render_dado("Passo", limpar_passo(m.get("passo_principal")))
                    render_dado("Fio", m.get("bitola_fio_principal"))
                    render_dado("Espiras", m.get("espiras_principal"))
                with c2:
                    st.caption("AUXILIAR")
                    render_dado("Passo", limpar_passo(m.get("passo_auxiliar")))
                    render_dado("Fio", m.get("bitola_fio_auxiliar"))
                    render_dado("Espiras", m.get("espiras_auxiliar"))
                render_dado("Ligação Interna", m.get("ligacao_interna"), highlight=True)

            with t_mecanica:
                c1, c2 = st.columns(2)
                with c1:
                    render_dado("Rolamento Diant.", m.get("rolamento_dianteiro"))
                    render_dado("Rolamento Tras.", m.get("rolamento_traseiro"))
                with c2:
                    render_dado("Pacote", m.get("comprimento_pacote_mm"), "mm")
                    render_dado("Ranhuras", m.get("numero_ranhuras"))
            
            st.markdown("</div>", unsafe_allow_html=True)

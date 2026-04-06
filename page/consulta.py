import streamlit as st
import re

# =============================
# 🎨 INJEÇÃO DE CSS (COMPACTO)
# =============================
def aplicar_estilo():
    st.markdown("""
        <style>
        /* CONTAINER DO MOTOR */
        .motor-container {
            position: relative;
            margin-bottom: 10px; /* Reduzido para aproximar os cards */
        }

        /* CARD VISUAL - MAIS COMPACTO */
        .tech-card {
            background: linear-gradient(145deg, #081018, #05070d);
            border: 2px solid #00ffff33;
            border-radius: 15px;
            padding: 18px; /* Reduzido de 30px para ocupar menos espaço */
            text-align: center;
            box-shadow: 0 0 20px #00ffff11;
            transition: all 0.3s ease;
            position: relative;
            z-index: 1;
        }

        .motor-container:hover .tech-card {
            border-color: #00ffff;
            box-shadow: 0 0 40px #00ffff33;
            transform: translateY(-1px);
        }

        /* BOTÃO INVISÍVEL (Cobre todo o card para clique) */
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

        /* ELEMENTOS INTERNOS DO CARD */
        .card-title { font-size: 1.25rem; color: #00ffff; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 2px; }
        .card-subtitle { color: #8b949e; font-size: 0.8rem; margin-bottom: 10px; }
        .metric-unit { font-size: 1rem; font-weight: bold; }

        /* Faz o texto ignorar o mouse para não bloquear o clique no botão */
        .tech-card * {
            pointer-events: none;
        }
        </style>
    """, unsafe_allow_html=True)

# =============================
# 🛠️ FUNÇÕES AUXILIARES
# =============================
def limpar_unidade(valor, unidade_fixa):
    """Remove a unidade do texto se ela já existir para evitar duplicação."""
    if not valor: return "-"
    valor_str = str(valor).upper()
    unidade_fixa = unidade_fixa.upper()
    # Remove a unidade (ex: 'CV') do valor para não ficar 'CV CV HP'
    limpo = valor_str.replace(unidade_fixa, "").strip()
    return limpo

def limpar_passo(passo_raw):
    if not passo_raw: return "---"
    s = str(passo_raw).strip()
    return re.sub(r"^[1][\s?:\-]*", "", s).replace(":", " ").replace("-", " ").strip()

def obter_configuracoes_ligacao(m):
    fases = 3 if "TRI" in str(m.get('fases', '')).upper() else 1
    tensao = str(m.get('tensao_v', ''))
    if fases == 3:
        if "220" in tensao and "380" in tensao:
            return "⚡ 220V: Triângulo (Δ) | 380V: Estrela (Y)"
        return f"⚡ Tensão: {tensao}"
    return "🔌 Monofásico: Verifique esquema Série/Paralelo"

# =============================
# 🚀 PÁGINA DE CONSULTA
# =============================
def show(supabase):
    aplicar_estilo()
    
    st.title("🔍 Central de Motores")
    busca = st.text_input("", placeholder="Pesquisar por Marca ou Modelo...", label_visibility="collapsed")
    
    try:
        # Busca direta do banco
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        motores = res.data if res.data else []
    except Exception:
        st.error("Falha na conexão com o Banco de Dados.")
        return

    if busca:
        q = busca.lower()
        motores = [m for m in motores if q in f"{str(m.get('marca',''))} {str(m.get('modelo',''))} {str(m.get('potencia_hp_cv',''))}".lower()]

    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"
        aberto = st.session_state.detalhes_visiveis.get(key_det, False)

        # Limpeza de unidades para evitar duplicatas visuais
        potencia = limpar_unidade(m.get('potencia_hp_cv'), "CV")
        rpm = limpar_unidade(m.get('rpm_nominal'), "RPM")
        corrente = limpar_unidade(m.get('corrente_nominal_a'), "A")
        
        marca = str(m.get('marca') or "---").upper()
        modelo = m.get('modelo') or "-"

        # Container do card
        st.markdown(f'<div class="motor-container">', unsafe_allow_html=True)

        # HTML do card com métricas limpas
        st.markdown(f'''
            <div class="tech-card">
                <div class="card-title">{marca}</div>
                <div class="card-subtitle">ID: {modelo}</div>
                <div style="display: flex; justify-content: space-around; gap: 5px;">
                    <div style="color: white;"><span style="color: #00ffff;" class="metric-unit">{potencia}</span> CV HP</div>
                    <div style="color: white;"><span style="color: #10b981;" class="metric-unit">{rpm}</span> RPM</div>
                    <div style="color: white;"><span style="color: #f59e0b;" class="metric-unit">{corrente}</span> A</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

        # Botão invisível que dispara a expansão do card
        if st.button(" ", key=f"btn_{id_m}"):
            st.session_state.detalhes_visiveis[key_det] = not aberto
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Área de detalhes (aparece quando o card é clicado)
        if aberto:
            with st.container():
                st.markdown("""
                <div style="background: rgba(0,255,255,0.03); border: 2px solid #00ffff44; 
                            border-top:none; border-radius: 0 0 15px 15px; padding: 15px; 
                            margin: -15px auto 20px auto; max-width: 92%;">
                """, unsafe_allow_html=True)
                
                t1, t2, t3 = st.tabs(["🔌 Ligações", "🌀 Bobinagem", "⚙️ Mecânica"])
                
                with t1:
                    st.info(obter_configuracoes_ligacao(m))
                    st.write(f"**Fases:** {m.get('fases') or '-'} | **Tensão:** {m.get('tensao_v') or '-'} V")
                    st.write(f"**Nº Série:** {m.get('num_serie') or '-'}")
                
                with t2:
                    c1, c2 = st.columns(2)
                    c1.metric("Passo Principal", limpar_passo(m.get("passo_principal")))
                    c2.metric("Bitola Fio", m.get("bitola_fio_principal") or "---")
                    st.write(f"**Esquema:** {m.get('observacoes') or '-'}")
                
                with t3:
                    st.markdown(f"**Rolamento Dianteiro:** `{m.get('rolamento_dianteiro') or '-'}`")
                    st.markdown(f"**Rolamento Traseiro:** `{m.get('rolamento_traseiro') or '-'}`")
                
                st.markdown('</div>', unsafe_allow_html=True)

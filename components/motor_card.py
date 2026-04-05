import streamlit as st
import re

# Função para limpar a formatação do passo (ex: tira o "1:")
def limpar_passo(passo_raw):
    if not passo_raw: return "---"
    s = str(passo_raw).strip()
    s = re.sub(r"^[1][\s?:\-]*", "", s)
    return s.replace(":", " ").replace("-", " ").strip()

# Função para criar as caixinhas de dados nas abas
def render_dado(label, valor, unidade="", highlight=False):
    color = "#00ffff" if not highlight else "#f59e0b"
    val = valor if valor and str(valor).lower() not in ["none", "nan", ""] else "---"
    st.markdown(f"""
        <div style="background: rgba(0, 255, 255, 0.03); border: 1px solid rgba(0, 255, 255, 0.1); border-radius: 6px; padding: 10px; margin-bottom: 5px;">
            <div style="font-size: 0.65rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
            <div style="font-size: 1rem; color: white; font-family: monospace; font-weight: bold;">{val} <span style="color: {color}; font-size: 0.8rem;">{unidade}</span></div>
        </div>
    """, unsafe_allow_html=True)

def motor_card(motor):
    id_m = motor.get("id", "S/N")
    key_det = f"vis_{id_m}"

    # Variável de sessão para controlar se a aba deste motor está aberta
    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}

    # --- 1. O BOTÃO (QUE SERVE DE FUNDO PARA O CARD) ---
    # Criamos um div para envolver o botão e o conteúdo visual do card
    # Isso nos permite aplicar estilos de card ao conjunto e controlar o clique
    card_container_style = """
        background: linear-gradient(145deg, #081018, #05070d);
        border: 2px solid #00ffff33;
        border-radius: 18px;
        padding: 25px;
        box-shadow: 0 0 30px #00ffff22;
        margin: 20px auto;
        width: 100%; /* Ocupa a largura total disponível */
        cursor: pointer;
        transition: 0.3s; 
    """

    # O botão 'invisível' que ocupa todo o espaço do card para ser clicável
    # Usamos o CSS para estilizá-lo como o fundo do card
    button_style = """
        width: 100%;
        height: 100%;
        background: transparent;
        border: none;
        position: absolute;
        top: 0;
        left: 0;
        z-index: 10;
    """

    st.markdown(f"<div class=\'clickable-card\' style='{card_container_style}' id=\'card-{id_m}'>", unsafe_allow_html=True)

    # O conteúdo visual do card
    st.markdown(f"""
        <div style="pointer-events: none;">
            <small style="color: #00ffff; font-family: monospace; letter-spacing: 2px;">REGISTRO TÉCNICO ID: #{id_m}</small>
            <div style="font-size: 1.35rem; color: white; font-weight: bold; margin-top: 5px;">
                {str(motor.get('marca', '---')).upper()} <span style="font-weight: 300; color: #aaa; font-size: 1.1rem;">{motor.get('modelo', '')}</span>
            </div>
            <div style="font-size: 0.7rem; color: #8b949e;">MOTORES {str(motor.get('fases', '')).upper()}</div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; margin-top: 12px;">
                <div style="text-align: center;">
                    <div style="font-size: 0.6rem; color: #8b949e; text-transform: uppercase;">Potência</div>
                    <div style="font-size: 1.1rem; font-weight: bold; color: #00f2ff;">{motor.get('potencia_hp_cv','-')}</div>
                </div>
                <div style="text-align: center; border-left: 1px solid rgba(255,255,255,0.1); border-right: 1px solid rgba(255,255,255,0.1);">
                    <div style="font-size: 0.6rem; color: #8b949e; text-transform: uppercase;">Rotação</div>
                    <div style="font-size: 1.1rem; font-weight: bold; color: #10b981;">{motor.get('rpm_nominal','-')} <small style="font-size:0.6rem;'>RPM</small></div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.6rem; color: #8b949e; text-transform: uppercase;">Tensão</div>
                    <div style="font-size: 1.1rem; font-weight: bold; color: #a855f7;">{motor.get('tensao_v','-')}V</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # O botão real para capturar o clique
    # Ele precisa ser separado do markdown para Streamlit capturar o clique.
    # É estilizado para ser transparente e cobrir a área do card.
    clicked = st.button("", key=f"btn_card_{id_m}", use_container_width=True)
    if clicked:
        st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
        # Forçar um re-run para que o estado de exibição seja atualizado imediatamente
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # --- 3. A ABA EXPANDIDA COM OS DADOS DO CSV ---
    if st.session_state.detalhes_visiveis.get(key_det):
        st.markdown("<div style='background: rgba(0,25,35,0.95); border: 1px solid #00ffff44; border-radius: 8px; padding: 20px; margin-top: -15px; margin-bottom: 30px;'>", unsafe_allow_html=True)
        
        t1, t2, t3 = st.tabs(["📋 CONEXÃO", "🌀 BOBINAGEM", "⚙️ MECÂNICA"])
        
        with t1:
            st.markdown("<small style='color:#8b949e;'>LIGAÇÃO DE CABOS PADRÃO</small>", unsafe_allow_html=True)
            st.code("1:AZ | 2:BR | 3:LA | 4:AM | 5:PR | 6:VM", language="")
            render_dado("Amperagem Nominal", motor.get("corrente_nominal_a"), "A")
            render_dado("Capacitores", f"{motor.get('capacitor_permanente', '')} / {motor.get('capacitor_partida', '')}")
            
        with t2:
            col_p, col_a = st.columns(2)
            with col_p:
                render_dado("Passo (P)", limpar_passo(motor.get("passo_principal")))
                render_dado("Fio (P)", motor.get("bitola_fio_principal"))
                render_dado("Espiras (P)", motor.get("espiras_principal"))
            with col_a:
                render_dado("Passo (A)", limpar_passo(motor.get("passo_auxiliar")))
                render_dado("Fio (A)", motor.get("bitola_fio_auxiliar"))
                render_dado("Espiras (A)", motor.get("espiras_auxiliar"))
            render_dado("Ligação Interna", motor.get("ligacao_interna"), highlight=True)
            
        with t3:
            render_dado("Ranhuras", motor.get("numero_ranhuras"))
            render_dado("Pacote (mm)", motor.get("comprimento_pacote_mm"))
            render_dado("Rolamentos", f"D: {motor.get('rolamento_dianteiro')} / T: {motor.get('rolamento_traseiro')}")
        
        st.markdown("</div>", unsafe_allow_html=True)

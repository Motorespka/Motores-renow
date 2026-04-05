import streamlit as st

def motor_card(motor):
    # Pegamos o ID para garantir chaves únicas
    id_m = motor.get("id")
    
    # Criamos um container que usará as regras do style.css
    with st.container():
        # 1. O BOTÃO INVISÍVEL (Para detecção de clique no card)
        # Ele fica por baixo, mas ocupa o espaço para o Streamlit entender o clique
        if st.button(" ", key=f"btn_card_{id_m}", use_container_width=True):
            st.session_state["motor_aberto"] = motor
            # Inverte o estado de exibição se você estiver usando o dicionário de detalhes
            key_det = f"vis_{id_m}"
            if "detalhes_visiveis" in st.session_state:
                st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()

        # 2. O VISUAL TECH (HTML + CSS que você já definiu)
        # Usamos o margin-top negativo para subir o visual por cima do botão acima
        st.markdown(f"""
        <div style="margin-top:-105px; margin-bottom:20px; pointer-events:none; position:relative; z-index:5;">
            <div class="tech-card">
                <small style="color:#00ffff; font-family:monospace; opacity:0.7;">
                    REGISTRO TÉCNICO ID: #{id_m}
                </small>
                
                <div style="font-size:1.35rem; color:white; font-weight:bold; margin-bottom:15px;">
                    {(motor.get('marca') or '---').upper()} 
                    <span style="color:#aaa; font-size:1.1rem; font-weight:normal;">
                        {motor.get('modelo') or ''}
                    </span>
                </div>
                
                <div style="display:grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap:10px;">
                    <div style="text-align:center;">
                        <div style="font-size:0.6rem; color:#8b949e; text-transform:uppercase;">Potência</div>
                        <div style="color:#00f2ff; font-weight:bold; font-family:monospace;">{motor.get('potencia_hp_cv','-')}</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:0.6rem; color:#8b949e; text-transform:uppercase;">Rotação</div>
                        <div style="color:#10b981; font-weight:bold; font-family:monospace;">{motor.get('rpm_nominal','-')}</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:0.6rem; color:#8b949e; text-transform:uppercase;">Corrente</div>
                        <div style="color:#f59e0b; font-weight:bold; font-family:monospace;">{motor.get('corrente_nominal_a','-')}A</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:0.6rem; color:#8b949e; text-transform:uppercase;">Tensão</div>
                        <div style="color:#a855f7; font-weight:bold; font-family:monospace;">{motor.get('tensao_v','-')}V</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

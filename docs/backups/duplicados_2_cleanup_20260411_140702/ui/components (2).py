import streamlit as st

# =============================
# HUD HEADER
# =============================

def hud():
    st.markdown("""
        <div class="hud">
        ⚡ MOTO-RENOW INDUSTRIAL SYSTEM ONLINE
        </div>
    """, unsafe_allow_html=True)


# =============================
# CARD TECNOLÓGICO
# =============================

def tech_card(title, value):

    st.markdown(f"""
        <div class="tech-card">
            <small>{title}</small>
            <h2 style="color:#00ffff">{value}</h2>
        </div>
    """, unsafe_allow_html=True)

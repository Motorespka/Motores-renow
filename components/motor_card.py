import streamlit as st

def motor_card(motor):
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)

        c1.metric("⚡ Potência", motor.get("potencia_hp_cv","-"))
        c2.metric("🔄 RPM", motor.get("rpm_nominal","-"))
        c3.metric("⚡ Corrente", motor.get("corrente_nominal_a","-"))
        c4.metric("🔌 Tensão", motor.get("tensao_v","-"))

        if st.button(
            "Abrir informações completas",
            key=f"motor_{motor['id']}",
            use_container_width=True
        ):
            st.session_state["motor_aberto"] = motor
import streamlit as st
from services.database import atualizar_motor

def show():

    motor = st.session_state.motor_editando

    st.title("✏️ Editar Motor")

    with st.form("editar"):

        marca = st.text_input("Marca", motor.get("marca",""))
        modelo = st.text_input("Modelo", motor.get("modelo",""))
        potencia = st.text_input("Potência", motor.get("potencia",""))
        tensao = st.text_input("Tensão", motor.get("tensao",""))
        rpm = st.text_input("RPM", motor.get("rpm",""))

        origem = st.selectbox(
            "Origem",
            ["União","Rebobinador","Próprio"],
            index=["União","Rebobinador","Próprio"].index(
                motor.get("origem_calculo","Próprio")
            )
        )

        salvar = st.form_submit_button("Salvar")
        fechar = st.form_submit_button("Fechar")

    if salvar:

        motor.update({
            "marca":marca,
            "modelo":modelo,
            "potencia":potencia,
            "tensao":tensao,
            "rpm":rpm,
            "origem_calculo":origem
        })

        atualizar_motor(motor["id"], motor)

        st.session_state.pagina = "consulta"
        st.rerun()

    if fechar:
        st.session_state.pagina = "consulta"
        st.rerun()

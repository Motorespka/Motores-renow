import streamlit as st
from services.ocr_motor import ler_placa_motor

def show():
    st.title("Cadastro de Motor")

    campos = [
        "marca","modelo","potencia","tensao","corrente",
        "rpm","frequencia","fp","carcaca","ip",
        "isolacao","regime","rolamento_dianteiro",
        "rolamento_traseiro","peso","diametro_eixo",
        "comprimento_pacote","numero_ranhuras",
        "ligacao","fabricacao"
    ]

    for campo in campos:
        if campo not in st.session_state:
            st.session_state[campo] = ""

    st.subheader("📸 Escanear placa")

    imagem = st.file_uploader(
        "Envie foto da placa do motor",
        type=["png","jpg","jpeg"]
    )

    if imagem:
        st.image(imagem, width=300)

        if st.button("🔎 Ler placa"):
            with st.spinner("Lendo placa..."):
                dados = ler_placa_motor(imagem)

            for chave, valor in dados.items():
                if chave in st.session_state:
                    st.session_state[chave] = valor

            st.success("✅ Dados preenchidos automaticamente!")
            st.rerun()

    st.subheader("⚙️ Dados do Motor")

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Marca", key="marca")
        st.text_input("Modelo", key="modelo")
        st.text_input("Potência", key="potencia")

    with col2:
        st.text_input("Classe de Isolação", key="isolacao")

    if st.button("💾 Salvar Motor", use_container_width=True):
        motor = {campo: st.session_state[campo] for campo in campos}
        st.success("Motor salvo com sucesso!")
        st.json(motor)

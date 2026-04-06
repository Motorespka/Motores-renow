import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import random

def show(supabase):

    # --- ESTILO CYBERPUNK ---
    st.markdown("""
        <style>
            .titulo-cyber {
                color: #00f2ff;
                text-shadow: 0 0 10px #00f2ff, 0 0 20px #00f2ff;
                font-family: 'Courier New', Courier, monospace;
                font-weight: bold;
                text-align: center;
            }
            .stCamera { border: 2px solid #00f2ff; border-radius: 10px; box-shadow: 0 0 15px #00f2ff; }
            .section-box {
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #1f2937;
                background-color: #0d1117;
                margin-bottom: 20px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="titulo-cyber">⚡ CADASTRO DE MATRIZ & O.S.</h1>', unsafe_allow_html=True)

    # --- FUNÇÃO DE INTELIGÊNCIA ARTIFICIAL (CORRIGIDA) ---
    def processar_plaqueta(foto_arquivo):
        try:
            img = Image.open(foto_arquivo)

            # 🔄 correção de selfie
            img = img.transpose(Image.FLIP_LEFT_RIGHT)

            prompt = """
            Você é um engenheiro sênior de manutenção de motores. Analise a imagem e extraia os dados.
            Retorne APENAS um JSON puro (sem markdown) com estas chaves:
            "marca", "cv", "rpm", "v", "a", "carcaca", "cos_phi", "isol".
            Se não ler algo, coloque "N/D".
            """

            keys = st.secrets["GEMINI_API_KEY"]
            response = None

            for key in keys:
                try:
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel('gemini-2.5-flash')

                    response = model.generate_content([prompt, img])

                    # debug opcional
                    # st.write(f"🔑 Usando key: {key[:6]}")

                    break

                except Exception as e:
                    erro = str(e).lower()

                    if "quota" in erro or "limit" in erro or "429" in erro:
                        continue
                    else:
                        st.error(f"Erro inesperado: {e}")
                        return None

            if response is None:
                st.error("❌ Todas as keys atingiram limite")
                return None

            limpo = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(limpo)

        except Exception as e:
            st.error(f"⚠️ Falha na varredura: {e}")
            return None

    # --- ÁREA DE CAPTURA ---
    with st.container():
        col_cam, col_ia = st.columns([1, 1])
        
        with col_cam:
            st.subheader("📸 Scanner de Plaqueta")

            foto_camera = st.camera_input("Capture a identidade do motor")
            foto_upload = st.file_uploader("📂 Ou envie a imagem da plaqueta", type=["jpg", "png", "jpeg"])

            foto = foto_camera if foto_camera else foto_upload
        
        with col_ia:
            st.subheader("🤖 Processamento Neural")
            if foto:
                if st.button("🧬 INICIAR VARREDURA BIOMÉTRICA"):
                    with st.spinner("Decodificando DNA do motor..."):
                        dados = processar_plaqueta(foto)
                        if dados:
                            st.session_state.motor_data = dados
                            st.success("Dados extraídos para a memória do sistema!")
            else:
                st.info("Aguardando entrada visual para análise.")

    # Inicializa dados se vazio
    if "motor_data" not in st.session_state:
        st.session_state.motor_data = {}

    # --- FORMULÁRIO TÉCNICO ---
    with st.form("os_form"):
        st.markdown("### 🛠️ Ficha Técnica de Alta Precisão")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            cliente = st.text_input("👤 Cliente", placeholder="Ex: Usina Delta")
            marca = st.text_input("🏷️ Marca", value=st.session_state.motor_data.get("marca", ""))
            carcaca = st.text_input("🏗️ Carcaça", value=st.session_state.motor_data.get("carcaca", ""))

        with c2:
            potencia = st.text_input("💪 Potência (CV/kW)", value=st.session_state.motor_data.get("cv", ""))
            rpm = st.text_input("🔄 RPM Nominal", value=st.session_state.motor_data.get("rpm", ""))
            voltagem = st.text_input("⚡ Tensão (V)", value=st.session_state.motor_data.get("v", ""))

        with c3:
            corrente = st.text_input("🔌 Corrente (A)", value=st.session_state.motor_data.get("a", ""))
            cos_phi = st.text_input("📉 Cos Φ", value=st.session_state.motor_data.get("cos_phi", ""))
            isol = st.text_input("❄️ Classe Isol.", value=st.session_state.motor_data.get("isol", ""))

        st.divider()
        st.markdown("### 🧠 Especificações de Rebobinagem (Nível Especialista)")
        
        c4, c5, c6 = st.columns(3)
        with c4:
            ligacao = st.selectbox("🔗 Esquema", ["Estrela (Y)", "Triângulo (Δ)", "Série", "Paralelo", "Dahlander"])
            fio = st.text_input("🧵 Bitola do Fio", placeholder="Ex: 2x 22 AWG")
        
        with c5:
            espiras = st.number_input("🌀 Nº de Espiras", min_value=0)
            passo = st.text_input("🛤️ Passo", placeholder="Ex: 1-8, 1-10")

        with c6:
            try:
                rpm_val = int(''.join(filter(str.isdigit, rpm)))
                polos = 2 if rpm_val > 3000 else 4 if rpm_val > 1500 else 6 if rpm_val > 900 else 8
                st.write(f"📌 Sugestão de Pólos: **{polos} pólos**")
            except:
                st.write("📌 Sugestão de Pólos: --")
            
            peso = st.number_input("⚖️ Peso de Cobre (kg)", format="%.3f")

        defeito = st.text_area("📝 Diagnóstico de Entrada", placeholder="Descreva os danos...")

        btn_save = st.form_submit_button("🚀 SINCRONIZAR COM A MATRIZ (SALVAR)")
        
        if btn_save:
            if not cliente or not marca:
                st.warning("Preencha ao menos o Cliente e a Marca")
            else:
                try:
                    payload = {
                        "cliente": cliente, "marca": marca, "potencia": potencia,
                        "rpm": rpm, "tensao": voltagem, "corrente": corrente,
                        "carcaca": carcaca, "esquema": ligacao, "fio": fio,
                        "espiras": espiras, "passo": passo, "peso_cobre": peso,
                        "diagnostico": defeito, "status": "Em Análise"
                    }
                    supabase.table("ordens_servico").insert(payload).execute()
                    st.success("🛰️ Dados transmitidos com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao acessar banco: {e}")

import streamlit as st
import importlib
import re
import os

# ✅ MANTIDO — TODAS AS SUAS IMPORTAÇÕES ORIGINAIS
from core.engenheiro_ia import engenheiro_busca_v4
from core.aprendizado import aprender
from core.ligacoes_motor import gerar_ligacoes_motor
import diagnostico

# ------------------------------
# BANCO SUPABASE
# ------------------------------
def listar_motores(supabase):
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).limit(1000).execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Erro ao listar motores: {e}")
        return []

def excluir_motor(supabase, id_motor):
    try:
        supabase.table("motores").delete().eq("id", id_motor).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir motor: {e}")
        return False

# ------------------------------
# FORMATAÇÃO TÉCNICA (MANTIDA IGUAL)
# ------------------------------
def limpar_passo(passo_raw):
    if not passo_raw:
        return "---"
    s = str(passo_raw).strip()
    s = re.sub(r"^[1][\s?:\-]*", "", s)
    return s.replace(":", " ").replace("-", " ").strip()

def render_dado(label, valor, unidade="", highlight=False):
    color = "#00ffff" if not highlight else "#f59e0b"
    val = valor if valor and str(valor).lower() not in ["none", "nan", ""] else "---"

    st.markdown(f"""
        <div style="background: rgba(0,255,255,0.03);
        border:1px solid rgba(0,255,255,0.1);
        border-radius:6px;padding:10px;margin-bottom:5px;">
            <div style="font-size:0.65rem;color:#8b949e;
            text-transform:uppercase;letter-spacing:1px;">
            {label}
            </div>
            <div style="font-size:1rem;color:white;
            font-family:monospace;font-weight:bold;">
            {val}
            <span style="color:{color};font-size:0.8rem;">{unidade}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ------------------------------
# TELA PRINCIPAL
# ------------------------------
def show(supabase):
    # Carregamento do CSS
    try:
        if os.path.exists("style.css"):
            with open("style.css") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

    st.markdown("## 🔍 Consulta de Motores")

    # --- BUSCA IA ---
    busca = st.text_input("🧠 Engenheiro IA", placeholder="Ex: weg 2cv 4 polos 220v")
    motores_db = listar_motores(supabase)

    # --- LÓGICA DE BUSCA (IA MANTIDA) ---
    sugestoes = []
    if busca:
        motores, sugestoes = engenheiro_busca_v4(motores_db, busca)
    else:
        motores = motores_db

    # --- SUGESTÕES ---
    if sugestoes:
        cols = st.columns(len(sugestoes))
        for i, s in enumerate(sugestoes):
            if cols[i].button(f"💡 {s}", key=f"sug_{i}"):
                st.session_state["busca_auto"] = s
                st.rerun()

    st.caption(f"Motores encontrados: {len(motores)}")

    # --- ESTADOS ---
    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}
    if "abrir_edit" not in st.session_state:
        st.session_state.abrir_edit = False

    # --- EDITOR (LÓGICA ORIGINAL) ---
    if st.session_state.abrir_edit and st.session_state.get("motor_editando"):
        edit_module = importlib.import_module("page.edit")
        edit_module.show(supabase)
        if st.button("🔙 Voltar"):
            st.session_state.abrir_edit = False
            st.rerun()
        return

    # --- CARDS (SUA INTERFACE HUD ORIGINAL) ---
    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"

        if st.button(" ", key=f"btn_m_{id_m}", use_container_width=True):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()

        # ✅ AJUSTADO: Agora usa 'potencia_hp_cv', 'rpm_nominal' e 'tensao_v' do seu Cadastro.py
        st.markdown(f"""
        <div style="margin-top:-165px;margin-bottom:20px;
        padding:18px;pointer-events:none;position:relative;z-index:5;">
            <small style="color:#00ffff;font-family:monospace;">ID: #{id_m}</small>
            <div style="font-size:1.35rem;color:white;font-weight:bold;">
                {(m.get('marca') or '---').upper()} 
                <span style="color:#aaa;font-size:1.1rem;">{m.get('modelo') or ''}</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:15px;">
                <div style="text-align:center;">
                    <div style="font-size:0.6rem;color:#8b949e;">Potência</div>
                    <div style="color:#00f2ff;font-weight:bold;">{m.get('potencia_hp_cv','-')}</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.6rem;color:#8b949e;">Rotação</div>
                    <div style="color:#10b981;font-weight:bold;">{m.get('rpm_nominal','-')} RPM</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.6rem;color:#8b949e;">Tensão</div>
                    <div style="color:#a855f7;font-weight:bold;">{m.get('tensao_v','-')}V</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- EXPANSÃO (DETALHES COMPLETOS) ---
        if st.session_state.detalhes_visiveis.get(key_det):
            if busca: aprender(busca, m)

            st.markdown("<div style='padding:20px;'>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("✏️ EDITAR", key=f"ed_{id_m}"):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()

            if c2.button("🗑️ EXCLUIR", key=f"ex_{id_m}"):
                if excluir_motor(supabase, id_m): st.rerun()

            # ✅ AJUSTADO: Puxando os campos longos do seu banco
            render_dado("Amperagem", m.get("corrente_nominal_a"), "A")
            render_dado("Ranhuras", m.get("numero_ranhuras"))
            render_dado("Pacote", m.get("comprimento_pacote_mm"), "mm")
            render_dado("Ø Interno", m.get("diametro_interno_estator_mm"), "mm")

            # --- LIGAÇÕES E DIAGNÓSTICO (MANTIDOS) ---
            st.markdown("### 🔌 Esquemas de Ligação")
            ligacoes = gerar_ligacoes_motor(m)
            if ligacoes:
                cols_lig = st.columns(len(ligacoes))
                for idx, lig in enumerate(ligacoes):
                    with cols_lig[idx]:
                        st.markdown(f"""
                        <div style="background: rgba(0,255,255,0.05); border: 1px solid #00ffff33; padding: 10px; border-radius: 8px;">
                            <b style="color:#00ffff;">{lig['titulo']}</b><br>
                            <small>{lig['descricao']}</small>
                        </div>
                        """, unsafe_allow_html=True)

            with st.expander("🧠 Diagnóstico Rápido"):
                diagnostico.render_diagnostico()

            st.markdown("</div>", unsafe_allow_html=True)

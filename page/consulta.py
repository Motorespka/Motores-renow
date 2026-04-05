import streamlit as st
import importlib
import re
import os

# =================================================================
# 1. IMPORTAÇÕES E DEPENDÊNCIAS (PROTEGIDAS)
# =================================================================
try:
    from core.engenheiro_ia import engenheiro_busca_v4
    from core.aprendizado import aprender
    from core.ligacoes_motor import gerar_ligacoes_motor
    # AJUSTE: Como diagnostico.py está na pasta 'page', importamos assim:
    from page import diagnostico 
except Exception as e:
    # Caso alguma dependência falhe, o app não quebra
    pass

# =================================================================
# 2. FUNÇÕES DE BANCO DE DADOS (COMPATÍVEIS COM CADASTRO.PY)
# =================================================================
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

# =================================================================
# 3. INTERFACE E FORMATAÇÃO (ESTILO HUD ORIGINAL)
# =================================================================
def render_dado(label, valor, unidade="", highlight=False):
    color = "#00ffff" if not highlight else "#f59e0b"
    val = valor if valor and str(valor).lower() not in ["none", "nan", ""] else "---"

    st.markdown(f"""
        <div style="background: rgba(0,255,255,0.03); border:1px solid rgba(0,255,255,0.1);
        border-radius:6px; padding:10px; margin-bottom:5px;">
            <div style="font-size:0.65rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">
            {label}
            </div>
            <div style="font-size:1rem; color:white; font-family:monospace; font-weight:bold;">
            {val} <span style="color:{color}; font-size:0.8rem;">{unidade}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# =================================================================
# 4. TELA PRINCIPAL (EXECUTADA PELO APP.PY)
# =================================================================
def show(supabase):
    # Carregamento do CSS
    if os.path.exists("style.css"):
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    st.markdown("## 🔍 Consulta de Motores")

    # --- CAMPO DE BUSCA IA ---
    busca = st.text_input("🧠 Engenheiro IA", placeholder="Ex: weg 2cv 4 polos")
    
    motores_db = listar_motores(supabase)

    # --- LÓGICA DE FILTRO (COMPATÍVEL COM NOMES DO CADASTRO.PY) ---
    sugestoes = []
    if busca:
        try:
            motores, sugestoes = engenheiro_busca_v4(motores_db, busca)
        except:
            motores = [m for m in motores_db if busca.lower() in 
                      f"{m.get('marca','')} {m.get('modelo','')} {m.get('potencia_hp_cv','')}".lower()]
    else:
        motores = motores_db

    # --- SUGESTÕES DE IA ---
    if sugestoes:
        cols = st.columns(len(sugestoes))
        for i, s in enumerate(sugestoes):
            if cols[i].button(f"💡 {s}", key=f"sug_{i}"):
                st.session_state["busca_auto"] = s
                st.rerun()

    st.caption(f"Motores encontrados: {len(motores)}")

    # --- ESTADOS DE NAVEGAÇÃO ---
    if "detalhes_visiveis" not in st.session_state:
        st.session_state.detalhes_visiveis = {}
    if "abrir_edit" not in st.session_state:
        st.session_state.abrir_edit = False

    # --- LÓGICA DO EDITOR ---
    if st.session_state.abrir_edit and st.session_state.get("motor_editando"):
        try:
            edit_module = importlib.import_module("page.edit")
            edit_module.show(supabase)
            if st.button("🔙 Voltar"):
                st.session_state.abrir_edit = False
                st.rerun()
            return
        except:
            st.error("Módulo de edição não encontrado.")

    # --- RENDERIZAÇÃO DOS CARDS (INTERFACE HUD) ---
    for m in motores:
        id_m = m.get("id")
        key_det = f"vis_{id_m}"

        if st.button(" ", key=f"btn_m_{id_m}", use_container_width=True):
            st.session_state.detalhes_visiveis[key_det] = not st.session_state.detalhes_visiveis.get(key_det, False)
            st.rerun()

        st.markdown(f"""
        <div style="margin-top:-165px; margin-bottom:20px; padding:18px; pointer-events:none; position:relative; z-index:5;">
            <small style="color:#00ffff; font-family:monospace;">REGISTRO TÉCNICO ID: #{id_m}</small>
            <div style="font-size:1.35rem; color:white; font-weight:bold;">
                {(m.get('marca') or '---').upper()} 
                <span style="color:#aaa; font-size:1.1rem;">{m.get('modelo') or ''}</span>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-top:15px;">
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e;">Potência</div>
                    <div style="color:#00f2ff; font-weight:bold;">{m.get('potencia_hp_cv','-')}</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e;">Rotação</div>
                    <div style="color:#10b981; font-weight:bold;">{m.get('rpm_nominal','-')} RPM</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:0.6rem; color:#8b949e;">Tensão</div>
                    <div style="color:#a855f7; font-weight:bold;">{m.get('tensao_v','-')}V</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.detalhes_visiveis.get(key_det):
            if busca: 
                try: aprender(busca, m)
                except: pass

            st.markdown("<div style='padding:20px;'>", unsafe_allow_html=True)
            
            c_edit, c_del = st.columns(2)
            if c_edit.button("✏️ EDITAR", key=f"ed_{id_m}"):
                st.session_state.motor_editando = m
                st.session_state.abrir_edit = True
                st.rerun()

            if c_del.button("🗑️ EXCLUIR", key=f"ex_{id_m}"):
                if excluir_motor(supabase, id_m): st.rerun()

            render_dado("Amperagem", m.get("corrente_nominal_a"), "A")
            render_dado("Ranhuras", m.get("numero_ranhuras"))
            render_dado("Pacote", m.get("comprimento_pacote_mm"), "mm")
            render_dado("Fio Principal", m.get("bitola_fio_principal"))

            st.markdown("### 🔌 Esquemas de Ligação")
            try:
                ligacoes = gerar_ligacoes_motor(m)
                if ligacoes:
                    cols_lig = st.columns(len(ligacoes))
                    for idx, lig in enumerate(ligacoes):
                        with cols_lig[idx]:
                            st.markdown(f"""
                            <div style="background: rgba(0,255,255,0.05); border: 1px solid #00ffff33; padding: 10px; border-radius: 8px;">
                                <b style="color:#00ffff;">{lig.get('titulo','Ligação')}</b><br>
                                <small>{lig.get('descricao','')}</small>
                            </div>
                            """, unsafe_allow_html=True)
            except:
                st.info("Esquema disponível nas observações.")

            with st.expander("🧠 Diagnóstico Rápido"):
                try:
                    # Chamada correta para a função no seu page/diagnostico.py
                    diagnostico.render_diagnostico()
                except:
                    st.write("Verifique a resistência das bobinas.")

            st.divider()
            st.markdown("**📝 Observações Adicionais:**")
            st.write(m.get("observacoes", "Sem observações registradas."))
            st.markdown("</div>", unsafe_allow_html=True)

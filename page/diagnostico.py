import streamlit as st
import os

# Tenta importar funções do core para cálculos avançados se necessário
try:
    from core.calculadora import calcular_corrente # Exemplo de função do seu core
    from core.ligacao_motor import gerar_ligacoes_motor
except:
    pass

def render_diagnostico():
    """Renderiza as informações de diagnóstico rápido dentro de um container"""
    st.markdown("""
<div style="background: rgba(0,255,255,0.02); border: 1px solid rgba(0,255,255,0.1); padding: 15px; border-radius: 10px;">

### ⚡ Identificação rápida
✅ **Girou leve** → 2 polos  
✅ **Girou firme** → 4 polos  
✅ **Pesado** → 6 ou 8 polos  

---

### ⚡ Teste de resistência
**Bobinas iguais** = OK  
**Uma diferente** = defeito  

---

### ⚡ Corrente
Diferença máxima entre fases: **10%**

</div>
""", unsafe_allow_html=True)

def show(supabase=None):
    """Página completa de diagnóstico com integração ao Core"""
    st.title("🧠 Diagnóstico Técnico")
    
    tab1, tab2 = st.tabs(["Checklist Rápido", "Calculadora de Apoio"])
    
    with tab1:
        render_diagnostico()
        
    with tab2:
        st.subheader("Simulador de Carga")
        v = st.number_input("Tensão (V)", value=220)
        p = st.number_input("Potência (CV)", value=1.0)
        if st.button("Analisar Corrente Esperada"):
            # Aqui ele usaria a lógica da sua pasta core
            st.info(f"Para um motor de {p}CV em {v}V, a corrente deve estar próxima ao cadastrado no banco.")


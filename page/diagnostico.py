import streamlit as st

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

def show():
    """Mantém a função original caso queira acessar como página cheia"""
    st.title("🧠 Diagnóstico Rápido de Motores")
    render_diagnostico()

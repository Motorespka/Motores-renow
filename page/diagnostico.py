import streamlit as st

def show():

    st.title("🧠 Diagnóstico Rápido de Motores")

    st.markdown("""
### ⚡ Identificação rápida

✅ Girou leve → 2 polos  
✅ Girou firme → 4 polos  
✅ Pesado → 6 ou 8 polos  

---

### ⚡ Teste de resistência

Bobinas iguais = OK  
Uma diferente = defeito  

---

### ⚡ Corrente

Diferença máxima entre fases:
**10%**
""")
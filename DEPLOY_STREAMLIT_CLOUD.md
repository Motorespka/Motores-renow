## Deploy no Streamlit Cloud (site principal)

Este repositório foi organizado para **Streamlit** continuar sendo o **entrypoint principal** e não depender do runtime do Next.js/FastAPI.

### 1) Configurar o app no Streamlit Cloud
- **Repository**: este repo
- **Main file path**: `App.py`
- **Python requirements**: `requirements.txt` (raiz)

> Desenvolvimento funcional: edite `app.py`.  
> Compatibilidade de deploy: `App.py` apenas importa e executa `app.main()`.

### 2) Variáveis/Secrets (Streamlit Cloud)
No Streamlit Cloud, configure em **Secrets** (ou variáveis do app):

Obrigatórias para PROD (Supabase):
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (ou `SUPABASE_KEY`)

Opcional (controle de ambiente):
- `ENV=PROD` (ou `DEV` para forçar modo dev)

### 3) Comportamento e fallback
- O Streamlit sempre mantém as páginas legadas (pasta `page/`) e a navegação do shell.

### 4) Rollback rápido (se der B.O.)
- No Streamlit Cloud, volte o deploy para o **commit anterior** (ou branch anterior).
- Alternativa: mantenha um branch `stable-streamlit` apontando para a versão “antiga” e troque o branch do app no Streamlit Cloud.


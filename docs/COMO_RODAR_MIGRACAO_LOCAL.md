# Como Rodar Localmente (MVP fora do Streamlit)

## 1) Streamlit legado / dev funcional (continua ativo)

```bash
streamlit run app.py
```

## 2) Backend FastAPI

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

### `.env` do backend (obrigatorio)

```env
APP_ENV=dev
APP_DEBUG=true
API_PREFIX=/api
BACKEND_CORS_ORIGINS=http://localhost:3000

SUPABASE_URL=https://SEU_PROJETO.supabase.co
SUPABASE_ANON_KEY=SEU_SUPABASE_ANON_KEY
```

### `.env` do backend (recomendado)

```env
SUPABASE_SERVICE_ROLE_KEY=SEU_SUPABASE_SERVICE_ROLE_KEY
DEFAULT_PAID_PLANS=paid,pro,premium,enterprise,business
SUPABASE_MOTORES_BUCKET=motores-imagens

GEMINI_API_KEY=SUA_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash

CADASTRO_MAX_FILES=5
CADASTRO_MAX_FILE_SIZE_MB=12
CADASTRO_MAX_TOTAL_SIZE_MB=40
```

## 3) Frontend Next.js

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

### `.env.local` do frontend

```env
NEXT_PUBLIC_SUPABASE_URL=https://SEU_PROJETO.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=SEU_SUPABASE_ANON_KEY
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

## URLs esperadas

- Streamlit legado: `http://localhost:8501`
- Backend novo: `http://localhost:8000`
- Frontend novo: `http://localhost:3000`

## Ordem recomendada

1. Subir backend (`8000`).
2. Subir frontend (`3000`).
3. Testar login e consulta no frontend novo.
4. Testar cadastro novo (`/cadastro`) com uma imagem real.
5. Manter Streamlit para os fluxos ainda nao migrados.

## Teste rapido de endpoints

1. `GET http://localhost:8000/api/health`
2. Logar no frontend (`/login`)
3. Abrir `/dashboard` e conferir perfil
4. Abrir `/motors`
5. Abrir `/motors/{id}` (conta paga/admin)
6. Abrir `/admin` (somente admin)
7. Abrir `/cadastro` e testar `analyze` + `save`

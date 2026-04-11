# Backend (FastAPI)

API paralela ao Streamlit para migracao progressiva.

## Objetivo desta etapa

- Validar token JWT do Supabase no backend.
- Expor perfil do usuario logado (`/api/auth/me`).
- Expor consulta de motores com modo teaser/full.
- Expor admin basico com validacao server-side.

## Estrutura

```text
backend/
  app/
    core/
    dependencies/
    integrations/
    routers/
    schemas/
    services/
    main.py
  .env.example
  requirements.txt
```

## Rodar localmente

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Variaveis

Obrigatorias:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

Opcional para admin:
- `SUPABASE_SERVICE_ROLE_KEY`

Sem `SUPABASE_SERVICE_ROLE_KEY`, endpoints de admin retornam `503` com mensagem explicita.

Para cadastro com Gemini:
- `GEMINI_API_KEY` (obrigatoria para OCR/IA)
- `GEMINI_MODEL` (opcional, default `gemini-2.5-flash`)
- `SUPABASE_MOTORES_BUCKET` (default `motores-imagens`)
- `CADASTRO_MAX_FILES` (default `5`)
- `CADASTRO_MAX_FILE_SIZE_MB` (default `12`)
- `CADASTRO_MAX_TOTAL_SIZE_MB` (default `40`)

## Endpoints MVP

- `GET /api/health`
- `GET /api/auth/me`
- `GET /api/motors`
- `GET /api/motors/{motor_id}`
- `POST /api/cadastro/analyze` (multipart upload + Gemini)
- `POST /api/cadastro/save` (salva motor no Supabase)
- `GET /api/admin/users/search?q=...`
- `GET /api/admin/users/{user_id}`
- `PATCH /api/admin/users/{user_id}`
- `GET /api/admin/cadastro-access`
- `POST /api/admin/cadastro-access/{user_id}`
- `DELETE /api/admin/cadastro-access/{user_id}`

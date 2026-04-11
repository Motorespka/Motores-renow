# Frontend (Next.js)

Interface web para substituir gradualmente o Streamlit.

## Objetivo desta etapa (MVP)

- Login via Supabase Auth.
- Dashboard autenticado.
- Consulta de motores.
- Detalhe de motor.
- Cadastro tecnico (upload + revisao + salvar).
- Painel admin basico.

## Rodar localmente

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

## Variaveis obrigatorias

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_BASE_URL` (ex.: `http://localhost:8000/api`)

## Rotas

- `/login`
- `/dashboard`
- `/motors`
- `/motors/[id]`
- `/cadastro`
- `/admin`

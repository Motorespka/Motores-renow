# FASE 2 - Base Paralela Criada

## Estrutura nova adicionada (sem quebrar Streamlit)

```text
backend/
  app/
    core/config.py
    dependencies/auth.py
    integrations/supabase_rest.py
    routers/{health,auth,motors,cadastro,admin}.py
    schemas/{access,motor,cadastro,admin}.py
    services/{access_service,motor_service,cadastro_service,admin_service}.py
    main.py
  .env.example
  requirements.txt

frontend/
  src/app/{login,dashboard,motors,motors/[id],cadastro,admin}
  src/components/app-shell.tsx
  src/lib/{supabase,api,auth,types}.ts
  src/app/globals.css
  src/app/manifest.ts
  public/icon.svg
  .env.example
  package.json
```

## Fluxo atual de migracao

- Streamlit continua operacional (`App.py`) como producao atual.
- Backend FastAPI roda em paralelo para servir o novo frontend.
- Frontend Next.js roda em paralelo consumindo backend + Supabase Auth.

## MVP funcional entregue nesta fase

- Login fora do Streamlit (Supabase Auth no frontend).
- Protecao de rotas no frontend.
- Endpoint de identidade (`/api/auth/me`) no backend.
- Consulta de motores (`/api/motors`) com modo `teaser` vs `full`.
- Detalhe tecnico (`/api/motors/{id}`) protegido por plano.
- Admin basico (`/api/admin/...`) para busca e update de usuario.
- Cadastro tecnico inicial fora do Streamlit:
  - `POST /api/cadastro/analyze` (upload + Gemini no backend)
  - `POST /api/cadastro/save` (persistencia no Supabase)
  - Tela `/cadastro` no frontend Next.js

## O que ainda depende do Streamlit

- Fluxo de cadastro legado com UX mais detalhada e formulario completo.
- Fluxo completo de diagnostico e aplicacao de snapshot.
- Edicao tecnica completa de motores na UI atual.
- Parte da camada de cache ligada a `st.cache_data` em servicos legados.

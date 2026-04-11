# Status da Migracao (Atual)

## Migrado para nova arquitetura

- Base backend FastAPI em `backend/`
  - `GET /api/auth/me`
  - `GET /api/motors`
  - `GET /api/motors/{id}`
  - `POST /api/cadastro/analyze`
  - `POST /api/cadastro/save`
  - Admin basico em `GET/PATCH /api/admin/users...` e `cadastro_access`
  - `auth/me` agora retorna `display_name`, `username` e `nome`
  - `auth/me` agora retorna `cadastro_allowed`
- Base frontend Next.js em `frontend/`
  - login
  - dashboard
  - consulta
  - detalhe
  - cadastro
  - admin
  - exibicao de "Logado como: <display_name>"
- Documentacao de auditoria, seguranca e execucao local em `docs/`

## Ainda no Streamlit (por enquanto)

- Cadastro ainda mais completo da versao legada (campos e UX detalhados)
- Diagnostico completo com aplicacao de snapshot
- Edicao tecnica completa de motor
- Fluxos legados com cache `st.cache_*` e estado via `st.session_state`

## Criterio de nao quebra

- Nenhum arquivo critico do fluxo Streamlit foi removido.
- A nova arquitetura foi criada em paralelo.
- Banco Supabase mantido.
- Mudancas reversiveis (basta parar de usar `backend/` e `frontend/`).

## Validacao executada

- Compilacao Python backend: `OK 24 backend python files compiled`
- Compilacao Python projeto inteiro: `OK 78 project python files compiled`

## Limites do ambiente desta execucao

- `git` CLI indisponivel neste terminal (nao foi possivel criar branch/commit por comando local).
- `node`/`npm` indisponiveis neste terminal (frontend nao foi buildado/executado aqui).

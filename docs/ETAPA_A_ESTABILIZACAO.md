# ETAPA A - Estabilizacao do MVP

## Ajustes executados

- Alinhado contrato de `auth/me`:
  - adicionados `display_name`, `username`, `nome`, `cadastro_allowed`
- Permissao de cadastro no backend:
  - nova dependencia `require_cadastro`
  - regra de acesso calculada no backend (admin/pago/liberacao manual)
- Hardening no backend:
  - sanitizacao de busca em PostgREST (`or=ilike`)
  - erro explicito em admin quando `SUPABASE_SERVICE_ROLE_KEY` nao esta configurada
  - ajuste de header para usar service role corretamente quando habilitado
- Hardening no frontend:
  - `ApiRequestError` para exibir erros reais de API
  - fluxo de `signUp` sem redirect indevido quando nao ha sessao imediata
  - menu lateral com estado ativo consistente

## Coerencia local

- Backend Python compila sem erro.
- Testes Python (`ai_board/tests`) passando.
- Healthcheck FastAPI (`/api/health`) retornando `200`.
- Frontend com `npm install` executado e build do Next validado no ambiente local.

## Arquivos de ambiente

- Backend: `backend/.env.example`
- Frontend: `frontend/.env.example`

## Como executar

<<<<<<< Updated upstream
- Guia completo:
  - [docs/COMO_RODAR_MIGRACAO_LOCAL.md](c:\Users\micke\Documents\GitHub\Uniao-motor\docs\COMO_RODAR_MIGRACAO_LOCAL.md)
=======
- Guia completo: `docs/COMO_RODAR_MIGRACAO_LOCAL.md`
>>>>>>> Stashed changes

## Tarefas (ordem atual)

- Configurar `backend/.env` com `SUPABASE_URL` e `SUPABASE_ANON_KEY`.
- Configurar `frontend/.env.local` com `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api`.
- Subir backend FastAPI.
- Subir frontend Next.js.
- Integracao final com repositorio Lovable: `git@github.com:Motorespka/motor-nova-vision.git`.

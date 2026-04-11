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
- Projeto Python inteiro compila sem erro.
- Frontend preparado, mas build nao executado neste terminal por ausencia de `node/npm`.

## Arquivos de ambiente

- Backend:
  - [backend/.env.example](c:\Users\micke\Documents\GitHub\Uniao-motor\backend\.env.example)
- Frontend:
  - [frontend/.env.example](c:\Users\micke\Documents\GitHub\Uniao-motor\frontend\.env.example)

## Como executar

- Guia completo:
  - [docs/COMO_RODAR_MIGRACAO_LOCAL.md](c:\Users\micke\Documents\GitHub\Uniao-motor\docs\COMO_RODAR_MIGRACAO_LOCAL.md)

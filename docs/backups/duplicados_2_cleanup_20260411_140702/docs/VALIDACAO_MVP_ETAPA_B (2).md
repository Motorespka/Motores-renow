# Validacao Funcional do MVP (Etapa B)

## Escopo validado

- login
- auth/me
- protecao de rotas
- dashboard
- listagem de motores
- detalhe do motor
- admin basico

## 1) Login

- Funcional:
  - Tela Next em `/login`.
  - `signInWithPassword` no Supabase.
  - `signUp` com `username` e `nome` em metadata.
- Incompleto/mock:
  - Nao ha fluxo custom de reset de senha nesta etapa.
- Corrigido:
  - Ajustado fluxo de cadastro para nao forcar redirect quando `signUp` nao retorna sessao (confirmacao por email).
- Como testar:
  1. Abrir `/login`.
  2. Entrar com usuario valido.
  3. Confirmar redirecionamento para `/dashboard`.

## 2) auth/me

- Funcional:
  - Endpoint `GET /api/auth/me` validando token no backend.
  - Retorna `role`, `plan`, `ativo`, `is_admin`, `tier`, `cadastro_allowed`.
  - Retorna `display_name`, `username`, `nome`.
- Incompleto/mock:
  - Nenhum mock nesta rota.
- Corrigido:
  - Inclusao de `display_name` e `cadastro_allowed`.
  - Tier agora pode retornar `cadastro`.
- Como testar:
  1. Logar no frontend.
  2. Abrir `/dashboard`.
  3. Verificar nome exibido em "Logado como".

## 3) Protecao de rotas

- Funcional:
  - Cliente: redireciona para `/login` sem sessao.
  - Backend: valida Bearer JWT em endpoints sensiveis.
  - Admin: `require_admin`.
  - Cadastro: `require_cadastro`.
- Incompleto/mock:
  - Nao existe middleware global no frontend; protecao esta por pagina.
- Corrigido:
  - Nova dependencia backend `require_cadastro`.
- Como testar:
  1. Deslogar e acessar `/dashboard`, `/motors`, `/admin`, `/cadastro`.
  2. Confirmar redirecionamento para `/login`.

## 4) Dashboard

- Funcional:
  - Carrega `auth/me`.
  - Mostra plano/tier e atalhos.
- Incompleto/mock:
  - KPIs ainda simples.
- Corrigido:
  - Atalho para cadastro quando `cadastro_allowed=true`.
- Como testar:
  1. Login.
  2. Abrir `/dashboard`.
  3. Confirmar dados do perfil.

## 5) Listagem de motores

- Funcional:
  - `GET /api/motors` com busca.
  - Modo `teaser` para free.
  - Modo `full` para pago/admin.
- Incompleto/mock:
  - Nao ha paginacao visual completa na UI nesta etapa.
- Corrigido:
  - Sanitizacao de busca no backend para PostgREST `or=ilike`.
- Como testar:
  1. Abrir `/motors`.
  2. Buscar por marca/modelo.
  3. Conferir teaser/full conforme plano.

## 6) Detalhe do motor

- Funcional:
  - `GET /api/motors/{id}`.
  - Bloqueio para quem nao e pago/admin (403).
- Incompleto/mock:
  - Visual ainda basico (JSON tecnico bruto).
- Corrigido:
  - Tratamento de erro de API mais claro no frontend (`ApiRequestError`).
- Como testar:
  1. Em conta paga/admin, abrir detalhe na lista.
  2. Em conta free, tentar acesso e conferir bloqueio.

## 7) Admin basico

- Funcional:
  - Busca de usuarios.
  - Edicao de `username`, `nome`, `role`, `plan`, `ativo`.
  - Leitura/alteracao de `cadastro_access` via API.
- Incompleto/mock:
  - Sem trilha de auditoria em tabela dedicada nesta etapa.
- Corrigido:
  - Backend retorna `503` explicito quando faltar `SUPABASE_SERVICE_ROLE_KEY`.
- Como testar:
  1. Logar como admin.
  2. Abrir `/admin`.
  3. Buscar usuario e salvar alteracoes.


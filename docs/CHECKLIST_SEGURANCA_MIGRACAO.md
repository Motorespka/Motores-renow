# Checklist de Seguranca - Migracao FastAPI + Next.js

## Auth e sessao

- [x] Frontend usa apenas `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- [x] Backend valida token JWT via `GET /auth/v1/user`.
- [x] Endpoints sensiveis exigem Bearer token no backend.
- [x] Cadastro exige permissao backend (`require_cadastro`), nao so UI.
- [ ] Adicionar middleware global de sessao no frontend para UX mais previsivel.

## Autorizacao

- [x] Admin exige verificacao no backend (`require_admin`).
- [x] Plano pago exigido no detalhe tecnico (`motors/{id}`).
- [x] Regras comerciais mantidas (`admin`, `paid`, `cadastro`, `teaser`).
- [ ] Revisar e endurecer RLS de `usuarios_app`, `motores`, `cadastro_access`.

## Segredos e chaves

- [x] `SUPABASE_SERVICE_ROLE_KEY` somente no backend.
- [x] `GEMINI_API_KEY` somente no backend.
- [x] Nenhum segredo backend em `NEXT_PUBLIC_*`.
- [ ] Rotacionar chaves antigas em caso de suspeita de exposicao.

## Entrada e validacao

- [x] Payload admin validado por schema.
- [x] Update admin com allowlist de campos.
- [x] Validacao backend de upload (quantidade, tamanho por arquivo, tamanho total, tipo imagem).
- [ ] Adicionar validacoes extras de formato para `username` e campos de cadastro.

## Upload / OCR / Gemini

- [x] Upload migrado para endpoint backend (`/api/cadastro/analyze`).
- [x] OCR/IA com Gemini executado no backend.
- [x] Retorno de erro/sucesso claro para frontend.
- [ ] Adicionar rate limit para proteger custo e abuso.
- [ ] Adicionar varredura antimalware (quando escalar ambiente).

## Ameacas especificas

- IDOR:
  - [x] Endpoints exigem token.
  - [ ] Confirmar policies RLS finais por tabela.
- Mass assignment:
  - [x] Update admin restrito por campos permitidos.
- Privilege escalation:
  - [x] Permissao de admin e cadastro decidida no backend.
- SQL injection:
  - [x] Sem SQL raw concatenado no backend novo (uso PostgREST + filtros controlados).

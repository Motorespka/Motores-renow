# Deploy SaaS — Gêmeo Digital (Render / Railway / Docker)

## Visão geral

| Camada | Função |
|--------|--------|
| `config/settings.py` | Credenciais via `.env` por ambiente (`APP_ENV`) |
| `saas/` | Multi-tenant: usuários, acessos, histórico de cálculos |
| `saas/auth_guard.py` | Login (`streamlit-authenticator`) ou Supabase + plano pago |
| `core/logging_config.py` | Loguru — app, erros e auditoria JSON |
| `Dockerfile` | Multi-stage + `libheif` para HEIC |
| `docker-compose.yml` | App + PostgreSQL |

## 1. Configurar ambiente

```bash
cp .env.example .env
cp config/auth_credentials.yaml.example config/auth_credentials.yaml
```

Edite `.env`:

- **development** — SQLite local (`DATABASE_URL=sqlite:///data/saas.db`)
- **staging / production** — PostgreSQL e `LOG_JSON=true`

Chaves Gemini **somente** em variáveis (`GEMINI_API_KEY`, `GEMINI_API_KEY_1`, …). Nunca no Git.

Para auth local sem Supabase:

```env
SAAS_STREAMLIT_AUTH_ENABLED=true
```

Gere senha bcrypt e cole em `config/auth_credentials.yaml`.

## 2. Subir com Docker (recomendado para validar)

```bash
docker compose up --build
```

Acesse: http://localhost:8501

## 3. Deploy no Render

1. **New → Web Service** — conecte o repositório `Motores-renow`.
2. **Runtime**: Docker (use o `Dockerfile` na raiz).
3. **Environment variables** (Dashboard → Environment):
   - `APP_ENV=production`
   - `DATABASE_URL` — use **Render PostgreSQL** (Internal URL):  
     `postgresql+psycopg2://user:pass@host:5432/dbname`
   - `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`
   - `SAAS_STREAMLIT_AUTH_ENABLED=true` (ou Supabase apenas com `false`)
   - `AUTH_COOKIE_KEY` — string aleatória longa
   - `LOG_JSON=true`
4. **Disk** (opcional): monte `/app/logs` e `/app/data` se precisar persistir SQLite; com Postgres use só o banco gerenciado.
5. **Health check path**: `/_stcore/health`
6. Porta interna: **8501**

Render injeta `PORT`; se necessário, ajuste o CMD:

```dockerfile
CMD streamlit run App.py --server.port=${PORT:-8501} --server.headless=true
```

## 4. Deploy no Railway

1. **New Project → Deploy from GitHub**.
2. Adicione plugin **PostgreSQL**; copie `DATABASE_URL` para variáveis do serviço (prefixo `postgresql://` → troque driver para `postgresql+psycopg2://` se usar psycopg2).
3. Defina as mesmas variáveis do `.env.example`.
4. Railway detecta `Dockerfile` automaticamente.
5. Domínio público na aba **Networking**; porta 8501 exposta pelo container.

## 5. Observabilidade

Logs em `logs/`:

| Arquivo | Conteúdo |
|---------|----------|
| `app_YYYY-MM-DD.log` | Operação geral |
| `errors_YYYY-MM-DD.log` | Erros críticos |
| `audit_YYYY-MM-DD.jsonl` | Cálculos (quando `LOG_JSON=true`) |

Tabela `historico_calculos` no Postgres/SQLite: quem calculou, modo, entrada/resumo JSON.

## 6. Monetização (próximos passos)

- Campo `plano_assinatura` em `tenant_users` (`free`, `pro`, `enterprise`)
- Integrar Stripe webhooks para atualizar `update_user_plan()`
- Manter Supabase como auth principal; `SAAS_STREAMLIT_AUTH_ENABLED` só para piloto/Docker

## 7. Checklist produção

- [ ] `.env` e `auth_credentials.yaml` fora do Git
- [ ] `AUTH_COOKIE_KEY` único por ambiente
- [ ] Postgres com backup automático (Render/Railway)
- [ ] Rate limit / quota Gemini por plano
- [ ] HTTPS no domínio (Render/Railway fornecem TLS)

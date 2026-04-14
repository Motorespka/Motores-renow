# Modulo Isolado - Mapeamento e Guia

## 1) Mapeamento da arquitetura atual (antes da implementacao)

- Entrada principal: `App.py`
- Navegacao/rotas: `core/navigation.py`
- Sessao/rota atual: `core/session_manager.py`
- Autenticacao/login: `auth/login.py`
- Controle de acesso (planos/admin/cadastro): `core/access_control.py`
- Paginas principais:
  - `page/cadastro.py`
  - `page/consulta.py`
  - `page/diagnostico.py`
  - `page/admin_panel.py`
  - `page/atualizacoes.py`
- Dados (cache/fetch): `services/supabase_data.py`
- Runtime local dev/fallback: `services/database.py`
- Parser/normalizacao tecnica: `services/oficina_parser.py`
- Enriquecimento tecnico operacional: `services/oficina_runtime.py`

## 2) Pontos de integracao escolhidos (sem quebrar v200)

- Flags centralizadas: `core/feature_flags.py`
- Controle de development por sessao: `core/development_mode.py`
- Nova rota isolada do modulo: `Route.HUB_COMERCIAL` em `core/navigation.py`
- Nova tela do modulo: `page/hub_comercial.py`
- Servico isolado do modulo comercial: `services/modulo_comercial.py`
- Laudo profissional aditivo:
  - Modelo/formatadores: `services/laudo_pro.py`
  - Renderer visual: `components/laudo_pro.py`
  - Integracao aditiva no diagnostico: `page/diagnostico.py`

## 3) Feature flags (base)

Lidas de `st.secrets` ou variavel de ambiente:

- `ENABLE_DEV_ENV`
- `ENABLE_DEV_BANNER`
- `ENABLE_LAUDO_PRO`
- `ENABLE_WHATSAPP_SEND`
- `ENABLE_CLASSIFICADOS`
- `ENABLE_EMPRESAS`
- `ENABLE_VAGAS`
- `ENABLE_FORNECEDORES`

No admin, em **Development**, ha override apenas para a sessao atual (nao altera producao permanentemente).

## 4) Como entrar/sair do development

1. Abrir **Admin > Development**
2. Clicar em **Abrir ambiente de teste**
3. O banner `MODO DEVELOPMENT / AMBIENTE DE TESTE` aparece no topo
4. Para sair, clicar em **Sair do development**

## 5) Isolamento de dados do novo modulo

- Em development, o modulo comercial usa modo isolado local da sessao (`CommercialModuleStore` em fallback local).
- Isso evita impacto direto no fluxo principal de cadastro/consulta/diagnostico.
- Se tabelas dedicadas existirem no Supabase, o modulo suporta persistencia remota sem alterar tabelas centrais de motores.

## 6) Termos e avisos implementados

No Hub Comercial:

- "Os anuncios sao publicados pelos proprios usuarios."
- "Voce sera direcionado para contato externo."
- "A plataforma nao participa da contratacao."
- "Indicadores baseados em atividade na plataforma, nao representando certificacao."
- "O numero informado para envio via WhatsApp nao sera armazenado."

Aceite registrado com:

- `user_id`
- `versao`
- `contexto`
- `data/hora`
- `ip` (quando disponivel em headers)

## 7) Backup pre-alteracao

Snapshot criado em:

- `docs/backups/dev_module_20260411_135030`


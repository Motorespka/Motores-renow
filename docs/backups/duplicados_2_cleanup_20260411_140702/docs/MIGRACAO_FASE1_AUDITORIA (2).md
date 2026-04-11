# FASE 1 — Auditoria e Plano de Migracao (Streamlit -> FastAPI + Next.js)

## Escopo auditado

- Arquivos analisados: 73
- Diretorios principais:
  - `page/`, `core/`, `auth/` (camada Streamlit e navegação)
  - `services/` (regras tecnicas, parser, integracoes, dados)
  - `assets/` (tema visual)
  - `docs/` (regras comerciais já criadas)

## 1) Mapa da estrutura atual por camada

### Interface Streamlit (camada temporaria)

- Entrada e roteamento:
  - `App.py`
  - `core/navigation.py`
  - `core/session_manager.py`
- Páginas:
  - `page/cadastro.py`
  - `page/consulta.py`
  - `page/motor_detail.py`
  - `page/diagnostico.py`
  - `page/edit.py`
  - `page/admin_panel.py`
- UI utilitaria:
  - `components/*`
  - `ui/*`
  - `assets/style.css`

### Regras de negocio (alto reaproveitamento)

- Normalizacao/contrato tecnico:
  - `services/oficina_parser.py`
- Enriquecimento tecnico/diagnostico/aprendizado:
  - `services/oficina_runtime.py`
  - `services/diagnostico_ia.py`
  - `services/engenharia_ia.py`
  - `services/fabrica_motor.py`
  - `services/engenharia_motor.py`
  - `core/calculadora.py`

### Integracoes com Supabase (hoje acopladas ao Streamlit)

- Acesso a dados com cache Streamlit:
  - `services/supabase_data.py`
- Auth + sincronizacao de perfil:
  - `auth/login.py`
  - `core/access_control.py`
- Upload em storage e writes:
  - `page/cadastro.py`
  - `page/edit.py`
  - `page/diagnostico.py`
  - `page/admin_panel.py`

### Autenticacao e permissao

- Fonte principal de acesso:
  - tabela `usuarios_app` (`role`, `plan`, `ativo`)
- Regras atuais:
  - admin: `role in {'admin','owner','superadmin','root'} + ativo=true`
  - pago: `plan in {'paid','pro','premium','enterprise','business'}`
  - cadastro: admin OU plano pago OU liberacao manual em `cadastro_access`
- Implementacao atual:
  - `core/access_control.py`

### Upload/OCR/Diagnostico/Consulta

- Upload e leitura Gemini:
  - `page/cadastro.py`
  - `services/gemini_oficina.py`
- OCR legado:
  - `services/ocr_motor.py` (easyocr/cv2)
- Consulta:
  - `page/consulta.py`
  - `services/supabase_data.py`
- Diagnostico:
  - `page/diagnostico.py`
  - `services/oficina_runtime.py`

## 2) O que pode ser reaproveitado

- Regras tecnicas puras (alto valor):
  - `services/oficina_parser.py`
  - `services/oficina_runtime.py` (com pequeno desacoplamento de trechos com `streamlit`)
  - `services/diagnostico_ia.py`, `services/engenharia_ia.py`, `services/fabrica_motor.py`
  - `core/calculadora.py`
- Estrategia de acesso comercial já definida:
  - papeis/plano em `usuarios_app`
  - tabela de excecao `cadastro_access`
- Modelo de dados atual (sem refatorar banco imediatamente):
  - `usuarios_app`, `motores`, `ordens_servico`, `vw_consulta_motores`

## 3) O que esta preso ao Streamlit e precisa recriacao

- Navegacao e estado de sessao via `st.session_state`
- `st.cache_data` / `st.cache_resource` como mecanismo de cache
- Formularios e workflow de telas
- Painel admin em UI Streamlit
- Mensagens e controles de permissao renderizados por `st.*`

## 4) Riscos tecnicos e de seguranca identificados

- Alto uso de `except Exception: pass` em fluxos sensiveis (baixa observabilidade de erro).
- `services/oficina_runtime.py` mistura regra de negocio com leitura de secrets e acesso direto ao Supabase (acoplamento).
- Persistencia local em JSON (`db/historico_motores.json`, `db_aprendizado.json`) sem controle transacional.
- Endpoint admin hoje depende de regras da tabela e pode sofrer com RLS mal definida.
- Necessidade de garantir que:
  - frontend nunca veja `service_role`
  - validacao de permissao admin ocorra no backend
  - inputs de update admin sejam validados (evitar mass assignment)
- Auth/session ja teve comportamento de troca entre clientes antes da correcao recente; requer testes regressivos apos migração.

## 5) Plano objetivo de migracao por modulos

## Fase A (MVP paralelo sem quebrar Streamlit)

1. Criar `backend/` FastAPI:
   - rotas: `auth`, `motors`, `admin`
   - validacao com Pydantic
   - integracao Supabase via REST (anon + bearer do usuario)
   - admin via `service_role` no backend (opcional, nunca no frontend)
2. Criar `frontend/` Next.js:
   - login, dashboard, consulta, detalhe, admin
   - protecao de rota cliente + backend autoritativo
3. Manter Streamlit ativo em paralelo.

## Fase B (migracao de fluxos tecnicos)

1. Migrar cadastro (upload + Gemini + salvar motor).
2. Migrar diagnostico.
3. Migrar gerenciamento de permissoes/admin completo.

## Fase C (hardening + custo baixo)

1. Checklist de seguranca (RLS, permissao por endpoint, validacoes).
2. Deploy barato:
   - frontend: Vercel free
   - backend: Render/Fly/Railway (menor custo viavel)
   - Supabase mantido
3. Preparar PWA.

## 6) Decisoes de compatibilidade

- Nao apagar nada do banco atual.
- Nao alterar schema existente na primeira entrega.
- Qualquer nova tabela/migracao deve ser aditiva e reversivel.
- Streamlit permanece operando durante a transicao.

## 7) Entregavel imediato apos esta fase

- Documento de auditoria concluido.
- Proxima etapa: scaffold real de `backend/` e `frontend/` com MVP funcional (auth + consulta + detalhe + admin basico), sem tocar destrutivamente na base atual.


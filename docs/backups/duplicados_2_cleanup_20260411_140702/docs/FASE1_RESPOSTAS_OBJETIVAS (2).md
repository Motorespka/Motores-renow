# Fase 1 - Respostas Objetivas

## 1) O que foi reaproveitado do Streamlit

- Regras de negocio e parser tecnico:
  - `services/oficina_parser.py`
  - `services/oficina_runtime.py` (regras, com desacoplamento progressivo)
  - `services/diagnostico_ia.py`
  - `services/engenharia_ia.py`
  - `services/fabrica_motor.py`
  - `core/calculadora.py`
- Modelo de acesso comercial existente:
  - tabela `usuarios_app` (`role`, `plan`, `ativo`)
  - tabela `cadastro_access` para liberacao manual
- Estrategia de consulta por tabelas/views ja existentes (`vw_consulta_motores`, `motores`, `vw_motores_para_site`)

## 2) O que precisou ser recriado

- Interface web completa (fora Streamlit) em Next.js:
  - login, dashboard, consulta, detalhe, admin
- Camada de API em FastAPI:
  - auth, motores, admin
- Dependencias de sessao/rota/caching que antes eram `st.session_state` e `st.cache_*`

## 3) Quais riscos de seguranca existiam

- Acoplamento entre regra tecnica e UI/estado Streamlit.
- Muitos `except Exception` genericos, dificultando detectar falhas reais.
- Dependencia forte da UI para parte das regras de acesso (risco de confiar demais no cliente).
- Risco operacional de RLS/policies mal configuradas (inclusive historico de recursao em policy).
- Necessidade de garantir service role somente no backend e jamais no frontend.

## 4) Caminho mais barato para publicar

Opcao inicial de menor custo:
- Frontend Next.js: Vercel (free)
- Backend FastAPI: Render free (ou Fly/Railway no menor plano)
- Banco/Auth: Supabase (plano free no inicio)

Isso permite operar com custo quase zero no comeco e escalar depois.

## 5) Caminho mais seguro para evoluir para app mobile/PWA

- Manter backend API-first (FastAPI + contratos estaveis).
- Manter autorizacao no backend + RLS no Supabase.
- Evoluir frontend Next para PWA (manifest + service worker + cache offline controlado).
- Depois, para mobile nativo/hibrido, reutilizar a mesma API:
  - React Native / Expo consumindo o mesmo backend.
- Evitar logica critica no app cliente (admin/permissoes sempre no backend).

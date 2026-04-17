# CHANGELOG AI

## 2026-04-17 | Cycle 0029
- **Change Description:** Restaurado o fluxo principal do Streamlit para o comportamento pré-Next/FastAPI: removida a home `dashboard` do entrypoint, restaurado o pós-login para `cadastro`/`consulta`, removidos os links externos de migração da sidebar e reajustado o `SessionManager` para iniciar em `cadastro`.
- **Reason:** Recolocar o Streamlit como ambiente principal de desenvolvimento funcional, usando o fluxo legado como base segura antes de portar/refatorar funcionalidades para o site em Vercel.
- **Risk Level:** Baixo-Médio (ajuste de roteamento inicial e sidebar; sem alteração de banco, autenticação ou contratos de dados).
- **Rollback Availability:** Alto (reaplicar a rota `dashboard` no `App.py`, reintroduzir `Route.DASHBOARD`/links externos em `core/navigation.py` e restaurar o default `dashboard` no `core/session_manager.py`).
- **Next Predicted Risk:** Sessões antigas com rota persistida podem tentar abrir caminhos removidos; o fallback para `cadastro` reduz o impacto, mas vale validar manualmente login, cadastro, consulta e diagnóstico no próximo ciclo funcional.

## 2026-04-16 | Cycle 0021
- **Change Description:** Implementada rota `dashboard` (Visão geral) como home pós-login, com página `page/visao_geral.py` (KPIs + atalhos) no estilo `motor-nova-vision` e fallback seguro para Consulta.
- **Reason:** Tornar a experiência mais próxima do dashboard de referência e mais clara para o usuário, sem hard cutover e preservando o legado.
- **Risk Level:** Baixo-Médio (nova rota + ajustes de default route).
- **Rollback Availability:** Alto (remover registro da rota, reverter `SessionManager.bootstrap` e `App.py` para defaults antigos).
- **Next Predicted Risk:** KPIs “—” dependem de endpoints novos; alimentar incrementalmente via FastAPI quando pronto.

## 2026-04-16 | Cycle 0022
- **Change Description:** Next.js: liberado “modo localhost sem senha” quando Supabase não está configurado (session DEV + mocks mínimos de API) e dashboard atualizado para layout premium (KPIs + fila + ações rápidas) no estilo `motor-nova-vision`.
- **Reason:** Permitir validar UI/fluxos no dev sem depender de Supabase/backend, mantendo autenticação real em produção e aproximando visual do sistema novo.
- **Risk Level:** Baixo-Médio (mudança em guard de autenticação no frontend; produção preservada por `SUPABASE_CONFIGURED`).
- **Rollback Availability:** Alto (reverter `frontend/src/lib/auth.ts`, `frontend/src/lib/api.ts`, `frontend/src/app/dashboard/page.tsx` e componentes novos).
- **Next Predicted Risk:** Mocks podem mascarar falhas de integração; ao conectar FastAPI, validar contratos reais (`/auth/me`, `/motors`) e remover/limitar mocks por `NODE_ENV`.

## 2026-04-16 | Cycle 0023
- **Change Description:** Next.js: páginas `/motors`, `/motors/[id]` e `/cadastro` migradas para layout premium (cards, badges, inputs) no estilo `motor-nova-vision`. Adicionado mock DEV para `/motors/:id` e fallback DEV para análise/salvamento no `/cadastro` sem backend.
- **Reason:** Manter consistência visual e permitir validar o fluxo completo no localhost sem dependências externas, preservando contratos e comportamento quando backend/Supabase estiverem conectados.
- **Risk Level:** Baixo-Médio (UI + fallback DEV condicionado a `token === "dev"`; produção permanece igual).
- **Rollback Availability:** Alto (reverter páginas e mocks DEV em `frontend/src/lib/api.ts`).
- **Next Predicted Risk:** Quando FastAPI real entrar, alinhar shapes de resposta (principalmente `MotorDetailResponse`) e remover mock DEV gradualmente para evitar divergência.

## 2026-04-16 | Cycle 0024
- **Change Description:** Next.js: painel `/admin` refatorado para layout premium (busca, resultados, editor) no estilo `motor-nova-vision`. Modo DEV agora retorna usuários mock para `/admin/users/search` e simula PATCH em `/admin/users/:id`.
- **Reason:** Validar e ajustar a UI/UX do admin no localhost sem backend, mantendo o fluxo real intacto quando conectado ao FastAPI.
- **Risk Level:** Baixo-Médio (UI + mocks DEV condicionados a `token === "dev"`).
- **Rollback Availability:** Alto (reverter `frontend/src/app/admin/page.tsx` e mocks DEV em `frontend/src/lib/api.ts`).
- **Next Predicted Risk:** Garantir que a resposta real do backend para `AdminUser` inclua os campos usados; se divergirem, adaptar via mapping sem quebrar UI.

## 2026-04-16 | Cycle 0025
- **Change Description:** Next.js: rota `/` (home) ajustada para loading premium no estilo `motor-nova-vision`, mantendo redirect automático para `/dashboard` (session OK) ou `/login` (sem sessão).
- **Reason:** Consistência visual e UX mais “polida” desde a primeira renderização, sem alterar regras de autenticação/roteamento.
- **Risk Level:** Baixo (UI apenas).
- **Rollback Availability:** Alto (reverter `frontend/src/app/page.tsx`).
- **Next Predicted Risk:** Nenhum significativo; garantir que o loading não bloqueie o redirect em dispositivos lentos.

## 2026-04-16 | Cycle 0026
- **Change Description:** Next.js: adicionadas rotas `/diagnostico`, `/conferencia` e `/settings` com layout premium e placeholders operacionais. Header/activeSection ajustados para títulos corretos. Criado componente `EmptyState` reutilizável.
- **Reason:** Completar o “dashboard navigation” com páginas faltantes, mantendo consistência visual e permitindo validação no localhost antes do backend de diagnóstico/conferência entrar.
- **Risk Level:** Baixo-Médio (novas páginas + UI; sem alterar contratos do backend).
- **Rollback Availability:** Alto (remover novas páginas e reverter `AppShell`/`CyberHeader`).
- **Next Predicted Risk:** Ao implementar backend real de diagnóstico/conferência, definir contratos claros (ex.: endpoints e shape) para substituir placeholders sem retrabalho visual.

## 2026-04-16 | Cycle 0027
- **Change Description:** Next.js: `apiFetch` ganhou fallback automático de mocks no localhost quando o backend estiver offline (erro de rede), mantendo as páginas funcionais mesmo sem Supabase/FastAPI.
- **Reason:** Garantir que você consiga validar UI e fluxo completo em dev mesmo se a infra externa não estiver acessível.
- **Risk Level:** Baixo (fallback só ativa em `localhost/127.0.0.1` e somente em falha de rede).
- **Rollback Availability:** Alto (reverter `frontend/src/lib/api.ts`).
- **Next Predicted Risk:** Evitar mascarar erros de API reais; por isso o fallback não dispara em respostas HTTP 4xx/5xx, apenas em erro de rede no localhost.

## 2026-04-16 | Cycle 0028
- **Change Description:** Documentado deploy seguro no Streamlit Cloud com Streamlit como entrypoint principal e links opcionais para Next/FastAPI (`DEPLOY_STREAMLIT_CLOUD.md`).
- **Reason:** Facilitar subir no “site principal” sem acoplamento e com rollback simples.
- **Risk Level:** Baixo (docs apenas).
- **Rollback Availability:** N/A (documentação).
- **Next Predicted Risk:** Deploy do Next/FastAPI em hosts separados exigirá configuração de CORS e URLs públicas; manter `NEXTJS_URL`/`FASTAPI_URL` alinhados.

## 2026-04-16 | Cycle 0020
- **Change Description:** “Limpeza” visual para aproximar do `motor-nova-vision`: reduzidos efeitos de grid/scanline/glow, cards mais sóbrios e consistentes, sidebar buttons com aparência de itens de navegação e mais espaçamento no conteúdo.
- **Reason:** Melhorar legibilidade e hierarquia visual (menos confusão) mantendo a identidade cyber-industrial e preservando 100% das funcionalidades do site.
- **Risk Level:** Baixo (CSS + rótulos na navegação).
- **Rollback Availability:** Alto (reverter `assets/style.css`, `core/navigation.py` e este registro).
- **Next Predicted Risk:** Ajustes de CSS podem exigir pequenos refinamentos por tela; manter iteração incremental com validação nas rotas críticas.

## 2026-04-16 | Cycle 0019
- **Change Description:** Header por rota refinado para ficar mais próximo do `motor-nova-vision`: tag/badge no hero (OCR/PRO/ADMIN/etc) e barra de busca global com borda+glow e tipografia no padrão cyber.
- **Reason:** Aumentar fidelidade visual do shell Streamlit ao novo design, mantendo migração incremental e preservando comportamento das páginas.
- **Risk Level:** Baixo (UI/CSS apenas).
- **Rollback Availability:** Alto (reverter `core/navigation.py`, `assets/style.css` e este registro).
- **Next Predicted Risk:** Seletores CSS baseados em `data-testid` podem variar entre versões do Streamlit; se ocorrer, ajustar seletor para `aria-label`/estrutura real.

## 2026-04-16 | Cycle 0018
- **Change Description:** Adicionado header/hero por rota no Streamlit (título/subtítulo estilo `motor-nova-vision`) + busca global opcional em `st.session_state["_global_search"]`, sem alterar regras de negócio nem páginas legadas.
- **Reason:** Aproximar a experiência do “novo produto” com UI consistente antes do hard cutover, mantendo migração incremental e fallback.
- **Risk Level:** Baixo (UI apenas).
- **Rollback Availability:** Alto (reverter `core/navigation.py`, `App.py`, `assets/style.css` e este registro).
- **Next Predicted Risk:** Alguns pages podem já renderizar seus próprios títulos; caso fique redundante, podemos desativar header por rota específica sem tocar na lógica.

## 2026-04-16 | Cycle 0017
- **Change Description:** Refatorada a sidebar do Streamlit para o estilo “motor-nova-vision” (brand header, workspace card, grupos OPERAÇÃO/ANÁLISE/etc e badges visuais) preservando a navegação e permissões existentes.
- **Reason:** Aproximar a experiência visual do novo produto sem reescrever páginas nem alterar regras de negócio.
- **Risk Level:** Baixo (UI/estilo + estrutura de sidebar).
- **Rollback Availability:** Alto (reverter `core/navigation.py` + `assets/style.css` e este registro).
- **Next Predicted Risk:** Ajustes de CSS em elementos internos do Streamlit podem variar entre versões; manter seletores centrados em `data-testid` e validar após upgrades.

## 2026-04-16 | Cycle 0016
- **Change Description:** Ajuste visual do Streamlit para alinhar com o design system do repositório de referência (`motor-nova-vision`): expansão de tipografia (Orbitron/Rajdhani/Inter/JetBrains Mono) e tokens de glow para consistência.
- **Reason:** Remapear identidade visual do shell Streamlit para a nova linguagem (sem alterar fluxos, permissões, dados ou páginas legadas).
- **Risk Level:** Baixo (apenas CSS/branding).
- **Rollback Availability:** Alto (reverter `assets/style.css` e este registro).
- **Next Predicted Risk:** Mudanças futuras em CSS podem afetar componentes específicos; manter ajustes incrementais e validar telas críticas (login, consulta, cadastro, admin).

## 2026-04-16 | Cycle 0015
- **Change Description:** Corrigida falha de startup do Streamlit no deploy ao transformar `core/` e `page/` em pacotes Python explícitos (`__init__.py`) e garantir o repo root no `sys.path` no início do `App.py`. Removidas dependências do FastAPI do `requirements.txt` do Streamlit e criado `pages/README.md` para preparar migração incremental sem ativar novos pages `.py`.
- **Reason:** Eliminar comportamento instável de namespace packages/colisão de módulos (observado como `KeyError: 'core'`) no Streamlit Cloud, restaurando o entrypoint `App.py` sem hard cutover e separando dependências por domínio.
- **Risk Level:** Baixo (mudança de packaging/import path; sem alterar regras de negócio, login, rotas ou dados).
- **Rollback Availability:** Alto (remover os novos `__init__.py` e reverter o `sys.path` bootstrap no topo do `App.py`; re-adicionar as 3 dependências removidas do `requirements.txt` se necessário).
- **Next Predicted Risk:** `streamlit.components.v1.html` ainda é usado para reset de scroll; ao modernizar o shell, preferir API nativa quando disponível e restringir embed externo a `st.iframe`.

## 2026-04-15 | Cycle 0014
- **Change Description:** Expandido conteúdo-base técnico dos packs transversais (`generic_motor_rules`, `generic_gearmotor_rules`, `rewinding_and_workshop_rules`, `nameplate_reading_rules`, `data_consistency_rules`, `admin_product_ideas`, `legacy_or_unknown_brands`) e padronizado o conteúdo dos 20 packs de marca com estrutura operacional repetível.
- **Reason:** Tornar o assistente interno realmente útil em manutenção, bancada, rebobinagem, validação de cadastro técnico e comparação multimarcas com cautela explícita.
- **Risk Level:** Baixo-Médio (mudança de conteúdo contextual, sem alterar contrato de código do roteador).
- **Rollback Availability:** Alto (reverter commit ou restaurar versões anteriores dos arquivos markdown dos packs).
- **Next Predicted Risk:** Crescimento de contexto pode aumentar tokens por requisição; sugerido próximo ciclo com priorização por relevância e compactação de trechos.

## 2026-04-15 | Cycle 0013
- **Change Description:** Adicionado GPT interno no painel admin com roteador inteligente de contexto (marca/intenção/tipo de produto), prompt-base auditável, packs transversais, 20 packs de marcas e trilha de auditoria segura em `updates/admin_ai_audit.log`.
- **Reason:** Habilitar consultoria técnica multimarcas dentro do admin para manutenção, cadastro, consulta e melhoria de produto sem acoplamento rígido e com governança de incerteza.
- **Risk Level:** Médio (novo fluxo de IA no admin com fallback local e uso opcional de chave secundária).
- **Rollback Availability:** Alto (remover `services/admin_ai_assistant.py`, arquivos novos em `ai_board/` e seção do admin panel).
- **Next Predicted Risk:** Crescimento dos packs sem curadoria pode gerar respostas longas e redundantes; recomendada futura camada de ranking/compactação de contexto.

## 2026-04-13 | Cycle 0011
- **Change Description:** Implementado runtime de 11 papéis com registry explícito de role->env var, loader seguro de credenciais, role prompt files separados, fallback controlado por política e trilha de auditoria segura.
- **Reason:** Garantir separação inegociável entre credencial (API key) e personalidade (role/prompt/skill/governança), habilitando seleção de papel pelo orquestrador com segurança.
- **Risk Level:** Médio (novo módulo integrado por interface; sem alterar fluxos legados).
- **Rollback Availability:** Alto (rollback por remoção do diretório `ai_board/` e restauração deste changelog).
- **Next Predicted Risk:** Integração futura do orchestrator pode ignorar `approval_gate/policy_engine/kill_switch` se não for obrigatória no ponto de chamada.

## 2026-04-13 | Cycle 0012
- **Change Description:** Fortalecido o runtime de papéis com política explícita de fallback aprovado (motivo + falha primária obrigatórios), API de resolução por nome e ponte dedicada para orquestrador (`orchestrator_runtime.py`).
- **Reason:** Corrigir ambiguidade de fallback e preparar integração direta do orchestrator com governança sem acoplamento indevido.
- **Risk Level:** Baixo-Médio (mudança em módulo novo, sem impactos em módulos legados).
- **Rollback Availability:** Alto (reverter commit desta mudança).
- **Next Predicted Risk:** Consumidores podem não fornecer `primary_failure` em fallback; necessário tratar no ponto de integração do orchestrator.

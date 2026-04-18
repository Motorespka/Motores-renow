# CHANGELOG AI

## 2026-04-18 | Cycle 0039
- **Change Description:** Página `diagnostico` aprimorada: filtro de busca (ID/marca/modelo) para selecionar motor com lista grande, botão de recarregar lista (limpa cache), e bypass de gating pago quando em `development mode` para permitir validação do fluxo sem bloquear a tela.
- **Reason:** Melhorar operabilidade do diagnóstico na oficina e reduzir fricção/instabilidade em ambientes de teste.
- **Risk Level:** Baixo.
- **Rollback Availability:** Alto (reverter `page/diagnostico.py` + este registro).
- **Next Predicted Risk:** Se o volume de motores crescer muito, o carregamento “lista inteira” pode ficar pesado; próximo passo seria busca/paginação server-side.

## 2026-04-18 | Cycle 0040
- **Change Description:** Diagnóstico com busca/paginação server-side: novos helpers `fetch_motores_recent_cached` e `fetch_motores_search_cached` em `services/supabase_data.py` e `page/diagnostico.py` passou a usar lista recente (até 200) ou busca no Supabase (até 500) em vez de baixar milhares de linhas.
- **Reason:** Escalar seleção de motor no diagnóstico sem travar a UI em bases grandes e reduzir roundtrips/payload.
- **Risk Level:** Baixo-Médio (query com `or_(...ilike...)` pode variar por view; há fallback de colunas e cadeia de fontes).
- **Rollback Availability:** Alto (voltar para `fetch_motores_cached` + remover helpers).
- **Next Predicted Risk:** Views com colunas divergentes podem rejeitar `or_` com `marca/modelo`; se ocorrer, fixar `SUPABASE_CONSULTA_TABLE` para uma fonte padrão ou restringir a busca para `motores`.

## 2026-04-18 | Cycle 0037
- **Change Description:** Nova camada read-only ``services/motor_rebobinagem`` (normalização passo/espiras/fio/ranhuras/mm, assinatura técnica, validação de coerência, ``analyze_rewinding_coherence``, similaridade futura ``prepare_similarity_query``, serialização FastAPI). UI: linha compacta na consulta + expander em detalhe/cadastro/edição. Testes ``tests/test_motor_rebobinagem.py``.
- **Reason:** Inteligência de rebobinagem de oficina modular, sem persistência nem alteração de fluxos core; aproveita ``motor_inteligencia`` só como contexto elétrico.
- **Risk Level:** Baixo.
- **Rollback Availability:** Alto (remover pacote, componente, imports nas páginas).
- **Next Predicted Risk:** Tabelas AWG/mm² e modelo ranhura×bobina — documentado em ``future_work``.

## 2026-04-18 | Cycle 0036
- **Change Description:** Fase 2 da camada ``motor_inteligencia``: ``batch_review.py`` (relatório read-only agregado), ``serialization.py`` (JSON-safe / FastAPI futuro), refinamento de severidade (insuficiente por dados lacunares vs. crítico só incoerência forte; limiares Pin/slip/corrente mais conservadores), ``summary_one_liner`` + resumo textual melhorado, consulta com linha mínima (badge + frase) sem expander pesado, admin no diagnóstico para relatório em lote + download JSON.
- **Reason:** Validar com dados reais, reduzir falsos positivos e UX leve na consulta, mantendo read-only e sem tocar persistência core.
- **Risk Level:** Baixo.
- **Rollback Availability:** Alto (reverter ficheiros da camada + consulta + diagnostico + componente).
- **Next Predicted Risk:** Amostras muito grandes na UI — já limitadas; cache opcional depois.

## 2026-04-18 | Cycle 0035
- **Change Description:** Nova camada técnica read-only ``services/motor_inteligencia`` (normalização numérica, cálculos ns/slip/Pin/Pout/torque, validação com status ok/alerta/critico/insuficiente, sugestões de cálculos futuros, coerção de linhas Supabase). Componente ``components/motor_inteligencia_panel.py`` com badges verde/amarelo/vermelho/cinza. Integração leve em expanders em ``motor_detail``, ``cadastro``, ``edit``, ``consulta`` e ``diagnostico``. Testes ``tests/test_motor_inteligencia.py`` (unittest).
- **Reason:** Base para inteligência técnica Moto-Renow sem acoplar lógica pesada à UI nem alterar fluxos de persistência/autenticação existentes.
- **Risk Level:** Baixo (código novo + expanders; falhas isoladas em try/except no painel).
- **Rollback Availability:** Alto (remover pacote, componente, imports nas páginas e testes).
- **Next Predicted Risk:** Performance na consulta com muitos cards se todos expandirem a análise; considerar cache por id se necessário.

## 2026-04-18 | Cycle 0034
- **Change Description:** Validação de coerência da bobinagem auxiliar: se existir qualquer dado auxiliar (passos ou fio), exige-se o conjunto completo **passos + fio + espiras**; alertas (`alertas_validacao_projeto`), aviso no detalhe e bloqueio de salvar em cadastro/edição até os três estarem preenchidos (sem sugerir apagar passo).
- **Reason:** Registros monofásicos não podem ficar com passo/fio auxiliar sem espiras, nem com dois dos três — evita dados incompletos na oficina.
- **Risk Level:** Baixo (regra localizada; registros legados incoerentes passam a exigir correção no próximo save).
- **Rollback Availability:** Alto (reverter `core/calculadora.py`, `services/oficina_runtime.py`, `page/cadastro.py`, `page/edit.py`, `page/motor_detail.py`).
- **Next Predicted Risk:** Casos raros de rascunho parcial; o fluxo correto é completar os três campos auxiliares.

## 2026-04-18 | Cycle 0038
- **Change Description:** Adicionada auditoria técnica automática de coerência dos cálculos na página `consulta` (expander “Análise técnica dos cálculos”). A triagem classifica os motores em três grupos: (1) cálculos aparentemente certos/coerentes, (2) faltando dados essenciais, (3) totalmente desnivelados. A validação cruza potência/RPM/tensão/corrente/polos/fase com heurísticas de plausibilidade (incluindo verificação aproximada de corrente esperada por fase e compatibilidade RPM × polos × frequência).
- **Reason:** Atender pedido de análise técnica prática dos cadastros da consulta com retorno objetivo dos motores “ok”, “incompletos” e “desnivelados”.
- **Risk Level:** Baixo-Médio (lógica heurística de diagnóstico pode gerar falso positivo/negativo em casos especiais de aplicação; não altera dados persistidos).
- **Rollback Availability:** Alto (reverter `page/consulta.py` para remover a auditoria).
- **Next Predicted Risk:** Motores especiais (partida, tensão não padrão, aplicação específica) podem exigir regra de exceção; recomendado adicionar tolerâncias por tipo de motor/serviço no próximo ciclo.

## 2026-04-17 | Cycle 0033
- **Change Description:** Reorganizada a experiência Consulta/Detalhes dos motores. Na página `consulta`, os cards passaram a exibir somente informações essenciais para triagem rápida (RPM, potência/cavalaria, corrente, fases/mono-trifásico, polos e resumo de eixo em X/Y). O conteúdo técnico denso (bobinagem, mecânica detalhada, esquema e leitura IA) foi removido da listagem e concentrado na página `motor_detail`, que agora apresenta visão limpa e completa em abas (Visão geral, Rebobinagem, Mecânica, Oficina & IA).
- **Reason:** Atender pedido de reduzir poluição visual na consulta e usar “Abrir detalhes” como tela técnica completa, melhorando fluxo operacional e leitura em desktop/mobile.
- **Risk Level:** Baixo-Médio (mudança de layout e distribuição de informação entre telas; sem alteração de dados persistidos).
- **Rollback Availability:** Alto (reverter `page/consulta.py` e `page/motor_detail.py` ao commit anterior).
- **Next Predicted Risk:** Alguns registros legados podem não preencher todos os campos de mecânica/oficina; manter fallback “-” e, se necessário, adicionar sinalização de completude por registro.

## 2026-04-17 | Cycle 0032
- **Change Description:** Aplicado refinamento mobile-first do shell Streamlit no estilo nova vision: sidebar com áreas de toque maiores, badges mais legíveis e com quebra controlada, estado ativo mais evidente no menu, header compactado em telas pequenas e redução de ruído visual (scanline/grid/glow) no mobile.
- **Reason:** Atender ao pedido de foco em experiência mobile, melhorando legibilidade e usabilidade da navegação no celular sem alterar regras de negócio.
- **Risk Level:** Baixo (ajustes CSS responsivos, sem mudança de fluxo de dados).
- **Rollback Availability:** Alto (reverter `assets/style.css` para o commit anterior).
- **Next Predicted Risk:** Em dispositivos muito antigos, efeitos visuais ainda podem impactar performance; se necessário, criar modo `reduced-motion` explícito para mobile.

## 2026-04-17 | Cycle 0031
- **Change Description:** Restaurada a base visual Streamlit no estilo atual ("nova vision") e aplicada melhoria de UX na navegação: adicionada entrada direta de `Consulta` na sidebar (sem depender de abrir a página `Visão geral` para alcançar a tela de consulta). Também realizado polimento visual leve dos botões de navegação da sidebar (gradiente, borda ativa e hover mais consistente no desktop/mobile).
- **Reason:** Atender pedido de manter o visual atual, melhorar acabamento gráfico e reduzir fricção de navegação para acesso da consulta em 1 clique.
- **Risk Level:** Baixo (mudança concentrada em UI/navegação, sem alterar regras de negócio ou persistência).
- **Rollback Availability:** Alto (reverter `core/navigation.py` e `assets/style.css` ao estado anterior).
- **Next Predicted Risk:** A sidebar pode crescer com muitos atalhos; caso isso aconteça, considerar agrupamento colapsável para manter legibilidade em telas pequenas.

## 2026-04-17 | Cycle 0030
- **Change Description:** Restaurado o visual legado do Streamlit (pré-camada “site novo”) ao reverter `core/navigation.py` e `assets/style.css` para o estado anterior ao commit de integração (`277f9da`). Também corrigido `core/session_manager.py` para remover fallback inválido em `Route.DASHBOARD`, voltando o bootstrap de rota para `Route.CADASTRO`.
- **Reason:** O usuário reportou que o site ainda estava com “cara do Vercel”; era necessário desacoplar não só `App.py`, mas também a camada de navegação/estilo e o fallback de sessão introduzidos no ciclo de integração visual.
- **Risk Level:** Baixo-Médio (mudança visual + correção de fallback de rota no bootstrap de sessão).
- **Rollback Availability:** Alto (reaplicar `core/navigation.py`/`assets/style.css`/`core/session_manager.py` do commit anterior ou reverter este commit).
- **Next Predicted Risk:** Como permanecem arquivos de páginas novos no repositório, futuras mudanças podem reintroduzir elementos visuais “premium”; manter Streamlit legado como baseline explícito para novos ciclos.

## 2026-04-17 | Cycle 0029
- **Change Description:** Restaurado `App.py` para o estado imediatamente anterior ao commit que introduziu shell Streamlit acoplado ao Next/FastAPI (`277f9da`). Removidos os acoplamentos adicionados nesse ciclo (rota `dashboard` no bootstrap do router, `render_route_header` e imports associados), retornando o fluxo padrão de rotas (`cadastro`/`consulta`) do Streamlit legado.
- **Reason:** Atender à estratégia operacional definida para usar o Streamlit como ambiente principal de desenvolvimento funcional, desacoplando o entrypoint das evoluções web (Next/FastAPI) nesta etapa.
- **Risk Level:** Baixo-Médio (alteração do entrypoint principal de navegação; risco de regressão visual em elementos adicionados recentemente ao shell).
- **Rollback Availability:** Alto (reaplicar `App.py` do commit `277f9da` ou reverter este commit).
- **Next Predicted Risk:** A remoção do header por rota no `App.py` pode reduzir consistência visual com estilos recentes; se necessário, reintroduzir apenas camada visual sem recoupling com stack web.

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

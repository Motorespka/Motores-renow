# CHANGELOG AI

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

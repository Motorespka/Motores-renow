# CHANGELOG AI

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

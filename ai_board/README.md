# AI Board Roles Runtime

Camada modular para separar **credencial** de **comportamento de papel**.

## Papéis suportados

- founder
- cto
- security
- qa
- performance
- product
- devops
- data_guardian
- ux
- risk
- advisor

## Variáveis de ambiente obrigatórias

- AI_KEY_FOUNDER
- AI_KEY_CTO
- AI_KEY_SECURITY
- AI_KEY_QA
- AI_KEY_PERFORMANCE
- AI_KEY_PRODUCT
- AI_KEY_DEVOPS
- AI_KEY_DATA_GUARDIAN
- AI_KEY_UX
- AI_KEY_RISK
- AI_KEY_ADVISOR

## Reserva opcional (fallback controlado)

Cada papel aceita opcionalmente `<ENV>_RESERVE`, por exemplo:

- AI_KEY_CTO_RESERVE
- AI_KEY_QA_RESERVE

O fallback não é automático. Ele exige:
- aprovação explícita (`approved=True`),
- motivo (`reason`),
- descrição de falha temporária da chave primária (`primary_failure`).

## Uso direto

```python
from ai_board.role_runtime import get_role_runtime

runtime = get_role_runtime("security")
# runtime.role_prompt -> personalidade/instruções
# runtime.api_key -> credencial em memória
```

## Uso com fallback governado

```python
from ai_board.role_runtime import RuntimeFallback, get_role_runtime

runtime = get_role_runtime(
    "qa",
    fallback=RuntimeFallback(
        approved=True,
        reason="provider_timeout",
        primary_failure="429 timeout from upstream provider",
    ),
)
```

## Integração com orchestrator

```python
from ai_board.orchestrator_runtime import (
    GovernanceHooks,
    OrchestratorSelection,
    get_orchestrator_role_runtime,
)

runtime = get_orchestrator_role_runtime(
    OrchestratorSelection(selected_role="security"),
    hooks=GovernanceHooks(
        approval_gate=my_approval_gate,
        policy_engine=my_policy_engine,
        kill_switch=my_kill_switch,
    ),
)
```

## Governança

`get_role_runtime` e `get_orchestrator_role_runtime` preservam:

- `approval_gate`
- `policy_engine`
- `kill_switch`

Sem aprovação, com policy negada ou kill switch ativo, a execução falha com `GovernanceViolation`.

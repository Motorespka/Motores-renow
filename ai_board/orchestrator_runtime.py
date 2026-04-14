from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ai_board.role_registry import RoleDefinition, get_role_definition
from ai_board.role_runtime import (
    ApprovalGate,
    KillSwitch,
    PolicyEngine,
    RoleRuntime,
    RuntimeFallback,
    get_role_runtime,
)


@dataclass(frozen=True)
class OrchestratorSelection:
    selected_role: str
    fallback: RuntimeFallback | None = None


@dataclass(frozen=True)
class GovernanceHooks:
    approval_gate: ApprovalGate | None = None
    policy_engine: PolicyEngine | None = None
    kill_switch: KillSwitch | None = None


def get_orchestrator_role_runtime(
    selection: OrchestratorSelection,
    *,
    hooks: GovernanceHooks | None = None,
) -> RoleRuntime:
    governance = hooks or GovernanceHooks()
    return get_role_runtime(
        selection.selected_role,
        fallback=selection.fallback,
        approval_gate=governance.approval_gate,
        policy_engine=governance.policy_engine,
        kill_switch=governance.kill_switch,
    )


def role_requires_human_approval(role: str, approval_gate: Callable[[RoleDefinition], bool]) -> bool:
    role_def = get_role_definition(role)
    return role_def.permissions.approval_required and not approval_gate(role_def)

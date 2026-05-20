from __future__ import annotations

import json
import os
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Literal


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact_secrets_in_text(text: str) -> str:
    """Remove padrões de chave Google do texto (logs / mensagens de erro)."""
    t = text or ""
    t = re.sub(r"AIza[0-9A-Za-z\-_]{20,}", "[REDACTED_API_KEY]", t, flags=re.IGNORECASE)
    return t


def mask_key(key: str) -> str:
    k = (key or "").strip()
    if len(k) <= 10:
        return k[:2] + "..." + k[-2:] if k else ""
    return f"{k[:4]}...{k[-4:]}"


def _t(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _parse_bool_env(v: str) -> bool:
    return _t(v).lower() in {"1", "true", "yes", "y", "on"}


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _extract_http_code(message: str) -> Optional[int]:
    m = re.search(r"\b(\d{3})\b", message or "")
    if not m:
        return None
    code = int(m.group(1))
    return code if 100 <= code <= 599 else None


def classify_gemini_exception(exc: BaseException) -> Dict[str, Any]:
    """
    Heurística robusta (sem depender de classes específicas do SDK) para classificar erro.
    """
    msg = (str(exc) or "").strip()
    low = msg.lower()
    http = getattr(exc, "status_code", None)
    http_code = int(http) if isinstance(http, int) else _extract_http_code(msg)

    # Códigos/labels comuns do Gemini
    if "api_key_invalid" in low or "invalid api key" in low or "invalid_argument" in low:
        return {"status": "invalid", "http_code": http_code, "error_code": "API_KEY_INVALID", "error_message": msg[:220]}
    if "permission_denied" in low or (http_code == 403):
        return {
            "status": "permission_denied",
            "http_code": http_code or 403,
            "error_code": "PERMISSION_DENIED",
            "error_message": msg[:220],
        }
    if "resource_exhausted" in low or "quota" in low or (http_code == 429):
        return {
            "status": "quota_exhausted",
            "http_code": http_code or 429,
            "error_code": "RESOURCE_EXHAUSTED",
            "error_message": msg[:220],
        }
    if http_code in {500, 503, 504} or "unavailable" in low:
        return {"status": "unavailable", "http_code": http_code, "error_code": "UNAVAILABLE", "error_message": msg[:220]}

    return {"status": "unknown_error", "http_code": http_code, "error_code": "", "error_message": msg[:220]}


@dataclass
class KeyStatus:
    key_alias: str
    masked_key: str
    status: str = "unknown"
    http_code: Optional[int] = None
    error_code: str = ""
    error_message_resumida: str = ""
    tested_at: str = ""
    last_success_at: str = ""
    last_failure_at: str = ""
    cooldown_until: str = ""
    cooldown_until_epoch: int = 0
    consecutive_failures: int = 0
    total_success: int = 0
    total_failure: int = 0
    total_quota_exhausted: int = 0
    total_invalid: int = 0
    # “Elegível OK” vindo de check/refresh (não deve ser derrubado por unknown_error de parsing)
    eligible_ok: bool = False
    # métricas por execução (reset a cada load_keys/load_keys_from_pairs)
    calls_this_run: int = 0
    success_this_run: int = 0
    quota_this_run: int = 0
    errors_this_run: int = 0
    # uso/erro recente (útil para rotação/diagnóstico)
    last_used_at: str = ""
    last_used_epoch: int = 0
    last_error_status: str = ""
    last_error_message: str = ""


RotationStrategy = Literal["random", "round_robin", "least_recently_used"]


class GeminiKeyManager:
    """
    Gerenciador de chaves Gemini com rotação segura.

    - Não imprime chaves inteiras (usa masked).
    - Evita martelar chave em cooldown (após 429).
    - Backoff exponencial por chave.
    """

    def __init__(
        self,
        *,
        status_path: str,
        model_default: str,
        enabled: bool = True,
        max_attempts_per_image: int = 2,
        cooldown_seconds_default: int = 30 * 60,
        retry_backoff_base_seconds: int = 5,
        retry_backoff_max_seconds: int = 5 * 60,
        per_key_soft_limit_per_run: int = 200,
    ) -> None:
        self.status_path = Path(status_path)
        self.model_default = (model_default or "gemini-2.5-flash").strip()
        self.enabled = enabled
        self.max_attempts_per_image = max(1, int(max_attempts_per_image))
        self.cooldown_seconds_default = max(10, int(cooldown_seconds_default))
        self.retry_backoff_base_seconds = max(1, int(retry_backoff_base_seconds))
        self.retry_backoff_max_seconds = max(self.retry_backoff_base_seconds, int(retry_backoff_max_seconds))
        self.per_key_soft_limit_per_run = max(1, int(per_key_soft_limit_per_run))
        self.rotation_strategy: RotationStrategy = "random"
        self.max_calls_per_key_per_run: int = 0  # 0 = sem limite específico
        self._rr_cursor: int = 0
        self._last_selected_alias: str = ""

        self._keys_by_alias: Dict[str, str] = {}
        self._status: Dict[str, KeyStatus] = {}
        self._used_count_run: Dict[str, int] = {}

        self._load_status_file()

    @staticmethod
    def load_keys_from_env_and_secrets() -> List[Tuple[str, str]]:
        """
        Ordem de leitura:
          1) GEMINI_API_KEYS (csv)
          2) GEMINI_API_KEY_1..10
          3) GEMINI_KEY_01..99 / GEMINI_KEY_1..99 (alias comum em .env)
          4) GEMINI_API_KEY (legado)
          5) st.secrets (GEMINI_API_KEYS ou GEMINI_API_KEY_1..10 ou GEMINI_API_KEY)
        Retorna lista [(alias, key)] com aliases estáveis KEY_1..KEY_N.
        """
        keys: List[str] = []

        env_many = _t(os.environ.get("GEMINI_API_KEYS"))
        if env_many:
            for part in env_many.split(","):
                k = _t(part)
                if k:
                    keys.append(k)

        for i in range(1, 1000):
            k = _t(os.environ.get(f"GEMINI_API_KEY_{i}"))
            if k:
                keys.append(k)

        # GEMINI_KEY_01..99 (zero-padded) e depois 1..999 sem / com padding
        for i in range(1, 100):
            k = _t(os.environ.get(f"GEMINI_KEY_{i:02d}"))
            if k:
                keys.append(k)
        for i in range(1, 1000):
            k = _t(os.environ.get(f"GEMINI_KEY_{i}"))
            if k:
                keys.append(k)

        # compat legado (um único) e chave de teste explícita
        k1 = _t(os.environ.get("GEMINI_API_KEY"))
        if k1:
            keys.append(k1)
        kt = _t(os.environ.get("GEMINI_TEST_KEY"))
        if kt:
            keys.append(kt)

        # streamlit secrets (opcional)
        try:
            import streamlit as st  # type: ignore

            sec = getattr(st, "secrets", None)
            if sec is not None:
                many = sec.get("GEMINI_API_KEYS", None)  # type: ignore[attr-defined]
                if isinstance(many, str):
                    for part in many.split(","):
                        k = _t(part)
                        if k:
                            keys.append(k)
                for i in range(1, 1000):
                    k = sec.get(f"GEMINI_API_KEY_{i}", None)  # type: ignore[attr-defined]
                    if isinstance(k, str) and k.strip():
                        keys.append(k.strip())
                for i in range(1, 100):
                    k = sec.get(f"GEMINI_KEY_{i:02d}", None)  # type: ignore[attr-defined]
                    if isinstance(k, str) and k.strip():
                        keys.append(k.strip())
                for i in range(1, 1000):
                    k = sec.get(f"GEMINI_KEY_{i}", None)  # type: ignore[attr-defined]
                    if isinstance(k, str) and k.strip():
                        keys.append(k.strip())
                k = sec.get("GEMINI_API_KEY", None)  # type: ignore[attr-defined]
                if isinstance(k, str) and k.strip():
                    keys.append(k.strip())
        except Exception:
            pass

        # uniq mantendo ordem
        uniq: List[str] = []
        for k in keys:
            if k not in uniq:
                uniq.append(k)

        out: List[Tuple[str, str]] = []
        for idx, k in enumerate(uniq, start=1):
            out.append((f"KEY_{idx}", k))
        return out

    def load_keys(self) -> int:
        pairs = self.load_keys_from_env_and_secrets()
        self._keys_by_alias = {alias: key for alias, key in pairs}
        for alias, key in pairs:
            self._status.setdefault(alias, KeyStatus(key_alias=alias, masked_key=mask_key(key)))
        for alias in list(self._status.keys()):
            if alias not in self._keys_by_alias:
                # mantém status antigo no arquivo, mas não usa em runtime
                continue
        self._used_count_run = {alias: 0 for alias in self._keys_by_alias.keys()}
        for alias in self._keys_by_alias.keys():
            st = self._status.get(alias)
            if st:
                st.calls_this_run = 0
                st.success_this_run = 0
                st.quota_this_run = 0
                st.errors_this_run = 0
        self._rr_cursor = 0
        self._last_selected_alias = ""
        return len(self._keys_by_alias)

    def load_keys_from_pairs(self, pairs: List[Tuple[str, str]]) -> int:
        """Carrega chaves a partir de [(alias, key), ...] em memória (testes / auditoria)."""
        self._keys_by_alias = {}
        for alias, key in pairs:
            al = _t(alias)
            if not al:
                continue
            self._keys_by_alias[al] = key
        for alias, key in self._keys_by_alias.items():
            self._status.setdefault(alias, KeyStatus(key_alias=alias, masked_key=mask_key(key)))
        self._apply_status_from_masked_key_peers()
        self._used_count_run = {alias: 0 for alias in self._keys_by_alias.keys()}
        for alias in self._keys_by_alias.keys():
            st = self._status.get(alias)
            if st:
                st.calls_this_run = 0
                st.success_this_run = 0
                st.quota_this_run = 0
                st.errors_this_run = 0
        self._rr_cursor = 0
        self._last_selected_alias = ""
        return len(self._keys_by_alias)

    def _apply_status_from_masked_key_peers(self) -> None:
        """
        Copia estado de verificação para o alias em uso quando há outra entrada no JSON
        com o mesmo masked_key (ex.: normalize/check gravam KEY_* e o extract usa UQ_*).
        Sem isto, UQ_* ficam com eligible_ok=false por defeito e get_available_key(require_ok)
        não escolhe nenhuma chave apesar do check mostrar OK.
        """
        peers_by_masked: Dict[str, List[KeyStatus]] = {}
        for st in list(self._status.values()):
            mk = _t(st.masked_key)
            if mk:
                peers_by_masked.setdefault(mk, []).append(st)

        def rank(st: KeyStatus) -> Tuple[int, int, str]:
            return (
                1 if st.eligible_ok else 0,
                1 if st.status == "ok" else 0,
                st.tested_at or "",
            )

        for alias, key in self._keys_by_alias.items():
            mk = mask_key(key)
            pool = peers_by_masked.get(mk, [])
            if not pool:
                continue
            best = max(pool, key=rank)
            tgt = self._status.setdefault(alias, KeyStatus(key_alias=alias, masked_key=mk))
            if best is tgt:
                continue
            tgt.key_alias = alias
            tgt.masked_key = mk
            tgt.eligible_ok = bool(best.eligible_ok)
            tgt.status = best.status
            tgt.http_code = best.http_code
            tgt.error_code = best.error_code
            tgt.error_message_resumida = best.error_message_resumida
            tgt.tested_at = best.tested_at
            tgt.last_success_at = best.last_success_at
            tgt.last_failure_at = best.last_failure_at
            tgt.cooldown_until = best.cooldown_until
            tgt.cooldown_until_epoch = best.cooldown_until_epoch
            tgt.consecutive_failures = best.consecutive_failures
            tgt.total_success = best.total_success
            tgt.total_failure = best.total_failure
            tgt.total_quota_exhausted = best.total_quota_exhausted
            tgt.total_invalid = best.total_invalid
            tgt.last_error_status = best.last_error_status
            tgt.last_error_message = best.last_error_message

    def _load_status_file(self) -> None:
        if not self.status_path.exists():
            return
        try:
            raw = json.loads(self.status_path.read_text(encoding="utf-8"))
        except Exception:
            return
        # check_gemini_keys.py grava "results"; save_status grava "keys"
        items = raw.get("keys") or raw.get("results") or []
        for item in items:
            try:
                ks = KeyStatus(
                    key_alias=_t(item.get("key_alias")),
                    masked_key=_t(item.get("masked_key")),
                    status=_t(item.get("status")) or "unknown",
                    http_code=item.get("http_code"),
                    error_code=_t(item.get("error_code")),
                    error_message_resumida=redact_secrets_in_text(_t(item.get("error_message_resumida"))),
                    tested_at=_t(item.get("tested_at")),
                    last_success_at=_t(item.get("last_success_at")),
                    last_failure_at=_t(item.get("last_failure_at")),
                    cooldown_until=_t(item.get("cooldown_until")),
                    cooldown_until_epoch=_safe_int(item.get("cooldown_until_epoch")),
                    consecutive_failures=_safe_int(item.get("consecutive_failures")),
                    total_success=_safe_int(item.get("total_success")),
                    total_failure=_safe_int(item.get("total_failure")),
                    total_quota_exhausted=_safe_int(item.get("total_quota_exhausted")),
                    total_invalid=_safe_int(item.get("total_invalid")),
                    eligible_ok=bool(item.get("eligible_ok")) if item.get("eligible_ok") is not None else (_t(item.get("status")) == "ok"),
                    # campos novos (compat com JSON antigo)
                    calls_this_run=_safe_int(item.get("calls_this_run")),
                    success_this_run=_safe_int(item.get("success_this_run")),
                    quota_this_run=_safe_int(item.get("quota_this_run")),
                    errors_this_run=_safe_int(item.get("errors_this_run")),
                    last_used_at=_t(item.get("last_used_at")),
                    last_used_epoch=_safe_int(item.get("last_used_epoch")),
                    last_error_status=_t(item.get("last_error_status")),
                    last_error_message=redact_secrets_in_text(_t(item.get("last_error_message"))),
                )
                if ks.key_alias:
                    self._status[ks.key_alias] = ks
            except Exception:
                continue

    def save_status(self) -> None:
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": _utc_now_iso(),
            "model_default": self.model_default,
            "keys": [
                {
                    "key_alias": s.key_alias,
                    "masked_key": s.masked_key,
                    "status": s.status,
                    "http_code": s.http_code,
                    "error_code": s.error_code,
                    "error_message_resumida": s.error_message_resumida,
                    "tested_at": s.tested_at,
                    "last_success_at": s.last_success_at,
                    "last_failure_at": s.last_failure_at,
                    "cooldown_until": s.cooldown_until,
                    "cooldown_until_epoch": s.cooldown_until_epoch,
                    "consecutive_failures": s.consecutive_failures,
                    "total_success": s.total_success,
                    "total_failure": s.total_failure,
                    "total_quota_exhausted": s.total_quota_exhausted,
                    "total_invalid": s.total_invalid,
                    "eligible_ok": bool(s.eligible_ok),
                    "calls_this_run": s.calls_this_run,
                    "success_this_run": s.success_this_run,
                    "quota_this_run": s.quota_this_run,
                    "errors_this_run": s.errors_this_run,
                    "last_used_at": s.last_used_at,
                    "last_used_epoch": s.last_used_epoch,
                    "last_error_status": s.last_error_status,
                    "last_error_message": redact_secrets_in_text(_t(s.last_error_message))[:220],
                }
                for s in sorted(self._status.values(), key=lambda x: x.key_alias)
            ],
        }
        self.status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _is_in_cooldown(self, alias: str) -> bool:
        st = self._status.get(alias)
        if not st:
            return False
        if st.cooldown_until_epoch and int(time.time()) < int(st.cooldown_until_epoch):
            return True
        return False

    def _soft_limit_reached(self, alias: str) -> bool:
        used = self._used_count_run.get(alias, 0)
        if self.max_calls_per_key_per_run and used >= int(self.max_calls_per_key_per_run):
            return True
        return used >= self.per_key_soft_limit_per_run

    def configure_rotation(self, *, strategy: str = "", max_calls_per_key_per_run: int = 0) -> None:
        st = _t(strategy).lower()
        if st in {"round_robin", "rr"}:
            self.rotation_strategy = "round_robin"
        elif st in {"least_recently_used", "lru"}:
            self.rotation_strategy = "least_recently_used"
        elif st in {"random", ""}:
            self.rotation_strategy = "random"
        else:
            self.rotation_strategy = "random"
        self.max_calls_per_key_per_run = max(0, int(max_calls_per_key_per_run or 0))

    def explain_no_keys(self, *, require_status_ok: bool) -> Dict[str, Any]:
        """
        Explica por que não há chave disponível *neste momento*.
        Não expõe chaves, só contagens/razão.
        """
        if not self._keys_by_alias:
            return {"reason": "no_keys_loaded", "counts": {"total_loaded": 0}}
        now = int(time.time())
        total = len(self._keys_by_alias)
        n_ok = 0
        n_eligible_ok = 0
        n_invalid_perm = 0
        n_cooldown = 0
        n_soft_limit = 0
        n_require_ok_block = 0
        n_eligible = 0
        for alias in self._keys_by_alias.keys():
            st = self._status.get(alias)
            if st and st.status == "ok":
                n_ok += 1
            if st and bool(st.eligible_ok):
                n_eligible_ok += 1
            if st and st.status in {"invalid", "permission_denied"}:
                n_invalid_perm += 1
            if st and st.cooldown_until_epoch and now < int(st.cooldown_until_epoch) and st.status != "ok":
                n_cooldown += 1
            if self._soft_limit_reached(alias):
                n_soft_limit += 1
            if require_status_ok and (not st or not bool(st.eligible_ok)):
                n_require_ok_block += 1
            # elegível conforme regras de get_available_key (require_status_ok → eligible_ok)
            if st and st.status in {"invalid", "permission_denied"}:
                continue
            if st and st.cooldown_until_epoch and now < int(st.cooldown_until_epoch) and st.status != "ok":
                continue
            if require_status_ok and (not st or not bool(st.eligible_ok)):
                continue
            if self._soft_limit_reached(alias):
                continue
            n_eligible += 1

        reason = "unknown"
        if require_status_ok and n_eligible_ok == 0:
            reason = "no_ok_from_start"
        elif n_soft_limit >= total and total > 0:
            reason = "per_key_limit"
        elif (n_cooldown + n_invalid_perm + n_require_ok_block) >= total and (n_ok > 0 or require_status_ok):
            reason = "all_in_cooldown_or_blocked"
        if n_eligible == 0 and reason == "unknown":
            # heurística final
            if n_cooldown > 0 and n_ok > 0:
                reason = "all_in_cooldown_or_blocked"
            elif n_soft_limit > 0:
                reason = "per_key_limit"
            elif require_status_ok and n_ok == 0:
                reason = "no_ok_from_start"

        return {
            "reason": reason,
            "counts": {
                "total_loaded": total,
                "ok": n_ok,
                "eligible_ok": n_eligible_ok,
                "invalid_or_permission": n_invalid_perm,
                "cooldown_active": n_cooldown,
                "soft_limit_reached": n_soft_limit,
                "blocked_by_require_ok": n_require_ok_block,
                "eligible_now": n_eligible,
            },
            "strategy": self.rotation_strategy,
            "max_calls_per_key_per_run": self.max_calls_per_key_per_run,
        }

    def get_available_key(self, *, require_status_ok: bool = False) -> Optional[Tuple[str, str]]:
        if not self.enabled:
            return None
        if not self._keys_by_alias:
            self.load_keys()

        candidates: List[str] = []
        for alias, key in self._keys_by_alias.items():
            if self._is_in_cooldown(alias):
                continue
            st = self._status.get(alias)
            if st and st.status in {"invalid", "permission_denied"}:
                continue
            if require_status_ok:
                if not st or not bool(st.eligible_ok):
                    continue
            if self._soft_limit_reached(alias):
                continue
            candidates.append(alias)

        if not candidates:
            return None

        # Estratégias de rotação: evitar concentrar numa só chave quando há outras OK.
        alias = ""
        if self.rotation_strategy == "round_robin":
            ordered = sorted(list(self._keys_by_alias.keys()), key=lambda x: x)
            start = self._rr_cursor % max(1, len(ordered))
            for j in range(len(ordered)):
                a = ordered[(start + j) % len(ordered)]
                if a in candidates:
                    alias = a
                    self._rr_cursor = (start + j + 1) % len(ordered)
                    break
            # não repetir a mesma chave se houver alternativa
            if alias and alias == self._last_selected_alias and len(candidates) > 1:
                for a in ordered:
                    if a in candidates and a != self._last_selected_alias:
                        alias = a
                        break
        elif self.rotation_strategy == "least_recently_used":
            def lru_rank(a: str) -> Tuple[int, int, int]:
                s = self._status.get(a) or KeyStatus(key_alias=a, masked_key=mask_key(self._keys_by_alias[a]))
                return (int(s.last_used_epoch or 0), int(self._used_count_run.get(a, 0)), int(s.consecutive_failures or 0))
            alias = sorted(candidates, key=lru_rank)[0]
            if alias == self._last_selected_alias and len(candidates) > 1:
                alt = [c for c in candidates if c != self._last_selected_alias]
                alias = sorted(alt, key=lru_rank)[0]
        else:
            # random antigo: menos uso e menos falhas, mas com jitter
            def rank(a: str) -> Tuple[int, int, int]:
                s = self._status.get(a) or KeyStatus(key_alias=a, masked_key=mask_key(self._keys_by_alias[a]))
                return (self._used_count_run.get(a, 0), s.consecutive_failures, random.randint(0, 9999))
            alias = sorted(candidates, key=rank)[0]

        if not alias:
            alias = candidates[0]

        self._used_count_run[alias] = self._used_count_run.get(alias, 0) + 1
        self._last_selected_alias = alias
        st = self._status.setdefault(alias, KeyStatus(key_alias=alias, masked_key=mask_key(self._keys_by_alias[alias])))
        st.calls_this_run += 1
        st.last_used_epoch = int(time.time())
        st.last_used_at = _utc_now_iso()
        return alias, self._keys_by_alias[alias]

    def mark_success(self, alias: str) -> None:
        st = self._status.setdefault(alias, KeyStatus(key_alias=alias, masked_key=mask_key(self._keys_by_alias.get(alias, ""))))
        st.status = "ok"
        st.eligible_ok = True
        st.http_code = 200
        st.error_code = ""
        st.error_message_resumida = ""
        st.last_success_at = _utc_now_iso()
        st.consecutive_failures = 0
        st.total_success += 1
        # Se a chave voltou a OK (ex.: recheck manual), não manter cooldown antigo.
        st.cooldown_until = ""
        st.cooldown_until_epoch = 0
        st.success_this_run += 1
        st.last_error_status = ""
        st.last_error_message = ""

    def mark_failure(self, alias: str, exc: BaseException) -> Dict[str, Any]:
        info = classify_gemini_exception(exc)
        st = self._status.setdefault(alias, KeyStatus(key_alias=alias, masked_key=mask_key(self._keys_by_alias.get(alias, ""))))
        st.status = _t(info.get("status")) or "unknown_error"
        st.http_code = info.get("http_code")
        st.error_code = _t(info.get("error_code"))
        st.error_message_resumida = redact_secrets_in_text(_t(info.get("error_message"))[:220])
        st.last_failure_at = _utc_now_iso()
        st.consecutive_failures += 1
        st.total_failure += 1
        st.errors_this_run += 1
        st.last_error_status = st.status
        st.last_error_message = _t(info.get("error_message"))

        if st.status == "quota_exhausted":
            st.total_quota_exhausted += 1
            st.quota_this_run += 1
            self.mark_quota_exhausted(alias, retry_after_seconds=None)
            # quota não “invalida” a chave; só coloca em cooldown
            st.eligible_ok = True if st.eligible_ok else True
        if st.status == "invalid":
            st.total_invalid += 1
            st.eligible_ok = False
        if st.status == "permission_denied":
            st.eligible_ok = False
        return info

    def mark_quota_exhausted(self, alias: str, retry_after_seconds: Optional[int]) -> None:
        st = self._status.setdefault(alias, KeyStatus(key_alias=alias, masked_key=mask_key(self._keys_by_alias.get(alias, ""))))
        now = int(time.time())
        cooldown = int(retry_after_seconds) if isinstance(retry_after_seconds, int) and retry_after_seconds > 0 else self.cooldown_seconds_default
        st.cooldown_until_epoch = now + cooldown
        st.cooldown_until = datetime.fromtimestamp(st.cooldown_until_epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def mark_invalid(self, alias: str) -> None:
        st = self._status.setdefault(alias, KeyStatus(key_alias=alias, masked_key=mask_key(self._keys_by_alias.get(alias, ""))))
        st.status = "invalid"

    def mark_permission_denied(self, alias: str) -> None:
        st = self._status.setdefault(alias, KeyStatus(key_alias=alias, masked_key=mask_key(self._keys_by_alias.get(alias, ""))))
        st.status = "permission_denied"

    def count_ok_ready_aliases(self, *, require_status_ok: bool = True) -> int:
        """Quantas chaves estão utilizáveis agora (espelha get_available_key: cooldown + eligible_ok)."""
        if not self._keys_by_alias:
            self.load_keys()
        n = 0
        for alias in self._keys_by_alias.keys():
            if self._is_in_cooldown(alias):
                continue
            st = self._status.get(alias)
            if st and st.status in {"invalid", "permission_denied"}:
                continue
            if require_status_ok:
                if not st or not bool(st.eligible_ok):
                    continue
            if self._soft_limit_reached(alias):
                continue
            n += 1
        return n

    def recommended_parallelism(self) -> int:
        """
        Recomendação conservadora: quantos arquivos testar agora (baseado em chaves OK e sem cooldown).
        """
        ok = 0
        for alias in self._keys_by_alias.keys():
            if self._is_in_cooldown(alias):
                continue
            st = self._status.get(alias)
            if st and st.status == "ok":
                ok += 1
        return max(1, ok)


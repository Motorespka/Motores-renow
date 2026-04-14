import os
import unittest

from ai_board.credentials import CredentialResolutionError
from ai_board.role_runtime import RuntimeFallback, get_role_runtime


class RoleRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        for name in [
            "AI_KEY_SECURITY",
            "AI_KEY_QA",
            "AI_KEY_QA_RESERVE",
        ]:
            os.environ.pop(name, None)

    def test_primary_runtime_success(self):
        os.environ["AI_KEY_SECURITY"] = "security-primary"
        runtime = get_role_runtime("security")
        self.assertEqual(runtime.env_var_used, "AI_KEY_SECURITY")
        self.assertEqual(runtime.audit["used_fallback"], False)

    def test_missing_primary_fails(self):
        with self.assertRaises(CredentialResolutionError):
            get_role_runtime("security")

    def test_fallback_requires_approval_and_failure_reason(self):
        os.environ["AI_KEY_QA"] = "qa-primary"
        os.environ["AI_KEY_QA_RESERVE"] = "qa-reserve"
        with self.assertRaises(CredentialResolutionError):
            get_role_runtime(
                "qa",
                fallback=RuntimeFallback(
                    approved=False,
                    reason="provider_timeout",
                    primary_failure="timeout",
                ),
            )

    def test_fallback_success(self):
        os.environ["AI_KEY_QA"] = "qa-primary"
        os.environ["AI_KEY_QA_RESERVE"] = "qa-reserve"
        runtime = get_role_runtime(
            "qa",
            fallback=RuntimeFallback(
                approved=True,
                reason="provider_timeout",
                primary_failure="429 timeout",
            ),
        )
        self.assertEqual(runtime.env_var_used, "AI_KEY_QA_RESERVE")
        self.assertEqual(runtime.audit["used_fallback"], True)


if __name__ == "__main__":
    unittest.main()

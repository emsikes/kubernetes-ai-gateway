"""Unit tests for PII Guard"""
import unittest
from models import ChatRequest, ChatMessage
from guardrails.pii_guard import PIIGuard, PII_PATTERNS
from guardrails.base import GuardrailAction, Severity


def make_request(text: str) -> ChatRequest:
    """Helper to build a ChatRequest with a single user message."""
    return ChatRequest(
        model="llama3.2:1b",
        messages=[ChatMessage(role="user", content=text)]
    )


# Default test config — all types enabled, block by default
TEST_CONFIG = {
    "enabled": True,
    "default_action": "block",
    "mask_strategy": "full",
    "pii_types": {
        "SSN": {"enabled": True, "severity": "critical", "action": "block"},
        "CREDIT_CARD": {"enabled": True, "severity": "critical", "action": "block"},
        "EMAIL": {"enabled": True, "severity": "high", "action": "redact", "mask_strategy": "partial"},
        "PHONE": {"enabled": True, "severity": "high", "action": "redact", "mask_strategy": "partial"},
        "IP_ADDRESS": {"enabled": True, "severity": "medium", "action": "log"},
        "DOB": {"enabled": True, "severity": "high", "action": "redact", "mask_strategy": "full"},
    }
}


class TestPIIGuard(unittest.TestCase):

    def setUp(self):
        self.guard = PIIGuard(TEST_CONFIG)

    def test_clean_text_passes(self):
        """No PII should pass cleanly."""
        result = self.guard.evaluate(make_request("What is the weather today?"))
        self.assertTrue(result.passed)

    def test_disabled_guard_passes_everything(self):
        """Disabled guard should let everything through."""
        guard = PIIGuard({"enabled": False})
        result = guard.evaluate(make_request("My SSN is 123-45-6789"))
        self.assertTrue(result.passed)

        # --- SSN Detection ---

    def test_ssn_with_dashes(self):
        """Standard SSN format: 123-45-6789"""
        result = self.guard.evaluate(make_request("My SSN is 123-45-6789"))
        self.assertFalse(result.passed)
        self.assertEqual(result.severity, Severity.CRITICAL)

    def test_ssn_with_spaces(self):
        """SSN with spaces: 123 45 6789"""
        result = self.guard.evaluate(make_request("SSN: 123 45 6789"))
        self.assertFalse(result.passed)

    def test_ssn_no_separators(self):
        """SSN without separators: 123456789"""
        result = self.guard.evaluate(make_request("My number is 123456789"))
        self.assertFalse(result.passed)

    # --- Credit Card Detection ---

    def test_credit_card_with_dashes(self):
        """Visa format: 4111-1111-1111-1111"""
        result = self.guard.evaluate(make_request("Card: 4111-1111-1111-1111"))
        self.assertFalse(result.passed)
        self.assertEqual(result.severity, Severity.CRITICAL)

    def test_credit_card_with_spaces(self):
        """Card with spaces: 4111 1111 1111 1111"""
        result = self.guard.evaluate(make_request("Pay with 4111 1111 1111 1111"))
        self.assertFalse(result.passed)

    # --- Email Detection ---

    def test_email_detected(self):
        """Standard email should be caught."""
        result = self.guard.evaluate(make_request("Email me at matt@example.com"))
        self.assertTrue(result.passed)  # Email action is REDACT, not BLOCK
        self.assertEqual(result.action, GuardrailAction.REDACT)

    def test_email_complex(self):
        """Email with dots and plus addressing."""
        result = self.guard.evaluate(make_request("Send to matt.sikes+test@company.co.uk"))
        self.assertTrue(result.passed)
        self.assertEqual(result.action, GuardrailAction.REDACT)

    # --- Phone Detection ---

    def test_phone_standard(self):
        """Standard US phone: (555) 123-4567"""
        result = self.guard.evaluate(make_request("Call me at (555) 123-4567"))
        self.assertTrue(result.passed)  # Phone action is REDACT
        self.assertEqual(result.action, GuardrailAction.REDACT)

    def test_phone_with_country_code(self):
        """+1 prefix: +1-555-123-4567"""
        result = self.guard.evaluate(make_request("Reach me at +1-555-123-4567"))
        self.assertTrue(result.passed)
        self.assertEqual(result.action, GuardrailAction.REDACT)

    # --- IP Address Detection ---

    def test_ip_address(self):
        """IPv4 address should be logged but pass."""
        result = self.guard.evaluate(make_request("Server is at 192.168.1.100"))
        self.assertTrue(result.passed)  # IP action is LOG
        self.assertEqual(result.action, GuardrailAction.LOG)

    # --- DOB Detection ---

    def test_dob_detected(self):
        """Date of birth format: 01/15/1990"""
        result = self.guard.evaluate(make_request("Born on 01/15/1990"))
        self.assertTrue(result.passed)  # DOB action is REDACT
        self.assertEqual(result.action, GuardrailAction.REDACT)

    def test_dob_with_dashes(self):
        """DOB with dashes: 12-25-2000"""
        result = self.guard.evaluate(make_request("DOB: 12-25-2000"))
        self.assertTrue(result.passed)
        self.assertEqual(result.action, GuardrailAction.REDACT)

        # --- Full Masking ---

    def test_mask_full_ssn(self):
        """Full mask should replace SSN entirely."""
        request = make_request("My SSN is 123-45-6789")
        matches = self.guard._scan_text(self.guard._extract_text(request))
        result = self.guard._mask_full(matches[0])
        self.assertEqual(result, "[REDACTED_SSN]")

    def test_mask_full_email(self):
        """Full mask should replace email entirely."""
        request = make_request("Email: matt@example.com")
        matches = self.guard._scan_text(self.guard._extract_text(request))
        # Find the email match specifically
        email_match = [m for m in matches if m.pii_type == "EMAIL"][0]
        result = self.guard._mask_full(email_match)
        self.assertEqual(result, "[REDACTED_EMAIL]")

    # --- Partial Masking ---

    def test_mask_partial_ssn(self):
        """Partial SSN should show last 4."""
        request = make_request("SSN: 123-45-6789")
        matches = self.guard._scan_text(self.guard._extract_text(request))
        ssn_match = [m for m in matches if m.pii_type == "SSN"][0]
        result = self.guard._mask_partial(ssn_match)
        self.assertEqual(result, "***-**-6789")

    def test_mask_partial_email(self):
        """Partial email should mask local, keep domain."""
        request = make_request("Email: matt@example.com")
        matches = self.guard._scan_text(self.guard._extract_text(request))
        email_match = [m for m in matches if m.pii_type == "EMAIL"][0]
        result = self.guard._mask_partial(email_match)
        self.assertEqual(result, "****@example.com")

    def test_mask_partial_credit_card(self):
        """Partial card should show last 4."""
        request = make_request("Card: 4111-1111-1111-1111")
        matches = self.guard._scan_text(self.guard._extract_text(request))
        cc_match = [m for m in matches if m.pii_type == "CREDIT_CARD"][0]
        result = self.guard._mask_partial(cc_match)
        self.assertEqual(result, "****-****-****-1111")

    # --- Hash Masking ---

    def test_mask_hash_deterministic(self):
        """Same input should always produce same hash."""
        request = make_request("SSN: 123-45-6789")
        matches = self.guard._scan_text(self.guard._extract_text(request))
        ssn_match = [m for m in matches if m.pii_type == "SSN"][0]
        result1 = self.guard._mask_hash(ssn_match)
        result2 = self.guard._mask_hash(ssn_match)
        self.assertEqual(result1, result2)

    def test_mask_hash_format(self):
        """Hash should follow [TYPE:hash] format."""
        request = make_request("SSN: 123-45-6789")
        matches = self.guard._scan_text(self.guard._extract_text(request))
        ssn_match = [m for m in matches if m.pii_type == "SSN"][0]
        result = self.guard._mask_hash(ssn_match)
        self.assertTrue(result.startswith("[SSN:"))
        self.assertTrue(result.endswith("]"))
        # 8 char hash between the colon and bracket
        hash_part = result.split(":")[1].rstrip("]")
        self.assertEqual(len(hash_part), 8)

        # --- Apply Masking Integration ---

    def test_apply_masking_single(self):
        """Full text should have PII replaced."""
        text = "My SSN is 123-45-6789 please help"
        matches = self.guard._scan_text(text)
        result = self.guard._apply_masking(text, matches)
        self.assertNotIn("123-45-6789", result)
        self.assertIn("[REDACTED_SSN]", result)
        self.assertIn("please help", result)  # Non-PII text preserved

    def test_apply_masking_multiple(self):
        """Multiple PII types in one message should all be masked."""
        text = "SSN 123-45-6789 and email matt@test.com"
        matches = self.guard._scan_text(text)
        result = self.guard._apply_masking(text, matches)
        self.assertNotIn("123-45-6789", result)
        self.assertNotIn("matt@test.com", result)

    def test_apply_masking_preserves_surrounding_text(self):
        """Text around PII should remain untouched."""
        text = "Before 123-45-6789 after"
        matches = self.guard._scan_text(text)
        result = self.guard._apply_masking(text, matches)
        self.assertTrue(result.startswith("Before"))
        self.assertTrue(result.endswith("after"))

    # --- Worst-Wins Escalation ---

    def test_mixed_severity_uses_worst(self):
        """SSN (critical) + email (high) should escalate to critical."""
        result = self.guard.evaluate(
            make_request("SSN 123-45-6789 email matt@test.com")
        )
        self.assertEqual(result.severity, Severity.CRITICAL)

    def test_mixed_actions_uses_worst(self):
        """SSN (block) + email (redact) should escalate to block."""
        result = self.guard.evaluate(
            make_request("SSN 123-45-6789 email matt@test.com")
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.action, GuardrailAction.BLOCK)

    # --- Disabled PII Type ---

    def test_disabled_type_ignored(self):
        """Disabled PII type should not trigger."""
        config = {
            "enabled": True,
            "default_action": "block",
            "mask_strategy": "full",
            "pii_types": {
                "EMAIL": {"enabled": False},
            }
        }
        guard = PIIGuard(config)
        result = guard.evaluate(make_request("Email me at matt@test.com"))
        self.assertTrue(result.passed)
        self.assertIsNone(result.masked_text)


if __name__ == "__main__":
    unittest.main()
"""OCT-022..026: scope models, parser, normalizer, Scope Gate (critical)."""
import uuid

import pytest

from app.models.enums import Confidence, ReviewStatus, ScopeDecision, ScopeKind
from app.modules.scope_gate.matcher import ScopeEntry, decide
from app.modules.scope_parser.normalizer import classify_and_normalize
from app.modules.scope_parser.parser import parse_scope


# ---------------------------------------------------------------------------
# OCT-022 models
# ---------------------------------------------------------------------------

class TestScopeModels:
    def test_models_importable(self):
        from app.models.scope import ScopeItem, OutOfScopeItem, ScopeRule, RateLimitRule
        assert ScopeItem.__tablename__ == "scope_items"
        assert OutOfScopeItem.__tablename__ == "out_of_scope_items"
        assert ScopeRule.__tablename__ == "scope_rules"
        assert RateLimitRule.__tablename__ == "rate_limit_rules"

    def test_scope_item_has_fk(self):
        from app.models.scope import ScopeItem
        fks = {fk.column.table.name for fk in ScopeItem.__table__.foreign_keys}
        assert "programs" in fks

    def test_migration_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "app/database/migrations/versions/0006_scope_entities.py"
        assert p.exists()


# ---------------------------------------------------------------------------
# OCT-023 normalizer / parser
# ---------------------------------------------------------------------------

class TestNormalizer:
    def test_domain(self):
        kind, norm, wc = classify_and_normalize("Example.COM")
        assert kind == ScopeKind.DOMAIN and norm == "example.com" and not wc

    def test_wildcard(self):
        kind, norm, wc = classify_and_normalize("*.example.com")
        assert kind == ScopeKind.WILDCARD and wc and norm == "*.example.com"

    def test_url(self):
        kind, norm, wc = classify_and_normalize("https://api.example.com/v1/")
        assert kind == ScopeKind.URL

    def test_ip(self):
        kind, norm, wc = classify_and_normalize("192.168.1.1")
        assert kind == ScopeKind.IP

    def test_cidr(self):
        kind, norm, wc = classify_and_normalize("10.0.0.0/8")
        assert kind == ScopeKind.CIDR

    def test_asn(self):
        kind, norm, wc = classify_and_normalize("AS12345")
        assert kind == ScopeKind.ASN

    def test_garbage_is_other(self):
        kind, norm, wc = classify_and_normalize("this is not a domain")
        assert kind == ScopeKind.OTHER


class TestParser:
    def test_parses_in_scope_domains(self):
        result = parse_scope("In scope:\n*.example.com\napi.example.com")
        norms = {i.normalized_value for i in result.in_scope}
        assert "*.example.com" in norms
        assert "api.example.com" in norms

    def test_out_of_scope_section(self):
        text = "In scope:\nexample.com\nOut of scope:\nadmin.example.com"
        result = parse_scope(text)
        oos = {i.normalized_value for i in result.out_of_scope}
        assert "admin.example.com" in oos

    def test_rule_detection(self):
        result = parse_scope("Do not perform DoS attacks.\nRate limit: 5 req/s")
        assert len(result.rules) >= 1

    def test_nothing_assumed_in_scope_for_garbage(self):
        result = parse_scope("please be nice and gentle")
        # No clean tokens → nothing added as in_scope high-confidence
        assert all(i.confidence != Confidence.HIGH for i in result.ambiguous)


# ---------------------------------------------------------------------------
# OCT-026 Scope Gate — CRITICAL NODE. Exhaustive decision tests.
# ---------------------------------------------------------------------------

class TestScopeGateMatcher:
    def _in(self, *vals):
        out = []
        for v in vals:
            wc = v.startswith("*.")
            kind = "wildcard" if wc else ("cidr" if "/" in v else ("ip" if v[0].isdigit() else "domain"))
            out.append(ScopeEntry(normalized_value=v, kind=kind, is_wildcard=wc))
        return out

    # --- in-scope allow ---
    def test_exact_domain_in_scope(self):
        d = decide("example.com", "domain", self._in("example.com"), [])
        assert d == ScopeDecision.IN

    def test_wildcard_covers_subdomain(self):
        d = decide("api.example.com", "domain", self._in("*.example.com"), [])
        assert d == ScopeDecision.IN

    def test_wildcard_covers_apex(self):
        d = decide("example.com", "domain", self._in("*.example.com"), [])
        assert d == ScopeDecision.IN

    def test_deep_subdomain(self):
        d = decide("a.b.c.example.com", "domain", self._in("*.example.com"), [])
        assert d == ScopeDecision.IN

    # --- default deny ---
    def test_unmatched_is_out(self):
        d = decide("other.com", "domain", self._in("example.com"), [])
        assert d == ScopeDecision.OUT

    def test_empty_scope_is_out(self):
        d = decide("example.com", "domain", [], [])
        assert d == ScopeDecision.OUT

    # --- out-of-scope hard block (precedence) ---
    def test_explicit_oos_blocks_even_if_in_scope(self):
        d = decide(
            "admin.example.com", "domain",
            self._in("*.example.com"),           # would be IN
            self._in("admin.example.com"),       # but explicitly OOS
        )
        assert d == ScopeDecision.OUT

    def test_oos_wildcard_blocks(self):
        d = decide(
            "x.internal.example.com", "domain",
            self._in("*.example.com"),
            self._in("*.internal.example.com"),
        )
        assert d == ScopeDecision.OUT

    # --- ambiguous (requires review) ---
    def test_requires_review_is_ambiguous(self):
        entry = ScopeEntry("example.com", "domain", False, requires_review=True)
        d = decide("example.com", "domain", [entry], [])
        assert d == ScopeDecision.AMBIGUOUS

    def test_confirmed_beats_review_sibling(self):
        confirmed = ScopeEntry("example.com", "domain", False, requires_review=False)
        review = ScopeEntry("*.example.com", "wildcard", True, requires_review=True)
        d = decide("example.com", "domain", [confirmed, review], [])
        assert d == ScopeDecision.IN

    # --- IP / CIDR ---
    def test_ip_in_cidr(self):
        d = decide("10.1.2.3", "ip", self._in("10.0.0.0/8"), [])
        assert d == ScopeDecision.IN

    def test_ip_not_in_cidr(self):
        d = decide("192.168.1.1", "ip", self._in("10.0.0.0/8"), [])
        assert d == ScopeDecision.OUT

    def test_ip_oos_blocks(self):
        d = decide("10.1.2.3", "ip", self._in("10.0.0.0/8"), self._in("10.1.2.3"))
        assert d == ScopeDecision.OUT

    # --- evasion attempts ---
    def test_case_insensitive(self):
        d = decide("API.EXAMPLE.COM", "domain", self._in("*.example.com"), [])
        assert d == ScopeDecision.IN

    def test_trailing_dot_normalized(self):
        d = decide("example.com.", "domain", self._in("example.com"), [])
        assert d == ScopeDecision.IN

    def test_lookalike_not_matched(self):
        d = decide("example.com.evil.com", "domain", self._in("*.example.com"), [])
        assert d == ScopeDecision.OUT

    def test_substring_not_matched(self):
        d = decide("notexample.com", "domain", self._in("example.com"), [])
        assert d == ScopeDecision.OUT

    def test_suffix_confusion_blocked(self):
        # "evilexample.com" should NOT match "*.example.com"
        d = decide("evilexample.com", "domain", self._in("*.example.com"), [])
        assert d == ScopeDecision.OUT

    def test_url_host_extracted(self):
        d = decide("https://api.example.com/path", "url", self._in("*.example.com"), [])
        assert d == ScopeDecision.IN

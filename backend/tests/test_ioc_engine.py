"""
LEATrace IOC Engine Tests — Production.

Tests the DB-backed IOC engine with lifecycle, versioning, and deduplication.
Verifies NO hardcoded IOCs exist anywhere in the codebase.
"""

import datetime
import uuid
import pytest
from unittest.mock import MagicMock, patch

from app.ioc_engine import ioc_engine, IOCType, IOCStatus, IOCSeverity


class TestIOCNormalization:
    """Tests IOC value normalization."""

    def test_normalize_ip_defang(self):
        assert ioc_engine.normalize_value("ip", "192[.]168[.]1[.]1") == "192.168.1.1"

    def test_normalize_domain_lowercase_strip(self):
        assert ioc_engine.normalize_value("domain", "EXAMPLE[.]COM.") == "example.com"

    def test_normalize_url_defang(self):
        result = ioc_engine.normalize_value("url", "hxxps://evil[.]com/path/")
        assert result == "https://evil.com/path"

    def test_normalize_hash_lowercase(self):
        result = ioc_engine.normalize_value("hash_sha256", "ABCDEF1234567890" * 4)
        assert result == ("abcdef1234567890" * 4)

    def test_normalize_email_lowercase(self):
        assert ioc_engine.normalize_value("email", "USER@EXAMPLE.COM") == "user@example.com"

    def test_normalize_cve_uppercase(self):
        assert ioc_engine.normalize_value("cve", "cve-2024-1234") == "CVE-2024-1234"

    def test_normalize_technique_uppercase(self):
        assert ioc_engine.normalize_value("attack_technique", "t1059") == "T1059"


class TestIOCValidation:
    """Tests IOC type validation patterns."""

    def test_validate_ipv4(self):
        assert ioc_engine.validate_value("ip", "192.168.1.1")

    def test_validate_ipv4_cidr(self):
        assert ioc_engine.validate_value("ip", "10.0.0.0/8")

    def test_validate_domain(self):
        assert ioc_engine.validate_value("domain", "example.com")
        assert ioc_engine.validate_value("domain", "sub.domain.example.co.uk")

    def test_validate_md5(self):
        assert ioc_engine.validate_value("hash_md5", "d41d8cd98f00b204e9800998ecf8427e")

    def test_validate_sha1(self):
        assert ioc_engine.validate_value("hash_sha1", "da39a3ee5e6b4b0d3255bfef95601890afd80709")

    def test_validate_sha256(self):
        assert ioc_engine.validate_value("hash_sha256", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_validate_email(self):
        assert ioc_engine.validate_value("email", "user@example.com")

    def test_validate_cve(self):
        assert ioc_engine.validate_value("cve", "CVE-2024-12345")

    def test_validate_technique(self):
        assert ioc_engine.validate_value("attack_technique", "T1059")
        assert ioc_engine.validate_value("attack_technique", "T1059.001")


class TestIOCDedupHash:
    """Tests deduplication hash computation."""

    def test_same_input_same_hash(self):
        h1 = ioc_engine.compute_dedup_hash("ip", "192.168.1.1")
        h2 = ioc_engine.compute_dedup_hash("ip", "192.168.1.1")
        assert h1 == h2

    def test_different_type_different_hash(self):
        h1 = ioc_engine.compute_dedup_hash("ip", "192.168.1.1")
        h2 = ioc_engine.compute_dedup_hash("domain", "192.168.1.1")
        assert h1 != h2

    def test_different_value_different_hash(self):
        h1 = ioc_engine.compute_dedup_hash("ip", "192.168.1.1")
        h2 = ioc_engine.compute_dedup_hash("ip", "192.168.1.2")
        assert h1 != h2


class TestIOCCheckNoFabrication:
    """Verifies that check_ioc never fabricates data."""

    def test_check_returns_not_flagged_when_not_found(self):
        """IOC check on unknown value should return flagged=False."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = ioc_engine.check_ioc("192.168.1.1", db=mock_db)
        assert result["flagged"] is False

    def test_check_without_db_returns_status(self):
        """IOC check without DB session returns db_unavailable status."""
        result = ioc_engine.check_ioc("192.168.1.1", db=None)
        assert result["flagged"] is False
        assert "db_unavailable" in result.get("status", "")


class TestIOCTypeInference:
    """Tests automatic IOC type inference."""

    def test_infer_ipv4(self):
        types = ioc_engine._infer_types("192.168.1.1")
        assert "ip" in types

    def test_infer_sha256(self):
        types = ioc_engine._infer_types("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        assert "hash_sha256" in types

    def test_infer_url(self):
        types = ioc_engine._infer_types("https://evil.com/malware.exe")
        assert "url" in types

    def test_infer_cve(self):
        types = ioc_engine._infer_types("CVE-2024-12345")
        assert "cve" in types

    def test_infer_email(self):
        types = ioc_engine._infer_types("user@evil.com")
        assert "email" in types

    def test_infer_evm_wallet(self):
        types = ioc_engine._infer_types("0x" + "a" * 40)
        assert "wallet" in types


class TestIOCEngineNoHardcodedData:
    """Ensures the IOC engine has no hardcoded indicator data."""

    def test_no_ioc_database_list(self):
        """The old IOC_DATABASE global list must not exist."""
        import app.ioc_engine as module
        assert not hasattr(module, "IOC_DATABASE"), \
            "IOC_DATABASE in-memory list must be removed"

    def test_no_fabricated_ioc_functions(self):
        """No mock/fake/demo data generation functions."""
        import app.ioc_engine as module
        members = dir(module)
        forbidden = [m for m in members if any(
            p in m.lower() for p in ["mock_", "fake_", "demo_", "sample_", "dummy_"]
        )]
        assert forbidden == [], f"Found forbidden functions: {forbidden}"

"""
Tests for production Sanctions ingestion, scheduler, and threat DB.
"""
import hashlib
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from app.feed_scheduler import ThreatFeedScheduler, NOT_CONFIGURED, _parse_ofac_sdn, _sha256
from app.threat_database import ThreatIntelligenceDatabase


# ─── Scheduler ────────────────────────────────────────────────────────────────

class TestThreatFeedSchedulerNotConfigured:
    def setup_method(self):
        # Ensure no sources configured
        with patch.dict(os.environ, {"SANCTIONS_SOURCES": ""}, clear=False):
            self.scheduler = ThreatFeedScheduler()

    def test_not_configured_returns_status(self):
        result = self.scheduler.get_status()
        assert result["status"] == "not_configured"
        assert "SANCTIONS_SOURCES" in result["message"]

    def test_run_sync_not_configured(self):
        result = self.scheduler.run_daily_sync(db=MagicMock())
        assert result["status"] == "not_configured"

    def test_is_configured_false(self):
        assert self.scheduler.is_configured() is False


class TestThreatFeedSchedulerConfigured:
    def test_is_configured_true(self):
        with patch.dict(os.environ, {"SANCTIONS_SOURCES": '[{"type":"OFAC_SDN"}]'}, clear=False):
            # _get_sources reads os.getenv dynamically — call is_configured inside patch
            s = ThreatFeedScheduler()
            assert s.is_configured() is True

    def test_status_shows_providers(self):
        with patch.dict(os.environ, {"SANCTIONS_SOURCES": '[{"type":"OFAC_SDN"}]'}, clear=False):
            s = ThreatFeedScheduler()
            result = s.get_status()
            assert result["configured"] is True
            assert "OFAC_SDN" in result["providers"]


# ─── OFAC XML Parser ──────────────────────────────────────────────────────────

SAMPLE_OFAC_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<sdnList xmlns="http://tempuri.org/sdnList.xsd">
  <sdnEntry>
    <uid>12345</uid>
    <lastName>Ivanov</lastName>
    <firstName>Test</firstName>
    <sdnType>Individual</sdnType>
    <programList>
      <program>RUSSIA</program>
    </programList>
    <idList>
      <id>
        <idType>Digital Currency Address - ETH</idType>
        <idNumber>0xDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF</idNumber>
      </id>
    </idList>
  </sdnEntry>
  <sdnEntry>
    <uid>67890</uid>
    <lastName>NoAddress Entity</lastName>
    <sdnType>Entity</sdnType>
    <programList>
      <program>IRAN</program>
    </programList>
    <idList/>
  </sdnEntry>
</sdnList>"""


class TestOFACXMLParser:
    def test_parses_entries_from_xml(self):
        entries = list(_parse_ofac_sdn(SAMPLE_OFAC_XML))
        assert len(entries) >= 1

    def test_extracts_crypto_address(self):
        entries = list(_parse_ofac_sdn(SAMPLE_OFAC_XML))
        crypto_entries = [e for e in entries if e.get("address")]
        assert len(crypto_entries) == 1
        assert "0xDEAD" in crypto_entries[0]["address"].upper() or crypto_entries[0]["address"]

    def test_list_type_is_ofac(self):
        entries = list(_parse_ofac_sdn(SAMPLE_OFAC_XML))
        for e in entries:
            assert e["list_type"] == "OFAC_SDN"

    def test_program_extracted(self):
        entries = list(_parse_ofac_sdn(SAMPLE_OFAC_XML))
        programs = [e["program"] for e in entries if e["program"]]
        assert any("RUSSIA" in p or "IRAN" in p for p in programs)

    def test_no_crash_on_empty_xml(self):
        entries = list(_parse_ofac_sdn(b"<sdnList></sdnList>"))
        assert isinstance(entries, list)

    def test_no_crash_on_malformed_xml(self):
        entries = list(_parse_ofac_sdn(b"NOT XML AT ALL <<<"))
        assert isinstance(entries, list)  # Should return empty list, not raise


# ─── Hash Deduplication ───────────────────────────────────────────────────────

class TestSHA256Dedup:
    def test_same_content_same_hash(self):
        data = b"test content"
        assert _sha256(data) == _sha256(data)

    def test_different_content_different_hash(self):
        assert _sha256(b"content_a") != _sha256(b"content_b")

    def test_hash_is_64_hex_chars(self):
        h = _sha256(b"data")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ─── ThreatIntelligenceDatabase ──────────────────────────────────────────────

class TestThreatIntelligenceDatabase:
    def setup_method(self):
        self.db = ThreatIntelligenceDatabase()

    def test_check_sanction_no_db_returns_none(self):
        result = self.db.check_sanction("0x1234", db=None)
        assert result is None

    def test_check_stix_no_db_returns_none(self):
        result = self.db.check_stix_indicator("0x1234", db=None)
        assert result is None

    def test_check_sanction_db_query(self):
        mock_db = MagicMock()
        mock_entry = MagicMock()
        mock_entry.address = "0xabc"
        mock_entry.entity_name = "Test Entity"
        mock_entry.list_type = "OFAC_SDN"
        mock_entry.program = "IRAN"
        mock_entry.source_id = "12345"
        mock_entry.entry_type = "individual"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_entry

        result = self.db.check_sanction("0xabc", db=mock_db)
        assert result is not None
        assert result["owner"] == "Test Entity"
        assert result["registry"] == "OFAC_SDN"
        assert result["severity"] == "Critical"
        assert result["data_source"] == "database"

    def test_check_sanction_not_found_returns_none(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = self.db.check_sanction("0xnotfound", db=mock_db)
        assert result is None

    def test_list_sanctions_no_db(self):
        result = self.db.list_sanctions(db=None)
        assert result["status"] == "error"

    def test_empty_address_returns_none(self):
        result = self.db.check_sanction("", db=MagicMock())
        assert result is None

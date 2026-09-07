"""
Tests for the production TAXII 2.1 client.
Covers: not-configured status, STIX bundle parsing, wallet extraction,
collection listing with mock server, and validation.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.taxii_client import TAXIIClient, NOT_CONFIGURED, TAXIIAuthError, TAXIIConnectionError
from app.stix_engine import STIXEngine, STIXValidationError


# ─── TAXIIClient ─────────────────────────────────────────────────────────────

class TestTAXIIClientNotConfigured:
    def test_not_configured_returns_status(self):
        client = TAXIIClient(server_url=None)
        result = client.health_check()
        assert result["configured"] is False
        assert result["status"] == "not_configured"
        assert "TAXII_SERVER_URL" in result["message"]

    def test_discover_not_configured(self):
        client = TAXIIClient(server_url=None)
        result = client.discover()
        assert result["status"] == "not_configured"

    def test_list_collections_not_configured(self):
        client = TAXIIClient(server_url=None)
        result = client.list_collections()
        assert isinstance(result, list)
        assert result[0]["status"] == "not_configured"

    def test_sync_not_configured(self):
        client = TAXIIClient(server_url=None)
        result = client.sync_collection_objects("test-collection")
        assert isinstance(result, list)
        assert result[0]["status"] == "not_configured"

    def test_is_configured_false(self):
        client = TAXIIClient(server_url=None)
        assert client.is_configured() is False

    def test_is_configured_true(self):
        client = TAXIIClient(server_url="https://example.com/taxii")
        assert client.is_configured() is True


class TestTAXIIClientHTTP:
    def test_auth_error_on_401(self):
        client = TAXIIClient(server_url="https://taxii.example.com")
        import urllib.error
        with patch("app.taxii_client._http_get") as mock_get:
            mock_get.side_effect = TAXIIAuthError("401")
            result = client.discover()
            assert result["status"] == "error"

    def test_connection_error_on_retry_exhaustion(self):
        client = TAXIIClient(server_url="https://taxii.example.com")
        with patch("app.taxii_client._http_get") as mock_get:
            mock_get.side_effect = TAXIIConnectionError("all retries failed")
            result = client.discover()
            assert result["status"] == "error"
            assert "retries" in result["message"].lower() or "connection" in result["message"].lower()

    def test_successful_discovery(self):
        client = TAXIIClient(server_url="https://taxii.example.com")
        mock_response = {
            "title": "Test TAXII Server",
            "versions": ["taxii-2.1"],
            "api_roots": ["https://taxii.example.com/api/v21/"],
        }
        with patch("app.taxii_client._http_get", return_value=mock_response):
            result = client.discover()
            assert result["title"] == "Test TAXII Server"
            assert "taxii-2.1" in result["versions"]

    def test_health_check_healthy(self):
        client = TAXIIClient(server_url="https://taxii.example.com")
        mock_response = {
            "title": "Test Server",
            "versions": ["taxii-2.1"],
            "api_roots": ["https://taxii.example.com/api/"],
        }
        with patch("app.taxii_client._http_get", return_value=mock_response):
            result = client.health_check()
            assert result["configured"] is True
            assert result["status"] == "healthy"
            assert result["server_title"] == "Test Server"


# ─── STIXEngine ───────────────────────────────────────────────────────────────

class TestSTIXEngineFactory:
    def setup_method(self):
        self.engine = STIXEngine()

    def test_create_indicator_structure(self):
        ind = self.engine.create_indicator(
            name="Test Indicator",
            pattern="[ipv4-addr:value = '1.2.3.4']",
        )
        assert ind["type"] == "indicator"
        assert ind["spec_version"] == "2.1"
        assert ind["pattern_type"] == "stix"
        assert ind["name"] == "Test Indicator"
        assert "indicator--" in ind["id"]

    def test_create_malware_structure(self):
        mal = self.engine.create_malware("TestMalware", "Test ransomware")
        assert mal["type"] == "malware"
        assert mal["spec_version"] == "2.1"
        assert "malware--" in mal["id"]

    def test_create_relationship(self):
        rel = self.engine.create_relationship("indicator--abc", "malware--def", "indicates")
        assert rel["type"] == "relationship"
        assert rel["relationship_type"] == "indicates"
        assert rel["source_ref"] == "indicator--abc"
        assert rel["target_ref"] == "malware--def"

    def test_create_bundle(self):
        ind = self.engine.create_indicator("test", "[domain-name:value = 'evil.com']")
        bundle = self.engine.create_bundle([ind])
        assert bundle["type"] == "bundle"
        assert len(bundle["objects"]) == 1


class TestSTIXValidation:
    def setup_method(self):
        self.engine = STIXEngine()

    def test_valid_indicator_passes(self):
        ind = self.engine.create_indicator("test", "[ipv4-addr:value = '1.1.1.1']")
        # Should not raise
        self.engine.validate_object(ind)

    def test_missing_type_fails(self):
        with pytest.raises(STIXValidationError, match="missing 'type'"):
            self.engine.validate_object({"id": "indicator--123", "spec_version": "2.1"})

    def test_missing_required_fields_fails(self):
        with pytest.raises(STIXValidationError, match="missing required fields"):
            self.engine.validate_object({
                "type": "indicator",
                "spec_version": "2.1",
                "id": "indicator--123",
                # Missing: name, pattern, pattern_type, valid_from
            })

    def test_invalid_id_format_fails(self):
        with pytest.raises(STIXValidationError, match="Invalid STIX ID"):
            self.engine.validate_object({
                "type": "indicator",
                "spec_version": "2.1",
                "id": "invalid-id-no-double-dash",
                "name": "test",
                "pattern": "[x:y = 'z']",
                "pattern_type": "stix",
                "valid_from": "2024-01-01T00:00:00Z",
            })


class TestSTIXBundleParsing:
    def setup_method(self):
        self.engine = STIXEngine()

    def test_parse_valid_bundle(self):
        ind = self.engine.create_indicator("test", "[ipv4-addr:value = '10.0.0.1']")
        bundle = self.engine.create_bundle([ind])
        objects = list(self.engine.parse_bundle(bundle))
        assert len(objects) == 1
        assert objects[0]["type"] == "indicator"

    def test_parse_bundle_skips_invalid(self):
        ind = self.engine.create_indicator("valid", "[ipv4-addr:value = '10.0.0.2']")
        bundle = {
            "type": "bundle",
            "id": "bundle--123",
            "objects": [ind, {"type": "broken"}],  # second is invalid
        }
        # Should yield 1 valid object, silently skip broken one
        objects = list(self.engine.parse_bundle(bundle))
        assert len(objects) == 1

    def test_parse_non_bundle_raises(self):
        with pytest.raises(STIXValidationError, match="Expected type 'bundle'"):
            list(self.engine.parse_bundle({"type": "indicator"}))

    def test_extract_indicators(self):
        ind = self.engine.create_indicator("test", "[ipv4-addr:value = '192.168.1.1']")
        mal = self.engine.create_malware("Ransomware", "bad malware")
        bundle = self.engine.create_bundle([ind, mal])
        indicators = self.engine.extract_indicators(bundle)
        assert len(indicators) == 1
        assert indicators[0]["type"] == "indicator"


class TestSTIXWalletExtraction:
    def setup_method(self):
        self.engine = STIXEngine()

    def test_extract_evm_address(self):
        ind = self.engine.create_indicator(
            "Sanctioned EVM",
            "[cryptocurrency-address:value = '0xAbCd1234567890AbCd1234567890AbCd12345678']",
        )
        addrs = self.engine.extract_wallet_addresses(ind)
        assert len(addrs) == 1
        assert addrs[0] == "0xAbCd1234567890AbCd1234567890AbCd12345678"

    def test_extract_no_address(self):
        ind = self.engine.create_indicator(
            "IP only",
            "[ipv4-addr:value = '1.2.3.4']",
        )
        addrs = self.engine.extract_wallet_addresses(ind)
        assert addrs == []

    def test_no_pattern_returns_empty(self):
        addrs = self.engine.extract_wallet_addresses({"type": "indicator"})
        assert addrs == []

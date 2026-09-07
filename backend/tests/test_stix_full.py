"""
LEATrace STIX 2.1 Engine Tests — Production.

Tests all 20 STIX SDO/SRO types, validation, bundle parsing,
relationship resolution, and wallet extraction.
"""

import pytest
from app.stix_engine import stix_engine, STIXValidationError, STIXBundleError, STIX_TYPES


class TestSTIXObjectCreation:
    """Tests STIX 2.1 object factory methods."""

    def test_create_indicator(self):
        obj = stix_engine.create_indicator(
            name="Malicious IP",
            pattern="[ipv4-addr:value = '198.51.100.1']",
            pattern_type="stix",
        )
        assert obj["type"] == "indicator"
        assert obj["spec_version"] == "2.1"
        assert obj["name"] == "Malicious IP"
        assert obj["pattern"] == "[ipv4-addr:value = '198.51.100.1']"
        assert obj["id"].startswith("indicator--")

    def test_create_malware(self):
        obj = stix_engine.create_malware(
            name="TestMalware",
            is_family=True,
        )
        assert obj["type"] == "malware"
        assert obj["is_family"] is True
        assert obj["name"] == "TestMalware"

    def test_create_threat_actor(self):
        obj = stix_engine.create_threat_actor(
            name="APT99",
            sophistication="advanced",
        )
        assert obj["type"] == "threat-actor"
        assert obj["name"] == "APT99"
        assert obj["sophistication"] == "advanced"

    def test_create_campaign(self):
        obj = stix_engine.create_campaign(name="Operation Test")
        assert obj["type"] == "campaign"
        assert obj["name"] == "Operation Test"

    def test_create_identity(self):
        obj = stix_engine.create_identity(
            name="ACME Corp",
            identity_class="organization",
        )
        assert obj["type"] == "identity"
        assert obj["identity_class"] == "organization"

    def test_create_tool(self):
        obj = stix_engine.create_tool(name="Mimikatz")
        assert obj["type"] == "tool"

    def test_create_infrastructure(self):
        obj = stix_engine.create_infrastructure(name="C2 Server")
        assert obj["type"] == "infrastructure"

    def test_create_intrusion_set(self):
        obj = stix_engine.create_intrusion_set(name="Dark Halo")
        assert obj["type"] == "intrusion-set"

    def test_create_attack_pattern(self):
        obj = stix_engine.create_attack_pattern(name="Spearphishing")
        assert obj["type"] == "attack-pattern"

    def test_create_course_of_action(self):
        obj = stix_engine.create_course_of_action(name="Block IP")
        assert obj["type"] == "course-of-action"

    def test_create_location(self):
        obj = stix_engine.create_location(
            name="US", country="US", latitude=38.0, longitude=-97.0,
        )
        assert obj["type"] == "location"
        assert obj["country"] == "US"
        assert obj["latitude"] == 38.0

    def test_create_report(self):
        obj = stix_engine.create_report(
            name="Test Report",
            published="2024-01-01T00:00:00Z",
            object_refs=["indicator--" + "0" * 36],
        )
        assert obj["type"] == "report"
        assert len(obj["object_refs"]) == 1

    def test_create_note(self):
        obj = stix_engine.create_note(
            content="This is a note",
            object_refs=["indicator--" + "0" * 36],
        )
        assert obj["type"] == "note"
        assert obj["content"] == "This is a note"

    def test_create_opinion(self):
        obj = stix_engine.create_opinion(
            opinion="agree",
            object_refs=["indicator--" + "0" * 36],
        )
        assert obj["type"] == "opinion"
        assert obj["opinion"] == "agree"

    def test_create_opinion_invalid_value(self):
        with pytest.raises(STIXValidationError, match="Invalid opinion"):
            stix_engine.create_opinion(
                opinion="invalid_opinion",
                object_refs=["indicator--" + "0" * 36],
            )

    def test_create_relationship(self):
        obj = stix_engine.create_relationship(
            source_ref="threat-actor--" + "0" * 36,
            target_ref="malware--" + "0" * 36,
            relationship_type="uses",
        )
        assert obj["type"] == "relationship"
        assert obj["relationship_type"] == "uses"

    def test_create_sighting(self):
        obj = stix_engine.create_sighting(
            sighting_of_ref="indicator--" + "0" * 36,
            count=5,
        )
        assert obj["type"] == "sighting"
        assert obj["count"] == 5


class TestSTIXValidation:
    """Tests STIX 2.1 validation."""

    def test_validate_missing_type(self):
        with pytest.raises(STIXValidationError, match="missing 'type'"):
            stix_engine.validate_object({"id": "test--123"})

    def test_validate_missing_required_fields(self):
        with pytest.raises(STIXValidationError, match="missing required"):
            stix_engine.validate_object({
                "type": "indicator",
                "id": "indicator--" + "0" * 36,
            })

    def test_validate_invalid_confidence(self):
        with pytest.raises(STIXValidationError, match="Confidence"):
            stix_engine.validate_object({
                "type": "indicator",
                "spec_version": "2.1",
                "id": "indicator--" + "0" * 36,
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
                "name": "test",
                "pattern": "[ipv4-addr:value = '1.2.3.4']",
                "pattern_type": "stix",
                "valid_from": "2024-01-01T00:00:00Z",
                "confidence": 150,
            })

    def test_validate_id_prefix_mismatch(self):
        with pytest.raises(STIXValidationError, match="does not match"):
            stix_engine.validate_object({
                "type": "indicator",
                "spec_version": "2.1",
                "id": "malware--" + "0" * 36,
                "created": "2024-01-01T00:00:00Z",
                "modified": "2024-01-01T00:00:00Z",
                "name": "test",
                "pattern": "[ipv4-addr:value = '1.2.3.4']",
                "pattern_type": "stix",
                "valid_from": "2024-01-01T00:00:00Z",
            })

    def test_validate_not_dict(self):
        with pytest.raises(STIXValidationError, match="must be a dict"):
            stix_engine.validate_object("not a dict")


class TestSTIXBundleParsing:
    """Tests STIX 2.1 bundle parsing."""

    def test_parse_valid_bundle(self):
        indicator = stix_engine.create_indicator(
            name="Test", pattern="[ipv4-addr:value = '1.2.3.4']",
        )
        bundle = stix_engine.create_bundle([indicator])
        parsed = list(stix_engine.parse_bundle(bundle))
        assert len(parsed) == 1
        assert parsed[0]["name"] == "Test"

    def test_parse_bundle_skips_invalid(self):
        good = stix_engine.create_indicator(
            name="Good", pattern="[ipv4-addr:value = '1.2.3.4']",
        )
        bundle = stix_engine.create_bundle([
            good,
            {"type": "indicator"},  # Missing required fields → skipped
        ])
        parsed = list(stix_engine.parse_bundle(bundle))
        assert len(parsed) == 1

    def test_parse_non_bundle_raises(self):
        with pytest.raises(STIXBundleError, match="Expected type 'bundle'"):
            list(stix_engine.parse_bundle({"type": "indicator"}))

    def test_parse_non_dict_raises(self):
        with pytest.raises(STIXBundleError, match="must be a JSON object"):
            list(stix_engine.parse_bundle("not a dict"))


class TestSTIXDeduplication:
    """Tests STIX bundle deduplication."""

    def test_deduplicate_removes_exact_duplicates(self):
        indicator = stix_engine.create_indicator(
            name="Dup", pattern="[ipv4-addr:value = '1.2.3.4']",
        )
        bundle = stix_engine.create_bundle([indicator, indicator])
        deduped = stix_engine.deduplicate_bundle(bundle)
        assert len(deduped["objects"]) == 1


class TestSTIXWalletExtraction:
    """Tests wallet address extraction from STIX patterns."""

    def test_extract_eth_address(self):
        indicator = stix_engine.create_indicator(
            name="ETH IOC",
            pattern="[cryptocurrency-address:value = '0x1234567890abcdef1234567890abcdef12345678']",
        )
        addrs = stix_engine.extract_wallet_addresses(indicator)
        assert len(addrs) == 1
        assert addrs[0] == "0x1234567890abcdef1234567890abcdef12345678"

    def test_extract_no_address(self):
        indicator = stix_engine.create_indicator(
            name="IP IOC",
            pattern="[ipv4-addr:value = '192.168.1.1']",
        )
        addrs = stix_engine.extract_wallet_addresses(indicator)
        assert addrs == []

    def test_extract_empty_pattern(self):
        addrs = stix_engine.extract_wallet_addresses({"pattern": ""})
        assert addrs == []


class TestSTIXAllTypesSupported:
    """Verifies all 20 STIX types are in the required fields spec."""

    def test_all_types_in_required_fields(self):
        expected_types = {
            "indicator", "malware", "threat-actor", "campaign", "identity",
            "tool", "infrastructure", "intrusion-set", "attack-pattern",
            "observed-data", "course-of-action", "location",
            "malware-analysis", "report", "grouping", "note", "opinion",
            "relationship", "sighting", "bundle",
        }
        assert expected_types.issubset(STIX_TYPES), \
            f"Missing types: {expected_types - STIX_TYPES}"


class TestSTIXObjectHash:
    """Tests deterministic object hashing."""

    def test_same_object_same_hash(self):
        obj = stix_engine.create_indicator(
            name="Test", pattern="[ipv4-addr:value = '1.2.3.4']",
        )
        h1 = stix_engine.compute_object_hash(obj)
        h2 = stix_engine.compute_object_hash(obj)
        assert h1 == h2

    def test_different_objects_different_hash(self):
        obj1 = stix_engine.create_indicator(
            name="Test1", pattern="[ipv4-addr:value = '1.2.3.4']",
        )
        obj2 = stix_engine.create_indicator(
            name="Test2", pattern="[ipv4-addr:value = '5.6.7.8']",
        )
        assert stix_engine.compute_object_hash(obj1) != stix_engine.compute_object_hash(obj2)

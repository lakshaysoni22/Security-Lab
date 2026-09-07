"""
LEATrace Unit Tests — Validators.

Tests for input validation, address format checking,
injection detection, and sanitization.
"""

import pytest
from app.validators import (
    validate_address,
    validate_tx_hash,
    validate_chain_id,
    sanitize_string,
    sanitize_label,
)


class TestEVMAddressValidation:
    """Tests for EVM address validation."""

    def test_valid_ethereum_address(self):
        assert validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28", "ethereum") is True

    def test_valid_lowercase_address(self):
        assert validate_address("0x742d35cc6634c0532925a3b844bc9e7595f2bd28", "ethereum") is True

    def test_invalid_short_address(self):
        assert validate_address("0x742d35Cc", "ethereum") is False

    def test_invalid_no_prefix(self):
        assert validate_address("742d35Cc6634C0532925a3b844Bc9e7595f2bD28", "ethereum") is False

    def test_empty_address(self):
        assert validate_address("", "ethereum") is False

    def test_none_address(self):
        assert validate_address(None, "ethereum") is False

    def test_too_long_address(self):
        assert validate_address("0x" + "a" * 200, "ethereum") is False

    def test_valid_for_polygon(self):
        assert validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28", "polygon") is True

    def test_valid_for_bnb(self):
        assert validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28", "bnb") is True


class TestBitcoinAddressValidation:
    """Tests for Bitcoin address validation."""

    def test_valid_p2pkh(self):
        assert validate_address("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", "bitcoin") is True

    def test_valid_p2sh(self):
        assert validate_address("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", "bitcoin") is True

    def test_valid_bech32(self):
        assert validate_address("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq", "bitcoin") is True

    def test_invalid_bitcoin(self):
        assert validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28", "bitcoin") is False


class TestSolanaAddressValidation:
    """Tests for Solana address validation."""

    def test_valid_solana(self):
        assert validate_address("7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU", "solana") is True

    def test_invalid_solana_too_short(self):
        assert validate_address("7xKXtg2CW87d", "solana") is False


class TestChainDetection:
    """Tests for chain-agnostic validation."""

    def test_evm_detected_without_chain(self):
        assert validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28") is True

    def test_btc_detected_without_chain(self):
        assert validate_address("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2") is True

    def test_gibberish_rejected(self):
        assert validate_address("notanaddress123") is False


class TestTransactionHashValidation:
    """Tests for transaction hash validation."""

    def test_valid_tx_hash(self):
        assert validate_tx_hash("0x" + "a" * 64) is True

    def test_invalid_short_hash(self):
        assert validate_tx_hash("0xabc") is False

    def test_empty_hash(self):
        assert validate_tx_hash("") is False


class TestChainIdValidation:
    """Tests for chain ID validation."""

    def test_valid_chains(self):
        for chain in ["ethereum", "polygon", "bnb", "bitcoin", "solana", "litecoin", "dogecoin"]:
            assert validate_chain_id(chain) is True

    def test_invalid_chain(self):
        assert validate_chain_id("fakecoin") is False


class TestInjectionPrevention:
    """Tests for SQL/Cypher injection detection."""

    def test_sql_injection_in_address(self):
        assert validate_address("'; DROP TABLE users; --", "ethereum") is False

    def test_sql_injection_in_string(self):
        assert sanitize_string("'; DROP TABLE users; --") == ""

    def test_cypher_injection(self):
        assert sanitize_string("DETACH DELETE n") == ""

    def test_path_traversal(self):
        assert sanitize_string("../../etc/passwd") == ""

    def test_clean_string_passes(self):
        assert sanitize_string("Normal search query") == "Normal search query"

    def test_max_length_truncation(self):
        result = sanitize_string("a" * 1000, max_length=50)
        assert len(result) == 50


class TestLabelSanitization:
    """Tests for Neo4j label sanitization."""

    def test_clean_label(self):
        assert sanitize_label("Wallet") == "Wallet"

    def test_label_with_special_chars(self):
        assert sanitize_label("Wallet; DROP") == "WalletDROP"

    def test_empty_label(self):
        assert sanitize_label("") == ""

    def test_max_length(self):
        result = sanitize_label("a" * 100)
        assert len(result) == 64

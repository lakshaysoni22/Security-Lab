"""
LEATrace Unit Tests — Chain Plugins.

Tests for chain interface, registry, address validation,
and chain detection across all 11 supported chains.
"""

import pytest
from app.chains.base import ChainInterface, EVMAddressValidator
from app.chains.evm import EVMChain, EVM_CHAIN_METADATA
from app.chains.bitcoin import BitcoinChain
from app.chains.solana import SolanaChain
from app.chains.litecoin import LitecoinChain
from app.chains.dogecoin import DogecoinChain
from app.chains.registry import ChainRegistry


class TestEVMAddressValidator:
    """Tests for EVM address validation utility."""

    def test_valid_address(self):
        assert EVMAddressValidator.is_valid_evm_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28") is True

    def test_invalid_no_prefix(self):
        assert EVMAddressValidator.is_valid_evm_address("742d35Cc6634C0532925a3b844Bc9e7595f2bD28") is False

    def test_invalid_short(self):
        assert EVMAddressValidator.is_valid_evm_address("0x742d") is False

    def test_empty(self):
        assert EVMAddressValidator.is_valid_evm_address("") is False

    def test_none(self):
        assert EVMAddressValidator.is_valid_evm_address(None) is False


class TestEVMChain:
    """Tests for EVM chain plugin."""

    def test_ethereum_metadata(self):
        chain = EVMChain("ethereum")
        assert chain.chain_id == "ethereum"
        assert chain.display_name == "Ethereum"
        assert chain.native_token == "ETH"
        assert chain.chain_type == "evm"

    def test_polygon_metadata(self):
        chain = EVMChain("polygon")
        assert chain.chain_id == "polygon"
        assert chain.native_token == "MATIC"

    def test_all_evm_chains_exist(self):
        for chain_id in ["ethereum", "polygon", "bnb", "arbitrum", "optimism", "avalanche", "base"]:
            chain = EVMChain(chain_id)
            assert chain.chain_id == chain_id
            assert chain.chain_type == "evm"

    def test_address_validation(self):
        chain = EVMChain("ethereum")
        assert chain.validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28") is True
        assert chain.validate_address("not_an_address") is False

    def test_get_info(self):
        chain = EVMChain("ethereum")
        info = chain.get_info()
        assert info["chain_id"] == "ethereum"
        assert info["native_token"] == "ETH"
        assert info["chain_type"] == "evm"


class TestBitcoinChain:
    """Tests for Bitcoin chain plugin."""

    def test_metadata(self):
        chain = BitcoinChain()
        assert chain.chain_id == "bitcoin"
        assert chain.native_token == "BTC"
        assert chain.chain_type == "utxo"

    def test_p2pkh_validation(self):
        chain = BitcoinChain()
        assert chain.validate_address("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2") is True

    def test_p2sh_validation(self):
        chain = BitcoinChain()
        assert chain.validate_address("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy") is True

    def test_bech32_validation(self):
        chain = BitcoinChain()
        assert chain.validate_address("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq") is True

    def test_evm_address_rejected(self):
        chain = BitcoinChain()
        assert chain.validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28") is False

    def test_is_not_contract(self):
        chain = BitcoinChain()
        assert chain.is_contract("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2") is False


class TestSolanaChain:
    """Tests for Solana chain plugin."""

    def test_metadata(self):
        chain = SolanaChain()
        assert chain.chain_id == "solana"
        assert chain.native_token == "SOL"
        assert chain.chain_type == "account"

    def test_valid_address(self):
        chain = SolanaChain()
        assert chain.validate_address("7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU") is True

    def test_evm_rejected(self):
        chain = SolanaChain()
        assert chain.validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28") is False


class TestLitecoinChain:
    """Tests for Litecoin chain plugin."""

    def test_metadata(self):
        chain = LitecoinChain()
        assert chain.chain_id == "litecoin"
        assert chain.native_token == "LTC"
        assert chain.chain_type == "utxo"

    def test_legacy_address(self):
        chain = LitecoinChain()
        assert chain.validate_address("LaMT348PWRnrqeeWArpwQPbuanpXDZGEUz") is True

    def test_is_not_contract(self):
        chain = LitecoinChain()
        assert chain.is_contract("LaMT348PWRnrqeeWArpwQPbuanpXDZGEUz") is False


class TestDogecoinChain:
    """Tests for Dogecoin chain plugin."""

    def test_metadata(self):
        chain = DogecoinChain()
        assert chain.chain_id == "dogecoin"
        assert chain.native_token == "DOGE"
        assert chain.chain_type == "utxo"

    def test_valid_address(self):
        chain = DogecoinChain()
        assert chain.validate_address("DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L") is True

    def test_is_not_contract(self):
        chain = DogecoinChain()
        assert chain.is_contract("DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L") is False


class TestChainRegistry:
    """Tests for chain registry."""

    def test_registry_initializes(self):
        registry = ChainRegistry()
        chains = registry.get_supported_chain_ids()
        assert len(chains) == 11

    def test_all_chains_present(self):
        registry = ChainRegistry()
        expected = {"ethereum", "polygon", "bnb", "arbitrum", "optimism",
                    "avalanche", "base", "bitcoin", "solana", "litecoin", "dogecoin"}
        assert set(registry.get_supported_chain_ids()) == expected

    def test_get_chain_by_id(self):
        registry = ChainRegistry()
        eth = registry.get_chain("ethereum")
        assert eth is not None
        assert eth.chain_id == "ethereum"

    def test_get_unknown_chain(self):
        registry = ChainRegistry()
        assert registry.get_chain("fakecoin") is None

    def test_case_insensitive(self):
        registry = ChainRegistry()
        assert registry.get_chain("ETHEREUM") is not None

    def test_detect_evm(self):
        registry = ChainRegistry()
        detected = registry.detect_chain("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28")
        assert detected == "ethereum"  # Default for EVM

    def test_detect_bitcoin(self):
        registry = ChainRegistry()
        detected = registry.detect_chain("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq")
        assert detected == "bitcoin"

    def test_detect_unknown(self):
        registry = ChainRegistry()
        detected = registry.detect_chain("not_an_address")
        assert detected is None

    def test_metadata_structure(self):
        registry = ChainRegistry()
        metadata = registry.get_chain_metadata()
        assert len(metadata) == 11
        for m in metadata:
            assert "chain_id" in m
            assert "display_name" in m
            assert "native_token" in m
            assert "chain_type" in m

    def test_validate_address_via_registry(self):
        registry = ChainRegistry()
        assert registry.validate_address("0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28", "ethereum") is True
        assert registry.validate_address("not_valid", "ethereum") is False

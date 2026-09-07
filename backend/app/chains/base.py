"""
LEATrace Chain Plugin — Abstract Base Interface.

All chain implementations must extend this interface.
Each chain provides: address validation, balance queries,
transaction history, contract detection, and block height.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class ChainInterface(ABC):
    """
    Abstract interface for a blockchain chain plugin.

    Each chain must implement all methods. Return empty lists/dicts/None
    when data is unavailable — never fabricate data.
    """

    @property
    @abstractmethod
    def chain_id(self) -> str:
        """Unique chain identifier (e.g., 'ethereum', 'bitcoin', 'solana')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable chain name."""
        ...

    @property
    @abstractmethod
    def native_token(self) -> str:
        """Native token symbol (e.g., 'ETH', 'BTC', 'SOL')."""
        ...

    @property
    @abstractmethod
    def chain_type(self) -> str:
        """Chain type: 'evm', 'utxo', 'account'."""
        ...

    @abstractmethod
    def validate_address(self, address: str) -> bool:
        """
        Validates that an address is correctly formatted for this chain.
        Must check format, length, and checksum where applicable.
        """
        ...

    @abstractmethod
    def get_balance(self, address: str) -> Optional[float]:
        """
        Gets the native token balance for an address.
        Returns None if unavailable.
        """
        ...

    @abstractmethod
    def get_transactions(self, address: str, page: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Gets transaction history for an address.
        Returns normalized transaction dicts with keys:
        - hash, from, to, value, timestamp, status, gas_used (if applicable)
        """
        ...

    @abstractmethod
    def get_block_height(self) -> Optional[int]:
        """Returns the current block height. None if unavailable."""
        ...

    @abstractmethod
    def is_contract(self, address: str) -> bool:
        """Checks if an address is a smart contract (EVM) or program (Solana)."""
        ...

    def get_token_transfers(self, address: str, page: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Gets ERC-20/SPL/TRC-20 token transfers for an address.
        Default: empty list (override in chain implementations that support tokens).
        """
        return []

    def get_info(self) -> Dict[str, Any]:
        """Returns chain metadata."""
        return {
            "chain_id": self.chain_id,
            "display_name": self.display_name,
            "native_token": self.native_token,
            "chain_type": self.chain_type,
        }


class EVMAddressValidator:
    """Shared EVM address validation utilities."""

    _HEX_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")

    @staticmethod
    def is_valid_evm_address(address: str) -> bool:
        """Validates an EVM address (hex format, 42 chars including 0x prefix)."""
        if not address or not EVMAddressValidator._HEX_PATTERN.match(address):
            return False
        return True

    @staticmethod
    def checksum_address(address: str) -> str:
        """Returns EIP-55 checksummed address."""
        import hashlib
        addr = address.lower().replace("0x", "")
        keccak = hashlib.sha3_256(addr.encode()).hexdigest()
        result = "0x"
        for i, char in enumerate(addr):
            if int(keccak[i], 16) >= 8:
                result += char.upper()
            else:
                result += char
        return result

"""
LEATrace Chain Registry — Production.

Central registry of all chain plugins. Provides chain lookup by ID,
address validation across all chains, and chain metadata queries.
"""

import logging
from typing import Dict, List, Optional

from .base import ChainInterface
from .evm import EVMChain
from .bitcoin import BitcoinChain
from .solana import SolanaChain
from .litecoin import LitecoinChain
from .dogecoin import DogecoinChain

logger = logging.getLogger("leatrace.chains.registry")


class ChainRegistry:
    """
    Central registry for all blockchain chain plugins.
    Lazily initializes chain instances on first access.
    """

    def __init__(self):
        self._chains: Dict[str, ChainInterface] = {}
        self._initialized = False

    def _ensure_initialized(self):
        """Lazily initializes all chain plugins."""
        if self._initialized:
            return

        # EVM chains
        for chain_id in ["ethereum", "polygon", "bnb", "arbitrum", "optimism", "avalanche", "base"]:
            self._chains[chain_id] = EVMChain(chain_id)

        # Non-EVM chains
        self._chains["bitcoin"] = BitcoinChain()
        self._chains["solana"] = SolanaChain()
        self._chains["litecoin"] = LitecoinChain()
        self._chains["dogecoin"] = DogecoinChain()

        self._initialized = True
        logger.info(f"Chain registry initialized with {len(self._chains)} chains: {list(self._chains.keys())}")

    def get_chain(self, chain_id: str) -> Optional[ChainInterface]:
        """Gets a chain plugin by ID. Returns None if chain not supported."""
        self._ensure_initialized()
        return self._chains.get(chain_id.lower())

    def get_all_chains(self) -> Dict[str, ChainInterface]:
        """Returns all registered chains."""
        self._ensure_initialized()
        return dict(self._chains)

    def get_supported_chain_ids(self) -> List[str]:
        """Returns list of all supported chain IDs."""
        self._ensure_initialized()
        return list(self._chains.keys())

    def get_chain_metadata(self) -> List[dict]:
        """Returns metadata for all supported chains."""
        self._ensure_initialized()
        return [chain.get_info() for chain in self._chains.values()]

    def validate_address(self, address: str, chain_id: str) -> bool:
        """Validates an address for a specific chain."""
        chain = self.get_chain(chain_id)
        if chain is None:
            return False
        return chain.validate_address(address)

    def detect_chain(self, address: str) -> Optional[str]:
        """
        Attempts to detect which chain an address belongs to based on format.
        Returns chain_id or None if ambiguous/unknown.
        """
        self._ensure_initialized()

        matches = []
        for chain_id, chain in self._chains.items():
            if chain.validate_address(address):
                matches.append(chain_id)

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # EVM addresses match multiple chains — default to ethereum
            if address.startswith("0x"):
                return "ethereum"
            return matches[0]
        return None


# Singleton
chain_registry = ChainRegistry()

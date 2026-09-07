"""
LEATrace Chain Plugin — Dogecoin.

Uses Blockcypher/Blockchair REST APIs for Dogecoin investigation.
UTXO model similar to Bitcoin/Litecoin.
"""

import re
import os
import logging
from typing import List, Dict, Any, Optional

from .base import ChainInterface
from ..connection_pool import connection_pool

logger = logging.getLogger("leatrace.chains.dogecoin")

# Dogecoin address: starts with D or A (multisig), base58
_DOGE_PATTERN = re.compile(r"^[DA9][a-km-zA-HJ-NP-Z1-9]{25,34}$")


class DogecoinChain(ChainInterface):
    """Dogecoin chain plugin using Blockcypher REST API."""

    def __init__(self):
        self._api_url = os.getenv("DOGE_API_URL", "https://api.blockcypher.com/v1/doge/main")

    @property
    def chain_id(self) -> str:
        return "dogecoin"

    @property
    def display_name(self) -> str:
        return "Dogecoin"

    @property
    def native_token(self) -> str:
        return "DOGE"

    @property
    def chain_type(self) -> str:
        return "utxo"

    def validate_address(self, address: str) -> bool:
        """Validates Dogecoin address format (starts with D or A, base58)."""
        if not address:
            return False
        return bool(_DOGE_PATTERN.match(address))

    def get_balance(self, address: str) -> Optional[float]:
        """Gets DOGE balance via Blockcypher."""
        try:
            url = f"{self._api_url}/addrs/{address}/balance"
            data = connection_pool.get_json(url, timeout=8)
            if data and "balance" in data:
                return data["balance"] / 1e8
        except Exception as e:
            logger.debug(f"Dogecoin balance failed: {e}")
        return None

    def get_transactions(self, address: str, page: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """Gets Dogecoin transaction history via Blockcypher."""
        try:
            url = f"{self._api_url}/addrs/{address}/full?limit={min(limit, 50)}"
            data = connection_pool.get_json(url, timeout=10)
            if data and "txs" in data:
                txs = []
                for tx in data["txs"][:limit]:
                    total_output = sum(out.get("value", 0) for out in tx.get("outputs", []))

                    from_addrs = [
                        addr for inp in tx.get("inputs", [])
                        for addr in inp.get("addresses", [])
                    ]
                    to_addrs = [
                        addr for out in tx.get("outputs", [])
                        for addr in out.get("addresses", [])
                    ]

                    txs.append({
                        "hash": tx.get("hash", ""),
                        "from": from_addrs[0] if from_addrs else "coinbase",
                        "to": to_addrs[0] if to_addrs else "unknown",
                        "value": total_output / 1e8,
                        "timestamp": tx.get("confirmed") or tx.get("received"),
                        "status": "confirmed" if tx.get("confirmations", 0) > 0 else "unconfirmed",
                        "fee": tx.get("fees", 0) / 1e8,
                        "chain": "dogecoin",
                        "confirmations": tx.get("confirmations", 0),
                    })
                return txs
        except Exception as e:
            logger.debug(f"Dogecoin tx fetch failed: {e}")
        return []

    def get_block_height(self) -> Optional[int]:
        """Gets current Dogecoin block height."""
        try:
            data = connection_pool.get_json(self._api_url, timeout=5)
            if data and "height" in data:
                return data["height"]
        except Exception:
            pass
        return None

    def is_contract(self, address: str) -> bool:
        """Dogecoin does not have smart contracts."""
        return False

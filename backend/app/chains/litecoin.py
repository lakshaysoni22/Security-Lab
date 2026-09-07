"""
LEATrace Chain Plugin — Litecoin.

Uses Blockchair/Blockcypher REST APIs for Litecoin investigation.
UTXO model similar to Bitcoin.
"""

import re
import os
import logging
from typing import List, Dict, Any, Optional

from .base import ChainInterface
from ..connection_pool import connection_pool

logger = logging.getLogger("leatrace.chains.litecoin")

# Litecoin address patterns
_LTC_LEGACY = re.compile(r"^[LM3][a-km-zA-HJ-NP-Z1-9]{25,34}$")
_LTC_BECH32 = re.compile(r"^ltc1[a-zA-HJ-NP-Z0-9]{25,90}$")


class LitecoinChain(ChainInterface):
    """Litecoin chain plugin using Blockcypher/Blockchair REST APIs."""

    def __init__(self):
        self._api_url = os.getenv("LTC_API_URL", "https://api.blockcypher.com/v1/ltc/main")
        self._blockchair_url = "https://api.blockchair.com/litecoin"

    @property
    def chain_id(self) -> str:
        return "litecoin"

    @property
    def display_name(self) -> str:
        return "Litecoin"

    @property
    def native_token(self) -> str:
        return "LTC"

    @property
    def chain_type(self) -> str:
        return "utxo"

    def validate_address(self, address: str) -> bool:
        """Validates Litecoin address format (Legacy L/M/3 and Bech32 ltc1)."""
        if not address:
            return False
        return bool(_LTC_LEGACY.match(address) or _LTC_BECH32.match(address))

    def get_balance(self, address: str) -> Optional[float]:
        """Gets LTC balance via Blockcypher."""
        try:
            url = f"{self._api_url}/addrs/{address}/balance"
            data = connection_pool.get_json(url, timeout=8)
            if data and "balance" in data:
                return data["balance"] / 1e8  # satoshis to LTC
        except Exception as e:
            logger.debug(f"Litecoin balance failed: {e}")
        return None

    def get_transactions(self, address: str, page: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """Gets Litecoin transaction history via Blockcypher."""
        try:
            url = f"{self._api_url}/addrs/{address}/full?limit={min(limit, 50)}"
            data = connection_pool.get_json(url, timeout=10)
            if data and "txs" in data:
                txs = []
                for tx in data["txs"][:limit]:
                    total_input = sum(inp.get("output_value", 0) for inp in tx.get("inputs", []))
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
                        "chain": "litecoin",
                        "confirmations": tx.get("confirmations", 0),
                    })
                return txs
        except Exception as e:
            logger.debug(f"Litecoin tx fetch failed: {e}")
        return []

    def get_block_height(self) -> Optional[int]:
        """Gets current Litecoin block height via Blockcypher."""
        try:
            data = connection_pool.get_json(self._api_url, timeout=5)
            if data and "height" in data:
                return data["height"]
        except Exception:
            pass
        return None

    def is_contract(self, address: str) -> bool:
        """Litecoin does not have smart contracts."""
        return False

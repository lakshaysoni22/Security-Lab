"""
LEATrace Chain Plugin — Bitcoin (UTXO Model).

Uses Blockstream/Mempool REST APIs for Bitcoin investigation.
Supports address info, transaction history, UTXO queries, and block height.
"""

import re
import os
import logging
from typing import List, Dict, Any, Optional

from .base import ChainInterface
from ..connection_pool import connection_pool

logger = logging.getLogger("leatrace.chains.bitcoin")

# Bitcoin address patterns
_LEGACY_PATTERN = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$")  # P2PKH / P2SH
_BECH32_PATTERN = re.compile(r"^bc1[a-zA-HJ-NP-Z0-9]{25,90}$")       # Bech32 / Bech32m


class BitcoinChain(ChainInterface):
    """Bitcoin chain plugin using Blockstream/Mempool REST APIs."""

    def __init__(self):
        self._api_urls = [
            os.getenv("BTC_API_1", "https://blockstream.info/api"),
            os.getenv("BTC_API_2", "https://mempool.space/api"),
        ]

    @property
    def chain_id(self) -> str:
        return "bitcoin"

    @property
    def display_name(self) -> str:
        return "Bitcoin"

    @property
    def native_token(self) -> str:
        return "BTC"

    @property
    def chain_type(self) -> str:
        return "utxo"

    def validate_address(self, address: str) -> bool:
        """Validates Bitcoin address format (Legacy P2PKH/P2SH and Bech32)."""
        if not address:
            return False
        return bool(_LEGACY_PATTERN.match(address) or _BECH32_PATTERN.match(address))

    def get_balance(self, address: str) -> Optional[float]:
        """Gets BTC balance via address info API."""
        for base_url in self._api_urls:
            try:
                url = f"{base_url}/address/{address}"
                data = connection_pool.get_json(url, timeout=8)
                if data and "chain_stats" in data:
                    funded = data["chain_stats"].get("funded_txo_sum", 0)
                    spent = data["chain_stats"].get("spent_txo_sum", 0)
                    return (funded - spent) / 1e8  # satoshis to BTC
            except Exception:
                continue
        return None

    def get_transactions(self, address: str, page: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """Gets Bitcoin transaction history."""
        for base_url in self._api_urls:
            try:
                url = f"{base_url}/address/{address}/txs"
                data = connection_pool.get_json(url, timeout=10)
                if data and isinstance(data, list):
                    txs = []
                    for tx in data[:limit]:
                        # Calculate value for this address
                        value_in = sum(
                            vin.get("prevout", {}).get("value", 0)
                            for vin in tx.get("vin", [])
                            if vin.get("prevout", {}).get("scriptpubkey_address") == address
                        )
                        value_out = sum(
                            vout.get("value", 0)
                            for vout in tx.get("vout", [])
                            if vout.get("scriptpubkey_address") == address
                        )
                        net_value = (value_out - value_in) / 1e8  # satoshis to BTC

                        # Determine from/to
                        from_addrs = list(set(
                            vin.get("prevout", {}).get("scriptpubkey_address", "unknown")
                            for vin in tx.get("vin", [])
                        ))
                        to_addrs = list(set(
                            vout.get("scriptpubkey_address", "unknown")
                            for vout in tx.get("vout", [])
                        ))

                        status = tx.get("status", {})
                        block_time = status.get("block_time", 0)
                        import datetime
                        try:
                            timestamp = datetime.datetime.fromtimestamp(
                                block_time, tz=datetime.timezone.utc
                            ).isoformat() if block_time else None
                        except (ValueError, OSError):
                            timestamp = None

                        txs.append({
                            "hash": tx.get("txid", ""),
                            "from": from_addrs[0] if from_addrs else "coinbase",
                            "to": to_addrs[0] if to_addrs else "unknown",
                            "value": abs(net_value),
                            "timestamp": timestamp,
                            "status": "confirmed" if status.get("confirmed") else "unconfirmed",
                            "fee": tx.get("fee", 0) / 1e8,
                            "chain": "bitcoin",
                            "inputs": len(tx.get("vin", [])),
                            "outputs": len(tx.get("vout", [])),
                        })
                    return txs
            except Exception as e:
                logger.debug(f"Bitcoin tx fetch failed from {base_url}: {e}")
                continue
        return []

    def get_block_height(self) -> Optional[int]:
        """Gets current Bitcoin block height."""
        for base_url in self._api_urls:
            try:
                url = f"{base_url}/blocks/tip/height"
                data = connection_pool.get_json(url, timeout=5)
                if data and "text" in data:
                    return int(data["text"])
            except Exception:
                continue
        return None

    def is_contract(self, address: str) -> bool:
        """Bitcoin does not have smart contracts in the EVM sense."""
        return False

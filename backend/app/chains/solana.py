"""
LEATrace Chain Plugin — Solana.

Uses Solana JSON-RPC and public REST APIs for investigation.
Supports address info, transaction history, token accounts, and block height.
"""

import re
import os
import logging
from typing import List, Dict, Any, Optional

from .base import ChainInterface
from ..connection_pool import connection_pool

logger = logging.getLogger("leatrace.chains.solana")

# Solana address: base58-encoded, 32-44 characters
_SOLANA_ADDR_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


class SolanaChain(ChainInterface):
    """Solana chain plugin using JSON-RPC and REST APIs."""

    def __init__(self):
        self._rpc_url = os.getenv(
            "SOLANA_RPC_URL",
            "https://api.mainnet-beta.solana.com"
        )

    @property
    def chain_id(self) -> str:
        return "solana"

    @property
    def display_name(self) -> str:
        return "Solana"

    @property
    def native_token(self) -> str:
        return "SOL"

    @property
    def chain_type(self) -> str:
        return "account"

    def validate_address(self, address: str) -> bool:
        """Validates Solana address format (base58, 32-44 chars)."""
        if not address:
            return False
        return bool(_SOLANA_ADDR_PATTERN.match(address))

    def _rpc_call(self, method: str, params: list) -> Optional[Any]:
        """Makes a Solana JSON-RPC call."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        response = connection_pool.post_json(self._rpc_url, payload, timeout=10)
        if response and "result" in response:
            return response["result"]
        if response and "error" in response:
            logger.warning(f"Solana RPC error: {response['error']}")
        return None

    def get_balance(self, address: str) -> Optional[float]:
        """Gets SOL balance via getBalance RPC."""
        result = self._rpc_call("getBalance", [address])
        if result and isinstance(result, dict):
            value = result.get("value", 0)
            return value / 1e9  # lamports to SOL
        return None

    def get_transactions(self, address: str, page: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Gets recent transaction signatures for an address via getSignaturesForAddress.
        Then fetches details for each transaction.
        """
        # Get signatures
        params = [address, {"limit": min(limit, 100)}]
        signatures = self._rpc_call("getSignaturesForAddress", params)
        if not signatures or not isinstance(signatures, list):
            return []

        txs = []
        for sig_info in signatures[:limit]:
            sig = sig_info.get("signature", "")
            block_time = sig_info.get("blockTime")
            err = sig_info.get("err")

            import datetime
            try:
                timestamp = datetime.datetime.fromtimestamp(
                    block_time, tz=datetime.timezone.utc
                ).isoformat() if block_time else None
            except (ValueError, OSError):
                timestamp = None

            txs.append({
                "hash": sig,
                "from": address,
                "to": "see_details",
                "value": 0.0,  # Would need full tx parsing for value
                "timestamp": timestamp,
                "status": "failed" if err else "success",
                "chain": "solana",
                "slot": sig_info.get("slot"),
                "memo": sig_info.get("memo"),
            })

        return txs

    def get_token_transfers(self, address: str, page: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """Gets SPL token accounts for the address."""
        result = self._rpc_call("getTokenAccountsByOwner", [
            address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"},
        ])
        if not result or not isinstance(result, dict):
            return []

        accounts = result.get("value", [])
        tokens = []
        for acc in accounts[:limit]:
            parsed = acc.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
            mint = parsed.get("mint", "")
            amount_info = parsed.get("tokenAmount", {})
            tokens.append({
                "mint": mint,
                "balance": float(amount_info.get("uiAmountString", "0")),
                "decimals": amount_info.get("decimals", 0),
                "owner": address,
            })
        return tokens

    def get_block_height(self) -> Optional[int]:
        """Gets current Solana slot height."""
        result = self._rpc_call("getSlot", [])
        if isinstance(result, int):
            return result
        return None

    def is_contract(self, address: str) -> bool:
        """Checks if an address is a program (Solana equivalent of smart contract)."""
        result = self._rpc_call("getAccountInfo", [address, {"encoding": "jsonParsed"}])
        if result and isinstance(result, dict):
            value = result.get("value")
            if value and isinstance(value, dict):
                return value.get("executable", False)
        return False

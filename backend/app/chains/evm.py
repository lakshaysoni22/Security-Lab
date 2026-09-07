"""
LEATrace Chain Plugin — EVM Chains.

Handles all EVM-compatible chains (Ethereum, Polygon, BNB, Arbitrum,
Optimism, Base, Avalanche) through a unified implementation using
Etherscan-family block explorer APIs and JSON-RPC.
"""

import os
import datetime
import logging
from typing import List, Dict, Any, Optional

from .base import ChainInterface, EVMAddressValidator
from ..connection_pool import connection_pool

logger = logging.getLogger("leatrace.chains.evm")

# Block explorer API gateways per chain
EVM_EXPLORER_APIS = {
    "ethereum": "https://api.etherscan.io/api",
    "polygon": "https://api.polygonscan.com/api",
    "bnb": "https://api.bscscan.com/api",
    "arbitrum": "https://api.arbiscan.io/api",
    "optimism": "https://api-optimistic.etherscan.io/api",
    "avalanche": "https://api.snowtrace.io/api",
    "base": "https://api.basescan.org/api",
}

EVM_CHAIN_METADATA = {
    "ethereum": {"display_name": "Ethereum", "native_token": "ETH"},
    "polygon": {"display_name": "Polygon", "native_token": "MATIC"},
    "bnb": {"display_name": "BNB Smart Chain", "native_token": "BNB"},
    "arbitrum": {"display_name": "Arbitrum One", "native_token": "ETH"},
    "optimism": {"display_name": "Optimism", "native_token": "ETH"},
    "avalanche": {"display_name": "Avalanche C-Chain", "native_token": "AVAX"},
    "base": {"display_name": "Base", "native_token": "ETH"},
}


class EVMChain(ChainInterface):
    """
    Unified EVM chain implementation using Etherscan-family APIs and JSON-RPC.
    Instantiate per chain: EVMChain("ethereum"), EVMChain("polygon"), etc.
    """

    def __init__(self, chain: str, rpc_url: Optional[str] = None):
        self._chain = chain
        meta = EVM_CHAIN_METADATA.get(chain, {"display_name": chain.title(), "native_token": "ETH"})
        self._display_name = meta["display_name"]
        self._native_token = meta["native_token"]
        self._explorer_api = EVM_EXPLORER_APIS.get(chain)

        # RPC URL from env or default
        env_key = f"{chain.upper()}_RPC_URL"
        defaults = {
            "ethereum": "https://cloudflare-eth.com",
            "polygon": "https://polygon-rpc.com",
            "bnb": "https://bsc-dataseed.binance.org",
            "avalanche": "https://api.avax.network/ext/bc/C/rpc",
            "arbitrum": "https://arb1.arbitrum.io/rpc",
            "optimism": "https://mainnet.optimism.io",
            "base": "https://mainnet.base.org",
        }
        self._rpc_url = rpc_url or os.getenv(env_key, defaults.get(chain, ""))

        # Explorer API key from env
        api_key_env = f"{chain.upper()}_EXPLORER_KEY"
        self._api_key = os.getenv(api_key_env, "")

    @property
    def chain_id(self) -> str:
        return self._chain

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def native_token(self) -> str:
        return self._native_token

    @property
    def chain_type(self) -> str:
        return "evm"

    def validate_address(self, address: str) -> bool:
        return EVMAddressValidator.is_valid_evm_address(address)

    def get_balance(self, address: str) -> Optional[float]:
        """Gets native token balance via JSON-RPC eth_getBalance."""
        if not self._rpc_url:
            return None
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1,
        }
        response = connection_pool.post_json(self._rpc_url, payload, timeout=5)
        if response and "result" in response:
            try:
                return int(response["result"], 16) / (10**18)
            except (ValueError, TypeError):
                return None
        return None

    def get_transactions(self, address: str, page: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """Gets transaction history via block explorer API."""
        return self._query_explorer(
            module="account",
            action="txlist",
            address=address,
            page=page,
            offset=limit,
        )

    def get_token_transfers(self, address: str, page: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """Gets ERC-20 token transfers via block explorer API."""
        if not self._explorer_api:
            return []

        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": "0",
            "endblock": "99999999",
            "page": str(page),
            "offset": str(limit),
            "sort": "desc",
        }
        if self._api_key:
            params["apikey"] = self._api_key

        url = f"{self._explorer_api}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        response = connection_pool.get_json(url, timeout=10)
        if response and isinstance(response.get("result"), list):
            transfers = []
            for item in response["result"]:
                try:
                    decimals = int(item.get("tokenDecimal", 18))
                    value = float(item.get("value", 0)) / (10 ** decimals)
                    timestamp = datetime.datetime.fromtimestamp(
                        int(item.get("timeStamp", 0)),
                        tz=datetime.timezone.utc
                    ).isoformat()
                except (ValueError, OSError):
                    value = 0.0
                    timestamp = "1970-01-01T00:00:00+00:00"

                transfers.append({
                    "hash": item.get("hash", ""),
                    "from": item.get("from", ""),
                    "to": item.get("to", ""),
                    "value": value,
                    "symbol": item.get("tokenSymbol", "TOKEN"),
                    "token_name": item.get("tokenName", ""),
                    "contract_address": item.get("contractAddress", ""),
                    "timestamp": timestamp,
                })
            return transfers
        return []

    def get_block_height(self) -> Optional[int]:
        """Gets latest block number via JSON-RPC."""
        if not self._rpc_url:
            return None
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_blockNumber",
            "params": [],
            "id": 1,
        }
        response = connection_pool.post_json(self._rpc_url, payload, timeout=5)
        if response and "result" in response:
            try:
                return int(response["result"], 16)
            except (ValueError, TypeError):
                return None
        return None

    def is_contract(self, address: str) -> bool:
        """Checks if an address has contract code via eth_getCode."""
        if not self._rpc_url:
            return False
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getCode",
            "params": [address, "latest"],
            "id": 1,
        }
        response = connection_pool.post_json(self._rpc_url, payload, timeout=5)
        if response and "result" in response:
            code = response["result"]
            return isinstance(code, str) and len(code) > 3
        return False

    def _query_explorer(self, module: str, action: str, address: str, page: int = 1, offset: int = 50) -> List[Dict[str, Any]]:
        """Queries the Etherscan-family block explorer API."""
        if not self._explorer_api:
            return []

        params = {
            "module": module,
            "action": action,
            "address": address,
            "startblock": "0",
            "endblock": "99999999",
            "page": str(page),
            "offset": str(offset),
            "sort": "desc",
        }
        if self._api_key:
            params["apikey"] = self._api_key

        url = f"{self._explorer_api}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        response = connection_pool.get_json(url, timeout=10)

        if response and isinstance(response.get("result"), list):
            txs = []
            for item in response["result"]:
                try:
                    value_native = float(item.get("value", 0)) / (10**18)
                    gas = float(item.get("gasUsed", 0)) * float(item.get("gasPrice", 0)) / (10**18)
                    timestamp = datetime.datetime.fromtimestamp(
                        int(item.get("timeStamp", 0)),
                        tz=datetime.timezone.utc
                    ).isoformat()
                except (ValueError, OSError):
                    value_native = 0.0
                    gas = 0.0
                    timestamp = "1970-01-01T00:00:00+00:00"

                txs.append({
                    "hash": item.get("hash", ""),
                    "from": item.get("from", "").lower(),
                    "to": (item.get("to", "") or "0x0").lower(),
                    "value": value_native,
                    "timestamp": timestamp,
                    "status": "success" if item.get("txreceipt_status") == "1" else "failed",
                    "gas_used": gas,
                    "block_number": int(item.get("blockNumber", 0)),
                    "chain": self._chain,
                })
            return txs
        return []

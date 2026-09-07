"""
LEATrace Wallet Profiler — Production.

Builds comprehensive wallet profiles from real blockchain data.
Uses chain plugins for multi-chain support and price oracle for USD conversion.

PRODUCTION INVARIANTS:
- All profile data from real blockchain queries.
- No fabricated activity patterns or balances.
- Multi-chain support via chain registry.
"""

import logging
from typing import Dict, Any, Optional, List

from .chains.registry import chain_registry
from .price_oracle import price_oracle

logger = logging.getLogger("leatrace.wallet_profiler")


class WalletProfiler:
    """Production wallet profiling from real blockchain data."""

    def build_profile(self, address: str, chain_id: str = "ethereum") -> Dict[str, Any]:
        """
        Builds a comprehensive wallet profile from real blockchain data.
        Returns honest results — empty fields when data unavailable.
        """
        chain = chain_registry.get_chain(chain_id)
        if chain is None:
            return {
                "address": address,
                "chain": chain_id,
                "error": f"Chain '{chain_id}' not supported",
                "data_available": False,
            }

        # Validate address
        if not chain.validate_address(address):
            return {
                "address": address,
                "chain": chain_id,
                "error": "Invalid address format for this chain",
                "data_available": False,
            }

        # Query real data
        balance = chain.get_balance(address)
        txs = chain.get_transactions(address, page=1, limit=50)
        is_contract = chain.is_contract(address)

        # Compute metrics from real transaction data
        total_txs = len(txs)
        incoming_txs = 0
        outgoing_txs = 0
        total_volume_in = 0.0
        total_volume_out = 0.0
        counterparties = set()
        first_activity = None
        last_activity = None

        addr_lower = address.lower()

        for tx in txs:
            tx_from = tx.get("from", "").lower()
            tx_to = tx.get("to", "").lower()
            timestamp = tx.get("timestamp")

            if tx_from == addr_lower:
                outgoing_txs += 1
                total_volume_out += tx.get("value", 0.0)
                if tx_to:
                    counterparties.add(tx_to)
            else:
                incoming_txs += 1
                total_volume_in += tx.get("value", 0.0)
                counterparties.add(tx_from)

            if timestamp:
                if last_activity is None:
                    last_activity = timestamp
                first_activity = timestamp

        # USD conversion via price oracle
        native_symbol = chain.native_token
        balance_usd = price_oracle.convert_to_usd(balance, native_symbol) if balance is not None else None
        volume_in_usd = price_oracle.convert_to_usd(total_volume_in, native_symbol)
        volume_out_usd = price_oracle.convert_to_usd(total_volume_out, native_symbol)

        # Activity analysis
        activity_level = "inactive"
        if total_txs > 100:
            activity_level = "very_high"
        elif total_txs > 30:
            activity_level = "high"
        elif total_txs > 10:
            activity_level = "moderate"
        elif total_txs > 0:
            activity_level = "low"

        # Token transfers (for chains that support it)
        token_transfers = chain.get_token_transfers(address, page=1, limit=20)

        data_available = total_txs > 0 or (balance is not None and balance > 0)

        return {
            "address": address,
            "chain": chain_id,
            "chain_display": chain.display_name,
            "native_token": native_symbol,
            "data_available": data_available,

            # Balance
            "balance": balance,
            "balance_usd": balance_usd,

            # Transaction metrics
            "total_transactions": total_txs,
            "incoming_txns": incoming_txs,
            "outgoing_txns": outgoing_txs,
            "total_volume_in": round(total_volume_in, 8),
            "total_volume_out": round(total_volume_out, 8),
            "volume_in_usd": volume_in_usd,
            "volume_out_usd": volume_out_usd,

            # Activity
            "first_activity": first_activity,
            "last_activity": last_activity,
            "activity_level": activity_level,
            "unique_counterparties": len(counterparties),

            # Wallet type
            "is_contract": is_contract,
            "wallet_type": "smart_contract" if is_contract else "eoa",

            # Token data
            "token_transfer_count": len(token_transfers),
            "recent_token_transfers": token_transfers[:5],
        }

    def build_multi_chain_profile(self, address: str, chains: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Builds profiles across multiple chains for the same address.
        Useful for EVM addresses that may have activity on multiple L2s.
        """
        if chains is None:
            # Auto-detect chains based on address format
            detected = chain_registry.detect_chain(address)
            if detected and chain_registry.get_chain(detected).chain_type == "evm":
                chains = ["ethereum", "polygon", "bnb", "arbitrum", "optimism", "base", "avalanche"]
            elif detected:
                chains = [detected]
            else:
                return {"address": address, "error": "Cannot detect chain for this address"}

        profiles = {}
        total_balance_usd = 0.0

        for chain_id in chains:
            profile = self.build_profile(address, chain_id)
            if profile.get("data_available"):
                profiles[chain_id] = profile
                if profile.get("balance_usd"):
                    total_balance_usd += profile["balance_usd"]

        return {
            "address": address,
            "chains_queried": chains,
            "chains_with_activity": list(profiles.keys()),
            "total_balance_usd": round(total_balance_usd, 2),
            "profiles": profiles,
        }


# Singleton
wallet_profiler = WalletProfiler()

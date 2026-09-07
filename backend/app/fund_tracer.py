"""
LEATrace Fund Tracer — Production.

Multi-hop forward and backward fund tracing using real transaction data.
Builds evidence-grade trace paths with configurable depth.

PRODUCTION INVARIANTS:
- All trace data from real blockchain queries.
- No fabricated paths or addresses.
- Configurable max depth to prevent infinite recursion.
- Evidence collection with timestamps and tx hashes.
"""

import logging
import hashlib
from typing import Dict, Any, List, Optional, Set
from collections import deque

from .chains.registry import chain_registry
from .price_oracle import price_oracle

logger = logging.getLogger("leatrace.fund_tracer")


class FundTracer:
    """
    Multi-hop fund tracer for blockchain investigation.
    Traces the flow of funds forward (where did the money go)
    or backward (where did the money come from).
    """

    def __init__(self, max_depth: int = 5, max_addresses_per_hop: int = 10):
        self.max_depth = max_depth
        self.max_addresses_per_hop = max_addresses_per_hop

    def trace_forward(
        self,
        address: str,
        chain_id: str = "ethereum",
        depth: int = 3,
        min_value: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Traces funds forward: where did money from this address go?
        Follows outgoing transactions from the source address.
        """
        effective_depth = min(depth, self.max_depth)
        chain = chain_registry.get_chain(chain_id)
        if chain is None:
            return {"error": f"Chain '{chain_id}' not supported"}

        visited: Set[str] = set()
        hops: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []
        queue = deque([(address.lower(), 0)])
        visited.add(address.lower())

        while queue:
            current_addr, current_depth = queue.popleft()
            if current_depth >= effective_depth:
                continue

            txs = chain.get_transactions(current_addr, page=1, limit=50)
            next_addresses = []

            for tx in txs:
                tx_from = tx.get("from", "").lower()
                tx_to = tx.get("to", "").lower()
                value = tx.get("value", 0.0)

                # Only follow outgoing transactions
                if tx_from != current_addr:
                    continue
                if value < min_value:
                    continue
                if not tx_to or tx_to == "0x0":
                    continue

                hop = {
                    "depth": current_depth + 1,
                    "from": tx_from,
                    "to": tx_to,
                    "value": value,
                    "tx_hash": tx.get("hash", ""),
                    "timestamp": tx.get("timestamp"),
                    "chain": chain_id,
                }
                hops.append(hop)

                evidence.append({
                    "type": "transaction",
                    "tx_hash": tx.get("hash", ""),
                    "direction": "forward",
                    "depth": current_depth + 1,
                    "from": tx_from,
                    "to": tx_to,
                    "value": value,
                    "timestamp": tx.get("timestamp"),
                })

                if tx_to not in visited and len(next_addresses) < self.max_addresses_per_hop:
                    next_addresses.append(tx_to)
                    visited.add(tx_to)

            for addr in next_addresses:
                queue.append((addr, current_depth + 1))

        # Build trace summary
        total_value = sum(h["value"] for h in hops)
        native_symbol = chain.native_token if chain else "ETH"
        total_usd = price_oracle.convert_to_usd(total_value, native_symbol)

        trace_id = hashlib.sha256(f"{address}:{chain_id}:forward".encode()).hexdigest()[:12]

        return {
            "trace_id": f"TRC-{trace_id}",
            "direction": "forward",
            "source_address": address,
            "chain": chain_id,
            "depth_requested": depth,
            "depth_reached": max((h["depth"] for h in hops), default=0),
            "total_hops": len(hops),
            "total_addresses_visited": len(visited),
            "total_value_traced": round(total_value, 8),
            "total_value_usd": total_usd,
            "hops": hops,
            "evidence": evidence,
        }

    def trace_backward(
        self,
        address: str,
        chain_id: str = "ethereum",
        depth: int = 3,
        min_value: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Traces funds backward: where did this address get its money?
        Follows incoming transactions to the target address.
        """
        effective_depth = min(depth, self.max_depth)
        chain = chain_registry.get_chain(chain_id)
        if chain is None:
            return {"error": f"Chain '{chain_id}' not supported"}

        visited: Set[str] = set()
        hops: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []
        queue = deque([(address.lower(), 0)])
        visited.add(address.lower())

        while queue:
            current_addr, current_depth = queue.popleft()
            if current_depth >= effective_depth:
                continue

            txs = chain.get_transactions(current_addr, page=1, limit=50)
            next_addresses = []

            for tx in txs:
                tx_from = tx.get("from", "").lower()
                tx_to = tx.get("to", "").lower()
                value = tx.get("value", 0.0)

                # Only follow incoming transactions
                if tx_to != current_addr:
                    continue
                if value < min_value:
                    continue

                hop = {
                    "depth": current_depth + 1,
                    "from": tx_from,
                    "to": tx_to,
                    "value": value,
                    "tx_hash": tx.get("hash", ""),
                    "timestamp": tx.get("timestamp"),
                    "chain": chain_id,
                }
                hops.append(hop)

                evidence.append({
                    "type": "transaction",
                    "tx_hash": tx.get("hash", ""),
                    "direction": "backward",
                    "depth": current_depth + 1,
                    "from": tx_from,
                    "to": tx_to,
                    "value": value,
                    "timestamp": tx.get("timestamp"),
                })

                if tx_from not in visited and len(next_addresses) < self.max_addresses_per_hop:
                    next_addresses.append(tx_from)
                    visited.add(tx_from)

            for addr in next_addresses:
                queue.append((addr, current_depth + 1))

        total_value = sum(h["value"] for h in hops)
        native_symbol = chain.native_token if chain else "ETH"
        total_usd = price_oracle.convert_to_usd(total_value, native_symbol)

        trace_id = hashlib.sha256(f"{address}:{chain_id}:backward".encode()).hexdigest()[:12]

        return {
            "trace_id": f"TRC-{trace_id}",
            "direction": "backward",
            "target_address": address,
            "chain": chain_id,
            "depth_requested": depth,
            "depth_reached": max((h["depth"] for h in hops), default=0),
            "total_hops": len(hops),
            "total_addresses_visited": len(visited),
            "total_value_traced": round(total_value, 8),
            "total_value_usd": total_usd,
            "hops": hops,
            "evidence": evidence,
        }

    def trace_bidirectional(
        self,
        address: str,
        chain_id: str = "ethereum",
        depth: int = 2,
        min_value: float = 0.0,
    ) -> Dict[str, Any]:
        """Traces funds in both directions."""
        forward = self.trace_forward(address, chain_id, depth, min_value)
        backward = self.trace_backward(address, chain_id, depth, min_value)

        return {
            "address": address,
            "chain": chain_id,
            "forward_trace": forward,
            "backward_trace": backward,
            "total_hops": forward.get("total_hops", 0) + backward.get("total_hops", 0),
            "total_addresses": (
                forward.get("total_addresses_visited", 0) +
                backward.get("total_addresses_visited", 0) - 1  # Don't double-count source
            ),
        }


# Singleton
fund_tracer = FundTracer()

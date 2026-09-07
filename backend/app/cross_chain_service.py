"""
LEAtTrace Blockchain Intelligence — Cross-Chain Investigation Engine.

Enterprise cross-chain tracing with multi-chain wallet tracking, bridge tx analysis,
wrapped asset detection, timeline reconstruction, evidence collection, and graph building.
"""

import datetime
import hashlib
import json
from typing import List, Dict, Any, Optional
from .bridge_detector import bridge_detector
from .asset_flow_engine import asset_flow_engine
from .cross_chain_graph import cross_chain_graph
from .entity_resolution import entity_resolution


SUPPORTED_CHAINS = ["ethereum", "polygon", "bnb", "arbitrum", "optimism", "base", "avalanche"]


class CrossChainService:
    """Enterprise cross-chain investigation engine."""

    def trace_cross_chain_movements(self, transactions: List[Dict[str, Any]], address: str) -> Dict[str, Any]:
        """Full cross-chain analysis: bridge detection, asset tracking, timeline, evidence."""
        hops = []
        bridge_events = []
        step = 1
        total_bridged_value = 0.0
        chains_touched = set(["ethereum"])

        for tx in transactions:
            target = tx.get("to", "").lower()
            analysis = bridge_detector.analyze_bridge_transaction(
                to_address=target,
                value_eth=tx.get("value", 0.0),
                sender_address=address,
            )

            if analysis.get("is_bridge"):
                hop = {
                    "step": step,
                    "source_chain": analysis["source_chain"],
                    "destination_chain": analysis["destination_chain"],
                    "bridge_protocol": analysis["protocol"],
                    "bridge_contract": analysis["bridge_name"],
                    "bridge_type": analysis["bridge_type"],
                    "tx_hash": tx.get("hash", ""),
                    "amount_sent": tx.get("value", 0.0),
                    "token": "ETH",
                    "risk_score": analysis["risk_score"],
                    "timestamp": tx.get("timestamp", ""),
                    "estimated_delay_min": analysis.get("avg_delay_minutes", 0),
                }
                hops.append(hop)
                total_bridged_value += tx.get("value", 0.0)
                chains_touched.add(analysis["destination_chain"])
                step += 1

                # Record bridge event
                bridge_events.append({
                    "bridge_name": analysis["bridge_name"],
                    "source_chain": analysis["source_chain"],
                    "destination_chain": analysis["destination_chain"],
                    "amount_eth": tx.get("value", 0.0),
                    "risk_score": analysis["risk_score"],
                    "tx_hash": tx.get("hash", ""),
                    "timestamp": tx.get("timestamp", ""),
                })

        # Asset flow splits
        flows = asset_flow_engine.reconstruct_splits(transactions, address)
        graph = cross_chain_graph.build_flow_graph(hops)

        # Wrapped asset analysis
        wrapped_assets = self._detect_wrapped_in_transfers(transactions)

        # Risk assessment
        chain_hopping_score = self._calculate_hopping_risk(len(hops), len(chains_touched), total_bridged_value)

        # Evidence collection
        evidence = self._collect_evidence(address, hops, chains_touched, total_bridged_value)

        return {
            "address": address,
            "chain_hopping_score": chain_hopping_score,
            "total_hops": len(hops),
            "chains_touched": sorted(chains_touched),
            "total_bridged_value_eth": round(total_bridged_value, 6),
            "hops_timeline": hops,
            "bridge_events": bridge_events,
            "wrapped_assets_detected": wrapped_assets,
            "asset_flow_splits": flows,
            "flow_graph": graph,
            "evidence": evidence,
        }

    def track_wallet_across_chains(self, address: str, blockchain_service=None) -> Dict[str, Any]:
        """Scans the same address on all supported EVM chains for activity."""
        chain_activity = {}

        if blockchain_service:
            for chain in SUPPORTED_CHAINS:
                try:
                    txs = blockchain_service.fetch_real_transactions(address, chain)
                    if txs:
                        chain_activity[chain] = {
                            "active": True,
                            "tx_count": len(txs),
                            "first_tx": txs[-1].get("timestamp") if txs else None,
                            "last_tx": txs[0].get("timestamp") if txs else None,
                        }
                    else:
                        chain_activity[chain] = {"active": False, "tx_count": 0}
                except Exception:
                    chain_activity[chain] = {"active": False, "tx_count": 0, "error": "scan_failed"}
        else:
            for chain in SUPPORTED_CHAINS:
                chain_activity[chain] = {"active": False, "tx_count": 0, "note": "no_blockchain_service"}

        active_chains = [c for c, info in chain_activity.items() if info.get("active")]
        return {
            "address": address,
            "multi_chain": len(active_chains) > 1,
            "active_chains": active_chains,
            "chain_count": len(active_chains),
            "chain_details": chain_activity,
        }

    def build_cross_chain_timeline(self, address: str, all_txs: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Builds a unified timeline of events across all chains."""
        timeline = []
        for chain, txs in all_txs.items():
            for tx in txs:
                event_type = "transfer"
                target = tx.get("to", "").lower()
                if bridge_detector.is_bridge_transaction(target):
                    event_type = "bridge"
                elif entity_resolution.is_mixer(target):
                    event_type = "mixer"
                elif entity_resolution.is_exchange(target):
                    event_type = "exchange_deposit"

                timeline.append({
                    "chain": chain,
                    "event_type": event_type,
                    "tx_hash": tx.get("hash", ""),
                    "from": tx.get("from", ""),
                    "to": tx.get("to", ""),
                    "value_eth": tx.get("value", 0.0),
                    "timestamp": tx.get("timestamp", ""),
                })

        # Sort by timestamp
        timeline.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return timeline

    def _detect_wrapped_in_transfers(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detects wrapped asset interactions in token transfers."""
        wrapped = []
        common_wrapped = ["WETH", "WBTC", "WMATIC", "WAVAX", "WBNB", "stETH", "rETH"]
        for tx in transactions:
            symbol = tx.get("symbol", "")
            if symbol.upper() in common_wrapped:
                info = bridge_detector.detect_wrapped_asset(symbol)
                if info:
                    wrapped.append({
                        "tx_hash": tx.get("hash", ""),
                        "symbol": symbol,
                        "underlying": info["underlying_asset"],
                        "value": tx.get("value", 0.0),
                    })
        return wrapped

    def _calculate_hopping_risk(self, hop_count: int, chain_count: int, total_value: float) -> int:
        """Calculates chain-hopping risk score."""
        if hop_count == 0:
            return 5
        base = min(hop_count * 15, 50)
        chain_bonus = min((chain_count - 1) * 10, 30)
        value_bonus = 20 if total_value > 50 else 10 if total_value > 10 else 0
        return min(base + chain_bonus + value_bonus, 100)

    def _collect_evidence(self, address: str, hops: list, chains: set, total_value: float) -> List[Dict[str, Any]]:
        """Collects forensic evidence from cross-chain activity."""
        evidence = []
        if len(hops) > 0:
            evidence.append({
                "type": "cross_chain_bridge",
                "severity": "high" if len(hops) > 3 else "medium",
                "detail": f"Address used {len(hops)} bridge(s) across {len(chains)} chains, moving {total_value:.4f} ETH",
            })
        if len(chains) > 3:
            evidence.append({
                "type": "multi_chain_activity",
                "severity": "high",
                "detail": f"Activity detected on {len(chains)} separate chains — possible fund obfuscation",
            })
        return evidence


cross_chain_service = CrossChainService()

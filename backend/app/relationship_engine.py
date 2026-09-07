"""
LEAtTrace Blockchain Intelligence — Relationship Engine.

Transaction-based relationship scoring between wallets: frequency, value,
timing, directionality, and entity correlation analysis.
"""

import datetime
from typing import List, Dict, Any, Optional
from .entity_resolution import entity_resolution


class RelationshipEngine:
    """Wallet relationship analysis engine with multi-dimensional scoring."""

    def analyze_relationships(self, address: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Builds a complete relationship map for an address from its transactions."""
        addr_clean = address.strip().lower()
        counterparties: Dict[str, Dict[str, Any]] = {}

        for tx in transactions:
            sender = tx.get("from", "").lower()
            receiver = tx.get("to", "").lower()
            value = tx.get("value", 0.0)
            ts = tx.get("timestamp", "")

            if sender == addr_clean:
                cp = receiver
                direction = "outgoing"
            elif receiver == addr_clean:
                cp = sender
                direction = "incoming"
            else:
                continue

            if cp not in counterparties:
                counterparties[cp] = {
                    "address": cp,
                    "tx_count": 0,
                    "total_value": 0.0,
                    "incoming_count": 0,
                    "outgoing_count": 0,
                    "incoming_value": 0.0,
                    "outgoing_value": 0.0,
                    "first_interaction": ts,
                    "last_interaction": ts,
                    "tx_hashes": [],
                }

            entry = counterparties[cp]
            entry["tx_count"] += 1
            entry["total_value"] += value
            if direction == "outgoing":
                entry["outgoing_count"] += 1
                entry["outgoing_value"] += value
            else:
                entry["incoming_count"] += 1
                entry["incoming_value"] += value
            if ts and (not entry["first_interaction"] or ts < entry["first_interaction"]):
                entry["first_interaction"] = ts
            if ts and (not entry["last_interaction"] or ts > entry["last_interaction"]):
                entry["last_interaction"] = ts
            if len(entry["tx_hashes"]) < 5:
                entry["tx_hashes"].append(tx.get("hash", ""))

        # Score and enrich each relationship
        relationships = []
        for cp_addr, data in counterparties.items():
            entity = entity_resolution.resolve_entity(cp_addr)
            score = self._score_relationship(data)

            relationships.append({
                "counterparty": cp_addr,
                "entity_name": entity["entity_name"] if entity else "Unknown",
                "entity_category": entity.get("category", "unknown") if entity else "unknown",
                "relationship_score": round(score, 1),
                "strength": "strong" if score > 60 else "moderate" if score > 30 else "weak",
                "tx_count": data["tx_count"],
                "total_value_eth": round(data["total_value"], 6),
                "direction": self._classify_direction(data),
                "incoming_count": data["incoming_count"],
                "outgoing_count": data["outgoing_count"],
                "first_interaction": data["first_interaction"],
                "last_interaction": data["last_interaction"],
            })

        # Sort by score
        relationships.sort(key=lambda r: r["relationship_score"], reverse=True)

        return {
            "address": address,
            "total_counterparties": len(relationships),
            "strong_relationships": sum(1 for r in relationships if r["strength"] == "strong"),
            "relationships": relationships[:50],
        }

    def _score_relationship(self, data: Dict[str, Any]) -> float:
        """Multi-factor relationship scoring."""
        tx_score = min(data["tx_count"] / 10.0, 1.0) * 35
        value_score = min(data["total_value"] / 50.0, 1.0) * 30
        bidirectional_bonus = 15 if data["incoming_count"] > 0 and data["outgoing_count"] > 0 else 0
        recency_bonus = 10  # Default medium recency
        frequency_bonus = 10 if data["tx_count"] > 5 else 0
        return min(tx_score + value_score + bidirectional_bonus + recency_bonus + frequency_bonus, 100)

    def _classify_direction(self, data: Dict[str, Any]) -> str:
        """Classifies the relationship direction."""
        if data["incoming_count"] > 0 and data["outgoing_count"] > 0:
            return "bidirectional"
        elif data["outgoing_count"] > 0:
            return "outgoing"
        return "incoming"

    def find_common_counterparties(self, addr_a: str, addr_b: str, txs_a: List[Dict], txs_b: List[Dict]) -> List[str]:
        """Finds addresses that interact with both wallets."""
        cp_a = set()
        cp_b = set()
        a_lower = addr_a.lower()
        b_lower = addr_b.lower()

        for tx in txs_a:
            sender = tx.get("from", "").lower()
            receiver = tx.get("to", "").lower()
            cp_a.add(receiver if sender == a_lower else sender)

        for tx in txs_b:
            sender = tx.get("from", "").lower()
            receiver = tx.get("to", "").lower()
            cp_b.add(receiver if sender == b_lower else sender)

        return sorted(cp_a & cp_b)


relationship_engine = RelationshipEngine()

"""
LEAtTrace Blockchain Intelligence — Laundering Detection Engine.

Production peel chain, smurfing, layering, round-amount structuring,
and timeline reconstruction for anti-money laundering analysis.
"""

from typing import List, Dict, Any


class LaunderingDetectionEngine:
    """Enterprise money laundering pattern detection engine."""

    def detect_peel_chain(self, transactions: List[Dict[str, Any]], address: str) -> Dict[str, Any]:
        """Detects peel chains where large funds are repeatedly split with small change returns."""
        peel_steps = []
        target_addr = address.lower()
        prev_value = None
        step_idx = 1

        for tx in transactions:
            if tx.get("from", "").lower() == target_addr:
                val = tx.get("value", 0.0)
                # Peel pattern: decreasing values sent to different addresses
                if val > 0.01 and val < 500.0:
                    is_peel = False
                    if prev_value is not None and val < prev_value * 0.9:
                        is_peel = True
                    elif prev_value is None and val < 100.0:
                        is_peel = True

                    if is_peel:
                        split_pct = f"{(val / max(prev_value, val)) * 100:.0f}%" if prev_value else "initial"
                        peel_steps.append({
                            "step": step_idx,
                            "sender": target_addr,
                            "receiver": tx.get("to", ""),
                            "amount_sent": round(val, 6),
                            "split_percentage": split_pct,
                            "tx_hash": tx.get("hash", ""),
                            "timestamp": tx.get("timestamp", ""),
                        })
                        step_idx += 1
                    prev_value = val

        total_peeled = sum(s["amount_sent"] for s in peel_steps)
        return {
            "is_peel_chain_active": len(peel_steps) > 2,
            "detected_hops": len(peel_steps),
            "total_peeled_value": round(total_peeled, 6),
            "peel_timeline": peel_steps,
            "confidence": min(0.3 + len(peel_steps) * 0.1, 0.95) if peel_steps else 0.1,
        }

    def detect_smurfing_pattern(self, transactions: List[Dict[str, Any]], address: str, threshold: float = 2.0) -> Dict[str, Any]:
        """Detects structured deposits below reporting thresholds (smurfing/structuring)."""
        target_addr = address.lower()
        structured_txs = []

        for tx in transactions:
            if tx.get("from", "").lower() == target_addr:
                val = tx.get("value", 0.0)
                # Transactions just below a round threshold
                for t in [1.0, 5.0, 10.0, 50.0, 100.0]:
                    if t * 0.85 <= val <= t * 0.99:
                        structured_txs.append({
                            "tx_hash": tx.get("hash", ""),
                            "value": round(val, 6),
                            "near_threshold": t,
                            "timestamp": tx.get("timestamp", ""),
                        })
                        break

        return {
            "is_structuring_detected": len(structured_txs) >= 3,
            "structured_tx_count": len(structured_txs),
            "structured_transactions": structured_txs[:20],
            "confidence": min(0.2 + len(structured_txs) * 0.12, 0.90),
        }

    def detect_layering(self, transactions: List[Dict[str, Any]], address: str) -> Dict[str, Any]:
        """Detects layering: multi-hop value splitting through intermediaries."""
        target_addr = address.lower()
        outgoing = []
        intermediaries = set()

        for tx in transactions:
            sender = tx.get("from", "").lower()
            receiver = tx.get("to", "").lower()
            if sender == target_addr and receiver != target_addr:
                outgoing.append(tx)
                intermediaries.add(receiver)

        # Layering indicator: many unique receivers with similar values
        values = [tx.get("value", 0.0) for tx in outgoing]
        if len(values) < 3:
            return {"is_layering_detected": False, "layer_count": 0, "confidence": 0.1}

        avg_val = sum(values) / len(values)
        similar_count = sum(1 for v in values if abs(v - avg_val) < avg_val * 0.3) if avg_val > 0 else 0
        similarity_ratio = similar_count / len(values) if values else 0

        is_layering = len(intermediaries) >= 4 and similarity_ratio > 0.5

        return {
            "is_layering_detected": is_layering,
            "layer_count": len(intermediaries),
            "unique_intermediaries": len(intermediaries),
            "value_similarity_ratio": round(similarity_ratio, 2),
            "avg_layer_value": round(avg_val, 6),
            "confidence": min(0.3 + similarity_ratio * 0.4, 0.85) if is_layering else 0.15,
        }

    def detect_round_amounts(self, transactions: List[Dict[str, Any]], address: str) -> Dict[str, Any]:
        """Detects suspicious round-amount transactions (structuring indicator)."""
        target_addr = address.lower()
        round_txs = []

        for tx in transactions:
            if tx.get("from", "").lower() == target_addr:
                val = tx.get("value", 0.0)
                # Check if value is a round number
                if val > 0.1 and (val == int(val) or val * 10 == int(val * 10)):
                    round_txs.append({
                        "tx_hash": tx.get("hash", ""),
                        "value": val,
                        "to": tx.get("to", ""),
                        "timestamp": tx.get("timestamp", ""),
                    })

        total_round = sum(t["value"] for t in round_txs)
        ratio = len(round_txs) / max(len(transactions), 1)

        return {
            "round_amount_count": len(round_txs),
            "round_amount_ratio": round(ratio, 2),
            "total_round_value": round(total_round, 6),
            "is_suspicious": ratio > 0.5 and len(round_txs) > 3,
            "round_transactions": round_txs[:20],
        }

    def full_aml_analysis(self, transactions: List[Dict[str, Any]], address: str) -> Dict[str, Any]:
        """Runs all AML detection patterns and produces a composite assessment."""
        peel = self.detect_peel_chain(transactions, address)
        smurf = self.detect_smurfing_pattern(transactions, address)
        layering = self.detect_layering(transactions, address)
        round_amt = self.detect_round_amounts(transactions, address)

        patterns_found = sum([
            peel["is_peel_chain_active"],
            smurf["is_structuring_detected"],
            layering["is_layering_detected"],
            round_amt["is_suspicious"],
        ])

        aml_risk = min(patterns_found * 25, 100)

        return {
            "address": address,
            "aml_risk_score": aml_risk,
            "patterns_detected": patterns_found,
            "risk_level": "critical" if aml_risk >= 75 else "high" if aml_risk >= 50 else "medium" if aml_risk >= 25 else "low",
            "peel_chain": peel,
            "structuring": smurf,
            "layering": layering,
            "round_amounts": round_amt,
        }


laundering_engine = LaunderingDetectionEngine()

"""
LEAtTrace Blockchain Intelligence — Mixer Detection Engine.

Enterprise mixer and privacy pool detection with Tornado Cash, Railgun, Aztec,
smurfing, circular transfers, timing correlation, and confidence scoring.
"""

import hashlib
from typing import List, Dict, Any
from .obfuscation_score import obfuscation_scorer
from .risk_engine import risk_engine
from .laundering_engine import laundering_engine
from .entity_resolution import entity_resolution
from .price_oracle import price_oracle

# Known mixer/privacy pool contracts
MIXER_POOLS = {
    # Tornado Cash
    "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc": {"name": "Tornado.Cash 0.1 ETH", "protocol": "tornado", "denomination": 0.1},
    "0x47ce0dbc5425fd3e2002a290749d5f6e9f6f8594": {"name": "Tornado.Cash 1 ETH", "protocol": "tornado", "denomination": 1.0},
    "0x91054378296ec657a4077c16c85a4cf13e8f8f8f": {"name": "Tornado.Cash 10 ETH", "protocol": "tornado", "denomination": 10.0},
    "0xa160cdab225685da1d56aa342ad8841c3b53f291": {"name": "Tornado.Cash 100 ETH", "protocol": "tornado", "denomination": 100.0},
    "0x71c20e241775e5332f143715df332f143789a71b": {"name": "Tornado.Cash Router", "protocol": "tornado", "denomination": 0},
    # Railgun Privacy
    "0xfa7093cdd9ee6932b4eb2c9e1cde7ce00b1fa4b9": {"name": "Railgun Relay Adapt", "protocol": "railgun", "denomination": 0},
    # Aztec Connect
    "0xff1f2b4adb9df6fc8eafecdcbf96a2b351680455": {"name": "Aztec Connect Bridge", "protocol": "aztec", "denomination": 0},
}

# Smurfing thresholds
SMURF_VALUE_THRESHOLD = 2.0  # ETH
SMURF_TX_COUNT_THRESHOLD = 5
CIRCULAR_HOP_LIMIT = 10


class MixerDetectorService:
    """Enterprise mixer and obfuscation analysis engine."""

    def analyze_address_obfuscation(self, address: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Full obfuscation analysis: mixer, smurfing, circular, peel, timing."""
        addr_clean = address.strip().lower()

        # 1. Direct mixer detection
        mixer_txs = self._detect_mixer_interactions(addr_clean, transactions)

        # 2. Smurfing detection
        smurfing = self._detect_smurfing(addr_clean, transactions)

        # 3. Circular transfer detection
        circular = self._detect_circular_transfers(addr_clean, transactions)

        # 4. Rapid splitting/consolidation
        rapid = self._detect_rapid_patterns(addr_clean, transactions)

        # 5. Peel chain detection
        peel = laundering_engine.detect_peel_chain(transactions, addr_clean)

        # 6. Timing analysis
        timing = self._timing_analysis(transactions)

        # Calculate total mixed volume
        mixed_volume = sum(tx.get("amount", 0.0) for tx in mixer_txs)

        # Composite scores
        pattern_count = sum([
            len(mixer_txs) > 0,
            smurfing["is_smurfing"],
            circular["has_circular"],
            rapid["has_rapid_splitting"],
            peel["is_peel_chain_active"],
        ])

        obf_score = obfuscation_scorer.calculate_score(
            mixer_hops=len(mixer_txs),
            peel_splits=peel["detected_hops"],
            smurf_count=smurfing["smurf_tx_count"],
            circular_count=circular["circular_count"],
            rapid_split=rapid["has_rapid_splitting"],
        )

        risk_score = risk_engine.evaluate_risk(
            obf_score if len(mixer_txs) > 0 else 10.0,
            peel["is_peel_chain_active"]
        )

        # Confidence: more patterns detected → higher confidence
        confidence = min(0.3 + pattern_count * 0.15, 0.98)

        return {
            "address": address,
            "has_mixer_interaction": len(mixer_txs) > 0,
            "obfuscation_probability_score": round(obf_score, 1),
            "mixer_exposure_risk_score": round(risk_score, 1),
            "confidence": round(confidence, 2),
            "total_mixed_value_eth": round(mixed_volume, 6),
            "total_mixed_value_usd": price_oracle.convert_to_usd(mixed_volume, "ETH"),
            "patterns_detected": {
                "mixer_deposits": len(mixer_txs) > 0,
                "smurfing": smurfing["is_smurfing"],
                "circular_transfers": circular["has_circular"],
                "rapid_splitting": rapid["has_rapid_splitting"],
                "peel_chain": peel["is_peel_chain_active"],
            },
            "pattern_count": pattern_count,
            "mixer_deposits": mixer_txs,
            "smurfing_analysis": smurfing,
            "circular_analysis": circular,
            "rapid_pattern_analysis": rapid,
            "peel_chain": peel,
            "timing_analysis": timing,
        }

    def _detect_mixer_interactions(self, address: str, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detects direct interactions with known mixer contracts."""
        mixer_txs = []
        for tx in transactions:
            target = tx.get("to", "").lower()
            if target in MIXER_POOLS:
                pool_info = MIXER_POOLS[target]
                mixer_txs.append({
                    "deposit_tx": tx.get("hash"),
                    "amount": tx.get("value", 0.0),
                    "pool": pool_info["name"],
                    "protocol": pool_info["protocol"],
                    "denomination": pool_info["denomination"],
                    "timestamp": tx.get("timestamp"),
                    "confidence": 0.95,
                })
            # Also check entity resolution for mixer categorization
            elif entity_resolution.is_mixer(target):
                entity = entity_resolution.resolve_entity(target)
                mixer_txs.append({
                    "deposit_tx": tx.get("hash"),
                    "amount": tx.get("value", 0.0),
                    "pool": entity["entity_name"] if entity else "Unknown Mixer",
                    "protocol": "unknown",
                    "timestamp": tx.get("timestamp"),
                    "confidence": 0.80,
                })

        return mixer_txs

    def _detect_smurfing(self, address: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detects structured small deposits designed to avoid detection thresholds."""
        small_outgoing = []
        for tx in transactions:
            if tx.get("from", "").lower() == address:
                value = tx.get("value", 0.0)
                if 0.01 < value <= SMURF_VALUE_THRESHOLD:
                    small_outgoing.append({
                        "tx_hash": tx.get("hash"),
                        "value": value,
                        "to": tx.get("to", ""),
                        "timestamp": tx.get("timestamp"),
                    })

        is_smurfing = len(small_outgoing) >= SMURF_TX_COUNT_THRESHOLD
        return {
            "is_smurfing": is_smurfing,
            "smurf_tx_count": len(small_outgoing),
            "threshold_value": SMURF_VALUE_THRESHOLD,
            "total_smurfed_value": round(sum(t["value"] for t in small_outgoing), 6),
            "smurf_transactions": small_outgoing[:20],
            "confidence": 0.7 if is_smurfing else 0.2,
        }

    def _detect_circular_transfers(self, address: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detects funds returning to the original address through intermediaries."""
        sent_to = set()
        received_from = set()

        for tx in transactions:
            sender = tx.get("from", "").lower()
            receiver = tx.get("to", "").lower()
            if sender == address:
                sent_to.add(receiver)
            elif receiver == address:
                received_from.add(sender)

        # Circular: addresses that both received from AND sent to this address
        circular_addresses = sent_to & received_from
        has_circular = len(circular_addresses) > 0

        return {
            "has_circular": has_circular,
            "circular_count": len(circular_addresses),
            "circular_addresses": list(circular_addresses)[:10],
            "confidence": min(0.3 + len(circular_addresses) * 0.15, 0.90),
        }

    def _detect_rapid_patterns(self, address: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detects rapid fund splitting (distribute fast) and consolidation (collect fast)."""
        outgoing_timestamps = []
        incoming_timestamps = []

        for tx in transactions:
            ts = tx.get("timestamp", "")
            sender = tx.get("from", "").lower()
            if sender == address:
                outgoing_timestamps.append(ts)
            else:
                incoming_timestamps.append(ts)

        # Rapid splitting: many outgoing txs in short window
        rapid_split = len(outgoing_timestamps) > 5 and len(outgoing_timestamps) > len(incoming_timestamps) * 2
        # Rapid consolidation: many incoming txs in short window
        rapid_consolidation = len(incoming_timestamps) > 5 and len(incoming_timestamps) > len(outgoing_timestamps) * 2

        return {
            "has_rapid_splitting": rapid_split,
            "has_rapid_consolidation": rapid_consolidation,
            "outgoing_count": len(outgoing_timestamps),
            "incoming_count": len(incoming_timestamps),
            "confidence": 0.6 if (rapid_split or rapid_consolidation) else 0.2,
        }

    def _timing_analysis(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes transaction timing patterns for suspicious activity."""
        if len(transactions) < 3:
            return {"pattern": "insufficient_data", "suspicious": False}

        hours = []
        for tx in transactions:
            ts = tx.get("timestamp", "")
            if ts:
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(ts.rstrip("Z"))
                    hours.append(dt.hour)
                except (ValueError, TypeError):
                    pass

        if not hours:
            return {"pattern": "no_timestamps", "suspicious": False}

        night_txs = sum(1 for h in hours if h < 5 or h > 23)
        night_ratio = night_txs / len(hours)

        return {
            "total_analyzed": len(hours),
            "night_transactions": night_txs,
            "night_ratio": round(night_ratio, 2),
            "pattern": "night_heavy" if night_ratio > 0.5 else "normal",
            "suspicious": night_ratio > 0.5,
        }


mixer_detector = MixerDetectorService()

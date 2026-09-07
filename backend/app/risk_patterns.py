"""
LEAtTrace Blockchain Intelligence — Risk Patterns Library.

Enumeration of all known laundering/obfuscation patterns with pattern matching,
confidence scoring, and combination analysis for forensic investigation.
"""

from typing import List, Dict, Any


# ===================================================================
# Pattern Definitions
# ===================================================================

RISK_PATTERNS = {
    "peel_chain": {
        "id": "PEEL_CHAIN",
        "name": "Peel Chain",
        "description": "Large funds repeatedly split into smaller amounts through intermediary wallets",
        "category": "laundering",
        "severity": "high",
        "indicators": ["decreasing_outgoing_values", "many_unique_receivers", "sequential_timing"],
        "min_confidence": 0.4,
    },
    "smurfing": {
        "id": "SMURFING",
        "name": "Smurfing / Structuring",
        "description": "Multiple small transactions designed to stay below reporting thresholds",
        "category": "structuring",
        "severity": "high",
        "indicators": ["many_small_deposits", "values_below_threshold", "regular_intervals"],
        "min_confidence": 0.5,
    },
    "layering": {
        "id": "LAYERING",
        "name": "Layering",
        "description": "Multi-hop transfers through intermediaries to obscure fund origin",
        "category": "laundering",
        "severity": "critical",
        "indicators": ["many_intermediaries", "similar_values", "rapid_forwarding"],
        "min_confidence": 0.5,
    },
    "circular_transfer": {
        "id": "CIRCULAR",
        "name": "Circular Transfer",
        "description": "Funds routed through intermediaries and returned to original sender",
        "category": "obfuscation",
        "severity": "high",
        "indicators": ["funds_return_to_origin", "intermediary_wallets", "short_time_window"],
        "min_confidence": 0.4,
    },
    "mixer_usage": {
        "id": "MIXER",
        "name": "Mixer / Privacy Pool",
        "description": "Direct interaction with known mixing services (Tornado Cash, Railgun, etc.)",
        "category": "obfuscation",
        "severity": "critical",
        "indicators": ["known_mixer_contract", "fixed_denomination", "deposit_withdraw_pattern"],
        "min_confidence": 0.9,
    },
    "rapid_consolidation": {
        "id": "RAPID_CONSOL",
        "name": "Rapid Consolidation",
        "description": "Many small inputs quickly consolidated into a single wallet",
        "category": "collection",
        "severity": "medium",
        "indicators": ["many_senders", "single_receiver", "short_time_window"],
        "min_confidence": 0.5,
    },
    "rapid_distribution": {
        "id": "RAPID_DIST",
        "name": "Rapid Distribution",
        "description": "Large amount quickly split to many receivers",
        "category": "distribution",
        "severity": "medium",
        "indicators": ["single_sender", "many_receivers", "similar_values", "short_time_window"],
        "min_confidence": 0.5,
    },
    "chain_hopping": {
        "id": "CHAIN_HOP",
        "name": "Chain Hopping",
        "description": "Funds moved across multiple blockchain networks to obscure trail",
        "category": "obfuscation",
        "severity": "high",
        "indicators": ["bridge_transactions", "multiple_chains", "value_preservation"],
        "min_confidence": 0.6,
    },
    "round_amount_structuring": {
        "id": "ROUND_AMT",
        "name": "Round Amount Structuring",
        "description": "Suspicious pattern of round-number transactions",
        "category": "structuring",
        "severity": "medium",
        "indicators": ["round_values", "consistent_pattern", "multiple_recipients"],
        "min_confidence": 0.3,
    },
    "dust_attack": {
        "id": "DUST_ATTACK",
        "name": "Dust Attack",
        "description": "Tiny amounts sent to many addresses for tracking/deanonymization",
        "category": "surveillance",
        "severity": "low",
        "indicators": ["very_small_values", "many_receivers", "no_prior_relationship"],
        "min_confidence": 0.4,
    },
}


class RiskPatternEngine:
    """Pattern matching engine for blockchain investigation."""

    def get_all_patterns(self) -> List[Dict[str, Any]]:
        """Returns all known risk patterns."""
        return list(RISK_PATTERNS.values())

    def get_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """Returns a specific pattern by ID."""
        return RISK_PATTERNS.get(pattern_id, {})

    def match_patterns(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Matches detected patterns from analysis results and returns findings."""
        matched = []

        patterns = analysis_results.get("patterns_detected", {})
        if patterns.get("mixer_deposits"):
            matched.append({**RISK_PATTERNS["mixer_usage"], "confidence": 0.95, "matched": True})
        if patterns.get("smurfing"):
            matched.append({**RISK_PATTERNS["smurfing"], "confidence": 0.70, "matched": True})
        if patterns.get("circular_transfers"):
            matched.append({**RISK_PATTERNS["circular_transfer"], "confidence": 0.65, "matched": True})
        if patterns.get("rapid_splitting"):
            matched.append({**RISK_PATTERNS["rapid_distribution"], "confidence": 0.60, "matched": True})
        if patterns.get("peel_chain"):
            matched.append({**RISK_PATTERNS["peel_chain"], "confidence": 0.70, "matched": True})

        return matched

    def calculate_combined_risk(self, matched_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates combined risk from multiple matched patterns."""
        if not matched_patterns:
            return {"combined_risk": 0, "risk_level": "low", "pattern_count": 0}

        severity_weights = {"critical": 30, "high": 20, "medium": 10, "low": 5}
        total_weight = sum(severity_weights.get(p.get("severity", "low"), 5) for p in matched_patterns)
        combined = min(total_weight, 100)

        return {
            "combined_risk": combined,
            "risk_level": "critical" if combined >= 75 else "high" if combined >= 50 else "medium" if combined >= 25 else "low",
            "pattern_count": len(matched_patterns),
            "most_severe": max(matched_patterns, key=lambda p: severity_weights.get(p.get("severity", "low"), 0))["name"] if matched_patterns else "none",
        }


risk_pattern_engine = RiskPatternEngine()

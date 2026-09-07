"""
LEAtTrace Blockchain Intelligence — Obfuscation Score Calculator.

Multi-factor obfuscation scoring across mixer, peel chain, smurfing, circular,
and rapid splitting patterns with confidence intervals.
"""


class ObfuscationScoreCalculator:
    """Multi-factor obfuscation scoring engine."""

    def calculate_score(
        self,
        mixer_hops: int = 0,
        peel_splits: int = 0,
        smurf_count: int = 0,
        circular_count: int = 0,
        rapid_split: bool = False,
    ) -> float:
        """Computes composite obfuscation percentage from multiple pattern signals."""
        score = 0.0

        # Mixer interaction (strongest signal)
        score += min(mixer_hops * 20.0, 40.0)

        # Peel chain (strong signal)
        score += min(peel_splits * 8.0, 25.0)

        # Smurfing (medium signal)
        score += min(smurf_count * 4.0, 15.0)

        # Circular transfers (medium signal)
        score += min(circular_count * 5.0, 10.0)

        # Rapid splitting/consolidation
        if rapid_split:
            score += 10.0

        return min(score, 100.0)

    def get_confidence_interval(self, score: float, data_points: int) -> dict:
        """Returns confidence interval for the obfuscation score."""
        if data_points < 5:
            margin = 25.0
        elif data_points < 20:
            margin = 15.0
        else:
            margin = 8.0

        return {
            "score": round(score, 1),
            "lower_bound": round(max(score - margin, 0.0), 1),
            "upper_bound": round(min(score + margin, 100.0), 1),
            "confidence": "low" if data_points < 5 else "medium" if data_points < 20 else "high",
        }


obfuscation_scorer = ObfuscationScoreCalculator()

"""Tiering logic for backup selection."""


def classify_tier(signal_score: float, ai_score: float, confidence: float) -> str:
    """Classify a path candidate into tier1/tier2/tier3."""
    if confidence < 0.6:
        return "tier2"
    score = (signal_score + ai_score) / 2.0
    if score >= 0.75:
        return "tier1"
    if score >= 0.4:
        return "tier2"
    return "tier3"

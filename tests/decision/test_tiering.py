from ark.decision.tiering import classify_tier


def test_classify_tier_routes_low_confidence_to_tier2() -> None:
    tier = classify_tier(signal_score=0.9, ai_score=0.2, confidence=0.4)
    assert tier == "tier2"

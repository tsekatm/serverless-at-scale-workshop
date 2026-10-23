"""FAN-IN: combine the three check results into one risk score."""
WEIGHTS = {"sanctions": 0.4, "credit": 0.3, "news": 0.3}


def combine(checks):
    scores = {c["check"]: c["score"] for c in checks}
    if scores["sanctions"] == 100:  # a confirmed sanctions match overrides everything
        return 100, "HIGH"
    total = int(sum(scores[name] * weight for name, weight in WEIGHTS.items()) + 0.5)
    if total >= 60:
        return total, "HIGH"
    if total >= 30:
        return total, "MEDIUM"
    return total, "LOW"

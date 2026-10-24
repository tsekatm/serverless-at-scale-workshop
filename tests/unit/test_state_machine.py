import json
from pathlib import Path

ASL = Path(__file__).resolve().parents[2] / "statemachine" / "supplier_risk.asl.json"


def test_score_step_retries_while_a_duplicate_is_in_progress():
    states = json.loads(ASL.read_text())["States"]
    retries = states["CalculateRiskScore"]["Retry"]
    rule = next(r for r in retries if "IdempotencyAlreadyInProgressError" in r["ErrorEquals"])
    assert 1 <= rule["MaxAttempts"] <= 5

import importlib.util
import json
from pathlib import Path

import pytest

import notifier

ROOT = Path(__file__).resolve().parents[2]


def sqs_event(*bodies):
    return {
        "Records": [
            {
                "messageId": f"msg-{i}",
                "receiptHandle": "rh",
                "body": json.dumps(body),
                "attributes": {"ApproximateReceiveCount": "1"},
                "messageAttributes": {},
                "md5OfBody": "x",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:eu-west-1:123456789012:alerts",
                "awsRegion": "eu-west-1",
            }
            for i, body in enumerate(bodies)
        ]
    }


GOOD = {"supplier_id": "SUP004", "supplier_name": "Highveld Electronics", "risk_level": "HIGH", "risk_score": 63}
LEGACY = {"supplierId": "SUP002", "supplierName": "Karoo Packaging Co", "riskLevel": "MEDIUM", "riskScore": 47}


def test_valid_alert_is_processed(lambda_context):
    assert notifier.handler(sqs_event(GOOD), lambda_context) == {"batchItemFailures": []}


def test_legacy_format_fails_only_that_message(lambda_context):
    result = notifier.handler(sqs_event(GOOD, LEGACY), lambda_context)
    assert result == {"batchItemFailures": [{"itemIdentifier": "msg-1"}]}


def test_normalise_legacy_converts_camel_case():
    assert notifier.normalise_legacy(LEGACY) == {
        "supplier_id": "SUP002",
        "supplier_name": "Karoo Packaging Co",
        "risk_level": "MEDIUM",
        "risk_score": 47,
    }


def test_normalise_legacy_leaves_new_format_alone():
    assert notifier.normalise_legacy(GOOD) == GOOD


def test_solution_notifier_accepts_legacy_format(lambda_context):
    spec = importlib.util.spec_from_file_location("solution_notifier", ROOT / "solution" / "notifier.py")
    solution = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(solution)

    assert solution.handler(sqs_event(GOOD, LEGACY), lambda_context) == {"batchItemFailures": []}

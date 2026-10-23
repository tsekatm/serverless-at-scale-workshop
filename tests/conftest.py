import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("POWERTOOLS_SERVICE_NAME", "supplier-risk-tests")


class FakeLambdaContext:
    function_name = "test-function"
    memory_limit_in_mb = 256
    invoked_function_arn = "arn:aws:lambda:eu-west-1:123456789012:function:test-function"
    aws_request_id = "test-request-id"

    def get_remaining_time_in_millis(self):
        return 10_000


@pytest.fixture
def lambda_context():
    return FakeLambdaContext()


def supplier_event(supplier_id="SUP004", request_id="req-001"):
    """The event EventBridge hands to Step Functions."""
    return {
        "source": "workshop.suppliers",
        "detail-type": "SupplierRiskCheckRequested",
        "detail": {"supplier_id": supplier_id, "request_id": request_id},
    }

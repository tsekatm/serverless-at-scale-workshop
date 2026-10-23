"""FAN-OUT: three independent checks that Step Functions runs in parallel.

Each check is mocked from suppliers.json so the workshop needs no API keys.
In a real system these would call a sanctions list, a credit bureau and a news feed.
"""
from aws_lambda_powertools import Logger

from suppliers import UnknownSupplierError, get_supplier  # noqa: F401 (re-exported for tests)

logger = Logger()

SANCTIONS_SCORES = {"clear": 0, "potential_match": 60, "confirmed_match": 100}
CREDIT_SCORES = {"A": 5, "B": 20, "C": 45, "D": 70, "E": 90}
NEWS_SCORES = {"low": 20, "medium": 50, "high": 85}


def _result(check, supplier, score, finding):
    result = {"check": check, "supplier_id": supplier["supplier_id"], "score": score, "finding": finding}
    logger.info("Check complete", extra=result)
    return result


@logger.inject_lambda_context
def sanctions_handler(event, context):
    supplier = get_supplier(event["detail"]["supplier_id"])
    sanctions = supplier["sanctions"]
    return _result("sanctions", supplier, SANCTIONS_SCORES[sanctions["status"]], sanctions["detail"])


@logger.inject_lambda_context
def credit_handler(event, context):
    supplier = get_supplier(event["detail"]["supplier_id"])
    credit = supplier["credit"]
    return _result("credit", supplier, CREDIT_SCORES[credit["rating"]], f"Rating {credit['rating']}: {credit['detail']}")


@logger.inject_lambda_context
def news_handler(event, context):
    supplier = get_supplier(event["detail"]["supplier_id"])
    if not supplier["news"]:
        return _result("news", supplier, 0, "No relevant news")
    worst = max(supplier["news"], key=lambda item: NEWS_SCORES[item["severity"]])
    return _result("news", supplier, NEWS_SCORES[worst["severity"]], worst["headline"])

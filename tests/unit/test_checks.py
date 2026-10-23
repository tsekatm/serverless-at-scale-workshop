import pytest

import checks
from tests.conftest import supplier_event


def test_sanctions_clear_supplier_scores_zero(lambda_context):
    result = checks.sanctions_handler(supplier_event("SUP001"), lambda_context)
    assert result == {
        "check": "sanctions",
        "supplier_id": "SUP001",
        "score": 0,
        "finding": "No watchlist matches",
    }


def test_sanctions_potential_match_scores_60(lambda_context):
    assert checks.sanctions_handler(supplier_event("SUP004"), lambda_context)["score"] == 60


def test_sanctions_confirmed_match_scores_100(lambda_context):
    assert checks.sanctions_handler(supplier_event("SUP010"), lambda_context)["score"] == 100


@pytest.mark.parametrize("supplier_id,expected", [("SUP001", 5), ("SUP003", 20), ("SUP004", 45), ("SUP002", 70)])
def test_credit_score_follows_rating(supplier_id, expected, lambda_context):
    result = checks.credit_handler(supplier_event(supplier_id), lambda_context)
    assert result["check"] == "credit"
    assert result["score"] == expected


def test_news_uses_most_severe_headline(lambda_context):
    result = checks.news_handler(supplier_event("SUP004"), lambda_context)
    assert result["check"] == "news"
    assert result["score"] == 85
    assert "Labour strike" in result["finding"]


def test_news_with_no_headlines_scores_zero(lambda_context):
    result = checks.news_handler(supplier_event("SUP001"), lambda_context)
    assert result["score"] == 0
    assert result["finding"] == "No relevant news"


def test_unknown_supplier_raises(lambda_context):
    with pytest.raises(checks.UnknownSupplierError):
        checks.sanctions_handler(supplier_event("SUP999"), lambda_context)

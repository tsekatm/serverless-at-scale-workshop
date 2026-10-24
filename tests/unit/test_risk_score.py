import importlib
import json
import os

import boto3
import pytest
from moto import mock_aws

from tests.conftest import supplier_event


def checks_for(sanctions, credit, news, supplier_id="SUP004"):
    return [
        {"check": "sanctions", "supplier_id": supplier_id, "score": sanctions, "finding": "s"},
        {"check": "credit", "supplier_id": supplier_id, "score": credit, "finding": "c"},
        {"check": "news", "supplier_id": supplier_id, "score": news, "finding": "n"},
    ]


def test_weighted_score_and_level():
    import scoring

    assert scoring.combine(checks_for(60, 45, 85)) == (63, "HIGH")
    assert scoring.combine(checks_for(0, 20, 50)) == (21, "LOW")
    assert scoring.combine(checks_for(0, 70, 85)) == (47, "MEDIUM")


def test_confirmed_sanctions_match_is_always_high():
    import scoring

    assert scoring.combine(checks_for(100, 5, 0)) == (100, "HIGH")


@pytest.fixture
def aws(monkeypatch):
    with mock_aws():
        ddb = boto3.client("dynamodb")
        ddb.create_table(
            TableName="idempotency",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        ddb.create_table(
            TableName="scores",
            KeySchema=[{"AttributeName": "score_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "score_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        sns = boto3.client("sns")
        sqs = boto3.client("sqs")
        topic_arn = sns.create_topic(Name="alerts")["TopicArn"]
        queue_url = sqs.create_queue(QueueName="alerts")["QueueUrl"]
        queue_arn = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
        sns.subscribe(TopicArn=topic_arn, Protocol="sqs", Endpoint=queue_arn, Attributes={"RawMessageDelivery": "true"})

        monkeypatch.setenv("IDEMPOTENCY_TABLE", "idempotency")
        monkeypatch.setenv("SCORES_TABLE", "scores")
        monkeypatch.setenv("ALERTS_TOPIC_ARN", topic_arn)
        import risk_score

        importlib.reload(risk_score)
        yield {"ddb": ddb, "sqs": sqs, "queue_url": queue_url, "module": risk_score}


def score_input(supplier_id="SUP004", request_id="req-001"):
    event = supplier_event(supplier_id, request_id)
    event["checks"] = checks_for(60, 45, 85, supplier_id)
    return event


def count_messages(aws):
    msgs = aws["sqs"].receive_message(QueueUrl=aws["queue_url"], MaxNumberOfMessages=10).get("Messages", [])
    return [json.loads(m["Body"]) for m in msgs]


def test_score_is_saved_and_published(aws, lambda_context):
    result = aws["module"].handler(score_input(), lambda_context)

    assert result["supplier_id"] == "SUP004"
    assert result["supplier_name"] == "Highveld Electronics"
    assert result["risk_score"] == 63
    assert result["risk_level"] == "HIGH"
    assert result["open_po_value_zar"] == 52600000
    assert aws["ddb"].scan(TableName="scores")["Count"] == 1
    messages = count_messages(aws)
    assert len(messages) == 1
    assert messages[0]["supplier_id"] == "SUP004"
    assert messages[0]["risk_level"] == "HIGH"


def test_same_request_twice_creates_one_score(aws, lambda_context):
    first = aws["module"].handler(score_input(request_id="req-dup"), lambda_context)
    second = aws["module"].handler(score_input(request_id="req-dup"), lambda_context)

    assert first == second
    assert aws["ddb"].scan(TableName="scores")["Count"] == 1
    assert len(count_messages(aws)) == 1


def test_new_request_id_creates_new_score(aws, lambda_context):
    aws["module"].handler(score_input(request_id="req-a"), lambda_context)
    aws["module"].handler(score_input(request_id="req-b"), lambda_context)

    assert aws["ddb"].scan(TableName="scores")["Count"] == 2


def test_retry_after_publish_failure_keeps_one_score(aws, lambda_context, monkeypatch):
    module = aws["module"]
    real_publish = module.sns.publish
    calls = {"n": 0}

    def flaky_publish(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("SNS unavailable")
        return real_publish(**kwargs)

    monkeypatch.setattr(module.sns, "publish", flaky_publish)
    with pytest.raises(RuntimeError):
        module.handler(score_input(request_id="req-retry"), lambda_context)
    result = module.handler(score_input(request_id="req-retry"), lambda_context)

    assert result["score_id"] == "SUP004#req-retry"
    assert aws["ddb"].scan(TableName="scores")["Count"] == 1

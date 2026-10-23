"""FAN-IN + IDEMPOTENCY: score the supplier, save it, publish an alert.

Events can be delivered more than once ("at least once" delivery). The
@idempotent decorator remembers each (supplier_id, request_id) pair in DynamoDB,
so a repeated request returns the saved result instead of creating a second
score and a second alert.
"""
import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)

from scoring import combine
from suppliers import get_supplier

logger = Logger()
scores_table = boto3.resource("dynamodb").Table(os.environ["SCORES_TABLE"])
sns = boto3.client("sns")

persistence = DynamoDBPersistenceLayer(table_name=os.environ["IDEMPOTENCY_TABLE"])
config = IdempotencyConfig(
    event_key_jmespath="detail.[supplier_id, request_id]",
    raise_on_no_idempotency_key=True,
    expires_after_seconds=3600,
)


@logger.inject_lambda_context
@idempotent(persistence_store=persistence, config=config)
def handler(event, context):
    supplier = get_supplier(event["detail"]["supplier_id"])
    risk_score, risk_level = combine(event["checks"])

    score = {
        "score_id": str(uuid.uuid4()),
        "supplier_id": supplier["supplier_id"],
        "supplier_name": supplier["name"],
        "request_id": event["detail"]["request_id"],
        "risk_score": risk_score,
        "risk_level": risk_level,
        "open_po_value_zar": supplier["open_po_value_zar"],
        "next_po_due": supplier["next_po_due"],
        "findings": {c["check"]: c["finding"] for c in event["checks"]},
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }
    scores_table.put_item(Item=score)
    sns.publish(
        TopicArn=os.environ["ALERTS_TOPIC_ARN"],
        Message=json.dumps(score),
        MessageAttributes={"risk_level": {"DataType": "String", "StringValue": risk_level}},
    )
    logger.info("Supplier scored", extra={"supplier_id": score["supplier_id"], "risk_score": risk_score})
    return score

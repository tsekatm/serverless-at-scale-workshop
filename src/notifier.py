"""FAILURE HANDLING: reads risk alerts from SQS.

If a message cannot be processed, only that message is reported as failed
(partial batch response). SQS retries it, and after 3 failed attempts moves it
to the dead-letter queue (DLQ) so it does not block the other messages.
"""
import json

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response

logger = Logger()
processor = BatchProcessor(event_type=EventType.SQS)

LEGACY_FIELDS = {
    "supplierId": "supplier_id",
    "supplierName": "supplier_name",
    "riskLevel": "risk_level",
    "riskScore": "risk_score",
}


def normalise_legacy(message):
    """Converts the old camelCase message format to the current snake_case one."""
    return {LEGACY_FIELDS.get(key, key): value for key, value in message.items()}


def record_handler(record):
    message = json.loads(record.body)
    # message = normalise_legacy(message)  # MODULE 3 FIX: remove the "# " at the start of this line
    alert = f"[{message['risk_level']}] {message['supplier_name']} ({message['supplier_id']}) scored {message['risk_score']}"
    logger.info("ALERT " + alert)


@logger.inject_lambda_context
def handler(event, context):
    return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)

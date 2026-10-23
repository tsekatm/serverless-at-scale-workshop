#!/usr/bin/env bash
# Moves messages from the dead-letter queue back to the alerts queue they came from.
source "$(dirname "$0")/_common.sh"
aws sqs start-message-move-task --source-arn "$(output AlertsDeadLetterQueueArn)" --query TaskHandle --output text >/dev/null
echo "Redrive started: DLQ messages are being moved back to the alerts queue"

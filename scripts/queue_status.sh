#!/usr/bin/env bash
# Shows how many messages are waiting in the alerts queue and the dead-letter queue.
source "$(dirname "$0")/_common.sh"
count() {
  aws sqs get-queue-attributes --queue-url "$1" \
    --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
    --query 'Attributes.[ApproximateNumberOfMessages, ApproximateNumberOfMessagesNotVisible]' --output text
}
read -r q_wait q_flight <<<"$(count "$(output AlertsQueueUrl)")"
read -r d_wait d_flight <<<"$(count "$(output AlertsDeadLetterQueueUrl)")"
echo "Alerts queue      : $q_wait waiting, $q_flight being retried"
echo "Dead-letter queue : $d_wait waiting"

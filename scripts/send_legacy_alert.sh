#!/usr/bin/env bash
# Publishes an alert in the OLD camelCase format, which the notifier cannot read yet.
source "$(dirname "$0")/_common.sh"
aws sns publish --topic-arn "$(output AlertsTopicArn)" \
  --message '{"supplierId":"SUP009","supplierName":"Garden Route Timber","riskLevel":"LOW","riskScore":21}' \
  --query MessageId --output text >/dev/null
echo "Sent a legacy-format alert for SUP009"

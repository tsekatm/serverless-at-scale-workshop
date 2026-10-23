#!/usr/bin/env bash
# Lists every risk score saved in DynamoDB.
source "$(dirname "$0")/_common.sh"
aws dynamodb scan --table-name "$(output ScoresTableName)" \
  --query 'Items[].[supplier_id.S, supplier_name.S, request_id.S, risk_score.N, risk_level.S]' \
  --output table

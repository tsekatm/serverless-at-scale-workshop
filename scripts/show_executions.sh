#!/usr/bin/env bash
# Shows the 5 most recent Step Functions executions.
source "$(dirname "$0")/_common.sh"
aws stepfunctions list-executions --state-machine-arn "$(output StateMachineArn)" --max-results 5 \
  --query 'executions[].[name, status, startDate]' --output table

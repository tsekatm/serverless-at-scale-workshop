#!/usr/bin/env bash
# Shared helpers: reads resource names from the CloudFormation stack outputs.
set -euo pipefail
STACK_NAME="${STACK_NAME:-supplier-risk}"
export AWS_REGION="${AWS_REGION:-eu-west-1}"

output() {
  aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}

# Every cold-start function in the stack (SnapStart ones are invoked through their "live" alias)
coldstart_functions() {
  aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?starts_with(OutputKey, 'ColdStart')].OutputValue" --output text | tr '\t' '\n' | sort
}

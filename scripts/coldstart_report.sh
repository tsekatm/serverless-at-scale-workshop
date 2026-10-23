#!/usr/bin/env bash
# Reads Lambda REPORT log lines with CloudWatch Logs Insights and compares
# cold starts, durations and cost per 1 million invocations.
source "$(dirname "$0")/_common.sh"
MINUTES="${1:-60}"

groups=()
for fn in $(coldstart_functions); do groups+=("/aws/lambda/$fn"); done

QUERY='filter @type = "REPORT"
| parse @message /Init Duration: (?<init>[\d.]+) ms/
| parse @message /Restore Duration: (?<restore>[\d.]+) ms/
| stats count(*) as invocations, count(init) as cold_inits, avg(init) as avg_init_ms,
        count(restore) as snap_restores, avg(restore) as avg_restore_ms,
        avg(@billedDuration) as avg_billed_ms, max(@memorySize) as memory_bytes by @log'

QUERY_ID=$(aws logs start-query --log-group-names "${groups[@]}" \
  --start-time $(( $(date +%s) - MINUTES * 60 )) --end-time "$(date +%s)" \
  --query-string "$QUERY" --query queryId --output text)

while true; do
  STATUS=$(aws logs get-query-results --query-id "$QUERY_ID" --query status --output text)
  [[ "$STATUS" == "Complete" ]] && break
  sleep 1
done

# Lambda prices in eu-west-1 (USD): per GB-second, plus $0.20 per 1M requests
X86_GBS=0.0000166667
ARM_GBS=0.0000133334

aws logs get-query-results --query-id "$QUERY_ID" --output json \
  | python3 "$(dirname "$0")/coldstart_table.py" "$X86_GBS" "$ARM_GBS"

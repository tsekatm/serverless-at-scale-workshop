#!/usr/bin/env bash
# Generates a burst for each cold-start function: 10 calls AT ONCE (each needs its own environment,
# so most are usually cold starts), then 10 calls one after another (these usually reuse warm ones).
# Lambda decides which calls are cold; coldstart_report.sh measures how many actually were.
source "$(dirname "$0")/_common.sh"
PAYLOAD=$(printf '%s' '{"name":"Northstar Trading LLC"}' | base64)
OUT_DIR=$(mktemp -d)
START=$(date +%s)
total_errors=0

# Prints None when the function succeeded. A failed CLI call (throttling, credentials) prints CLI_ERROR.
invoke() {
  aws lambda invoke --function-name "$1" --payload "$PAYLOAD" --query FunctionError --output text \
    "$OUT_DIR/$RANDOM.json" 2>/dev/null || echo CLI_ERROR
}

for fn in $(coldstart_functions); do
  [[ "$fn" == *SnapStart* ]] && fn="$fn:live"
  echo "== $fn"
  for i in $(seq 1 10); do invoke "$fn" > "$OUT_DIR/err-$i" & done
  wait
  for i in $(seq 1 10); do invoke "$fn" >> "$OUT_DIR/err-seq"; done
  errors=$(cat "$OUT_DIR"/err-* | grep -vc '^None$' || true)
  rm -f "$OUT_DIR"/err-*
  if [[ "$errors" -gt 0 ]]; then
    echo "   !! $errors of 20 invocations FAILED - check the function's logs"
  else
    echo "   20 invocations OK (10 at once, then 10 one after another)"
  fi
  total_errors=$(( total_errors + errors ))
done
rm -rf "$OUT_DIR"
echo "Wait ~30 seconds for logs to arrive, then run:"
echo "  ./scripts/coldstart_report.sh --since $START"
[[ "$total_errors" -eq 0 ]]

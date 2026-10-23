#!/usr/bin/env bash
# Invokes each cold-start function 10 times AT ONCE (forces new environments = cold starts),
# then 10 times one after another (reuses warm environments).
source "$(dirname "$0")/_common.sh"
PAYLOAD=$(printf '%s' '{"name":"Northstar Trading LLC"}' | base64)
OUT_DIR=$(mktemp -d)

invoke() {
  aws lambda invoke --function-name "$1" --payload "$PAYLOAD" --query FunctionError --output text "$OUT_DIR/$RANDOM.json"
}

for fn in $(coldstart_functions); do
  [[ "$fn" == *SnapStart* ]] && fn="$fn:live"
  echo "== $fn"
  for i in $(seq 1 10); do invoke "$fn" > "$OUT_DIR/err-$i" & done
  wait
  errors=$(cat "$OUT_DIR"/err-* | grep -vc '^None$' || true)
  for i in $(seq 1 10); do invoke "$fn" >> "$OUT_DIR/err-seq"; done
  errors=$(( errors + $(grep -vc '^None$' "$OUT_DIR/err-seq" || true) ))
  rm -f "$OUT_DIR"/err-*
  if [[ "$errors" -gt 0 ]]; then
    echo "   !! $errors of 20 invocations FAILED - check the function's logs"
  else
    echo "   20 invocations OK (10 parallel = cold, 10 sequential = warm)"
  fi
done
rm -rf "$OUT_DIR"
echo "Wait ~30 seconds for logs to arrive, then run ./scripts/coldstart_report.sh"

#!/usr/bin/env bash
# Usage: ./scripts/send_event.sh SUP004 [request-id]
# Publishes a "SupplierRiskCheckRequested" event to the default EventBridge bus.
source "$(dirname "$0")/_common.sh"
SUPPLIER_ID="${1:?Usage: $0 SUPPLIER_ID [REQUEST_ID]}"
REQUEST_ID="${2:-req-$(date +%s)}"

DETAIL=$(printf '{"supplier_id":"%s","request_id":"%s"}' "$SUPPLIER_ID" "$REQUEST_ID")
ENTRIES=$(printf '[{"Source":"workshop.suppliers","DetailType":"SupplierRiskCheckRequested","Detail":%s}]' \
  "$(printf '%s' "$DETAIL" | sed 's/"/\\"/g; s/^/"/; s/$/"/')")

FAILED=$(aws events put-events --entries "$ENTRIES" --query 'FailedEntryCount' --output text)
[[ "$FAILED" == "0" ]] || { echo "EventBridge rejected the event" >&2; exit 1; }
echo "Sent: supplier_id=$SUPPLIER_ID request_id=$REQUEST_ID"

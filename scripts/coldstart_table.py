"""Formats the Logs Insights results from coldstart_report.sh as a table (Python 3.9+)."""
import json
import sys

X86_PRICE, ARM_PRICE = float(sys.argv[1]), float(sys.argv[2])
REQUEST_PRICE_PER_MILLION = 0.20


def number(row, key):
    value = row.get(key)
    return "-" if value in (None, "") else "{:.0f}".format(float(value))


rows = [{f["field"]: f["value"] for f in result} for result in json.load(sys.stdin)["results"]]

header = ["function", "mem MB", "arch", "calls", "cold", "init ms", "restore ms", "billed ms", "USD per 1M"]
widths = [22, 7, 7, 7, 6, 9, 12, 11, 12]
print("".join(h.ljust(w) if i == 0 else h.rjust(w) for i, (h, w) in enumerate(zip(header, widths))))

for row in sorted(rows, key=lambda r: r["@log"]):
    name = row["@log"].split("/")[-1]
    label = "ColdStart" + name.split("-ColdStart")[-1].split("-")[0]
    memory_mb = int(float(row["memory_bytes"]) / 1_000_000)
    arch = "x86" if "X86" in name else "arm64"
    price = X86_PRICE if arch == "x86" else ARM_PRICE
    billed_ms = float(row["avg_billed_ms"])
    cost = 1_000_000 * (billed_ms / 1000) * (memory_mb / 1024) * price + REQUEST_PRICE_PER_MILLION
    cold = int(row.get("cold_inits", 0)) + int(row.get("snap_restores", 0))
    values = [label, memory_mb, arch, row["invocations"], cold, number(row, "avg_init_ms"),
              number(row, "avg_restore_ms"), "{:.1f}".format(billed_ms), "{:.2f}".format(cost)]
    print("".join(str(v).ljust(w) if i == 0 else str(v).rjust(w) for i, (v, w) in enumerate(zip(values, widths))))

print("\nbilled ms = average across ALL calls (cold + warm) and includes init or restore time.\nNot included: SnapStart snapshot cache charges and restore data charges.")

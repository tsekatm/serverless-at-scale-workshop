"""COLD START LAB: a sanctions-screening function with realistic start-up work.

Everything at module level runs once per cold start (the "INIT" phase):
importing the AWS SDK, creating clients, and loading + indexing a watchlist.
Lambda's REPORT log line shows this as "Init Duration" - or "Restore Duration"
when SnapStart restores a snapshot taken AFTER init instead of re-running it.
"""
import random
from collections import defaultdict

import boto3

# --- INIT phase: runs once per execution environment ---
dynamodb = boto3.client("dynamodb")
sns = boto3.client("sns")
sqs = boto3.client("sqs")
stepfunctions = boto3.client("stepfunctions")

WATCHLIST_SIZE = 60_000
_WORDS = ["Global", "Trading", "Holdings", "Northern", "Star", "Pacific", "Union", "Atlas", "Delta", "Prime",
          "Group", "Logistics", "Energy", "Metals", "Capital", "Marine", "United", "Eastern", "Industrial", "Partners"]
_SUFFIXES = ["LLC", "Ltd", "FZE", "SA", "GmbH", "Corp", "Inc", "JSC"]


def build_watchlist(size):
    """Stands in for downloading and parsing a real sanctions list (these lists hold many thousands of names)."""
    rng = random.Random(42)
    return [f"{' '.join(rng.sample(_WORDS, 3))} {rng.choice(_SUFFIXES)} {i}" for i in range(size)]


def trigrams(text):
    text = f"  {text.lower()} "
    return {text[i:i + 3] for i in range(len(text) - 2)}


WATCHLIST = build_watchlist(WATCHLIST_SIZE)
INDEX = defaultdict(set)
for position, entry in enumerate(WATCHLIST):
    for gram in trigrams(entry):
        INDEX[gram].add(position)


# --- INVOKE phase: runs on every request ---
def handler(event, context):
    query = trigrams(event["name"])
    rarest = sorted(query, key=lambda gram: len(INDEX.get(gram, ())))[:3]
    candidates = set.intersection(*(INDEX.get(gram, set()) for gram in rarest))
    matches = [WATCHLIST[p] for p in candidates
               if len(query & trigrams(WATCHLIST[p])) / len(query | trigrams(WATCHLIST[p])) >= 0.8]
    return {"name": event["name"], "watchlist_size": WATCHLIST_SIZE, "possible_matches": matches}

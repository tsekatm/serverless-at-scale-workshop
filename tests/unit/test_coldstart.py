import coldstart


def test_watchlist_is_built_during_init():
    assert len(coldstart.WATCHLIST) == coldstart.WATCHLIST_SIZE
    assert coldstart.WATCHLIST_SIZE >= 50_000


def test_exact_watchlist_name_is_a_match(lambda_context):
    listed = coldstart.WATCHLIST[123]
    result = coldstart.handler({"name": listed}, lambda_context)
    assert listed in result["possible_matches"]
    assert result["watchlist_size"] == coldstart.WATCHLIST_SIZE


def test_clean_name_has_no_matches(lambda_context):
    assert coldstart.handler({"name": "Ubuntu Foods (Pty) Ltd"}, lambda_context)["possible_matches"] == []


def test_watchlist_is_deterministic():
    assert coldstart.build_watchlist(10) == coldstart.build_watchlist(10)


def test_screening_is_fast_once_warm(lambda_context):
    import time

    start = time.perf_counter()
    for _ in range(20):
        coldstart.handler({"name": "Global Trading Holdings LLC"}, lambda_context)
    assert (time.perf_counter() - start) / 20 < 0.02

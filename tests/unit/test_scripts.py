"""The cold-start scripts, run against a fake `aws` command."""
import os
import stat
import subprocess
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"

FAKE_AWS = r"""#!/usr/bin/env bash
echo "$*" >> "$FAKE_LOG"
case "$1 $2" in
  "cloudformation describe-stacks") echo "fn-ColdStartArmMem512" ;;
  "lambda invoke") [[ "${FAKE_INVOKE_EXIT:-0}" == 0 ]] && echo None; exit "${FAKE_INVOKE_EXIT:-0}" ;;
  "logs start-query") echo qid ;;
  "logs get-query-results")
    if [[ "$*" == *"--query status"* ]]; then echo "${FAKE_QUERY_STATUS:-Complete}"; else echo '{"results": []}'; fi ;;
esac
"""


def run(tmp_path, script, *args, **env):
    fake = tmp_path / "aws"
    fake.write_text(FAKE_AWS)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "aws.log"
    full_env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}", "FAKE_LOG": str(log), **env}
    result = subprocess.run([str(SCRIPTS / script), *args], env=full_env, capture_output=True, text=True, timeout=20)
    return result, log.read_text() if log.exists() else ""


def test_burst_reports_failed_cli_calls(tmp_path):
    result, _ = run(tmp_path, "coldstart_burst.sh", FAKE_INVOKE_EXIT="255")
    assert result.returncode != 0
    assert "20 of 20 invocations FAILED" in result.stdout


def test_burst_prints_the_start_time_for_the_report(tmp_path):
    result, _ = run(tmp_path, "coldstart_burst.sh")
    assert result.returncode == 0
    assert "./scripts/coldstart_report.sh --since " in result.stdout


def test_report_measures_from_the_given_start_time(tmp_path):
    result, log = run(tmp_path, "coldstart_report.sh", "--since", "1792800000")
    assert result.returncode == 0
    assert "--start-time 1792800000" in log


def test_report_stops_when_the_query_fails(tmp_path):
    result, _ = run(tmp_path, "coldstart_report.sh", FAKE_QUERY_STATUS="Failed")
    assert result.returncode != 0
    assert "Failed" in result.stderr

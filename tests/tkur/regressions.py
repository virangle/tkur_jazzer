#!/usr/bin/env python3
"""Regression checks for the removed launcher; logs stay outside production output."""
import json
from pathlib import Path
import socket
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
JAR = ROOT / "tkur_jazzer_standalone.jar"
OUT = ROOT / "build/tkur-regressions"
OUT.mkdir(parents=True, exist_ok=True)
results = []

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
result = subprocess.run([
    "java", "-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=127.0.0.1:" + str(port),
    "-jar", str(JAR), "--version"], capture_output=True, text=True, timeout=15)
(OUT / "jdwp.log").write_text(result.stdout + result.stderr)
assert result.returncode == 0, result
assert result.stderr.strip() == "tkur_jazzer v0.30.0", result
results.append({"name": "jdwp", "status": "PASS", "exit_code": result.returncode})

for args in (["--new-stall"], ["--cov-stall=-1"], ["--new-stall=2147483648"],
             ["--new-stall=abc"], ["--cov-stall=1.5"]):
    result = subprocess.run(["java", "-jar", str(JAR)] + args,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 1 and "ERROR:" in result.stderr, result
results.append({"name": "invalid_cli_values", "status": "PASS", "cases": 5})

subprocess.run(["javac", "--release", "8", "-d", str(OUT),
                str(ROOT / "tests/tkur/LongTeardownTarget.java")], check=True)
ready = threading.Event()
received = []
process = subprocess.Popen([
    "java", "-Xmx512m", "-cp", str(JAR) + ":" + str(OUT),
    "com.code_intelligence.jazzer.Jazzer", "--target_class=tkur.LongTeardownTarget",
    "--instrumentation_includes=tkur.**", "--new-stall=60", "-rss_limit_mb=2048",
    "-artifact_prefix=" + str(OUT) + "/",
    "--coverage_dump=" + str(OUT / "sigterm.exec")],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def capture():
    for line in process.stdout:
        line = line.decode("utf-8", errors="replace")
        received.append(line)
        if "INITED" in line:
            ready.set()

reader = threading.Thread(target=capture)
reader.start()
try:
    assert ready.wait(20), "No INITED before termination"
    started = time.monotonic()
    process.terminate()
    status = process.wait(timeout=20)
    elapsed = time.monotonic() - started
finally:
    if process.poll() is None:
        process.kill()
        process.wait()
    reader.join()
    text = "".join(received)
    (OUT / "sigterm.log").write_text(text)
# Stock libFuzzer's ExitCallback can classify an external SIGTERM as target
# exit (77) if its callback was running. This check tests complete teardown,
# not a new promise about upstream signal exit codes.
assert status in (143, 77), (status, text)
assert "TKUR_LONG_TEARDOWN_COMPLETED" in text, text
assert elapsed >= 7, elapsed
assert (OUT / "sigterm.exec").stat().st_size > 0
results.append({"name": "sigterm_long_teardown", "status": "PASS", "exit_code": status,
                "seconds_after_signal": elapsed})

started = time.monotonic()
result = subprocess.run([
    "java", "-Xmx512m", "-cp", str(JAR) + ":" + str(OUT),
    "com.code_intelligence.jazzer.Jazzer", "--target_class=tkur.LongTeardownTarget",
    "--instrumentation_includes=tkur.**", "--new-stall=1", "-rss_limit_mb=2048",
    "--coverage_dump=" + str(OUT / "stall.exec"), "-artifact_prefix=" + str(OUT) + "/"],
    capture_output=True, text=True, timeout=25)
(OUT / "long-teardown-stall.log").write_text(result.stdout + result.stderr)
assert result.returncode == 0, result
assert "TKUR_LONG_TEARDOWN_COMPLETED" in result.stderr
assert "--new-stall=1 reached:" in result.stderr
assert (OUT / "stall.exec").stat().st_size > 0
results.append({"name": "stall_long_teardown", "status": "PASS", "exit_code": 0,
                "seconds": time.monotonic() - started})
(OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))

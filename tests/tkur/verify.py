#!/usr/bin/env python3
"""Exercise the actual standalone jar, retaining logs and reports in build/tkur-tests."""
import concurrent.futures
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import threading

ROOT = Path(__file__).resolve().parents[2]
JAR = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "tkur_jazzer_standalone.jar"
OUT = ROOT / "build/tkur-stall-tests"
OUT.mkdir(parents=True, exist_ok=True)
CLASSES = OUT / "classes"
CLASSES.mkdir(exist_ok=True)
subprocess.run(["javac", "--release", "8", "-d", str(CLASSES)] +
               [str(ROOT / "tests/tkur" / (name + ".java")) for name in
                ("FlatTarget", "FeatureTarget", "CoverageTarget", "Work", "CrashTarget")], check=True)
STAMP = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ")
STATUS = re.compile(r"#\d+\s+(INITED|NEW|REDUCE|DONE|pulse)\s+.*?cov: (\d+)")


def run(name, flags, target="FlatTarget", expected="new", instrument=None, code=0):
    folder = OUT / name
    folder.mkdir(exist_ok=True)
    corpus = folder / "corpus"
    corpus.mkdir(exist_ok=True)
    # Separate fresh corpus directories for reproducible reruns.
    import tempfile
    corpus = Path(tempfile.mkdtemp(prefix="run-", dir=corpus))
    cmd = ["java", "-Xmx512m", "-cp", str(JAR) + os.pathsep + str(CLASSES),
           "com.code_intelligence.jazzer.Jazzer",
           "--target_class=tkur." + target,
           "--instrumentation_includes=" + (instrument or "tkur.**"),
           "--coverage_dump=" + str(folder / "coverage.exec"),
           "--coverage_report=" + str(folder / "coverage.txt"),
           "--reproducer_path=" + str(folder), "-artifact_prefix=" + str(folder) + "/",
           "-seed=1234", "-max_len=32", "-timeout=10", "-rss_limit_mb=2048",
           "-print_final_stats=1"] + flags + [str(corpus)]
    started = time.monotonic()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    received = []
    def capture():
        for line in process.stdout:
            received.append((time.monotonic(), line.decode("utf-8", errors="replace")))
    reader = threading.Thread(target=capture)
    reader.start()
    try:
        process.wait(timeout=50)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise
    finally:
        reader.join()
    elapsed = time.monotonic() - started
    text = "".join(line for _, line in received)
    (folder / "run.log").write_text(text)
    (folder / "events.json").write_text(json.dumps(received, indent=2))
    (folder / "command.json").write_text(json.dumps(cmd, indent=2))
    assert process.returncode == code, (name, process.returncode, text[-4000:])
    assert not any(STAMP.match(line) for line in text.splitlines()), name
    if code == 0:
        assert "TKUR_TEARDOWN_OK" in text, (name, "teardown missing")
        assert (folder / "coverage.exec").stat().st_size > 0
        assert (folder / "coverage.txt").stat().st_size > 0
        if expected:
            assert "--" + expected + "-stall=" in text, (name, text[-2000:])
            if "-verbosity=0" not in flags:
                assert "DONE" in text, name
        else:
            assert " reached:" not in text, name
    else:
        assert "TKUR_EXPECTED_FINDING" in text
        assert list(folder.glob("crash-*"))
    statuses = [(line, STATUS.search(line)) for line in text.splitlines()]
    statuses = [(line, match.group(1), int(match.group(2)))
                for line, match in statuses if match]
    measured_stall = None
    if expected and "-verbosity=0" not in flags:
        last_new = last_cov = None
        max_cov = -1
        for observed, line in received:
            match = STATUS.search(line)
            if match:
                event, cov = match.group(1), int(match.group(2))
                if event == "INITED":
                    last_new = last_cov = observed
                if event == "NEW":
                    last_new = observed
                if cov > max_cov:
                    last_cov, max_cov = observed, cov
            if "--" + expected + "-stall=2 reached:" in line:
                measured_stall = observed - (last_new if expected == "new" else last_cov)
                assert 1.9 <= measured_stall <= 2.75, (name, measured_stall)
        assert measured_stall is not None, name
    if target == "FeatureTarget":
        news = [(line, cov) for line, event, cov in statuses if event == "NEW"]
        assert news, (name, "no NEW events")
        assert len(set(cov for _, _, cov in statuses)) == 1, (name, statuses)
        if expected == "cov":
            assert "--new-stall=2 reached:" not in text, name
        if expected == "new":
            assert len(news) >= 3, (name, news)
    if target == "CoverageTarget":
        assert len(set(cov for _, _, cov in statuses)) >= 3, (name, statuses)
    return {"name": name, "seconds": round(elapsed, 2), "exit_code": process.returncode,
            "measured_stall_seconds": measured_stall,
            "status": "PASS", "log": str(folder / "run.log")}


cases = [
    ("new", ["--new-stall", "2"]),
    ("cov", ["--cov-stall=2"], "FlatTarget", "cov"),
    ("both_new", ["--new-stall=2", "--cov-stall=5"]),
    ("both_cov", ["--new-stall=5", "--cov-stall", "2"], "FlatTarget", "cov"),
    ("disabled", ["--new-stall=0", "--cov-stall=0", "-runs=100"], "FlatTarget", None),
    ("default", ["-runs=100"], "FlatTarget", None),
    ("both_equal", ["--new-stall=2", "--cov-stall=2"]),
    ("feature_cov", ["--new-stall=2", "--cov-stall=2"], "FeatureTarget", "cov", "tkur.Work"),
    ("feature_new", ["--new-stall=2"], "FeatureTarget", "new", "tkur.Work"),
    ("coverage_reset", ["--new-stall=10", "--cov-stall=2"], "CoverageTarget", "cov", "tkur.Work"),
    ("silent", ["--new-stall=2", "-verbosity=0", "-print_new=0"]),
    ("crash", ["--new-stall=2"], "CrashTarget", None, None, 77),
]
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    futures = [pool.submit(run, *case) for case in cases]
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        results.append(result)
        print(json.dumps(result), flush=True)
(OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
print("All standalone checks passed")

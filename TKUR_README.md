# tkur_jazzer 0.30.0 — stall timers

Local source fork of Jazzer at commit
`50a0e8f2c3aa0d28165b860e1c942383ba08d180`.

The current artifact uses Jazzer's original entry point and logging. There is
no timestamp prefix, output relay, or additional launcher JVM.

## Run

```bash
java -Xmx1g -cp 'tkur_jazzer_standalone.jar:target.jar:lib/*' \
  com.code_intelligence.jazzer.Jazzer \
  --target_class=example.FuzzTarget \
  --new-stall 300 --cov-stall 120 \
  -timeout=30 corpus/ > fuzz.log 2>&1
```

Supply target classes and dependencies using Java's `-cp`, as shown above.
The former wrapper's `java -jar ... --cp=...` behavior was removed.
`java -jar tkur_jazzer_standalone.jar --help` and `--version` still work.

* `--new-stall N`: normal stop after N seconds without the event corresponding
  to libFuzzer's `NEW` line. `REDUCE`, `RELOAD`, and `pulse` do not reset it.
* `--cov-stall N`: normal stop after N seconds without an increase of
  libFuzzer's `cov:` counter. Growth of `ft:` alone does not reset it.
  This counter is instrumented PC coverage, not JaCoCo line/branch coverage.
* Each timer tracks its own progress. Either can stop the run. If both expire
  at the same check, both reasons are logged.
* Durations are integer seconds in `[0, 2147483647]`; `0` disables a timer.
  Both are disabled by default. Both `--flag N` and `--flag=N` are supported.
* Timing uses a monotonic clock, starting after seed corpus initialization.
  JVM startup, target initialization and initial corpus execution are excluded.
* Timers use internal events, not log parsing, and work with `-verbosity=0`
  and `-print_new=0`.
* Checks happen between inputs. A running input must return before a stall
  can terminate the loop. Use `-timeout=N` for hung or excessively slow inputs.
  These stall timers are not hard deadlines that interrupt target execution.
* A stall normally exits with status 0, prints its reason and `DONE`, and runs
  normal Jazzer teardown and requested coverage export. Findings and standard
  timeout/error exit codes remain unchanged.
* Timers apply to the fuzzing loop, not corpus merge, crash minimization or
  single-input replay. With `-jobs`/`-fork`, they apply to individual workers,
  not the entire campaign.

Example end of a run:

```text
INFO: --cov-stall=3 reached: no cov increase for 3 seconds (cov: 3786)
#2735   DONE   cov: 3786 ft: 3988 corp: 14/14b ...
Done 2735 runs in 7 second(s)
```

## Build and verify

The supplied JAR contains Linux x86_64 native libraries; tested on OpenJDK 17.
Build prerequisites are documented upstream in `CONTRIBUTING.md`.

```bash
BAZEL=/path/to/bazel-8.4.2 bash tools/build-tkur.sh
python3 tests/tkur/verify.py
python3 tests/tkur/regressions.py
sha256sum --check tkur_jazzer_standalone.jar.sha256
```

The build script fetches only the libFuzzer subtree at pinned commit
`10f5d63a31c4bd2c00c24077b5fd02ffdd59ae67` (tag `2023-04-25`), applies
`third_party/libfuzzer-tkur.patch`, and builds the normal standalone target.
The normal upstream Bazel command also works, but downloads the whole LLVM archive:

```bash
bazel build //src/main/java/com/code_intelligence/jazzer:jazzer_standalone_deploy.jar
cp bazel-bin/src/main/java/com/code_intelligence/jazzer/jazzer_standalone_deploy.jar \
  tkur_jazzer_standalone.jar
```

Only CLI normalization/help and native stall state/checks differ from upstream
runtime behavior. Java and libFuzzer logging are restored to upstream code.

See [TKUR_VERIFICATION.md](TKUR_VERIFICATION.md) for results for the current JAR.

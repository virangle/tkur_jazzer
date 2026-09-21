# Verification — tkur_jazzer 0.30.0

Artifact: `tkur_jazzer_standalone.jar`, Linux x86_64.
Built with Bazel 8.4.2; tested with OpenJDK 17.0.20.

SHA-256: `99fe7ccd5d22496a473f0d2a11a47ee9716c141087a25d972fd91e710bd9e4c4`

Jazzer base: `50a0e8f2c3aa0d28165b860e1c942383ba08d180`.
libFuzzer base: `10f5d63a31c4bd2c00c24077b5fd02ffdd59ae67`.

## Runtime scope

The previous timestamp implementation and StandaloneLauncher have been removed.
The manifest again names `com.code_intelligence.jazzer.Jazzer`.
Java Log.java, native FuzzerIO.cpp and FuzzerFork.cpp are restored to upstream.
There is no additional launcher JVM, log relay, inherited JVM argument duplication,
or custom shutdown deadline.

The native patch now contains only stall flags, state and fuzzing-loop checks.
The project name/version command returns `tkur_jazzer v0.30.0`.

## Stall tests

`python3 tests/tkur/verify.py`: **12/12 PASS**.
[Machine-readable results](build/tkur-stall-tests/results.json).

Tests cover each timer separately, both orderings of unequal timers,
equal timers, both explicitly disabled, defaults, NEW with unchanged cov,
repeated NEW resets, repeated cov growth resets, disabled progress logging,
and a Java finding (exit 77 and crash artifact).

For N=2, externally observed time from the last relevant event to the stop
message was 2.00003–2.03763 seconds in the 0.30.0 tests. The test observer uses
a monotonic clock; production logs contain no timestamps. This is measured
test evidence, not a hard real-time guarantee.

Every normal run checks teardown and nonempty binary/text coverage exports.
Initialization sleeps 1.5 seconds to verify exclusion from the stall budget.
All captured logs are checked for absence of the removed timestamp prefix.

## Regression checks

`python3 tests/tkur/regressions.py`: **PASS**.
[Results](build/tkur-regressions/results.json).

* JDWP plus `java -jar ... --version`: exit 0; no duplicate debugger port bind.
* Five invalid/missing CLI values: rejected with exit 1.
* Stall followed by a 7-second teardown: completed, coverage saved, exit 0.
* External SIGTERM with a 7-second teardown: teardown completed after at least 7 seconds,
  confirming removal of the wrapper's forced-kill deadline. The observed exit
  was 77: stock libFuzzer can classify termination during a callback as
  "fuzz target exited". External signal handling was not changed by this fork;
  a clean stall exit and external termination have different semantics.
* JavaChecks: CLI normalization, bounds, missing values and `--` handling pass.
* Earlier [fork-mode smoke test](build/tkur-fork-no-ts/run.log), using the same
  native stall implementation: exit 0, worker statistics
  parsed (4,435,157 executions), target teardown completed.

## Open-source target

This additional run was performed before the 0.30.0 name/version update;
the native stall implementation is unchanged.

[Commons Compress 1.27.1 log](build/oss-no-ts/run.log):
2,707 executions, coverage increased from 3,731 to 3,786, then
`--cov-stall=3` stopped the run normally (exit 0).
Corpus, binary coverage and text coverage report are under `build/oss-no-ts`.

The harness and dependencies were copied from existing local artifacts.
No source projects under `/home/user/*_fuzz` were modified.

## Limits

Stall checks run between inputs, after initial corpus execution. They cannot
interrupt an input stuck inside target code; use libFuzzer `-timeout`.
With `-fork`/`-jobs`, timers govern workers, not a global campaign deadline.
Only the focused tests above were run, not the entire upstream suite.

## Release identity

Both Bazel tests `//deploy:jazzer_version_test` and
`//deploy:jazzer_standalone_version_test` pass with `tkur_jazzer v0.30.0`.
The 12 standalone checks and launcher-removal regression checks were rerun
on the rebuilt 0.30.0 JAR identified above.

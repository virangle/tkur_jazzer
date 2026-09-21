package tkur;

public final class FeatureTarget {
  private static int calls;

  public static void fuzzerTestOneInput(byte[] data) throws Exception {
    // Only Work is instrumented: its blocks stay the same while hit-count
    // features change over time, yielding NEW without increasing cov.
    Work.loop(1 << Math.min(7, 1 + calls++ / 10));
    Thread.sleep(100);
  }

  public static void fuzzerTearDown() {
    System.err.println("TKUR_TEARDOWN_OK");
  }
}

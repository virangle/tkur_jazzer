package tkur;

public final class CoverageTarget {
  private static int calls;

  public static void fuzzerTestOneInput(byte[] data) throws Exception {
    Work.steps(Math.min(3, calls++ / 10));
    Thread.sleep(100);
  }

  public static void fuzzerTearDown() {
    System.err.println("TKUR_TEARDOWN_OK");
  }
}

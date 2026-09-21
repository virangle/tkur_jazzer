package tkur;

public final class LongTeardownTarget {
  public static void fuzzerTestOneInput(byte[] data) {}

  public static void fuzzerTearDown() throws Exception {
    System.err.println("TKUR_LONG_TEARDOWN_STARTED");
    Thread.sleep(7000);
    System.err.println("TKUR_LONG_TEARDOWN_COMPLETED");
  }
}

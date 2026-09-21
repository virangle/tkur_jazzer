package tkur;

public final class FlatTarget {
  public static void fuzzerInitialize() throws Exception {
    // Initialization must not consume the stall budget.
    Thread.sleep(1500);
    System.out.print("target: split ");
    System.out.println("line\nsecond line: Привет");
  }

  public static void fuzzerTestOneInput(byte[] data) {}

  public static void fuzzerTearDown() {
    System.err.println("TKUR_TEARDOWN_OK");
  }
}

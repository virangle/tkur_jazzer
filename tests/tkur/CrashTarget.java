package tkur;

public final class CrashTarget {
  public static void fuzzerTestOneInput(byte[] data) {
    throw new IllegalStateException("TKUR_EXPECTED_FINDING");
  }
}

package com.code_intelligence.jazzer;

import java.util.Arrays;

public final class JavaChecks {
  public static void main(String[] unused) throws Exception {
    check(
        StallOptions.normalize(Arrays.asList("--new-stall", "3", "--cov-stall=5", "corpus"))
            .equals(Arrays.asList("-new_stall=3", "-cov_stall=5", "corpus")));
    check(
        StallOptions.normalize(Arrays.asList("--new-stall=0", "--", "--cov-stall"))
            .equals(Arrays.asList("-new_stall=0", "--", "--cov-stall")));
    for (String invalid : Arrays.asList("-1", "", "1.5", "2147483648", "abc", "+1")) {
      try {
        StallOptions.normalize(Arrays.asList("--new-stall=" + invalid));
        throw new AssertionError("Accepted: " + invalid);
      } catch (IllegalArgumentException expected) {
        // Expected validation error.
      }
    }
    try {
      StallOptions.normalize(Arrays.asList("--cov-stall"));
      throw new AssertionError("Missing value accepted");
    } catch (IllegalArgumentException expected) {
      // Expected validation error.
    }
    System.out.println("Java CLI checks passed");
  }

  private static void check(boolean condition) {
    if (!condition) throw new AssertionError();
  }
}

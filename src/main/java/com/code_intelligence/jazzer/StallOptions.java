package com.code_intelligence.jazzer;

import java.util.ArrayList;
import java.util.List;

/** CLI aliases for the native libFuzzer stall timers. */
final class StallOptions {
  private StallOptions() {}

  static List<String> normalize(List<String> args) {
    List<String> result = new ArrayList<>();
    for (int i = 0; i < args.size(); i++) {
      String arg = args.get(i);
      if (arg.equals("--")) {
        result.addAll(args.subList(i, args.size()));
        break;
      }
      String flag = arg.split("=", 2)[0];
      if (!flag.equals("--new-stall") && !flag.equals("--cov-stall")) {
        result.add(arg);
        continue;
      }
      String value;
      if (arg.contains("=")) {
        value = arg.substring(arg.indexOf('=') + 1);
      } else if (i + 1 < args.size()) {
        value = args.get(++i);
      } else {
        throw new IllegalArgumentException(flag + " requires a duration in seconds");
      }
      try {
        if (!value.matches("[0-9]+") || Integer.parseInt(value) < 0) {
          throw new NumberFormatException();
        }
      } catch (NumberFormatException e) {
        throw new IllegalArgumentException(flag + " requires an integer from 0 to 2147483647");
      }
      result.add("-" + flag.substring(2).replace('-', '_') + "=" + value);
    }
    return result;
  }
}

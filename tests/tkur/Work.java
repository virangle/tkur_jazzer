package tkur;

public final class Work {
  public static volatile int sink;

  public static void steps(int stage) {
    switch (stage) {
      case 0: sink = 11; break;
      case 1: sink = 22; break;
      case 2: sink = 33; break;
      default: sink = 44;
    }
  }

  public static void loop(int repetitions) {
    for (int i = 0; i < repetitions; i++) {
      sink += i;
    }
  }
}

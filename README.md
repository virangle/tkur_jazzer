# tkur_jazzer

**Версия: 0.30.0**

**tkur_jazzer — проект испытательно лаборатории ООО «ТЕХКОНСУР» для облегчения проведения
сертификационных испытаний ФСТЭК России.**

Проект представляет собой модификацию [Jazzer](https://github.com/CodeIntelligenceTesting/jazzer)
для проведения фаззинг-тестирования JVM-компонентов. В нативный цикл libFuzzer
добавлены независимые таймеры остановки при отсутствии новых путей и роста
покрытия. Сохранены штатные запуск, логирование и обработка результатов Jazzer.

## Возможности

- `--new-stall N` — завершить прогон после N секунд без события `NEW`.
- `--cov-stall N` — завершить прогон после N секунд без увеличения `cov`.
- Флаги можно использовать одновременно: остановку вызывает любой истёкший таймер.
- `0` отключает соответствующий таймер; по умолчанию оба отключены.
- Поддерживаются формы `--new-stall 300` и `--new-stall=300`.
- Отсчёт ведётся по монотонным часам после выполнения начального корпуса.
- Остановка по застою завершается с кодом 0, с выполнением teardown и
  сохранением запрошенных отчётов покрытия.
- Вывод остаётся штатным, без добавленных временных меток и дополнительной JVM-оболочки.

`REDUCE` не сбрасывает таймер новых путей; рост только `ft` не сбрасывает
таймер покрытия. Проверки выполняются между входами. Для зависших входов
используйте штатный `-timeout=N`: stall-таймер не прерывает исполняемый вход.

## Запуск

Готовый файл: `tkur_jazzer_standalone.jar`. Текущая сборка содержит нативные
библиотеки Linux x86_64 и проверена на OpenJDK 17.

```bash
mkdir -p corpus

java -Xmx1g -cp 'tkur_jazzer_standalone.jar:target.jar:lib/*' \
  com.code_intelligence.jazzer.Jazzer \
  --target_class=example.FuzzTarget \
  --new-stall 300 --cov-stall 120 \
  -timeout=30 corpus/ > fuzz.log 2>&1
```

Классы тестовой обёртки и зависимости задаются через Java `-cp`.
Имя Java-точки входа сохранено для совместимости с Jazzer.

```bash
java -jar tkur_jazzer_standalone.jar --version
# tkur_jazzer v0.30.0

java -jar tkur_jazzer_standalone.jar --help
```

## Сборка из исходников

Требуются Git, Bazel 8.4.2 (либо Bazelisk), `patch` и окружение сборки,
описанное в [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
BAZEL=/path/to/bazel-8.4.2 bash tools/build-tkur.sh
```

Скрипт получает закреплённую версию libFuzzer, применяет патч проекта и
создаёт `tkur_jazzer_standalone.jar` в корне репозитория.
Версия выпуска указана в [VERSION](VERSION); версия для Bazel задаётся
в [deploy/BUILD.bazel](deploy/BUILD.bazel).

## Проверки и документация

```bash
python3 tests/tkur/verify.py
python3 tests/tkur/regressions.py
```

- [Подробное описание таймеров и ограничений](TKUR_README.md).
- [Отчёт о проверках](TKUR_VERIFICATION.md).
- [Исходная документация Jazzer](README.upstream.md).
- [Нативный патч stall-таймеров](third_party/libfuzzer-tkur.patch).

Сборочные инструменты, кэши, логи тестов и JAR не включаются в Git.
Репозиторий хранит исходники, патчи, инструкции и воспроизводимые проверки.

## Происхождение и лицензия

Проект основан на Jazzer компании Code Intelligence:
коммит `50a0e8f2c3aa0d28165b860e1c942383ba08d180`.
Исходная история Git и сведения об авторских правах сохранены.
Remote `upstream` указывает на исходный репозиторий Jazzer.

Jazzer распространяется по лицензии [Apache License 2.0](LICENSE).
Для libFuzzer действуют условия Apache License 2.0 with LLVM Exceptions,
указанные в его исходниках.

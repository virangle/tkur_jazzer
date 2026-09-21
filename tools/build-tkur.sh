#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
task_root="$PWD"
task_bazel="${BAZEL:-bazel}"
mkdir -p build
# Avoid downloading the full LLVM archive: fetch the same pinned libFuzzer tree.
if [[ ! -d build/llvm-source/.git ]]; then
  git clone --depth 1 --filter=blob:none --sparse --branch 2023-04-25 \
    https://github.com/CodeIntelligenceTesting/llvm-project-jazzer.git build/llvm-source
  git -C build/llvm-source sparse-checkout set compiler-rt/lib/fuzzer
fi
task_revision="$(git -C build/llvm-source rev-parse HEAD)"
[[ "$task_revision" == 10f5d63a31c4bd2c00c24077b5fd02ffdd59ae67 ]]
task_native_dir="$(mktemp -d "$task_root/build/libfuzzer.XXXXXX")"
cp -a build/llvm-source/compiler-rt/lib/fuzzer/. "$task_native_dir/"
cp third_party/libFuzzer.BUILD "$task_native_dir/BUILD.bazel"
cp tools/libfuzzer.MODULE.bazel "$task_native_dir/MODULE.bazel"
patch -d "$task_native_dir" -p1 -i "$task_root/third_party/libfuzzer-tkur.patch"
"$task_bazel" build //src/main/java/com/code_intelligence/jazzer:jazzer_standalone_deploy.jar \
  "--override_repository=+_repo_rules+jazzer_libfuzzer=$task_native_dir" --jobs="${BUILD_JOBS:-6}" "$@"
cp bazel-bin/src/main/java/com/code_intelligence/jazzer/jazzer_standalone_deploy.jar \
  tkur_jazzer_standalone.jar
sha256sum tkur_jazzer_standalone.jar

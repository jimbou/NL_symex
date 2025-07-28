#!/bin/bash
set -e

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <program.c> <pass.cpp>"
  exit 1
fi

PROGRAM_SRC="$1"
PASS_SRC="$2"
BRANCH_LOGGER_SRC="$(dirname "$0")/branch_logger.c"

# Extract base name without extension
BASE_NAME=$(basename "$PROGRAM_SRC" .c)

# Working directory
WORKDIR="$(pwd)/build_tmp/$BASE_NAME"
mkdir -p "$WORKDIR"
cp "$PROGRAM_SRC" "$WORKDIR/${BASE_NAME}.c"

PASS_SO="$WORKDIR/libBranchTracePass_${BASE_NAME}.so"
PROGRAM_BC="$WORKDIR/${BASE_NAME}.bc"
INSTRUMENTED_BC="$WORKDIR/${BASE_NAME}_instrumented.bc"
BRANCH_LOGGER_BC="$WORKDIR/branch_logger_${BASE_NAME}.bc"
FINAL_BC="$WORKDIR/final_${BASE_NAME}.bc"

echo "🔧 Compiling LLVM pass"
clang++ -fno-rtti -shared -fPIC \
  -I$(llvm-config --includedir) \
  "$PASS_SRC" -o "$PASS_SO"

echo "📦 Compiling program to bitcode"
clang -emit-llvm -c -g -O0 "$PROGRAM_SRC" -o "$PROGRAM_BC"

echo "🪄 Running LLVM pass"
opt --enable-new-pm=0 -load "$PASS_SO" -branchtrace "$PROGRAM_BC" -o "$INSTRUMENTED_BC"

echo "🧱 Compiling branch_logger to bitcode"
clang -emit-llvm -c -g -O0 "$BRANCH_LOGGER_SRC" -o "$BRANCH_LOGGER_BC"

echo "🔗 Linking all bitcode files for KLEE execution"
llvm-link \
  "$INSTRUMENTED_BC" \
  "$BRANCH_LOGGER_BC" \
  "/tmp/klee_build130stp_z3/runtime/lib/libkleeRuntimePOSIX64_Release+Debug.bca" \
  -o "$FINAL_BC"

echo "✅ Build complete. Final BC: $FINAL_BC"

#!/bin/bash

set -e

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <program.c> <pass.cpp>"
  exit 1
fi

PROGRAM_SRC="$1"
PASS_SRC="$2"
BRANCH_LOGGER_SRC="$(dirname "$0")/branch_logger.c"

# Paths
WORKDIR="$(pwd)/build_tmp"
mkdir -p "$WORKDIR"

PASS_SO="$WORKDIR/libBranchTracePass.so"
PROGRAM_BC="$WORKDIR/program.bc"
INSTRUMENTED_BC="$WORKDIR/instrumented.bc"
BRANCH_LOGGER_BC="$WORKDIR/branch_logger.bc"
FINAL_BC="$WORKDIR/final.bc"
FINAL_S="$WORKDIR/final.s"
FINAL_EXE="$WORKDIR/final"

echo "🔧 Compiling LLVM pass: $PASS_SRC"
clang++ -fno-rtti -shared -fPIC \
  -I$(llvm-config --includedir) \
  "$PASS_SRC" -o "$PASS_SO"

echo "📦 Compiling program to LLVM bitcode"
clang -emit-llvm -c -g -O0 "$PROGRAM_SRC" -o "$PROGRAM_BC"

echo "🪄 Running LLVM pass"
opt --enable-new-pm=0 -load "$PASS_SO" -branchtrace "$PROGRAM_BC" -o "$INSTRUMENTED_BC"

echo "🧱 Compiling branch_logger.c to bitcode"
clang -emit-llvm -c -g -O0 "$BRANCH_LOGGER_SRC" -o "$BRANCH_LOGGER_BC"

echo "🔗 Linking instrumented program with logger"
llvm-link "$INSTRUMENTED_BC" "$BRANCH_LOGGER_BC" -o "$FINAL_BC"

echo "📜 Compiling to assembly"
llc "$FINAL_BC" -o "$FINAL_S"

echo "🚧 Linking to final executable"
clang "$FINAL_S" -lm -o "$FINAL_EXE"

echo "✅ Build complete. Executable: $FINAL_EXE"

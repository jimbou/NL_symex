#!/bin/bash
set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <source_file.c> <output_name>"
    exit 1
fi

SRC="$1"
OUT_NAME="$2"

# Extract file paths
SRC_BASENAME=$(basename "$SRC" .c)
SRC_DIR=$(dirname "$SRC")
EXE="$SRC_DIR/$OUT_NAME"

# Create temporary working directory
WORKDIR="$SRC_DIR/build_replay_temp_$SRC_BASENAME"
mkdir -p "$WORKDIR"

# Intermediate file paths
BC="$WORKDIR/tmp.bc"
S="$WORKDIR/tmp.s"

# Compile to LLVM bitcode
echo "[📦] Compiling $SRC to LLVM bitcode"
clang -emit-llvm -c -g -O0 "$SRC" -o "$BC"

# Compile bitcode to assembly
echo "[⚙️] Compiling bitcode to native assembly"
llc "$BC" -o "$S"

# Link final executable using kleeRuntest
echo "[🔗] Linking final executable: $EXE"
clang "$S" -L/tmp/klee_build130stp_z3/lib -lkleeRuntest -lm -o "$EXE"

# Clean up temp build dir
rm -rf "$WORKDIR"

echo "[✅] Native replay executable ready: $EXE"

#!/bin/bash
set -e

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <program.c> <pass.cpp>"
  exit 1
fi
REBUILD_PASS=false
if [ "$3" == "--rebuild-pass" ]; then
  REBUILD_PASS=true
fi

PROGRAM_SRC="$1"
PASS_SRC="$2"
BRANCH_LOGGER_SRC="$(dirname "$0")/branch_logger.c"

# Extract base name without extension
BASE_NAME=$(basename "$PROGRAM_SRC" .c)

# Working directory
#we want the work dir to be the same as the src file pth
WORKDIR="$(dirname "$PROGRAM_SRC")/build_tmp/$BASE_NAME"
# #WORKDIR="$(pwd)/build_tmp/$BASE_NAME"
# WORKDIR="$(pwd)/build_tmp/$BASE_NAME"
mkdir -p "$WORKDIR"

# Prepend dummy assume_NL_start/stop definitions
TMPFILE="$WORKDIR/tmp_$BASE_NAME.c"
# Create a temporary file with dummy functions, if it exists delete it forst
if [ -f "$TMPFILE" ]; then
  rm "$TMPFILE"
fi
echo -e 'void assume_NL_stop() {}\nvoid assume_NL_start() {}' > "$TMPFILE"
cat "$PROGRAM_SRC" >> "$TMPFILE"
mv "$TMPFILE" "$WORKDIR/${BASE_NAME}.c"
# cp "$PROGRAM_SRC" "$WORKDIR/${BASE_NAME}.c"
PROGRAM_SRC="$WORKDIR/${BASE_NAME}.c"

# Uncomment assume_NL_start() and assume_NL_stop() in the source file if commented
sed -i 's|//\s*\(assume_NL_start\s*(.*);\)|\1|' "$PROGRAM_SRC"
sed -i 's|//\s*\(assume_NL_stop\s*(.*);\)|\1|' "$PROGRAM_SRC"


PASS_SO="$WORKDIR/libBranchTracePass_${BASE_NAME}.so"
PROGRAM_BC="$WORKDIR/${BASE_NAME}.bc"
INSTRUMENTED_BC="$WORKDIR/${BASE_NAME}_instrumented.bc"
BRANCH_LOGGER_BC="$WORKDIR/branch_logger_${BASE_NAME}.bc"
FINAL_BC="$WORKDIR/final_${BASE_NAME}.bc"





if [ "$REBUILD_PASS" = true ]; then
  echo "🔧 Compiling LLVM pass"
  clang++ -fno-rtti -shared -fPIC \
    -I$(llvm-config --includedir) \
    "$PASS_SRC" -o "$PASS_SO"
else
  echo "⚠️  Skipping LLVM pass rebuild. Using existing $PASS_SO"
fi

echo "📦 Compiling program to bitcode"
clang -emit-llvm -c -g -O0 "$PROGRAM_SRC" -o "$PROGRAM_BC"

echo "🪄 Running LLVM pass"
opt --enable-new-pm=0 -load "$PASS_SO" -branchtrace "$PROGRAM_BC" -o "$INSTRUMENTED_BC"

echo "🧱 Compiling branch_logger to bitcode"
clang -emit-llvm -c -g -O0 "$BRANCH_LOGGER_SRC" -o "$BRANCH_LOGGER_BC"

echo "🔗 Linking all bitcode files for KLEE execution"
# llvm-link \
#   "$INSTRUMENTED_BC" \
#   "$BRANCH_LOGGER_BC" \
#   "/tmp/klee_build130stp_z3/runtime/lib/libkleeRuntimePOSIX64_Release+Debug.bca" \
#   -o "$FINAL_BC"

llvm-link \
  "$INSTRUMENTED_BC" \
  "$BRANCH_LOGGER_BC" \
  -o "$FINAL_BC"

echo "✅ Build complete. Final BC: $FINAL_BC"

#echo what the workdir is
# 🎯 Build native replay executable from instrumented bitcode
REPLAY_BC="$WORKDIR/final_${BASE_NAME}_replay.bc"
REPLAY_S="$WORKDIR/final_${BASE_NAME}_replay.s"
REPLAY_EXE="$WORKDIR/final_${BASE_NAME}_replay"

# Create separate BC with no KLEE runtime (just kleeRuntest)
llvm-link "$INSTRUMENTED_BC" "$BRANCH_LOGGER_BC" -o "$REPLAY_BC"

# Compile to assembly
llc "$REPLAY_BC" -o "$REPLAY_S"

# Link using kleeRuntest (not full KLEE runtime)
clang "$REPLAY_S" -L/tmp/klee_build130stp_z3/lib -lkleeRuntest -lm -o "$REPLAY_EXE"

echo "✅ Replay executable ready: $REPLAY_EXE"

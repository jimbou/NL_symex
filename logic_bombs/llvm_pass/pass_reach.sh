#!/bin/bash
set -e

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <program.c> <Reachability_pass.cpp> [--rebuild-pass]"
  exit 1
fi

PROGRAM_SRC="$1"
PASS_SRC="$2"
REBUILD_PASS=false
if [ "$3" == "--rebuild-pass" ]; then
  REBUILD_PASS=true
fi

REACH_LOGGER_SRC="$(dirname "$0")/reach_here.c"
BASE_NAME=$(basename "$PROGRAM_SRC" .c)
WORKDIR="$(dirname "$PROGRAM_SRC")/build_tmp/${BASE_NAME}_reach"
mkdir -p "$WORKDIR"

TMPFILE="$WORKDIR/tmp_$BASE_NAME.c"
if [ -f "$TMPFILE" ]; then
  rm "$TMPFILE"
fi

# Insert dummy assume_NL markers if not already in the file
echo -e 'void assume_NL_stop() {}\nvoid assume_NL_start() {}' > "$TMPFILE"
cat "$PROGRAM_SRC" >> "$TMPFILE"
mv "$TMPFILE" "$WORKDIR/${BASE_NAME}.c"
PROGRAM_SRC="$WORKDIR/${BASE_NAME}.c"

# Uncomment assume_NL markers if commented out
sed -i 's|//\s*\(assume_NL_start\s*(.*);\)|\1|' "$PROGRAM_SRC"
sed -i 's|//\s*\(assume_NL_stop\s*(.*);\)|\1|' "$PROGRAM_SRC"

PASS_SO="$WORKDIR/libReachabilityPass_${BASE_NAME}.so"
PROGRAM_BC="$WORKDIR/${BASE_NAME}.bc"
INSTRUMENTED_BC="$WORKDIR/${BASE_NAME}_reach_instrumented.bc"
REACH_LOGGER_BC="$WORKDIR/reach_logger_${BASE_NAME}.bc"
FINAL_BC="$WORKDIR/final_${BASE_NAME}_reach.bc"

if [ "$REBUILD_PASS" = true ]; then
  echo "🔧 Compiling Reachability LLVM pass"
  clang++ -fno-rtti -shared -fPIC \
    -I$(llvm-config --includedir) \
    "$PASS_SRC" -o "$PASS_SO"
else
  echo "⚠️  Skipping LLVM pass rebuild. Using existing $PASS_SO"
fi

echo "📦 Compiling program to LLVM bitcode"
clang -emit-llvm -c -g -O0 "$PROGRAM_SRC" -o "$PROGRAM_BC"

echo "🪄 Running Reachability LLVM pass"
opt --enable-new-pm=0 -load "$PASS_SO" -inject-reach-marker "$PROGRAM_BC" -o "$INSTRUMENTED_BC"

echo "🧱 Compiling reach_here.c to bitcode"
clang -emit-llvm -c -g -O0 "$REACH_LOGGER_SRC" -o "$REACH_LOGGER_BC"

echo "🔗 Linking instrumented bitcode with runtime logger"
llvm-link "$INSTRUMENTED_BC" "$REACH_LOGGER_BC" -o "$FINAL_BC"

echo "✅ Final KLEE-compatible bitcode: $FINAL_BC"

# Optional: Build native executable for replay
REPLAY_BC="$WORKDIR/final_${BASE_NAME}_replay.bc"
REPLAY_S="$WORKDIR/final_${BASE_NAME}_replay.s"
REPLAY_EXE="$WORKDIR/final_${BASE_NAME}_replay"

llvm-link "$INSTRUMENTED_BC" "$REACH_LOGGER_BC" -o "$REPLAY_BC"
llc "$REPLAY_BC" -o "$REPLAY_S"
clang "$REPLAY_S" -L/tmp/klee_build130stp_z3/lib -lkleeRuntest -lm -o "$REPLAY_EXE"

echo "✅ Native replay executable ready: $REPLAY_EXE"

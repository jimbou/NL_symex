#!/bin/bash

set -e

# ---- ARGUMENTS ----
LOG_FOLDER=$1
FILE1=$2
FILE2=$3

if [ -z "$LOG_FOLDER" ] || [ -z "$FILE1" ] || [ -z "$FILE2" ]; then
    echo "Usage: $0 <log_folder> <klee_ready_1.c> <klee_ready_2.c>"
    exit 1
fi

DOCKER_IMAGE="klee/klee"
CONTAINER_NAME="klee_temp"
LOCAL_DIR=$(pwd)
BASENAME1=$(basename "$FILE1")
BASENAME2=$(basename "$FILE2")
REMOTE_DIR="/home/klee/$LOG_FOLDER"

# ---- CONTAINER CHECK ----
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    STATUS=$(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")
    if [ "$STATUS" = "exited" ]; then
        echo "[1] Starting existing container '$CONTAINER_NAME'..."
        docker start "$CONTAINER_NAME" > /dev/null
    else
        echo "[1] Reusing running container '$CONTAINER_NAME'..."
    fi
else
    echo "[1] Creating new container '$CONTAINER_NAME'..."
    docker run -dit --name "$CONTAINER_NAME" "$DOCKER_IMAGE" bash
fi

# ---- REMOTE WORKSPACE SETUP ----
# echo "[2] Creating working directory in container..."
# Delete existing remote log folder (if any), then recreate
echo "[2] Cleaning and creating working directory in container..."
docker exec "$CONTAINER_NAME" bash -c "rm -rf $REMOTE_DIR && mkdir -p $REMOTE_DIR"


# ---- COPY FILES ----
echo "[3] Copying source files into container..."
docker cp "$FILE1" "$CONTAINER_NAME:$REMOTE_DIR/$BASENAME1"
docker cp "$FILE2" "$CONTAINER_NAME:$REMOTE_DIR/$BASENAME2"

# ---- COMPILE + KLEE FOR FILE 1 ----
echo "[4] Analyzing $BASENAME1..."
docker exec "$CONTAINER_NAME" bash -c "cd $REMOTE_DIR && \
    clang -I /klee/include -emit-llvm -c -g $BASENAME1 -o file1.bc && \
    klee --output-dir=klee-out-1 file1.bc"

# ---- COMPILE + KLEE FOR FILE 2 ----
echo "[5] Analyzing $BASENAME2..."
docker exec "$CONTAINER_NAME" bash -c "cd $REMOTE_DIR && \
    clang -I /klee/include -emit-llvm -c -g $BASENAME2 -o file2.bc && \
    klee --output-dir=klee-out-2 file2.bc"

# ---- COPY RESULTS ----
echo "[6] Copying output back to host..."
mkdir -p "$LOG_FOLDER"
docker cp "$CONTAINER_NAME:$REMOTE_DIR/klee-out-1" "$LOG_FOLDER/klee-out-1"
docker cp "$CONTAINER_NAME:$REMOTE_DIR/klee-out-2" "$LOG_FOLDER/klee-out-2"

echo "[✓] Done. Outputs saved to:"
echo "  $LOG_FOLDER/klee-out-1"
echo "  $LOG_FOLDER/klee-out-2"

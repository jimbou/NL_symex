# Ghost-Code Guided KLEE Pipeline

This pipeline automates end‑to‑end **ghost-code–guided symbolic execution** and **post‑translation path‑suffix comparison** between an **original** C program and its **translated (ghost)** version.

It will:

1. Compile the **ghost** C file to LLVM bitcode inside the KLEE Docker.
2. Run **KLEE** on the ghost bitcode to generate `.ktest` test cases.
3. Instrument **both** the original and ghost C sources with an LLVM pass that logs branch IDs **after** `assume_NL_stop`.
4. Build **native replay executables** for both versions (so we can replay `.ktest` without KLEE).
5. (Optionally) Use an LLM to learn a **remapping** from ghost `.ktest` inputs → original inputs (for when your ghost translation changes types/semantics).
6. Replay:

   * remapped tests on **original** replay executable; and
   * the original ghost `.ktest` files on the **ghost** replay executable,
     collecting **branch traces**.
7. Copy everything back locally and **compare traces** to check Post‑Translation Path Suffix Equivalence (PTPSE).

---

## Repository Layout (key files)

```
.
├── pipeline.py                  # Main pipeline (this file)
├── llvm_pass/
│   ├── pass.sh                  # Instruments a C source and builds replay exe
│   ├── BranchTracePass.cpp      # LLVM pass: injects __record_branch_hit(...) calls after assume_NL_stop
│   └── branch_logger.c          # Defines __record_branch_hit
├── branch_checker.py            # Compares two trace files
├── ktest_transform.py           # Remap logic to produce *_updated.ktest files
├── model.py                     # get_model() factory for the LLM used in remapping
└── logic_bombs/                 # (Mounted on Docker) host side shared folder
```

> **Note**: Your Docker image must have KLEE + Clang + LLVM set up.
> The container used below is named `klee_logic_bombs` and expects a host mount of `logic_bombs → /home/klee/logic_bombs`.

---

## Prerequisites

* **Docker** installed on the host.
* A running container (or startable container) named **`klee_logic_bombs`** with a working KLEE install.
* The container must include:

  * `clang`, `opt`, `llvm-link`, `llc`
  * KLEE (and `klee-replay`) at `/tmp/klee_build130stp_z3/bin/klee`
  * `libkleeRuntest.so` at `/tmp/klee_build130stp_z3/lib`
* The `logic_bombs` directory on the host is **mounted** into `/home/klee/logic_bombs` inside the container.
  This script writes temp workdirs under `logic_bombs/tmp_ghost_*` so both host and container see the same files.

---

## Container Environment (recommended)

Inside the Docker container, persist the runtime path for `klee-replay` by editing `~/.bashrc` (or `/etc/profile` if you prefer):

```bash
echo 'export PATH="/tmp/klee_build130stp_z3/bin:$PATH"' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH="/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH"' >> ~/.bashrc
source ~/.bashrc
```

This ensures `klee-replay` can find `libkleeRuntest.so` and KLEE binaries.

---

## Source Annotations & Instrumentation

* The LLVM pass logs branches **after** your NL block by searching for calls to `assume_NL_stop()` in the IR and instrumenting **conditional branches** that occur after it.
* If your source does not have these markers, the pass wrapper will **prepend** dummy definitions and then **uncomment** the first occurrences of:

  ```c
  //assume_NL_start();
  //assume_NL_stop();
  ```

  into

  ```c
  assume_NL_start();
  assume_NL_stop();
  ```

  (so placement matters—use these comments to indicate the end of your translated region in the file).

### `pass.sh` (what it does)

* Compiles the pass (`BranchTracePass.cpp`) into a `.so`.
* Compiles your program to bitcode.
* Runs the pass to inject `__record_branch_hit(int)`.
* Links with `branch_logger.c` to define the logger (using **printf** so output goes to stdout).
* Builds a **replay executable** (`final_<name>_replay`) linked against `-lkleeRuntest` so we can replay `.ktest` without running KLEE again.

> The replay executable prints lines like `Branch taken: <id>` whenever a branch is traversed after `assume_NL_stop`.

---

## Installing Python Dependencies (host)

* You will need the support modules:

  * `branch_checker.py` (compare traces)
  * `ktest_transform.py` (read, write, remap `.ktest`)
  * `model.py` (provides `get_model` to query your LLM)

If your LLM library requires API keys, set them before running `pipeline.py`.

---

## Running the Pipeline

```bash
python3 pipeline.py \
  --original /path/to/original.c \
  --translated /path/to/ghost.c \
  --log_folder log_tmp_ghost \
  --docker_name klee_logic_bombs \
  --model_name gpt-4.1
```

**Arguments:**

* `--original` Path to original C file (host path).
* `--translated` Path to translated / ghost C file (host path).
* `--log_folder` Where all outputs will be staged locally. Defaults to `log_tmp_ghost`.
* `--docker_name` Name of the Docker container. Defaults to `klee_logic_bombs`.
* `--model_name` LLM model name used by the remapper; defaults to `gpt-4.1`. You can point to a local model in `model.py` if needed.

---

## What the Pipeline Produces

* A temp working directory under your host mount (e.g., `logic_bombs/tmp_ghost_<id>`), mirrored inside the container at `/home/klee/tmp_ghost_<id>`.
* `ghost_out-*` inside that directory with KLEE’s `.ktest` outputs for the **ghost** version.
* Under `/home/klee/tmp_ghost_<id>/build_tmp/orig` and `/home/klee/tmp_ghost_<id>/build_tmp/ghost`:

  * `final_orig_replay` and `final_ghost_replay` executables.
* A `trace_logs/` directory in the same temp root with:

  * `orig_testNNNNNN[_updated].ktest.trace` – branch trace from original replay executable **using remapped test**.
  * `ghost_testNNNNNN.ktest.trace` – branch trace from ghost replay executable **using original (unmodified) test**.
* A local results directory under `log_tmp_ghost/ghost_cmp_<id>` containing:

  * `trace_logs/` (copied from container)
  * a **`summary.txt`** listing `MATCH / MISMATCH` for each test after comparing the first 5 post-min branch IDs (or exact match if shorter) via `branch_checker.py`.

---

## Typical Flow (step by step)

1. **Compile ghost.c to BC & run KLEE**
   Generates `.ktest` files under `ghost_out-*`.

2. **Instrument original.c and ghost.c**
   `pass.sh` injects the branch logging, builds `final_*_replay` executables.

3. **Remap `.ktest` (optional but recommended)**

   * All `.ktest` are copied locally into `log_tmp_ghost/local_ktests/ghost_out-*`.
   * A sample `.ktest` plus both source files are fed to your LLM via `ktest_transform.py` to generate a `remap_testcase()` function.
   * The function is applied to all `.ktest`, producing `*_updated.ktest`.

4. **Copy tests back to container**
   Both original `.ktest` and `*_updated.ktest` are placed back into `ghost_out-*` in the container.

5. **Replay & collect traces**

   * **Original** executable replays **remapped** tests → `orig_..._updated.ktest.trace`.
   * **Ghost** executable replays **original** tests → `ghost_...ktest.trace`.

6. **Compare**

   * Copy all container outputs locally.
   * Run `branch_checker.compare_traces` for each pair and write a `summary.txt`.

---

## Troubleshooting

* **`klee-replay: error while loading shared libraries: libkleeRuntest.so.1.0`**

  * Make sure `LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib` is set **inside** the container (export it in `~/.bashrc`).

* **`execv: Permission denied` / replay fails via Docker but works interactively**

  * Ensure the `docker exec ... bash -c` command inherits the same environment as your interactive shell:

    ```
    export LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH
    ```

    The pipeline already prepends this in its `bash -c` calls, but verify your path is correct for your container.

* **No branch prints appear**

  * Confirm your program actually reaches `assume_NL_stop();` and branches after it.
  * The pass only logs **conditional branches** that appear **after** the NL stop marker.

* **`log()` / math symbol link errors when building replay**

  * The pass script links with `-lm`. If you change the toolchain path, keep `-lm`.

* **KLEE external calls**

  * If your program uses `printf`, you may need to run KLEE with `--external-calls=all` in `run_klee_in_docker` if you hit warnings. (In many cases, this is not needed for bitcode compiled as in the script.)

---

## Notes on Remapping

* The remapping logic (in `ktest_transform.py`) prompts an LLM to produce:

  ```python
  def remap_testcase(inputs: dict[str, list[int]]) -> dict[str, list[int]]:
      ...
  ```

  This function **inverts** ghost‑side transformations (e.g., int‑cast, sqrt, affine/exp/log transforms) back to the input format expected by the original code.

* Only **remapped** tests (`*_updated.ktest`) are used on the **original** executable.
  The **ghost** executable replays the **original** ghost `.ktest` values unmodified.

---

## Example

```bash
python3 pipeline.py \
  --original logic_bombs/sample/original.c \
  --translated logic_bombs/sample/ghost.c \
  --log_folder log_tmp_ghost \
  --docker_name klee_logic_bombs \
  --model_name gpt-4.1
```

**Output** (abridged):

```
🟢 Docker already running.
📦 Compiling ghost to BC and running KLEE...
🛠️  Instrumenting with LLVM pass
✅ Replay executable ready: /home/klee/tmp_ghost_.../build_tmp/orig/final_orig_replay
✅ Replay executable ready: /home/klee/tmp_ghost_.../build_tmp/ghost/final_ghost_replay
[INFO] Remapped ktests saved in: log_tmp_ghost/local_ktests/ghost_out-0
📦 Found 12 test cases.
📤 Trace and output directories copied to: log_tmp_ghost/ghost_cmp_ab12cd34
✅ Comparison finished. Summary written to: log_tmp_ghost/ghost_cmp_ab12cd34/summary.txt
```

Open `log_tmp_ghost/ghost_cmp_*/summary.txt` to see `MATCH` / `MISMATCH` judgments per test.

---

## Extending / Customizing

* **Branch ID policy**: If you want stable IDs across builds, ensure the pass uses a deterministic ordering (it does sequential numbering as it sees branches after `assume_NL_stop`).
* **Comparison function**: The default `branch_checker.py` compares the **first five** branch IDs after dropping the minimum (to skip setup/logging). Adjust to your needs.
* **Model**: Implement your own `get_model()` in `model.py` to connect to your LLM or rules engine.

---


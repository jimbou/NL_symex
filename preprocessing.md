
# `preprocessing.py` — C Code Preprocessing for KLEE Symbolic Execution

This script automates the preprocessing of C programs to prepare them for symbolic execution using the KLEE engine. It performs the following:

* Optionally instruments the C file with a `main()` suitable for KLEE (if not already annotated)
* Runs symbolic execution in a Docker container
* Identifies uncovered code regions
* Uses an LLM to annotate problematic code regions with `assume_NL_start();` and `assume_NL_stop();`
* Outputs modified source files and logs in a structured directory

---

## 🔧 Command-Line Usage

```bash
python preprocessing.py \
  --c_file_path path/to/file.c \
  [--log_folder my_logs] \
  [--docker_name klee_logic_bombs] \
  [--model my-model-name] \
  [--is_klee_annotated]
```

### Arguments:

| Argument              | Description                                                                    |
| --------------------- | ------------------------------------------------------------------------------ |
| `--c_file_path`       | Path to the C file to analyze (**required**)                                   |
| `--log_folder`        | Folder to store logs and intermediate results (default: `log_tmp`)             |
| `--docker_name`       | Name of the Docker container running KLEE (default: `klee_logic_bombs`)        |
| `--model`             | Name of the LLM to use for annotation (default: `deepseek-v3-aliyun`)          |
| `--is_klee_annotated` | Set this flag if your input file already contains a `main()` suitable for KLEE |

---

## 🧠 Overview of Workflow

### Step 1. **Optional KLEE Instrumentation**

If `--is_klee_annotated` is **not** provided, the script uses an LLM to generate a `main()` function compatible with KLEE, using the function:

```python
merge_and_save(model, original_path, output_path)
```

This ensures the code declares symbolic inputs using `klee_make_symbolic()` and properly invokes the user-defined functions.

### Step 2. **Copy to Log Folder**

The (optionally instrumented) C file is copied to the log directory (default: `log_tmp/`).

### Step 3. **Temporary KLEE Directory**

A directory `logic_bombs/tmp_run_klee/` is created and populated with the C file. This mimics the KLEE environment.

### Step 4. **Run KLEE in Docker**

The Docker container is started and this command is executed inside it:

```bash
python3 /home/klee/get_klee_coverage.py /home/klee/tmp_run_klee/your_file.c
```

This returns a JSON object:

```json
{
  "covered": [[line_num, "line content"], ...],
  "uncovered": [[line_num, "line content"], ...]
}
```

Captured via:

```python
get_uncovered_from_container(docker_name, c_path_inside_container)
```

### Step 5. **Move Results**

The directory `logic_bombs/tmp_run_klee/` is renamed and moved into the log folder for persistence.

### Step 6. **Insert Markers for LLM Translation**

An LLM is queried with the code and uncovered lines. It suggests where to insert:

* `assume_NL_start();`
* `assume_NL_stop();`

The modified file is saved with `_marked.c` suffix.

Function used:

```python
get_assume_code(model, source_path, output_path, uncovered)
```

---

## 🧩 Supporting Modules

### `get_assume_code.py`

This module parses KLEE coverage output and instructs the LLM to locate problematic regions that should be surrounded with:

```c
assume_NL_start();
// complex code
assume_NL_stop();
```

#### Key Functions

* `get_klee_lines(model, code, uncovered_lines)`:
  Constructs a rich prompt using the original code and uncovered lines.

* `insert_assume_markers(...)`:
  Inserts marker statements after the suggested lines.

* `get_assume_code(...)`:
  Orchestrates the whole annotation process.

---

### `start_klee.py`

This module creates a KLEE-compatible `main()` using an LLM and merges it into the original file.

#### Key Functions

* `get_klee_suitable(model, code)`:
  Sends the source code to the LLM to generate a symbolic main function.

* `extract_main_function(response)`:
  Extracts the `main()` function from the LLM's response.

* `merge_and_save(model, original_path, output_path)`:
  Merges the generated main with the original file, avoiding duplicate `#include` lines.

---

## 📁 Output Files

* `log_folder/` — Main working directory

  * `tmp_run_klee/` — Coverage logs and KLEE run files
  * `*.c` — Original (or annotated) C file
  * `*_marked.c` — Final output with `assume_NL` markers
  * `Klee_main/` — Logs from main function generation
  * `Nl_markers/` — Logs from assume marker insertion

---

## ✅ Example Flow

```bash
python preprocessing.py \
  --c_file_path programs/fork_example.c \
  --log_folder logs/fork_test \
  --model gpt-4o \
  --docker_name klee_logic_bombs
```

1. Instruments the C file with a `main()` using GPT-4o
2. Executes KLEE via Docker
3. Identifies uncovered lines
4. Uses LLM to insert `assume_NL_start/stop`
5. Saves final file as `fork_example_marked.c`

---

## 📎 Notes

* Make sure Docker is running and the container `klee_logic_bombs` exists `
* All model querying must return **JSON with line numbers only**, or the parsing will fail.
* This script assumes a Linux-like host environment with `docker`, `shutil`, and Python 3.10+ installed.


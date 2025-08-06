
import glob

import struct
import importlib.util
import os
from ktest import read_ktest_structured, format_ktest_as_string, write_ktest_file
import subprocess

ktest_inverse_prompt_minimal_stub = """
You are a symbolic execution assistant. Your task is to **reconstruct inputs for the original C code** based on the behavior of a **minimal stub replacement**.

---

## Context

We originally replaced a complex or difficult code region in a C program (e.g., complex loops, math libraries, or external I/O) with a **minimal no-op placeholder**, just to make the program compilable and executable under KLEE. For example, this region may now contain only variable declarations or dummy assignments.

We then ran KLEE on this simplified version, which produced some test inputs (symbolic values). These inputs are not valid for the **original** code, which contains real logic in the removed region.

Now, we want to **invert the original code logic** to recover valid inputs from the test outputs. In essence:

> We are treating the original removed code block as a function `f(x) = y`, and trying to compute `x = f⁻¹(y)` using known observed values.

---

## Your Input

You will be provided with:

1. The **full original C code**, including the difficult code block between markers `assume_NL_start();` and `assume_NL_stop();`
2. The **minimal replacement region**, which was used instead of the original code to allow KLEE analysis.
3. One symbolic test case (`ktest` style) in dictionary format. The values in this test case are the ones observed **after** the simplified code (e.g., symbolic variables reintroduced with dummy values).

---

## Your Task

Write a Python function that **inverts the logic of the original code region** to reconstruct a plausible set of symbolic input values for the original code.

The mapping should:
- Assume the minimal region had no logic, so any values produced were directly symbolic
- Use the original code's logic to infer which input values would have produced those same values
- Only transform variables that appear inside or after the removed code region
- Maintain the correct type and byte length (e.g., 4 bytes for `float`, 1 byte for `char`, etc.)

---

## Output Format

Write a single Python function like this:

```python
def remap_testcase_simple(inputs: dict[str, list[int]]) -> dict[str, list[int]]:
````

Your function:


* Accepts a dictionary where each value is a list of bytes (from a `.ktest` file).
* Converts the relevant values (e.g., reconstruct floats, apply inverse math).
* Returns a new dictionary in the same format, containing remapped bytes.


Include any necessary `struct`, `math`, or other imports.

---

## Inputs

### Original C Code:

```c
{FULL_ORIGINAL_CODE}
```

---

### Minimal Replacement Code:

```c
{MINIMAL_CODE}
```

---

### KLEE ktest Test Case:

```
{TESTCASE_AS_DICT}
```

---

## Output

Return only the Python function `remap_testcase(...)`. Do not include any extra text.
"""


def read_ktest_file(file_path):
    """
    Reads a .ktest file and extracts input variables as a dictionary.
    """
    with open(file_path, "rb") as f:
        data = f.read()

    offset = 0
    def read(fmt):
        nonlocal offset
        size = struct.calcsize(fmt)
        val = struct.unpack(fmt, data[offset:offset+size])
        offset += size
        return val[0] if len(val) == 1 else val

    assert data[offset:offset+5] == b'KTEST'
    offset += 5
    version = read(">i")
    num_args = read(">i")
    args = []
    for _ in range(num_args):
        length = read(">i")
        args.append(data[offset:offset+length].decode())
        offset += length

    num_objects = read(">i")
    inputs = {}
    input_metadata = []
    for _ in range(num_objects):
        name_len = read(">i")
        name = data[offset:offset+name_len].decode()
        offset += name_len
        size = read(">i")
        value = data[offset:offset+size]
        offset += size
        inputs[name] = list(value)
        input_metadata.append((name, size))

    return inputs, input_metadata, version, args



# def display_ktest_to_user(name: str, data: dict):
#     df = pd.DataFrame([(k, v) for k, v in data.items()], columns=["Variable", "Value(Bytes)"])
#     from ace_tools import display_dataframe_to_user
#     display_dataframe_to_user(name, df)
#     return df

ktest_input_mapping_prompt ="""
You are a C program transformation assistant. Your task is to help map symbolic inputs from a **transformed** C program (used with KLEE) back to the **original** C program, so that **the same execution path** is triggered.

This situation occurs because the transformed code simplifies or rewrites parts of the original code to make it KLEE-compatible. These changes may involve:
- Type conversions (e.g., `float` → `int`)
- Removing or replacing mathematical operations
- Simplifying expressions or control flow

---

## Your Input

You will be provided with:

1. The **original full C code**, which contains logic that has been transformed.
2. The **transformed code region**, replacing a part of the original (marked with `assume_NL_start` and `assume_NL_stop`).
3. One **example symbolic test case**  in the ktest format (just the test variable and its type).

---

## Your Task

You must write a Python function that **reconstructs the expected input** for the original code, based on the test case for the transformed code.

In other words:

> Given that the transformed code removes or simplifies some computation, you must **re-apply those transformations in reverse** to recover the original input values.

This ensures the input will follow the **same execution path** in the original code.

### For example:

If the **original code** contains:

float x;
x = x + 356;
x = pow(x, 2);
if (x == 625)


And the **transformed code** simplifies it to:


int x;
if (x == 625)

Then a test case like `x = 625` (int) works for the transformed code. But to make it work in the original code, we need to **reverse the transformation**:

* Take `x = 625`
* `x = sqrt(625) = 25`
* `x = 25 - 356 = -331`

Then we convert `-331` to 4 bytes as a float.


## Output Requirements

You must return a Python function:

```python
def remap_testcase(inputs: dict[str, list[int]]) -> dict[str, list[int]]:
```

This function:

* Accepts a dictionary where each value is a list of bytes (from a `.ktest` file).
* Converts the relevant values (e.g., reconstruct floats, apply inverse math).
* Returns a new dictionary in the same format, containing remapped bytes.

Ensure:

* Byte size is preserved (e.g., 4-byte float → 4-byte float).
* Transformed expressions are **inverted** correctly (e.g., `x = pow(x+356, 2)` → `x = sqrt(x) - 356`)
* You **only modify inputs relevant to the transformed region**
* Any necessary imports are included.

---

## Inputs

### Original Code:

```c
{FULL_ORIGINAL_CODE}
```

---

### Transformed Region:

```c
{TRANSLATED_CODE}
```

---

### Example Transformed Test Case:


{TESTCASE_AS_DICT}


---

## Your Output

Return only the Python function `remap_testcase(...)` as described above with the necessary imports.
"""



def build_ktest_mapping_prompt(original_code: str, transformed_code: str, ktest_inputs: dict) -> str:
    """
    Constructs a prompt for the LLM to determine whether remapping of KLEE test inputs is needed,
    and if so, to return a Python function to do the remapping.
    """
    return ktest_input_mapping_prompt.format(
        FULL_ORIGINAL_CODE=original_code,
        TRANSLATED_CODE=transformed_code,
        TESTCASE_AS_DICT=str(ktest_inputs)
    )

def build_ktest_mapping_prompt_simple(original_code: str, minimal_code: str, ktest_inputs: dict) -> str:
    """
    Constructs a prompt for the LLM to determine whether remapping of KLEE test inputs is needed,
    and if so, to return a Python function to do the remapping.
    """
    return ktest_inverse_prompt_minimal_stub.format(
        FULL_ORIGINAL_CODE=original_code,
        MINIMAL_CODE=minimal_code,
        TESTCASE_AS_DICT=str(ktest_inputs)
    )

import re

def extract_remap_function(response: str) -> str | None:
    """
    Extracts the remap_testcase Python function from an LLM response.
    Returns None if 'NO_TRANSLATION_NEEDED' is found.
    """
    if "NO_TRANSLATION_NEEDED" in response:
        return None

    # Try to extract from code block
    match = re.search(r"```(?:python)?\s*(def remap_testcase\(.*?\n(?:.*\n)*?)```", response)
    if match:
        return match.group(1).strip()

    # Fallback: find start of the function in plaintext
    lines = response.strip().splitlines()
    in_function = False
    collected = []
    for line in lines:

        if line.strip().startswith("def remap_testcase("):
            in_function = True
        if line.startswith("import ") or line.startswith("from"):
            collected.append(line.strip())
        
        if in_function:
            if line != "```":
                collected.append(line)
    return "\n".join(collected).strip() if collected else None
def save_remap_function(code: str, filepath: str = "remap_testcase.py"):
    with open(filepath, "w") as f:
        f.write(code)

def apply_remap_on_ktests(model, original_code, transformed_code, input_dir, remap_path=None):


    remap_code_path = os.path.join(input_dir, "remap_testcase.py")
    
    first_ktest = glob.glob(os.path.join(input_dir, "*.ktest"))[0]
    print(f"[INFO] Using ktest file: {first_ktest}")
    ktest_info = read_ktest_structured(first_ktest)
    ktest_str= format_ktest_as_string(ktest_info)
    print(f"[INFO] Ktest info: {ktest_str}")
    # print(f"ktest info: {ktest_info}")
    # # text_inputs = ktest_info["objects"]['text']
    # ktest_total_str=""
    # for obj in ktest_info['objects']:
    #     k_test_string = f"Variable {obj['name']} with size {obj['size']} and value in integer format : {obj['text']}"
    #     print(k_test_string)
    #     ktest_total_str += k_test_string + "\n"

    # print(f"[INFO] Original inputs: {ktest_str}")
    if remap_path and os.path.exists(remap_path):
        remap_code = open(remap_path).read()
        print(f"[INFO] Found existing remap_testcase.py at {remap_path}. Skipping model generation.")
    else:
        print(f"[INFO] No remap_testcase.py found. Generating with model...")
        prompt= build_ktest_mapping_prompt(
            original_code=original_code,
            transformed_code=transformed_code,
            ktest_inputs=ktest_str
        )
        resp= model.query(prompt)
        remap_code= extract_remap_function(resp)
    if remap_code is None:
        print("No translation needed. Skipping transformation.")
        return
    
    save_remap_function(remap_code, remap_code_path)

    
    spec = importlib.util.spec_from_file_location("remap_testcase", remap_code_path)
    remap_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(remap_module)

    for ktest_path in glob.glob(os.path.join(input_dir, "*.ktest")):
        ktest_dict = read_ktest_structured(ktest_path)
        original_inputs = {obj["name"]: obj["bytes"] for obj in ktest_dict["objects"]}
        remapped_inputs = remap_module.remap_testcase(original_inputs)
        print(f"Remapped inputs: {remapped_inputs} from original inputs: {original_inputs}")

        new_name = "remapped_"+os.path.splitext(os.path.basename(ktest_path))[0] + ".ktest"
        output_path = os.path.join(input_dir, new_name)

        write_ktest_file(ktest_path, remapped_inputs, output_path)
        print(f"Transformed {ktest_path} -> {output_path}")



def get_covered_lines_for_ktest(docker_name, exe_path, c_file_path, ktest_path):
    """
    Runs one ktest on ghost_coverage inside docker and returns a set of covered line numbers.
    """
    coverage_dir = os.path.dirname(exe_path)
    profraw = f"{coverage_dir}/single.profraw"
    profdata = f"{coverage_dir}/single.profdata"
    cov_output = f"{coverage_dir}/single_cov.txt"

    # Run test with profile output
    replay_cmd = (
        f"cd {coverage_dir} && "
        f"export LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH && "
        f"LLVM_PROFILE_FILE={profraw} "
        f"KTEST_FILE={ktest_path} {exe_path}"
    )
    docker_bash(docker_name, replay_cmd, check=True)

    # Merge to profdata
    docker_bash(docker_name, f"llvm-profdata merge -sparse {profraw} -o {profdata}", check=True)

    # Show coverage to text file
    cov_cmd = (
        f"llvm-cov show {exe_path} "
        f"-instr-profile={profdata} "
        f"--path-equivalence . "
        f"-format=text {c_file_path} > {cov_output}"
    )
    docker_bash(docker_name, cov_cmd, check=True)

    # Retrieve and parse covered lines
    result = subprocess.run(
        ["docker", "exec", docker_name, "cat", cov_output],
        capture_output=True,
        text=True,
        check=True
    )

    covered_lines = set()
    for line in result.stdout.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        try:
            lineno = int(parts[0].strip())
        except ValueError:
            continue
        count_str = parts[1].strip()
        if count_str != "0" and not count_str.startswith("#####"):
            covered_lines.add(lineno)

    return covered_lines


def apply_remap_on_single_ktest(model, original_code, minimal_code, input_dir, ktest_path):
    assert os.path.exists(ktest_path), f"KTest path {ktest_path} does not exist."

    # input_dir = os.path.dirname(ktest_path)
    remap_code_path = os.path.join(input_dir, "remap_testcase_simple.py")

    if os.path.exists(remap_code_path):
        print(f"[INFO] Found existing remap_testcase_simple.py at {remap_code_path}. Skipping model generation.")
    else:
        print(f"[INFO] No remap_testcase_simple.py found. Generating with model...")
        ktest_info = read_ktest_structured(ktest_path)
        ktest_str = format_ktest_as_string(ktest_info)

        prompt = build_ktest_mapping_prompt(
            original_code=original_code,
            minimal_code=minimal_code,
            ktest_inputs=ktest_str
        )
        resp = model.query(prompt)
        remap_code = extract_remap_function(resp)

        if remap_code is None:
            print("No remapping code extracted. Skipping remap.")
            return

        save_remap_function(remap_code, remap_code_path)

    # Import remap function
    spec = importlib.util.spec_from_file_location("remap_testcase_simple", remap_code_path)
    remap_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(remap_module)

    # Apply remapping
    ktest_dict = read_ktest_structured(ktest_path)
    original_inputs = {obj["name"]: obj["bytes"] for obj in ktest_dict["objects"]}
    remapped_inputs = remap_module.remap_testcase(original_inputs)
    print(f"[INFO] Remapped inputs: {remapped_inputs} from original inputs: {original_inputs}")

    # Save output
    base = os.path.splitext(os.path.basename(ktest_path))[0]
    output_path = os.path.join(input_dir, f"remapped_simple_{base}.ktest")
    #if it already exists, add a counter after the remapped_simple_
    if os.path.exists(output_path):
        print(f"[WARNING] Output path {output_path} already exists. Adding counter.")
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(input_dir, f"remapped_simple_{base}_{counter}.ktest")
            counter += 1
    write_ktest_file(ktest_path, remapped_inputs, output_path)

    print(f"[✅] Remapped {ktest_path} → {output_path}")

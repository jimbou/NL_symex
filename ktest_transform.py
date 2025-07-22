
import glob

import struct
import importlib.util
import os
from ktest import read_ktest_structured, format_ktest_as_string, write_ktest_file

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
3. One **example symbolic test case**  in the ktest format from running KLEE on the transformed version.

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
* You **only modify inputs relevant to the transformed region**.

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
Don't focus only on the example test case. Use it as a guide to understand how the transformation works, but apply the same logic to any input that would be used in the original code by reversing the difference between the original and transformed code.
The remapping function should be general enough to handle any input that would be used in the original code, not just the example provided.
## Your Output

Return only the Python function `remap_testcase(...)` as described above.
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
        if in_function:
            collected.append(line)
    return "\n".join(collected).strip() if collected else None
def save_remap_function(code: str, filepath: str = "remap_testcase.py"):
    with open(filepath, "w") as f:
        f.write(code)

def apply_remap_on_ktests(model, original_code, transformed_code, input_dir):


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

        new_name = os.path.splitext(os.path.basename(ktest_path))[0] + "_updated.ktest"
        output_path = os.path.join(input_dir, new_name)

        write_ktest_file(ktest_path, remapped_inputs, output_path)
        print(f"Transformed {ktest_path} -> {output_path}")
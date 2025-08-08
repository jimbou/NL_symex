import re
import os
PROMPT_COMPLEX = """
You are given a C function. This function originally contained a section that is hard to analyze with a symbolic execution tool like KLEE. That section was marked between two custom markers:

```c
assume_NL_start();
...
assume_NL_stop();
````
We are now removing that region entirely, and your job is to produce the **minimal code necessary** to ensure that the overall function still compiles and runs under standard C and symbolic execution tools such as KLEE.

---

Here is the full original function:

```
{c_function}
````

Here is the specific code region being removed:

```
{NL_code}
```

---

### Your Task:
Your goal is to replace the removed block with **as little code as possible**, while ensuring:

1. The resulting program compiles.
2.  Any **variables defined inside the removed code and used later** that were dependent on the symbolic inputs in the now removed code, but were not originally symbolic themselves (i.e., not made symbolic), then assign them the symbolic inputs they were dependent on directly (or parts of them if they were dependent on parts of the symbolic inputs).

3. Any **variables defined inside the removed code and used later** that were not dependent on symbolic inputs should be:

   * Declared with the correct type.
   *Assigned dummy values if needed for compilation.
3. If such variables are the symbolic inputs for klee , then:

   * They must be re-declared (if necessary) and
   * Made symbolic again using `klee_make_symbolic` (i.e., havoced).
4. If the program already compiles without any replacement code, return nothing.
 Do **not** preserve functionality or correctness. Do **not** simulate the removed logic. Do **not** insert comments or excessive stubs. Your only goal is compilability and KLEE executability.

Be especially careful to:

* Match the types of any variables that must be declared.
* Use `klee_make_symbolic` on variables that were previously symbolic and whose values are now undefined due to removal.
* Use `klee_assume` if a constraint is **strictly necessary** to prevent crashes (e.g., log, sqrt, array index).

---
So to summarise, if the variable is not used later forget about it, 
if it is used later and was not symbolic before or dependent on a symbolic var before, declare it with a dummy value, 
if it was not symbolic before but dependent on a symbolic var before, declare it with the same type and assign it the symbolic var,
if it was symbolic before, make it symbolic again.

### Output Format

Explain your reasoning  and then provide only the replacement code in the format:

REPLACEMENT_CODE_START
code
REPLACEMENT_CODE_END

If no replacement is needed, simply return an empty string between the markers.
REPLACEMENT_CODE_START

REPLACEMENT_CODE_END
"""

PROMPT = """
You are given a C function. This function originally contained a section marked as 'natural language code' between custom markers `assume_NL_start;` and `assume_NL_stop;`. We are now removing that part.

Here is the original function (with the NL block included):

{c_function}

Here is the NL block we are removing:
{NL_code}


Your task is to determine the **minimal replacement** required for the code to remain compilable and runnable. 
Ideally we want just to remove the code and replace it with nothing. But we need to ensure that the resulting file is compilable. If the code can compile and run simply by removing the NL block, then do not return any replacement.

If there are undeclared variables or dependencies introduced in the NL block that are used later, please introduce only the **minimal placeholder code** (such as variable declarations or dummy assignments) required to preserve compilation.
Pls do not add any additional code or comments that are not strictly necessary for compilation.

We do not care about correctness or functionality — we only care that the resulting C function compiles.

Explain your reasoning  and then provide only the replacement code in the format:

REPLACEMENT_CODE_START
code
REPLACEMENT_CODE_END

If no replacement is needed, simply return an empty string between the markers.
REPLACEMENT_CODE_START

REPLACEMENT_CODE_END
"""


def extract_minimal(response_content: str) -> str:
    match = re.search(
        r'REPLACEMENT_CODE_START\s*(.*?)\s*REPLACEMENT_CODE_END',
        response_content,
        re.DOTALL
    )
    if match:
        return match.group(1).strip()
    else:
        raise ValueError("No replacement code found in response.")


def extract_c_code(response):
    """
    Extract the C code block from the LLM response.
    It tries to find ```c ... ``` first, then ``` ... ```, then falls back to the whole text.
    """
    # Try to find ```c ... ```
    code_blocks = re.findall(r"```c\s*(.*?)```", response, re.DOTALL)
    if code_blocks:
        return code_blocks[0].strip()
    
    # Try to find any ```
    code_blocks = re.findall(r"```(?:[^\n]*)\n(.*?)```", response, re.DOTALL)
    if code_blocks:
        return code_blocks[0].strip()
    
    # Try to find ''' (alternative sometimes used)
    code_blocks = re.findall(r"'''(?:[^\n]*)\n(.*?)'''", response, re.DOTALL)
    if code_blocks:
        return code_blocks[0].strip()

    # Fallback: whole response
    return response.strip()

def extract_nl_block(code: str) -> str:
    """
    Extracts the lines between 'assume_NL_start' and 'assume_NL_stop' markers,
    excluding the marker lines themselves.
    Returns the code block as a single string.
    """
    lines = code.splitlines()
    start_idx = end_idx = -1

    for i, line in enumerate(lines):
        if "assume_NL_start" in line:
            start_idx = i
        elif "assume_NL_stop" in line:
            end_idx = i
            break

    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        raise ValueError("Markers not found or in wrong order.")

    block_lines = lines[start_idx + 1:end_idx]
    return "\n".join(block_lines)


def get_minimal(model, code_path, minimal_file_path):
    #read the code form the code_path
    with open(code_path, 'r') as f:
        code = f.read()
    #extract the NL code
    NL_code = extract_nl_block(code)
    prompt = PROMPT_COMPLEX.format(c_function=code, NL_code=NL_code)
    response = model.query(prompt)
    response=extract_minimal(response)
    #replace between the markers
    response = extract_c_code(response)
    #in the original c code, replace between the assume_NL_start and assume_NL_stop with the response
    minimal = apply_replacement_and_save(
        original_code=code,
        replacement_code=response,
        output_path=minimal_file_path
    )
    return  minimal

def apply_replacement_and_save(original_code: str, replacement_code: str, output_path: str):
    start_marker = "assume_NL_start"
    end_marker = "assume_NL_stop"

    lines = original_code.splitlines()
    start_idx = end_idx = -1

    for i, line in enumerate(lines):
        if start_marker in line:
            start_idx = i
        if end_marker in line:
            end_idx = i
        if start_idx != -1 and end_idx != -1:
            break

    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        raise ValueError("Markers not found or invalid order in original code.")

    # Build new list of lines
    new_lines = []
    new_lines.extend(lines[:start_idx])
    new_lines.append("// #assume_NL_start();")

    # Insert replacement code lines
    for repl_line in replacement_code.strip().splitlines():
        new_lines.append(repl_line.rstrip())

    new_lines.append("// #assume_NL_stop();")
    new_lines.extend(lines[end_idx + 1:])

    # Join and remove #include "assume.h" if it exists
    cleaned = "\n".join(new_lines)
    # cleaned = re.sub(r'#include\s+["<]assume\.h[">]\s*\n?', '', cleaned)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(cleaned + "\n")

    print(f"[✓] Saved modified file to {output_path}")
    return cleaned

# def run_minimal_symex(minimal_file_path_in_docker, ktest_local_path):
def insert_klee_assume_in_main(lines):
    """
    Insert `klee_assume(reached_NL);` before every `return` inside `main()`.
    """
    in_main = False
    brace_depth = 0
    updated_lines = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'\s*int\s+main\s*\(', line):
            in_main = True

        if in_main:
            brace_depth += line.count('{')
            brace_depth -= line.count('}')

            if stripped.startswith('return') and 'reached_NL' not in stripped:
                indent = re.match(r'^(\s*)', line).group(1)
                updated_lines.append(f"{indent}if (!reached_NL) klee_silent_exit(0);")

        updated_lines.append(line)

        if in_main and brace_depth == 0:
            in_main = False  # we've exited main()

    return updated_lines


def get_minimal_prefix(original_code_path) -> str:
    print(f"[INFO] Generating minimal prefix code for code in: {original_code_path}")
    with open(original_code_path, 'r') as f:
        original_code = f.read()
    lines = original_code.splitlines()

    # Step 1: insert global flag after last #include
    include_end = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("#include"):
            include_end = i + 1
    new_lines = lines[:include_end]
    new_lines.append("int reached_NL = 0;")
    new_lines.extend(lines[include_end:])

    # Step 2: replace code between assume_NL_start and assume_NL_stop
    inside_nl_block = False
    updated_lines = []
    for line in new_lines:
        if not inside_nl_block and "assume_NL_start" in line:
            inside_nl_block = True
            indent = re.match(r'^(\s*)', line).group(1)
            updated_lines.append(line)
            updated_lines.append(f"{indent}reached_NL = 1;")
            updated_lines.append(f"{indent}klee_assert(0);")
            continue
        if inside_nl_block and "assume_NL_stop" in line:
            inside_nl_block = False
            updated_lines.append(line)
            continue
       
        updated_lines.append(line)
        # skip all lines inside the NL block

    # Step 3: insert klee_assume before every return in main()
    final_lines = insert_klee_assume_in_main(updated_lines)
    #add the #include <assert.h> at the first line
    if not any('#include <assert.h>' in line for line in final_lines):
        final_lines.insert(0, '#include <assert.h>')
    return "\n".join(final_lines)


def get_reachable_line_simple(original_code_path, target_line_number) -> str:
    
    with open(original_code_path, 'r') as f:
        original_code = f.read()
    lines = original_code.splitlines()

    # Step 1: insert global flag after last #include
    

    # Step 2: replace code between assume_NL_start and assume_NL_stop
    updated_lines = []
    for i, line in enumerate(lines):
        if i == target_line_number - 1:  # target line (1-indexed)
            indent = re.match(r'^(\s*)', line).group(1)
            updated_lines.append(f'{indent}printf("Reached target line\\n");')
         
        updated_lines.append(line)

        # skip all lines inside the NL block

    #
    #add the #include <assert.h> at the first line
    if not any('#include <stdio.h>' in line for line in updated_lines):
        updated_lines.insert(0, '#include <stdio.h>')
    return "\n".join(updated_lines)

def get_reachable_line_klee(original_code_path, target_line_number) -> str:
    print(f"[INFO] Generating minimal prefix code for code in: {original_code_path}")
    with open(original_code_path, 'r') as f:
        original_code = f.read()
    lines = original_code.splitlines()

   
    # Step 2: replace code between assume_NL_start and assume_NL_stop
    updated_lines = []
    for i, line in enumerate(lines):
        if i == target_line_number - 1:  # target line (1-indexed)
            indent = re.match(r'^(\s*)', line).group(1)
            # updated_lines.append(f'{indent}printf("Reached target line\\n");')
            updated_lines.append(f'{indent}reached_NL = 1;')
        updated_lines.append(line)

        # skip all lines inside the NL block
     # Step 1: insert global flag after last #include
    include_end = 0
    for i, line in enumerate(updated_lines):
        if line.strip().startswith("#include"):
            include_end = i + 1
    new_lines = updated_lines[:include_end]
    new_lines.append("int reached_NL = 0;")
    new_lines.extend(updated_lines[include_end:])

    # Step 3: insert klee_assume before every return in main()
    final_lines = insert_klee_assume_in_main(new_lines)
    #add the #include <assert.h> at the first line
    
    return "\n".join(final_lines)
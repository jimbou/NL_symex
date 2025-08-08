from model import get_model
import re
import os
import subprocess
import shutil

PROMPT = """
You are a C program analysis assistant.

You are given the full C source code of a function and a **specific line** in the code that we want to ensure is **covered during testing**.

---

## Your Task:

Add a series of **printf statements** to print the values of variables that are **critical to reaching the specified line**.

Be **conservative and precise**. A variable is considered **critical** if it satisfies all of the following:
1. it is declared or written in the part between `assume_NL_start();` and `assume_NL_stop();`
1. After the `assume_NL_stop();` it **influences the control flow that leads to the specified line**, meaning it is:
   - used in an `if`, `while`, `for`, or `switch` condition that guards the target line
   - used in a `return` whose value is then used in a condition influencing the line
   - used as an argument to a function whose return influences a branch that leads to the target line

2. It must be **read** before reaching the target line (not just written to).

3. Prefer **direct dependencies**, but include **indirect ones** only if they are clearly linked to the control flow reaching the line.

---

## Instrumentation Format

1. Print the variables in the format:

```c
printf("Variable VAR_NAME = FORMAT_SPECIFIER of type TYPE\n", VAR_NAME);
````

For example:

```c
printf("Variable a = %d of type int\n", a);
printf("Variable x = %f of type float\n", x);
```

2. If a variable is of type `float` or `double`, **try to cast or treat it as `int` if doing so allows the program to compile and behave as expected**.

3. Do **not** print variables that are:
   * are not written or read in the  part of the code between `assume_NL_start();` and `assume_NL_stop();`
   * written but never read before the target line
   * unrelated to the control flow leading to the line
   * we care about the conrol flow after `assume_NL_stop();`, so do not print variables that are only used before it



## Inputs:

You are given:

* The **full C source code** of a function
* The **line number** of the line we want to ensure is covered (1-based indexing)
* The **exact string** of the target line (to help you locate it)

Use this information to reason about which variables affect control flow leading to that line.

---

## Output Format

* First explain your reasoning clearly and briefly.
* Then write the line: `PRINT STATEMENTS START NOW`
* Then output the `printf` lines, one per line, exactly as they would appear in the code. Do **not** include any extra text or markdown.

---

## Example Output

Reasoning:
The line `if (x > 3)` is guarded by `if (x > 3)` and depends on `x`.

PRINT STATEMENTS START NOW
printf("Variable x = %d of type int\n", x);

---

## Code to Analyze:

```c
{original_code}
```

## Line to Cover:

Line {line_number}:
{line_content}
"""



def extract_tracking_prints(llm_response: str) -> list[str]:
    """
    Extract printf statements from the LLM response.
    """
    lines = llm_response.strip().splitlines()
    return [line.strip() for line in lines if line.strip().startswith("printf")]

## ✅ Step 3: Insert Tracking Code After `assume_NL_stop();`



def insert_var_tracking_prints(original_code: str, print_lines: list[str]) -> str:
    """
    Inserts the print_lines wrapped with START and END markers
    right after the line containing assume_NL_stop();
    """
    lines = original_code.splitlines()
    new_lines = []
    inserted = False

    for line in lines:
        new_lines.append(line)
        if not inserted and "assume_NL_stop();" in line:
            indent = re.match(r'^(\s*)', line).group(1)
            new_lines.append(f'{indent}printf("== SYMBOLIC VARS START ==\\n");')
            print(f"adding {len(print_lines)} print lines")
            for print_line in print_lines:
                new_lines.append(indent + print_line)
            new_lines.append(f'{indent}printf("== SYMBOLIC VARS END ==\\n");')
            inserted = True

    return "\n".join(new_lines)


## ✅ Step 4: File Handling Wrapper




def generate_code_with_var_tracking(c_file_path: str, llm_response: str) -> str:
    """
    Reads a C file, extracts the printf lines from an LLM response,
    inserts them after assume_NL_stop(), and saves the new code.
    """
    assert os.path.exists(c_file_path), f"File not found: {c_file_path}"
    with open(c_file_path, 'r') as f:
        original_code = f.read()

    print_lines = extract_tracking_prints(llm_response)
    new_code = insert_var_tracking_prints(original_code, print_lines)
    #if include stdio.h is not in the code then add it at the top
    if '#include <stdio.h>' not in new_code:
        new_code = '#include <stdio.h>\n' + new_code

    output_path = c_file_path.replace(".c", "_with_varTracking.c")
    with open(output_path, 'w') as f:
        f.write(new_code)

    print(f"[✅] Tracking code saved to {output_path}")
    return output_path

def create_model_log_based_name(model_name, log_folder, suffix):
    """
    Create a log folder name based on the model name and suffix.
    """
    log_folder_new= os.path.join(log_folder, suffix)

    # Ensure the log folder exists
    if not os.path.exists(log_folder_new):
        os.makedirs(log_folder_new)
    
    
    print(f"[INFO] Created log folder: {log_folder_new}")
    return get_model(model_name, 0.5, log_folder_new)


def extract_prints_after_marker(llm_response: str) -> str:
    """
    Extracts the printf statements from the LLM response after the marker.
    """
    # Find the start of the PRINT STATEMENTS section
    start_marker = "PRINT STATEMENTS START NOW"
   
    
    start_index = llm_response.find(start_marker)
    if start_index == -1:
        return llm_response.strip()  # If marker not found, return the whole response
    
    # Extract everything after the start marker
    relevant_part = llm_response[start_index + len(start_marker):].strip()
    
    #return the string relevant_part
    return relevant_part

def get_klee_assumes(C_code_path, log_folder, line_number: int, line_content: str, model_name= "gpt-4.1"):
    #read the code form the code_path
    with open(C_code_path, 'r') as f:
        code = f.read()
    #extract the NL code
    #add line numbers to the code
    lines = code.splitlines()
    numbered_lines = [f"{i+1}: {line}" for i, line in enumerate(lines)]
    code_with_line_numbers = "\n".join(numbered_lines)
    #find the line with assume_NL_start
    prompt = PROMPT.format(original_code=code_with_line_numbers,line_number=line_number, line_content=line_content)
    model_assumes= create_model_log_based_name(model_name, log_folder, "get_klee_assumes")
    response = model_assumes.query(prompt)
    response= extract_prints_after_marker(response)
    
    #
    output_path = generate_code_with_var_tracking(C_code_path, response)
    output_declare_path= generate_code_with_var_declarations_and_symbolics(C_code_path, response)
    return output_path, output_declare_path





def run_replay_with_ktest(
    local_c_file: str,
    local_ktest_file: str,
    docker_dir: str,
    docker_name="klee_logic_bombs",
    docker_script_path="/home/klee/make_klee_executable.sh"
):
    """
    1. Copies C file and KTest file into `docker_dir` inside Docker container.
    2. Runs the executable generation script inside Docker.
    3. Executes the program using the .ktest file and captures output.
    """

    assert os.path.exists(local_c_file), f"C file does not exist: {local_c_file}"
    assert os.path.exists(local_ktest_file), f"KTest file does not exist: {local_ktest_file}"

    c_filename = os.path.basename(local_c_file)
    ktest_filename = os.path.basename(local_ktest_file)
    exe_name = os.path.splitext(c_filename)[0]
    docker_c_path = os.path.join(docker_dir, c_filename)
    docker_ktest_path = os.path.join(docker_dir, ktest_filename)
    docker_exe_path = os.path.join(docker_dir, exe_name)
    trace_path = os.path.join(docker_dir, f"{exe_name}_trace.txt")

    #if the dir does not exist inside docket then create it
    print(f"[📁] Ensuring directory exists in Docker: {docker_dir}" )
    subprocess.run(["docker", "exec", docker_name, "mkdir", "-p", docker_dir], check=True)

    print(f"[📤] Copying C file to Docker: {docker_c_path}")
    subprocess.run(["docker", "cp", local_c_file, f"{docker_name}:{docker_c_path}"], check=True)

    print(f"[📤] Copying KTest file to Docker: {docker_ktest_path}")
    subprocess.run(["docker", "cp", local_ktest_file, f"{docker_name}:{docker_ktest_path}"], check=True)

    print(f"[⚙️] Running compilation script in Docker")
    subprocess.run([
        "docker", "exec", docker_name,
        "bash", docker_script_path, docker_c_path, exe_name
    ], check=True)

    print(f"[🚀] Replaying executable with KTest")
    cmd = (
        f"export LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH && "
        f"KTEST_FILE={docker_ktest_path} {docker_exe_path} > {trace_path} 2>/dev/null"
    )
    subprocess.run(["docker", "exec", docker_name, "bash", "-c", cmd], check=True)

    print(f"[📥] Copying trace from Docker to host")
    local_trace_path = os.path.join(os.path.dirname(local_ktest_file), f"{exe_name}_trace.txt")
    subprocess.run(["docker", "cp", f"{docker_name}:{trace_path}", local_trace_path], check=True)

    print(f"[✅] Trace saved to: {local_trace_path}")
    return local_trace_path



import re

def extract_vars_and_generate_single_abs_assumes(trace_file_path, delta=0.5):
    """
    Extracts variable values and types from a trace file and generates one klee_assume per variable:
        klee_assume(fabs(var - rounded_val) <= epsilon);
    """
    in_block = False
    var_dict = {}
    assumes = []

    with open(trace_file_path, 'r') as f:
        for line in f:
            line = line.strip()

            if "== SYMBOLIC VARS START ==" in line:
                in_block = True
                continue
            if "== SYMBOLIC VARS END ==" in line:
                in_block = False
                continue

            if in_block:
                match = re.match(r'Variable\s+(\w+)\s+=\s+([-\d.eE]+)\s+of\s+type\s+(\w+)', line)
                if match:
                    var, val_str, var_type = match.groups()
                    try:
                        val = round(float(val_str))
                        eps = max(1, abs(val)) * delta
                        var_dict[var] = (val, var_type)
                        assumes.append(f'klee_assume(fabs({var} - {val}) <= {eps});')
                    except ValueError:
                        continue

    return var_dict, assumes

def extract_var_names_and_types(print_lines: list[str]) -> list[tuple[str, str]]:

    """
    From lines like printf("Variable d = %f of type float", d);
    extract [('d', 'float')]
    """
    results = []
    pattern = re.compile(r'printf\("Variable (\w+) = .*? of type (\w+)\\n"')
    for line in print_lines:
        match = pattern.search(line)
        if match:
            var_name, var_type = match.groups()
            results.append((var_name, var_type))
    return results

def find_declared_vars(code: str) -> set[tuple[str, str]]:
    """
    Finds already declared variables and their types.
    Returns a set of (var_name, type).
    """
    declared = set()
    pattern = re.compile(r'\b(\w+)\s+(\w+)\s*(=|;|\[)')  # matches `type var;` or `type var = ...`
    for line in code.splitlines():
        match = pattern.search(line)
        if match:
            var_type, var_name = match.group(1), match.group(2)
            declared.add((var_name, var_type))
    return declared


def insert_decls_and_symbolics_after_stop(code: str, vars_and_types: list[tuple[str, str]], declared_vars: set[tuple[str, str]]) -> str:
    """
    Inserts declarations (if missing) and klee_make_symbolic for all variables
    right after the line containing assume_NL_stop();, preserving indentation and the line itself.
    """
    lines = code.splitlines()
    new_lines = []
    inserted = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        if not inserted and "assume_NL_stop();" in line:
            indent = re.match(r'^(\s*)', line).group(1)
            for var_name, var_type in vars_and_types:
                declared_type = "int" if var_type in {"float", "double"} else var_type
                if (var_name, var_type) not in declared_vars and (var_name, declared_type) not in declared_vars:
                    new_lines.append(f"{indent}{declared_type} {var_name};  // originally {var_type}")
                new_lines.append(f'{indent}klee_make_symbolic(&{var_name}, sizeof({var_name}), "{var_name}");')
            inserted = True

    return "\n".join(new_lines)


def remove_lines_between_assume_markers(original_code: str) -> str:
    """
    Keeps the lines containing assume_NL_start(); and assume_NL_stop();,
    but removes all lines in between them.
    """
    lines = original_code.splitlines()
    start_idx = stop_idx = -1

    for i, line in enumerate(lines):
        if "assume_NL_start();" in line:
            start_idx = i
        elif "assume_NL_stop();" in line:
            stop_idx = i
            break

    if start_idx == -1 or stop_idx == -1:
        print("[⚠️] Warning: assume_NL_start or assume_NL_stop not found in the code. Skipping variable declaration insertion.")
        return original_code

    # Preserve lines before start, the start line, the stop line, and after stop
    new_lines = lines[:start_idx + 1] + lines[stop_idx:]
    return "\n".join(new_lines)

def generate_code_with_var_declarations_and_symbolics(c_file_path: str, llm_response: str) -> str:
    """
    Reads a C file and an LLM response,
    extracts variable declarations and adds them after assume_NL_stop,
    adding klee_make_symbolic calls for each.
    """
    assert os.path.exists(c_file_path), f"File not found: {c_file_path}"
    with open(c_file_path, 'r') as f:
        original_code = f.read()

    #remove from the original code the lines between assume_NL_start and assume_NL_stop but keep the lines with assume_NL_start and assume_NL_stop
    original_code = remove_lines_between_assume_markers(original_code)

    # Extract printf lines and parse variable names/types
    print_lines = extract_tracking_prints(llm_response)
    vars_and_types = extract_var_names_and_types(print_lines)

    # Scan for existing declarations
    declared_vars = find_declared_vars(original_code)

    # Insert declarations and klee_make_symbolic lines after assume_NL_stop
    new_code = insert_decls_and_symbolics_after_stop(original_code, vars_and_types, declared_vars)

    # Add includes if needed
    if '#include <klee/klee.h>' not in new_code:
        new_code = '#include <klee/klee.h>\n' + new_code
    if '#include <stdio.h>' not in new_code:
        new_code = '#include <stdio.h>\n' + new_code

    output_path = c_file_path.replace(".c", "_with_varDecls.c")
    with open(output_path, 'w') as f:
        f.write(new_code)

    print(f"[✅] Declarations + symbolic code saved to {output_path}")
    return output_path

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate KLEE assumes for a C function.")
    parser.add_argument("--c_file_path", type=str, help="Path to the C file containing the function.")
    parser.add_argument("--log_folder", type=str, default="logs", help="Folder to save logs and outputs.")
    parser.add_argument("--model_name", required=False, type=str, default="gpt-4.1", help="Name of the model to use for querying.")
    parser.add_argument("--ktest_path", type=str, help="Path to the KTest file for replay.")
    parser.add_argument("--docker_dir", type=str, help="Directory inside Docker to use for processing.")
    parser.add_argument("--docker_name",required=False, type=str, default="klee_logic_bombs", help="Name of the Docker container.")
    parser.add_argument("--local_assume_path",required=False, type=str, help="Path to the C file with inserted assumes.")
    parser.add_argument("--line_number",required=False, type=int, help="Line number to extract variables and assumes.")
    parser.add_argument("--line_content",required=False, type=str, help="Content of the line to extract variables and assumes.")

    args = parser.parse_args()
    if args.local_assume_path:
        local_assume_path= args.local_assume_path
    else:

        local_assume_path, local_declare_path= get_klee_assumes(args.c_file_path, args.log_folder, args.line_number, args.line_content, args.model_name)


    local_trace_path= run_replay_with_ktest(
        local_c_file= local_assume_path,
        local_ktest_file= args.ktest_path,
        docker_dir= args.docker_dir,
        docker_name= args.docker_name

    )
    var_dict, assumes = extract_vars_and_generate_single_abs_assumes(local_trace_path)
    print(f"[📊] Extracted {len(var_dict)} variables from trace.")
    print(f"The assumes generated are:")
    for assume in assumes:
        print(assume)   

if __name__ == "__main__":
    main()
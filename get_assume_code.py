import os
import sys
import subprocess
import json
import re

klee_line_prompt = """\
You are analyzing a C program to help improve its compatibility with a symbolic execution engine like KLEE.

Here is the code, with line numbers:
----------------------------
{original_code}
----------------------------

The following lines were **not covered** during symbolic execution:
{uncovered_lines}

To assist symbolic execution, we annotate parts of the code that are difficult for the engine to reason about using two markers:

- `assume_NL_start();` – placed **before** a region of difficult code
- `assume_NL_stop();` – placed **after** the region

This region is later translated or abstracted into simpler, more tractable code.

Symbolic execution engines typically struggle with the following kinds of code constructs:

- **Hidden/implicit inputs**: `getpid()`, `getenv()`, `rand()`, reading from files, system calls
- **Covert flows**: writing to disk, launching shell commands, inter-process communication
- **Buffer overflows**: e.g. unchecked `strcpy`, `memcpy`
- **Indirect memory access**: symbolic array indices, pointer arithmetic, function pointer jumps
- **External computation**: `sin()`, `sqrt()`, cryptographic functions (e.g., `SHA1`, `AES`), inline assembly
- **Unbounded or symbolic loops**: loops with symbolic bounds or unknown termination
- **Concurrency or signals**: multithreading, interrupts, signal handlers
- **OS-specific behavior**: `stat()`, `open()`, `execve()`
- **Pointer aliasing**: multiple symbolic names for the same memory
- **Floating point or overflow logic**: rounding, integer wraparound
- **Standard input/output**: `scanf`, `fgets`, `printf`

**Your task:**  
Given the uncovered lines and the code, determine a minimal continuous region of code that contains the uncovered logic and might be responsible for symbolic execution failure. Then:

Tell me:
1. After which line number I should insert `assume_NL_start();`
2. After which line number I should insert `assume_NL_stop();`

Use this strict JSON format as your output (no comments, no prose):

{{
  "insert_after_start": LINE_NUMBER,
  "insert_after_stop": LINE_NUMBER
}}
"""



def parse_lines(response_text):
    try:
        match = re.search(r'{.*}', response_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            raise ValueError("No JSON block found.")
    except Exception as e:
        raise ValueError("Failed to parse response: " + str(e))

def get_klee_lines(model, code, uncovered_lines):
    prompt = klee_line_prompt.format(original_code= code, uncovered_lines=uncovered_lines)
    response = model.query(prompt)
    lines= parse_lines(response)
    return lines

def insert_assume_markers(source_path, insert_after_start, insert_after_stop, output_path):
    with open(source_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for idx, line in enumerate(lines, start=1):
        new_lines.append(line)
        if idx == insert_after_start:
            new_lines.append("    assume_NL_start();\n")
        if idx == insert_after_stop:
            new_lines.append("    assume_NL_stop();\n")

    with open(output_path, 'w') as f:
        f.writelines(new_lines)
    return new_lines

def get_assume_code(model, source_path, output_path, uncovered):
    # Read the source code
    with open(source_path, 'r') as f:
        source_code = f.readlines()

    # Convert the uncovered set into a string list of lines with numbers and content
    uncovered_str = "\n".join(f"{lineno}: {line}" for lineno, line in sorted(uncovered))

    # Generate the LLM response suggesting where to insert assume_NL markers
    lines = get_klee_lines(model, source_code, uncovered_str)

    # Parse the LLM output (assumed to be in JSON format)
    cleaned_lines = parse_lines(lines)
    insert_start_line = cleaned_lines.get("insert_after_start")
    insert_stop_line = cleaned_lines.get("insert_after_stop")

    # Insert assume_NL_start/stop and write to new file
    output_code = insert_assume_markers(source_path, insert_start_line, insert_stop_line, output_path)
    return output_code




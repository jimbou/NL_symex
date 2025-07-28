import re
import sys

def instrument_c_file(input_path, output_path):
    with open(input_path, 'r') as f:
        lines = f.readlines()

    inside_nl = False
    branch_id = 0
    instrumented_lines = []

    # Patterns to detect branch-related constructs
    branch_patterns = [
    r'^\s*if\s*\(.*\)\s*{?\s*$',          # if (...)
    r'^\s*else\s+if\s*\(.*\)\s*{?\s*$',    # else if (...)
    r'^\s*else\s*{?\s*$',                 # else or else {
    r'^.*\}\s*else\s*{?\s*$',             # } else {
    r'^\s*while\s*\(.*\)\s*{?\s*$',       # while (...)
    r'^\s*for\s*\(.*\)\s*{?\s*$',         # for (...)
    r'^\s*do\s*{?\s*$',                   # do
    r'^\s*switch\s*\(.*\)\s*{?\s*$',      # switch (...)
    r'^\s*case\s+.*:\s*$',                # case ...
    r'^\s*default\s*:\s*$',               # default:
]


    def should_instrument(line):
        return any(re.match(pat, line) for pat in branch_patterns)

    for i, line in enumerate(lines):
        stripped = line.strip()

        if 'assume_NL_stop' in stripped:
            inside_nl = True

        instrumented_lines.append(line)

        if inside_nl and should_instrument(stripped):
            indent = ' ' * (len(line) - len(line.lstrip()))
            trace_line = f'{indent}TRACE({branch_id});\n'
            instrumented_lines.append(trace_line)
            branch_id += 1

    with open(output_path, 'w') as f:
        f.writelines(instrumented_lines)

    print(f"Instrumented {branch_id} branches. Output: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python instrument_branches.py input.c output.c")
    else:
        instrument_c_file(sys.argv[1], sys.argv[2])

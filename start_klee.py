import re

klee_main_prompt = """
You are given a C file that defines one or more functions, but does not include a `main()` function.

Your task is to write a standalone `main()` function that enables symbolic execution of this code using the KLEE engine.

Your `main()` must:
- Declare appropriate symbolic inputs (e.g., `char input[8];` or `int x;`)
- Use `klee_make_symbolic()` to make inputs symbolic
- Optionally use `klee_assume()` if needed to constrain symbolic values
- Call the relevant function(s) with those inputs
- Include `#include <klee/klee.h>` at the top of the output
- Ensure any symbolic strings are null-terminated

Output format:
Return **only** the full `main()` function and the required includes that are not already present in the original code.
Do not return the original function(s) or any other code.
Do NOT include or modify the original code.
Do NOT add any explanation or markdown formatting.

Here is the original C code:
{original_code}
"""


def extract_main_function(response_content: str) -> str:
    match = re.search(r"```(?:c)?(.*?)```", response_content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback if no formatting, just plain C text
    if "main" in response_content:
        return response_content.strip()

    raise ValueError("No valid C main function found in the response.")


def get_klee_suitable(model, code):
    prompt = klee_main_prompt.format(original_code= code)
    response = model.query(prompt)
    main_func= extract_main_function(response)
    return main_func


def merge_and_save(model, original_path: str, output_path: str):
    """
    Reads the original code from `original_path`, appends the generated main() from `main_response`,
    and writes the full result to `output_path`.
    """
    with open(original_path, 'r') as f:
        original_code = f.read()
    main_response = get_klee_suitable(model, original_code)
    main_code = extract_main_function(main_response)

    # Avoid duplicate includes
    if '#include <klee/klee.h>' in original_code:
        original_code = re.sub(r'#include\s*<klee/klee.h>', '', original_code)

    if '#include <klee/klee.h>' in main_code:
        main_code = re.sub(r'#include\s*<klee/klee.h>', '', main_code)
    
    original_includes = set(re.findall(r'#include\s*<[^>]+>', original_code))
    main_includes = set(re.findall(r'#include\s*<[^>]+>', main_code))

    # 2. Remove includes from main_code that are already in original_code
    for inc in original_includes:
        main_code = main_code.replace(inc, '')
    merged_code = "#include <klee/klee.h>\n\n"+ original_code.rstrip() + "\n\n" + main_code.strip() + "\n"

    with open(output_path, 'w') as f:
        f.write(merged_code)

    print(f"Saved instrumented C file to: {output_path}")
    return merged_code


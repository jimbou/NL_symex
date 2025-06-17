import re

PROMPT_GEN_MAIN_FOR_KLEE = """
You are given a C function (do not modify it). Your job is to write a minimal `main()` function for **KLEE symbolic execution**.

Requirements:
- Assume the function is defined in the same file
- Use `#include <klee/klee.h>` (but don't include the function again)
- Create symbolic inputs using `klee_make_symbolic(...)` with meaningful variable names
- Call the function with those symbolic inputs
- Wrap the code like this:

MAIN_FOR_KLEE_START
<your main() with klee_make_symbolic calls>
MAIN_FOR_KLEE_END
"""

def extract_klee_main(response: str) -> str:
    match = re.search(r'MAIN_FOR_KLEE_START\s*(.*?)\s*MAIN_FOR_KLEE_END', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        raise ValueError("KLEE main block not found.")

def create_klee_main(model, original_code: str):
    

    # Send the function only (not whole code if possible)
    prompt = PROMPT_GEN_MAIN_FOR_KLEE.format()
    prompt += f"\n\nFunction to test:\n```\n{original_code}\n```"

    response = model.query(prompt)
    klee_main_code = extract_klee_main(response)
    # remove #include <klee/klee.h>
    klee_main_code = klee_main_code.replace('#include <klee/klee.h>', '').strip()
    final_code = "#include <klee/klee.h>\n\n" + original_code.strip() + "\n\n" + klee_main_code

    return final_code, klee_main_code

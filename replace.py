import re


PROMPT_REWRITE_C = """
You are given a C function that includes a missing or complex block of code marked between `assume_NL_start;` and `assume_NL_stop;`.

Here is the full function:
```

{c_function}

```

And here is the missing or natural-language-defined block:
```

{NL_code}

```

Your job is to **rewrite this block into compilable C code** that:
- Mimics the likely functionality described in the block
- Avoids external libraries or complex control flow
- Is easy to analyze with symbolic execution engines like **KLEE**
- Uses only simple operations, fixed loops, arrays, conditionals, etc.
- Avoids pointer aliasing, heap allocation, recursion, or dynamic behavior

Output only the **replacement code** for that block.
Wrap your response with:

C_REWRITE_START
... (your code here)
C_REWRITE_END
"""



def extract_c_rewrite(response: str) -> str:
    match = re.search(r'C_REWRITE_START\s*(.*?)\s*C_REWRITE_END', response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        raise ValueError("Could not find rewritten C code in response.")


def get_rewritten_c_block(model, full_code: str, nl_block: str) -> str:
    prompt = PROMPT_REWRITE_C.format(c_function=full_code, NL_code=nl_block)
    response = model.query(prompt)
    return extract_c_rewrite(response)


def rewrite_and_replace(model, full_code: str, nl_code: str) -> str:
    if not full_code or not nl_code:
        raise ValueError("Full code or NL code is empty")

    start = full_code.find("assume_NL_start;")
    end = full_code.find("assume_NL_stop;")
    if start == -1 or end == -1:
        raise ValueError("Missing NL markers")

    prefix = full_code[:start].rstrip()
    # nl_block = full_code[start + len("assume_NL_start;"): end].strip()
    suffix = full_code[end + len("assume_NL_stop;"):].lstrip()

    replacement_code = get_rewritten_c_block(model, full_code, nl_code)

    new_code = prefix + "\n" + replacement_code + "\n" + suffix

    

    print(f"[✓]  rewritten function is  {new_code}")
    return new_code



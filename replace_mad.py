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

If the behavior is not identical but covers a **subset of valid inputs**, it's okay to suggest adding a `klee_assume(...)` to restrict the input domain.
Output only the **replacement code** for that block.
Wrap your response with:

C_REWRITE_START
... (your code here)
C_REWRITE_END
"""

PROMPT_CRITIC = """
You are reviewing a proposed replacement for a missing block of code in a C function. The original code contained a fragment marked as `assume_NL_start; ... assume_NL_stop;`, which has now been replaced with a simpler block.

Your job is to assess whether the replacement is **acceptable** for symbolic execution purposes:
- Exact equivalence is NOT required.
- The new code must have the same **effect on the function's variables**, even approximately.
- It must be simple enough for symbolic engines (e.g., KLEE) — avoid recursion, pointers, dynamic allocations.

If the behavior is not identical but covers a **subset of valid inputs**, it's okay to suggest adding a `klee_assume(...)` to restrict the input domain.

---

Function context:

{c_function}

Original removed NL part or code:

{NL_code}
Proposed replacement:


{rewritten_code}
Please respond in this format:

ASSESSMENT_START
Write here ACCEPTABLE  or NOT_ACCEPTABLE
ASSESSMENT_END

CRITIC_START
Your reasoning, what's missing, and what could improve the replacement.
CRITIC_END
"""


PROMPT_REWRITE_C_MAD = """
You are given a C function that includes a missing or complex block of code marked between `assume_NL_start;` and `assume_NL_stop;`.

Here is the full function:
```

{c_function}

```

And here is the missing or natural-language-defined block:

```
{NL_code}

```
We have attempted to rewrite  this block into compilable C code that:
- Mimics the likely functionality described in the block
- Avoids external libraries or complex control flow
- Is easy to analyze with symbolic execution engines like **KLEE**
- Uses only simple operations, fixed loops, arrays, conditionals, etc.
- Avoids pointer aliasing, heap allocation, recursion, or dynamic behavior

The rewritten code is:
{rewritten_code}

But we got this critisism that the rewritten code is not acceptable because it does not have the same effect to the variables as the original code.
The critisism is:

{critic}

Your job is to **rewrite this block into compilable C code taking into account the critisism.
If the behavior is not identical but covers a **subset of valid inputs**, it's okay to suggest adding a `klee_assume(...)` to restrict the input domain.
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

def extract_assessment(response: str) -> str:
    match = re.search(r'ASSESSMENT_START\s*(.*?)\s*ASSESSMENT_END', response, re.DOTALL)
    if not match:
        raise ValueError("Assessment block missing")
    return match.group(1).strip().upper()

def extract_critic_feedback(response: str) -> str:
    match = re.search(r'CRITIC_START\s*(.*?)\s*CRITIC_END', response, re.DOTALL)
    if not match:
        raise ValueError("Critique block missing")
    return match.group(1).strip()

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


def debate_rewrite(model, full_code: str, nl_code: str, max_attempts: int = 3) -> str:
    start = full_code.find("assume_NL_start;")
    end = full_code.find("assume_NL_stop;")
    if start == -1 or end == -1:
        raise ValueError("Missing NL markers")

    prefix = full_code[:start].rstrip()
    suffix = full_code[end + len("assume_NL_stop;"):].lstrip()

    attempt = 0
    rewritten_code = get_rewritten_c_block(model, full_code, nl_code)

    while attempt < max_attempts:
        print(f"\n Attempt {attempt+1} — Critiquing replacement...")

        prompt_critic = PROMPT_CRITIC.format(
            c_function=full_code,
            NL_code=nl_code,
            rewritten_code=rewritten_code
        )
        response = model.query(prompt_critic)
        assessment = extract_assessment(response)
        critique = extract_critic_feedback(response)

        print(f"\n ASSESSMENT: {assessment}")
        print(f" CRITIQUE:\n{critique}")

        if "not" not in assessment.lower() :
            break

        prompt_improve = PROMPT_REWRITE_C_MAD.format(
            c_function=full_code,
            NL_code=nl_code,
            rewritten_code=rewritten_code,
            critic=critique
        )
        improved_response = model.query(prompt_improve)
        rewritten_code = extract_c_rewrite(improved_response)
        attempt += 1

    final_code = prefix + "\n" + rewritten_code + "\n" + suffix
    print("\n[✓] Final version assembled.")
    return final_code
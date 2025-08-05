import re

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
2. Any **variables defined inside the removed code and used later** are:

   * Declared with the correct type.
   * Optionally assigned dummy values if needed for compilation.
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

def get_minimal(model, code, NL_code):
    prompt = PROMPT_COMPLEX.format(c_function=code, NL_code=NL_code)
    response = model.query(prompt)
    return extract_minimal(response)



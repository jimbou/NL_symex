
import os
import re

PROMPT_SMT_FULL = """
You are helping translate part of a C function into SMT-LIBv2 format for symbolic execution.

The function contains a region marked by `assume_NL_start;` and `assume_NL_stop;`. This region is missing and will be replaced by constraints over input/output variables.

Function context:


{c_function}



Missing block (could be in NAtural language, code or a mix):


{NL_code}

Precondition path constraints (path constraints before this block):


{precondition}


Postcondition path constraints: (path constraints before this block):
{postcondition}
 

* Translate the NL block to SMT constraints consistent with the inputs/outputs described.
* Reuse variable names or declare them if needed.
* Use logic appropriate for **KLEE** (e.g., bitvectors and arrays).
* Focus on modeling **data flow and logic** from the NL block only — do not re-express pre/post constraints.

Wrap your output strictly between:

SMT\_START <your SMT2 code>
SMT\_END

---

"""


def get_smt_constraints(model, full_code: str, nl_block: str, precondition: str, postcondition: str) -> str:
    prompt = PROMPT_SMT_FULL.format(
        c_function=full_code,
        NL_code=nl_block,
        precondition=precondition,
        postcondition=postcondition
    )
    response = model.query(prompt)
    return extract_smt(response)



def extract_smt(response_content: str) -> str:
    match = re.search(
        r'SMT_START\s*(.*?)\s*SMT_END',
        response_content,
        re.DOTALL
    )
    if match:
        return match.group(1).strip()
    else:
        raise ValueError("No SMT block found in response.")


import re

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
    prompt = PROMPT.format(c_function=code, NL_code=NL_code)
    response = model.query(prompt)
    return extract_minimal(response)



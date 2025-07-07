import re
import json

analyze_prompt = """
You are a symbolic execution assistant.

Given the following C code:

--------------------
{code}
--------------------

Determine which of the following categories (one or multiple) this code falls into.
Respond with your reasoning and then  with a JSON list of category numbers (like `[3]` or `[1, 7]`).

Here are the categories:

1. Symbolic Variable Declarations
   - Implicit inputs like process IDs, environment vars, or file contents that are not declared symbolic.

2. Covert Propagations
   - Symbolic values passed indirectly via files, shell commands, or IPC, breaking direct data flow tracking.

3. Buffer Overflows
   - Symbolic data overflowing buffers to overwrite adjacent memory, needing explicit assertions.

4. Parallel Executions
   - Symbolic data processed in parallel threads, creating interleaved orders invisible to sequential symbolic execution.

5. Symbolic Memories
   - Symbolic indices or pointers used in arrays, leading to many memory paths or incomplete exploration.

6. Contextual Symbolic Values
   - Symbolic values passed to environment-dependent calls like `fopen` on symbolic filenames.

7. Symbolic Jumps
   - Symbolic values used in indirect jumps or function pointer arrays, hiding control flow.

8. Floating-Point Numbers
   - Computations using floats/doubles with rounding and precision issues hard for SMT solvers.

9. Arithmetic Overflows
   - Integer operations relying on wrapping behavior (e.g., signed 32-bit overflows).

10. External Function Calls
    - Use of library functions like `sin`, `atoi`, or `sqrt` whose internals are not modeled.

11. System Calls
    - OS calls like `read`, `stat`, `execve` whose behavior depends on external system state.

12. Loops
    - Loops with symbolic or data-dependent bounds that can explode into many paths.

13. Cryptographic Functions
    - Using hashes or ciphers (SHA1, AES) that can't be inverted by symbolic solvers.

14. Non-deterministic Inputs
    - Inputs from `rand()`, `/dev/urandom`, or `time` that are not automatically symbolic.

15. Signal or Interrupt Handling
    - Programs using `signal` handlers or hardware interrupts, causing asynchronous control flow.

16. Inline Assembly and Hardware Instructions
    - Using inline assembly or CPU-specific instructions that are not preserved in LLVM IR.

17. Pointer Aliasing and Complex Data Aliasing
    - Multiple pointers (or indices) that might alias the same memory, requiring explicit equality constraints.

Return a JSON array of category numbers indicating which issues are present.
"""



symbolic_declarations = """
Category: Symbolic Variable Declarations

## The problem
Programs often rely on values obtained implicitly at runtime, like process IDs (`getpid()`), 
environment variables (`getenv()`), or file contents (`fread()`), which are not explicitly 
declared as symbolic. Tools like KLEE treat these as fixed concrete values, exploring only 
one path and missing alternative feasible executions.

## How to fix it
Rewrite the code to:
- Replace implicit inputs with explicit symbolic variables using `klee_make_symbolic`.
- Add `klee_assume` constraints if needed to reflect realistic bounds.



## Example

### Original code
#include <stdio.h>
#include <unistd.h>

int main() {
    int pid = getpid();
    if (pid % 2 == 0) {
        printf("Even PID\\n");
    } else {
        printf("Odd PID\\n");
    }
}

### Transformed code
#include <stdio.h>
#include <klee/klee.h>

int main() {
    int pid;
    klee_make_symbolic(&pid, sizeof(pid), "pid");
    klee_assume(pid > 0);

    if (pid % 2 == 0) {
        printf("Even PID\\n");
    } else {
        printf("Odd PID\\n");
    }
}


"""

covert_propagations = """
Category: Covert Propagations

## The problem
Some programs pass symbolic values indirectly, like writing to files and reading them back, 
using shell commands (e.g., `echo`), or inter-process communication. These covert data flows 
break standard symbolic execution, because tools like KLEE do not track values outside the 
program’s memory, treating re-read data as concrete.

## How to fix it
Rewrite the code to:
- Eliminate indirect data flows and instead pass symbolic values directly in memory.
- Replace file or shell operations with direct assignments that keep data under symbolic control.

## Example

### Original code
#include <stdio.h>
#include <stdlib.h>

int main() {
    int x;
    scanf("%d", &x);  // user input becomes symbolic with KLEE normally
    char cmd[50];
    sprintf(cmd, "echo %d > temp.txt", x);
    system(cmd);

    FILE *fp = fopen("temp.txt", "r");
    int y;
    fscanf(fp, "%d", &y);
    fclose(fp);

    if (y == 42) {
        printf("Special case!\\n");
    }
}

### Transformed code
#include <stdio.h>
#include <klee/klee.h>

int main() {
    int x;
    klee_make_symbolic(&x, sizeof(x), "x");

    int y = x;  // direct propagation in memory

    if (y == 42) {
        printf("Special case!\\n");
    }
}
"""

buffer_overflows = """
Category: Buffer Overflows

## The problem
Programs that copy symbolic data into fixed-size buffers without checks can overwrite 
adjacent variables (like flags), causing classic buffer overflow bugs. Symbolic execution 
may miss these if symbolic data is not explicitly represented in memory or if there's no 
property to prove.

## How to fix it
Rewrite the code to:
- Declare the input buffer explicitly symbolic.
- Add assertions (e.g., `klee_assert`) to help KLEE discover violating inputs that exploit 
  the overflow.

## Example

### Original code
int logic_bomb(char* symvar) {
    int flag = 0;
    char buf[8];
    strcpy(buf, symvar);
    if(flag == 1){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}

### Transformed code
#include <string.h>
#include <klee/klee.h>

int logic_bomb() {
    int flag = 0;
    char buf[8];
    char symvar[20];

    klee_make_symbolic(symvar, sizeof(symvar), "symvar");

    strcpy(buf, symvar);

    klee_assert(flag != 1);

    if(flag == 1){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}
"""


parallel_executions = """
Category: Parallel executions

## The problem
Parallel programs process symbolic data across multiple threads, creating execution orders 
that depend on the system scheduler. Classic symbolic execution builds a sequential control-flow 
graph and cannot model interleaved memory updates, so it misses possible outcomes from parallel code.

## How to fix it
Rewrite parallel code to an equivalent sequential program that conservatively models 
different interleavings, using symbolic variables or explicit branches to simulate 
thread order effects.

## Example

### Original code
int threadprop(int in){
    pthread_t tid[2];
    pthread_create(&tid[0], NULL, Inc, (void *) &in);
    pthread_create(&tid[1], NULL, Mult, (void *) &in);
    pthread_join(tid[0], NULL);
    pthread_join(tid[1], NULL);
    return in;
}

int logic_bomb(char* symvar) {
    int i = symvar[0] - 48;
    int j = threadprop(i);
    if(j == 50){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int inc(int x) { return x + 1; }
int mult(int x) { return x * 2; }

int threadprop(int in){
    int nondet;
    klee_make_symbolic(&nondet, sizeof(nondet), "nondet");
    klee_assume(nondet >= 0 && nondet <= 2);

    int out;
    if (nondet == 0) {
        out = mult(inc(in));
    } else if (nondet == 1) {
        out = inc(mult(in));
    } else {
        klee_make_symbolic(&out, sizeof(out), "out");
    }
    return out;
}

int logic_bomb() {
    int i;
    klee_make_symbolic(&i, sizeof(i), "i");
    klee_assume(i >= 0 && i <= 9);

    int j = threadprop(i);
    if(j == 50){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}
"""


symbolic_memories = """
Category: Symbolic memories

## The problem
Programs often use symbolic variables as array indices or pointers, 
such as `array[i]`. This forces the symbolic engine to consider 
many possible memory accesses, causing exponential path exploration 
or incomplete handling. Some tools concretize these indices, 
missing feasible behaviors.

## How to fix it
Rewrite the code to:
- Expand symbolic memory reads into explicit branches (`if` or `switch`) 
for each possible index. This ensures symbolic execution clearly 
tracks each path without relying on implicit array theory.

## Example

### Original code
int logic_bomb(char* symvar) {
    int i = symvar[0]-48;
    int array[] ={1,2,3,4,5};
    if(array[i%5] == 5){
        return BOMB_ENDING;
    }
    else
        return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int logic_bomb() {
    int i;
    klee_make_symbolic(&i, sizeof(i), "i");
    klee_assume(i >= 0 && i <= 9);

    int index = i % 5;
    int value;

    if (index == 0)
        value = 1;
    else if (index == 1)
        value = 2;
    else if (index == 2)
        value = 3;
    else if (index == 3)
        value = 4;
    else
        value = 5;

    if(value == 5){
        return BOMB_ENDING;
    }
    else
        return NORMAL_ENDING;
}
"""
contextual_symbolic_values = """
Category: Contextual symbolic values

## The problem
Programs sometimes pass symbolic values into environment-dependent calls, 
like `fopen(symvar, "r")` or accessing symbolic filenames. The behavior 
then depends on external state (like the actual file system), which is 
not modeled by symbolic execution. Tools like KLEE cannot explore 
whether files exist or what their contents are.

## How to fix it
Rewrite the code by introducing explicit symbolic booleans that represent 
the possible outcomes (like file existence), letting symbolic execution 
explore all branches without relying on the real environment.

## Example

### Original code
int logic_bomb(char* symvar) {
    FILE *fp = fopen(symvar, "r");
    if(fp != NULL){
        fclose(fp);
        return BOMB_ENDING;
    } else {
        return NORMAL_ENDING;
    }
}

### Transformed code
#include <klee/klee.h>

int logic_bomb() {
    int file_exists;
    klee_make_symbolic(&file_exists, sizeof(file_exists), "file_exists");
    klee_assume(file_exists == 0 || file_exists == 1);

    if(file_exists){
        return BOMB_ENDING;
    } else {
        return NORMAL_ENDING;
    }
}
"""


symbolic_jumps_balanced = """
Category: Symbolic jumps (balanced exploration of critical and normal paths)

## The problem
Programs may use symbolic values to control indirect jumps, such as selecting 
from a function pointer array. This hides the control flow from the symbolic 
executor, preventing it from generating path constraints to cover all cases, 
especially critical or rare execution paths.

## How to fix it
Rewrite indirect jumps into explicit conditional branches (`if` or `switch`) 
so the symbolic execution engine can track all control flows. To ensure 
symbolic execution explores interesting or dangerous paths (like the one 
triggering a BOMB_ENDING), add a `klee_assert` inside these branches. 
This encourages exploration of critical paths while still allowing normal 
execution analysis.

## Example

### Original code
int f0() {return 0;} ... int f6() {return 6;}

int logic_bomb(char* symvar) {
    int (*func[7])() = {f0, f1, f2, f3, f4, f5, f6};
    int ret = func[(symvar[0] - 48)%7]();
    if(ret == 5){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int logic_bomb() {
    int i;
    klee_make_symbolic(&i, sizeof(i), "i");
    klee_assume(i >= 0 && i <= 99);

    int selector = (i - 48) % 7;
    int ret;

    if (selector == 0) ret = 0;
    else if (selector == 1) ret = 1;
    else if (selector == 2) ret = 2;
    else if (selector == 3) ret = 3;
    else if (selector == 4) ret = 4;
    else if (selector == 5) {
        ret = 5;
        klee_assert(ret != 5); // explicitly force symbolic execution to test this critical path
    }
    else ret = 6;

    if(ret == 5){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}
"""


floating_point_numbers = """
Category: Floating-point numbers

## The problem
Floating-point numbers approximate real numbers using fixed bit layouts (IEEE-754). 
This introduces rounding errors, limited precision, and makes equalities and 
inequalities over floats difficult to reason about symbolically. Tools like KLEE 
struggle to extract and solve precise constraints over floats.

## How to fix it
Rewrite the code to:
- Replace floating-point computations with scaled integer equivalents (fixed-point), 
preserving relative comparisons while making constraints bit-precise.
- This lets symbolic execution explore all branches correctly without complex 
floating-point reasoning.

## Example

### Original code
int logic_bomb(char* symvar) {
    float a = (symvar[0] - 48) * 0.1;
    float b = 0.7;
    if (a != 1 && a == b){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int logic_bomb() {
    int i;
    klee_make_symbolic(&i, sizeof(i), "i");
    klee_assume(i >= 0 && i <= 9);

    // Scale to simulate fixed-point arithmetic
    int a = i * 1; // equivalent to (i * 0.1) * 10
    int b = 7;

    if (a != 10 && a == b){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}
"""


arithmetic_overflows = """
Category: Arithmetic overflows

## The problem
Arithmetic overflows happen when computations exceed the representable range of 
integer types, wrapping around due to modular semantics. For example, multiplying 
large positive numbers can result in a negative value under 32-bit signed arithmetic. 
Some symbolic execution tools miss such cases if they reason over real numbers 
instead of modeling modular integer behavior.

## How to fix it
Most modern symbolic execution engines like KLEE already use modular arithmetic. 
However, to be explicit and portable:
- Use fixed-width types like `int32_t` to clearly indicate wraparound behavior.
- Keep computations as they are, allowing symbolic execution to discover 
overflow-triggered paths naturally.

## Example

### Original code
int logic_bomb(char* symvar) {
    int i = symvar[0] - 48;
    if (254748364 * i < 0 && i > 0){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}

### Transformed code
#include <stdint.h>
#include <klee/klee.h>

int logic_bomb() {
    int32_t i;
    klee_make_symbolic(&i, sizeof(i), "i");

    klee_assume(i > 0);

    int32_t prod = 254748364 * i; // explicit modular arithmetic
    if (prod < 0){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}
"""


external_function_calls = """
Category: External function calls

## The problem
Programs often rely on external library functions (like `sin`, `atoi`, `sqrt`) 
for computations. Since these functions are dynamically linked or opaque to the 
symbolic engine, their internal control flows and constraints are invisible. 
If these outputs are used in later conditions, symbolic execution may miss 
critical paths.

## How to fix it
Rewrite the code to:
- Replace external function calls with explicit approximations, either via 
piecewise functions, look-up tables, or symbolic variables with carefully 
chosen assumptions. This ensures the symbolic execution engine can still 
reason about possible outputs and explore all relevant branches.

## Example

### Original code
int logic_bomb(char* symvar) {
    int i = symvar[0] - 48;
    float v = sin(i * PI / 30);
    if(v > 0.5){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int logic_bomb() {
    int i;
    klee_make_symbolic(&i, sizeof(i), "i");
    klee_assume(i >= 0 && i <= 30);

    float v;
    // Piecewise approximation of sin
    if (i < 5)
        v = 0.1;
    else if (i < 10)
        v = 0.3;
    else if (i < 15)
        v = 0.6;
    else
        v = 0.9;

    if(v > 0.5){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}
"""


system_calls = """
Category: System calls

## The problem
System calls like `read`, `write`, `open`, `stat`, or `execve` interact with 
the operating system, depending on external state such as the file system or 
process table. Symbolic execution engines typically cannot model the full 
OS environment, so they either skip system calls or concretize their results, 
missing alternative paths.

## How to fix it
Rewrite system call dependent code to:
- Replace system call results with explicit symbolic variables that capture 
possible outcomes, adding `klee_assume` constraints as needed.
- This abstracts external OS state into symbolic inputs, allowing exploration 
of all relevant branches.

## Example

### Original code
int logic_bomb(char* symvar) {
    if (stat(symvar, &info) == 0) {
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int logic_bomb() {
    int file_exists;
    klee_make_symbolic(&file_exists, sizeof(file_exists), "file_exists");
    klee_assume(file_exists == 0 || file_exists == 1);

    if(file_exists == 1){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}
"""


loops = """
Category: Loops

## The problem
Loops are a major source of path explosion in symbolic execution. 
Loops with symbolic or data-dependent conditions may generate an 
unbounded number of paths, making it infeasible for the engine 
to explore exhaustively.

## How to fix it
Rewrite the code by:
- Unrolling the loop a fixed number of times explicitly, then 
adding `klee_assume` constraints to enforce that it terminates 
within that bound.
- This ensures the symbolic engine explores only a manageable 
number of paths, without diverging.

## Example

### Original code
int f(int x){
    if (x % 2 == 0)
        return x / 2;
    return 3 * x + 1;
}

int logic_bomb(char* symvar) {
    int i = symvar[0]-48+94;
    int j = f(i);
    int loopcount = 1;

    while(j != 1){
        j = f(j);
        loopcount++;
    }
    if(loopcount == 25)
        return BOMB_ENDING;
    else
        return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int f(int x){
    if (x % 2 == 0)
        return x / 2;
    return 3 * x + 1;
}

int logic_bomb() {
    int i;
    klee_make_symbolic(&i, sizeof(i), "i");
    klee_assume(i >= 0 && i <= 100);

    int j = f(i);
    int loopcount = 1;

    // Unroll a few iterations
    if(j != 1){
        j = f(j); loopcount++;
    }
    if(j != 1){
        j = f(j); loopcount++;
    }
    if(j != 1){
        j = f(j); loopcount++;
    }
    if(j != 1){
        j = f(j); loopcount++;
    }

    // Enforce max bound to avoid infinite symbolic paths
    klee_assume(loopcount <= 25);

    if(loopcount == 25)
        return BOMB_ENDING;
    else
        return NORMAL_ENDING;
}
"""

cryptographic_functions = """
Category: Cryptographic functions

## The problem
Cryptographic functions like SHA1, MD5, AES are specifically designed 
to be computationally hard to invert. Constraints like `SHA1(x) == y` 
are impossible for symbolic execution to solve, so the tool either fails 
or concretizes these expressions, missing important control flows.

## How to fix it
Rewrite the code by:
- Replacing cryptographic computations with fresh symbolic variables 
representing the output (the digest or encrypted data).
- Use assumptions or direct symbolic predicates to allow exploration of 
both match and non-match cases.

## Example

### Original code
if (SHA1_COMP(plaintext, cipher) == 0){
    return BOMB_ENDING;
} else {
    return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int logic_bomb() {
    int match;
    klee_make_symbolic(&match, sizeof(match), "match");
    klee_assume(match == 0 || match == 1);

    if(match){
        return BOMB_ENDING;
    } else {
        return NORMAL_ENDING;
    }
}
"""


non_deterministic_inputs = """
Category: Non-deterministic inputs beyond symbolic arguments

## The problem
Programs often obtain values from non-deterministic sources such as `rand()`, 
`random()`, `/dev/urandom`, or `time()`. These are not automatically treated 
as symbolic inputs by symbolic execution tools, which means the tool only 
explores a single concrete execution path, missing many possible behaviors.

## How to fix it
Rewrite the code to:
- Replace non-deterministic calls with explicit symbolic variables using 
`klee_make_symbolic`. This ensures all potential outcomes are explored.

## Example

### Original code
#include <stdlib.h>

int logic_bomb() {
    int r = rand();
    if (r % 10 == 7) {
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int logic_bomb() {
    int r;
    klee_make_symbolic(&r, sizeof(r), "r");

    if (r % 10 == 7) {
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}
"""


signal_interrupt_handling = """
Category: Signal or interrupt handling

## The problem
Programs may use signals or hardware interrupts (like `signal(SIGINT, handler)`) 
to handle asynchronous events, causing control flow to jump unpredictably to 
handlers. This behavior is not visible in the static CFG and is not naturally 
modeled by symbolic execution tools, which only track explicit sequential flow.

## How to fix it
Rewrite the code to:
- Replace or simulate the interrupt effect with explicit symbolic variables 
(e.g., `interrupted`) and assumptions to model whether the signal was received. 
This allows the symbolic engine to explore both interrupted and uninterrupted paths.

## Example

### Original code
#include <signal.h>
#include <stdio.h>

int interrupted = 0;

void handler(int sig) {
    interrupted = 1;
}

int logic_bomb() {
    signal(SIGINT, handler);
    if(interrupted){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int logic_bomb() {
    int interrupted;
    klee_make_symbolic(&interrupted, sizeof(interrupted), "interrupted");
    klee_assume(interrupted == 0 || interrupted == 1);

    if(interrupted){
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}
"""

inline_assembly = """
Category: Inline assembly and hardware-specific instructions

## The problem
Programs may use inline assembly or CPU-specific instructions 
(e.g., reading special segment registers or hardware counters). 
LLVM often cannot preserve these semantics in IR, so symbolic execution 
tools either skip, havoc, or misinterpret these instructions. This 
breaks symbolic data flow and can miss critical paths.

## How to fix it
Rewrite the code to:
- Replace the result of inline assembly or hardware instructions with 
explicit symbolic variables using `klee_make_symbolic`. This models 
their uncertain outcomes and lets the symbolic engine explore 
dependent branches.

## Example

### Original code
int logic_bomb() {
    int val;
    __asm__("movl %%gs:0, %0" : "=r"(val));
    if (val == 42) {
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}

### Transformed code
#include <klee/klee.h>

int logic_bomb() {
    int val;
    klee_make_symbolic(&val, sizeof(val), "val");

    if (val == 42) {
        return BOMB_ENDING;
    }
    return NORMAL_ENDING;
}
"""
pointer_aliasing_explicit = """
Category: Pointer aliasing and complex data aliasing

## The problem
Programs often use multiple pointers that explicitly alias the same 
memory location, like `int *p = &array[i]; int *q = p;`. Without explicit 
constraints, symbolic execution might explore unnecessary cases or 
fail to understand that writes through `p` must be seen through `q`.

## How to fix it
Rewrite the code by:
- Using simple array indexing with symbolic indices.
- Adding `klee_assume(i == j);` to enforce that both indices point to 
the same location, precisely modeling the aliasing of `p` and `q`.

## Example

### Original code
int *p = &array[i];
int *q = p;
*p = 42;
if(*q == 42){
    return BOMB_ENDING;
}

### Transformed code (explicit aliasing)
#include <klee/klee.h>

int logic_bomb() {
    int array[10] = {0};
    int i, j;

    klee_make_symbolic(&i, sizeof(i), "i");
    klee_make_symbolic(&j, sizeof(j), "j");
    klee_assume(i >= 0 && i < 10);
    klee_assume(j >= 0 && j < 10);
    klee_assume(i == j);  // explicitly force aliasing effect

    array[i] = 42;

    if (array[j] == 42) {
        return BOMB_ENDING;
    }
    return NORMAL_ENDING; // this is effectively unreachable because i == j
}
"""

rewrite_prompt_template = """
You are a symbolic execution assistant.

The user is working with KLEE, a symbolic execution engine for C code. 
They want to explore more execution paths, but their code contains constructs 
that are difficult for symbolic execution tools to analyze (e.g., indirect memory, 
system calls, external functions, loops, etc.).

You are given:
1. The original C code that contains symbolic execution challenges.
2. A list of relevant transformation strategies to guide rewriting.

Your task is:
- Identify the part(s) of the original code that fall under the listed categories.
- Rewrite those parts into code that is **equivalent in behavior**, but **better suited for symbolic execution** with tools like KLEE.
- Ensure the final code is **compilable** and that functionality (i.e., return values, branching logic, and I/O behavior) is preserved.
- Use constructs like `klee_make_symbolic`, `klee_assume`, and optionally `klee_assert` where appropriate.

Only rewrite the minimal necessary fragment(s) — not the whole program if it’s not needed. Be precise and KLEE-compatible.

---

### Original C Code:
```c
{CODE_SNIPPET}

### Relevant Transformation Strategies

{RELEVANT_PROMPTS}


## Now rewrite the problematic part(s) of the code and return the transformed version in the follwoing format:
### Transformed C Code:
Start_of_transformed_code
```c
TRANSFORMED_CODE
```
End_of_transformed_code
"""

category_prompt_dict = {
    1: symbolic_declarations,
    2: covert_propagations,
    3: buffer_overflows,
    4: parallel_executions,
    5: symbolic_memories,
    6: contextual_symbolic_values,
    7: symbolic_jumps_balanced,
    8: floating_point_numbers,
    9: arithmetic_overflows,
    10: external_function_calls,
    11: system_calls,
    12: loops,
    13: cryptographic_functions,
    14: non_deterministic_inputs,
    15: signal_interrupt_handling,
    16: inline_assembly,
    17: pointer_aliasing_explicit
}

import re

def extract_transformed_code(response: str) -> str:
    # Use regex to capture between the markers
    pattern = r"Start_of_transformed_code.*?```c(.*?)```.*?End_of_transformed_code"
    match = re.search(pattern, response, re.DOTALL)

    if match:
        code_block = match.group(1).strip()
        return code_block
    else:
        raise ValueError("No transformed C code block found in response.")



def extract_categories(llm_output: str):
    start = llm_output.rfind('[')
    end = llm_output.rfind(']') + 1
    categories_json = llm_output[start:end]
    category_numbers = json.loads(categories_json)
    if category_numbers:
        return  category_numbers
    else:
        raise ValueError("No  category found in response.")

def get_categories(model, code, NL_code):
    prompt = analyze_prompt.format(code=code)
    response = model.query(prompt)
    return extract_categories(response)

def get_category_prompt(category_number: int) -> str:
    if category_number in category_prompt_dict:
        return category_prompt_dict[category_number]
    else:
        raise ValueError(f"Category {category_number} not found.")

def get_all_categories(category_numbers: list) -> str:
    return "\n\n".join(get_category_prompt(num) for num in category_numbers if num in category_prompt_dict)


#given the original code get the categories then get the relevant prompts and msake the final call to get the ocrrected vrsion
def get_rewrite_prompt(model, code, NL_code):
    categories = get_categories(model, code, NL_code)
    relevant_prompts = get_all_categories(categories)
    prompt = rewrite_prompt_template.format(CODE_SNIPPET=code, RELEVANT_PROMPTS=relevant_prompts)
    response = model.query(prompt)
    return extract_transformed_code(response)
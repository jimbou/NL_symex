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


# NL_symex: Symbolic Execution with Natural Language Constraints

##  Project Overview

Traditional symbolic execution interprets programs over symbolic inputs to reason about correctness, coverage, or test generation. However, real-world programs often include **fragments that cannot be interpreted symbolically**, such as:

- External API calls (e.g., cryptographic functions)
- Dynamic-language interop (e.g., Python from C)
- Missing code (e.g., unavailable libraries)
- Logic described only in natural language (e.g., "compute tax for international clients")

These regions are invisible to SMT solvers and often cause symbolic execution to **fail or over-approximate** using `havoc` semantics.

The **NL_symex** project proposes a solution: **model these fragments as natural language constraints**, treating them as uninterpreted functions whose semantics can be inferred using auxiliary tools like large language models (LLMs).

By doing so, we aim to:
- Allow symbolic engines to reason through programs with incomplete code
- Integrate LLMs as soft solvers or oracles during path constraint solving
- Extend the symbolic theory with a new NL-theory (`T_NL`) that supports translation, rewriting, and function inversion

This project builds on the theoretical foundation introduced in:

> **Dimitrios Stamatios Bouras**  
> *Extending Symbolic Execution with Natural Language Constraints*, 2025  
> See: `NL_constraints_symex.pdf`

---

## Implemented So Far

This prototype system focuses on the **preprocessing** stage — preparing C code with natural language fragments for symbolic execution.

###  Assumptions

We assume the original code marks NL code blocks with special markers:

```c
#include "assume.h"

int f(int x) {
    assume_NL_start;
    // Natural language or unavailable code block
    assume_NL_stop;
}
````

Markers:

* `assume_NL_start;`
* `assume_NL_stop;`

These delimit the region to treat as opaque or natural-language defined.

---

### 🔧 Parsing & Preprocessing

* Parses a C program and extracts:

  * `prefix`: everything before the NL block
  * `nl_block`: the code between the markers
  * `suffix`: everything after the NL block

* Writes:

  * `prefix.c`: The prefix made compilable (adds a dummy return)
  * `nl_block.c`: The extracted NL block
  * (later) `modified.c`: Full code with NL replaced

---

###  LLM Integration

* Constructs a prompt for the LLM describing:

  * The full original code
  * The code block to be removed
* Asks: **Can we just remove the NL block, or must we replace it with minimal dummy code to remain compilable?**
* Expected LLM response includes:

```
REPLACEMENT_CODE_START
<int x = 0;> // or empty
REPLACEMENT_CODE_END
```

* The replacement is:

  * Extracted using regex
  * Reinserted into the original program to generate `modified.c`

---

###  Output Structure

If the log folder is `log_temp/`, the tool will produce:

```
log_temp/
├── prefix.c         # Code before NL, made compilable
├── nl_block.c       # The removed NL code
├── modified.c       # The new version with minimal LLM-generated patch
└── total_vars/      # Folder for model logs
```

---

###  CLI Usage

```bash
python extract_nl_code.py \
  --c_code path/to/your.c \
  [--log_folder logs/] \
  [--model deepseek-v3-aliyun]
```

---

###  Model Support

We assume a function `get_model(model_type, temperature, log_dir)` defined in `model.py` that returns an object with:

```python
response = model.query(prompt)
```


### 1. Rewriting to SMT Constraints (Strategy I)

We now support translating the NL block directly into **SMT-LIBv2 constraints** using an LLM, enabling integration with symbolic solvers like KLEE.

- The LLM receives the original function, the NL block, and optionally pre/postconditions.
- It generates a block of SMT constraints wrapped in:

```

SMT\_START
(set-logic QF\_AUFBV)
(declare-fun ...)
(assert ...)
(check-sat)
(exit)
SMT\_END

```

- Output is saved to `nl_block.smt2` for direct use in SMT-based reasoning.

### 2. Rewriting to Executable C Code (Strategy II)

We also support rewriting the NL code block into **concrete C code** that mimics its intended functionality while remaining easy for symbolic execution engines to analyze.

- The LLM is prompted to produce compilable C code that avoids:
  - Dynamic allocation
  - External libraries
  - Recursion or complex control flow

- The result is wrapped in:

```

C\_REWRITE\_START <rewritten C code>
C\_REWRITE\_END

````

- The replacement is inserted in place of the NL block to produce `rewritten.c`.



##  License

MIT License.




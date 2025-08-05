import os
import re
import shutil
import tempfile
import subprocess
from ktest import read_ktest_structured, format_ktest_as_string, write_ktest_file

# You must define KLEE_BIN (e.g., "/klee/build/bin/klee") in your env or here.
KLEE_BIN = "/tmp/klee_build130stp_z3/bin/klee"

def run_klee_in_docker(bc_file_path, output_dir, docker_name="klee_logic_bombs"):
    klee_cmd = [
        "docker", "exec", docker_name,
        KLEE_BIN,
        f"--output-dir={output_dir}",
        "--write-cov",
        "--emit-all-errors",
        bc_file_path
    ]
    subprocess.run(klee_cmd, check=True)


def compile_to_bc_in_docker(c_file_path, docker_name="klee_logic_bombs"):
    """
    Compile a C file to LLVM bitcode (.bc) inside the Docker container.
    `c_file_path` should be absolute inside the container, e.g., /home/klee/tmp_dir/file.c
    """
    bc_file_path = c_file_path.replace(".c", ".bc")
    compile_cmd = [
        "docker", "exec", docker_name,
        "clang", "-emit-llvm", "-c", "-g",
        "-Xclang", "-disable-O0-optnone",
        "-o", bc_file_path, c_file_path
    ]
    subprocess.run(compile_cmd, check=True)
    return bc_file_path


def add_relaxed_klee_assume(ktest_path, c_file_path, docker_name="klee_logic_bombs"):
    assert os.path.exists(ktest_path), f"KTest file not found: {ktest_path}"
    assert os.path.exists(c_file_path), f"C file not found: {c_file_path}"

    ktest_info = read_ktest_structured(ktest_path)

    variable_constraints = []
    for obj in ktest_info['objects']:
        name = obj['name']
        val_list = obj['text']
        if len(val_list) == 1:
            xb = val_list[0]
            variable_constraints.append((name, xb))

    relaxation_factors = [0.1, 0.25, 0.5, 1.0]

    for factor in relaxation_factors:
        # Rebuild code with new relaxation
        with open(c_file_path, 'r') as f:
            code = f.read()

        if '#include <klee/klee.h>' not in code:
            code = '#include <klee/klee.h>\n#include <math.h>\n' + code

        assumes = []
        for name, xb in variable_constraints:
            if xb == 0:
                bound = factor  # use epsilon > 0
            else:
                bound = abs(xb) * factor
            expr = f"klee_assume(fabs({name} - {xb}) <= {bound});"
            assumes.append(expr)

        # Insert assumes right before assume_NL_start
        match = re.search(r'(assume_NL_start\s*\(\s*\)\s*;)', code)
        if not match:
            raise ValueError("Could not find `assume_NL_start();` in the source code.")
        insert_pos = match.start()
        comment = f"// inserted klee_assume relaxation factor = {factor}"
        insertion = f"{comment}\n" + "\n".join("    " + a for a in assumes) + "\n"
        modified_code = code[:insert_pos] + insertion + code[insert_pos:]

        # Save to a temp file
        relabel = f"_relaxed_{str(int(factor * 100))}"
        new_c_path = c_file_path.replace(".c", f"{relabel}.c")
        with open(new_c_path, 'w') as f:
            f.write(modified_code)

        print(f"[🧪] Trying KLEE with relaxed factor {factor} at: {new_c_path}")

        # Compile to .bc
        bc_path = compile_to_bc_in_docker(new_c_path, docker_name=docker_name)
        # Run KLEE in Docker
        tmp_output = tempfile.mkdtemp(prefix=f"klee_relax_{int(factor*100)}_")
        try:
            run_klee_in_docker(bc_path, tmp_output, docker_name=docker_name)
        except subprocess.CalledProcessError as e:
            print(f"[⚠️] KLEE failed to run for factor {factor}")
            continue

        # Check for .ktest output
        ktest_outputs = [f for f in os.listdir(tmp_output) if f.endswith(".ktest")]
        if ktest_outputs:
            print(f"[✅] Found solution at factor {factor}. Saved to {new_c_path}")
            return new_c_path

        print(f"[❌] No solutions found for factor {factor}. Trying next relaxation...")

    print(f"[🚫] No solutions found even after full relaxation.")
    return None

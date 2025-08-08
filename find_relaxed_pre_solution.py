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


def add_relaxed_klee_assume(ktest_path, c_file_path, docker_dir, docker_name="klee_logic_bombs"):
    assert os.path.exists(ktest_path), f"KTest file not found: {ktest_path}"
    assert os.path.exists(c_file_path), f"C file not found: {c_file_path}"
    print(f"[📝] Reading KTest file: {ktest_path}")
    ktest_info = read_ktest_structured(ktest_path)
    print(f"[🔍] KTest info: {ktest_info}")
    variable_constraints = []

    for obj in ktest_info['objects']:
        name = obj.get('name')
        bytes_list = obj.get('bytes', [])

        if isinstance(bytes_list, list) and len(bytes_list) > 0:
            # Extract first byte
            for i in range(len(bytes_list)):
                if isinstance(bytes_list[i], int):
                    variable_constraints.append((f"{name}[{i}]", bytes_list[i]))
        elif isinstance(bytes_list, int):
            # If it's a single integer, treat it as a single byte
            variable_constraints.append((name, bytes_list))
            

    print(f"[🔍] Found {len(variable_constraints)} variable constraints in KTest.")
    for var, val in variable_constraints:
        print(f"  {var} = {val}")

    relaxation_factors = [0.1, 0.25, 0.5, 1.0]

    for factor in relaxation_factors:
        print(f"[🔍] Trying relaxation factor: {factor}")
        # Rebuild code with new relaxation
        with open(c_file_path, 'r') as f:
            code = f.read()

        if '#include <klee/klee.h>' not in code:
            code = '#include <klee/klee.h>\n#include <math.h>\n' + code

        assumes = []
        for name, xb in variable_constraints:
            if xb == 0:
                bound = factor*10  # use epsilon > 0
            else:
                bound = abs(xb) * factor
            expr = f"klee_assume(fabs({name} - {xb}) <= {bound});"
            assumes.append(expr)

        # Insert assumes right before assume_NL_start
        #find the lien with assume_NL_start

        lines = code.splitlines()

        # Locate line index with assume_NL_start
        insert_idx = -1
        for i, line in enumerate(lines):
            if "assume_NL_start" in line:
                insert_idx = i
                break

        if insert_idx == -1:
            raise ValueError("Could not find `assume_NL_start();` in the source code.")

        # Get indentation of the matched line
        indent = re.match(r'^(\s*)', lines[insert_idx]).group(1)
        comment = f"{indent}// inserted klee_assume relaxation factor = {factor}"
        insertion_lines = [comment] + [f"{indent}{a}" for a in assumes]

        # Insert just before the matched line
        lines = lines[:insert_idx] + insertion_lines + lines[insert_idx:]

        # Rejoin the modified code
        modified_code = "\n".join(lines)

        # Save to a temp file
        relabel = f"_relaxed_{str(int(factor * 100))}"
        new_c_path = c_file_path.replace(".c", f"{relabel}.c")
        with open(new_c_path, 'w') as f:
            f.write(modified_code)

        print(f"[🧪] Trying KLEE with relaxed factor {factor} at: {new_c_path}")
        #here we need to copy it in the docker in the right place in the docker_dir
        docker_c_path = os.path.join(docker_dir, os.path.basename(new_c_path))
        #use docker cp to copy the file
        subprocess.run(["docker", "cp", new_c_path, f"{docker_name}:{docker_c_path}"], check=True)
        print(f"[⬆️] Copied modified C file to Docker at: {docker_c_path}")
        # Compile to .bc
        bc_path = compile_to_bc_in_docker(docker_c_path, docker_name=docker_name)
        # Run KLEE in Docker i with tmp output in docker dir
        #you need to create this in the docker
        tmp_output = os.path.join(docker_dir, f"klee_relax_{int(factor*100)}_output")
        subprocess.run([
            "docker", "exec", docker_name, "bash", "-c", f"rm -rf {tmp_output}"
        ], check=True)

        
        try:
            run_klee_in_docker(bc_path, tmp_output, docker_name=docker_name)
        except subprocess.CalledProcessError as e:
            print(f"[⚠️] KLEE failed to run for factor {factor}")
            continue

        # Check for .ktest output
        # ktest_outputs = [f for f in os.listdir(tmp_output) if f.endswith(".ktest")]
        #you need to check inside the docker
        
        list_ktests_cmd = [
                "docker", "exec", docker_name,
                "bash", "-c", f"ls {tmp_output}/*.ktest 2>/dev/null || true"
            ]
        result = subprocess.run(list_ktests_cmd, capture_output=True, text=True)
        ktest_files_in_docker = result.stdout.strip().splitlines()

        if ktest_files_in_docker:
            print(f"[✅] Found solution at factor {factor}. Saved to {new_c_path}")

            # Create local directory to save the ktests
            local_ktest_output = os.path.join(os.path.dirname(new_c_path), f"klee_relax_{int(factor*100)}_ktests")
            os.makedirs(local_ktest_output, exist_ok=True)

            # Copy each .ktest file from docker to host
            for docker_ktest_path in ktest_files_in_docker:
                ktest_filename = os.path.basename(docker_ktest_path)
                local_ktest_path = os.path.join(local_ktest_output, ktest_filename)
                subprocess.run(
                    ["docker", "cp", f"{docker_name}:{docker_ktest_path}", local_ktest_path],
                    check=True
                )
                print(f"[⬇️] Copied {ktest_filename} to {local_ktest_path}")

            return local_ktest_output
import sys
def main():
    if len(sys.argv) <3:
        print("Usage: python add_relaxed_klee_assume.py <ktest_path> <c_file_path> <docker_dir> [docker_name]")
        sys.exit(1)
    ktest_path = sys.argv[1]
    c_file_path = sys.argv[2]
    docker_dir = sys.argv[3]
    docker_name = sys.argv[4] if len(sys.argv) > 4 else "klee_logic_bombs"
    add_relaxed_klee_assume(ktest_path, c_file_path, docker_dir, docker_name)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3

import argparse
import subprocess
import os
import sys
import shutil
import uuid
from branch_ckecker import compare_traces

import subprocess

KLEE_BIN = "/tmp/klee_build130stp_z3/bin/klee"


def get_next_output_dir_in_docker(base="klee-out-analysis", docker_name="klee_logic_bombs"):
    i = 0
    while True:
        candidate = f"{base}-{i}"
        result = subprocess.run(
            ["docker", "exec", docker_name, "test", "!", "-e", candidate],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode == 0:
            return candidate
        i += 1

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

def run_klee_in_docker(bc_file_path, output_dir, docker_name="klee_logic_bombs"):
    """
    Run KLEE inside the Docker container on the given .bc file.
    """
    klee_cmd = [
        "docker", "exec", docker_name,
        KLEE_BIN,
        f"--output-dir={output_dir}",
        "--write-cov",
        "--emit-all-errors",
        bc_file_path
    ]
    subprocess.run(klee_cmd, check=True)



def main():
    parser = argparse.ArgumentParser(description="Run ghost code pipeline in KLEE docker.")
    parser.add_argument("--original", required=True, help="Path to original C file")
    parser.add_argument("--translated", required=True, help="Path to translated (ghost) C file")
    parser.add_argument("--log_folder", default="log_tmp_ghost", help="Folder to save logs and results")
    parser.add_argument("--docker_name", default="klee_logic_bombs", help="Docker container name")

    args = parser.parse_args()
    docker_name = args.docker_name

    TEMP_DIR_LOCAL = f"logic_bombs/tmp_ghost_{uuid.uuid4().hex[:8]}"
    os.makedirs(TEMP_DIR_LOCAL, exist_ok=True)
    TEMP_DIR = f"/home/klee/{TEMP_DIR_LOCAL}".replace("/logic_bombs", "")  # Docker-friendly path
    # Copy files to shared Docker directory
    original_c_path = os.path.join(TEMP_DIR_LOCAL, "orig.c")
    translated_c_path = os.path.join(TEMP_DIR_LOCAL, "ghost.c")
    original_c_path_inside_docker = f"{TEMP_DIR}/orig.c"
    translated_c_path_inside_docker = f"{TEMP_DIR}/ghost.c"
    shutil.copyfile(args.original, original_c_path)
    shutil.copyfile(args.translated, translated_c_path)

    # Start container if not running
    docker_status = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", docker_name],
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if docker_status.returncode != 0 or "false" in docker_status.stdout.decode():
        print("🟡 Starting Docker container...")
        subprocess.run(["docker", "start", docker_name], check=True)
    else:
        print("🟢 Docker already running.")

    translated_bc_path = compile_to_bc_in_docker(translated_c_path_inside_docker, docker_name)
    ghost_output_dir = get_next_output_dir_in_docker(base=os.path.join(TEMP_DIR, "ghost_out"), docker_name=docker_name)
    run_klee_in_docker(translated_bc_path, ghost_output_dir, docker_name=docker_name)

    # Instrument with LLVM pass
    print("🛠️  Instrumenting with LLVM pass")
    for name in ["orig", "ghost"]:
        subprocess.run([
            "docker", "exec", docker_name, "/home/klee/llvm_pass/pass.sh",
            f"{TEMP_DIR}/{name}.c", "/home/klee/llvm_pass/BranchTracePass.cpp"
        ], check=True)

    # Paths to instrumented .bc files
    orig_bc = os.path.join(TEMP_DIR, "build_tmp", "orig", f"final_orig.bc")
    ghost_bc = os.path.join(TEMP_DIR, "build_tmp", "ghost", f"final_ghost.bc")

    #find all the tests
    #run all the tests on the 2 bc and collects the differences


if __name__ == "__main__":
    main()

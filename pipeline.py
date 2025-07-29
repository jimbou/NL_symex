#!/usr/bin/env python3

import argparse
import subprocess
import os
import sys
import shutil
import uuid


import subprocess

from branch_checker import compare_traces  # <- Fix the module name here
from model import get_model
import os
import shutil
import glob
import subprocess
from ktest_transform import apply_remap_on_ktests

def prepare_and_remap_ktests(model, TEMP_DIR, local_log_folder, docker_name, original_code_path, transformed_code_path):
    # Step 1: Copy all ktests from container to local
    ghost_output_dir = os.path.join(TEMP_DIR, "ghost_out-0")
    local_ktest_dir = os.path.join(local_log_folder, "local_ktests")
    os.makedirs(local_ktest_dir, exist_ok=True)
    #read the original and transformed files
    with open(original_code_path, "r") as f:
        original_code = f.read()
    with open(transformed_code_path, "r") as f:
        transformed_code = f.read()
    print("[INFO] Copying .ktest files from container...")
    subprocess.run([
        "docker", "cp",
        f"{docker_name}:/home/klee/tmp_ghost_76687470/ghost_out-0",
        local_ktest_dir
    ], check=True)

    ktest_dir = os.path.join(local_ktest_dir, "ghost_out-0")

    # Step 2: Remap ktests (generates _updated.ktest files)
    apply_remap_on_ktests(model, original_code, transformed_code, ktest_dir)

    # Step 3: Copy original and remapped tests back to container
    print("[INFO] Copying ktest files back into container...")
    for f in glob.glob(os.path.join(ktest_dir, "*.ktest")):
        subprocess.run([
            "docker", "cp", f,
            f"{docker_name}:{TEMP_DIR}/ghost_out-0/"
        ], check=True)

    return ktest_dir

def run_replay_traces_with_mapping(TEMP_DIR, docker_name, orig_executable, ghost_executable, ktest_dir, trace_dir):
    container_trace_dir = f"{TEMP_DIR}/trace_logs"
    ktest_files = sorted(glob.glob(os.path.join(ktest_dir, "*.ktest")))
    
    for ktest in ktest_files:
        name = os.path.basename(ktest)

        if name.endswith("_updated.ktest"):
            # remapped test -> run on original
            trace_path = os.path.join(container_trace_dir, f"orig_{name}.trace")
            exe = orig_executable
        else:
            # unmodified test -> run on ghost
            trace_path = os.path.join(container_trace_dir, f"ghost_{name}.trace")
            exe = ghost_executable

        cmd = (
            f"export LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH && "
            f"KTEST_FILE=/home/klee/tmp_ghost_76687470/ghost_out-0/{name} {exe} > {trace_path} 2>/dev/null"
        )
        subprocess.run(["docker", "exec", docker_name, "bash", "-c", cmd], check=True)

    print("[INFO] Finished replaying all test cases.")

    return sorted([
        (
            os.path.join(trace_dir, f"orig_{os.path.basename(f)}.trace"),
            os.path.join(trace_dir, f"ghost_{os.path.basename(f).replace('_updated','')}.trace")
        )
        for f in ktest_files if f.endswith("_updated.ktest")
    ])


def run_tests_and_compare(TEMP_DIR, docker_name, orig_executable, ghost_executable, ghost_output_dir, args):
        print("📁 Creating trace output directory in container")
        container_trace_dir = f"{TEMP_DIR}/trace_logs"
        subprocess.run(["docker", "exec", docker_name, "mkdir", "-p", container_trace_dir], check=True)

        print("🔎 Finding .ktest files in ghost output dir")
        find_ktests_cmd = [
            "docker", "exec", docker_name,
            "bash", "-c", f"find {ghost_output_dir} -name '*.ktest'"
        ]
        result = subprocess.run(find_ktests_cmd, stdout=subprocess.PIPE, check=True)
        ktest_files = result.stdout.decode().strip().split('\n')
        ktest_files = [ktest for ktest in ktest_files if ktest.strip()]
        print(f"📦 Found {len(ktest_files)} test cases.")

        for ktest in ktest_files:
            name = os.path.basename(ktest)
            trace_orig = f"{container_trace_dir}/orig_{name}.trace"
            trace_ghost = f"{container_trace_dir}/ghost_{name}.trace"

            for exe_path, trace_path in [(orig_executable, trace_orig), (ghost_executable, trace_ghost)]:
                cmd = (
                   f"export LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH && KTEST_FILE={ktest} {exe_path} > {trace_path} 2>/dev/null"
                )
                subprocess.run([
                    "docker", "exec", docker_name, "bash", "-c", cmd
                ], check=True)

        local_result_dir = os.path.join(args.log_folder, f"ghost_cmp_{uuid.uuid4().hex[:8]}")
        os.makedirs(local_result_dir, exist_ok=True)

        for remote_dir in [container_trace_dir, TEMP_DIR]:
            subprocess.run([
                "docker", "cp",
                f"{docker_name}:{remote_dir}",
                local_result_dir
            ], check=True)
        print("📤 Trace and output directories copied to:", local_result_dir)

        summary_path = os.path.join(local_result_dir, "summary.txt")
        trace_dir = os.path.join(local_result_dir, os.path.basename(container_trace_dir))
        with open(summary_path, "w") as fsum:
            for ktest in ktest_files:
                name = os.path.basename(ktest)
                f1 = os.path.join(trace_dir, f"orig_{name}.trace")
                f2 = os.path.join(trace_dir, f"ghost_{name}.trace")
                if os.path.exists(f1) and os.path.exists(f2):
                    match = compare_traces(f1, f2)
                    fsum.write(f"{name}: {'MATCH' if match else 'MISMATCH'}\n")

        print("✅ Comparison finished. Summary written to:", summary_path)

    # Call it
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


def create_model_log_based_name(model_name, log_folder, suffix):
    """
    Create a log folder name based on the model name and suffix.
    """
    log_folder_new= os.path.join(log_folder, suffix)

    # Ensure the log folder exists
    if not os.path.exists(log_folder_new):
        os.makedirs(log_folder_new)
    
    
    print(f"[INFO] Created log folder: {log_folder_new}")
    return get_model(model_name, 0.5, log_folder_new)



def main():
    parser = argparse.ArgumentParser(description="Run ghost code pipeline in KLEE docker.")
    parser.add_argument("--original", required=True, help="Path to original C file")
    # parser.add_argument("--remap_path", required=True, help="Path to remap file for ghost code")
    parser.add_argument("--translated", required=True, help="Path to translated (ghost) C file")
    parser.add_argument("--log_folder", default="log_tmp_ghost", help="Folder to save logs and results")
    parser.add_argument("--docker_name", default="klee_logic_bombs", help="Docker container name")
    parser.add_argument("--model_name", default="gpt-4.1", help="Model name for KLEE main generation")

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

    # Paths to executable files
    orig_executable = os.path.join(TEMP_DIR, "build_tmp", "orig", f"final_orig_replay")
    ghost_executable = os.path.join(TEMP_DIR, "build_tmp", "ghost", f"final_ghost_replay")

    model_remap= create_model_log_based_name(
        model_name=args.model_name,
        log_folder=args.log_folder,
        suffix="remap"
    )
    res= prepare_and_remap_ktests(model_remap, TEMP_DIR, args.log_folder, docker_name, original_c_path, translated_c_path)
    print(f"[INFO] Remapped ktests saved in: {res}")
    #find all the tests
    #run all the tests on the 2 bc and collects the differences
    #lift the ktest
    run_tests_and_compare(TEMP_DIR, docker_name, orig_executable, ghost_executable, ghost_output_dir, args)


if __name__ == "__main__":
    main()

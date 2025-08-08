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
from cov_line_coverage import get_uncovered_lines_in_docker, get_covered_lines_for_ktest
from reach_Nl_start import get_ktests_that_do_not_reach_nl_start
from map_line_numbers import relaxed_line_map
from get_minimal import get_minimal, get_minimal_prefix, get_reachable_line_klee, get_reachable_line_simple
from find_relaxed_pre_solution import add_relaxed_klee_assume

def find_tests_covering_ghost_lines(
    docker_name,
    ghost_output_dir,
    ghost_c_path_inside_docker,
    target_orig_lines
):
    """
    For each (orig_lineno, ghost_lineno) in target_orig_lines,
    find all .ktest files in ghost_output_dir that cover ghost_lineno.

    Returns:
        dict mapping (orig_lineno, ghost_lineno) -> list of ktest paths
    """

    result_map = {}

    # List all ktest files inside the container
    ktest_list_proc = subprocess.run(
        ["docker", "exec", docker_name, "bash", "-lc", f"ls {ghost_output_dir}/*.ktest"],
        capture_output=True,
        text=True,
        check=True
    )
    ktest_files = ktest_list_proc.stdout.strip().splitlines()

    ghost_exe_path = f"{os.path.dirname(ghost_c_path_inside_docker)}/ghost_coverage"

    for orig_lineno, ghost_lineno in target_orig_lines:
        covering_tests = []
        for ktest in ktest_files:
            covered_lines = get_covered_lines_for_ktest(
                docker_name,
                ghost_exe_path,
                ghost_c_path_inside_docker,
                ktest
            )
            if ghost_lineno in covered_lines:
                covering_tests.append(ktest)
        result_map[(orig_lineno, ghost_lineno)] = covering_tests

    # Print results
    for (orig_ln, ghost_ln), tests in result_map.items():
        print(f"Original line {orig_ln} (Ghost line {ghost_ln}) is covered only in ghost by tests:")
        for t in tests:
            print(f"  {t}")

    return result_map

def prepare_and_remap_ktests(model, TEMP_DIR, local_log_folder, docker_name, original_code_path, transformed_code_path, remap_path=None):
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
        f"{docker_name}:{TEMP_DIR}/ghost_out-0",
        local_ktest_dir
    ], check=True)

    ktest_dir = os.path.join(local_ktest_dir, "ghost_out-0")

    # Step 2: Remap ktests (generates _updated.ktest files)
    if remap_path:
        print(f"[INFO] Using remap path: {remap_path}")
        apply_remap_on_ktests(model, original_code, transformed_code, ktest_dir, remap_path)
    else:
        apply_remap_on_ktests(model, original_code, transformed_code, ktest_dir)

    # Step 3: Copy original and remapped tests back to container
    print("[INFO] Copying ktest files back into container...")
    for f in glob.glob(os.path.join(ktest_dir, "*.ktest")):
        subprocess.run([
            "docker", "cp", f,
            f"{docker_name}:{TEMP_DIR}/ghost_out-0/"
        ], check=True)

    return ktest_dir


def docker_bash(docker_name, cmd, **kwargs):
    return subprocess.run(["docker", "exec", docker_name, "bash", "-lc", cmd], **kwargs)

def instrument_source_in_docker(docker_name, temp_dir, src_name):
    """
    Copy instrument_branches.py & trace_logger.h into container temp dir
    and create an instrumented C file with TRACE() calls after assume_NL_stop().
    Returns path to the instrumented C file in the container and built replay exe path.
    """
    #from the source name keep only the file name
    src_name = os.path.basename(src_name)
    src_name_prefix = src_name.replace(".c", "")
    container_src = f"{temp_dir}/{src_name}"
    container_instr = container_src.replace(".c", "_instr.c")
    container_hdr = f"/home/klee/llvm_pass/trace.h"
    container_py = f"/home/klee/llvm_pass/pass.py"
    replay_exe = f"{temp_dir}/build_tmp/{src_name_prefix}/final_{src_name_prefix}_instr_replay"

    # ensure build dir
    docker_bash(docker_name, f"mkdir -p {temp_dir}/build_tmp_simple/{src_name_prefix}", check=True)

    # copy helper files into the container
    # subprocess.run(["docker", "cp", "instrument_branches.py", f"{docker_name}:{container_py}"], check=True)
    # subprocess.run(["docker", "cp", "trace_logger.h", f"{docker_name}:{container_hdr}"], check=True)

    # run instrumentation
    docker_bash(docker_name, f"python3 {container_py} {container_src} {container_instr}", check=True)

    # build replay exe linked with kleeRuntest (+ libm)
    build_cmd = (
        f"clang {container_instr} -I{temp_dir} "
        f"-L/tmp/klee_build130stp_z3/lib -lkleeRuntest -lm "
        f"-o {replay_exe}"
    )
    docker_bash(docker_name, build_cmd, check=True)

    return container_instr, replay_exe
    

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


def run_tests_and_compare(TEMP_DIR, docker_name, orig_executable, ghost_executable, ghost_output_dir, trace_logs, local_folder_name):
        print("📁 Creating trace output directory in container")
        container_trace_dir = f"{TEMP_DIR}/{trace_logs}"
        subprocess.run(["docker", "exec", docker_name, "mkdir", "-p", container_trace_dir], check=True)

        print(f"🔎 Finding .ktest files in {ghost_output_dir}")
        find_ktests_cmd = [
            "docker", "exec", docker_name,
            "bash", "-c", f"find {ghost_output_dir} -name '*.ktest'"
        ]
        result = subprocess.run(find_ktests_cmd, stdout=subprocess.PIPE, check=True)
        ktest_files = result.stdout.decode().strip().split('\n')
        ktest_files = [ktest for ktest in ktest_files if ktest.strip()]
        print(f"📦 Found {len(ktest_files)} test cases.")

        for ktest in ktest_files:
            remapped=False
            name = os.path.basename(ktest)
            name_cleaned = name
            if "remapped" in name:
                remapped=True  
                name_cleaned=name.replace("remapped_", "")

            trace_orig = f"{container_trace_dir}/orig_{name_cleaned}.trace"
            trace_ghost = f"{container_trace_dir}/ghost_{name_cleaned}.trace"
            if remapped:
                #running on the original
                exe_path = orig_executable
                trace_path = trace_orig
            # for exe_path, trace_path in [(orig_executable, trace_orig), (ghost_executable, trace_ghost)]:
                
            else:
                #running on the ghost
                exe_path = ghost_executable
                trace_path = trace_ghost
               
            cmd = (
                   f"export LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH && KTEST_FILE={ktest} {exe_path} > {trace_path} 2>/dev/null"
                )
            subprocess.run([
                "docker", "exec", docker_name, "bash", "-c", cmd
            ], check=True)

        local_result_dir = local_folder_name
        os.makedirs(local_result_dir, exist_ok=True)

        for remote_dir in [container_trace_dir, TEMP_DIR]:
            subprocess.run([
                "docker", "cp",
                f"{docker_name}:{remote_dir}",
                local_result_dir
            ], check=True)
        print("📤 Trace and output directories copied to:", local_result_dir)

        summary_path = os.path.join(local_result_dir, f"summary_{trace_logs}.txt")
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
        return summary_path

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
    parser.add_argument("--remap_path", required=False, help="Path to remap file for ghost code")
    parser.add_argument("--minimal_file", required=False, help="Path to minimal file for symex")
    parser.add_argument("--minimal_prefix_file", required=False, help="Path to minimal prefix file for symex")
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
# ,"--rebuild-pass"
    # Instrumenting with reachability pass
    print("🛠️  Instrumenting with reachability pass")
    for name in ["orig", "ghost"]:
        subprocess.run([
            "docker", "exec", docker_name, "/home/klee/llvm_pass/pass_reach.sh",
            f"{TEMP_DIR}/{name}.c", "/home/klee/llvm_pass/Reachability_pass.cpp"
        ], check=True)
    # Paths to executable files
    orig_executable = os.path.join(TEMP_DIR, "build_tmp", "orig", f"final_orig_replay")
    ghost_executable = os.path.join(TEMP_DIR, "build_tmp", "ghost", f"final_ghost_replay")

    orig_reachability= os.path.join(TEMP_DIR, "build_tmp", "orig_reach", f"reachability_orig_replay")
    ghost_reachability= os.path.join(TEMP_DIR, "build_tmp", "ghost_reach", f"reachability_ghost_replay")

    model_remap= create_model_log_based_name(
        model_name=args.model_name,
        log_folder=args.log_folder,
        suffix="remap"
    )
    local_folder_name= args.log_folder+TEMP_DIR_LOCAL.replace("logic_bombs", "")
    if args.remap_path:
        print(f"[INFO] Using remap path: {args.remap_path}")
        res= prepare_and_remap_ktests(model_remap, TEMP_DIR, local_folder_name, docker_name, original_c_path, translated_c_path,args.remap_path)

    else:
        print(f"[INFO] Using default remap path: {model_remap}")
        res= prepare_and_remap_ktests(model_remap, TEMP_DIR, local_folder_name, docker_name, original_c_path, translated_c_path)
        # print(f"[INFO] Remapped ktests saved in: {res}")
    #find all the tests
    #run all the tests on the 2 bc and collects the differences
    #lift the ktest

    _, replay_orig_simple_instrumented = instrument_source_in_docker(docker_name, TEMP_DIR, original_c_path)
    print(f"Original source instrumented executable: {replay_orig_simple_instrumented}")
    _, replay_ghost_simple_instrumented = instrument_source_in_docker(docker_name, TEMP_DIR, translated_c_path)
    print(f"Ghost source instrumented executable: {replay_ghost_simple_instrumented}")
    
    summary_path_complex= run_tests_and_compare(TEMP_DIR, docker_name, orig_executable, ghost_executable, ghost_output_dir, "llvm_traces",local_folder_name)
    summary_path_simple= run_tests_and_compare(
        TEMP_DIR, docker_name,
        replay_orig_simple_instrumented, replay_ghost_simple_instrumented,
        ghost_output_dir, "simple_traces",local_folder_name
    )
    uncovered = get_uncovered_lines_in_docker(docker_name, ghost_output_dir, original_c_path_inside_docker)
    uncovered_lines_orig= {lineno for lineno, content in uncovered if lineno is not None and content is not None}
    print("Uncovered lines:")
    for lineno, content in uncovered:
        print(f"{lineno}: {content}")

    if len(uncovered)==0:
        print("All lines covered!")
        # return 

    #lets find out if the ktests all reach the assume_NL_start
    print("Finding ktests that do not reach assume_NL_start...")
    dont_reach_start=get_ktests_that_do_not_reach_nl_start(docker_name, ghost_reachability, ghost_output_dir)
    print(f"KTests that do NOT reach assume NL start: {dont_reach_start}")


    map_ghost_to_orig, map_orig_to_ghost = relaxed_line_map(translated_c_path, original_c_path)
    uncovered_ghost =get_uncovered_lines_in_docker(docker_name, ghost_output_dir, translated_c_path_inside_docker)
    uncovered_lines_ghost = {lineno for lineno, content in uncovered_ghost if lineno is not None and content is not None}

    # 3. Find lines uncovered in original but covered in ghost
    target_orig_lines = []
    for orig_lineno in uncovered_lines_orig:
        ghost_lineno = map_orig_to_ghost.get(orig_lineno, -1)
        if ghost_lineno != -1 and ghost_lineno not in uncovered_lines_ghost:
            target_orig_lines.append((orig_lineno, ghost_lineno))

    print("Lines uncovered in original but covered in ghost:")
    for orig_lineno, ghost_lineno in target_orig_lines:
        print(f"Original line {orig_lineno} -> Ghost line {ghost_lineno}")

    result_map = find_tests_covering_ghost_lines(
        docker_name,
        ghost_output_dir,
        translated_c_path_inside_docker,
        target_orig_lines
    )
    print("Tests covering ghost lines:")
    for (orig_lineno, ghost_lineno), tests in result_map.items():
        print(f"Original line {orig_lineno} (Ghost line {ghost_lineno}) is covered by tests:")
        for t in tests:
            print(f"  {t}")


    minimal_file_path= original_c_path.replace(".c", "_minimal.c")
    minimal_prefix_file_path= original_c_path.replace(".c", "_minimal_prefix.c")
    if len(result_map)>= 0: #change this only to >
        minimal_log_path = os.path.join(args.log_folder, os.path.basename(minimal_file_path))

        if args.minimal_file:
            #copy the minimal file to the minimal_file_path
            shutil.copyfile(args.minimal_file, minimal_log_path)
            shutil.copyfile(args.minimal_file, minimal_file_path)
        else:
            model_minimal = create_model_log_based_name(
                model_name=args.model_name,
                log_folder=args.log_folder,
                suffix="minimal"
            )
            print(f"[INFO] Using model to get the minimal file from original file: {original_c_path}")
            minimal_code = get_minimal(
                model_minimal,
                original_c_path, minimal_file_path
                )
            print(f"[INFO] Minimal code saved to: {minimal_file_path}")
            #save it also to the log_folder with the same base name
            with open(minimal_log_path, "w") as f:
                f.write(minimal_code)
        map_orig_to_minimal, map_minimal_to_orig = relaxed_line_map( original_c_path,minimal_log_path)


        minimal_prefix_log_path = os.path.join(args.log_folder, os.path.basename(minimal_prefix_file_path))

        if args.minimal_prefix_file:
            #copy the minimal file to the minimal_file_path
            shutil.copyfile(args.minimal_prefix_file, minimal_prefix_log_path)
            shutil.copyfile(args.minimal_prefix_file, minimal_prefix_file_path)
        else:
            
            print(f"[INFO] Using custom logic to get the minimal prefix file from original file: {original_c_path}")
            minimal_code_prefix = get_minimal_prefix(
                
                original_c_path
            )
            print(f"[INFO] Minimal code saved to: {minimal_prefix_file_path}")
            #save it also to the log_folder with the same base name
            with open(minimal_prefix_log_path, "w") as f:
                f.write(minimal_code_prefix)

    code_with_reachable_line_simple = get_reachable_line_simple(original_c_path, 16)
    # print(f"[INFO] Code with reachable line (simple): {code_with_reachable_line_simple}")
    #print the map original to minimal
    # print(f"[INFO] Map from original to minimal lines: {map_orig_to_minimal}")
    # print(f"[INFO] Map from minimal to original lines: {map_minimal_to_orig}")
    code_with_reachable_line_klee = get_reachable_line_klee(minimal_log_path, map_orig_to_minimal[16])
    # print(f"[INFO] Code with reachable line (KLEE): {code_with_reachable_line_klee}")
    #save both to files


    #use /home/jim/NL_constraints/logic_bombs/make_klee_executable.sh to make the code_rechable_line_simple replayable

    #use bc comiple and then klee to explore the code_with_reachable_line_klee

    #minimal is a simple replacement of the original code, so we can use it directly without the difficult part
    #mininal p[refix is to explore on klee with just up to the prefix
    #code with reachable line simple is to explore on the original code if we reach the line we want
    #code with reachable line klee is to find a solution that reaches the line we want in the minimal code potentially in the future will add some klee_assume abs to make it similar to the solution we want but for that solution we want we must first calculate it by running on the original line simple


    with open(os.path.join(args.log_folder, "reachable_line_simple.c"), "w") as f:
        f.write(code_with_reachable_line_simple)
    with open(os.path.join(args.log_folder, "reachable_line_klee.c"), "w") as f:
        f.write(code_with_reachable_line_klee)
    print(f"[INFO] Saved reachable lines to log folder: {args.log_folder}")

    # add_relaxed_klee_assume("/home/jim/NL_constraints/test000001.ktest", minimal_prefix_log_path, docker_name)
    #while the result map is not empty, pick a line in the original that is not covered and  a test case that covers it in ghost
    while target_orig_lines:
        orig_lineno, ghost_lineno = target_orig_lines.pop(0)
        tests = result_map.get((orig_lineno, ghost_lineno), [])
        if not tests:
            print(f"No tests found covering original line {orig_lineno} (Ghost line {ghost_lineno})")
            continue

        # Pick the first test that covers this line
        ktest_path = tests[0]
        print(f"Using test {ktest_path} to cover original line {orig_lineno} (Ghost line {ghost_lineno})")
        add_relaxed_klee_assume(ktest_path, minimal_file_path, docker_name)

        code_with_reachable_line_simple = get_reachable_line_simple(original_c_path, orig_lineno)
        code_with_reachable_line_klee = get_reachable_line_klee(original_c_path, map_orig_to_minimal[orig_lineno])

        
        # Run the remapped test on the original code
        
    


if __name__ == "__main__":
    main()

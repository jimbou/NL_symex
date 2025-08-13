import argparse
import os
import shutil
import glob

from preprocessing import run_preprocessing,get_uncovered_from_container
from test_templates import get_translated_code, extract_blocks
from cov_line_coverage import  get_uncovered_lines_in_docker, get_covered_lines_for_ktest
from map_line_numbers import relaxed_line_map
from ktest_transform import apply_remap_on_ktests
from pipeline import  create_model_log_based_name
from reach_Nl_start import check_if_ktest_reaches_Nl_start



def prepare_and_remap_ktests(model, klee_docker_ghost, local_log_folder, docker_name, original_code_path, transformed_code_path, ktest_path=None, remap_path=None):
    # Step 1: Copy all ktests from container to local
    
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
        f"{docker_name}:{klee_docker_ghost}",
        local_ktest_dir
    ], check=True)
    # The copied folder will appear as a subdirectory inside local_ktest_dir,
    # with the same basename as klee_docker_ghost.
    # For example, if klee_docker_ghost is "/home/klee/ghost_out-0",
    # the copied folder will be: os.path.join(local_ktest_dir, "ghost_out-0")
    #find from the klee_docker_ghost the path after the basename of home/klee/
    ktest_dir = os.path.join(local_ktest_dir, os.path.basename(klee_docker_ghost))
    print(f"[INFO] Ktest directory: {ktest_dir}")

    # Step 2: Remap ktests (generates _updated.ktest files)
    
    apply_remap_on_ktests(model, original_code, transformed_code, ktest_dir, remap_path=remap_path, ktest_path=ktest_path)
   

    # Step 3: Copy original and remapped tests back to container
    print("[INFO] Copying ktest files back into container...")
    for f in glob.glob(os.path.join(ktest_dir, "*.ktest")):
        subprocess.run([
            "docker", "cp", f,
            f"{docker_name}:{klee_docker_ghost}"
        ], check=True)

    return ktest_dir

import os
import subprocess

def get_per_test_coverage(docker_name: str, ktest_dir: str, c_file_path: str, sort_lines: bool = True):
    """
    For every .ktest in `ktest_dir` (inside the Docker container), compute the lines
    covered in `c_file_path` (also inside the container), using llvm-cov via
    `get_covered_lines_for_ktest`.

    Returns:
        dict[str, list[int]]: { <ktest_basename>: [covered_line_numbers] }
    """
    # List ktests inside the container
    ls_proc = subprocess.run(
        ["docker", "exec", docker_name, "bash", "-lc", f'ls -1 {ktest_dir}/*.ktest 2>/dev/null'],
        capture_output=True,
        text=True,
        check=False  # tolerate empty dir
    )
    if ls_proc.returncode != 0 or not ls_proc.stdout.strip():
        return {}

    ktest_paths = [p.strip() for p in ls_proc.stdout.splitlines() if p.strip()]
    per_test = {}

    for kpath in ktest_paths:
        try: 
            covered = get_covered_lines_for_ktest(docker_name=docker_name, c_file_path=c_file_path, ktest_path=kpath)
            key = os.path.basename(kpath)
            per_test[key] = sorted(covered) if sort_lines else list(covered)
        except subprocess.CalledProcessError as e:
            # Skip this test but keep going
            key = os.path.basename(kpath)
            per_test[key] = []
            print(f"[WARN] Coverage failed for {key}: {e}")

    return per_test


def find_coverage_of_file(docker_name, container_log, log_folder, c_path_inside_container):
     # Step 4: Run get_uncovered inside container
    
    
    klee_run_dir= f"{container_log}/coverage_run_ghost"
    result = get_uncovered_from_container(docker_name, c_path_inside_container, klee_run_dir=klee_run_dir   )
    # Print covered and uncovered lines nicely
    uncovered_lines = result.get("uncovered", [])
    covered_lines = result.get("covered", [])
    print("Covered lines:")
    for line in covered_lines:
        print(line)

    print("\nUncovered lines:")
    for line in uncovered_lines:
        print(line)
    

    uncovered_llvm = get_uncovered_lines_in_docker(docker_name, klee_run_dir, c_path_inside_container)
    #this is a list of tuples pls make them into a list of lists
    uncovered_llvm = [list(item) for item in uncovered_llvm]
    print(f"Uncovered lines in LLVM coverage:\n{uncovered_llvm}")
    uncovered_lines_llvm= {lineno for lineno, content in uncovered_llvm if lineno is not None and content is not None}
    print(f"Uncovered lines in LLVM coverage:\n")
    print("Uncovered lines:")

    #copy from the docker with docker cp the klee_run_dir to the log folder
    coverage_dir = os.path.join(log_folder, "coverage_ghost")
    if not os.path.exists(coverage_dir):
        os.makedirs(coverage_dir)
    #we need to use docker cp to copy a dir in a docker
        os.system(f"docker cp {docker_name}:{klee_run_dir} {coverage_dir}")
        for lineno, content in uncovered_llvm:
         print(f"{lineno}: {content}")
    return {
        "covered": covered_lines,
        "uncovered": uncovered_lines,
        "uncovered_llvm": uncovered_llvm,
        "coverage_dir": klee_run_dir
    }

def find_uncovered_in_orig_covered_in_ghost(uncovered_orig, uncovered_ghost, map_orig_to_ghost):
    """
    Find lines that are uncovered in the original code but covered in the ghost code.
    """
    uncovered_orig_set = {line[0] for line in uncovered_orig}
    print(f"Uncovered lines in original of lenght {len(uncovered_orig_set)}: {uncovered_orig_set}")
    unbcovered_ghost_set = {line[0] for line in uncovered_ghost}
    #map the lines from the orig to the ghost
    uncovered_orig_set = {map_orig_to_ghost.get(line, line) for line in uncovered_orig_set}
    print(f"Uncovered lines in original mapped to ghost: {uncovered_orig_set}")
    # Find lines that are in original but not in ghost
    uncovered_in_orig_covered_in_ghost = set()
    for line in uncovered_orig_set:
        if line not in unbcovered_ghost_set:
            uncovered_in_orig_covered_in_ghost.add(line)
    print(f"Uncovered lines in original covered in ghost: {uncovered_in_orig_covered_in_ghost}")
    return uncovered_in_orig_covered_in_ghost

import subprocess

def docker_bash(docker_name: str, cmd: str, **kwargs):
    """Run a bash command inside the docker container."""
    return subprocess.run(
        ["docker", "exec", docker_name, "bash", "-lc", cmd],
        check=True,
        **kwargs
    )

def combine_ktests_in_docker(docker_name: str, orig_dir: str, ghost_dir: str, combined_dir: str):
    """
    Inside the container:
      - Create combined_dir (fresh)
      - Copy *.ktest from orig_dir -> combined_dir with suffix _orig.ktest
      - Copy *.ktest from ghost_dir -> combined_dir with suffix _ghost.ktest
    """
    # fresh dir
    docker_bash(docker_name, f"rm -rf {combined_dir} && mkdir -p {combined_dir}")

    # copy & rename original ktests
    copy_orig = (
        f'if compgen -G "{orig_dir}/*.ktest" > /dev/null; then '
        f'  for f in {orig_dir}/*.ktest; do '
        f'    b="$(basename "$f" .ktest)"; '
        f'    cp "$f" "{combined_dir}/${{b}}_orig.ktest"; '
        f'  done; '
        f'fi'
    )
    docker_bash(docker_name, copy_orig)

    # copy & rename ghost ktests
    copy_ghost = (
        f'if compgen -G "{ghost_dir}/*.ktest" > /dev/null; then '
        f'  for f in {ghost_dir}/*.ktest; do '
        f'    b="$(basename "$f" .ktest)"; '
        f'    cp "$f" "{combined_dir}/${{b}}_ghost.ktest"; '
        f'  done; '
        f'fi'
    )
    docker_bash(docker_name, copy_ghost)

    # quick count for logging
    res = docker_bash(
        docker_name,
        f'ls -1 {combined_dir}/*.ktest 2>/dev/null | wc -l',
        capture_output=True,
        text=True
    )
    print(f"[INFO] Combined ktests in {combined_dir}: {res.stdout.strip()}")


def main():
    parser = argparse.ArgumentParser(description="Run get_uncovered inside KLEE container.")
    parser.add_argument("--c_file_path", help="Path to the C file to analyze")
    parser.add_argument("--log_folder", default="log_tmp", help="Log folder to store outputs (default: log_tmp)")
    parser.add_argument("--docker_name", default="klee_logic_bombs", help="Name of the running KLEE container (default: klee_logic_bombs)")
    parser.add_argument('--model', required=False, default='deepseek-v3-aliyun',
                        help='Model to use (optional, default: deepseek-v3-aliyun)')
    parser.add_argument('--is_klee_annotated',required=False, default=False, 
                        help='Set this if the input C file is already KLEE-annotated')
    parser.add_argument('--is_klee_marked', required=False, default=False,
                        help='Set this if the input C file is already KLEE-marked')
    parser.add_argument('--translated_file_path', required=False, 
                        help='Set this if the input C file is already translated')
    parser.add_argument('--remap_path', required=False,
                    help='Path to an existing remap_testcase.py (optional). If omitted, it will be generated.')

    args = parser.parse_args()

   
    c_file_path = args.c_file_path
    log_folder = args.log_folder
    docker_name = args.docker_name
    is_klee_annotated = args.is_klee_annotated
    is_klee_marked = args.is_klee_marked
    model_name = args.model

    if str(is_klee_annotated).lower() in ['yes', 'true', '1', 'on', 'y', 't']:
        is_klee_annotated = True
    else:
        is_klee_annotated = False

    if not os.path.isfile(c_file_path):
        raise FileNotFoundError(f"C file not found: {c_file_path}")
    if args.translated_file_path:
        translated_code_path = args.translated_file_path
        is_klee_translated = True
    else:
        is_klee_translated = False


    #create log folder if it does not exist 
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    # If the file is already translated, we can directly use it
    print(f"[INFO] Using already translated C file: {c_file_path}")
    # No need to run preprocessing, just set the translated code path
    #copy the c_file_path to log folder and use this as the translated path
    
    preprocessing_results= run_preprocessing(c_file_path= c_file_path, log_folder=log_folder, docker_name=docker_name, model_name=model_name, is_klee_annotated=is_klee_annotated , is_klee_marked=is_klee_marked)


    #print the preprocessing results in anice way
    print("Preprocessing results:")
    print(f"Annotated path :{preprocessing_results['annotated_path']}")
    c_file_path_marked = preprocessing_results['annotated_path']

    for covered in preprocessing_results["coverage"]["covered"]:
        print(f"  Covered line: {covered}")
        
    for uncovered in preprocessing_results["coverage"]["uncovered"]:
        print(f"  Uncovered line: {uncovered}")
    
    print(f"Uncovered LLVM\n:")
    for uncov in preprocessing_results["coverage"]["uncovered_llvm"]:
        print(f"{uncov}")

    coverage_dir_local = preprocessing_results["dir_of_coverage"]
    print(f"Coverage directory (local): {coverage_dir_local}")  
    # Find substring after "logic_bombs" and join with /home/klee/
    # parts = coverage_dir_local.split("logic_bombs", 1)
    # if len(parts) < 2:
    #     raise ValueError(f"'logic_bombs' not found in path: {coverage_dir_local}")

    # remaining_path = parts[1].lstrip(os.sep)  # remove leading slash if present
    # coverage_dir_klee = os.path.join("/home/klee", remaining_path)
    coverage_dir_klee= preprocessing_results["dir_of_coverage_inside_docker"]
    log_inside_container = preprocessing_results["log_inside_container"]
    print(f"Coverage directory in KLEE: {coverage_dir_klee}")


    # FIRST BREAKPOINT
    # GET TRANSLATION
    if not is_klee_translated:
        print(f"Translating C code: {c_file_path_marked}")  
        translated_code_path, pre_code, nl_code = get_translated_code(model_name, log_folder, c_file_path_marked)
    else:
        translated_file=  os.path.join(log_folder, "translated.c")
        shutil.copy(translated_code_path, translated_file)
        translated_code_path = translated_file
    print(f"Translated code path: {translated_code_path}")
    #read the code from the translated code path
    with open(translated_code_path, 'r') as f:
        translated_code = f.read()
    pre_ghost, ghost, post_ghost = extract_blocks(translated_code)

    #copy the translated code to the log folder inside the container
    translated_code_path_inside_container = os.path.join(log_inside_container, "translated.c")
    #use docker cp to copy the file
    os.system(f"docker cp {translated_code_path} {docker_name}:{translated_code_path_inside_container}")
    results_coverage_ghost = find_coverage_of_file(
        docker_name,
        log_inside_container,
        log_folder,
        c_path_inside_container=translated_code_path_inside_container
    )
    print(f"Coverage results for ghost code:\n{results_coverage_ghost}")
    coverage_dir_klee_ghost = results_coverage_ghost["coverage_dir"]

    print(f"Translated code saved to: {translated_code_path}")

    if len(results_coverage_ghost["uncovered"]) == len(preprocessing_results["coverage"]["uncovered"]):
        print("We were not able to trigger any new coverage in the ghost code.")
        return

    # Find lines that are uncovered in original but covered in ghost
    map_ghost_to_orig, map_orig_to_ghost = relaxed_line_map(translated_code_path, c_file_path_marked)
    # uncovered_in_orig
    uncovered_in_orig_covered_in_ghost = find_uncovered_in_orig_covered_in_ghost( preprocessing_results["coverage"]["uncovered"], results_coverage_ghost["uncovered"], map_orig_to_ghost)
    print(f"Uncovered lines in original covered in ghost: {uncovered_in_orig_covered_in_ghost}")   
    #mqap them to original values
    uncovered_in_orig_covered_in_ghost = {map_orig_to_ghost.get(line, line) for line in uncovered_in_orig_covered_in_ghost}
    print(f"Uncovered lines in original covered in ghost mapped to original: {uncovered_in_orig_covered_in_ghost}")

    #for every ktest in the coverage_dir_klee and in the coverage_dir_klee_ghost use get_uncovered_lines_in_docker to get the coverage of the total ktyetss 

        # --- NEW: combine ktests from original+ghost and compute total coverage ---

    # where the original annotated file lives inside the container
    #we need to copy c_file_path_marked inside the container if it is not already there
    orig_inside_container = os.path.join(log_inside_container, os.path.basename(c_file_path_marked))
    #check if this path inside the container exists with some docker command
    #this file is not local so we need to use docker commands
    res = docker_bash(
        docker_name,
        f"if [ -f {orig_inside_container} ]; then echo 'exists'; else echo 'missing'; fi",
        capture_output=True,
        text=True
    )
    if res.stdout.strip() == "missing":
        print(f"[INFO] Copying {c_file_path_marked} to {orig_inside_container}...")
        os.system(f"docker cp {c_file_path_marked} {docker_name}:{orig_inside_container}")
    
    # dirs with ktests inside container
    #   coverage_dir_klee      -> from preprocessing (original run)
    #   coverage_dir_klee_ghost-> from results_coverage_ghost (ghost run)
    combined_dir = os.path.join(log_inside_container, "combined_ktests")

    print(f"[INFO] Combining ktests into: {combined_dir}")
    combine_ktests_in_docker(
        docker_name,
        coverage_dir_klee,          # original's coverage dir (inside container)
        coverage_dir_klee_ghost,    # ghost's coverage dir (inside container)
        combined_dir
    )

    # Use your existing per-dir coverage function on ORIGINAL source with the combined tests
    print("[INFO] Measuring coverage of ORIGINAL with combined ktests...")
    combined_uncovered = get_uncovered_lines_in_docker(
        docker_name,
        combined_dir,
        orig_inside_container
    )

    print("\n[RESULT] Uncovered lines in ORIGINAL with combined tests:")
    for ln, txt in combined_uncovered:
        print(f"{ln}: {txt}")

    if len(combined_uncovered) == 0:
        print("[INFO] All lines covered in ORIGINAL with combined tests. No further action needed.")
        return
    

    # We will remap the ghost test cases back to the original
    model_remap = create_model_log_based_name(
        model_name=model_name,
        log_folder=log_folder,          # <- fixed typo (alog_folder -> log_folder)
        suffix="remap"
    )

    # local absolute path to the log folder (used to stage remapped ktests)
    

    # We’ll use the ghost coverage dir (inside container) as the source of ghost ktests
    # You already computed: coverage_dir_klee_ghost = results_coverage_ghost["coverage_dir"]
    

    # Container paths to original & translated sources
    original_c_path_inside_container = os.path.join(
        log_inside_container, os.path.basename(c_file_path_marked)
    )
    translated_c_path_inside_container = translated_code_path_inside_container

    # Optional user-provided remap path
    remap_path = getattr(args, "remap_path", None)

    per_test_cov_dict = get_per_test_coverage(docker_name, coverage_dir_klee_ghost, translated_code_path_inside_container)
    print(f"[INFO] Per-test coverage dict (ghost ktests on ghost code): {per_test_cov_dict}")

    # For every line in combined_uncovered_REMAPPED, find its remapped line in ghost code,
    # then find the ktest that covers it in per_test_cov_dict.
    # Output: {orig_line: ktest_name or None}
    line_to_ktest_orig = {}
    for orig_ln, _ in combined_uncovered:
        ghost_ln = map_orig_to_ghost.get(orig_ln)
        if ghost_ln is None:
            line_to_ktest_orig[orig_ln] = None
            continue
        found_ktest = None
        for ktest_name, covered_lines in per_test_cov_dict.items():
            if ghost_ln in covered_lines:
                found_ktest = ktest_name
                break
        line_to_ktest_orig[orig_ln] = found_ktest

    # From the translated_c_path_inside_container and the orig_inside_container,
    # rename them in the same folder (inside the container) to orig.c and ghost.c
    print(f"[INFO] Mapping of uncovered original lines to ktest covering their ghost-mapped line:\n{line_to_ktest_orig}")

    #find one of the ktests that appear in line_to_ktest_orig
    first_ktest = next((ktest for ktest in line_to_ktest_orig.values() if ktest is not None), None)
    if first_ktest is None:
        print("[WARN] No ktests found that cover any uncovered lines in ghost code. Exiting.")
        
    else:
        ktest_promising_path= os.path.join(coverage_dir_klee_ghost, first_ktest)
        
    # Prepare + remap ghost ktests, and push remapped back into the container
    ktests_local_dir = prepare_and_remap_ktests(
        model=model_remap,
        klee_docker_ghost=coverage_dir_klee_ghost,                                # container dir holding ghost_out-0
        local_log_folder=log_folder,
        docker_name=docker_name,
        original_code_path=c_file_path_marked,            # local original code (for prompt)
        transformed_code_path=translated_code_path,       # local translated code (for prompt)
        remap_path=remap_path,
        ktest_path=ktest_promising_path  # local path to a promising ktest
    )

    print(f"[INFO] Remapped ktests staged at: {ktests_local_dir}")

    #from the ktests_local_dir we need to copy all the remapped ktests to the combined_dir in the docker
    for f in glob.glob(os.path.join(ktests_local_dir, "remapped_*.ktest")):
        subprocess.run([
            "docker", "cp", f,
            f"{docker_name}:{combined_dir}"
        ], check=True)

    print("[INFO] Re-measuring coverage of ORIGINAL with remapped ktests...")

    combined_uncovered_REMAPPED = get_uncovered_lines_in_docker(
        docker_name,
        combined_dir,
        orig_inside_container
    )

    print("\n[RESULT] Uncovered lines in ORIGINAL with combined tests:")
    for ln, txt in combined_uncovered_REMAPPED:
        print(f"{ln}: {txt}")

    if len(combined_uncovered_REMAPPED) == 0:
        print("[INFO] All lines covered in ORIGINAL with combined tests. No further action needed.")
        # return
    combined_uncovered_REMAPPED.append((16, "return 1;"))  # Add a marker for end of remapped coverage NEED TO REMOVE THIS LATER
   
     
     #for that ktest see if it reaches the assume_NL_start or not using get_ktests_that_do_not_reach_nl_start from pipeline

    line_to_ktest = {}
    for orig_ln, _ in combined_uncovered_REMAPPED:
        ghost_ln = map_orig_to_ghost.get(orig_ln)
        if ghost_ln is None:
            line_to_ktest[orig_ln] = None
            continue
        found_ktest = None
        for ktest_name, covered_lines in per_test_cov_dict.items():
            if ghost_ln in covered_lines:
                found_ktest = ktest_name
                break
        line_to_ktest[orig_ln] = found_ktest
    
    docker_bash(
        docker_name,
        f"cp {orig_inside_container} {os.path.join(log_inside_container, 'orig.c')}"
    )
    docker_bash(
        docker_name,
        f"cp {translated_c_path_inside_container} {os.path.join(log_inside_container, 'ghost.c')}"
    )

    TEMP_DIR = log_inside_container  # Use this as the working directory for instrumentation
    
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
    #print all the paths
    print(f"[INFO] Original executable: {orig_executable}")
    print(f"[INFO] Ghost executable: {ghost_executable}")
    print(f"[INFO] Original reachability executable: {orig_reachability}")  
    print(f"[INFO] Ghost reachability executable: {ghost_reachability}")

    ktests_dont_reach = []
    # for every ktest in line_to_ktest they are goinna be in the coverage_dir_klee_ghost make the full path and call check_if_ktest_reaches_Nl_start
    for line, ktest_name in line_to_ktest.items():
        
        ktest_full_path = os.path.join(coverage_dir_klee_ghost, ktest_name)
        print(f"[INFO] Checking ktest: {ktest_full_path}")
        #if the file does not exist in the container, skip it
        res = subprocess.run(
            ["docker", "exec", docker_name, "bash", "-c", f"test -f {ktest_full_path}"],
            capture_output=True
        )
        if res.returncode != 0:
            print(f"[WARN] KTest file does not exist: {ktest_full_path}")
            continue
        # Check if the ktest reaches the assume_NL_start use this get_ktest_does_not_reach_nl_start(docker_name: str, exe_path: str, ktest_path: str) -> tuple[bool, str]:
        does_reach, output = check_if_ktest_reaches_Nl_start(
            docker_name=docker_name,
            exe_path=ghost_reachability,
            ktest_path=ktest_full_path
        )
        if does_reach:
            print(f"✅ KTest {ktest_name} reaches assume NL start: {output}")
        else:
            print(f"❌ KTest {ktest_name} does NOT reach assume NL start: {output}")
            # If it does not reach, we add it to the list
            ktests_dont_reach.append(ktest_full_path)
    print(f"[INFO] KTests that do NOT reach assume NL start: {ktests_dont_reach}")
        
if __name__ == "__main__":
    main()

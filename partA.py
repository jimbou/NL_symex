import argparse
import os
import shutil

from preprocessing import run_preprocessing,get_uncovered_from_container
from test_templates import get_translated_code, extract_blocks
from cov_line_coverage import  get_uncovered_lines_in_docker
from map_line_numbers import relaxed_line_map

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

    # Find substring after "logic_bombs" and join with /home/klee/
    parts = coverage_dir_local.split("logic_bombs", 1)
    if len(parts) < 2:
        raise ValueError(f"'logic_bombs' not found in path: {coverage_dir_local}")

    remaining_path = parts[1].lstrip(os.sep)  # remove leading slash if present
    coverage_dir_klee = os.path.join("/home/klee", "logic_bombs", remaining_path)
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
    #if total stop

    #else remap test cases
    #call remap, apply remap
    #add these testcases with the other
     #for every ktest in the  use get_uncovered_lines_in_docker to get the coverage of the total ktyetss 
     #for uncovered in orig covered in ghost find the ktest that finds the line number
     #for that ktest see if it reaches the assume_NL_start or not using get_ktests_that_do_not_reach_nl_start from pipeline


if __name__ == "__main__":
    main()

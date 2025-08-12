import os
import shutil
import argparse
import subprocess
import json
from get_assume_code import get_assume_code
from model import get_model  # Assuming you have a model module to import
from start_klee import merge_and_save 
from cov_line_coverage import get_uncovered_lines_in_docker, get_covered_lines_for_ktest
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


def get_uncovered_from_container(container_name, c_path_inside_container, klee_run_dir=None):
    try:
        # Start the container
        subprocess.run(["docker", "start", container_name], check=True)

        # Show the command being run
        print(f"Running in container {container_name}: python3 /home/klee/get_klee_coverage.py {c_path_inside_container}")

        # Run the coverage script inside the container
        if klee_run_dir:
            print(F"Running with KLEE run dir: {klee_run_dir} for file {c_path_inside_container}")
            result = subprocess.run([
                "docker", "exec", container_name,
                "python3", "/home/klee/get_klee_coverage.py", "--c_file_path", c_path_inside_container, "--klee_run_dir", klee_run_dir
            ], capture_output=True, text=True, check=True)


        else:
            result = subprocess.run([
                "docker", "exec", container_name,
                "python3", "/home/klee/get_klee_coverage.py","--c_file_path", c_path_inside_container
            ], capture_output=True, text=True, check=True)

        # Capture and display stdout
        output = result.stdout.strip()
        print("Output from container:", output)

        # Parse JSON result
        parsed = json.loads(output)
        covered = parsed.get("covered", [])
        uncovered = parsed.get("uncovered", [])

        return {
            "covered": covered,
            "uncovered": uncovered
        }

    except subprocess.CalledProcessError as e:
        print("Error running in container:", e.stderr)
        return None

    # finally:
    #     # Stop the container
    #     try:
    #         subprocess.run(["docker", "stop", container_name], check=True)
    #     except Exception as stop_err:
    #         print("Warning: failed to stop container", stop_err)


def run_preprocessing(
    c_file_path: str,
    log_folder: str = "log_tmp",
    docker_name: str = "klee_logic_bombs",
    model_name: str = "deepseek-v3-aliyun",
    is_klee_annotated: bool = False,
    is_klee_marked: bool = False
):
    
    
   
   
    
    
    if str(is_klee_annotated).lower() in ['yes', 'true', '1', 'on', 'y', 't']:
        is_klee_annotated = True
    else:
        is_klee_annotated = False

    if not os.path.isfile(c_file_path):
        raise FileNotFoundError(f"C file not found: {c_file_path}")

    # Step 1: Reset log folder
    if os.path.exists(log_folder):
        shutil.rmtree(log_folder)
    os.makedirs(log_folder)

    if not is_klee_annotated:
        #create new C file with KLEE annotations 
        #copy the C file to the log folder
        c_file_path_annotated = c_file_path.replace(".c", "_annotated.c")
        model_klee_main = create_model_log_based_name(model_name, log_folder, "Klee_main")
        annotated_klee = merge_and_save(model_klee_main, c_file_path, c_file_path_annotated)
        c_file_path = c_file_path_annotated
        print(f"Annotated C file written to: {c_file_path}")
    else:
        c_file_path_annotated = c_file_path.replace(".c", "_annotated.c")
        #copy the C file to the log folder
        shutil.copy(c_file_path, c_file_path_annotated)
        c_file_path = c_file_path_annotated

    shutil.copy(c_file_path, log_folder)
    #make the copy the current C file
    c_file_path = os.path.join(log_folder, os.path.basename(c_file_path))

    # Step 2: Prepare tmp_run_klee inside logic_bombs
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logic_bombs_root = os.path.join(script_dir, "logic_bombs")
    #get the base name of the logfolder
    log_base = os.path.basename(log_folder)
    tmp_dir = os.path.join(logic_bombs_root, log_base)
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    print(f"Temporary directory created at: {tmp_dir}")

    # Step 3: Copy the C file to tmp_run_klee
    c_file_name = os.path.basename(c_file_path)
    target_c_path = os.path.join(tmp_dir, c_file_name)
    shutil.copy(c_file_path, target_c_path)

    # Step 4: Run get_uncovered inside container
    container_log=f"/home/klee/{log_base}"
    c_path_inside_container = f"{container_log}/{c_file_name}"
    klee_run_dir= f"{container_log}/coverage_run"
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
    for lineno, content in uncovered_llvm:
        print(f"{lineno}: {content}")

    # Step 5: Move tmp_run_klee to log folder
    final_log_path = os.path.join(log_folder, "docker_preprocessing")
    #copy the tmp dir into the log folder
    shutil.copytree(tmp_dir, final_log_path, dirs_exist_ok=True)
    marked_path= c_file_path.replace(".c", "_marked.c")
    print(f"Marked C file will be written to: {marked_path}")
    if not is_klee_marked:
        model_marked= create_model_log_based_name(model_name, log_folder, "Nl_markers")

        modified_code = get_assume_code(
            model=model_marked,
            source_path=c_file_path,
            output_path=marked_path,
            uncovered=uncovered_lines
        )
    else:
        modified_code = marked_path
        shutil.copy(c_file_path, modified_code)
        print(f"Marked C file written to: {modified_code}")
    uncovered_llvm_list = [list(item) for item in uncovered_llvm]
    print(f"Modified code written to: {c_file_path.replace('.c', '_marked.c')}")
    return {
        "annotated_path": marked_path,   # or whatever outputs you want to return
        "coverage": {
            "covered": covered_lines,
            "uncovered": uncovered_lines,
            "uncovered_llvm": uncovered_llvm_list
        },
        "dir_of_coverage": tmp_dir,
        "log_inside_container": container_log
    }


def main():
    parser = argparse.ArgumentParser(description="Run get_uncovered inside KLEE container.")
    parser.add_argument("--c_file_path", help="Path to the C file to analyze")
    parser.add_argument("--log_folder", default="log_tmp", help="Log folder to store outputs (default: log_tmp)")
    parser.add_argument("--docker_name", default="klee_logic_bombs", help="Name of the running KLEE container (default: klee_logic_bombs)")
    parser.add_argument('--model', required=False, default='deepseek-v3-aliyun',
                        help='Model to use (optional, default: deepseek-v3-aliyun)')
    parser.add_argument('--is_klee_annotated',required=False, action='store_true',
                        help='Set this if the input C file is already KLEE-annotated')
    parser.add_argument('--is_klee_marked', required=False, default=False,
                        help='Set this if the input C file is already KLEE-marked')

    args = parser.parse_args()
    if args.model:
        model_name = args.model
    else:
        model_name = "deepseek-v3-aliyun"
    c_file_path = args.c_file_path
    log_folder = args.log_folder
    docker_name = args.docker_name
    
    if args.is_klee_marked.lower() in ['yes', 'true', '1', 'on', 'y', 't']:
        is_klee_marked = True
    else:
        is_klee_marked = False
    if not args.is_klee_annotated:
        is_klee_annotated = False
    else:
        is_klee_annotated = args.is_klee_annotated
    if str(is_klee_annotated).lower() in ['yes', 'true', '1', 'on', 'y', 't']:
        is_klee_annotated = True
    else:
        is_klee_annotated = False
    if not os.path.isfile(c_file_path):
        raise FileNotFoundError(f"C file not found: {c_file_path}")
    
    preprocessing_results= run_preprocessing(c_file_path= c_file_path, log_folder=log_folder, docker_name=docker_name, model_name=model_name, is_klee_annotated=is_klee_annotated, is_klee_marked=is_klee_marked)
    #print the preprocessing results in anice way
    print("Preprocessing results:")
    print(f"Annotated path :{preprocessing_results['annotated_path']}")

    for covered in preprocessing_results["coverage"]["covered"]:
        print(f"  Covered line: {covered}")
        
    for uncovered in preprocessing_results["coverage"]["uncovered"]:
        print(f"  Uncovered line: {uncovered}")
    # Step 1: Reset log folder
    print(f"Uncovered LLVM\n:")
    for uncov in preprocessing_results["coverage"]["uncovered_llvm"]:
        print(f"{uncov}")

    # #print the types of the results
    # print(f"Types of results:")
    # print(f"  Annotated path type: {type(preprocessing_results['annotated_path'])}")
    # print(f"  Covered lines type: {type(preprocessing_results['coverage']['covered'][0])}")
    # print(f"  Uncovered lines type: {type(preprocessing_results['coverage']['uncovered'][0])}")
    # print(f"  Uncovered LLVM lines type: {type(preprocessing_results['coverage']['uncovered_llvm'][0])}")


if __name__ == "__main__":
    main()

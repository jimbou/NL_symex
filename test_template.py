import os
import sys
import shutil
import json
import re
from get_minimal import get_minimal
import argparse
from model import get_model
from translate_to_smt import get_smt_constraints
from replace import rewrite_and_replace
from replace_mad import debate_rewrite
from  prepare_klee import create_klee_main
from templates import get_rewrite_prompt, universal_prompt, get_feedback, get_correction, get_test_vectors,get_differential_testing_code, run_differential_testing_code



import subprocess
import os

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


def create_log_folders_and_models(log_folder,model_name):
    log_folder_template= os.path.join(log_folder, "template_choice")
    if not os.path.exists(log_folder_template):
        os.makedirs(log_folder_template)
        print(f"[INFO] Created log folder: {log_folder_template}")
    else:
        print(f"[INFO] Using existing log folder: {log_folder_template}")
    #create the model
    model_template = get_model(model_name, 0.5, log_folder_template)

    log_folder_translated = os.path.join(log_folder, "translated")
    if not os.path.exists(log_folder_translated):
        os.makedirs(log_folder_translated)
        print(f"[INFO] Created log folder: {log_folder_translated}")
    else:
        print(f"[INFO] Using existing log folder: {log_folder_translated}")
    #create the model

    model_translated = get_model(model_name, 0.5, log_folder_translated)

    log_folder_universal = os.path.join(log_folder, "universal")
    if not os.path.exists(log_folder_universal):
        os.makedirs(log_folder_universal)
        print(f"[INFO] Created log folder: {log_folder_universal}")
    else:
        print(f"[INFO] Using existing log folder: {log_folder_universal}")
    #create the model
    model_universal = get_model(model_name, 0.5, log_folder_universal)

    log_folder_feedback = os.path.join(log_folder, "feedback")
    if not os.path.exists(log_folder_feedback):
        os.makedirs(log_folder_feedback)
        print(f"[INFO] Created log folder: {log_folder_feedback}")
    else:
        print(f"[INFO] Using existing log folder: {log_folder_feedback}")
    #create the model
    model_feedback = get_model(model_name, 0.5, log_folder_feedback)

    return model_template, log_folder_template, model_translated, log_folder_translated, model_universal, log_folder_universal, model_feedback, log_folder_feedback

def extract_blocks(c_code: str):
    start_marker = "assume_NL_start;"
    end_marker = "assume_NL_stop;"
    
    start_idx = c_code.find(start_marker)
    end_idx = c_code.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        raise ValueError("Missing NL markers")

    prefix = c_code[:start_idx].strip()
    nl_code = c_code[start_idx+len(start_marker):end_idx].strip()
    suffix = c_code[end_idx+len(end_marker):].strip()

    return prefix, nl_code, suffix

def make_prefix_compilable(prefix: str) -> str:
    if 'return' not in prefix:
        return prefix + "\nreturn 0;\n}"
    return prefix

def ensure_log_folder(log_dir: str):
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)
    os.makedirs(log_dir)

def apply_replacement_and_save(original_code: str, replacement_code: str, output_path: str):
    start_marker = "assume_NL_start;"
    end_marker = "assume_NL_stop;"
    
    start_idx = original_code.find(start_marker)
    end_idx = original_code.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        raise ValueError("Markers not found in original code.")

    # Remove the entire NL block including the markers
    before = original_code[:start_idx].rstrip()
    after = original_code[end_idx + len(end_marker):].lstrip()

    # Remove include "assume.h" if present
    cleaned = re.sub(r'#include\s+["<]assume\.h[">]\s*', '', before + '\n' + replacement_code + '\n' + after)
    #if file does not exist create it and write the result there
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    with open(output_path, 'w') as f:
        f.write(cleaned)

    print(f"[✓] Saved modified file to {output_path}")



def main():
    parser = argparse.ArgumentParser(description="Extract NL code block and generate minimal compilable replacement.")
    parser.add_argument('--c_code', required=True,
                        help='Path to C file containing the whole program')
    parser.add_argument('--log_folder', required=False, default='log_temp',
                        help='Path to log folder (optional, default: log_temp)')
    parser.add_argument('--model', required=False, default='deepseek-v3-aliyun',
                        help='Model to use (optional, default: deepseek-v3-aliyun)')
    parser.add_argument('--mad', required=False, default=True,
                        help='Should we use multi agent debate? (optional, default: True)')

    args = parser.parse_args()
    if args.model:
        model_name = args.model
    else:
        model_name = "deepseek-v3-aliyun"
    print(f"Using model {model_name}")
    # Check if the log folder argument is provided, otherwise use the default
    if args.log_folder:
        log_folder = args.log_folder
    else:
        log_folder = 'log_temp'

    c_script_path = args.c_code

    
    if args.mad == 'True' or args.mad == 'true' or args.mad == '1' or args.mad == 'yes' or args.mad == True:
        print("[INFO] Using multi-agent debate mode")
        mad= True
    else:
        print("[INFO] Not using multi-agent debate mode")
        mad= False
    # Ensure clean log folder
    if os.path.exists(log_folder):
        shutil.rmtree(log_folder)
    os.makedirs(log_folder)

    model_template= create_model_log_based_name(model_name, log_folder, "template_choice")
    model_translated= create_model_log_based_name(model_name, log_folder, "translated")
    model_universal= create_model_log_based_name(model_name, log_folder, "universal")
    model_feedback= create_model_log_based_name(model_name, log_folder, "feedback")
    model_updated_trasnlation= create_model_log_based_name(model_name, log_folder, "updated_translation")
    # log_template, model_translated, log_translated, model_universal, log_universal, model_feedback, log_folder_feedback = create_log_folders_and_models(f"{log_folder}/llm_calls" , model_name)

    with open(c_script_path, 'r') as f:
        c_code = f.read()
    #remove #include "assume.h" if it exists
    c_code = c_code.replace('#include "assume.h"', '').strip()


    prefix, nl_code, _ = extract_blocks(c_code)
    prefix_compilable = make_prefix_compilable(prefix)

    
    with open(os.path.join(log_folder, "prefix.c"), 'w') as f:
        f.write(prefix_compilable)

    with open(os.path.join(log_folder, "nl_block.c"), 'w') as f:
        f.write(nl_code)

    print(f"[✓] Written prefix.c and nl_block.c to {log_folder}/")
    clean_code = c_code.replace('assume_NL_start;', '').replace('assume_NL_stop;', '').strip()
    universal_transformed_code = universal_prompt(model_universal, clean_code, nl_code)

    #get the feedback from the model
    decision, feedback = get_feedback(model_feedback, clean_code, universal_transformed_code)
    decision = "NO"
    feedback = "The transformation is not correct. Please try to create a model of the bonus function"
    with open(os.path.join(log_folder, "universal_transformed_code.c"), 'w') as f:
        f.write(universal_transformed_code)

    with open(os.path.join(log_folder, "feedback.txt"), 'w') as f:
        f.write(f"Decision: {decision}\n")
        f.write(feedback)

    if "no" in decision.lower():
        print("[INFO] Feedback indicates the transformation is not correct. Exiting.")
        updated_transformed_code = get_correction(model_updated_trasnlation, clean_code, universal_transformed_code, feedback)
        with open(os.path.join(log_folder, "updated_transformed_code.c"), 'w') as f:
            f.write(updated_transformed_code)
    else :
        updated_transformed_code = universal_transformed_code
    
    model_differential_testing = create_model_log_based_name(model_name, log_folder, "differential_testing")
    differential_testing_code = get_differential_testing_code(model_differential_testing, clean_code, nl_code, updated_transformed_code)
    with open(os.path.join(log_folder, "differential_testing_code.c"), 'w') as f:
        f.write(differential_testing_code)
        #keep the path of this file
    path_to_differential_testing_code = os.path.join(log_folder, "differential_testing_code.c")

    model_tests = create_model_log_based_name(model_name, log_folder, "model_tests")
                                                  
    test_vectors = get_test_vectors(model_tests, differential_testing_code)
    
    with open(os.path.join(log_folder, "test_vectors.json"), 'w') as f:
        json.dump(test_vectors, f, indent=4)

    run_tests_results = run_differential_testing_code( path_to_differential_testing_code, test_vectors)

    with open(os.path.join(log_folder, "run_tests.c"), 'w') as f:
        f.write(run_tests_results)



    # clean_code = c_code.replace('#include "assume.h"', '')
    
    transformed_code = get_rewrite_prompt( model_template, model_translated, c_code)


    with open(os.path.join(log_folder, "trasnlated_code.c"), 'w') as f:
        f.write(transformed_code)


if __name__ == "__main__":
    main()

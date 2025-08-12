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
from ktest_transform import apply_remap_on_ktests


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
    start_marker = "assume_NL_start();"
    end_marker = "assume_NL_stop();"
    start_marker2 = "assume_NL_start"
    end_marker2 = "assume_NL_stop"
    
    start_idx = c_code.find(start_marker)
    end_idx = c_code.find(end_marker)
    
    if start_idx == -1:
        start_idx = c_code.find(start_marker2)
    if end_idx == -1:
        end_idx = c_code.find(end_marker2)
    if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
        print(f"[ERROR] Could not find NL markers in the C code.{c_code}")
        print(f"Start marker: {start_marker}, End marker: {end_marker}")
        print(f"Start marker2: {start_marker2}, End marker2: {end_marker2}")
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
import os
import re

def apply_replacement_and_save(original_code: str, replacement_code: str, output_path: str):
    start_marker = "assume_NL_start"
    end_marker = "assume_NL_stop"

    lines = original_code.splitlines()
    start_idx = end_idx = -1

    for i, line in enumerate(lines):
        if start_marker in line:
            start_idx = i
        if end_marker in line:
            end_idx = i
        if start_idx != -1 and end_idx != -1:
            break

    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        raise ValueError("Markers not found or invalid order in original code.")

    # Determine base indentation from the first line inside the block
    if start_idx + 1 < len(lines):
        match = re.match(r'^(\s*)', lines[start_idx + 1])
        base_indent = match.group(1) if match else ''
    else:
        base_indent = ''

    # Re-indent replacement code
    replacement_lines = [
        base_indent + line.strip() for line in replacement_code.strip().splitlines()
    ]

    # Build new lines
    new_lines = []
    new_lines.extend(lines[:start_idx])
    new_lines.append(base_indent + "// assume_NL_start();")
    new_lines.extend(replacement_lines)
    new_lines.append(base_indent + "// assume_NL_stop();")
    new_lines.extend(lines[end_idx + 1:])

    # Remove include of assume.h
    cleaned = "\n".join(new_lines)
    cleaned = re.sub(r'#include\s+["<]assume\.h[">]\s*\n?', '', cleaned)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(cleaned + "\n")

    print(f"[✓] Saved modified file to {output_path}")
    return cleaned

def get_translated_code(model_name, log_folder, c_script_path):
    """
    Translates the C code using the specified model and saves the result.
    """
    #check that the log folder exists
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
        print(f"[INFO] Created log folder: {log_folder}")
    else:
        print(f"[INFO] Using existing log folder: {log_folder}")
    
    #if the c_script_path is not a file, raise an error
    if not os.path.isfile(c_script_path):
        raise FileNotFoundError(f"C file not found: {c_script_path}")
    with open(c_script_path, 'r') as f:
        c_code = f.read()

    # Remove #include "assume.h" if it exists
    c_code = c_code.replace('#include "assume.h"', '').strip()
    c_code = c_code.replace('#include "../../assume.h"', '').strip()
    c_code = c_code.replace('#include "../assume.h"', '').strip()

    prefix, nl_code, _ = extract_blocks(c_code)
    prefix_compilable = make_prefix_compilable(prefix)

    with open(os.path.join(log_folder, "prefix.c"), 'w') as f:
        f.write(prefix_compilable)

    with open(os.path.join(log_folder, "nl_block.c"), 'w') as f:
        f.write(nl_code)

    print(f"[✓] Written prefix.c and nl_block.c to {log_folder}/")
    #replace the line with assume_Nl_start rith a comment //assume_NL_start();
    #the line m,ight contain more stuff bwfore and after
    # Replace any line containing 'assume_NL_start' with '// assume_NL_start();'
    c_code_lines = c_code.splitlines()
    replaced_lines = []
    for line in c_code_lines:
        if 'assume_NL_start' in line:
            #keep the indentation and replace the line with a comment
            #collect the spaces in the beginning of the line
            indent = re.match(r'^\s*', line).group(0)
            replaced_lines.append(f"{indent}// assume_NL_start();")
        elif 'assume_NL_stop' in line:
            #keep the indentation and replace the line with a comment
            indent = re.match(r'^\s*', line).group(0)
            replaced_lines.append(f"{indent}// assume_NL_stop();")
            replaced_lines.append('// assume_NL_start();')
        else:
            replaced_lines.append(line)
    c_code = '\n'.join(replaced_lines)
    model_universal= create_model_log_based_name(model_name, log_folder, "universal")
    universal_transformed_code = universal_prompt(model_universal, c_code, nl_code)
    print(f"[✓] Transformed code using universal model: {universal_transformed_code}")
    translated_path = os.path.join(log_folder, "universal_transformed_code.c")
    with open(translated_path, 'w') as f:
        f.write(universal_transformed_code)
    return translated_path, prefix, nl_code

def main():
    parser = argparse.ArgumentParser(description="Extract NL code block and generate minimal compilable replacement.")
    parser.add_argument('--c_code', required=True,
                        help='Path to C file containing the whole program')
    parser.add_argument('--log_folder', required=False, default='log_temp',
                        help='Path to log folder (optional, default: log_temp)')
    parser.add_argument('--model', required=False, default='deepseek-v3-aliyun',
                        help='Model to use (optional, default: deepseek-v3-aliyun)')
    parser.add_argument('--mad', required=False, default=False,
                        help='Should we use multi agent debate? (optional, default: True)')
    parser.add_argument('--differential_testing', action='store_true',
                        help='Enable differential testing mode', required=False, default=False)
    parser.add_argument('--ktest_dir', required=False, default='ktests',
                        help='Directory containing ktest files for remapping (optional, default: ktests)')
    
   
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

    if args.differential_testing or args.differential_testing == 'True' or args.differential_testing == 'true' or args.differential_testing == '1' or args.differential_testing == 'yes' or args.differential_testing == True:
        print("[INFO] Using differential testing mode")
        differential_testing = True
    else:
        print("[INFO] Not using differential testing mode")
        differential_testing = False
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

    model_k_tests = create_model_log_based_name(model_name, log_folder, "k_tests")

    #read a file for the original code, read a file for the transformed code
    with open("/home/jim/NL_constraints/logic_bombs/ln_ef_l2/ln_ef_l2_klee_transformed_internal.c", 'r') as f:
        transformed_code = f.read()
    with open("/home/jim/NL_constraints/logic_bombs/ln_ef_l2/ln_ef_l2_klee.c", 'r') as f:
        original_code = f.read()
    
    input_dir = args.ktest_dir
    apply_remap_on_ktests(model_k_tests, original_code, transformed_code, input_dir)
    return 0
    with open(c_script_path, 'r') as f:
        c_code = f.read()
    #remove #include "assume.h" if it exists
    c_code = c_code.replace('#include "assume.h"', '').strip()
    c_code = c_code.replace('#include "../../assume.h"', '').strip()

    c_code = c_code.replace('#include "../assume.h"', '').strip()

    prefix, nl_code, _ = extract_blocks(c_code)
    prefix_compilable = make_prefix_compilable(prefix)

    
    with open(os.path.join(log_folder, "prefix.c"), 'w') as f:
        f.write(prefix_compilable)

    with open(os.path.join(log_folder, "nl_block.c"), 'w') as f:
        f.write(nl_code)

    print(f"[✓] Written prefix.c and nl_block.c to {log_folder}/")
    clean_code = c_code.replace('assume_NL_start;', '').replace('assume_NL_stop;', '').strip()
    universal_transformed_code = universal_prompt(model_universal, clean_code, nl_code)

    with open(os.path.join(log_folder, "universal_transformed_code.c"), 'w') as f:
        f.write(universal_transformed_code)

    if mad:
        #get the feedback from the model
        decision, feedback = get_feedback(model_feedback, clean_code, universal_transformed_code)
        # decision = "NO"
        # feedback = "The transformation is not correct. Please try to create a model of the bonus function"
    

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
    else:
        updated_transformed_code = universal_transformed_code
        with open(os.path.join(log_folder, "updated_transformed_code.c"), 'w') as f:
            f.write(updated_transformed_code)
    

    if differential_testing:
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



    # # clean_code = c_code.replace('#include "assume.h"', '')
    
    # transformed_code = get_rewrite_prompt( model_template, model_translated, c_code)


    # with open(os.path.join(log_folder, "trasnlated_code.c"), 'w') as f:
    #     f.write(transformed_code)


if __name__ == "__main__":
    main()

import os
import sys
import shutil
import re
from get_minimal import get_minimal
import argparse
from model import get_model
from translate_to_smt import get_smt_constraints
from replace import rewrite_and_replace


def create_log_folders_and_models(log_folder,model_name):
    log_folder_total= os.path.join(log_folder, "total_vars")
    if not os.path.exists(log_folder_total):
        os.makedirs(log_folder_total)
        print(f"[INFO] Created log folder: {log_folder_total}")
    else:
        print(f"[INFO] Using existing log folder: {log_folder_total}")
    #create the model
    model_total = get_model(model_name, 0.5, log_folder_total)

    log_folder_smt = os.path.join(log_folder, "smt_vars")
    if not os.path.exists(log_folder_smt):
        os.makedirs(log_folder_smt)
        print(f"[INFO] Created log folder: {log_folder_smt}")
    else:
        print(f"[INFO] Using existing log folder: {log_folder_smt}")
    #create the model
    model_smt = get_model(model_name, 0.5, log_folder_smt)
    print(f"[INFO] Using model: {model_name} with temperature 0.5")

    log_folder_replace = os.path.join(log_folder, "replace_NL")
    if not os.path.exists(log_folder_replace):
        os.makedirs(log_folder_replace)
        print(f"[INFO] Created log folder: {log_folder_replace}")
    else:
        print(f"[INFO] Using existing log folder: {log_folder_replace}")
    #create the model
    model_replace = get_model(model_name, 0.5, log_folder_replace)
    print(f"[INFO] Using model: {model_name} with temperature 0.5 for replacement")

    return model_total, log_folder_total, model_smt, log_folder_smt, model_replace, log_folder_replace

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
    
    args = parser.parse_args()
    if args.model:
        model_name = args.model
    else:
        model_name = "deepseek-v3-aliyun"

    # Check if the log folder argument is provided, otherwise use the default
    if args.log_folder:
        log_folder = args.log_folder
    else:
        log_folder = 'log_temp'

    c_script_path = args.c_code
    
   

    
    # Ensure clean log folder
    if os.path.exists(log_folder):
        shutil.rmtree(log_folder)
    os.makedirs(log_folder)

    model, model_folder, model_smt, log_folder_smt, model_replace, log_folder_replace = create_log_folders_and_models(f"{log_folder}/get_minimal" , model_name)

    with open(c_script_path, 'r') as f:
        c_code = f.read()

    prefix, nl_code, _ = extract_blocks(c_code)
    prefix_compilable = make_prefix_compilable(prefix)

    
    with open(os.path.join(log_folder, "prefix.c"), 'w') as f:
        f.write(prefix_compilable)

    with open(os.path.join(log_folder, "nl_block.c"), 'w') as f:
        f.write(nl_code)

    print(f"[✓] Written prefix.c and nl_block.c to {log_folder}/")

    clean_code = c_code.replace('#include "assume.h"', '')
    clean_code = clean_code.replace('assume_NL_start;', '').replace('assume_NL_stop;', '').strip()

    replacement = get_minimal(model, clean_code, nl_code)
    apply_replacement_and_save(c_code, replacement, '{log_folder}/minimal.c')

    prefix_constraints = f"tbf\n"
    post_constraints = f"tbf\n"

    smt_translation = get_smt_constraints(model_smt, c_code, nl_code, prefix_constraints, post_constraints)

    with open(os.path.join(log_folder, "nl_block.smt2"), 'w') as f:
        f.write(smt_translation)

    rewritten_code = rewrite_and_replace(model_replace, c_code, nl_code)

    with open(os.path.join(log_folder, "nl_block_rewritten.c"), 'w') as f:
        f.write(rewritten_code)


if __name__ == "__main__":
    main()

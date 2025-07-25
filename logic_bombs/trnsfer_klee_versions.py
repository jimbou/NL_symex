import os
import shutil

src_root = "src"
out_root = "output_dir"

for dirpath, dirnames, filenames in os.walk(src_root):
    for fname in filenames:
        if fname.endswith(".c"):
            src_file_path = os.path.join(dirpath, fname)
            output_file_path = os.path.join(out_root, fname)

            if os.path.exists(output_file_path):
                klee_file_path = os.path.join(dirpath, fname.replace(".c", "_klee.c"))
                shutil.copy(output_file_path, klee_file_path)
                print(f"Copied {output_file_path} -> {klee_file_path}")
            else:
                print(f"Not found in output_dir: {fname}")

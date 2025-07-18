import os
import shutil

source_dir = "/home/jim/NL_constraints/logic_bombs/src/experiments"         # directory with files to copy
dest_root = "/home/jim/NL_constraints/log_folders"           # destination directory that contains subdirs named after filenames (without extension)

for filename in os.listdir(source_dir):
    file_path = os.path.join(source_dir, filename)
    if os.path.isfile(file_path):
        name, _ = os.path.splitext(filename)
        dest_subdir = os.path.join(dest_root, name)

        if os.path.isdir(dest_subdir):
            dest_path = os.path.join(dest_subdir, filename)
            shutil.copy(file_path, dest_path)
            print(f"Copied {filename} → {dest_subdir}")
        else:
            print(f"Skipping {filename}: no subdirectory {dest_subdir}")

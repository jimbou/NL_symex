import os
import subprocess

# Path to the directory containing .c files
experiments_dir = "/home/jim/NL_constraints/logic_bombs/src/experiments2"
log_dir_base = "log_folders"

error_log_file = "failed_runs.txt"

os.makedirs(log_dir_base, exist_ok=True)

# Clear previous error log (optional)
with open(error_log_file, "w") as f:
    f.write("")

for filename in os.listdir(experiments_dir):
    if filename.endswith(".c"):
        name = filename[:-2]
        c_code_path = os.path.join(experiments_dir, filename)
        log_folder = os.path.join(log_dir_base, name)
        os.makedirs(log_folder, exist_ok=True)

        command = [
            "python3",
            "test_template.py",
            "--c_code", c_code_path,
            "--model", "gpt-4.1",
            "--log_folder", log_folder,
            "--mad", "True"
        ]

        print("Running:", " ".join(command))
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            with open(error_log_file, "a") as f:
                f.write(f"FAILED: {filename}\nError: {str(e)}\n\n")
            print(f"Error running {filename}, logged to {error_log_file}")
        except Exception as e:
            with open(error_log_file, "a") as f:
                f.write(f"FAILED: {filename}\nUnexpected Error: {str(e)}\n\n")
            print(f"Unexpected error in {filename}, logged to {error_log_file}")
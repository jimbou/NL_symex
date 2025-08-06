import os
import subprocess
import sys

def docker_bash(docker_name, cmd, **kwargs):
    """Run a bash command inside a running docker container."""
    return subprocess.run(["docker", "exec", docker_name, "bash", "-lc", cmd], **kwargs)

def docker_copy_to(docker_name, local_path, container_path):
    """Copy a file or directory into the Docker container."""
    return subprocess.run(["docker", "cp", local_path, f"{docker_name}:{container_path}"], check=True)

def get_uncovered_lines_in_docker(docker_name, ktest_dir, c_file_path):
    c_basename = os.path.basename(c_file_path)
    c_name = os.path.splitext(c_basename)[0]
    coverage_dir = os.path.normpath(f"{ktest_dir.rstrip('/')}/../coverage_dir")

    replay_exe = f"{coverage_dir}/ghost_coverage"
    profdata = f"{coverage_dir}/ghost.profdata"
    cov_output = f"{coverage_dir}/llvm_cov_output.txt"
    print(f"[INFO] Using coverage directory: {coverage_dir}")
    # Step 1: Create coverage_dir and delete if exists
    docker_bash(docker_name, f"rm -rf {coverage_dir}", check=True)
    print(f"[INFO] Removed existing coverage directory: {coverage_dir}")
    docker_bash(docker_name, f"mkdir -p {coverage_dir}", check=True)
    print(f"[INFO] Created coverage directory: {coverage_dir}")
    # Step 2: Copy C file and .ktest files into container:/tmp/coverage_dir
    #aqll the folders are in the docker so use docker bash with cp
    docker_bash(docker_name, f"cp {c_file_path} {coverage_dir}/{c_basename}", check=True)
    print(f"[INFO] Copied C file to container: {coverage_dir}/{c_basename}")
    # Get list of .ktest files inside the container
    list_ktests = subprocess.run(
        ["docker", "exec", docker_name, "bash", "-lc", f"ls {ktest_dir}/*.ktest"],
        capture_output=True,
        text=True,
        check=True
    )

    ktest_files = list_ktests.stdout.strip().splitlines()

    # Copy each one inside the container (from ktest_dir to coverage_dir)
    for ktest_path in ktest_files:
        ktest_base = os.path.basename(ktest_path)
        docker_bash(
            docker_name,
            f"cp {ktest_path} {coverage_dir}/{ktest_base}",
            check=True
        )
    # Step 3: Compile with instrumentation
    compile_cmd = (
        f"clang -O0 -g -fprofile-instr-generate -fcoverage-mapping "
        f"-L/tmp/klee_build130stp_z3/lib -I/tmp/klee_build130stp_z3/include "
        f"{coverage_dir}/{c_basename} -lkleeRuntest -lm -o {replay_exe}"
    )
    docker_bash(docker_name, compile_cmd, check=True)

    # Step 4: Replay each .ktest file
    replay_cmd = (
    f"cd {coverage_dir} && "
    f"export LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH && "
    f"for f in *.ktest; do "
    f"LLVM_PROFILE_FILE=ghost_$f.profraw KTEST_FILE=$f ./ghost_coverage; "
    f"done"
)

    docker_bash(docker_name, replay_cmd, check=True)

    # Step 5: Merge coverage data
    merge_cmd = f"cd {coverage_dir} && llvm-profdata merge -sparse ghost_*.profraw -o ghost.profdata"
    docker_bash(docker_name, merge_cmd, check=True)

    # Step 6: Run llvm-cov and save to file
    cov_cmd = (
        f"cd {coverage_dir} && "
        f"llvm-cov show ./ghost_coverage "
        f"-instr-profile=ghost.profdata "
        f"--path-equivalence . "
        f"-format=text {c_basename} > llvm_cov_output.txt"
    )
    docker_bash(docker_name, cov_cmd, check=True)

    # Step 7: Extract coverage output from container
    result = subprocess.run(
        ["docker", "exec", docker_name, "cat", cov_output],
        capture_output=True,
        text=True,
        check=True
    )
    text = result.stdout

    # Step 8: Parse uncovered lines
    uncovered = []
    for line in text.splitlines():
        # print(f"Processing line: {line}")
        parts = line.split("|", 2)  # <--- FIXED: use '|' as delimiter
        if len(parts) < 3:
            # print(f"Skipping line due to insufficient parts: {line}")
            continue

        lineno_str = parts[0].strip()
        count_str = parts[1].strip()
        content = parts[2]

        try:
            lineno = int(lineno_str)
        except ValueError:
            # print(f"Skipping line due to invalid lineno: {lineno_str}")
            continue

        print(f"Line {lineno}: {content.strip()} (count: {count_str})")
        if count_str.strip() == "":
            #this is a comment or include line
            # print(f"Skipping line {lineno} due to empty count")
            continue
        if count_str == "0" or count_str.startswith("#####"):
            stripped = content.strip()
            if not stripped:
                continue
            if stripped.startswith("//") or stripped.startswith("#"):
                continue
            if stripped in ("{", "}"):
                continue
            uncovered.append((lineno, stripped))

    return uncovered

def get_covered_lines_for_ktest(docker_name, exe_path, c_file_path, ktest_path):
    """
    Runs one .ktest file on the given executable inside Docker and returns
    a set of covered line numbers for the given C source file.
    """
    c_basename = os.path.basename(c_file_path)
    coverage_dir = os.path.normpath(f"{os.path.dirname(ktest_path.rstrip('/'))}/../coverage_dir_single")

    replay_exe = f"{coverage_dir}/ghost_coverage"
    profraw = f"{coverage_dir}/single.profraw"
    profdata = f"{coverage_dir}/single.profdata"
    cov_output = f"{coverage_dir}/single_cov.txt"

    # Step 1: Create clean coverage dir in Docker
    docker_bash(docker_name, f"rm -rf {coverage_dir}", check=True)
    docker_bash(docker_name, f"mkdir -p {coverage_dir}", check=True)

    # Step 2: Copy the C file and the .ktest file
    docker_bash(docker_name, f"cp {c_file_path} {coverage_dir}/{c_basename}", check=True)
    ktest_base = os.path.basename(ktest_path)
    docker_bash(docker_name, f"cp {ktest_path} {coverage_dir}/{ktest_base}", check=True)

    # Step 3: Compile with instrumentation
    compile_cmd = (
        f"clang -O0 -g -fprofile-instr-generate -fcoverage-mapping "
        f"-L/tmp/klee_build130stp_z3/lib -I/tmp/klee_build130stp_z3/include "
        f"{coverage_dir}/{c_basename} -lkleeRuntest -lm -o {replay_exe}"
    )
    docker_bash(docker_name, compile_cmd, check=True)

    # Step 4: Replay the single .ktest
    replay_cmd = (
        f"cd {coverage_dir} && "
        f"export LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH && "
        f"LLVM_PROFILE_FILE={profraw} "
        f"KTEST_FILE={ktest_base} ./ghost_coverage"
    )
    docker_bash(docker_name, replay_cmd, check=True)

    # Step 5: Merge to profdata
    docker_bash(docker_name, f"llvm-profdata merge -sparse {profraw} -o {profdata}", check=True)

    # Step 6: Run llvm-cov
    cov_cmd = (
        f"cd {coverage_dir} && "
        f"llvm-cov show ./ghost_coverage "
        f"-instr-profile={profdata} "
        f"--path-equivalence . "
        f"-format=text {c_basename} > {cov_output}"
    )
    docker_bash(docker_name, cov_cmd, check=True)

    # Step 7: Parse coverage output
    result = subprocess.run(
        ["docker", "exec", docker_name, "cat", cov_output],
        capture_output=True,
        text=True,
        check=True
    )

    covered_lines = set()
    for line in result.stdout.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue

        lineno_str = parts[0].strip()
        count_str = parts[1].strip()

        try:
            lineno = int(lineno_str)
        except ValueError:
            continue

        # Covered = any non-zero and not "#####"
        if count_str != "0" and not count_str.startswith("#####") and count_str != "":
            covered_lines.add(lineno)
    #remove the coverage dir from docker
    docker_bash(docker_name, f"rm -rf {coverage_dir}", check=True)
    return covered_lines


# === CLI runner ===
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <docker_name> <ktest_dir> <c_file_path>")
        sys.exit(1)

    docker_name = sys.argv[1]
    ktest_dir = sys.argv[2]
    c_file_path = sys.argv[3]

    uncovered = get_uncovered_lines_in_docker(docker_name, ktest_dir, c_file_path)

    print("Uncovered lines:")
    for lineno, content in uncovered:
        print(f"{lineno}: {content}")

import subprocess
import os


def check_if_ktest_reaches_Nl_start(docker_name: str, exe_path: str, ktest_path: str) -> tuple[bool, str]:
    """
    Runs `exe_path` inside `docker_name` with the single `ktest_path` (both inside the container).
    Returns (does_not_reach, trace_text).

    does_not_reach == True  => "Reached assume NL start" was NOT printed.
    does_not_reach == False => it DID reach (the marker was found).
    """
    # Where to drop the trace; use the executable's directory so we always have write access there
    exe_dir = os.path.dirname(exe_path) if os.path.dirname(exe_path) else "."
    trace_path = os.path.join(exe_dir, "trace_output.txt")

    # Clean any previous trace
    subprocess.run(
        ["docker", "exec", docker_name, "bash", "-lc", f"rm -f {trace_path}"],
        check=True
    )

    # Replay
    cmd = (
        f"export LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH && "
        f"KTEST_FILE='{ktest_path}' '{exe_path}' > '{trace_path}' 2>/dev/null"
    )
    try:
        subprocess.run(["docker", "exec", docker_name, "bash", "-lc", cmd], check=True)
    except subprocess.CalledProcessError as e:
        # If the program exits non-zero it's still okay; we only care about the trace text
        # Re-raise if you want strict behavior instead.
        pass

    # Read the trace
    read_output = subprocess.run(
        ["docker", "exec", docker_name, "bash", "-lc", f"cat '{trace_path}' || true"],
        capture_output=True,
        text=True,
        check=True
    )
    out = read_output.stdout

    reached = "Reached assume NL start" in out
    return (reached, out)


def get_ktests_that_do_not_reach_nl_start(docker_name, exe_path, ktest_dir):
    print(f"Getting .ktest files that do NOT reach NL start in {docker_name}...")
    print(f"Executable path inside container: {exe_path}")
    print(f"KTest directory inside container: {ktest_dir}")
    #if ktest dir does not end ina  / add it
    if not ktest_dir.endswith('/'):
        ktest_dir += '/'
    """
    For each .ktest in ktest_dir (in Docker), runs the given executable with it.
    Returns a list of full paths to .ktest files that do NOT print 'Reached assume NL start'.
    """
    # Step 1: List all .ktest files inside container
    result = subprocess.run(
        ["docker", "exec", docker_name, "bash", "-c", f"ls {ktest_dir}*.ktest"],
        capture_output=True,
        text=True,
        check=True
    )
    ktest_files = result.stdout.strip().splitlines()
    print(f"Found the following .ktest files: {ktest_files}")
    not_reaching = []

    for ktest_path in ktest_files:
        # use temp path inside container in the same path as the executable
        trace_path = f"{ktest_dir}/trace_output.txt"
        #rmove the trace file if it exists
        subprocess.run(["docker", "exec", docker_name, "rm", "-f", trace_path], check=True)
        cmd = (
            f"export LD_LIBRARY_PATH=/tmp/klee_build130stp_z3/lib:$LD_LIBRARY_PATH && "
            f"KTEST_FILE={ktest_path} {exe_path} > {trace_path} 2>/dev/null"
        )
        try:
            # Run the executable with the .ktest file
            subprocess.run(["docker", "exec", docker_name, "bash", "-c", cmd], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {ktest_path}: {e}")
            continue

        # Run the executable with this .ktest
        # subprocess.run(["docker", "exec", docker_name, "bash", "-c", cmd], check=True)

        # Read the trace output
        read_output = subprocess.run(
            ["docker", "exec", docker_name, "cat", trace_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Output for {ktest_path}: {read_output.stdout.strip()}")

        if "Reached assume NL start" not in read_output.stdout:
            not_reaching.append(ktest_path)
        else:
            print(f"✅ {ktest_path} reaches assume NL start")

    return not_reaching


if __name__ == "__main__":
    # Example usage
    docker_name = "klee_logic_bombs"
    exe_path = "tmp_ghost_8974dae9/build_tmp/ghost/reachability_ghost_replay"  # Path to the executable inside the container
    ktest_dir = "tmp_ghost_8974dae9/ghost_out-0/"  # Directory containing .ktest files inside the container

    not_reaching_ktests = get_ktests_that_do_not_reach_nl_start(docker_name, exe_path, ktest_dir)
    print("KTests that do NOT reach NL start:", not_reaching_ktests)
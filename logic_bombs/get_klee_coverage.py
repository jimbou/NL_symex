import os
import sys
import subprocess
import json
import re


def get_next_output_dir(base="klee-out-analysis"):
    i = 0
    while True:
        candidate = f"{base}-{i}"
        if not os.path.exists(candidate):
            return candidate
        i += 1

def compile_to_bc(c_file_path):
    """Compile a C file to LLVM bitcode (.bc) suitable for KLEE."""
    bc_file_path = c_file_path.replace(".c", ".bc")
    compile_cmd = [
        "clang", "-emit-llvm", "-c", "-g",
        "-Xclang", "-disable-O0-optnone",  # Keep debug info
        "-o", bc_file_path, c_file_path
    ]
    subprocess.run(compile_cmd, check=True)
    return bc_file_path

def run_klee(bc_file_path, output_dir):
    klee_cmd = [
        "klee",
        f"--output-dir={output_dir}",
        "--write-cov",
        "--emit-all-errors",
        bc_file_path
    ]
    subprocess.run(klee_cmd, check=True)

def parse_klee_stats(output_dir):
    """Parse KLEE metrics from the given output directory."""
    stats_path = os.path.join(output_dir, "run.stats")
    istats_path = os.path.join(output_dir, "run.istats")
    err_files = [f for f in os.listdir(output_dir) if f.endswith(".err")]

    metrics = {
        "total_errors": len(err_files),
        "uncovered_lines": 0,
        "unreached_functions": 0,
        "forking_hotspots": [],   # Placeholder; not in run.stats directly
        "timeouts": 0,
        "solver_queries": 0,
    }

    # Parse run.stats for timeouts and solver queries
    if os.path.exists(istats_path):
        with open(istats_path) as f:
            uncovered_lines = 0
            unreached_funcs = set()
            current_func = None
            func_reached = False

            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue  # Skip empty lines and comments

                if line.startswith("fn="):
                    if current_func and not func_reached:
                        unreached_funcs.add(current_func)
                    current_func = line.split("fn=")[-1].strip()
                    func_reached = False
                elif line.isdigit():
                    count = int(line)
                    if count == 0:
                        uncovered_lines += 1
                    else:
                        func_reached = True

            # Final check for the last function
            if current_func and not func_reached:
                unreached_funcs.add(current_func)

        metrics["uncovered_lines"] = uncovered_lines
        metrics["unreached_functions"] = len(unreached_funcs)
    return metrics

def extract_all_covered_lines(klee_output_dir):
    """Extracts all covered line numbers from .cov files in the KLEE output directory."""
    covered = set()
    for file in os.listdir(klee_output_dir):
        if file.endswith(".cov"):
            with open(os.path.join(klee_output_dir, file), "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        try:
                            _, lineno = line.rsplit(":", 1)
                            covered.add(int(lineno))
                        except ValueError:
                            continue
    return covered


def filter_useful_source_lines(source_path):
    """Return a list of (lineno, line) tuples for lines that are meaningful."""
    useful_lines = []
    in_multiline_comment = False

    with open(source_path, "r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f, start=1):
            raw = line.rstrip()
            stripped = raw.strip()

            # Skip empty
            if not stripped:
                continue

            # Skip multiline comments
            if in_multiline_comment:
                if "*/" in stripped:
                    in_multiline_comment = False
                continue
            if stripped.startswith("/*"):
                if "*/" not in stripped:
                    in_multiline_comment = True
                continue

            # Skip single-line comments and preprocessor
            if stripped.startswith("//") or stripped.startswith("#"):
                continue

            # Skip single brace
            if stripped in ("{", "}"):
                continue

            # Skip pure else or if lines (with or without braces)
            if re.fullmatch(r"(else|if)\s*[{]?", stripped):
                continue

            # Skip lines like "} else {"
            if re.fullmatch(r"}\s*else\s*[{]?", stripped):
                continue

            # Skip labels like `TOY:`
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\s*:", stripped):
                continue

            useful_lines.append((idx, raw))

    return useful_lines

def analyze_coverage(source_path, klee_output_dir):
    """Returns sets of covered and uncovered meaningful lines from the source file."""
    covered_line_numbers = extract_all_covered_lines(klee_output_dir)
    useful_lines = filter_useful_source_lines(source_path)

    covered = set()
    uncovered = set()

    for lineno, content in useful_lines:
        if lineno in covered_line_numbers:
            covered.add((lineno, content))
        else:
            uncovered.add((lineno, content))

    return covered, uncovered




def get_uncovered(c_file_path):
    if not os.path.isfile(c_file_path):
        print(f"Error: File not found: {c_file_path}")
        return

    try:
        bc_file_path = compile_to_bc(c_file_path)
        output_dir = get_next_output_dir()
        run_klee(bc_file_path, output_dir)
        # metrics = parse_klee_stats(output_dir)
        covered, uncovered =analyze_coverage(c_file_path,output_dir )

        # covered, uncovered = analyze_coverage(source_file, output_dir)

        print("Covered lines:")
        for l in sorted(covered):
            print(l)

        print("\nUncovered lines:")
        for l in sorted(uncovered):
            print(l)
    except subprocess.CalledProcessError as e:
        print(f"Error during execution: {e}")
    finally:
        pass
    return uncovered

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_klee_metrics.py <path_to_c_file>")
        return

    c_file_path = sys.argv[1]
    if not os.path.isfile(c_file_path):
        print(f"Error: File not found: {c_file_path}")
        return

    try:
        bc_file_path = compile_to_bc(c_file_path)
        output_dir = get_next_output_dir()
        run_klee(bc_file_path, output_dir)
        # metrics = parse_klee_stats(output_dir)
        covered, uncovered =analyze_coverage(c_file_path,output_dir )

        # covered, uncovered = analyze_coverage(source_file, output_dir)

        print("Covered lines:")
        for l in sorted(covered):
            print(l)

        print("\nUncovered lines:")
        for l in sorted(uncovered):
            print(l)
    except subprocess.CalledProcessError as e:
        print(f"Error during execution: {e}")
    finally:
        pass
    
    


if __name__ == "__main__":
    main()

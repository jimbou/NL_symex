def extract_branch_trace(filepath):
    trace = []
    with open(filepath, 'r') as f:
        for line in f:
            if "Branch taken:" in line:
                try:
                    num = int(line.strip().split("Branch taken:")[1].strip())
                    trace.append(num)
                except ValueError:
                    continue  # skip malformed lines

    if not trace:
        return []

    # Find index of the smallest number
    min_value = min(trace)
    min_index = trace.index(min_value)

    # Return all values *after* the smallest one
    return trace[min_index + 1:]


def compare_traces(file1, file2):
    trace1 = extract_branch_trace(file1)
    trace2 = extract_branch_trace(file2)

    if len(trace1) < 5 or len(trace2) < 5:
        if trace1 == trace2:
            print("Traces are identical.")
            return True
        else:
            print("Traces are not identical")
            return False

    first_five_1 = trace1[:5]
    first_five_2 = trace2[:5]

    print("First 5 after min in file1:", first_five_1)
    print("First 5 after min in file2:", first_five_2)
    if first_five_1 == first_five_2:
        print("First 5 after min are identical.")
        return True
    else:
        print("First 5 after min are not identical.")

        return False
    

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python branch_checker.py <file1> <file2>")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    if not compare_traces(file1, file2):
        print("Traces differ.")
        sys.exit(1)
    else:
        print("Traces are the same.")
        sys.exit(0)
    

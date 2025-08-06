import sys 
def filter_lines(filepath):
    """
    Returns a list of (line_num, line_content) tuples,
    excluding #include lines and lines between assume_NL_start/stop.
    """
    filtered = []
    in_nl_block = False
    with open(filepath, 'r') as f:
        for idx, line in enumerate(f, 1):
            stripped = line.strip()
            if stripped.startswith("#include"):
                continue
            if "// assume_NL_start();" in stripped:
                in_nl_block = True
                continue
            if "// assume_NL_stop();" in stripped:
                in_nl_block = False
                continue
            if in_nl_block:
                continue
            filtered.append((idx, line.rstrip('\n')))
    return filtered

def relaxed_line_map(file1, file2):
    lines1 = filter_lines(file1)
    lines2 = filter_lines(file2)

    # Only content from file2 needed for search
    used2 = set()
    map1to2 = {}

    for line_num1, content1 in lines1:
        found = -1
        for line_num2, content2 in lines2:
            if content1 == content2 and line_num2 not in used2:
                found = line_num2
                used2.add(line_num2)
                break
        map1to2[line_num1] = found

    # Reverse mapping: file2 → file1
    used1 = set()
    map2to1 = {}

    for line_num2, content2 in lines2:
        found = -1
        for line_num1, content1 in lines1:
            if content1 == content2 and line_num1 not in used1:
                found = line_num1
                used1.add(line_num1)
                break
        map2to1[line_num2] = found

    return map1to2, map2to1

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python line_mapper.py <file1.c> <file2.c>")
        sys.exit(1)

    file1, file2 = sys.argv[1], sys.argv[2]
    map1to2, map2to1 = relaxed_line_map(file1, file2)
    file1lines = filter_lines(file1)
    file2lines = filter_lines(file2)

    print("\nLine mapping from file1 to file2:")
    for k in sorted(map1to2):
        #print the line num and the line content
        print(f"{k}:{file1lines[k-1]} -> {file2lines[map1to2[k]-1]}")

    print("\nLine mapping from file2 to file1:")
    for k in sorted(map2to1):
        print(f"{file2}:{k} -> {file1}:{map2to1[k]}")

    
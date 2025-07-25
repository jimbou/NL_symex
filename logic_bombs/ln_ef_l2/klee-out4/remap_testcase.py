def remap_testcase(inputs: dict[str, list[int]]) -> dict[str, list[int]]:
    """
    Remap inputs from the transformed code back to the original code.

    The transformed code region replaces:
        double d = log(symvar);
    with:
        if (symvar == 7) d = 2.5; else d = 0.0;

    So, to reconstruct the original input:
    - If the transformed input sets s[0] to '7' (0x37), then in the original code, s[0] must also be '7'.
    - For all other values, keep as is.

    Only s[0] is relevant (since symvar = s[0] - 48).

    This function leaves all other bytes as is.

    Args:
        inputs: dict mapping variable names to list of bytes.

    Returns:
        dict with remapped inputs.
    """
    outputs = dict(inputs)  # shallow copy

    if "s" in inputs:
        s_bytes = list(inputs["s"])
        if len(s_bytes) >= 1:
            # symvar = s[0] - 48
            # In transformed code, symvar is directly compared to 7.
            # To trigger the same path, s[0] should be 55 ('7') for the true branch.
            # For other values, keep as is.
            # However, if s[0] is not in the printable ASCII range, leave as is.
            # (We do not invert any math here, as the transformation is a direct mapping.)

            # No remapping is needed, because the transformation is just a direct check on symvar.
            # However, if the transformed test case set s[0] to a value that would NOT be valid in the original code
            # (e.g., outside ASCII '0'..'9'), we should map it to a corresponding valid ASCII digit.

            # But since symvar = s[0] - 48, and symvar must be > 0, so s[0] > 48 ('0')
            # For symvar == 7, s[0] == 55 ('7')

            # So, we ensure s[0] is set to 55 if symvar==7 in the test case.
            symvar = s_bytes[0] - 48
            if symvar == 7:
                s_bytes[0] = 29  # ASCII '7'
            # else: leave as is

        outputs["s"] = s_bytes

    return outputs
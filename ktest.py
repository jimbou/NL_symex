import struct
import io
import string

# Drop in this class (from your ktest-tool source)
# or import it if you put it in ktest_tool.py

class KTest:
    valid_chars = string.digits + string.ascii_letters + string.punctuation + ' '

    @staticmethod
    def fromfile(path):
        with open(path, 'rb') as f:
            hdr = f.read(5)
            if len(hdr) != 5 or (hdr != b'KTEST' and hdr != b'BOUT\n'):
                raise ValueError('unrecognized file')
            version, = struct.unpack('>i', f.read(4))
            if version > 3:
                raise ValueError('unsupported version')

            numArgs, = struct.unpack('>i', f.read(4))
            args = [f.read(struct.unpack('>i', f.read(4))[0]).decode('ascii') for _ in range(numArgs)]

            if version >= 2:
                symArgvs, = struct.unpack('>i', f.read(4))
                symArgvLen, = struct.unpack('>i', f.read(4))
            else:
                symArgvs = 0
                symArgvLen = 0

            numObjects, = struct.unpack('>i', f.read(4))
            objects = []
            for _ in range(numObjects):
                name_len, = struct.unpack('>i', f.read(4))
                name = f.read(name_len).decode('utf-8')
                size, = struct.unpack('>i', f.read(4))
                value = f.read(size)
                objects.append((name, value))

            return KTest(version, path, args, symArgvs, symArgvLen, objects)

    def __init__(self, version, path, args, symArgvs, symArgvLen, objects):
        self.version = version
        self.path = path
        self.symArgvs = symArgvs
        self.symArgvLen = symArgvLen
        self.args = args
        self.objects = objects

import struct

def interpret_bytes(name, value_bytes):
    """
    Return a dict with different interpretations of the input bytes.
    """
    size = len(value_bytes)
    hex_repr = value_bytes.hex()
    text_repr = value_bytes.decode('ascii', errors='replace')

    interpretations = {
        "name": name,
        "size": size,
        "bytes": list(value_bytes),
        "hex": hex_repr,
        "text": ''.join(c if 32 <= ord(c) < 127 else '.' for c in text_repr)
    }

    # Try integer interpretations
    for n, fmt in [(1, 'b'), (2, 'h'), (4, 'i'), (8, 'q')]:
        if size == n:
            interpretations["int"] = struct.unpack(fmt, value_bytes)[0]
            interpretations["uint"] = struct.unpack(fmt.upper(), value_bytes)[0]
            break

    return interpretations



def format_ktest_as_string(ktest_info):
    sio = io.StringIO()
    objects = ktest_info["objects"]
    args = ktest_info["args"]
    path = ktest_info.get("path", "<unknown>")
    width = len(str(len(objects) - 1))  # for object number alignment

    # Header
    print(f"ktest file : '{path}'", file=sio)
    print(f"args       : {args}", file=sio)
    print(f"num objects: {len(objects)}", file=sio)

    # Object info
    for i, obj in enumerate(objects):
        name = obj["name"]
        size = obj["size"]
        data = bytes(obj["bytes"])
        hex_repr = obj["hex"]
        text_repr = obj["text"]

        print(f"object {i:{width}}: name: '{name}'", file=sio)
        print(f"object {i:{width}}: size: {size}", file=sio)
        print(f"object {i:{width}}: data: {data}", file=sio)
        print(f"object {i:{width}}: hex : 0x{hex_repr}", file=sio)

        if "int" in obj and "uint" in obj:
            print(f"object {i:{width}}: int : {obj['int']}", file=sio)
            print(f"object {i:{width}}: uint: {obj['uint']}", file=sio)

        print(f"object {i:{width}}: text: {text_repr}", file=sio)

    return sio.getvalue()

def read_ktest_structured(path):
    """
    Return a list of interpreted ktest objects with int/uint/hex/text views.
    """
    kt = KTest.fromfile(path)
    object_views = [interpret_bytes(name, value) for name, value in kt.objects]
    return {
        "version": kt.version,
        "args": kt.args,
        "symArgvLen": kt.symArgvLen,
        "symArgvs": kt.symArgvs,
        "objects": object_views
    }


def write_ktest_file(base_ktest_path: str, new_inputs: dict[str, list[int]], output_path: str):
    """
    Writes a new .ktest file using the original structure, but updates the object values
    with remapped inputs (from remap_testcase).
    """
    # Load original .ktest file
    ktest = KTest.fromfile(base_ktest_path)

    with open(output_path, "wb") as f:
        f.write(b'KTEST')
        f.write(struct.pack(">i", ktest.version))

        # Write args
        f.write(struct.pack(">i", len(ktest.args)))
        for arg in ktest.args:
            arg_bytes = arg.encode("ascii")
            f.write(struct.pack(">i", len(arg_bytes)))
            f.write(arg_bytes)

        # Write symbolic argv info (even if unused)
        if ktest.version >= 2:
            f.write(struct.pack(">i", ktest.symArgvs))
            f.write(struct.pack(">i", ktest.symArgvLen))

        # Write objects
        f.write(struct.pack(">i", len(ktest.objects)))
        for name, old_bytes in ktest.objects:
            new_bytes = new_inputs.get(name, list(old_bytes))
            name_bytes = name.encode("utf-8")
            f.write(struct.pack(">i", len(name_bytes)))
            f.write(name_bytes)
            f.write(struct.pack(">i", len(new_bytes)))
            f.write(bytes(new_bytes))

# def read_ktest_structured(path):
#     """
#     Read a .ktest file using KLEE's official logic and return a structured dict.
#     """
#     kt = KTest.fromfile(path)
#     inputs = {}
#     for name, value in kt.objects:
#         # Value is bytes; convert to list of ints for compatibility
#         inputs[name] = list(value)
#     return {
#         "version": kt.version,
#         "args": kt.args,
#         "symArgvLen": kt.symArgvLen,
#         "symArgvs": kt.symArgvs,
#         "inputs": inputs
#     }

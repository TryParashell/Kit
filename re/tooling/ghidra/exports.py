import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pemap import sections


def rva_to_file(secs, rva):
    for name, vaddr, vsize, raddr, rsize in secs:
        if vaddr <= rva < vaddr + max(vsize, rsize):
            return raddr + (rva - vaddr)
    return None


def exports(path):
    blob = path.read_bytes()
    image_base, secs = sections(blob)
    pe = struct.unpack_from("<I", blob, 0x3C)[0]
    magic = struct.unpack_from("<H", blob, pe + 24)[0]
    dd = pe + 24 + (112 if magic == 0x20B else 96)
    edir_rva, edir_size = struct.unpack_from("<II", blob, dd)
    base = rva_to_file(secs, edir_rva)
    count_funcs, count_names = struct.unpack_from("<II", blob, base + 20)
    addr_funcs, addr_names, addr_ords = struct.unpack_from("<III", blob, base + 28)
    fbase = rva_to_file(secs, addr_funcs)
    nbase = rva_to_file(secs, addr_names)
    obase = rva_to_file(secs, addr_ords)
    out = []
    for i in range(count_names):
        name_rva = struct.unpack_from("<I", blob, nbase + 4 * i)[0]
        noff = rva_to_file(secs, name_rva)
        end = blob.index(b"\x00", noff)
        name = blob[noff:end].decode("latin1")
        index = struct.unpack_from("<H", blob, obase + 2 * i)[0]
        func_rva = struct.unpack_from("<I", blob, fbase + 4 * index)[0]
        out.append((name, func_rva, image_base + func_rva))
    return image_base, out


def main():
    path = pathlib.Path(sys.argv[1])
    keys = sys.argv[2:]
    image_base, table = exports(path)
    print(f"image_base 0x{image_base:x} exports {len(table)}")
    for name, rva, va in table:
        if keys and not any(k in name for k in keys):
            continue
        print(f"  0x{va:x} rva=0x{rva:x} {name}")


if __name__ == "__main__":
    main()

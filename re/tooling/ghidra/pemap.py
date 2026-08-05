import pathlib
import struct
import sys


def sections(blob):
    pe = struct.unpack_from("<I", blob, 0x3C)[0]
    machine, nsec = struct.unpack_from("<HH", blob, pe + 4)
    opt_size = struct.unpack_from("<H", blob, pe + 20)[0]
    magic = struct.unpack_from("<H", blob, pe + 24)[0]
    if magic == 0x20B:
        image_base = struct.unpack_from("<Q", blob, pe + 24 + 24)[0]
    else:
        image_base = struct.unpack_from("<I", blob, pe + 24 + 28)[0]
    table = pe + 24 + opt_size
    out = []
    for i in range(nsec):
        base = table + 40 * i
        name = blob[base : base + 8].rstrip(b"\x00").decode("latin1")
        vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", blob, base + 8)
        out.append((name, vaddr, vsize, raddr, rsize))
    return image_base, out


def main():
    path = pathlib.Path(sys.argv[1])
    blob = path.read_bytes()
    image_base, secs = sections(blob)
    print(f"image_base 0x{image_base:x}")
    for name, vaddr, vsize, raddr, rsize in secs:
        print(
            f"  {name:9s} rva=0x{vaddr:08x} vsize=0x{vsize:08x} raw=0x{raddr:08x} rsize=0x{rsize:08x}"
        )
    for arg in sys.argv[2:]:
        off = int(arg, 0)
        for name, vaddr, vsize, raddr, rsize in secs:
            if raddr <= off < raddr + rsize:
                rva = vaddr + (off - raddr)
                print(
                    f"file 0x{off:x} -> section {name} rva 0x{rva:x} va 0x{image_base + rva:x}"
                )
                break
        else:
            print(f"file 0x{off:x} -> not in any section raw range")


if __name__ == "__main__":
    main()

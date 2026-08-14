import pathlib
import sys


def main():
    path = pathlib.Path(sys.argv[1])
    start = int(sys.argv[2], 0)
    length = int(sys.argv[3], 0)
    blob = path.read_bytes()
    lo = max(0, start)
    hi = min(len(blob), start + length)
    for off in range(lo, hi, 16):
        chunk = blob[off : off + 16]
        hexpart = " ".join(f"{b:02x}" for b in chunk)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{off:08x}  {hexpart:<47s}  {text}")


if __name__ == "__main__":
    main()

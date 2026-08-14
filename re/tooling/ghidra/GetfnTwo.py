import pathlib
import re
import sys

OUT = pathlib.Path(__file__).resolve().parents[3] / ".rescratch/ghidra/out"
KEEP = re.compile(
    r"AR_get_|AR_put_|operator>>|operator<<|ReadObject|WriteObject|IsStoring"
    r"|hasCondition|Serialize|getCurrentFileVerion|0x780|goto|LAB_|if \(|\} else"
    r"|while|for \(|su_DBKey|CStringT<wchar_t.*\"|code \*\*\)\(\*"
)


def blocks(path):
    text = path.read_text(errors="replace").splitlines()
    starts = [i for i, line in enumerate(text) if line.startswith("=== FUNCTION")]
    starts.append(len(text))
    for pos in range(len(starts) - 1):
        head = starts[pos]
        body = text[head : starts[pos + 1]]
        address = ""
        for line in body[:5]:
            if line.startswith("=== ADDRESS "):
                address = line.split()[-1]
        yield address, body[0], body


def main():
    path = OUT / sys.argv[1]
    wanted = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "skeleton"
    for address, header, body in blocks(path):
        if wanted.lower() not in address.lower() and wanted not in header:
            continue
        print(f"##### {header} @ {address} lines={len(body)}")
        for index, line in enumerate(body):
            stripped = line.strip()
            if mode == "full" or KEEP.search(stripped):
                print(f"{index:5d} {stripped[:160]}")
        print()


if __name__ == "__main__":
    main()

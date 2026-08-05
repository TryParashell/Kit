import pathlib
import sys


def blocks(path):
    text = pathlib.Path(path).read_text(errors="replace")
    parts = text.split("\n=== FUNCTION ")
    for part in parts[1:]:
        head, _, body = part.partition("\n")
        yield head.strip(), "=== FUNCTION " + head + "\n" + body


def main():
    path = sys.argv[1]
    pats = sys.argv[2:]
    for name, body in blocks(path):
        if not pats or any(p in name for p in pats):
            print(body)
            print("-" * 78)


if __name__ == "__main__":
    main()

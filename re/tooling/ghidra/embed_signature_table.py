import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
GENERATOR = pathlib.Path(__file__).resolve().parent / "gen_signature_table.py"
FRAGMENT = ROOT / ".rescratch/ghidra/out/signature_table_b85.py"
TARGET = ROOT / "src/convert/adapters/solidworks/container.py"
PLACEHOLDER = '_SIGNATURE_TABLE_B85 = "@@SIGNATURE_TABLE_B85@@"\n'
MARKER = "_SIGNATURE_TABLE_B85 = ("


def main() -> int:
    subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=str(ROOT),
        check=False,
    )
    fragment = FRAGMENT.read_text(encoding="utf-8")
    text = TARGET.read_text(encoding="utf-8")
    if PLACEHOLDER in text:
        TARGET.write_text(text.replace(PLACEHOLDER, fragment), encoding="utf-8")
        print("embedded signature table into container.py")
        return 0
    start = text.find(MARKER)
    if start < 0:
        print("no signature table placeholder or literal found in container.py")
        return 1
    end = text.find("\n)\n", start)
    if end < 0:
        print("existing signature table literal is malformed")
        return 1
    TARGET.write_text(text[:start] + fragment + text[end + 3 :], encoding="utf-8")
    print("replaced signature table in container.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

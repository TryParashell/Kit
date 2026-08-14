import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
PATH = ROOT / ".rescratch/ghidra/out/sldmodu_vtables.txt"


def tables():
    cur = None
    rows = []
    for line in PATH.read_text(errors="replace").splitlines():
        if line.startswith("=== VFTABLE "):
            if cur is not None:
                yield cur, rows
            body = line[len("=== VFTABLE ") :]
            name, _, addr = body.rpartition(" @ ")
            cur = (name.strip(), addr.strip())
            rows = []
        elif cur is not None and line.startswith("  "):
            parts = line.split()
            if len(parts) >= 3:
                rows.append((int(parts[0]), parts[1], parts[2]))
    if cur is not None:
        yield cur, rows


def main():
    wanted = sys.argv[1:]
    mode_slot = None
    if wanted and wanted[0].startswith("slot="):
        mode_slot = int(wanted[0].split("=", 1)[1])
        wanted = wanted[1:]
    for (name, addr), rows in tables():
        if wanted and name not in wanted:
            continue
        if mode_slot is not None:
            hit = [r for r in rows if r[0] == mode_slot]
            if hit:
                print(f"{name:34s} @{addr} slot{mode_slot} {hit[0][1]} {hit[0][2]}")
            continue
        print(f"=== {name} @ {addr}  slots={len(rows)}")
        for slot, target, fn in rows:
            print(f"  {slot:4d} {target} {fn}")


if __name__ == "__main__":
    main()

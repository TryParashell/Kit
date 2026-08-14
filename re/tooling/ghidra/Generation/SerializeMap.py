import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
DUMPS = ROOT / ".rescratch/ghidra/out"
OUT = ROOT / "re/data"
VT = DUMPS / "sldmodu_vtslots.txt"
SLOT = 5


def tables(path):
    cur = None
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("=== VFTABLE "):
            if cur is not None:
                yield cur, rows
            body = line[len("=== VFTABLE ") :]
            name, _, addr = body.rpartition(" @ ")
            cur = (name.strip(), addr.strip())
            rows = []
        elif line.startswith("VT "):
            if cur is not None:
                yield cur, rows
            body = line[3:]
            head, _, rest = body.partition(" @ ")
            addr = rest.split(" ")[0]
            cur = (head.strip(), addr.strip())
            rows = []
        elif cur is not None and (line.startswith("  ")):
            parts = line.replace("|", " ").split()
            if len(parts) >= 3 and parts[0].isdigit():
                rows.append((int(parts[0]), parts[1], parts[2]))
    if cur is not None:
        yield cur, rows


def build(path=VT, slot=SLOT):
    best = {}
    for (name, addr), rows in tables(path):
        if not rows:
            continue
        if rows[0][2].split("::")[-1] != "GetRuntimeClass":
            continue
        hit = [r for r in rows if r[0] == slot]
        if not hit:
            continue
        target, fn = hit[0][1], hit[0][2]
        prev = best.get(name)
        if prev is None or len(rows) > prev[2]:
            best[name] = (target, fn, len(rows))
    return best


def main():
    path = VT
    if len(sys.argv) > 1:
        path = pathlib.Path(sys.argv[1])
    best = build(path)
    OUT.mkdir(parents=True, exist_ok=True)
    doc = {
        name: {"serialize_addr": v[0], "serialize_name": v[1], "vtable_slots": v[2]}
        for name, v in sorted(best.items())
    }
    (OUT / "SerializeMap.json").write_text(json.dumps(doc, indent=1))
    print("classes", len(doc))
    shared = {}
    for name, v in doc.items():
        shared.setdefault(v["serialize_addr"], []).append(name)
    print("distinct serialize functions", len(shared))
    for key in sys.argv[2:]:
        for name, v in doc.items():
            if key.lower() in name.lower():
                print(
                    f"{name:34s} {v['serialize_addr']} {v['serialize_name']} "
                    f"shared_with={len(shared[v['serialize_addr']])}"
                )


if __name__ == "__main__":
    main()

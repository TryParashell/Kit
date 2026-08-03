from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
base = HERE.parents[1]

name_types: dict[str, Counter] = defaultdict(Counter)
for r in rows:
    for s in r["streams"]:
        name_types[s["name"]][s["type_id"]] += 1

print("=== deliverable 3: stream name -> type_id ===")
print(f"{'stream name':46} {'files':>5}  type_id(s) with counts")
for name in sorted(name_types):
    c = name_types[name]
    tids = "  ".join(f"{t:#010x}x{n}" for t, n in sorted(c.items()))
    print(f"{name:46} {sum(c.values()):>5}  {tids}")

print(f"\ndistinct type_id values overall: ", end="")
allt = Counter()
for c in name_types.values():
    allt.update(c)
print({f"{k:#010x}": v for k, v in sorted(allt.items())})
multi = {n: sorted(c) for n, c in name_types.items() if len(c) > 1}
print(f"stream names with >1 type_id: {len(multi)}")
for n, t in multi.items():
    print(f"  {n}: {[f'{x:#010x}' for x in t]}")

print("\n=== deliverable 4: stream-name sets ===")
setsig: dict[frozenset, list[str]] = defaultdict(list)
for r in rows:
    setsig[frozenset(s["name"] for s in r["streams"])].append(
        str(Path(r["path"]).relative_to(base))
    )
print(f"distinct stream-name sets: {len(setsig)}")
universe = sorted({n for k in setsig for n in k})
print(f"union of all stream names: {len(universe)}")
groups = sorted(setsig.items(), key=lambda kv: -len(kv[1]))
for i, (k, files) in enumerate(groups):
    print(f"\n  group {i}: {len(files)} files, {len(k)} streams")
    print(f"    e.g. {files[0]}")
    if i:
        b = groups[0][0]
        print(f"    vs group0  extra: {sorted(k - b)}")
        print(f"    vs group0  missing: {sorted(b - k)}")

print("\n=== _MO_VERSION_* streams per file ===")
mo: dict[str, list[str]] = defaultdict(list)
for r in rows:
    names = sorted(s["name"] for s in r["streams"] if "_MO_VERSION" in s["name"])
    mo["|".join(names)].append(str(Path(r["path"]).relative_to(base)))
for k, v in sorted(mo.items()):
    print(f"  {k or '(none)'}  -> {len(v)} files")
    for f in v[:3]:
        print(f"      {f}")

print("\n=== deliverable 5: format_version distribution ===")
print(Counter(r["format_version"] for r in rows))
print("file_id vs format_version: ", Counter(r["format_version"] for r in rows))

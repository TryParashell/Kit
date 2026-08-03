from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
from convert.adapters.solidworks.container import SldprtArchive  # noqa: E402

rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
base = HERE.parents[1]
combos = Counter()
detail = []
for r in rows:
    a = SldprtArchive.open(r["path"])
    app = a.get("docProps/app.xml") or b""
    txt = app.decode("utf-8", "replace")
    ver = re.search(r"<AppVersion>([^<]*)</AppVersion>", txt)
    name = re.search(r"<Application>([^<]*)</Application>", txt)
    mo = sorted(n for n in a.streams if "_MO_VERSION" in n)
    dl = sorted(n for n in a.streams if "_DL_VERSION" in n)
    key = (
        name.group(1) if name else "?",
        ver.group(1) if ver else "?",
        mo[0].split("/")[0] if mo else "-",
        dl[0].split("/")[0] if dl else "-",
        r["format_version"],
    )
    combos[key] += 1
    detail.append((str(Path(r["path"]).relative_to(base)), key))

print(f"{'Application':22} {'AppVersion':12} {'_MO_VERSION':20} {'_DL_VERSION':20} fmt  files")
for k, n in sorted(combos.items()):
    print(f"{k[0]:22} {k[1]:12} {k[2]:20} {k[3]:20} {k[4]:<4} {n}")
print()
for p, k in detail:
    if k[2] != "_MO_VERSION_13000":
        print(f"  outlier: {p} -> {k}")

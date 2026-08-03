import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / "scan.json").read_text(encoding="utf-8"))
base = HERE.parents[1]

print(
    f"{'path':62} {'fid':>10} {'v':>2} {'n':>4} {'local':>9} {'central':>9} {'end':>9} {'cmark':>5}"
)
for r in rows:
    p = str(Path(r["path"]).relative_to(base))
    if len(p) > 62:
        p = "..." + p[-59:]
    print(
        f"{p:62} {r['file_id']:#010x} {r['format_version']:>2} {r['stream_count']:>4} "
        f"{','.join(r['local_sigs']):>9} {','.join(r['central_sigs']):>9} "
        f"{str(r['end_sig']):>9} {r['central_marker_count']:>5}"
    )

print()
print("distinct format_version:", sorted({r["format_version"] for r in rows}))
print("distinct file_id count:", len({r["file_id"] for r in rows}))
print(
    "files with >1 local sig:",
    [r["path"] for r in rows if len(r["local_sigs"]) != 1],
)
print(
    "files with >1 central sig:",
    [r["path"] for r in rows if len(r["central_sigs"]) != 1],
)
print("files missing end sig:", [r["path"] for r in rows if not r["end_sig"]])
print(
    "distinct local prefix bytes:",
    sorted({x for r in rows for x in r["prefix_at_local"]}),
)
print(
    "distinct central prefix bytes:",
    sorted({x for r in rows for x in r["central_prefix_at"]}),
)
print(
    "central_marker_count == stream_count for all:",
    all(r["central_marker_count"] == r["stream_count"] for r in rows),
)

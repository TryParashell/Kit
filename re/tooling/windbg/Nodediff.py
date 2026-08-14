from __future__ import annotations

import difflib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parents[2] / ".rescratch"
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import blocks as blockslib
import model as modellib

OUT = SCRATCH / "trace" / "out"


def key(node: modellib.Node) -> tuple[str, str]:
    if node.kind == "definition":
        return "class", node.class_name
    if node.kind == "classref":
        return "instance", node.class_name
    return node.kind, ""


def align(models: list[tuple[str, modellib.Model]]) -> list[list[int | None]]:
    reference = models[-1][1]
    rows: list[list[int | None]] = [[None] * len(models) for _ in reference.nodes]
    for column, (_label, model) in enumerate(models):
        matcher = difflib.SequenceMatcher(
            a=[key(node) for node in model.nodes],
            b=[key(node) for node in reference.nodes],
            autojunk=False,
        )
        for alow, blow, size in matcher.get_matching_blocks():
            for step in range(size):
                rows[blow + step][column] = alow + step
    return rows


def main() -> int:
    arguments = sys.argv[1:]
    stream = arguments[0]
    models: list[tuple[str, modellib.Model]] = []
    for position in range(1, len(arguments), 3):
        label = arguments[position]
        part = Path(arguments[position + 1]).resolve()
        log = Path(arguments[position + 2]).resolve()
        models.append((label, blockslib.load_model(part, log, stream)))
    rows = align(models)
    reference = models[-1][1]
    labels = [label for label, _ in models]
    print(f"stream {stream}")
    print("ref  kind        class                          " + "  ".join(labels))
    payload: list[dict[str, object]] = []
    for position, row in enumerate(rows):
        node = reference.nodes[position]
        sizes: list[str] = []
        lengths: list[int | None] = []
        for column, (_label, model) in enumerate(models):
            source = row[column]
            if source is None:
                sizes.append("   -")
                lengths.append(None)
            else:
                sizes.append(f"{len(model.nodes[source].body):4d}")
                lengths.append(len(model.nodes[source].body))
        flag = ""
        present = [value for value in lengths if value is not None]
        if len(present) != len(models):
            flag = " NEW"
        elif len(set(present)) > 1:
            flag = " GROWS"
        print(
            f"{position:3d}  {node.kind:11s} {(node.class_name or '-'):30s} "
            + " ".join(sizes)
            + flag
        )
        payload.append(
            {
                "node": position,
                "kind": node.kind,
                "class_name": node.class_name,
                "sources": row,
                "body_lengths": lengths,
                "state": flag.strip() or "same",
            }
        )
    OUT.mkdir(parents=True, exist_ok=True)
    tag = stream.replace("/", "_").replace("-", "_")
    (OUT / f"nodediff_{tag}.json").write_text(
        json.dumps({"stream": stream, "labels": labels, "rows": payload}, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

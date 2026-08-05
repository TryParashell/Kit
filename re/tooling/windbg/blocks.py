from __future__ import annotations

from dataclasses import dataclass
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

import model as modellib
import segment as segmentlib

OUT = SCRATCH / "trace" / "out"


class BlockError(RuntimeError):
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Insertion:
    low: int
    high: int

    @property
    def size(self) -> int:
        return self.high - self.low


def signature(node: modellib.Node) -> tuple[str, str, int]:
    if node.kind == "definition":
        return "class", node.class_name, len(node.body)
    if node.kind == "classref":
        return "instance", node.class_name, len(node.body)
    return node.kind, "", len(node.body)


def signatures(model: modellib.Model) -> list[tuple[str, str, int]]:
    return [signature(node) for node in model.nodes]


def insertions(
    smaller: modellib.Model, larger: modellib.Model
) -> tuple[Insertion, ...]:
    left = signatures(smaller)
    right = signatures(larger)
    matcher = difflib.SequenceMatcher(a=left, b=right, autojunk=False)
    result: list[Insertion] = []
    for tag, alow, ahigh, blow, bhigh in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            result.append(Insertion(blow, bhigh))
            continue
        if tag == "replace" and bhigh - blow > ahigh - alow:
            result.append(Insertion(blow + (ahigh - alow), bhigh))
            continue
        if tag != "replace":
            raise BlockError(f"unexpected opcode {tag} at [{blow},{bhigh})")
        result.append(Insertion(blow, bhigh))
    return tuple(result)


def load_model(part: Path, log: Path, stream: str) -> modellib.Model:
    blob, segments = segmentlib.load(part, log, stream=stream)
    return modellib.parse(blob, segments)


def describe(model: modellib.Model, block: Insertion) -> list[str]:
    return [
        f"{position}:{model.nodes[position].kind}"
        f":{model.nodes[position].class_name or '-'}"
        f":{len(model.nodes[position].body)}"
        for position in range(block.low, block.high)
    ]


def compare(stream: str, rows: list[tuple[str, Path, Path]]) -> dict[str, object]:
    models = [(label, load_model(part, log, stream)) for label, part, log in rows]
    payload: dict[str, object] = {
        "stream": stream,
        "parts": [
            {"label": label, "nodes": len(model.nodes), "base": model.base}
            for label, model in models
        ],
        "steps": [],
    }
    steps: list[dict[str, object]] = []
    for (left_label, left), (right_label, right) in zip(models, models[1:]):
        found = insertions(left, right)
        steps.append(
            {
                "from": left_label,
                "to": right_label,
                "insertions": [
                    {
                        "low": block.low,
                        "high": block.high,
                        "size": block.size,
                        "nodes": describe(right, block),
                    }
                    for block in found
                ],
                "inserted_nodes": sum(block.size for block in found),
            }
        )
    payload["steps"] = steps
    return payload


def main() -> int:
    arguments = sys.argv[1:]
    if len(arguments) < 4 or (len(arguments) - 1) % 3:
        raise SystemExit("usage: blocks.py <stream> <label> <part> <log> [...]")
    stream = arguments[0]
    rows: list[tuple[str, Path, Path]] = []
    for position in range(1, len(arguments), 3):
        rows.append(
            (
                arguments[position],
                Path(arguments[position + 1]).resolve(),
                Path(arguments[position + 2]).resolve(),
            )
        )
    payload = compare(stream, rows)
    OUT.mkdir(parents=True, exist_ok=True)
    tag = stream.replace("/", "_").replace("-", "_")
    (OUT / f"blocks_{tag}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(f"stream {stream}")
    for row in payload["parts"]:
        print(f"  {row['label']:14s} nodes={row['nodes']:5d} base={row['base']}")
    for step in payload["steps"]:
        print(
            f"  {step['from']} -> {step['to']} inserted={step['inserted_nodes']} "
            f"blocks={len(step['insertions'])}"
        )
        for block in step["insertions"]:
            print(f"    [{block['low']},{block['high']}) size={block['size']}")
            print("      " + " ".join(block["nodes"][:24]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

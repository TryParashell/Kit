from __future__ import annotations

import argparse
import json
import re
from typing import Dict, List, Optional, Tuple

SCALAR_WIDTH = {
    "uchar": 1,
    "char": 1,
    "ushort": 2,
    "short": 2,
    "long": 4,
    "ulong": 4,
    "int": 4,
    "uint": 4,
    "float": 4,
    "double": 8,
    "__int64": 8,
    "int64": 8,
}

BLOCK_START_RE = re.compile(r"^=== FUNCTION (.+)$")
ADDRESS_RE = re.compile(r"^=== ADDRESS ([0-9a-fA-F]+)$")
GET_RE = re.compile(r"su_CArchive::AR_get_([A-Za-z0-9_]+)\s*\(")
PUT_RE = re.compile(r"su_CArchive::AR_put_([A-Za-z0-9_]+)\s*\(")
DECL_RE = re.compile(
    r"^\s*(?:void|undefined\d*|int|uint|longlong)\s+[A-Za-z_][A-Za-z0-9_:<>,\s]*?"
    r"\(\s*([A-Za-z_][A-Za-z0-9_:<>,\s]*?)\s*(\*+)?\s*(this|param_1)\s*[,)]"
)
POINTER_SCALE = {
    "longlong": 8,
    "ulonglong": 8,
    "double": 8,
    "int64": 8,
    "__int64": 8,
    "int": 4,
    "uint": 4,
    "long": 4,
    "ulong": 4,
    "float": 4,
    "short": 2,
    "ushort": 2,
    "wchar_t": 2,
}
READ_OBJECT_RE = re.compile(
    r"(?:su_CArchive|su_CDBArchive)::ReadObject\s*\([^;]*?class([A-Za-z0-9_]+)"
)
GLOBAL_READ_RE = re.compile(r"(?<!su_CArchive)(?<!su_CDBArchive)::operator>>\s*\(")
CSTRING_RE = re.compile(r"CStringT<wchar_t")
SLOT5_RE = re.compile(
    r"\(\*\*\(code \*\*\)\(\*\(longlong \*\)\((?:this|param_1)\s*\+\s*"
    r"(0x[0-9a-fA-F]+|\d+)\)\s*\+\s*0x28\)\)"
)
STRING_RE = re.compile(r'"([^"\\]{1,64})"')
BASE_CALL_RE = re.compile(
    r"\b((?:FUN_[0-9a-f]+)|(?:[A-Za-z_][A-Za-z0-9_]*::Serialize))"
    r"\s*\(\s*(?:\([A-Za-z0-9_:<>,\s]*\*+\)\s*)?(?:this|param_1)\s*,\s*"
    r"(?:param_1|param_2)\s*\)"
)
BASE_SERIALIZE_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)::Serialize\s*\(")
DBKEY_NAME_RE = re.compile(r'CStringT\s*\(\s*[^,]+,\s*"([^"]+)"')
READ_COUNT_RE = re.compile(r"su_CArchive::ReadCount\s*\(")
VERSION_CMP_RE = re.compile(
    r"(0x[0-9a-fA-F]+|\d+)\s*<\s*(?:\(int\))?\s*([iu]Var\d+)"
    r"|([iu]Var\d+)\s*<\s*(0x[0-9a-fA-F]+|\d+)"
)
HAS_CONDITION_RE = re.compile(r"hasCondition\s*\([^,]+,\s*(0x[0-9a-fA-F]+|\d+)\s*\)")


def parse_int(text: str) -> int:
    return int(text, 16) if text.lower().startswith("0x") else int(text)


def strip_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


class Dump:
    def __init__(self, paths: List[str]) -> None:
        self.by_address: Dict[str, dict] = {}
        for path in paths:
            raw = open(path, encoding="utf-8", errors="replace").read()
            lines = raw.splitlines()
            starts = [i for i, line in enumerate(lines) if line.startswith("=== FUNCTION ")]
            starts.append(len(lines))
            for k in range(len(starts) - 1):
                chunk = lines[starts[k] : starts[k + 1]]
                name = BLOCK_START_RE.match(chunk[0]).group(1).strip()
                address = ""
                for line in chunk[:6]:
                    match = ADDRESS_RE.match(line)
                    if match:
                        address = match.group(1).lower()
                        break
                if not address:
                    continue
                record = {
                    "name": name,
                    "address": address,
                    "source": "%s:%d" % (path.replace("\\", "/").rsplit("/", 1)[-1], starts[k] + 1),
                    "body": "\n".join(chunk),
                }
                self.by_address.setdefault(address, record)

        self.by_name: Dict[str, dict] = {}
        for record in self.by_address.values():
            self.by_name.setdefault(record["name"], record)

    def get(self, address: str) -> Optional[dict]:
        return self.by_address.get(address.lower())

    def resolve(self, token: str) -> Optional[dict]:
        if token.startswith("FUN_"):
            return self.get(token[4:])
        return self.by_name.get(token)


def condition_stack(body: str) -> List[Tuple[int, str]]:
    text = strip_comments(body)
    lines = text.splitlines()
    stack: List[Tuple[int, str]] = []
    result: List[Tuple[int, str]] = []
    depth = 0
    pending: Optional[str] = None
    for line in lines:
        stripped = line.strip()
        match = re.match(r"^(?:\}\s*else\s+)?if\s*\((.*)$", stripped)
        if match:
            pending = match.group(1)
        elif stripped.startswith("} else"):
            pending = "!previous"
        opens = line.count("{")
        closes = line.count("}")
        for _ in range(closes):
            if stack and stack[-1][0] == depth:
                stack.pop()
            depth = max(0, depth - 1)
        for _ in range(opens):
            depth += 1
            stack.append((depth, pending or ""))
            pending = None
        result.append((depth, " && ".join(c for _, c in stack if c)))
    return result


def version_gates(condition: str) -> List[str]:
    gates: List[str] = []
    for match in VERSION_CMP_RE.finditer(condition):
        if match.group(1):
            gates.append("version > %d" % parse_int(match.group(1)))
        elif match.group(4):
            gates.append("version < %d" % parse_int(match.group(4)))
    for match in HAS_CONDITION_RE.finditer(condition):
        gates.append("hasCondition(0x%x)" % parse_int(match.group(1)))
    return gates


def object_param(body: str) -> Tuple[str, int]:
    for line in strip_comments(body).splitlines():
        match = DECL_RE.match(line)
        if match:
            base = (match.group(1) or "").strip().split()[-1]
            stars = match.group(2) or ""
            name = match.group(3)
            if len(stars) >= 2:
                return name, 8
            return name, POINTER_SCALE.get(base, 1)
    return "param_1", 1


def struct_offsets(line: str, holder: str, scale: int) -> List[int]:
    found: List[int] = []
    pattern = re.compile(
        r"\(\s*%s\s*\+\s*(?:\(longlong\)[A-Za-z0-9_]+\s*\*\s*\d+\s*\+\s*)?"
        r"(0x[0-9a-fA-F]+|\d+)\s*\)" % re.escape(holder)
    )
    for match in pattern.finditer(line):
        found.append(parse_int(match.group(1)) * scale)
    subscript = re.compile(r"%s\[\s*(0x[0-9a-fA-F]+|\d+)\s*\]" % re.escape(holder))
    for match in subscript.finditer(line):
        found.append(parse_int(match.group(1)) * scale)
    if not found and re.search(r"\)\s*%s\s*[,)]" % re.escape(holder), line):
        found.append(0)
    return found


def extract_ops(record: dict) -> dict:
    body = record["body"]
    text = strip_comments(body)
    lines = text.splitlines()
    conditions = condition_stack(body)
    holder, scale = object_param(body)
    reads: List[dict] = []
    writes: List[dict] = []
    bases: List[str] = []
    dbkeys: List[dict] = []
    pending_name: Optional[str] = None
    pending_key = False
    for i, line in enumerate(lines):
        depth, condition = conditions[i] if i < len(conditions) else (0, "")
        gates = version_gates(condition)
        offsets = struct_offsets(line, holder, scale)
        literal = STRING_RE.search(line)
        if literal and "Serialize" not in literal.group(1):
            pending_name = literal.group(1)
        for match in BASE_CALL_RE.finditer(line):
            bases.append(match.group(1))
        get_match = GET_RE.search(line)
        if get_match:
            kind = get_match.group(1)
            reads.append(
                {
                    "op": "AR_get_" + kind,
                    "width": SCALAR_WIDTH.get(kind, 0),
                    "type": kind,
                    "struct_offset": offsets[0] if offsets else None,
                    "gates": gates,
                    "condition": condition,
                    "line": i + 1,
                }
            )
            continue
        put_match = PUT_RE.search(line)
        if put_match:
            kind = put_match.group(1)
            entry = {
                "op": "AR_put_" + kind,
                "width": SCALAR_WIDTH.get(kind, 0),
                "type": kind,
                "struct_offset": offsets[0] if offsets else None,
                "gates": gates,
                "line": i + 1,
            }
            if kind == "su_DBKey":
                if pending_name:
                    dbkeys.append({"name": pending_name, "line": i + 1})
                    pending_key = True
                    pending_name = None
            elif pending_key and dbkeys:
                dbkeys[-1]["struct_offset"] = entry["struct_offset"]
                dbkeys[-1]["width"] = entry["width"]
                dbkeys[-1]["type"] = kind
                pending_key = False
            writes.append(entry)
            continue
        read_object = READ_OBJECT_RE.search(line)
        if read_object:
            reads.append(
                {
                    "op": "ReadObject",
                    "width": None,
                    "type": read_object.group(1),
                    "struct_offset": offsets[0] if offsets else None,
                    "gates": gates,
                    "condition": condition,
                    "line": i + 1,
                }
            )
            continue
        slot5 = SLOT5_RE.search(line)
        if slot5:
            reads.append(
                {
                    "op": "slot5_subrecord",
                    "width": None,
                    "type": "member",
                    "struct_offset": parse_int(slot5.group(1)),
                    "gates": gates,
                    "condition": condition,
                    "line": i + 1,
                }
            )
            continue
        if GLOBAL_READ_RE.search(line):
            reads.append(
                {
                    "op": "operator>>",
                    "width": None,
                    "type": "CString" if CSTRING_RE.search(line) else "object",
                    "struct_offset": offsets[0] if offsets else None,
                    "gates": gates,
                    "condition": condition,
                    "line": i + 1,
                }
            )
            continue
        if READ_COUNT_RE.search(line):
            reads.append(
                {
                    "op": "ReadCount",
                    "width": None,
                    "type": "count",
                    "struct_offset": None,
                    "gates": gates,
                    "condition": condition,
                    "line": i + 1,
                }
            )
    return {
        "function": record["name"],
        "address": "0x" + record["address"],
        "source": record["source"],
        "object_param": holder,
        "pointer_scale": scale,
        "bases": bases,
        "reads": reads,
        "writes": writes,
        "dbkeys": dbkeys,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dumps", nargs="+")
    parser.add_argument("--map", required=True)
    parser.add_argument("--classes", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    dump = Dump(args.dumps)
    serialize_map = json.load(open(args.map, encoding="utf-8"))
    classes = [
        line.strip()
        for line in open(args.classes, encoding="utf-8")
        if line.strip()
    ]
    payload: Dict[str, dict] = {}
    for name in classes:
        entry = serialize_map.get(name)
        if entry is None:
            payload[name] = {"status": "no_serialize_map_entry"}
            continue
        record = dump.get(entry["serialize_addr"])
        if record is None:
            payload[name] = {
                "status": "serialize_not_dumped",
                "serialize_address": "0x" + entry["serialize_addr"],
            }
            continue
        extracted = extract_ops(record)
        extracted["status"] = "ok"
        chain: List[dict] = []
        seen = {record["address"]}
        frontier = list(extracted["bases"])
        while frontier:
            token = frontier.pop(0)
            base = dump.resolve(token)
            if base is None:
                chain.append({"token": token, "status": "not_dumped"})
                continue
            if base["address"] in seen:
                continue
            seen.add(base["address"])
            info = extract_ops(base)
            info["token"] = token
            info["status"] = "ok"
            chain.append(info)
            frontier.extend(info["bases"])
        extracted["chain"] = chain
        payload[name] = extracted
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    ok = sum(1 for v in payload.values() if v.get("status") == "ok")
    print(
        "classes=%d extracted=%d missing=%d"
        % (len(payload), ok, len(payload) - ok)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

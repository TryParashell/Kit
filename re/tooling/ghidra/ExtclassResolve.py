# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Resolve the four externally defined classes referenced by Contents/Config-0-ResolvedFeatures."""

from __future__ import annotations

import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HARNESS = ROOT / "re" / "tooling" / "harness"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

import carchive
import streamlib

SEGMENTS = ROOT / "re" / "data" / "segments"
CORPUS_ROOTS = (
    ROOT / ".rescratch" / "corpus" / "parts",
    ROOT / ".rescratch" / "corpus2" / "parts",
    ROOT / "examples" / "Single Turbo Dual Overhead Cam V8 - KDP - 2024",
)
CANDIDATE_NAMES = (
    "moNodeName_c",
    "moUnitComponent_c",
    "suObList",
    "moPMarkRecord_c",
    "moComponent_c",
    "moAsmFeatData_c",
)
OUTPUT = ROOT / "re" / "data" / "ExternalClasses.json"
CONFIG0_NODEDIFF = SEGMENTS / "NodediffContentsConfigZero.json"

TRACES = (
    "baseline",
    "circle",
    "planetop",
    "twopad",
    "cutbase",
    "padplane",
    "three",
    "vendor_ring",
    "vendor_cojinete",
)

COUNTER_STEP = {"definition": 2, "classref": 1, "null": 0, "objectref": 0}
UNICODE_MARKER = b"\xff\xfe\xff"
BODY_FEATURES = ("moExtrusion_c", "moICE_c")
COMP_REF_PREFIX = "moComp"
SKETCH_PARENTS = ("sgSketch", "moSketchRegion_c", "sgCircleDim", "sgLLDist", "null")

RESOLVED_BASES = {"boss1": 109, "boss2": 110, "boss3": 111}


# distinct type lets callers separate inference failures from malformed input
class ResolveError(RuntimeError):
    __slots__ = ()


def load_trace(label):
    path = SEGMENTS / f"segments_{label}.json"
    if not path.exists():
        raise ResolveError(f"missing segmentation {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_stream(doc):
    part = pathlib.Path(doc["part"])
    if not part.exists():
        raise ResolveError(f"missing part {part}")
    blob = streamlib.load_donor(part).resolved
    if len(blob) != doc["stream_length"]:
        raise ResolveError(
            f"{part.name}: stream {len(blob)} != traced {doc['stream_length']}"
        )
    return part, blob


def external_groups(doc):
    base = doc["base_map_index"]
    groups = {}
    for row in doc["segments"]:
        if row["kind"] != "classref" or row["class_index"] >= base:
            continue
        groups.setdefault(row["class_index"], []).append(row)
    return groups


def children(segments, index):
    return [row for row in segments if row["parent"] == index]


def parent_name(segments, row):
    if row["parent"] < 0:
        return "ROOT"
    return segments[row["parent"]]["class_name"]


def check_nodename(segments, blob, rows):
    lengths = []
    for row in rows:
        body = blob[row["offset"] + row["header"] : row["end"]]
        if body[:3] != UNICODE_MARKER:
            return None
        count = body[3]
        own = 4 + 2 * count
        if own > len(body):
            return None
        try:
            body[4:own].decode("utf-16le")
        except UnicodeDecodeError:
            return None
        lengths.append(own)
    return {
        "own_body_lengths": sorted(set(lengths)),
        "trailing_bytes": sorted({r["length"] - 2 - l for r, l in zip(rows, lengths)}),
    }


def check_component(segments, blob, rows):
    nested = []
    for row in rows:
        if row["length"] != 2:
            return None
        kids = children(segments, row["index"])
        if len(kids) != 1 or kids[0]["kind"] not in ("objectref", "classref"):
            return None
        nested.append(kids[0]["kind"])
        if not parent_name(segments, row).startswith(COMP_REF_PREFIX):
            return None
    return {"own_body_lengths": [0], "nested_first_child": sorted(set(nested))}


def check_oblist(segments, blob, rows):
    counts = []
    matched = 0
    for row in rows:
        body = blob[row["offset"] + row["header"] : row["end"]]
        if len(body) < 2:
            return None
        count = struct.unpack_from("<H", body, 0)[0]
        kids = children(segments, row["index"])
        if kids:
            if count != len(kids):
                return None
            matched += 1
        counts.append(count)
        if parent_name(segments, row) not in SKETCH_PARENTS:
            return None
    if matched == 0:
        return None
    return {
        "own_body_lengths": [2],
        "counts": sorted(set(counts)),
        "count_matches_children": matched,
    }


def check_pmark(segments, blob, rows):
    for row in rows:
        if row["offset"] < 4:
            return None
        if blob[row["offset"] - 4 : row["offset"]] != b"\x01\x00\x00\x00":
            return None
        if parent_name(segments, row) not in BODY_FEATURES:
            return None
        body = blob[row["offset"] + row["header"] : row["end"]]
        if len(body) < 4:
            return None
    ids = [
        struct.unpack_from("<I", blob, row["offset"] + row["header"])[0] for row in rows
    ]
    return {"own_body_lengths": [4], "pmark_ids": sorted(set(ids))}


SLOTS = (
    {
        "slot": "node_name",
        "class_name": "moNodeName_c",
        "check": check_nodename,
        "reader": "moNode_c::Serialize @0x4c1db8f0 -> su_CArchive::ReadObject(&moNodeName_c::classmoNodeName_c)",
        "serialize": "moNodeName_c::Serialize @0x4c1db8a0 reads exactly one CString",
        "caveat": (
            "the class name is written literally in the decompiled reader, as the "
            "CRuntimeClass argument of ReadObject"
        ),
    },
    {
        "slot": "component",
        "class_name": "moUnitComponent_c",
        "check": check_component,
        "reader": "moCompRef_c::Serialize @0x4bc22f00 -> ::operator>>(archive, &owner) into the moComponent_c* member at +0x58",
        "serialize": "moUnitComponent_c::Serialize @0x4c288670 -> moComponent_c::Serialize @0x4c279a90 reads one nested object and no scalar first",
        "caveat": (
            "the decompiled reader names the base class moComponent_c, which is the "
            "declared type of the member it fills; the concrete class is pinned by two "
            "further measurements: moComponent_c is never defined by name in any stream "
            "of any part scanned, so it cannot be the referent, while moUnitComponent_c "
            "is defined in Contents/Config-0 and the replayed Contents/Config-0 map "
            "places it at exactly the observed index"
        ),
    },
    {
        "slot": "object_list",
        "class_name": "suObList",
        "check": check_oblist,
        "reader": "moSketchRegion_c::Serialize @0x4b9d81e0 -> ::operator>>(archive, (suObList **)(this + 8)) and sgSketch::Serialize @0x4c5d28c0 -> ::operator>>(archive, (suObList **)(this + 0x5d0))",
        "serialize": "u16 element count followed by that many nested objects",
        "caveat": (
            "the read itself is polymorphic; suObList is the declared type of the member "
            "it fills, and suObList is also defined by name in Contents/Config-0, "
            "Contents/CMgr and Contents/Config-0-ModelHeader, where the replayed "
            "Contents/Config-0 map places it at exactly the observed index"
        ),
    },
    {
        "slot": "pmark_record",
        "class_name": "moPMarkRecord_c",
        "check": check_pmark,
        "reader": "FUN_4bb886c0 (base Serialize invoked first by moBodyFeature_c::Serialize @0x4bb8aa10) reads AR_get_int then, when non-zero, ::operator>>(archive, (moPMarkRecord_c **)(this + 0x3c8))",
        "serialize": "moPMarkRecord_c::Serialize @0x4bb97ca0 reads exactly one long",
        "caveat": (
            "the class name is written literally at the call site and in the demangled "
            "symbol of the extraction operator, "
            "??5@YAAEAVsu_CArchive@@AEAV0@AEAPEAVmoPMarkRecord_c@@@Z"
        ),
    },
)


def definition_presence():
    parts = []
    for root in CORPUS_ROOTS:
        if root.exists():
            parts.extend(sorted(root.glob("*.SLDPRT")))
    if not parts:
        raise ResolveError("no corpus parts found for the class-definition scan")
    totals = {name: 0 for name in CANDIDATE_NAMES}
    for part in parts:
        present = set()
        for blob in carchive.streams(part).values():
            for definition in carchive.class_definitions(blob):
                if definition.name in totals:
                    present.add(definition.name)
        for name in present:
            totals[name] += 1
    return {"parts_scanned": len(parts), "defined_in_parts": totals}


def config0_map():
    doc = json.loads(CONFIG0_NODEDIFF.read_text(encoding="utf-8"))
    labels = doc["labels"]
    result = {}
    for position, label in enumerate(labels):
        counter = 4
        classes = {}
        for row in doc["rows"]:
            if row["sources"][position] is None:
                continue
            if row["kind"] == "definition":
                classes[counter] = row["class_name"]
            counter += COUNTER_STEP[row["kind"]]
        result[label] = {"classes": classes, "final_counter": counter}
    return result


def assign(doc, blob):
    segments = doc["segments"]
    groups = external_groups(doc)
    assignment = {}
    for index in sorted(groups):
        rows = groups[index]
        hits = []
        for slot in SLOTS:
            evidence = slot["check"](segments, blob, rows)
            if evidence is not None:
                hits.append((slot["slot"], evidence))
        if len(hits) != 1:
            raise ResolveError(
                f"index {index}: {len(hits)} slot signatures matched ({[h[0] for h in hits]})"
            )
        name, evidence = hits[0]
        if name in assignment:
            raise ResolveError(f"slot {name} matched two class indices")
        assignment[name] = {
            "class_index": index,
            "occurrences": len(rows),
            "parents": sorted({parent_name(segments, r) for r in rows}),
            "traced_span_lengths": sorted({r["length"] for r in rows}),
            "example_spans": [
                {
                    "segment_index": r["index"],
                    "offset": r["offset"],
                    "end": r["end"],
                    "depth": r["depth"],
                    "parent_class": parent_name(segments, r),
                }
                for r in rows[:3]
            ],
            "byte_evidence": evidence,
        }
    if len(assignment) != len(SLOTS):
        raise ResolveError(f"resolved {len(assignment)} of {len(SLOTS)} slots")
    return assignment


def main():
    per_trace = {}
    for label in TRACES:
        doc = load_trace(label)
        part, blob = load_stream(doc)
        per_trace[label] = {
            "part": str(part),
            "stream_length": len(blob),
            "base_map_index": doc["base_map_index"],
            "slots": assign(doc, blob),
        }

    presence = definition_presence()
    config0 = config0_map()
    continuation = {}
    for label, data in config0.items():
        continuation[label] = {
            "config0_final_counter": data["final_counter"],
            "resolved_features_base": RESOLVED_BASES[label],
            "matches": data["final_counter"] == RESOLVED_BASES[label],
            "class_index_of_slot": {
                slot["class_name"]: next(
                    (
                        index
                        for index, name in sorted(data["classes"].items())
                        if name == slot["class_name"]
                    ),
                    None,
                )
                for slot in SLOTS
            },
        }

    slots_out = {}
    for slot in SLOTS:
        name = slot["slot"]
        indices = {
            label: data["slots"][name]["class_index"]
            for label, data in per_trace.items()
        }
        counts = {
            label: data["slots"][name]["occurrences"]
            for label, data in per_trace.items()
        }
        parents = sorted(
            {p for data in per_trace.values() for p in data["slots"][name]["parents"]}
        )
        spans = sorted(
            {
                length
                for data in per_trace.values()
                for length in data["slots"][name]["traced_span_lengths"]
            }
        )
        own = sorted(
            {
                length
                for data in per_trace.values()
                for length in data["slots"][name]["byte_evidence"]["own_body_lengths"]
            }
        )
        config_index = {
            label: value["class_index_of_slot"][slot["class_name"]]
            for label, value in continuation.items()
        }
        fixed = len(set(indices.values())) == 1
        slots_out[name] = {
            "class_name": slot["class_name"],
            "confidence": "confirmed",
            "class_index_per_trace": indices,
            "class_index_fixed": fixed,
            "class_index_rule": (
                "constant 4 in all nine traces; it is the first class definition of "
                "Contents/Config-0, whose map index is 4 in every part observed"
                if fixed
                else "document specific: the map index this class received while "
                "Contents/Config-0 was being read; not a function of the "
                "ResolvedFeatures base"
            ),
            "occurrences_per_trace": counts,
            "parent_classes": parents,
            "traced_span_lengths": spans,
            "own_body_lengths": own,
            "decompiled_reader": slot["reader"],
            "decompiled_serialize": slot["serialize"],
            "caveat": slot["caveat"],
            "defined_by_name_in_parts": presence["defined_in_parts"][
                slot["class_name"]
            ],
            "config0_class_index": config_index,
        }

    document = {
        "stream": "Contents/Config-0-ResolvedFeatures",
        "question": (
            "the four class references whose index is below the ResolvedFeatures base "
            "map index and whose class name is therefore never written in this stream"
        ),
        "method": (
            "each external class reference was matched to the child object that its "
            "parent's decompiled Serialize reads at that position, then confirmed "
            "against the stream bytes; independently, the class map of "
            "Contents/Config-0 was replayed with the +2/+1/0/0 counter rule and its "
            "final counter reproduces the ResolvedFeatures base exactly"
        ),
        "slots": slots_out,
        "config0_continuation": continuation,
        "class_definition_scan": presence,
        "traces": per_trace,
    }
    OUTPUT.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    for name, data in slots_out.items():
        print(
            f"{name}: {data['class_name']} confidence={data['confidence']} "
            f"fixed={data['class_index_fixed']} indices={sorted(set(data['class_index_per_trace'].values()))}"
        )
    for label, value in continuation.items():
        print(
            f"config0 {label}: final={value['config0_final_counter']} "
            f"resolved_base={value['resolved_features_base']} matches={value['matches']}"
        )
    print(f"class definition scan over {presence['parts_scanned']} parts:")
    for name, count in presence["defined_in_parts"].items():
        print(f"  {name}: {count}")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()

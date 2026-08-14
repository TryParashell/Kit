import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[4]
TRACE = ROOT / "re/data/segments"
OUT = ROOT / ".rescratch/ghidra/out"
GH = ROOT / "re/tooling/ghidra"

PRIORITY = [
    "moExtrusion_c",
    "moICE_c",
    "moEndSpec_c",
    "moFromEndSpec_c",
    "moRevEndSpec_c",
    "moRevolution_c",
    "moRevolutionThin_c",
    "moRevCut_c",
    "moCut_c",
    "moProfileFeature_c",
    "moOriginProfileFeature_c",
    "moLengthParameter_c",
    "moAngleParameter_c",
    "moBodyFeature_c",
    "moFeature_c",
    "moModelFeature_c",
    "moCompFeature_c",
    "moPerBodyChooserData_c",
    "moFaceRef_c",
    "moFR_c",
    "moBBoxCenterData_c",
    "moDisplayDistanceDim_c",
    "moFeatureDimHandle_c",
    "moFavoriteHandle_c",
    "sgSketch",
    "sgArc",
    "sgLine",
    "sgSpline",
    "sgPoint",
    "sgEntHandle",
    "sgArcHandle",
    "sgLineHandle",
    "sgSplineHandle",
    "sgPointHandle",
    "sgDim",
    "sgLogDim",
    "moHistoryFeatItemData_c",
    "moSketchChain_c",
    "moSketchRegion_c",
]


def observed():
    names = set()
    for path in sorted(TRACE.glob("segments_*.json")):
        doc = json.loads(path.read_text())
        segs = doc["segments"]
        for seg in segs:
            name = seg["class_name"]
            m = re.match(r"backref->(\d+)$", name)
            if m:
                name = segs[int(m.group(1))]["class_name"]
            if (
                name in ("null",)
                or name.startswith("external#")
                or name.startswith("backref->")
            ):
                continue
            names.add(name)
    return names


def main():
    smap = json.loads((OUT / "SerializeMap.json").read_text())
    want = []
    for name in PRIORITY:
        if name in smap:
            want.append(name)
    for name in sorted(observed()):
        if name in smap and name not in want:
            want.append(name)
    lines = []
    seen = set()
    rows = []
    for name in want:
        addr = smap[name]["serialize_addr"]
        rows.append((name, addr, smap[name]["serialize_name"]))
        if addr in seen:
            continue
        seen.add(addr)
        lines.append("0x" + addr)
    (GH / "SpecSldmodu.txt").write_text("\n".join(lines) + "\n")
    (OUT / "SpecSldmoduClasses.json").write_text(
        json.dumps([{"class": n, "addr": a, "name": f} for n, a, f in rows], indent=1)
    )
    print("classes requested", len(rows), "distinct functions", len(lines))
    missing = [n for n in PRIORITY if n not in smap]
    print("priority classes with no vtable entry:", missing)


if __name__ == "__main__":
    main()

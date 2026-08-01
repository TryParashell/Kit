from __future__ import annotations

import hashlib
import io
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zipfile

import pytest

from convert import convert, open_document
from convert.adapters.freecad import FreeCADAdapter


SAMPLE = Path(__file__).parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"
FREECAD_EXAMPLES = (
    Path(__file__).parents[3]
    / "Parashell"
    / ".pixi"
    / "envs"
    / "default"
    / "Library"
    / "data"
    / "examples"
)


def _native_property(
    name: str,
    type_id: str,
    tag: str,
    attributes: dict[str, str] | None = None,
) -> ET.Element:
    node = ET.Element("Property", {"name": name, "type": type_id})
    ET.SubElement(node, tag, attributes or {})
    return node


def _native_placement(name: str = "Placement") -> ET.Element:
    return _native_property(
        name,
        "App::PropertyPlacement",
        "PropertyPlacement",
        {
            "Px": "0",
            "Py": "0",
            "Pz": "0",
            "Q0": "0",
            "Q1": "0",
            "Q2": "0",
            "Q3": "1",
        },
    )


def _native_link_list(name: str, values: tuple[str, ...]) -> ET.Element:
    node = _native_property(
        name, "App::PropertyLinkList", "LinkList", {"count": str(len(values))}
    )
    for value in values:
        ET.SubElement(node[0], "Link", {"value": value})
    return node


def _native_xlink(
    name: str, target: str, subelements: tuple[str, ...] = ()
) -> ET.Element:
    node = _native_property(
        name,
        "App::PropertyXLinkSubHidden" if subelements else "App::PropertyXLink",
        "XLink",
        {
            "file": "",
            "stamp": "",
            "name": target,
            "count": str(len(subelements)),
        },
    )
    for subelement in subelements:
        ET.SubElement(node[0], "Sub", {"value": subelement})
    return node


def _native_archive(
    objects: tuple[
        tuple[str, str, tuple[str, ...], tuple[ET.Element, ...]], ...
    ],
    entries: dict[str, bytes],
) -> bytes:
    root = ET.Element(
        "Document",
        {"SchemaVersion": "4", "ProgramVersion": "1.0", "FileVersion": "1"},
    )
    declarations = ET.SubElement(
        root, "Objects", {"Count": str(len(objects)), "Dependencies": "1"}
    )
    for name, _, dependencies, _ in objects:
        dependency_node = ET.SubElement(
            declarations,
            "ObjectDeps",
            {"Name": name, "Count": str(len(dependencies))},
        )
        for dependency in dependencies:
            ET.SubElement(dependency_node, "Dep", {"Name": dependency})
    for index, (name, type_id, _, _) in enumerate(objects, start=1):
        ET.SubElement(
            declarations,
            "Object",
            {"type": type_id, "name": name, "id": str(index)},
        )
    data = ET.SubElement(root, "ObjectData", {"Count": str(len(objects))})
    for name, _, _, properties in objects:
        object_node = ET.SubElement(data, "Object", {"name": name})
        property_node = ET.SubElement(object_node, "Properties", {"Count": "0"})
        property_node.extend(properties)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "Document.xml", ET.tostring(root, encoding="utf-8", xml_declaration=True)
        )
        for name, value in entries.items():
            archive.writestr(name, value)
    return stream.getvalue()


def _native_part_fixture() -> bytes:
    plane_properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "XY"}),
        _native_placement(),
    )
    attachment = _native_property(
        "AttachmentSupport",
        "App::PropertyLinkSubList",
        "LinkSubList",
        {"count": "1"},
    )
    ET.SubElement(attachment[0], "Link", {"obj": "XY_Plane", "sub": ""})
    geometry = _native_property(
        "Geometry", "Part::PropertyGeometryList", "GeometryList", {"count": "2"}
    )
    circle = ET.SubElement(
        geometry[0],
        "Geometry",
        {"type": "Part::GeomCircle", "id": "101", "migrated": "1"},
    )
    ET.SubElement(
        circle,
        "Circle",
        {"CenterX": "0", "CenterY": "0", "Radius": "5"},
    )
    ET.SubElement(circle, "Construction", {"value": "0"})
    point = ET.SubElement(
        geometry[0],
        "Geometry",
        {"type": "Part::GeomPoint", "id": "102", "migrated": "1"},
    )
    ET.SubElement(point, "GeomPoint", {"X": "2", "Y": "3", "Z": "0"})
    ET.SubElement(point, "Construction", {"value": "0"})
    constraints = _native_property(
        "Constraints",
        "Sketcher::PropertyConstraintList",
        "ConstraintList",
        {"count": "3"},
    )
    for attributes in (
        {
            "Name": "Diameter",
            "Type": "18",
            "Value": "10",
            "IsDriving": "1",
            "IsActive": "1",
            "First": "0",
            "FirstPos": "3",
            "Second": "-2000",
            "SecondPos": "0",
            "Third": "-2000",
            "ThirdPos": "0",
        },
        {
            "Name": "Angle",
            "Type": "9",
            "Value": "1.5707963267948966",
            "IsDriving": "1",
            "IsActive": "1",
            "First": "0",
            "FirstPos": "3",
            "Second": "1",
            "SecondPos": "1",
            "Third": "-2000",
            "ThirdPos": "0",
        },
        {
            "Name": "PointOnObject",
            "Type": "13",
            "Value": "0",
            "IsDriving": "1",
            "IsActive": "1",
            "First": "1",
            "FirstPos": "1",
            "Second": "0",
            "SecondPos": "0",
            "Third": "-2000",
            "ThirdPos": "0",
        },
    ):
        ET.SubElement(constraints[0], "Constrain", attributes)
    expressions = _native_property(
        "ExpressionEngine",
        "App::PropertyExpressionEngine",
        "ExpressionEngine",
        {"count": "1"},
    )
    ET.SubElement(
        expressions[0],
        "Expression",
        {"path": "Constraints[0]", "expression": "diameter"},
    )
    sketch_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Sketch"}
        ),
        attachment,
        geometry,
        constraints,
        expressions,
        _native_property(
            "FullyConstrained", "App::PropertyBool", "Bool", {"value": "true"}
        ),
        _native_placement(),
    )
    profile = _native_property(
        "Profile", "App::PropertyLinkSub", "LinkSub", {"value": "Sketch", "count": "0"}
    )
    direction = _native_property(
        "Direction",
        "App::PropertyVector",
        "PropertyVector",
        {"valueX": "0", "valueY": "0", "valueZ": "1"},
    )
    shape = _native_property(
        "Shape", "Part::PropertyPartShape", "Part", {"file": "Pad.Shape.brp"}
    )
    pad_expressions = _native_property(
        "ExpressionEngine",
        "App::PropertyExpressionEngine",
        "ExpressionEngine",
        {"count": "1"},
    )
    ET.SubElement(
        pad_expressions[0],
        "Expression",
        {"path": "Length", "expression": "height"},
    )
    pad_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Pad"}
        ),
        profile,
        _native_property(
            "Length", "App::PropertyLength", "Float", {"value": "25"}
        ),
        _native_property(
            "Type", "App::PropertyEnumeration", "Integer", {"value": "0"}
        ),
        _native_property(
            "Reversed", "App::PropertyBool", "Bool", {"value": "false"}
        ),
        _native_property(
            "Midplane", "App::PropertyBool", "Bool", {"value": "false"}
        ),
        direction,
        shape,
        pad_expressions,
    )
    body_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Body"}
        ),
        _native_link_list("Group", ("Sketch", "Pad")),
        _native_property(
            "Tip", "App::PropertyLink", "Link", {"value": "Pad"}
        ),
    )
    brep = b"\nCASCADE Topology V1, (c) Matra-Datavision\nfixture\n"
    return _native_archive(
        (
            ("Body", "PartDesign::Body", ("Sketch", "Pad"), body_properties),
            ("XY_Plane", "App::Plane", (), plane_properties),
            ("Sketch", "Sketcher::SketchObject", ("XY_Plane",), sketch_properties),
            ("Pad", "PartDesign::Pad", ("Sketch", "Body"), pad_properties),
        ),
        {"Pad.Shape.brp": brep},
    )


def _native_assembly_fixture() -> bytes:
    shape_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Shape"}
        ),
        _native_property(
            "Shape", "Part::PropertyPartShape", "Part", {"file": "Shape.Shape.brp"}
        ),
    )
    assembly_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Assembly"}
        ),
        _native_link_list("Group", ("Joints", "PartLink", "Grounded", "Revolute")),
        _native_placement(),
    )
    link_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Part 1"}
        ),
        _native_xlink("LinkedObject", "Shape"),
        _native_placement(),
        _native_placement("LinkPlacement"),
        _native_property(
            "Visibility", "App::PropertyBool", "Bool", {"value": "true"}
        ),
    )
    grounded_proxy = _native_property(
        "Proxy",
        "App::PropertyPythonObject",
        "Python",
        {"value": "bnVsbA==", "encoded": "yes", "module": "JointObject", "class": "GroundedJoint"},
    )
    grounded_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Grounded"}
        ),
        grounded_proxy,
        _native_property(
            "ObjectToGround", "App::PropertyLink", "Link", {"value": "PartLink"}
        ),
        _native_placement(),
    )
    joint_type = _native_property(
        "JointType",
        "App::PropertyEnumeration",
        "Integer",
        {"value": "1", "CustomEnum": "true"},
    )
    enum_list = ET.SubElement(joint_type, "CustomEnumList", {"count": "2"})
    ET.SubElement(enum_list, "Enum", {"value": "Fixed"})
    ET.SubElement(enum_list, "Enum", {"value": "Revolute"})
    joint_proxy = _native_property(
        "Proxy",
        "App::PropertyPythonObject",
        "Python",
        {"value": "bnVsbA==", "encoded": "yes", "module": "JointObject", "class": "Joint"},
    )
    joint_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Revolute"}
        ),
        joint_proxy,
        joint_type,
        _native_xlink("Reference1", "Assembly", ("PartLink.Face1", "PartLink.Edge1")),
        _native_xlink("Reference2", "Assembly", ("PartLink.Face2",)),
        _native_placement("Placement1"),
        _native_placement("Placement2"),
        _native_property(
            "Suppressed", "App::PropertyBool", "Bool", {"value": "false"}
        ),
    )
    joint_group_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Joints"}
        ),
        _native_link_list("Group", ("Grounded", "Revolute")),
    )
    brep = b"\nCASCADE Topology V1, (c) Matra-Datavision\nassembly fixture\n"
    return _native_archive(
        (
            ("Shape", "Part::Feature", (), shape_properties),
            (
                "Assembly",
                "Assembly::AssemblyObject",
                ("Joints", "PartLink", "Grounded", "Revolute"),
                assembly_properties,
            ),
            ("Joints", "Assembly::JointGroup", ("Grounded", "Revolute"), joint_group_properties),
            ("PartLink", "App::Link", ("Shape",), link_properties),
            ("Grounded", "App::FeaturePython", ("Assembly", "PartLink"), grounded_properties),
            ("Revolute", "App::FeaturePython", ("Assembly",), joint_properties),
        ),
        {"Shape.Shape.brp": brep},
    )


def test_direct_fcstd_roundtrip_preserves_interchange_and_brep(tmp_path) -> None:
    output = tmp_path / "example.FCStd"
    result = convert(SAMPLE, output)
    restored = open_document(output)
    assert restored == result.document
    assert restored.validate() == ()
    assert [payload.sha256 for payload in restored.brep_payloads] == [
        "8c57db227621a15a0a429cdd65dbe3f374e2c1145ef2f3edc3a25b745513bf3d",
        "3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6",
        "59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7",
    ]
    with zipfile.ZipFile(output) as archive:
        archive.testzip()
        names = set(archive.namelist())
        assert "Document.xml" in names
        assert "interchange/document.json" in names
        assert "Fillet1.Edges" in names
        assert (
            len(
                names
                & {
                    "interchange/native/sldprt_brep_0.x_b",
                    "interchange/native/sldprt_brep_1.x_b",
                    "interchange/native/sldprt_brep_2.x_b",
                }
            )
            == 3
        )
        for payload in restored.brep_payloads:
            entry = f"interchange/native/{payload.id.replace(':', '_')}.x_b"
            assert hashlib.sha256(archive.read(entry)).hexdigest() == payload.sha256


def test_fcstd_contains_editable_native_history(tmp_path) -> None:
    output = tmp_path / "example.FCStd"
    convert(SAMPLE, output)
    with zipfile.ZipFile(output) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
        objects = root.findall("./Objects/Object")
        types = [item.get("type") for item in objects]
        names = {item.get("name") for item in objects}
        assert types.count("Spreadsheet::Sheet") == 1
        assert types.count("Sketcher::SketchObject") == 5
        assert types.count("Part::Extrusion") == 5
        assert types.count("Part::Cut") == 2
        assert types.count("Part::MultiFuse") == 2
        assert types.count("Part::Fillet") == 1
        assert {
            "Parameters",
            "Sketch1",
            "Sketch2",
            "Sketch3",
            "Sketch4",
            "Sketch6",
            "Boss_Extrude1",
            "Cut_Extrude1",
            "Boss_Extrude2",
            "Cut_Extrude2",
            "Boss_Extrude3",
            "Fillet1",
        } <= names
        count, edge, start_radius, end_radius = struct.unpack(
            "<IIdd", archive.read("Fillet1.Edges")
        )
        assert (count, edge, start_radius, end_radius) == (1, 3, 0.25, 0.25)
        xml = archive.read("Document.xml")
        assert b"KitMetadata" in xml


def test_fcstd_output_is_deterministic(tmp_path) -> None:
    first = tmp_path / "first.FCStd"
    second = tmp_path / "second.FCStd"
    convert(SAMPLE, first)
    convert(SAMPLE, second)
    assert first.read_bytes() == second.read_bytes()


def test_fcstd_stream_probe_does_not_consume_input(tmp_path) -> None:
    output = tmp_path / "example.FCStd"
    result = convert(SAMPLE, output)
    stream = io.BytesIO(output.read_bytes())
    assert FreeCADAdapter().probe(stream).confidence == 1.0
    assert stream.tell() == 0
    assert open_document(stream) == result.document


def test_generic_fcstd_is_not_claimed_as_readable() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("Document.xml", "<Document/>")
    assert FreeCADAdapter().probe(stream.getvalue()).confidence == 0.0


def test_native_partdesign_fcstd_restores_history_sketches_and_brep() -> None:
    source = FREECAD_EXAMPLES / "PartDesignExample.FCStd"
    if not source.is_file():
        pytest.skip("bundled FreeCAD PartDesign example is unavailable")
    adapter = FreeCADAdapter()
    assert adapter.probe(source).confidence == 0.95
    document = adapter.read(source)
    assert document.validate() == ()
    assert [
        (sketch.name, len(sketch.entities), len(sketch.constraints))
        for sketch in document.sketches
    ] == [
        ("Sketch", 4, 12),
        ("Sketch001", 4, 11),
        ("Sketch003", 1, 2),
        ("Sketch002", 12, 32),
    ]
    assert [feature.name for feature in document.feature_timeline] == [
        "Pad",
        "Pocket",
        "Pocket001",
        "Pocket002",
    ]
    assert document.bodies[0].final_feature_id == "freecad:feature:Pocket002"
    final_payload = next(
        payload
        for payload in document.brep_payloads
        if payload.source_stream == "Pocket002.Shape.brp"
    )
    assert final_payload.sha256 == (
        "285ae851c79757d7252b67236637f52c776b45b8c42d1e5749109b048d0430c9"
    )
    assert len(final_payload.data or b"") == 51454

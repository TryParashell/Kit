# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import base64
from dataclasses import replace
import hashlib
import inspect
import io
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zipfile
import zlib

import pytest

from convert import (
    ApplicationUsabilityError,
    convert,
    open_document,
    registry,
    write_document,
)
from convert.adapters.base import CarrierReason, ReadOptions, TransferMode, WriteOptions
from convert.adapters.freecad import (
    FreeCADAdapter,
    FreeCADAdapterError,
    build_fcstd_archive,
    document_to_manifest,
)
from convert.adapters.freecad.Brep import brep_model_brep
import convert.adapters.freecad.Adapter as freecad_adapter_module
import convert.adapters.freecad.Archive as freecad_archive_module
import convert.adapters.freecad.Native as freecad_native_module
from convert.adapters.freecad.Adapter import _filtered_document
from convert.adapters.freecad.Format import CAPABILITY_CARRIER_REASONS, CAPABILITY_WRITE_TYPE_IDS, FORMAT_ID, INFO, NATIVE_CAPABILITIES, SUFFIX
from convert.adapters.freecad.Protocol import ADDITIONAL_PART_OBJECT_TYPE_IDS, ASSEMBLY_CONNECTOR_PROPERTY_PREFIXES, ASSEMBLY_JOINT_GROUP_TYPE_ID, ASSEMBLY_LINK_TYPE_ID, ASSEMBLY_OBJECT_TYPE_PREFIX, ASSEMBLY_ROOT_TYPE_ID, APP_PART_TYPE_ID, APP_LINK_TYPE_ID, BODY_CONTAINER_TYPE_IDS, BODY_TYPE_ID, BOOLEAN_OPERATION_TYPE_BY_KIND, BOOLEAN_OPERATION_TYPES, CIRCULAR_GEOMETRY_KINDS, CONSTRAINT_CODE_BY_KIND, CONSTRAINT_CARRIER_KINDS, CONSTRAINT_COMPOSED_KINDS, CONSTRAINT_DIRECT_KINDS, CONSTRAINT_KIND_BY_CODE, CONSTRAINT_POINT_BY_INDEX, CONSTRAINT_POINT_INDEX_BY_NAME, CONSTRAINT_POINTS, CONSTRAINT_TYPES, CONSTRAINT_VALUE_KIND_BY_CODE, CONSTRAINT_WRITE_CODES, CONSTRAINT_WRITE_KINDS, CREATE_OPERATION_NAMES, DIMENSIONAL_CONSTRAINT_CODES, EXTRUSION_TYPE_BY_CODE, EXTRUSION_TYPES, FEATURE_KIND_BY_TYPE_ID, FEATURE_CARRIER_KINDS, FEATURE_TYPES, FEATURE_WRITE_KINDS, FEATURE_WRITE_TYPE_IDS, FIXED_CONSTRAINT_KINDS, GEOMETRY_KIND_BY_TYPE_ID, GEOMETRY_CARRIER_KINDS, GEOMETRY_TYPES, GEOMETRY_TYPE_IDS_BY_KIND, GEOMETRY_WRITE_KINDS, GEOMETRY_WRITE_TYPE_IDS, JOINT_GROUND_PROPERTY, JOINT_REFERENCE_INDEX_BY_PROPERTY, JOINT_REFERENCE_PROPERTIES, JOINT_RESERVED_LINK_PROPERTIES, JOINT_TYPE_BY_MATE_KIND, JOINT_TYPE_DEFINITIONS, JOINT_TYPE_PROPERTIES, JOINT_TYPES, JOINT_TYPES_USING_DISTANCE, JOINT_TYPES_USING_SECOND_DISTANCE, MATE_KIND_BY_JOINT_TYPE, MATE_CARRIER_KINDS, MATE_KINDS_USING_DISTANCE, MATE_KINDS_USING_SECOND_DISTANCE, MATE_WRITE_KINDS, MATE_WRITE_TYPES, MIDPOINT_REFERENCE_POINT_NAMES, NEUTRAL_GEOMETRY_TYPE_BY_KIND, NEUTRAL_GEOMETRY_TYPE_ID_BY_KIND, NON_FEATURE_OBJECT_TYPE_IDS, PART_CONTAINER_TYPE_IDS, PART_OBJECT_TYPE_IDS, PERMISSIVE_TRUE_VALUES, POCKET_TYPE_ID, PRIMITIVE_FEATURE_FAMILIES, PRIMITIVE_FEATURE_TYPE_IDS, QUANTITY_PROPERTY_UNITS, REGISTERED_PART_OBJECT_TYPE_IDS, SCALAR_PROPERTY_KINDS, SCALAR_PROPERTY_TYPES, SKETCH_TYPE_ID, SPLINE_GEOMETRY_KINDS, SPLINE_GEOMETRY_TYPE_IDS, SPLINE_CONTROL_TAGS, STRING_HASHER_TAGS, SUBELEMENT_KIND_BY_PREFIX, SUBELEMENT_MATE_ENTITY_KINDS, SUPPORT_PLANE_TYPE_IDS, XML_TRUE_VALUES
from convert.geometry.Opencascade import is_structurally_valid_ascii_brep
from interchange import (
    ArcEllipseGeometry,
    ArcHyperbolaGeometry,
    ArcParabolaGeometry,
    BooleanOperation,
    BrepPayload,
    Capability,
    ChamferFeature,
    CircleGeometry,
    CircularPatternFeature,
    Configuration,
    ConstraintKind,
    ConstraintReference,
    Expression,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureKind,
    FeatureStep,
    EllipseGeometry,
    GeometryKind,
    HyperbolaGeometry,
    LineGeometry,
    LinearPatternFeature,
    MateKind,
    Mesh,
    NativeFeatureDefinition,
    NativeGeometry,
    Parameter,
    ParameterValue,
    ParabolaGeometry,
    PayloadRole,
    PointGeometry,
    Selection,
    SelectionPathElement,
    ShellFeature,
    SketchConstraint,
    SketchEntity,
    Transform,
    ValueKind,
    Vector2,
    Vector3,
)

from tests.interchange.document.DocumentTests import document as neutral_document
from tests.interchange.brep.BrepTests import triangle_brep

SAMPLE = Path(__file__).parents[3] / "examples" / ".SLDPRT" / "example.SLDPRT"
FREECAD_EXAMPLES = (
    Path(__file__).parents[4]
    / "Parashell"
    / ".pixi"
    / "envs"
    / "default"
    / "Library"
    / "data"
    / "examples"
)


def _line_entity(
    identifier: str,
    start: tuple[float, float],
    end: tuple[float, float],
) -> SketchEntity:
    return SketchEntity(
        identifier,
        GeometryKind.LINE,
        LineGeometry(Vector2(*start), Vector2(*end)),
    )


def test_native_closed_profile_inference_accepts_simple_edge_cycles() -> None:
    first = tuple(
        _line_entity(identifier, start, end)
        for identifier, start, end in (
            ("edge:0", (-30.0, -15.0), (30.0, -15.0)),
            ("edge:1", (30.0, -15.0), (30.0, 15.0)),
            ("edge:2", (30.0, 15.0), (-30.0, 15.0)),
            ("edge:3", (-30.0, 15.0), (-30.0, -15.0)),
        )
    )
    second = tuple(
        _line_entity(identifier, start, end)
        for identifier, start, end in (
            ("edge:4", (50.0, 0.0), (60.0, 0.0)),
            ("edge:5", (60.0, 0.0), (55.0, 10.0)),
            ("edge:6", (55.0, 10.0), (50.0, 0.0)),
        )
    )
    assert freecad_native_module._closed_profile_entity_ids((*first, *second)) == (
        ("edge:0", "edge:1", "edge:2", "edge:3"),
        ("edge:4", "edge:5", "edge:6"),
    )


@pytest.mark.parametrize(
    "entities",
    (
        (
            _line_entity("open:0", (0.0, 0.0), (10.0, 0.0)),
            _line_entity("open:1", (10.0, 0.0), (10.0, 10.0)),
            _line_entity("open:2", (10.0, 10.0), (0.0, 10.0)),
        ),
        (
            _line_entity("branch:0", (0.0, 0.0), (10.0, 0.0)),
            _line_entity("branch:1", (10.0, 0.0), (10.0, 10.0)),
            _line_entity("branch:2", (10.0, 10.0), (0.0, 10.0)),
            _line_entity("branch:3", (0.0, 10.0), (0.0, 0.0)),
            _line_entity("branch:4", (0.0, 0.0), (-10.0, 0.0)),
        ),
        (
            _line_entity("cross:0", (-10.0, -10.0), (10.0, 10.0)),
            _line_entity("cross:1", (10.0, 10.0), (-10.0, 10.0)),
            _line_entity("cross:2", (-10.0, 10.0), (10.0, -10.0)),
            _line_entity("cross:3", (10.0, -10.0), (-10.0, -10.0)),
        ),
    ),
)
def test_native_closed_profile_inference_rejects_ambiguous_networks(
    entities: tuple[SketchEntity, ...],
) -> None:
    assert freecad_native_module._closed_profile_entity_ids(entities) == ()


def test_native_reader_infers_closed_profile_from_unconstrained_rectangle() -> None:
    def rectangle(root: ET.Element) -> None:
        geometry = root.find(
            "./ObjectData/Object[@name='Sketch']/Properties/"
            "Property[@name='Geometry']/GeometryList"
        )
        constraints = root.find(
            "./ObjectData/Object[@name='Sketch']/Properties/"
            "Property[@name='Constraints']/ConstraintList"
        )
        assert geometry is not None
        assert constraints is not None
        geometry.clear()
        geometry.set("count", "4")
        constraints.clear()
        constraints.set("count", "0")
        points = ((-30.0, -15.0), (30.0, -15.0), (30.0, 15.0), (-30.0, 15.0))
        for index, start in enumerate(points):
            end = points[(index + 1) % len(points)]
            item = ET.SubElement(
                geometry,
                "Geometry",
                {
                    "type": "Part::GeomLineSegment",
                    "id": str(index + 1),
                    "migrated": "1",
                },
            )
            ET.SubElement(
                item,
                "LineSegment",
                {
                    "StartX": str(start[0]),
                    "StartY": str(start[1]),
                    "EndX": str(end[0]),
                    "EndY": str(end[1]),
                },
            )
            ET.SubElement(item, "Construction", {"value": "0"})

    document = FreeCADAdapter().read(
        _rewrite_document_xml(_native_part_fixture(), rectangle)
    )
    sketch = document.sketches[0]
    assert sketch.constraints == ()
    assert sketch.closed_profile_entity_ids == (
        tuple(entity.id for entity in sketch.entities),
    )


def test_native_origin_planes_use_principal_frames_and_preserve_datum_planes() -> None:
    def plane(
        name: str,
        label: str,
        quaternion: tuple[float, float, float, float],
        origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
        role: str = "",
        type_id: str = "App::Plane",
    ):
        placement = _native_placement()
        value = placement.find("./PropertyPlacement")
        assert value is not None
        for key, coordinate in zip(("Q0", "Q1", "Q2", "Q3"), quaternion):
            value.set(key, str(coordinate))
        for key, coordinate in zip(("Px", "Py", "Pz"), origin):
            value.set(key, str(coordinate))
        properties = {
            "Label": _native_property(
                "Label", "App::PropertyString", "String", {"value": label}
            ),
            "Placement": placement,
        }
        if role:
            properties["Role"] = _native_property(
                "Role", "App::PropertyString", "String", {"value": role}
            )
        return freecad_native_module._NativeObject(
            name,
            type_id,
            0,
            name,
            False,
            (),
            (),
            (),
            properties,
        )

    half = math.sqrt(0.5)
    objects = (
        plane("XY_Plane", "XY-plane", (0.0, 0.0, 0.0, 1.0), role="XY_Plane"),
        plane("XZ_Plane", "XZ-plane", (half, 0.0, 0.0, half), role="XZ_Plane"),
        plane("YZ_Plane", "YZ-plane", (0.5, 0.5, 0.5, 0.5), role="YZ_Plane"),
        plane(
            "DatumPlane",
            "Datum Plane",
            (0.0, 0.0, math.sin(math.pi / 8.0), math.cos(math.pi / 8.0)),
            (7.0, 8.0, 9.0),
            type_id="PartDesign::Plane",
        ),
    )
    planes, sketches = freecad_native_module._parse_sketches(objects, [], set())
    assert sketches == ()
    assert [value.id for value in planes] == [
        "freecad:plane:XY_Plane",
        "freecad:plane:XZ_Plane",
        "freecad:plane:YZ_Plane",
        "freecad:plane:DatumPlane",
    ]
    assert [value.attributes.get("principal_index") for value in planes] == [
        0,
        1,
        2,
        None,
    ]
    frames = tuple(
        (
            (
                value.transform.x_axis.x,
                value.transform.x_axis.y,
                value.transform.x_axis.z,
            ),
            (
                value.transform.y_axis.x,
                value.transform.y_axis.y,
                value.transform.y_axis.z,
            ),
            (
                value.transform.z_axis.x,
                value.transform.z_axis.y,
                value.transform.z_axis.z,
            ),
        )
        for value in planes[:3]
    )
    assert frames == (
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
        ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    )
    datum = planes[3].transform
    assert (datum.origin.x, datum.origin.y, datum.origin.z) == (7.0, 8.0, 9.0)
    assert (datum.x_axis.x, datum.x_axis.y, datum.x_axis.z) == pytest.approx(
        (half, half, 0.0)
    )
    assert (datum.y_axis.x, datum.y_axis.y, datum.y_axis.z) == pytest.approx(
        (-half, half, 0.0)
    )


@pytest.mark.parametrize(
    ("source", "target", "expected_start", "expected_end"),
    (
        (
            Transform(
                x_axis=Vector3(1.0, 0.0, 0.0),
                y_axis=Vector3(0.0, 0.0, 1.0),
                z_axis=Vector3(0.0, -1.0, 0.0),
            ),
            Transform(
                x_axis=Vector3(1.0, 0.0, 0.0),
                y_axis=Vector3(0.0, 0.0, -1.0),
                z_axis=Vector3(0.0, 1.0, 0.0),
            ),
            (2.0, -3.0),
            (5.0, -7.0),
        ),
        (
            Transform(
                x_axis=Vector3(0.0, 1.0, 0.0),
                y_axis=Vector3(0.0, 0.0, 1.0),
                z_axis=Vector3(1.0, 0.0, 0.0),
            ),
            Transform(
                x_axis=Vector3(0.0, 0.0, -1.0),
                y_axis=Vector3(0.0, 1.0, 0.0),
                z_axis=Vector3(1.0, 0.0, 0.0),
            ),
            (-3.0, 2.0),
            (-7.0, 5.0),
        ),
    ),
)
def test_native_principal_plane_reframe_preserves_world_geometry(
    source: Transform,
    target: Transform,
    expected_start: tuple[float, float],
    expected_end: tuple[float, float],
) -> None:
    geometry = LineGeometry(Vector2(2.0, 3.0), Vector2(5.0, 7.0))
    reframed = freecad_native_module._reframe_geometry(
        geometry,
        freecad_native_module._plane_reframe(source, target),
    )
    assert isinstance(reframed, LineGeometry)
    assert (reframed.start.x, reframed.start.y) == expected_start
    assert (reframed.end.x, reframed.end.y) == expected_end

    def world(transform: Transform, point: Vector2) -> tuple[float, float, float]:
        return (
            transform.origin.x
            + point.x * transform.x_axis.x
            + point.y * transform.y_axis.x,
            transform.origin.y
            + point.x * transform.x_axis.y
            + point.y * transform.y_axis.y,
            transform.origin.z
            + point.x * transform.x_axis.z
            + point.y * transform.y_axis.z,
        )

    assert world(source, geometry.start) == pytest.approx(world(target, reframed.start))
    assert world(source, geometry.end) == pytest.approx(world(target, reframed.end))


def test_pre_payload_field_fcstd_carrier_restores_payload_semantics() -> None:
    source = replace(
        neutral_document(),
        brep_payloads=(
            BrepPayload(
                "legacy-shape",
                "opencascade",
                "shape",
                "Open CASCADE 7.8",
                hashlib.sha256(b"legacy shape").hexdigest(),
                data=b"legacy shape",
                source_stream="Body.Shape.brp",
                role=PayloadRole.BREP,
                file_extension=".brep",
            ),
            BrepPayload(
                "legacy-fcstd",
                "freecad.fcstd",
                "native_document",
                "FreeCAD Schema 4",
                hashlib.sha256(b"legacy FCStd").hexdigest(),
                data=b"legacy FCStd",
                source_stream="Legacy.FCStd",
                role=PayloadRole.DOCUMENT,
                file_extension=".FCStd",
            ),
            BrepPayload(
                "legacy-history",
                "catia.v5.osmx",
                "native_feature_graph",
                "CATPrtCont",
                hashlib.sha256(b"legacy history").hexdigest(),
                data=b"legacy history",
                source_stream="1000_00000002_2",
                role=PayloadRole.FEATURE_HISTORY,
                file_extension=".osmx",
            ),
            BrepPayload(
                "legacy-tessellation",
                "catia.cgr",
                "native_tessellation",
                "CATCGRCont",
                hashlib.sha256(b"legacy tessellation").hexdigest(),
                data=b"legacy tessellation",
                source_stream="1000_00000004_4",
                role=PayloadRole.TESSELLATION,
                file_extension=".cgr",
            ),
        ),
    )
    manifest = document_to_manifest(source)
    for payload in manifest["brep_payloads"]["$tuple"]:
        payload.pop("role")
        payload.pop("file_extension")
    carrier = build_fcstd_archive(manifest)
    restored = FreeCADAdapter().read(
        carrier,
        ReadOptions(include_brep=True, include_tessellation=True),
    )
    fields = {
        payload.id: (payload.role, payload.file_extension, payload.data)
        for payload in restored.brep_payloads
    }
    assert fields == {
        "legacy-shape": (PayloadRole.BREP, ".brep", b"legacy shape"),
        "legacy-fcstd": (PayloadRole.DOCUMENT, ".FCStd", b"legacy FCStd"),
        "legacy-history": (
            PayloadRole.FEATURE_HISTORY,
            ".osmx",
            b"legacy history",
        ),
        "legacy-tessellation": (
            PayloadRole.TESSELLATION,
            ".cgr",
            b"legacy tessellation",
        ),
    }
    filtered = FreeCADAdapter().read(
        carrier,
        ReadOptions(include_brep=False, include_tessellation=False),
    )
    assert {payload.id for payload in filtered.brep_payloads} == {
        "legacy-fcstd",
        "legacy-history",
    }


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
    name: str, target: str, subelements: tuple[str, ...] = (), file: str = ""
) -> ET.Element:
    node = _native_property(
        name,
        "App::PropertyXLinkSubHidden" if subelements else "App::PropertyXLink",
        "XLink",
        {
            "file": file,
            "stamp": "",
            "name": target,
            "count": str(len(subelements)),
        },
    )
    for subelement in subelements:
        ET.SubElement(node[0], "Sub", {"value": subelement})
    return node


def _native_archive(
    objects: tuple[tuple[str, str, tuple[str, ...], tuple[ET.Element, ...]], ...],
    entries: dict[str, bytes],
    object_options: dict[str, dict[str, object]] | None = None,
) -> bytes:
    object_options = object_options or {}
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
        options = object_options.get(name, {})
        attributes = {
            "type": type_id,
            "name": name,
            "id": str(options.get("id", index)),
        }
        if bool(options.get("touched")):
            attributes["Touched"] = "1"
        ET.SubElement(
            declarations,
            "Object",
            attributes,
        )
    data = ET.SubElement(root, "ObjectData", {"Count": str(len(objects))})
    for name, _, _, properties in objects:
        options = object_options.get(name, {})
        extensions = tuple(
            value
            for value in options.get("extensions", ())
            if isinstance(value, str) and value
        )
        object_attributes = {"name": name}
        if extensions:
            object_attributes["Extensions"] = "True"
        object_node = ET.SubElement(data, "Object", object_attributes)
        if extensions:
            extension_node = ET.SubElement(
                object_node, "Extensions", {"Count": str(len(extensions))}
            )
            for extension in extensions:
                ET.SubElement(
                    extension_node,
                    "Extension",
                    {
                        "type": extension,
                        "name": extension.rsplit("::", 1)[-1],
                    },
                )
        transient_properties = tuple(
            value
            for value in options.get("transient_properties", ())
            if isinstance(value, ET.Element)
        )
        property_node = ET.SubElement(
            object_node,
            "Properties",
            {
                "Count": str(len(properties)),
                "TransientCount": str(len(transient_properties)),
            },
        )
        property_node.extend(transient_properties)
        property_node.extend(properties)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "Document.xml", ET.tostring(root, encoding="utf-8", xml_declaration=True)
        )
        for name, value in entries.items():
            archive.writestr(name, value)
    return stream.getvalue()


def _rewrite_document_xml(source: bytes, mutate) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(source)) as input_archive:
        root = ET.fromstring(input_archive.read("Document.xml"))
        mutate(root)
        document_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as output_archive:
            for info in input_archive.infolist():
                output_archive.writestr(
                    info,
                    (
                        document_xml
                        if info.filename == "Document.xml"
                        else input_archive.read(info)
                    ),
                )
    return output.getvalue()


def _mesh_kernel_fixture(endian: str = "<") -> bytes:
    vertices = ((-2.0, 3.0, 1.0), (5.0, -7.0, 4.0), (1.0, 2.0, -6.0))
    banner = (b"MESH-" * 52)[:255] + b"\n"
    result = bytearray(struct.pack(f"{endian}II", 0xA0B0C0D0, 0x00010000))
    result.extend(banner)
    result.extend(struct.pack(f"{endian}II", len(vertices), 1))
    for vertex in vertices:
        result.extend(struct.pack(f"{endian}fff", *vertex))
    result.extend(
        struct.pack(
            f"{endian}IIIIII",
            0,
            1,
            2,
            0xFFFFFFFF,
            0xFFFFFFFF,
            0xFFFFFFFF,
        )
    )
    result.extend(struct.pack(f"{endian}ffffff", -2.0, 5.0, -7.0, 3.0, -6.0, 4.0))
    return bytes(result)


def _native_mesh_fixture(endian: str = "<", inline: bool = False) -> bytes:
    mesh = _native_property("Mesh", "Mesh::PropertyMeshKernel", "Mesh")
    entries: dict[str, bytes] = {}
    if inline:
        points = ET.SubElement(mesh[0], "Points", {"Count": "3"})
        for x, y, z in ((-2, 3, 1), (5, -7, 4), (1, 2, -6)):
            ET.SubElement(points, "P", {"x": str(x), "y": str(y), "z": str(z)})
        faces = ET.SubElement(mesh[0], "Faces", {"Count": "1"})
        ET.SubElement(
            faces,
            "F",
            {
                "p0": "0",
                "p1": "1",
                "p2": "2",
                "n0": "4294967295",
                "n1": "4294967295",
                "n2": "4294967295",
            },
        )
    else:
        mesh[0].set("file", "Derived.MeshKernel.bms")
        entries["Derived.MeshKernel.bms"] = _mesh_kernel_fixture(endian)
    properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Derived Mesh"}
        ),
        mesh,
    )
    return _native_archive((("Derived", "Mesh::Import", (), properties),), entries)


def _native_part_fixture(brep_data: bytes | None = None) -> bytes:
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
        "Geometry", "Part::PropertyGeometryList", "GeometryList", {"count": "4"}
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
    ellipse = ET.SubElement(
        geometry[0],
        "Geometry",
        {"type": "Part::GeomEllipse", "id": "103", "migrated": "1"},
    )
    ET.SubElement(
        ellipse,
        "Ellipse",
        {
            "CenterX": "4",
            "CenterY": "5",
            "MajorAxisX": "1",
            "MajorAxisY": "0",
            "MajorRadius": "8",
            "MinorRadius": "3",
        },
    )
    ET.SubElement(ellipse, "Construction", {"value": "1"})
    spline = ET.SubElement(
        geometry[0],
        "Geometry",
        {"type": "Part::GeomBSplineCurve", "id": "104", "migrated": "1"},
    )
    spline_curve = ET.SubElement(
        spline,
        "BSplineCurve",
        {"Degree": "2", "Periodic": "false"},
    )
    for x, y in (("0", "0"), ("2", "4"), ("5", "1")):
        ET.SubElement(spline_curve, "Pole", {"X": x, "Y": y, "Z": "0"})
    ET.SubElement(spline, "Construction", {"value": "0"})
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
            "Second": "-3",
            "SecondPos": "3",
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
        _native_property("Label", "App::PropertyString", "String", {"value": "Sketch"}),
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
        _native_property("Label", "App::PropertyString", "String", {"value": "Pad"}),
        profile,
        _native_property("Length", "App::PropertyLength", "Float", {"value": "25"}),
        _native_property("Type", "App::PropertyEnumeration", "Integer", {"value": "0"}),
        _native_property("Reversed", "App::PropertyBool", "Bool", {"value": "false"}),
        _native_property("Midplane", "App::PropertyBool", "Bool", {"value": "false"}),
        direction,
        shape,
        pad_expressions,
    )
    body_properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "Body"}),
        _native_link_list("Group", ("Sketch", "Pad")),
        _native_property("Tip", "App::PropertyLink", "Link", {"value": "Pad"}),
    )
    brep = (
        b"\nCASCADE Topology V1, (c) Matra-Datavision\nfixture\n"
        if brep_data is None
        else brep_data
    )
    return _native_archive(
        (
            ("Body", "PartDesign::Body", ("Sketch", "Pad"), body_properties),
            ("XY_Plane", "App::Plane", (), plane_properties),
            ("Sketch", "Sketcher::SketchObject", ("XY_Plane",), sketch_properties),
            ("Pad", "PartDesign::Pad", ("Sketch", "Body"), pad_properties),
        ),
        {"Pad.Shape.brp": brep},
    )


def _native_assembly_fixture(brep_data: bytes | None = None) -> bytes:
    shape_properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "Shape"}),
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
        _native_property("Label", "App::PropertyString", "String", {"value": "Part 1"}),
        _native_xlink("LinkedObject", "Shape"),
        _native_placement(),
        _native_placement("LinkPlacement"),
        _native_property("Visibility", "App::PropertyBool", "Bool", {"value": "true"}),
    )
    grounded_proxy = _native_property(
        "Proxy",
        "App::PropertyPythonObject",
        "Python",
        {
            "value": "bnVsbA==",
            "encoded": "yes",
            "json": "yes",
        },
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
        {
            "value": "bnVsbA==",
            "encoded": "yes",
            "json": "yes",
        },
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
        _native_property("Suppressed", "App::PropertyBool", "Bool", {"value": "false"}),
    )
    joint_group_properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "Joints"}),
        _native_link_list("Group", ("Grounded", "Revolute")),
    )
    opaque_properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "Opaque"}),
        _native_property(
            "Blob",
            "App::PropertyFileIncluded",
            "File",
            {"file": "Blob.bin"},
        ),
    )
    brep = (
        b"\nCASCADE Topology V1, (c) Matra-Datavision\nassembly fixture\n"
        if brep_data is None
        else brep_data
    )
    return _native_archive(
        (
            ("Shape", "Part::Feature", (), shape_properties),
            (
                "Assembly",
                "Assembly::AssemblyObject",
                ("Joints", "PartLink", "Grounded", "Revolute"),
                assembly_properties,
            ),
            (
                "Joints",
                "Assembly::JointGroup",
                ("Grounded", "Revolute"),
                joint_group_properties,
            ),
            ("PartLink", "App::Link", ("Shape",), link_properties),
            (
                "Grounded",
                "App::FeaturePython",
                ("Assembly", "PartLink"),
                grounded_properties,
            ),
            ("Revolute", "App::FeaturePython", ("Assembly",), joint_properties),
            ("Opaque", "App::FeaturePython", (), opaque_properties),
        ),
        {"Shape.Shape.brp": brep, "Blob.bin": b"opaque"},
    )


def _native_external_assembly_fixture(
    links: tuple[tuple[str, str, str, str], ...],
    grouped_names: tuple[str, ...] | None = None,
) -> bytes:
    link_names = tuple(name for name, _, _, _ in links)
    grouped_names = link_names if grouped_names is None else grouped_names
    assembly_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "External Assembly"}
        ),
        _native_link_list("Group", grouped_names),
        _native_placement(),
    )
    objects: list[tuple[str, str, tuple[str, ...], tuple[ET.Element, ...]]] = [
        (
            "Assembly",
            "Assembly::AssemblyObject",
            grouped_names,
            assembly_properties,
        )
    ]
    for name, type_id, file, target in links:
        objects.append(
            (
                name,
                type_id,
                (),
                (
                    _native_property(
                        "Label",
                        "App::PropertyString",
                        "String",
                        {"value": name},
                    ),
                    _native_xlink("LinkedObject", target, file=file),
                    _native_placement(),
                    _native_placement("LinkPlacement"),
                    _native_property(
                        "Visibility",
                        "App::PropertyBool",
                        "Bool",
                        {"value": "true"},
                    ),
                ),
            )
        )
    return _native_archive(tuple(objects), {})


def _native_link_only_fixture(file: str, target: str = "Body") -> bytes:
    properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "External Part"}
        ),
        _native_xlink("LinkedObject", target, file=file),
        _native_placement(),
        _native_placement("LinkPlacement"),
        _native_property("Visibility", "App::PropertyBool", "Bool", {"value": "true"}),
    )
    return _native_archive((("PartLink", "App::Link", (), properties),), {})


def test_freecad_adapter_declares_exact_capabilities_and_media_type() -> None:
    adapter = FreeCADAdapter()
    assert adapter.info is INFO
    assert FORMAT_ID == INFO.format_id
    assert (SUFFIX,) == INFO.extensions
    assert adapter.info.capabilities == frozenset(Capability)
    assert set(CAPABILITY_WRITE_TYPE_IDS) == set(Capability)
    assert set(CAPABILITY_CARRIER_REASONS) == set(Capability)
    assert all(
        isinstance(type_ids, frozenset)
        for type_ids in CAPABILITY_WRITE_TYPE_IDS.values()
    )
    assert all(
        isinstance(reason, CarrierReason)
        for reason in CAPABILITY_CARRIER_REASONS.values()
    )
    with pytest.raises(TypeError):
        CAPABILITY_WRITE_TYPE_IDS[Capability.PARAMETERS] = frozenset()
    with pytest.raises(TypeError):
        CAPABILITY_CARRIER_REASONS[Capability.PARAMETERS] = (
            CarrierReason.TARGET_UNSUPPORTED
        )
    assert NATIVE_CAPABILITIES == frozenset(
        capability
        for capability, type_ids in CAPABILITY_WRITE_TYPE_IDS.items()
        if type_ids
    )
    assert adapter.info.native_capabilities == NATIVE_CAPABILITIES
    assert adapter.info.media_types == ("application/x-extension-fcstd",)


def test_freecad_format_identity_has_one_literal_source() -> None:
    for module in (
        freecad_adapter_module,
        freecad_archive_module,
        freecad_native_module,
    ):
        source = inspect.getsource(module)
        assert '"freecad.fcstd"' not in source
        assert '".FCStd"' not in source
        assert '".fcstd"' not in source


def test_freecad_protocol_registries_are_exact_and_exhaustive() -> None:
    assert freecad_archive_module.DOCUMENT_ENTRY == "Document.xml"
    assert ASSEMBLY_OBJECT_TYPE_PREFIX == "Assembly::"
    assert ASSEMBLY_ROOT_TYPE_ID == "Assembly::AssemblyObject"
    assert ASSEMBLY_JOINT_GROUP_TYPE_ID == "Assembly::JointGroup"
    assert ASSEMBLY_LINK_TYPE_ID == "Assembly::AssemblyLink"
    assert APP_LINK_TYPE_ID == "App::Link"
    assert APP_PART_TYPE_ID == "App::Part"
    assert BODY_TYPE_ID == "PartDesign::Body"
    assert SKETCH_TYPE_ID == "Sketcher::SketchObject"
    assert PART_CONTAINER_TYPE_IDS == frozenset({"Part::BodyBase", BODY_TYPE_ID})
    assert BODY_CONTAINER_TYPE_IDS == PART_CONTAINER_TYPE_IDS | {APP_PART_TYPE_ID}
    assert NON_FEATURE_OBJECT_TYPE_IDS == BODY_CONTAINER_TYPE_IDS | {SKETCH_TYPE_ID}
    assert STRING_HASHER_TAGS == frozenset({"StringHasher", "StringHasher2"})
    assert JOINT_GROUND_PROPERTY == "ObjectToGround"
    assert JOINT_REFERENCE_PROPERTIES == ("Reference1", "Reference2")
    assert JOINT_REFERENCE_INDEX_BY_PROPERTY == {
        name: index for index, name in enumerate(JOINT_REFERENCE_PROPERTIES)
    }
    assert JOINT_RESERVED_LINK_PROPERTIES == frozenset(
        (JOINT_GROUND_PROPERTY, *JOINT_REFERENCE_PROPERTIES)
    )
    assert JOINT_TYPE_PROPERTIES == frozenset({"JointType", "MateType"})
    assert ASSEMBLY_CONNECTOR_PROPERTY_PREFIXES == ("Reference", "Placement")
    assert XML_TRUE_VALUES == frozenset({"1", "true"})
    assert PERMISSIVE_TRUE_VALUES == XML_TRUE_VALUES | {"yes"}
    assert SPLINE_CONTROL_TAGS == frozenset({"Pole", "Knot"})
    assert SUBELEMENT_KIND_BY_PREFIX == {
        kind.value.title(): kind for kind in SUBELEMENT_MATE_ENTITY_KINDS
    }
    assert SUPPORT_PLANE_TYPE_IDS == frozenset(
        {"App::Plane", "Part::DatumPlane", "PartDesign::Plane"}
    )
    assert len(QUANTITY_PROPERTY_UNITS) == 59
    assert (
        hashlib.sha256(
            json.dumps(
                sorted(QUANTITY_PROPERTY_UNITS.items()), separators=(",", ":")
            ).encode()
        ).hexdigest()
        == "e9cb0cb88f8f8cc431a538b891c20635bc685f8800d7118b53881be35839c8b8"
    )
    assert len({value.type_id for value in SCALAR_PROPERTY_TYPES}) == len(
        SCALAR_PROPERTY_TYPES
    )
    assert SCALAR_PROPERTY_KINDS == {
        **{
            f"App::Property{name}": (ValueKind.QUANTITY, unit, "Float")
            for name, unit in QUANTITY_PROPERTY_UNITS.items()
        },
        **{
            value.type_id: (value.value_kind, value.unit, value.value_tag)
            for value in SCALAR_PROPERTY_TYPES
        },
    }
    assert len(SCALAR_PROPERTY_KINDS) == 74
    assert len(FEATURE_TYPES) == 93
    assert len({value.type_id for value in FEATURE_TYPES}) == len(FEATURE_TYPES)
    assert FEATURE_KIND_BY_TYPE_ID == {
        value.type_id: value.kind for value in FEATURE_TYPES
    }
    assert tuple(value.operation for value in BOOLEAN_OPERATION_TYPES) == tuple(
        BooleanOperation
    )
    assert BOOLEAN_OPERATION_TYPE_BY_KIND == {
        value.operation.value: value for value in BOOLEAN_OPERATION_TYPES
    }
    assert CREATE_OPERATION_NAMES == frozenset({"", BooleanOperation.CREATE.value})
    assert set(FEATURE_WRITE_TYPE_IDS) == set(FeatureKind)
    assert FEATURE_WRITE_KINDS == frozenset(
        kind for kind, type_ids in FEATURE_WRITE_TYPE_IDS.items() if type_ids
    )
    assert FEATURE_CARRIER_KINDS == frozenset(FeatureKind) - FEATURE_WRITE_KINDS
    assert FEATURE_WRITE_KINDS | FEATURE_CARRIER_KINDS == set(FeatureKind)
    assert FEATURE_WRITE_KINDS.isdisjoint(FEATURE_CARRIER_KINDS)
    assert FEATURE_WRITE_TYPE_IDS[FeatureKind.EXTRUSION] == frozenset(
        value.type_id for value in BOOLEAN_OPERATION_TYPES
    )
    assert {
        value.type_id for value in BOOLEAN_OPERATION_TYPES
    } <= FEATURE_KIND_BY_TYPE_ID.keys()
    assert tuple(value.code for value in EXTRUSION_TYPES) == tuple(range(6))
    assert EXTRUSION_TYPE_BY_CODE == {value.code: value for value in EXTRUSION_TYPES}
    assert POCKET_TYPE_ID == "PartDesign::Pocket"
    assert EXTRUSION_TYPE_BY_CODE[1].end_condition == ExtrusionEndCondition.UP_TO_LAST
    assert (
        EXTRUSION_TYPE_BY_CODE[1].pocket_end_condition
        == ExtrusionEndCondition.THROUGH_ALL
    )
    assert len(PRIMITIVE_FEATURE_TYPE_IDS) == 39
    assert PRIMITIVE_FEATURE_TYPE_IDS == frozenset(
        f"{family.namespace}::{prefix}{shape}"
        for family in PRIMITIVE_FEATURE_FAMILIES
        for prefix in family.prefixes
        for shape in family.shapes
    )
    assert PART_OBJECT_TYPE_IDS == frozenset(
        (
            *FEATURE_KIND_BY_TYPE_ID,
            *PRIMITIVE_FEATURE_TYPE_IDS,
            *SUPPORT_PLANE_TYPE_IDS,
            *BODY_CONTAINER_TYPE_IDS,
        )
    )
    assert len(PART_OBJECT_TYPE_IDS) == 138
    assert (
        hashlib.sha256(
            json.dumps(sorted(PART_OBJECT_TYPE_IDS), separators=(",", ":")).encode()
        ).hexdigest()
        == "589bb6d7434a0fd03697172fe47b83a3385d0a9069aecf014e9de3715f1b1c8e"
    )
    assert ADDITIONAL_PART_OBJECT_TYPE_IDS == frozenset(
        {"App::Plane", "Part::FeatureGeometrySet"}
    )
    assert REGISTERED_PART_OBJECT_TYPE_IDS == (
        PART_OBJECT_TYPE_IDS - ADDITIONAL_PART_OBJECT_TYPE_IDS
    )
    assert len(REGISTERED_PART_OBJECT_TYPE_IDS) == 136
    assert (
        hashlib.sha256(
            json.dumps(
                sorted(REGISTERED_PART_OBJECT_TYPE_IDS), separators=(",", ":")
            ).encode()
        ).hexdigest()
        == "5d46a78532f802c86552b56704f5238758e098dd1afb4ce9802b4ffc78649993"
    )
    assert CONSTRAINT_POINT_BY_INDEX == {
        value.index: value.name for value in CONSTRAINT_POINTS
    }
    assert CONSTRAINT_POINT_INDEX_BY_NAME == {
        name: value.index
        for value in CONSTRAINT_POINTS
        for name in (value.name, *value.aliases)
    }
    assert MIDPOINT_REFERENCE_POINT_NAMES == frozenset(
        {
            "",
            "mid",
            *(
                name
                for value in CONSTRAINT_POINTS
                if value.index == 3
                for name in (value.name, *value.aliases)
            ),
        }
    )
    assert tuple(value.code for value in CONSTRAINT_TYPES) == tuple(range(1, 22))
    assert CONSTRAINT_KIND_BY_CODE == {
        value.code: value.kind for value in CONSTRAINT_TYPES
    }
    assert CONSTRAINT_VALUE_KIND_BY_CODE == {
        value.code: (value.value_kind, value.unit)
        for value in CONSTRAINT_TYPES
        if value.value_kind is not None
    }
    assert DIMENSIONAL_CONSTRAINT_CODES == frozenset(
        value.code for value in CONSTRAINT_TYPES if value.value_kind is not None
    )
    assert FIXED_CONSTRAINT_KINDS == frozenset(
        kind
        for kind, code in CONSTRAINT_CODE_BY_KIND.items()
        if code == CONSTRAINT_CODE_BY_KIND[ConstraintKind.BLOCK.value]
    )
    assert set(CONSTRAINT_KIND_BY_CODE.values()) == set(ConstraintKind) - {
        ConstraintKind.CONCENTRIC,
        ConstraintKind.FIXED,
        ConstraintKind.MIDPOINT,
        ConstraintKind.NATIVE,
    }
    assert set(CONSTRAINT_CODE_BY_KIND) == {
        value.value
        for value in ConstraintKind
        if value not in {ConstraintKind.MIDPOINT, ConstraintKind.NATIVE}
    }
    assert set(CONSTRAINT_WRITE_CODES) == set(ConstraintKind)
    assert CONSTRAINT_WRITE_KINDS == frozenset(
        kind for kind, codes in CONSTRAINT_WRITE_CODES.items() if codes
    )
    assert CONSTRAINT_COMPOSED_KINDS == frozenset(
        {
            ConstraintKind.CONCENTRIC,
            ConstraintKind.FIXED,
            ConstraintKind.MIDPOINT,
        }
    )
    assert CONSTRAINT_DIRECT_KINDS == (
        CONSTRAINT_WRITE_KINDS - CONSTRAINT_COMPOSED_KINDS
    )
    assert CONSTRAINT_CARRIER_KINDS == frozenset(ConstraintKind) - (
        CONSTRAINT_DIRECT_KINDS | CONSTRAINT_COMPOSED_KINDS
    )
    assert CONSTRAINT_WRITE_KINDS | CONSTRAINT_CARRIER_KINDS == set(ConstraintKind)
    assert CONSTRAINT_WRITE_KINDS.isdisjoint(CONSTRAINT_CARRIER_KINDS)
    assert len({value.type_id for value in GEOMETRY_TYPES}) == len(GEOMETRY_TYPES)
    assert set(GEOMETRY_KIND_BY_TYPE_ID.values()) == set(GeometryKind) - {
        GeometryKind.NATIVE
    }
    assert set(GEOMETRY_TYPE_IDS_BY_KIND) == {
        value.value for value in GeometryKind if value != GeometryKind.NATIVE
    }
    neutral_geometry_kinds = {
        value.kind.value for value in GEOMETRY_TYPES if value.neutral_default
    }
    assert set(NEUTRAL_GEOMETRY_TYPE_BY_KIND) == neutral_geometry_kinds
    assert set(NEUTRAL_GEOMETRY_TYPE_ID_BY_KIND) == neutral_geometry_kinds
    assert set(GEOMETRY_WRITE_TYPE_IDS) == set(GeometryKind)
    assert GEOMETRY_WRITE_KINDS == frozenset(
        kind for kind, type_ids in GEOMETRY_WRITE_TYPE_IDS.items() if type_ids
    )
    assert GEOMETRY_CARRIER_KINDS == frozenset(GeometryKind) - GEOMETRY_WRITE_KINDS
    assert GEOMETRY_WRITE_KINDS | GEOMETRY_CARRIER_KINDS == set(GeometryKind)
    assert GEOMETRY_WRITE_KINDS.isdisjoint(GEOMETRY_CARRIER_KINDS)
    assert CIRCULAR_GEOMETRY_KINDS == frozenset(
        {GeometryKind.CIRCLE.value, GeometryKind.ARC.value}
    )
    assert SPLINE_GEOMETRY_KINDS == frozenset(
        {GeometryKind.BEZIER.value, GeometryKind.SPLINE.value}
    )
    assert SPLINE_GEOMETRY_TYPE_IDS == frozenset(
        value.type_id
        for value in GEOMETRY_TYPES
        if value.kind.value in SPLINE_GEOMETRY_KINDS
    )
    assert len({value.name for value in JOINT_TYPE_DEFINITIONS}) == len(
        JOINT_TYPE_DEFINITIONS
    )
    assert set(MATE_KIND_BY_JOINT_TYPE) == set(JOINT_TYPES)
    assert set(MATE_KIND_BY_JOINT_TYPE.values()) == {
        value.kind for value in JOINT_TYPE_DEFINITIONS
    }
    carrier_only_mates = {
        MateKind.COINCIDENT,
        MateKind.TANGENT,
        MateKind.COORDINATE,
        MateKind.UNIVERSAL_JOINT,
        MateKind.CAM,
        MateKind.SLOT,
        MateKind.WIDTH,
        MateKind.SYMMETRIC,
        MateKind.LINEAR_COUPLER,
        MateKind.PATH,
        MateKind.MAGNETIC,
        MateKind.PROFILE_CENTER,
        MateKind.NATIVE,
    }
    supported_mates = {
        value for value in MateKind if value.value in JOINT_TYPE_BY_MATE_KIND
    }
    assert supported_mates.isdisjoint(carrier_only_mates)
    assert supported_mates | carrier_only_mates == set(MateKind)
    assert set(MATE_WRITE_TYPES) == set(MateKind)
    assert MATE_WRITE_KINDS == frozenset(
        kind for kind, types in MATE_WRITE_TYPES.items() if types
    )
    assert MATE_CARRIER_KINDS == frozenset(MateKind) - MATE_WRITE_KINDS
    assert MATE_WRITE_KINDS == supported_mates
    assert MATE_CARRIER_KINDS == carrier_only_mates
    assert MATE_WRITE_KINDS.isdisjoint(MATE_CARRIER_KINDS)
    assert JOINT_TYPES_USING_DISTANCE == frozenset(
        value.name for value in JOINT_TYPE_DEFINITIONS if value.uses_distance
    )
    assert JOINT_TYPES_USING_SECOND_DISTANCE == frozenset(
        value.name for value in JOINT_TYPE_DEFINITIONS if value.uses_second_distance
    )
    assert MATE_KINDS_USING_DISTANCE == frozenset(
        value.kind for value in JOINT_TYPE_DEFINITIONS if value.uses_distance
    )
    assert MATE_KINDS_USING_SECOND_DISTANCE == frozenset(
        value.kind for value in JOINT_TYPE_DEFINITIONS if value.uses_second_distance
    )


def test_brep_filter_removes_only_brep_payload_roles() -> None:
    payloads = tuple(
        BrepPayload(
            f"payload:{role.value}",
            "test.payload",
            role.value,
            "1",
            hashlib.sha256(role.value.encode("ascii")).hexdigest(),
            data=role.value.encode("ascii"),
            role=role,
        )
        for role in PayloadRole
    )
    source = neutral_document()
    document = replace(
        source,
        brep_payloads=payloads,
        capabilities=source.capabilities
        | {
            Capability.BREP,
            Capability.TESSELLATION,
            Capability.NATIVE_PAYLOADS,
        },
    )
    filtered = _filtered_document(
        document,
        ReadOptions(include_brep=False, include_tessellation=True),
    )
    assert {payload.role for payload in filtered.brep_payloads} == set(PayloadRole) - {
        PayloadRole.BREP
    }
    assert Capability.BREP not in filtered.capabilities
    assert Capability.TESSELLATION in filtered.capabilities
    assert Capability.NATIVE_PAYLOADS in filtered.capabilities


def test_encodable_neutral_brep_transfer_is_native_with_faceted_display() -> None:
    source = replace(neutral_document(), brep=triangle_brep())
    adapter = FreeCADAdapter()
    carrier_output = io.BytesIO()
    carrier_result = adapter.write(source, carrier_output)
    carrier_transfers = {
        transfer.capability: transfer for transfer in carrier_result.transfers
    }
    assert carrier_transfers[Capability.BREP].mode == TransferMode.NATIVE
    assert carrier_transfers[Capability.BREP].carrier_reason is None
    assert adapter.read(carrier_output.getvalue()) == source
    mesh = Mesh(
        "mesh:brep-display",
        "BRep display",
        (
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        ),
        ((0, 1, 2),),
    )
    displayed = replace(source, meshes=(mesh,))
    mixed_output = io.BytesIO()
    mixed_result = adapter.write(displayed, mixed_output)
    mixed_transfers = {
        transfer.capability: transfer for transfer in mixed_result.transfers
    }
    assert mixed_transfers[Capability.BREP].mode == TransferMode.NATIVE
    assert mixed_transfers[Capability.BREP].carrier_reason is None
    assert mixed_transfers[Capability.TESSELLATION].mode == TransferMode.NATIVE
    with zipfile.ZipFile(io.BytesIO(mixed_output.getvalue())) as archive:
        shape_entries = [name for name in archive.namelist() if name.endswith(".brp")]
        assert shape_entries
        assert all(
            b"CASCADE Topology V" in archive.read(name)[:512] for name in shape_entries
        )
    assert adapter.read(mixed_output.getvalue()) == displayed


def test_non_open_cascade_brep_bytes_are_never_bound_as_freecad_shapes() -> None:
    source = neutral_document()
    payload = BrepPayload(
        "foreign:brep",
        "parasolid.x_b",
        "shape",
        "SCH_3500040",
        hashlib.sha256(b"PS\x00\x00foreign").hexdigest(),
        data=b"PS\x00\x00foreign",
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )
    document = replace(source, brep_payloads=(payload,))
    output = io.BytesIO()
    result = FreeCADAdapter().write(document, output)
    transfers = {transfer.capability: transfer for transfer in result.transfers}
    assert transfers[Capability.BREP].mode == TransferMode.CARRIER
    assert transfers[Capability.BREP].carrier_reason is CarrierReason.SOURCE_OPAQUE
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
        shape_files = {
            node.get("file", "")
            for node in root.findall(
                ".//Property[@type='Part::PropertyPartShape']/Part"
            )
            if node.get("file", "")
        }
        assert shape_files == set()
        assert archive.read("interchange/native/foreign_brep.x_b") == payload.data
    assert FreeCADAdapter().read(output.getvalue()) == document


def test_solidworks_opaque_brep_with_executable_history_is_application_usable() -> None:
    source = neutral_document()
    circle = SketchEntity(
        "sketch:1:circle:1",
        GeometryKind.CIRCLE,
        CircleGeometry(Vector2(0.0, 0.0), 10.0),
    )
    sketch = replace(
        source.sketches[0],
        entities=(circle,),
        constraints=(),
        closed_profile_entity_ids=((circle.id,),),
    )
    feature = replace(
        source.feature_timeline[0],
        definition=ExtrusionFeature(ParameterValue(5.0, ValueKind.LENGTH, "mm")),
    )
    data = b"PS\x00\x00opaque-source"
    payload = BrepPayload(
        "solidworks:brep",
        "parasolid.x_b",
        "partition",
        "SCH_3500040",
        hashlib.sha256(data).hexdigest(),
        data=data,
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )
    document = replace(
        source,
        source=replace(source.source, format_id="solidworks.sldprt"),
        sketches=(sketch,),
        feature_timeline=(feature,),
        brep_payloads=(payload,),
    )
    output = io.BytesIO()
    result = FreeCADAdapter().write(document, output)
    assert result.application_usable is True
    assert (
        freecad_archive_module.native_shape_feature_count(
            document_to_manifest(document)
        )
        == 1
    )


def test_decoded_brep_and_retained_source_payload_are_accounted_once() -> None:
    source = neutral_document()
    data = b"PS\x00\x00retained-source"
    payload = BrepPayload(
        "source:brep",
        "parasolid.x_b",
        "partition",
        "SCH_3500040",
        hashlib.sha256(data).hexdigest(),
        data=data,
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )
    document = replace(source, brep=triangle_brep(), brep_payloads=(payload,))
    output = io.BytesIO()
    result = FreeCADAdapter().write(document, output)
    transfers = {transfer.capability: transfer for transfer in result.transfers}
    assert transfers[Capability.BREP].mode is TransferMode.NATIVE
    assert transfers[Capability.BREP].carrier_reason is None
    assert transfers[Capability.NATIVE_PAYLOADS].mode is TransferMode.CARRIER
    assert (
        transfers[Capability.NATIVE_PAYLOADS].carrier_reason
        is CarrierReason.TARGET_UNSUPPORTED
    )
    assert FreeCADAdapter().read(output.getvalue()) == document


def test_duplicate_reference_and_housekeeping_nodes_do_not_degrade_history() -> None:
    source = neutral_document()
    reference = FeatureStep(
        "feature:reference-plane",
        "Reference plane",
        FeatureKind.REFERENCE,
        1,
        attributes={"native_type": "Plane"},
    )
    housekeeping = FeatureStep(
        "feature:comments",
        "Comments",
        FeatureKind.NATIVE,
        2,
        attributes={"native_type": "Comments"},
    )
    document = replace(
        source,
        feature_timeline=(*source.feature_timeline, reference, housekeeping),
    )
    document.assert_valid()
    baseline = FreeCADAdapter().write(source, io.BytesIO())
    result = FreeCADAdapter().write(document, io.BytesIO())
    baseline_transfers = {
        transfer.capability: transfer for transfer in baseline.transfers
    }
    transfers = {transfer.capability: transfer for transfer in result.transfers}
    assert (
        transfers[Capability.PARAMETRIC_HISTORY]
        == baseline_transfers[Capability.PARAMETRIC_HISTORY]
    )


def test_native_capabilities_follow_restored_sections() -> None:
    document = FreeCADAdapter().read(_native_part_fixture())
    assert document.capabilities == frozenset(
        {
            Capability.PARAMETERS,
            Capability.PARAMETRIC_HISTORY,
            Capability.SUPPORT_PLANES,
            Capability.EDITABLE_SKETCHES,
            Capability.BODY_STRUCTURE,
            Capability.CONFIGURATIONS,
            Capability.EXPRESSIONS,
            Capability.BREP,
            Capability.NATIVE_PAYLOADS,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
        }
    )
    assert Capability.MATERIALS not in document.capabilities
    assembly = FreeCADAdapter().read(_native_assembly_fixture())
    assert assembly.capabilities == frozenset(
        {
            Capability.PARAMETERS,
            Capability.CONFIGURATIONS,
            Capability.BREP,
            Capability.ASSEMBLIES,
            Capability.ASSEMBLY_MATES,
            Capability.COMPONENT_DOCUMENTS,
            Capability.NATIVE_PAYLOADS,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
        }
    )


# native chamfer properties must become a semantic editable feature definition
def test_native_equal_distance_chamfer_is_semantic() -> None:
    # the fixture mutation adds the exact PartDesign history and property contracts
    def AddChamfer(RootData: ET.Element) -> None:
        ObjectsData = RootData.find("./Objects")
        ObjectData = RootData.find("./ObjectData")
        assert ObjectsData is not None
        assert ObjectData is not None
        ObjectsData.set("Count", str(int(ObjectsData.get("Count", "0")) + 1))
        ObjectData.set("Count", str(int(ObjectData.get("Count", "0")) + 1))
        BodyDeps = ObjectsData.find("./ObjectDeps[@Name='Body']")
        assert BodyDeps is not None
        ET.SubElement(BodyDeps, "Dep", {"Name": "Chamfer"})
        BodyDeps.set("Count", str(int(BodyDeps.get("Count", "0")) + 1))
        ChamferDeps = ET.SubElement(
            ObjectsData,
            "ObjectDeps",
            {"Name": "Chamfer", "Count": "2"},
        )
        ET.SubElement(ChamferDeps, "Dep", {"Name": "Pad"})
        ET.SubElement(ChamferDeps, "Dep", {"Name": "Body"})
        ET.SubElement(
            ObjectsData,
            "Object",
            {"type": "PartDesign::Chamfer", "name": "Chamfer", "id": "5"},
        )
        BodyProperties = ObjectData.find("./Object[@name='Body']/Properties")
        assert BodyProperties is not None
        GroupData = BodyProperties.find("./Property[@name='Group']/LinkList")
        TipData = BodyProperties.find("./Property[@name='Tip']/Link")
        assert GroupData is not None
        assert TipData is not None
        ET.SubElement(GroupData, "Link", {"value": "Chamfer"})
        GroupData.set("count", str(int(GroupData.get("count", "0")) + 1))
        TipData.set("value", "Chamfer")
        BaseData = _native_property(
            "Base",
            "App::PropertyLinkSub",
            "LinkSub",
            {"value": "Pad", "count": "1"},
        )
        ET.SubElement(BaseData[0], "Sub", {"value": "Edge5"})
        PropertiesData = (
            _native_property(
                "Label", "App::PropertyString", "String", {"value": "Chamfer"}
            ),
            BaseData,
            _native_property(
                "BaseFeature", "App::PropertyLink", "Link", {"value": "Pad"}
            ),
            _native_property(
                "Size",
                "App::PropertyQuantityConstraint",
                "Float",
                {"value": "2"},
            ),
            _native_property(
                "Size2",
                "App::PropertyQuantityConstraint",
                "Float",
                {"value": "1"},
            ),
            _native_property("Angle", "App::PropertyAngle", "Float", {"value": "45"}),
            _native_property(
                "ChamferType",
                "App::PropertyEnumeration",
                "Integer",
                {"value": "0"},
            ),
            _native_property(
                "FlipDirection",
                "App::PropertyBool",
                "Bool",
                {"value": "false"},
            ),
            _native_property(
                "UseAllEdges",
                "App::PropertyBool",
                "Bool",
                {"value": "false"},
            ),
        )
        ChamferData = ET.SubElement(ObjectData, "Object", {"name": "Chamfer"})
        ChamferProperties = ET.SubElement(
            ChamferData,
            "Properties",
            {"Count": str(len(PropertiesData)), "TransientCount": "0"},
        )
        ChamferProperties.extend(PropertiesData)

    DocumentData = FreeCADAdapter().read(
        _rewrite_document_xml(_native_part_fixture(), AddChamfer)
    )
    ChamferData = next(
        ItemData
        for ItemData in DocumentData.feature_timeline
        if ItemData.kind == FeatureKind.CHAMFER
    )
    assert isinstance(ChamferData.definition, ChamferFeature)
    assert ChamferData.definition.distance == ParameterValue(
        2.0,
        ValueKind.LENGTH,
        "mm",
    )
    assert ChamferData.definition.mode == "equal_distance"
    assert ChamferData.definition.second_distance is None
    assert ChamferData.definition.angle is None
    assert ChamferData.input_feature_ids == ("freecad:feature:Pad",)
    assert len(ChamferData.selection_ids) == 1
    SelectionData = next(
        ItemData
        for ItemData in DocumentData.selections
        if ItemData.id == ChamferData.selection_ids[0]
    )
    assert SelectionData.path[0].entity_kind == "edge"
    assert SelectionData.path[0].subelement == "Edge5"


# native thickness properties must become an inward editable shell definition
def test_native_inward_thickness_is_semantic() -> None:
    # the fixture mutation adds the exact source links needed by shell semantics
    def AddThickness(RootData: ET.Element) -> None:
        ObjectsData = RootData.find("./Objects")
        ObjectData = RootData.find("./ObjectData")
        assert ObjectsData is not None
        assert ObjectData is not None
        ObjectsData.set("Count", str(int(ObjectsData.get("Count", "0")) + 1))
        ObjectData.set("Count", str(int(ObjectData.get("Count", "0")) + 1))
        BodyDeps = ObjectsData.find("./ObjectDeps[@Name='Body']")
        assert BodyDeps is not None
        ET.SubElement(BodyDeps, "Dep", {"Name": "Thickness"})
        BodyDeps.set("Count", str(int(BodyDeps.get("Count", "0")) + 1))
        ThicknessDeps = ET.SubElement(
            ObjectsData,
            "ObjectDeps",
            {"Name": "Thickness", "Count": "2"},
        )
        ET.SubElement(ThicknessDeps, "Dep", {"Name": "Pad"})
        ET.SubElement(ThicknessDeps, "Dep", {"Name": "Body"})
        ET.SubElement(
            ObjectsData,
            "Object",
            {"type": "PartDesign::Thickness", "name": "Thickness", "id": "5"},
        )
        BodyProperties = ObjectData.find("./Object[@name='Body']/Properties")
        assert BodyProperties is not None
        GroupData = BodyProperties.find("./Property[@name='Group']/LinkList")
        TipData = BodyProperties.find("./Property[@name='Tip']/Link")
        assert GroupData is not None
        assert TipData is not None
        ET.SubElement(GroupData, "Link", {"value": "Thickness"})
        GroupData.set("count", str(int(GroupData.get("count", "0")) + 1))
        TipData.set("value", "Thickness")
        BaseData = _native_property(
            "Base",
            "App::PropertyLinkSub",
            "LinkSub",
            {"value": "Pad", "count": "1"},
        )
        ET.SubElement(BaseData[0], "Sub", {"value": "Face6"})
        PropertiesData = (
            _native_property(
                "Label", "App::PropertyString", "String", {"value": "Thickness"}
            ),
            BaseData,
            _native_property(
                "BaseFeature", "App::PropertyLink", "Link", {"value": "Pad"}
            ),
            _native_property(
                "Value",
                "App::PropertyQuantityConstraint",
                "Float",
                {"value": "2"},
            ),
            _native_property(
                "Reversed", "App::PropertyBool", "Bool", {"value": "true"}
            ),
        )
        ThicknessData = ET.SubElement(ObjectData, "Object", {"name": "Thickness"})
        ThicknessProperties = ET.SubElement(
            ThicknessData,
            "Properties",
            {"Count": str(len(PropertiesData)), "TransientCount": "0"},
        )
        ThicknessProperties.extend(PropertiesData)

    DocumentData = FreeCADAdapter().read(
        _rewrite_document_xml(_native_part_fixture(), AddThickness)
    )
    ShellData = next(
        ItemData
        for ItemData in DocumentData.feature_timeline
        if ItemData.kind == FeatureKind.SHELL
    )
    assert isinstance(ShellData.definition, ShellFeature)
    assert ShellData.definition.thickness == ParameterValue(
        2.0,
        ValueKind.LENGTH,
        "mm",
    )
    assert ShellData.definition.outward is False
    assert ShellData.input_feature_ids == ("freecad:feature:Pad",)
    assert len(ShellData.selection_ids) == 1
    SelectionData = next(
        ItemData
        for ItemData in DocumentData.selections
        if ItemData.id == ShellData.selection_ids[0]
    )
    assert SelectionData.path[0].entity_kind == "face"
    assert SelectionData.path[0].subelement == "Face6"


def test_native_partdesign_linear_pattern_restores_parametric_semantics() -> None:
    def AddLinearPattern(DocumentRoot: ET.Element) -> None:
        ObjectData = DocumentRoot.find("./ObjectData")
        ObjectsData = DocumentRoot.find("./Objects")
        assert ObjectData is not None
        assert ObjectsData is not None
        ObjectsData.set("Count", str(int(ObjectsData.get("Count", "0")) + 1))
        ObjectData.set("Count", str(int(ObjectData.get("Count", "0")) + 1))
        BodyDeps = ObjectsData.find("./ObjectDeps[@Name='Body']")
        assert BodyDeps is not None
        ET.SubElement(BodyDeps, "Dep", {"Name": "LinearPattern"})
        BodyDeps.set("Count", str(int(BodyDeps.get("Count", "0")) + 1))
        PatternDeps = ET.SubElement(
            ObjectsData,
            "ObjectDeps",
            {"Name": "LinearPattern", "Count": "3"},
        )
        for DependencyName in ("Pad", "Sketch", "Body"):
            ET.SubElement(PatternDeps, "Dep", {"Name": DependencyName})
        ET.SubElement(
            ObjectsData,
            "Object",
            {"type": "PartDesign::LinearPattern", "name": "LinearPattern", "id": "5"},
        )
        BodyProperties = ObjectData.find("./Object[@name='Body']/Properties")
        assert BodyProperties is not None
        GroupData = BodyProperties.find("./Property[@name='Group']/LinkList")
        TipData = BodyProperties.find("./Property[@name='Tip']/Link")
        assert GroupData is not None
        assert TipData is not None
        ET.SubElement(GroupData, "Link", {"value": "LinearPattern"})
        GroupData.set("count", str(int(GroupData.get("count", "0")) + 1))
        TipData.set("value", "LinearPattern")
        OriginalsData = _native_property(
            "Originals",
            "App::PropertyLinkList",
            "LinkList",
            {"count": "1"},
        )
        ET.SubElement(OriginalsData[0], "Link", {"value": "Pad"})
        DirectionData = _native_property(
            "Direction",
            "App::PropertyLinkSub",
            "LinkSub",
            {"value": "Sketch", "count": "1"},
        )
        ET.SubElement(DirectionData[0], "Sub", {"value": "N_Axis"})
        PropertiesData = (
            _native_property(
                "Label", "App::PropertyString", "String", {"value": "LinearPattern"}
            ),
            OriginalsData,
            DirectionData,
            _native_property("Length", "App::PropertyLength", "Float", {"value": "10"}),
            _native_property("Offset", "App::PropertyLength", "Float", {"value": "5"}),
            _native_property(
                "Occurrences", "App::PropertyInteger", "Integer", {"value": "3"}
            ),
            _native_property(
                "Mode", "App::PropertyEnumeration", "Integer", {"value": "0"}
            ),
            _native_property(
                "Reversed", "App::PropertyBool", "Bool", {"value": "false"}
            ),
        )
        PatternData = ET.SubElement(ObjectData, "Object", {"name": "LinearPattern"})
        PatternProperties = ET.SubElement(
            PatternData,
            "Properties",
            {"Count": str(len(PropertiesData)), "TransientCount": "0"},
        )
        PatternProperties.extend(PropertiesData)

    DocumentData = FreeCADAdapter().read(
        _rewrite_document_xml(_native_part_fixture(), AddLinearPattern)
    )
    PatternData = next(
        ItemData
        for ItemData in DocumentData.feature_timeline
        if ItemData.kind == FeatureKind.PATTERN
    )
    assert isinstance(PatternData.definition, LinearPatternFeature)
    assert PatternData.definition.spacing == ParameterValue(
        5.0,
        ValueKind.LENGTH,
        "mm",
    )
    assert PatternData.definition.instance_count == 3
    assert PatternData.definition.reversed is False
    assert PatternData.input_feature_ids == ("freecad:feature:Pad",)
    assert PatternData.selection_ids == (PatternData.definition.direction_selection_id,)
    SelectionData = next(
        ItemData
        for ItemData in DocumentData.selections
        if ItemData.id == PatternData.definition.direction_selection_id
    )
    assert SelectionData.path[0].entity_kind == "native"
    assert SelectionData.path[0].entity_id == "Sketch"
    assert SelectionData.path[0].subelement == "N_Axis"
    assert DocumentData.bodies[0].final_feature_id == PatternData.id


def test_native_partdesign_polar_pattern_restores_parametric_semantics() -> None:
    def AddPolarPattern(DocumentRoot: ET.Element) -> None:
        ObjectData = DocumentRoot.find("./ObjectData")
        ObjectsData = DocumentRoot.find("./Objects")
        assert ObjectData is not None
        assert ObjectsData is not None
        ObjectsData.set("Count", str(int(ObjectsData.get("Count", "0")) + 1))
        ObjectData.set("Count", str(int(ObjectData.get("Count", "0")) + 1))
        BodyDeps = ObjectsData.find("./ObjectDeps[@Name='Body']")
        assert BodyDeps is not None
        ET.SubElement(BodyDeps, "Dep", {"Name": "PolarPattern"})
        BodyDeps.set("Count", str(int(BodyDeps.get("Count", "0")) + 1))
        PatternDeps = ET.SubElement(
            ObjectsData,
            "ObjectDeps",
            {"Name": "PolarPattern", "Count": "3"},
        )
        for DependencyName in ("Pad", "Sketch", "Body"):
            ET.SubElement(PatternDeps, "Dep", {"Name": DependencyName})
        ET.SubElement(
            ObjectsData,
            "Object",
            {"type": "PartDesign::PolarPattern", "name": "PolarPattern", "id": "5"},
        )
        BodyProperties = ObjectData.find("./Object[@name='Body']/Properties")
        assert BodyProperties is not None
        GroupData = BodyProperties.find("./Property[@name='Group']/LinkList")
        TipData = BodyProperties.find("./Property[@name='Tip']/Link")
        assert GroupData is not None
        assert TipData is not None
        ET.SubElement(GroupData, "Link", {"value": "PolarPattern"})
        GroupData.set("count", str(int(GroupData.get("count", "0")) + 1))
        TipData.set("value", "PolarPattern")
        OriginalsData = _native_property(
            "Originals",
            "App::PropertyLinkList",
            "LinkList",
            {"count": "1"},
        )
        ET.SubElement(OriginalsData[0], "Link", {"value": "Pad"})
        AxisData = _native_property(
            "Axis",
            "App::PropertyLinkSub",
            "LinkSub",
            {"value": "Sketch", "count": "1"},
        )
        ET.SubElement(AxisData[0], "Sub", {"value": "N_Axis"})
        PropertiesData = (
            _native_property(
                "Label", "App::PropertyString", "String", {"value": "PolarPattern"}
            ),
            OriginalsData,
            AxisData,
            _native_property("Angle", "App::PropertyAngle", "Float", {"value": "360"}),
            _native_property(
                "Occurrences", "App::PropertyInteger", "Integer", {"value": "4"}
            ),
            _native_property(
                "Reversed", "App::PropertyBool", "Bool", {"value": "false"}
            ),
        )
        PatternData = ET.SubElement(ObjectData, "Object", {"name": "PolarPattern"})
        PatternProperties = ET.SubElement(
            PatternData,
            "Properties",
            {"Count": str(len(PropertiesData)), "TransientCount": "0"},
        )
        PatternProperties.extend(PropertiesData)

    DocumentData = FreeCADAdapter().read(
        _rewrite_document_xml(_native_part_fixture(), AddPolarPattern)
    )
    PatternData = next(
        ItemData
        for ItemData in DocumentData.feature_timeline
        if ItemData.kind == FeatureKind.PATTERN
    )
    assert isinstance(PatternData.definition, CircularPatternFeature)
    assert PatternData.definition.angle == ParameterValue(
        360.0,
        ValueKind.ANGLE,
        "deg",
    )
    assert PatternData.definition.instance_count == 4
    assert PatternData.definition.reversed is False
    assert PatternData.input_feature_ids == ("freecad:feature:Pad",)
    assert PatternData.selection_ids == (PatternData.definition.axis_selection_id,)
    SelectionData = next(
        ItemData
        for ItemData in DocumentData.selections
        if ItemData.id == PatternData.definition.axis_selection_id
    )
    assert SelectionData.path[0].entity_kind == "native"
    assert SelectionData.path[0].entity_id == "Sketch"
    assert SelectionData.path[0].subelement == "N_Axis"
    assert DocumentData.bodies[0].final_feature_id == PatternData.id


def test_neutral_sections_are_exposed_by_native_freecad_graph() -> None:
    source = neutral_document()
    first_parameter = Parameter("p:a", "A", ParameterValue(2.0))
    second_parameter = Parameter(
        "p:b",
        "B",
        ParameterValue(4.0),
        expression=Expression("p:a * 2", ("p:a",), "kit"),
    )
    selection = Selection(
        "selection:face",
        "Face selection",
        (SelectionPathElement("face", source.feature_timeline[0].id, "Face1"),),
    )
    fallback = FeatureStep(
        "feature:fallback",
        "Revolve fallback",
        FeatureKind.REVOLUTION,
        1,
        input_feature_ids=(source.feature_timeline[0].id,),
        selection_ids=(selection.id,),
    )
    document = replace(
        source,
        parameters=(first_parameter, second_parameter),
        selections=(selection,),
        feature_timeline=(*source.feature_timeline, fallback),
        bodies=(
            replace(
                source.bodies[0],
                final_feature_id=fallback.id,
                material_id="material:steel",
            ),
        ),
        brep=triangle_brep(),
    )
    output = io.BytesIO()
    result = FreeCADAdapter().write(document, output)
    transfers = {item.capability: item.mode for item in result.transfers}
    assert transfers[Capability.SUPPORT_PLANES] is TransferMode.NATIVE
    assert transfers[Capability.BODY_STRUCTURE] is TransferMode.NATIVE
    assert transfers[Capability.SELECTIONS] is TransferMode.NATIVE
    assert transfers[Capability.EXPRESSIONS] is TransferMode.NATIVE
    assert transfers[Capability.MATERIALS] is TransferMode.NATIVE
    assert transfers[Capability.CONFIGURATIONS] is TransferMode.NATIVE
    assert transfers[Capability.BREP] is TransferMode.NATIVE
    assert transfers[Capability.PARAMETRIC_HISTORY] is TransferMode.MIXED
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
        declarations = {
            item.get("name", ""): item.get("type", "")
            for item in root.findall("./Objects/Object")
        }
        assert declarations["XY"] == "App::Plane"
        assert declarations["Body"] == "App::DocumentObjectGroup"
        assert declarations["Revolve_fallback"] == "Part::Feature"
        formula = root.find(
            "./ObjectData/Object[@name='Parameters']/Properties/"
            "Property[@name='cells']/Cells/Cell[@address='B2']"
        )
        assert formula is not None
        assert formula.get("content") == "=p_a * 2"
        material = root.find(
            "./ObjectData/Object[@name='Body']/Properties/"
            "Property[@name='MaterialId']/String"
        )
        assert material is not None
        assert material.get("value") == "material:steel"
        link = root.find(
            "./ObjectData/Object[@name='Face_selection']/Properties/"
            "Property[@name='Selection']/LinkSubList/Link"
        )
        assert link is not None
        assert (link.get("obj"), link.get("sub")) == ("Boss1", "Face1")
        kind = root.find(
            "./ObjectData/Object[@name='Revolve_fallback']/Properties/"
            "Property[@name='FeatureKind']/String"
        )
        assert kind is not None
        assert kind.get("value") == FeatureKind.REVOLUTION.value
        configuration = root.find(
            "./ObjectData/Object[@name='Default']/Properties/"
            "Property[@name='KitConfigurationId']/String"
        )
        assert configuration is not None
        assert configuration.get("value") == "config:default"
        shape = root.find(
            "./ObjectData/Object[@name='BRep']/Properties/Property[@name='Shape']/Part"
        )
        assert shape is not None
        shape_file = shape.get("file", "")
        assert shape_file
        assert is_structurally_valid_ascii_brep(archive.read(shape_file))
    assert FreeCADAdapter().read(output.getvalue()) == document
    native = freecad_native_module.read_native_fcstd(output.getvalue())
    assert len(native.support_planes) == 1
    assert native.bodies[0].material_id == "material:steel"
    assert native.configurations[0].id == "config:default"
    assert any(item.id == selection.id for item in native.selections)


def test_neutral_feature_scope_ignores_native_and_reference_carriers() -> None:
    source = neutral_document()
    system = FeatureStep("system:history", "History carrier", FeatureKind.NATIVE, 0)
    reference = FeatureStep(
        "reference:sketch",
        "Sketch feature carrier",
        FeatureKind.REFERENCE,
        1,
        sketch_id=source.sketches[0].id,
    )
    extrusion = replace(
        source.feature_timeline[0],
        order=2,
        input_feature_ids=(reference.id,),
    )
    document = replace(
        source,
        feature_timeline=(system, reference, extrusion),
    )
    document.assert_valid()
    output = io.BytesIO()
    FreeCADAdapter().write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    declarations = {
        item.get("name", ""): item.get("type", "")
        for item in root.findall("./Objects/Object")
    }
    assert declarations["Boss1"] == "Part::Extrusion"
    assert declarations["Body"] == "App::DocumentObjectGroup"
    assert "Boss1_Profile" not in declarations
    dependencies = root.find("./Objects/ObjectDeps[@Name='Boss1']")
    assert dependencies is not None
    assert [item.get("Name") for item in dependencies.findall("./Dep")] == [
        "Sketch1",
        "Sketches",
    ]
    base = root.find(
        "./ObjectData/Object[@name='Boss1']/Properties/Property[@name='Base']/Link"
    )
    assert base is not None
    assert base.get("value") == "Sketch1"


def test_native_quantities_preserve_value_kind_and_internal_units() -> None:
    def quantities(root: ET.Element) -> None:
        properties = root.find("./ObjectData/Object[@name='Pad']/Properties")
        assert properties is not None
        properties.extend(
            (
                _native_property(
                    "Pressure",
                    "App::PropertyPressure",
                    "Float",
                    {"value": "2.5"},
                ),
                _native_property(
                    "Percent",
                    "App::PropertyPercent",
                    "Integer",
                    {"value": "75"},
                ),
                _native_property(
                    "Uuid",
                    "App::PropertyUUID",
                    "Uuid",
                    {"value": "7db2d7ea-e03e-4cd5-a4ac-9f1abc7ad12a"},
                ),
            )
        )
        properties.set("Count", str(len(properties.findall("./Property"))))

    document = FreeCADAdapter().read(
        _rewrite_document_xml(_native_part_fixture(), quantities)
    )
    by_path = {
        item.attributes.get("freecad_path"): item.value for item in document.parameters
    }
    assert str(by_path["Pressure"].kind) == "quantity"
    assert by_path["Pressure"].unit == "kg/(mm*s^2)"
    assert by_path["Pressure"].value == 2.5
    assert str(by_path["Percent"].kind) == "quantity"
    assert by_path["Percent"].unit == "%"
    assert by_path["Percent"].value == 75
    assert str(by_path["Uuid"].kind) == "string"
    assert by_path["Uuid"].value == "7db2d7ea-e03e-4cd5-a4ac-9f1abc7ad12a"


def test_datum_plane_legacy_support_and_structural_selection_restore() -> None:
    def datum_and_selection(root: ET.Element) -> None:
        declaration = root.find("./Objects/Object[@name='XY_Plane']")
        assert declaration is not None
        declaration.set("type", "PartDesign::Plane")
        attachment = root.find(
            "./ObjectData/Object[@name='Sketch']/Properties/"
            "Property[@name='AttachmentSupport']"
        )
        assert attachment is not None
        attachment.set("name", "Support")
        properties = root.find("./ObjectData/Object[@name='Pad']/Properties")
        assert properties is not None
        selection = _native_property(
            "Targets", "Vendor::DerivedLinkSelection", "LinkSub", {"value": "Body"}
        )
        ET.SubElement(selection[0], "Sub", {"value": "Face1"})
        properties.append(selection)
        properties.set("Count", str(len(properties.findall("./Property"))))

    document = FreeCADAdapter().read(
        _rewrite_document_xml(_native_part_fixture(), datum_and_selection)
    )
    assert document.sketches[0].support_plane_id == document.support_planes[0].id
    assert document.support_planes[0].attributes["freecad"]["type_id"] == (
        "PartDesign::Plane"
    )
    assert len(document.selections) == 1
    assert document.selections[0].path[0].entity_kind == "face"
    assert document.selections[0].path[0].entity_id == "Body"
    assert document.feature_timeline[-1].selection_ids == (document.selections[0].id,)
    assert Capability.SELECTIONS in document.capabilities


def test_custom_featurepython_sketch_support_is_restored_as_plane() -> None:
    def custom_plane(root: ET.Element) -> None:
        declaration = root.find("./Objects/Object[@name='XY_Plane']")
        assert declaration is not None
        declaration.set("type", "Vendor::FeaturePythonPlane")

    document = FreeCADAdapter().read(
        _rewrite_document_xml(_native_part_fixture(), custom_plane)
    )
    assert len(document.support_planes) == 1
    assert document.sketches[0].support_plane_id == document.support_planes[0].id
    assert document.support_planes[0].attributes["freecad"]["type_id"] == (
        "Vendor::FeaturePythonPlane"
    )


def test_unreferenced_custom_datum_plane_is_restored_structurally() -> None:
    assert "Vendor::FutureDatumPlane" not in SUPPORT_PLANE_TYPE_IDS
    proxy = _native_property(
        "Proxy",
        "App::PropertyPythonObject",
        "Python",
        {
            "value": "bnVsbA==",
            "encoded": "yes",
            "module": "VendorDatum",
            "class": "DatumPlane",
        },
    )
    properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Future datum"}
        ),
        proxy,
        _native_placement(),
        _native_placement("AttachmentOffset"),
        _native_property(
            "MapMode", "App::PropertyString", "String", {"value": "Deactivated"}
        ),
    )
    document = FreeCADAdapter().read(
        _native_archive(
            (("FutureDatum", "Vendor::FutureDatumPlane", (), properties),), {}
        )
    )
    assert len(document.support_planes) == 1
    assert document.support_planes[0].name == "Future datum"
    assert document.support_planes[0].attributes["freecad"]["type_id"] == (
        "Vendor::FutureDatumPlane"
    )


def test_custom_feature_and_derived_shape_property_restore_structurally() -> None:
    properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "Custom"}),
        _native_property("Length", "App::PropertyLength", "Float", {"value": "12"}),
        _native_property(
            "Result",
            "Vendor::DerivedShapeProperty",
            "Part",
            {"file": "Custom.Result.brp"},
        ),
    )
    document = FreeCADAdapter().read(
        _native_archive(
            (("Custom", "Vendor::ParametricFeature", (), properties),),
            {
                "Custom.Result.brp": (
                    b"\nCASCADE Topology V1, (c) Matra-Datavision\ncustom\n"
                )
            },
        )
    )
    assert len(document.feature_timeline) == 1
    assert str(document.feature_timeline[0].kind) == "native"
    assert document.feature_timeline[0].attributes["freecad"]["type_id"] == (
        "Vendor::ParametricFeature"
    )
    shape_payloads = tuple(
        payload
        for payload in document.brep_payloads
        if payload.role == PayloadRole.BREP
    )
    assert len(shape_payloads) == 1
    assert shape_payloads[0].attributes["freecad_property"] == "Result"
    assert shape_payloads[0].source_stream == "Custom.Result.brp"
    assert Capability.PARAMETRIC_HISTORY in document.capabilities
    assert Capability.BREP in document.capabilities


@pytest.mark.parametrize("schema_version", (3, 4))
def test_native_object_graph_schema_versions_are_readable(schema_version: int) -> None:
    source = _rewrite_document_xml(
        _native_part_fixture(),
        lambda root: root.set("SchemaVersion", str(schema_version)),
    )
    document = FreeCADAdapter().read(source)
    assert document.validate() == ()
    assert document.source.attributes["freecad_schema_version"] == str(schema_version)


def test_native_schema_two_feature_graph_is_readable() -> None:
    def schema_two(root: ET.Element) -> None:
        root.set("SchemaVersion", "2")
        objects = root.find("./Objects")
        object_data = root.find("./ObjectData")
        assert objects is not None
        assert object_data is not None
        declarations = objects.findall("./Object")
        data_by_name = {
            item.get("name", ""): item for item in object_data.findall("./Object")
        }
        features = ET.Element("Features", {"Count": str(len(declarations))})
        feature_data = ET.Element("FeatureData", {"Count": str(len(declarations))})
        for declaration in declarations:
            name = declaration.get("name", "")
            ET.SubElement(
                features,
                "Feature",
                {"type": declaration.get("type", ""), "name": name},
            )
            source_data = data_by_name[name]
            target_data = ET.SubElement(feature_data, "Feature", {"name": name})
            for child in source_data:
                target_data.append(ET.fromstring(ET.tostring(child)))
        root.remove(objects)
        root.remove(object_data)
        root.append(features)
        root.append(feature_data)

    document = FreeCADAdapter().read(
        _rewrite_document_xml(_native_part_fixture(), schema_two)
    )
    assert document.validate() == ()
    assert document.source.attributes["freecad_schema_version"] == "2"


def test_empty_native_object_graph_is_preserved_as_native_document() -> None:
    root = ET.Element(
        "Document",
        {"SchemaVersion": "4", "ProgramVersion": "1.0", "FileVersion": "1"},
    )
    ET.SubElement(root, "Objects", {"Count": "0", "Dependencies": "1"})
    ET.SubElement(root, "ObjectData", {"Count": "0"})
    source = io.BytesIO()
    with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "Document.xml", ET.tostring(root, encoding="utf-8", xml_declaration=True)
        )
    document = FreeCADAdapter().read(source.getvalue())
    assert document.validate() == ()
    assert [payload.kind for payload in document.brep_payloads] == [
        "native_document",
        "native_document_binding",
    ]
    assert document.capabilities == frozenset(
        {
            Capability.CONFIGURATIONS,
            Capability.NATIVE_PAYLOADS,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
        }
    )


def test_all_current_sketch_constraint_codes_and_arbitrary_elements_restore() -> None:
    expected = tuple(value.kind.value for value in CONSTRAINT_TYPES)

    def constraints(root: ET.Element) -> None:
        constraint_list = root.find(
            "./ObjectData/Object[@name='Sketch']/Properties/"
            "Property[@name='Constraints']/ConstraintList"
        )
        assert constraint_list is not None
        constraint_list.clear()
        constraint_list.set("count", str(len(CONSTRAINT_TYPES)))
        for code in CONSTRAINT_KIND_BY_CODE:
            ET.SubElement(
                constraint_list,
                "Constrain",
                {
                    "Name": f"Constraint{code}",
                    "Type": str(code),
                    "Value": "1.25",
                    "IsDriving": "1",
                    "IsActive": "1",
                    "ElementIds": "0 1 2 3",
                    "ElementPositions": "1 2 3 1",
                },
            )

    document = FreeCADAdapter().read(
        _rewrite_document_xml(_native_part_fixture(), constraints)
    )
    sketch = document.sketches[0]
    assert tuple(str(item.kind) for item in sketch.constraints) == expected
    assert all(len(item.references) == 4 for item in sketch.constraints)
    assert len(sketch.parameter_ids) == 8
    assert sketch.entities[0].fixed


def test_unavailable_sketch_geometry_uses_explicit_carrier_fallback() -> None:
    source = neutral_document()
    kinds = (
        GeometryKind.ARC_ELLIPSE,
        GeometryKind.HYPERBOLA,
        GeometryKind.ARC_HYPERBOLA,
        GeometryKind.PARABOLA,
        GeometryKind.ARC_PARABOLA,
        GeometryKind.OFFSET,
        GeometryKind.TRIMMED,
        GeometryKind.NATIVE,
    )
    entities = tuple(
        SketchEntity(
            f"carrier:{kind.value}",
            kind,
            NativeGeometry(
                "catia.catpart",
                f"CATIA::{kind.value}",
                {"token": kind.value},
            ),
        )
        for kind in kinds
    )
    sketch = replace(source.sketches[0], entities=entities, constraints=())
    document = replace(source, sketches=(sketch,))
    document.assert_valid()
    output = io.BytesIO()
    adapter = FreeCADAdapter()
    result = adapter.write(document, output)
    transfers = {transfer.capability: transfer for transfer in result.transfers}
    assert transfers[Capability.EDITABLE_SKETCHES].mode == TransferMode.MIXED
    assert (
        transfers[Capability.EDITABLE_SKETCHES].carrier_reason
        is CarrierReason.SOURCE_OPAQUE
    )
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    sketch_object = next(
        item
        for item in root.findall("./ObjectData/Object")
        if item.find("./Properties/Property[@name='Geometry']") is not None
    )
    geometry_list = sketch_object.find(
        "./Properties/Property[@name='Geometry']/GeometryList"
    )
    assert geometry_list is not None
    assert geometry_list.get("count") == "0"
    assert geometry_list.findall("./Geometry") == []
    assert geometry_list.findall(".//GeomPoint") == []
    diagnostics_node = sketch_object.find(
        "./Properties/Property[@name='KitSketchDiagnosticsJSON']/String"
    )
    assert diagnostics_node is not None
    diagnostics = json.loads(diagnostics_node.get("value", ""))
    assert {item["kind"] for item in diagnostics} == {kind.value for kind in kinds}
    assert {item["mode"] for item in diagnostics} == {"carrier_only"}
    source_node = sketch_object.find(
        "./Properties/Property[@name='SourceSketchJSON']/String"
    )
    assert source_node is not None
    source_sketch = json.loads(source_node.get("value", ""))
    assert len(source_sketch["entities"]["$tuple"]) == len(kinds)
    assert adapter.read(output.getvalue()) == document


def test_neutral_conics_round_trip_through_native_fcstd_geometry() -> None:
    source = neutral_document()
    axis = Vector2(0.6, 0.8)
    values = (
        (
            GeometryKind.ELLIPSE,
            EllipseGeometry(Vector2(1.0, 2.0), axis, 8.0, 3.0),
            "Part::GeomEllipse",
        ),
        (
            GeometryKind.ARC_ELLIPSE,
            ArcEllipseGeometry(Vector2(2.0, 3.0), axis, 9.0, 4.0, -0.5, 1.25),
            "Part::GeomArcOfEllipse",
        ),
        (
            GeometryKind.ARC_HYPERBOLA,
            ArcHyperbolaGeometry(Vector2(4.0, 5.0), axis, 11.0, 6.0, -0.75, 1.5),
            "Part::GeomArcOfHyperbola",
        ),
        (
            GeometryKind.ARC_PARABOLA,
            ArcParabolaGeometry(Vector2(6.0, 7.0), axis, 8.0, -1.0, 2.0),
            "Part::GeomArcOfParabola",
        ),
    )
    entities = tuple(
        SketchEntity(f"conic:{index}", kind, geometry)
        for index, (kind, geometry, _) in enumerate(values)
    )
    sketch = replace(
        source.sketches[0],
        entities=entities,
        constraints=(),
        closed_profile_entity_ids=(),
    )
    document = replace(
        source,
        sketches=(sketch,),
        feature_timeline=(replace(source.feature_timeline[0], suppressed=True),),
    )
    document.assert_valid()
    output = io.BytesIO()
    result = FreeCADAdapter().write(document, output)
    transfers = {item.capability: item.mode for item in result.transfers}
    assert transfers[Capability.EDITABLE_SKETCHES] is TransferMode.NATIVE
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    geometry_nodes = root.findall(".//Property[@name='Geometry']/GeometryList/Geometry")
    assert [item.get("type") for item in geometry_nodes] == [
        type_id for _, _, type_id in values
    ]
    native = freecad_native_module.read_native_fcstd(output.getvalue())
    restored = native.sketches[0].entities
    assert [item.kind for item in restored] == [kind for kind, _, _ in values]
    for item, (_, expected, _) in zip(restored, values, strict=True):
        actual = item.geometry
        assert type(actual) is type(expected)
        assert (actual.center.x, actual.center.y) == pytest.approx(
            (expected.center.x, expected.center.y)
        )
        expected_axis = getattr(expected, "major_axis", getattr(expected, "axis", None))
        actual_axis = getattr(actual, "major_axis", getattr(actual, "axis", None))
        assert (actual_axis.x, actual_axis.y) == pytest.approx(
            (expected_axis.x, expected_axis.y)
        )
        for name in (
            "major_radius",
            "minor_radius",
            "focal_length",
            "start_angle",
            "end_angle",
        ):
            if hasattr(expected, name):
                assert getattr(actual, name) == pytest.approx(getattr(expected, name))


def test_unbounded_neutral_conics_are_explicit_freecad_carriers() -> None:
    source = neutral_document()
    axis = Vector2(0.6, 0.8)
    values = (
        (
            GeometryKind.HYPERBOLA,
            HyperbolaGeometry(Vector2(3.0, 4.0), axis, 10.0, 5.0),
        ),
        (GeometryKind.PARABOLA, ParabolaGeometry(Vector2(5.0, 6.0), axis, 7.0)),
    )
    entities = tuple(
        SketchEntity(f"unbounded:{index}", kind, geometry)
        for index, (kind, geometry) in enumerate(values)
    )
    sketch = replace(
        source.sketches[0],
        entities=entities,
        constraints=(),
        closed_profile_entity_ids=(),
    )
    document = replace(
        source,
        sketches=(sketch,),
        feature_timeline=(replace(source.feature_timeline[0], suppressed=True),),
    )
    output = io.BytesIO()
    result = FreeCADAdapter().write(document, output)
    transfers = {item.capability: item for item in result.transfers}
    transfer = transfers[Capability.EDITABLE_SKETCHES]
    assert transfer.mode is TransferMode.MIXED
    assert transfer.carrier_reason is CarrierReason.WRITER_UNIMPLEMENTED
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    geometry_nodes = root.findall(".//Property[@name='Geometry']/GeometryList/Geometry")
    assert geometry_nodes == []
    assert FreeCADAdapter().read(output.getvalue()) == document


def test_native_geometry_payload_restores_every_registered_conic_and_wrapper() -> None:
    source = neutral_document()
    kinds = (
        (GeometryKind.ARC_ELLIPSE, "Part::GeomArcOfEllipse", "ArcOfEllipse"),
        (GeometryKind.HYPERBOLA, "Part::GeomHyperbola", "Hyperbola"),
        (
            GeometryKind.ARC_HYPERBOLA,
            "Part::GeomArcOfHyperbola",
            "ArcOfHyperbola",
        ),
        (GeometryKind.PARABOLA, "Part::GeomParabola", "Parabola"),
        (
            GeometryKind.ARC_PARABOLA,
            "Part::GeomArcOfParabola",
            "ArcOfParabola",
        ),
        (GeometryKind.OFFSET, "Part::GeomOffsetCurve", "OffsetCurve"),
        (GeometryKind.TRIMMED, "Part::GeomTrimmedCurve", "TrimmedCurve"),
    )
    entities = tuple(
        SketchEntity(
            f"native:{kind.value}",
            kind,
            NativeGeometry(
                "freecad.fcstd",
                type_id,
                {
                    "tag": "Geometry",
                    "attributes": {
                        "type": type_id,
                        "id": str(index + 1),
                        "migrated": "1",
                    },
                    "children": [
                        {
                            "tag": tag,
                            "attributes": {"Token": kind.value},
                        },
                        {"tag": "Construction", "attributes": {"value": "0"}},
                    ],
                },
            ),
        )
        for index, (kind, type_id, tag) in enumerate(kinds)
    )
    document = replace(
        source,
        sketches=(replace(source.sketches[0], entities=entities, constraints=()),),
    )
    output = io.BytesIO()
    adapter = FreeCADAdapter()
    result = adapter.write(document, output)
    transfers = {transfer.capability: transfer.mode for transfer in result.transfers}
    assert transfers[Capability.EDITABLE_SKETCHES] == TransferMode.NATIVE
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    sketch_object = next(
        item
        for item in root.findall("./ObjectData/Object")
        if item.find("./Properties/Property[@name='Geometry']") is not None
    )
    geometry_nodes = sketch_object.findall(
        "./Properties/Property[@name='Geometry']/GeometryList/Geometry"
    )
    assert [item.get("type") for item in geometry_nodes] == [
        type_id for _, type_id, _ in kinds
    ]
    assert [list(item)[0].tag for item in geometry_nodes] == [
        tag for _, _, tag in kinds
    ]
    assert [list(item)[0].get("Token") for item in geometry_nodes] == [
        kind.value for kind, _, _ in kinds
    ]
    assert (
        sketch_object.find("./Properties/Property[@name='KitSketchDiagnosticsJSON']")
        is None
    )
    assert sketch_object.findall(".//GeomPoint") == []
    assert adapter.read(output.getvalue()) == document


def test_constraint_carrier_fallback_and_sound_midpoint_composition() -> None:
    source = neutral_document()
    line = source.sketches[0].entities[0]
    point = SketchEntity(
        "sketch:1:point:1",
        GeometryKind.POINT,
        PointGeometry(Vector2(5.0, 0.0)),
    )
    carrier_constraints = tuple(
        SketchConstraint(f"carrier:{kind.value}", kind, ()) for kind in ConstraintKind
    )
    midpoint = SketchConstraint(
        "midpoint:sound",
        ConstraintKind.MIDPOINT,
        (
            ConstraintReference(line.id),
            ConstraintReference(point.id),
        ),
    )
    sketch = replace(
        source.sketches[0],
        entities=(line, point),
        constraints=(*carrier_constraints, midpoint),
    )
    document = replace(source, sketches=(sketch,))
    document.assert_valid()
    output = io.BytesIO()
    adapter = FreeCADAdapter()
    result = adapter.write(document, output)
    transfers = {transfer.capability: transfer.mode for transfer in result.transfers}
    assert transfers[Capability.EDITABLE_SKETCHES] == TransferMode.MIXED
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    sketch_object = next(
        item
        for item in root.findall("./ObjectData/Object")
        if item.find("./Properties/Property[@name='Constraints']") is not None
    )
    encoded = sketch_object.findall(
        "./Properties/Property[@name='Constraints']/ConstraintList/Constrain"
    )
    assert len(encoded) == 1
    assert encoded[0].get("Type") == "14"
    assert encoded[0].get("ElementIds") == "0 0 1"
    assert encoded[0].get("ElementPositions") == "1 2 1"
    diagnostics_node = sketch_object.find(
        "./Properties/Property[@name='KitSketchDiagnosticsJSON']/String"
    )
    assert diagnostics_node is not None
    diagnostics = json.loads(diagnostics_node.get("value", ""))
    carrier_only = [item for item in diagnostics if item["mode"] == "carrier_only"]
    assert {item["kind"] for item in carrier_only} == {
        kind.value for kind in ConstraintKind
    }
    composition = [item for item in diagnostics if item["mode"] == "native_composition"]
    assert composition == [
        {
            "code": "freecad.sketch_constraint_composed",
            "constraint_id": midpoint.id,
            "kind": ConstraintKind.MIDPOINT.value,
            "mode": "native_composition",
            "native_kind": "Symmetric",
            "reason": "encoded as symmetry between a line's endpoints and the referenced point",
            "severity": "info",
        }
    ]
    source_node = sketch_object.find(
        "./Properties/Property[@name='SourceSketchJSON']/String"
    )
    assert source_node is not None
    source_sketch = json.loads(source_node.get("value", ""))
    assert len(source_sketch["constraints"]["$tuple"]) == len(ConstraintKind) + 1
    assert adapter.read(output.getvalue()) == document


def test_neutral_point_distance_uses_valid_sketcher_point_slots() -> None:
    source = neutral_document()
    first = SketchEntity(
        "sketch:1:point:1",
        GeometryKind.POINT,
        PointGeometry(Vector2(0.0, 0.0)),
    )
    second = SketchEntity(
        "sketch:1:point:2",
        GeometryKind.POINT,
        PointGeometry(Vector2(10.0, 0.0)),
    )
    distance = SketchConstraint(
        "distance:points",
        ConstraintKind.DISTANCE,
        (ConstraintReference(first.id), ConstraintReference(second.id)),
        attributes={"Value": 10.0},
    )
    sketch = replace(
        source.sketches[0],
        entities=(first, second),
        constraints=(distance,),
    )
    document = replace(source, sketches=(sketch,))
    output = io.BytesIO()
    FreeCADAdapter().write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    encoded = root.find(".//Property[@name='Constraints']/ConstraintList/Constrain")
    assert encoded is not None
    assert encoded.get("Type") == "6"
    assert encoded.get("FirstPos") == "1"
    assert encoded.get("SecondPos") == "1"
    assert encoded.get("ElementPositions") == "1 1 0"


def test_parameterless_native_radius_constraint_retains_its_value() -> None:
    source = neutral_document()
    circle = SketchEntity(
        "sketch:1:circle:1",
        GeometryKind.CIRCLE,
        CircleGeometry(Vector2(0.0, 0.0), 8.0),
    )
    radius = SketchConstraint(
        "radius:native",
        ConstraintKind.RADIUS,
        (ConstraintReference(circle.id),),
        attributes={"native_value": 8.0},
    )
    sketch = replace(
        source.sketches[0],
        entities=(circle,),
        constraints=(radius,),
        closed_profile_entity_ids=((circle.id,),),
    )
    output = io.BytesIO()
    FreeCADAdapter().write(replace(source, sketches=(sketch,)), output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    encoded = root.find(".//Property[@name='Constraints']/ConstraintList/Constrain")
    assert encoded is not None
    assert encoded.get("Type") == str(CONSTRAINT_CODE_BY_KIND["radius"])
    assert float(encoded.get("Value", "")) == 8.0


def test_solidworks_opaque_extrusion_is_typed_non_executable_feature() -> None:
    source = neutral_document()
    document = replace(
        source,
        source=replace(source.source, format_id="solidworks.sldprt"),
    )
    output = io.BytesIO()
    FreeCADAdapter().write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    declaration = root.find("./Objects/Object[@name='Boss1']")
    assert declaration is not None
    assert declaration.get("type") == "Part::Feature"
    properties = root.find("./ObjectData/Object[@name='Boss1']/Properties")
    assert properties is not None
    executable = properties.find("./Property[@name='NativeExecutable']/Bool")
    reason = properties.find("./Property[@name='NativeExecutionReason']/String")
    assert executable is not None and executable.get("value") == "false"
    assert reason is not None and reason.get("value") == "no_native_closed_profile"
    assert FreeCADAdapter().read(output.getvalue()) == document


def test_solidworks_intersecting_profiles_are_typed_non_executable_feature() -> None:
    source = neutral_document()
    first = SketchEntity(
        "sketch:1:circle:1",
        GeometryKind.CIRCLE,
        CircleGeometry(Vector2(0.0, 0.0), 10.0),
    )
    second = SketchEntity(
        "sketch:1:circle:2",
        GeometryKind.CIRCLE,
        CircleGeometry(Vector2(15.0, 0.0), 10.0),
    )
    sketch = replace(
        source.sketches[0],
        entities=(first, second),
        closed_profile_entity_ids=((first.id,), (second.id,)),
    )
    document = replace(
        source,
        source=replace(source.source, format_id="solidworks.sldprt"),
        sketches=(sketch,),
    )
    output = io.BytesIO()
    FreeCADAdapter().write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    declaration = root.find("./Objects/Object[@name='Boss1']")
    reason = root.find(
        "./ObjectData/Object[@name='Boss1']/Properties/Property[@name='NativeExecutionReason']/String"
    )
    assert declaration is not None and declaration.get("type") == "Part::Feature"
    assert reason is not None
    assert reason.get("value") == "profile_topology_not_statically_sound"
    assert FreeCADAdapter().read(output.getvalue()) == document


@pytest.mark.parametrize(
    ("type_id", "type_code", "expected"),
    (
        ("PartDesign::Pad", 0, "blind"),
        ("PartDesign::Pad", 1, "up_to_last"),
        ("PartDesign::Pad", 2, "up_to_first"),
        ("PartDesign::Pad", 3, "up_to_face"),
        ("PartDesign::Pad", 4, "two_lengths"),
        ("PartDesign::Pad", 5, "up_to_shape"),
        ("PartDesign::Pocket", 0, "blind"),
        ("PartDesign::Pocket", 1, "through_all"),
        ("PartDesign::Pocket", 2, "up_to_first"),
        ("PartDesign::Pocket", 3, "up_to_face"),
        ("PartDesign::Pocket", 4, "two_lengths"),
        ("PartDesign::Pocket", 5, "up_to_shape"),
    ),
)
def test_current_pad_and_pocket_end_condition_registries(
    type_id: str, type_code: int, expected: str
) -> None:
    properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "X"}),
        _native_property("Length", "App::PropertyLength", "Float", {"value": "8"}),
        _native_property("Length2", "App::PropertyLength", "Float", {"value": "3"}),
        _native_property(
            "Type", "App::PropertyEnumeration", "Integer", {"value": str(type_code)}
        ),
        _native_property(
            "Type2", "App::PropertyEnumeration", "Integer", {"value": "5"}
        ),
        _native_property(
            "SideType", "App::PropertyEnumeration", "Integer", {"value": "1"}
        ),
        _native_property("Offset", "App::PropertyLength", "Float", {"value": "2"}),
        _native_property("Offset2", "App::PropertyLength", "Float", {"value": "4"}),
        _native_property("TaperAngle", "App::PropertyAngle", "Float", {"value": "5"}),
        _native_property("TaperAngle2", "App::PropertyAngle", "Float", {"value": "6"}),
    )
    document = FreeCADAdapter().read(
        _native_archive((("Extrude", type_id, (), properties),), {})
    )
    definition = document.feature_timeline[0].definition
    assert definition is not None
    assert str(definition.end_condition) == expected
    assert str(definition.second_end_condition) == "up_to_shape"
    assert definition.second_length is not None
    assert definition.second_length.value == 3.0
    assert definition.offset is not None
    assert definition.offset.value == 2.0
    assert definition.second_offset is not None
    assert definition.second_offset.value == 4.0
    assert definition.second_draft_angle is not None
    assert definition.second_draft_angle.value == 6.0


def test_a_revolution_carries_a_boolean_operation() -> None:
    revolution = (
        "Revolution",
        "PartDesign::Revolution",
        (),
        (
            _native_property(
                "Label", "App::PropertyString", "String", {"value": "Revolution"}
            ),
            _native_property(
                "Angle", "App::PropertyAngle", "Float", {"value": "360.0"}
            ),
        ),
    )
    groove = (
        "Groove",
        "PartDesign::Groove",
        ("Revolution",),
        (
            _native_property(
                "Label", "App::PropertyString", "String", {"value": "Groove"}
            ),
            _native_property(
                "Angle", "App::PropertyAngle", "Float", {"value": "360.0"}
            ),
        ),
    )
    document = FreeCADAdapter().read(_native_archive((revolution, groove), {}))
    steps = {item.name: item for item in document.feature_timeline}
    assert steps["Revolution"].kind == FeatureKind.REVOLUTION
    assert steps["Revolution"].operation == BooleanOperation.CREATE
    assert steps["Groove"].kind == FeatureKind.REVOLUTION
    assert steps["Groove"].operation == BooleanOperation.CUT


def test_native_feature_definition_preserves_and_applies_unmapped_feature_data() -> (
    None
):
    properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "Revolution"}
        ),
        _native_property("Angle", "App::PropertyAngle", "Float", {"value": "45.0"}),
        _native_property(
            "ReferenceAxis",
            "App::PropertyString",
            "String",
            {"value": "V_Axis"},
        ),
    )
    adapter = FreeCADAdapter()
    document = adapter.read(
        _native_archive((("Revolution", "PartDesign::Revolution", (), properties),), {})
    )
    feature = document.feature_timeline[0]
    assert feature.kind == FeatureKind.REVOLUTION
    assert isinstance(feature.definition, NativeFeatureDefinition)
    assert feature.definition.format_id == "freecad.fcstd"
    assert feature.definition.type_id == "PartDesign::Revolution"
    object_data = dict(feature.definition.object_data)
    native_properties = dict(object_data["properties"])
    angle = dict(native_properties["Angle"])
    angle_value = dict(angle["children"][0])
    angle_attributes = dict(angle_value["attributes"])
    angle_attributes["value"] = "37.5"
    angle_value["attributes"] = angle_attributes
    angle["children"] = [angle_value]
    native_properties["Angle"] = angle
    object_data["properties"] = native_properties
    edited = replace(
        document,
        feature_timeline=(
            replace(
                feature,
                definition=replace(feature.definition, object_data=object_data),
            ),
        ),
    )
    output = io.BytesIO()
    adapter.write(edited, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    angle_node = root.find(
        "./ObjectData/Object[@name='Revolution']/Properties/"
        "Property[@name='Angle']/Float"
    )
    assert angle_node is not None
    assert angle_node.get("value") == "37.5"


def test_non_native_feature_definition_uses_lossless_feature_data_object() -> None:
    source = neutral_document()
    previous = source.feature_timeline[-1]
    feature = replace(
        previous,
        id="feature:native-hole",
        name="Native Hole",
        kind=FeatureKind.HOLE,
        order=previous.order + 1,
        input_feature_ids=(previous.id,),
        sketch_id=None,
        parameter_ids=(),
        definition=NativeFeatureDefinition(
            "freecad.fcstd",
            "PartDesign::Hole",
            {"diameter": 6.5, "thread": "M6", "depth": 12.0},
        ),
        selection_ids=(),
    )
    document = replace(
        source,
        feature_timeline=source.feature_timeline + (feature,),
        bodies=tuple(
            replace(body, final_feature_id=feature.id) for body in source.bodies
        ),
    )
    document.assert_valid()
    output = io.BytesIO()
    adapter = FreeCADAdapter()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    feature_object = next(
        node
        for node in root.findall("./ObjectData/Object")
        if (kit_id := node.find("./Properties/Property[@name='KitId']/String"))
        is not None
        and kit_id.get("value") == feature.id
    )
    values = {
        node.get("name"): node.find("./String").get("value")
        for node in feature_object.findall("./Properties/Property")
        if node.find("./String") is not None
    }
    assert values["KitRole"] == "feature-data"
    assert values["NativeTypeId"] == "PartDesign::Hole"
    assert '"diameter":6.5' in values["NativeDefinitionJSON"]
    restored = adapter.read(output.getvalue())
    assert restored.feature(feature.id).definition == feature.definition


@pytest.mark.parametrize(
    ("source", "expected_source"),
    (
        (_native_mesh_fixture(), "Derived.MeshKernel.bms"),
        (_native_mesh_fixture(">"), "Derived.MeshKernel.bms"),
        (_native_mesh_fixture(inline=True), ""),
    ),
    ids=("derived_little_endian", "derived_big_endian", "inline"),
)
def test_current_mesh_kernel_representations_restore(
    source: bytes, expected_source: str
) -> None:
    document = FreeCADAdapter().read(source)
    assert document.validate() == ()
    assert len(document.meshes) == 1
    mesh = document.meshes[0]
    assert tuple((item.x, item.y, item.z) for item in mesh.vertices) == (
        (-2.0, 3.0, 1.0),
        (5.0, -7.0, 4.0),
        (1.0, 2.0, -6.0),
    )
    assert mesh.triangles == ((0, 1, 2),)
    assert mesh.attributes["source_stream"] == expected_source
    assert Capability.TESSELLATION in document.capabilities


def test_mesh_kernel_writer_uses_unsigned_facets_and_axis_interleaved_bounds() -> None:
    source = neutral_document()
    mesh = Mesh(
        "mesh:1",
        "Mesh",
        (
            Vector3(-2.0, 3.0, 1.0),
            Vector3(5.0, -7.0, 4.0),
            Vector3(1.0, 2.0, -6.0),
        ),
        ((0, 1, 2),),
    )
    output = io.BytesIO()
    FreeCADAdapter().write(
        replace(
            source,
            meshes=(mesh,),
            capabilities=source.capabilities | {Capability.TESSELLATION},
        ),
        output,
    )
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        name = next(
            item for item in archive.namelist() if item.endswith(".MeshKernel.bms")
        )
        data = archive.read(name)
    assert struct.unpack_from("<IIIIII", data, 272 + 36) == (
        0,
        1,
        2,
        0xFFFFFFFF,
        0xFFFFFFFF,
        0xFFFFFFFF,
    )
    assert struct.unpack_from("<ffffff", data, len(data) - 24) == (
        -2.0,
        5.0,
        -7.0,
        3.0,
        -6.0,
        4.0,
    )


@pytest.mark.parametrize(
    ("joint_index", "expected"),
    tuple(
        (index, value.kind.value) for index, value in enumerate(JOINT_TYPE_DEFINITIONS)
    ),
)
def test_current_assembly_joint_registry(joint_index: int, expected: str) -> None:
    def joint_type(root: ET.Element) -> None:
        property_element = root.find(
            "./ObjectData/Object[@name='Revolute']/Properties/"
            "Property[@name='JointType']"
        )
        assert property_element is not None
        selected = property_element.find("./Integer")
        assert selected is not None
        selected.set("value", str(joint_index))
        enum_list = property_element.find("./CustomEnumList")
        assert enum_list is not None
        enum_list.clear()
        choices = JOINT_TYPES
        enum_list.set("count", str(len(choices)))
        for choice in choices:
            ET.SubElement(enum_list, "Enum", {"value": choice})

    document = FreeCADAdapter().read(
        _rewrite_document_xml(_native_assembly_fixture(), joint_type)
    )
    assert document.assembly is not None
    assert str(document.assembly.mates[0].kind) == expected


def test_joint_secondary_values_limits_and_empty_subelement_restore() -> None:
    def gear(root: ET.Element) -> None:
        properties = root.find("./ObjectData/Object[@name='Revolute']/Properties")
        assert properties is not None
        joint_type = properties.find("./Property[@name='JointType']")
        assert joint_type is not None
        selected = joint_type.find("./Integer")
        assert selected is not None
        selected.set("value", "11")
        enum_list = joint_type.find("./CustomEnumList")
        assert enum_list is not None
        enum_list.clear()
        choices = JOINT_TYPES
        enum_list.set("count", str(len(choices)))
        for choice in choices:
            ET.SubElement(enum_list, "Enum", {"value": choice})
        reference = properties.find("./Property[@name='Reference1']/XLink")
        assert reference is not None
        for child in list(reference.findall("./Sub")):
            reference.remove(child)
        ET.SubElement(reference, "Sub", {"value": ""})
        properties.extend(
            (
                _native_property(
                    "Distance", "App::PropertyLength", "Float", {"value": "4"}
                ),
                _native_property(
                    "Distance2", "App::PropertyLength", "Float", {"value": "2"}
                ),
                _native_property(
                    "LengthMin", "App::PropertyLength", "Float", {"value": "1"}
                ),
                _native_property(
                    "AngleMax", "App::PropertyAngle", "Float", {"value": "35"}
                ),
                _native_property(
                    "EnableLengthMin",
                    "App::PropertyBool",
                    "Bool",
                    {"value": "true"},
                ),
                _native_property(
                    "EnableAngleMax",
                    "App::PropertyBool",
                    "Bool",
                    {"value": "true"},
                ),
            )
        )
        properties.set("Count", str(len(properties.findall("./Property"))))

    document = FreeCADAdapter().read(
        _rewrite_document_xml(_native_assembly_fixture(), gear)
    )
    assert document.assembly is not None
    mate = document.assembly.mates[0]
    assert str(mate.kind) == "gear"
    assert mate.value is not None
    assert mate.value.value == 4.0
    by_id = {item.id: item for item in document.parameters}
    assert {
        by_id[parameter_id].attributes["freecad_path"]
        for parameter_id in mate.parameter_ids
    } == {"Distance", "Distance2", "LengthMin", "AngleMax"}
    entities = {item.id: item for item in document.assembly.mate_entities}
    first = entities[mate.entity_ids[0]]
    assert first.source_entity_id == ""
    assert first.attributes["freecad_subelement"] == ""


def test_explicit_kit_mate_carrier_restores_without_native_joint_type() -> None:
    def carrier(root: ET.Element) -> None:
        properties = root.find("./ObjectData/Object[@name='Revolute']/Properties")
        assert properties is not None
        for property_name in ("JointType", "Proxy", "Suppressed"):
            value = properties.find(f"./Property[@name='{property_name}']")
            assert value is not None
            properties.remove(value)
        properties.extend(
            (
                _native_property(
                    "KitMateCarrier",
                    "App::PropertyBool",
                    "Bool",
                    {"value": "true"},
                ),
                _native_property(
                    "MateType",
                    "App::PropertyString",
                    "String",
                    {"value": "tangent"},
                ),
                _native_property(
                    "Alignment",
                    "App::PropertyString",
                    "String",
                    {"value": "anti_aligned"},
                ),
                _native_property(
                    "SourceSuppressed",
                    "App::PropertyBool",
                    "Bool",
                    {"value": "true"},
                ),
                _native_property(
                    "Driving",
                    "App::PropertyBool",
                    "Bool",
                    {"value": "false"},
                ),
            )
        )
        properties.set("Count", str(len(properties.findall("./Property"))))

    document = FreeCADAdapter().read(
        _rewrite_document_xml(_native_assembly_fixture(), carrier)
    )
    assert document.assembly is not None
    mate = document.assembly.mates[0]
    assert str(mate.kind) == "tangent"
    assert str(mate.alignment) == "anti_aligned"
    assert mate.suppressed
    assert not mate.driving


def test_strict_sldprt_to_fcstd_rejects_opaque_native_portions(
    tmp_path,
) -> None:
    output = tmp_path / "blocked.FCStd"
    with pytest.raises(ApplicationUsabilityError) as captured:
        convert(SAMPLE, output, allow_carrier=False)
    assert "opaque_source_data" in captured.value.issues
    assert not output.exists()


def test_direct_fcstd_roundtrip_preserves_interchange_and_brep(tmp_path) -> None:
    output = tmp_path / "example.FCStd"
    result = convert(SAMPLE, output, allow_carrier=True)
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
        assert "Fillet1.Edges" not in names
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
    convert(SAMPLE, output, allow_carrier=True)
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
        assert types.count("Part::Fillet") == 0
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
        fillet = root.find("./Objects/Object[@name='Fillet1']")
        assert fillet is not None
        assert fillet.get("type") == "Part::Feature"
        executable = root.find(
            "./ObjectData/Object[@name='Fillet1']/Properties/Property[@name='NativeExecutable']/Bool"
        )
        reason = root.find(
            "./ObjectData/Object[@name='Fillet1']/Properties/Property[@name='NativeExecutionReason']/String"
        )
        assert executable is not None and executable.get("value") == "false"
        assert reason is not None
        assert reason.get("value") == "topology_selection_not_statically_provable"
        xml = archive.read("Document.xml")
        assert b"KitMetadata" in xml


def test_fcstd_intersection_emits_native_common() -> None:
    source = neutral_document()
    first = replace(
        source.feature_timeline[0],
        operation=BooleanOperation.CREATE,
    )
    second = replace(
        first,
        id="feature:intersection",
        name="Intersection",
        order=1,
        input_feature_ids=(first.id,),
        operation=BooleanOperation.INTERSECT,
    )
    source = replace(
        source,
        feature_timeline=(first, second),
        bodies=(replace(source.bodies[0], final_feature_id=second.id),),
    )
    destination = io.BytesIO()
    FreeCADAdapter().write(source, destination)
    data = destination.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    declaration = root.find("./Objects/Object[@type='Part::Common']")
    assert declaration is not None
    name = declaration.get("name")
    base = root.find(
        f"./ObjectData/Object[@name='{name}']/Properties/Property[@name='Base']/Link"
    )
    tool = root.find(
        f"./ObjectData/Object[@name='{name}']/Properties/Property[@name='Tool']/Link"
    )
    assert base is not None and base.get("value") == "Boss1"
    assert tool is not None and tool.get("value") == "Intersection_Profile"
    assert FreeCADAdapter().read(data) == source


def test_fcstd_output_is_deterministic(tmp_path) -> None:
    first = tmp_path / "first.FCStd"
    second = tmp_path / "second.FCStd"
    convert(SAMPLE, first, allow_carrier=True)
    convert(SAMPLE, second, allow_carrier=True)
    assert first.read_bytes() == second.read_bytes()


def test_fcstd_stream_probe_does_not_consume_input(tmp_path) -> None:
    output = tmp_path / "example.FCStd"
    result = convert(SAMPLE, output, allow_carrier=True)
    stream = io.BytesIO(output.read_bytes())
    assert FreeCADAdapter().probe(stream).confidence == 1.0
    assert stream.tell() == 0
    assert open_document(stream) == result.document


def test_generic_fcstd_is_not_claimed_as_readable() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("Document.xml", "<Document/>")
    assert FreeCADAdapter().probe(stream.getvalue()).confidence == 0.0


def test_opaque_only_native_fcstd_roundtrips_without_kit_metadata() -> None:
    source = _native_archive(
        (
            (
                "Opaque",
                "App::FeaturePython",
                (),
                (
                    _native_property(
                        "Label",
                        "App::PropertyString",
                        "String",
                        {"value": "Opaque"},
                    ),
                    _native_property(
                        "Token",
                        "App::PropertyString",
                        "String",
                        {"value": "retained"},
                    ),
                ),
            ),
        ),
        {},
        {"Opaque": {"id": "41", "touched": True}},
    )
    adapter = FreeCADAdapter()
    assert adapter.probe(source).confidence == 0.95
    document = adapter.read(source)
    assert document.validate() == ()
    assert document.feature_timeline == ()
    assert len(document.brep_payloads) == 2
    payload = next(
        payload
        for payload in document.brep_payloads
        if payload.kind == "native_document"
    )
    assert payload.kind == "native_document"
    assert payload.format_id == "freecad.fcstd"
    assert payload.role == PayloadRole.DOCUMENT
    assert payload.file_extension == ".FCStd"
    assert payload.data == source
    assert Capability.NATIVE_PAYLOADS in document.capabilities
    assert Capability.BREP not in document.capabilities
    without_brep = adapter.read(source, ReadOptions(include_brep=False))
    assert without_brep.brep_payloads == document.brep_payloads
    output = io.BytesIO()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
        opaque = root.find("./ObjectData/Object[@name='Opaque']")
        assert opaque is not None
        token = opaque.find("./Properties/Property[@name='Token']/String")
        assert token is not None
        assert token.get("value") == "retained"
        declaration = root.find("./Objects/Object[@name='Opaque']")
        assert declaration is not None
        assert declaration.attrib == {
            "type": "App::FeaturePython",
            "name": "Opaque",
            "id": "41",
            "Touched": "1",
        }
        assert "interchange/document.json" not in archive.namelist()
    assert output.getvalue() == source
    assert adapter.read(output.getvalue()) == document


@pytest.mark.parametrize("carrier_suffix", (".SLDPRT", ".CATPart"))
def test_unknown_native_fcstd_data_survives_foreign_carrier_and_exact_replay(
    carrier_suffix: str, tmp_path: Path
) -> None:
    source_data = _native_archive(
        (
            (
                "FutureResult",
                "FutureWorkbench::SolverResult",
                (),
                (
                    _native_property(
                        "Label",
                        "App::PropertyString",
                        "String",
                        {"value": "Future Result"},
                    ),
                    _native_property(
                        "SolverState",
                        "FutureWorkbench::PropertyState",
                        "FutureState",
                        {"encoding": "opaque", "value": "future-state"},
                    ),
                ),
            ),
        ),
        {"FutureWorkbench/state.bin": b"future opaque state\x00\xff"},
    )
    source = tmp_path / "Future.FCStd"
    source.write_bytes(source_data)
    carrier = tmp_path / f"Future{carrier_suffix}"
    convert(source, carrier, allow_carrier=True)
    carried = open_document(carrier)
    native_document = next(
        payload
        for payload in carried.brep_payloads
        if payload.id == "freecad:native-document"
    )
    native_binding = next(
        payload
        for payload in carried.brep_payloads
        if payload.id == "freecad:native-document-binding"
    )
    assert native_document.data == source_data
    assert native_binding.data == hashlib.sha256(source_data).digest()
    future_object = next(
        value
        for value in carried.metadata["freecad"]["objects"]
        if value["name"] == "FutureResult"
    )
    assert future_object["properties"]["SolverState"]["children"][0]["attributes"] == {
        "encoding": "opaque",
        "value": "future-state",
    }
    restored = tmp_path / "Restored.FCStd"
    result = convert(carrier, restored)
    assert result.output.metadata["compatibility"] == "native-exact"
    assert restored.read_bytes() == source_data
    with zipfile.ZipFile(restored) as archive:
        assert (
            archive.read("FutureWorkbench/state.bin") == b"future opaque state\x00\xff"
        )


def test_self_contained_native_part_restores_editable_data() -> None:
    data = _native_part_fixture()
    adapter = FreeCADAdapter()
    assert adapter.probe(data).confidence == 0.95
    document = adapter.read(data)
    assert document.validate() == ()
    assert len(document.sketches) == 1
    assert [str(entity.kind) for entity in document.sketches[0].entities] == [
        "circle",
        "point",
        "ellipse",
        "spline",
    ]
    assert [
        str(constraint.kind) for constraint in document.sketches[0].constraints
    ] == [
        "diameter",
        "angle",
        "point_on_object",
    ]
    angle = next(
        parameter
        for parameter in document.parameters
        if parameter.attributes.get("freecad_path") == "Constraints[1]"
    )
    assert angle.value.value == 1.5707963267948966
    assert angle.value.unit == "rad"
    assert [feature.name for feature in document.feature_timeline] == ["Pad"]
    assert document.bodies[0].final_feature_id == "freecad:feature:Pad"
    assert document.brep_payloads[0].data == (
        b"\nCASCADE Topology V1, (c) Matra-Datavision\nfixture\n"
    )
    assert (
        sum(parameter.expression is not None for parameter in document.parameters) == 2
    )
    native_constraint = document.sketches[0].constraints[2]
    slots = native_constraint.attributes["freecad_reference_slots"]
    assert [slot["freecad_geometry_index"] for slot in slots] == [1, -3, -2000]
    sketch_model = document.sketches[0]
    circle_entity = sketch_model.entities[0]
    edited_circle = replace(
        circle_entity,
        geometry=replace(circle_entity.geometry, radius=7.5),
    )
    edited_sketch = replace(
        sketch_model,
        entities=(edited_circle, *sketch_model.entities[1:]),
    )
    document = replace(document, sketches=(edited_sketch,))
    output = io.BytesIO()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    sketch = root.find("./ObjectData/Object[@name='Sketch']")
    assert sketch is not None
    assert [
        item.get("type")
        for item in sketch.findall(
            "./Properties/Property[@name='Geometry']/GeometryList/Geometry"
        )
    ] == [
        "Part::GeomCircle",
        "Part::GeomPoint",
        "Part::GeomEllipse",
        "Part::GeomBSplineCurve",
    ]
    circle = sketch.find(
        "./Properties/Property[@name='Geometry']/GeometryList/Geometry/Circle"
    )
    assert circle is not None
    assert float(circle.get("Radius", "")) == 7.5
    encoded_constraints = sketch.findall(
        "./Properties/Property[@name='Constraints']/ConstraintList/Constrain"
    )
    assert len(encoded_constraints) == 3
    assert encoded_constraints[2].get("Type") == "13"
    assert encoded_constraints[2].get("Second") == "-3"
    pad = root.find("./ObjectData/Object[@name='Pad']")
    assert pad is not None
    assert len(pad.findall("./Properties/Property[@name='Shape']")) == 1


def test_native_replay_applies_edited_support_plane_placement() -> None:
    adapter = FreeCADAdapter()
    document = adapter.read(_native_part_fixture())
    plane = document.support_planes[0]
    edited_plane = replace(
        plane,
        transform=replace(plane.transform, origin=Vector3(12.0, 34.0, 56.0)),
    )
    output = io.BytesIO()
    adapter.write(replace(document, support_planes=(edited_plane,)), output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    placement = root.find(
        "./ObjectData/Object[@name='XY_Plane']/Properties/"
        "Property[@name='Placement']/PropertyPlacement"
    )
    assert placement is not None
    assert tuple(float(placement.get(name, "")) for name in ("Px", "Py", "Pz")) == (
        12.0,
        34.0,
        56.0,
    )


def test_native_replay_serializes_feature_suppression_without_source_property() -> None:
    adapter = FreeCADAdapter()
    document = adapter.read(_native_part_fixture())
    feature = document.feature_timeline[0]
    output = io.BytesIO()
    adapter.write(
        replace(document, feature_timeline=(replace(feature, suppressed=True),)),
        output,
    )
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    suppressed = root.find(
        "./ObjectData/Object[@name='Pad']/Properties/Property[@name='Suppressed']/Bool"
    )
    assert suppressed is not None
    assert suppressed.get("value") == "true"


def test_native_sketch_shape_sidecars_remain_routed_to_the_sketch() -> None:
    def shape_property(owner: str, element_map: str) -> ET.Element:
        node = _native_property(
            "Shape",
            "Part::PropertyPartShape",
            "Part",
            {"ElementMap": element_map, "file": f"{owner}.Shape.brp"},
        )
        element_map_node = ET.SubElement(node, "ElementMap", {"new": "1", "count": "1"})
        ET.SubElement(element_map_node, "Element", {"key": "Dummy", "value": "Dummy"})
        ET.SubElement(node, "ElementMap2", {"file": f"{owner}.Shape.Map.txt"})
        return node

    sketch_brep = b"\nCASCADE Topology V1, (c) Matra-Datavision\nsketch\n"
    final_brep = b"\nCASCADE Topology V1, (c) Matra-Datavision\nfinal\n"
    sketch_map = b"BeginElementMap v1\nSketch map\nEndMap\n"
    final_map = b"BeginElementMap v1\nFinal map\nEndMap\n"
    source = _native_archive(
        (
            (
                "Sketch",
                "Sketcher::SketchObject",
                (),
                (
                    _native_property(
                        "Label",
                        "App::PropertyString",
                        "String",
                        {"value": "Sketch"},
                    ),
                    _native_property(
                        "Geometry",
                        "Part::PropertyGeometryList",
                        "GeometryList",
                        {"count": "0"},
                    ),
                    _native_property(
                        "Constraints",
                        "Sketcher::PropertyConstraintList",
                        "ConstraintList",
                        {"count": "0"},
                    ),
                    shape_property("Sketch", "0.15.70200.5"),
                ),
            ),
            (
                "Final",
                "Part::Feature",
                ("Sketch",),
                (
                    _native_property(
                        "Label",
                        "App::PropertyString",
                        "String",
                        {"value": "Final"},
                    ),
                    shape_property("Final", "1.15.70200.5"),
                ),
            ),
        ),
        {
            "Sketch.Shape.brp": sketch_brep,
            "Sketch.Shape.Map.txt": sketch_map,
            "Final.Shape.brp": final_brep,
            "Final.Shape.Map.txt": final_map,
        },
    )
    adapter = FreeCADAdapter()
    document = adapter.read(source)
    payloads = {payload.source_stream: payload for payload in document.brep_payloads}
    assert payloads["Sketch.Shape.brp"].data == sketch_brep
    assert payloads["Sketch.Shape.brp"].attributes["freecad_sidecars"] == [
        {"source_stream": "Sketch.Shape.Map.txt", "data": sketch_map}
    ]
    assert payloads["Final.Shape.brp"].data == final_brep
    output = io.BytesIO()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        assert archive.read("Sketch.Shape.brp") == sketch_brep
        assert archive.read("Sketch.Shape.Map.txt") == sketch_map
        assert archive.read("Final.Shape.brp") == final_brep
        assert archive.read("Final.Shape.Map.txt") == final_map
        root = ET.fromstring(archive.read("Document.xml"))
    sketch_shape = root.find(
        "./ObjectData/Object[@name='Sketch']/Properties/Property[@name='Shape']"
    )
    final_shape = root.find(
        "./ObjectData/Object[@name='Final']/Properties/Property[@name='Shape']"
    )
    assert sketch_shape is not None
    assert final_shape is not None
    assert sketch_shape.find("./Part").attrib == {
        "ElementMap": "0.15.70200.5",
        "file": "Sketch.Shape.brp",
    }
    assert sketch_shape.find("./ElementMap").attrib == {"new": "1", "count": "1"}
    assert sketch_shape.find("./ElementMap/Element").attrib == {
        "key": "Dummy",
        "value": "Dummy",
    }
    assert sketch_shape.find("./ElementMap2").attrib == {"file": "Sketch.Shape.Map.txt"}
    assert final_shape.find("./Part").attrib == {
        "ElementMap": "1.15.70200.5",
        "file": "Final.Shape.brp",
    }
    assert final_shape.find("./ElementMap2").attrib == {"file": "Final.Shape.Map.txt"}


def test_native_string_hasher_root_and_table_roundtrip_in_stream_order() -> None:
    table = b"StringTableStart v1 0\n"
    with zipfile.ZipFile(io.BytesIO(_native_part_fixture())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
        entries = [
            (name, archive.read(name))
            for name in archive.namelist()
            if name != "Document.xml"
        ]
    root.set("StringHasher", "1")
    root.insert(
        0,
        ET.Element(
            "StringHasher",
            {"saveall": "0", "threshold": "0", "count": "0", "new": "1"},
        ),
    )
    root.insert(1, ET.Element("StringHasher2", {"file": "StringHasher.Table.txt"}))
    source = io.BytesIO()
    with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "Document.xml", ET.tostring(root, encoding="utf-8", xml_declaration=True)
        )
        archive.writestr("StringHasher.Table.txt", table)
        for name, data in entries:
            archive.writestr(name, data)
    adapter = FreeCADAdapter()
    document = adapter.read(source.getvalue())
    string_hasher = document.metadata["freecad"]["string_hasher"]
    assert string_hasher["attribute"] == "1"
    assert string_hasher["entries"] == [
        {"source_stream": "StringHasher.Table.txt", "data": table}
    ]
    output = io.BytesIO()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        assert archive.namelist()[:3] == [
            "Document.xml",
            "StringHasher.Table.txt",
            "Pad.Shape.brp",
        ]
        assert archive.read("StringHasher.Table.txt") == table
        restored_root = ET.fromstring(archive.read("Document.xml"))
    assert restored_root.get("StringHasher") == "1"
    hasher = restored_root.find("./StringHasher")
    hasher_table = restored_root.find("./StringHasher2")
    assert hasher is not None
    assert hasher.attrib == {
        "saveall": "0",
        "threshold": "0",
        "count": "0",
        "new": "1",
    }
    assert hasher_table is not None
    assert hasher_table.attrib == {"file": "StringHasher.Table.txt"}


def test_native_part_graph_preserves_source_order_opaque_objects_and_empty_shapes() -> (
    None
):
    def shape_property(name: str, source: str, mapped: bool = False) -> ET.Element:
        node = _native_property(
            name,
            "Part::PropertyPartShape",
            "Part",
            {"ElementMap": "1.15.70200.5", "file": source},
        )
        ET.SubElement(node, "ElementMap")
        if mapped:
            ET.SubElement(node, "ElementMap2", {"file": source + ".Map.txt"})
        return node

    attachment = _native_property(
        "AttachmentSupport",
        "App::PropertyLinkSubList",
        "LinkSubList",
        {"count": "1"},
    )
    ET.SubElement(attachment[0], "Link", {"obj": "XY_Plane", "sub": ""})
    profile = _native_property(
        "Profile", "App::PropertyLinkSub", "LinkSub", {"value": "Sketch", "count": "0"}
    )
    body_properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "Body"}),
        _native_link_list("Group", ("Sketch", "Pad")),
        shape_property("Shape", "Body.Shape.brp", True),
        _native_property("Tip", "App::PropertyLink", "Link", {"value": "Pad"}),
        _native_property("Visibility", "App::PropertyBool", "Bool", {"value": "true"}),
    )
    opaque_properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "Opaque"}),
        _native_property(
            "Token", "App::PropertyString", "String", {"value": "retained"}
        ),
        _native_property(
            "Blob",
            "App::PropertyFileIncluded",
            "FileIncluded",
            {"file": "Blob.bin"},
        ),
    )
    plane_properties = (
        _native_property(
            "Label", "App::PropertyString", "String", {"value": "XY_Plane"}
        ),
        _native_placement(),
        _native_property("Visibility", "App::PropertyBool", "Bool", {"value": "false"}),
    )
    sketch_properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "Sketch"}),
        attachment,
        _native_property(
            "Geometry", "Part::PropertyGeometryList", "GeometryList", {"count": "0"}
        ),
        _native_property(
            "Constraints",
            "Sketcher::PropertyConstraintList",
            "ConstraintList",
            {"count": "0"},
        ),
        shape_property("InternalShape", "Sketch.InternalShape.brp"),
        _native_placement(),
        shape_property("Shape", "Sketch.Shape.brp", True),
        _native_property("Visibility", "App::PropertyBool", "Bool", {"value": "false"}),
    )
    pad_properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "Pad"}),
        shape_property("AddSubShape", "Pad.AddSubShape.brp", True),
        profile,
        _native_property("Length", "App::PropertyLength", "Float", {"value": "25"}),
        _native_property("Type", "App::PropertyEnumeration", "Integer", {"value": "0"}),
        _native_property("Reversed", "App::PropertyBool", "Bool", {"value": "false"}),
        _native_property("Midplane", "App::PropertyBool", "Bool", {"value": "false"}),
        shape_property("Shape", "Pad.Shape.brp", True),
        shape_property("SuppressedShape", "Pad.SuppressedShape.brp"),
        _native_property("Suppressed", "App::PropertyBool", "Bool", {"value": "false"}),
        _native_property("Visibility", "App::PropertyBool", "Bool", {"value": "true"}),
    )
    body_transient = ET.Element(
        "_Property",
        {
            "name": "_ElementMapVersion",
            "type": "App::PropertyString",
            "status": "234881024",
        },
    )
    sketch_transient = ET.Element(
        "_Property",
        {
            "name": "_ElementMapVersion",
            "type": "App::PropertyString",
            "status": "234881024",
        },
    )
    pad_transients = (
        ET.Element(
            "_Property",
            {
                "name": "PreviewShape",
                "type": "Part::PropertyPartShape",
                "status": "152",
            },
        ),
        ET.Element(
            "_Property",
            {
                "name": "_Body",
                "type": "App::PropertyLinkHidden",
                "status": "251658240",
            },
        ),
        ET.Element(
            "_Property",
            {
                "name": "_ElementMapVersion",
                "type": "App::PropertyString",
                "status": "234881024",
            },
        ),
    )
    entries = {
        "Body.Shape.brp": b"\nCASCADE Topology V1, (c) Matra-Datavision\nbody\n",
        "Blob.bin": b"opaque-native-stream",
        "Body.Shape.brp.Map.txt": b"Body map",
        "Sketch.InternalShape.brp": b"",
        "Sketch.Shape.brp": b"\nCASCADE Topology V1, (c) Matra-Datavision\nsketch\n",
        "Sketch.Shape.brp.Map.txt": b"Sketch map",
        "Pad.AddSubShape.brp": b"\nCASCADE Topology V1, (c) Matra-Datavision\nadd\n",
        "Pad.AddSubShape.brp.Map.txt": b"Add map",
        "Pad.Shape.brp": b"\nCASCADE Topology V1, (c) Matra-Datavision\npad\n",
        "Pad.Shape.brp.Map.txt": b"Pad map",
        "Pad.SuppressedShape.brp": b"",
    }
    source = _native_archive(
        (
            ("Body", "PartDesign::Body", ("Sketch", "Pad"), body_properties),
            ("Opaque", "App::FeaturePython", (), opaque_properties),
            ("XY_Plane", "App::Plane", (), plane_properties),
            ("Sketch", "Sketcher::SketchObject", ("XY_Plane",), sketch_properties),
            ("Pad", "PartDesign::Pad", ("Body", "Sketch"), pad_properties),
        ),
        entries,
        {
            "Body": {
                "id": "1",
                "extensions": ("App::OriginGroupExtension",),
                "transient_properties": (body_transient,),
            },
            "Opaque": {"id": "50"},
            "XY_Plane": {"id": "3"},
            "Sketch": {
                "id": "9",
                "extensions": ("Part::AttachExtension",),
                "transient_properties": (sketch_transient,),
            },
            "Pad": {
                "id": "12",
                "touched": True,
                "extensions": (
                    "App::SuppressibleExtension",
                    "Part::PreviewExtension",
                ),
                "transient_properties": pad_transients,
            },
        },
    )
    adapter = FreeCADAdapter()
    document = adapter.read(source)
    assert [item["name"] for item in document.metadata["freecad"]["objects"]] == [
        "Body",
        "Opaque",
        "XY_Plane",
        "Sketch",
        "Pad",
    ]
    assert {payload.source_stream: payload.data for payload in document.brep_payloads}[
        "Sketch.InternalShape.brp"
    ] == b""
    assert document.metadata["freecad"]["entries"] == [
        {"source_stream": "Blob.bin", "data": b"opaque-native-stream"}
    ]
    output = io.BytesIO()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        names = archive.namelist()
        assert names[: 1 + len(entries)] == ["Document.xml", *entries]
        assert archive.read("Blob.bin") == b"opaque-native-stream"
        assert archive.read("Sketch.InternalShape.brp") == b""
        assert archive.read("Pad.SuppressedShape.brp") == b""
        root = ET.fromstring(archive.read("Document.xml"))
    declarations = root.findall("./Objects/Object")
    assert [item.get("name") for item in declarations[:5]] == [
        "Body",
        "Opaque",
        "XY_Plane",
        "Sketch",
        "Pad",
    ]
    assert [item.get("type") for item in declarations[:5]] == [
        "PartDesign::Body",
        "App::FeaturePython",
        "App::Plane",
        "Sketcher::SketchObject",
        "PartDesign::Pad",
    ]
    assert [item.get("id") for item in declarations[:5]] == ["1", "50", "3", "9", "12"]
    assert declarations[4].get("Touched") == "1"
    objects = {
        item.get("name", ""): item for item in root.findall("./ObjectData/Object")
    }
    assert [
        item.get("name") for item in objects["Opaque"].findall("./Properties/Property")
    ] == ["Label", "Token", "Blob"]
    assert (
        objects["Opaque"]
        .find("./Properties/Property[@name='Token']/String")
        .get("value")
        == "retained"
    )
    assert [
        item.get("type") for item in objects["Pad"].findall("./Extensions/Extension")
    ] == ["App::SuppressibleExtension", "Part::PreviewExtension"]
    assert [
        item.get("name") for item in objects["Pad"].findall("./Properties/_Property")
    ] == ["PreviewShape", "_Body", "_ElementMapVersion"]
    body_shape = objects["Body"].find("./Properties/Property[@name='Shape']/Part")
    assert body_shape is not None
    assert body_shape.get("file") == "Body.Shape.brp"
    assert objects["Pad"].find("./Properties/Property[@name='Sketches']") is None


def test_self_contained_native_assembly_restores_links_and_joints() -> None:
    document = FreeCADAdapter().read(_native_assembly_fixture())
    assert document.validate() == ()
    assert document.assembly is not None
    assert len(document.assembly.definitions) == 2
    assert len(document.assembly.instances) == 1
    assert document.assembly.instances[0].fixed
    assert [str(mate.kind) for mate in document.assembly.mates] == ["hinge"]
    revolute = document.assembly.mates[0]
    entities = {entity.id: entity for entity in document.assembly.mate_entities}
    assert [
        entities[entity_id].source_entity_id for entity_id in revolute.entity_ids
    ] == [
        "Face1",
        "Edge1",
        "Face2",
    ]


def test_custom_assembly_types_and_link_property_restore_structurally() -> None:
    def custom_types(root: ET.Element) -> None:
        declarations = {
            item.get("name", ""): item for item in root.findall("./Objects/Object")
        }
        declarations["Assembly"].set("type", "Vendor::FutureAssemblyRoot")
        declarations["Joints"].set("type", "Vendor::FutureConstraintCollection")
        declarations["PartLink"].set("type", "Vendor::FutureOccurrenceLink")
        declarations["Grounded"].set("type", "Vendor::FutureFixedObject")
        declarations["Revolute"].set("type", "Vendor::FutureKinematicObject")
        linked = root.find(
            "./ObjectData/Object[@name='PartLink']/Properties/"
            "Property[@name='LinkedObject']"
        )
        assert linked is not None
        linked.set("name", "ComponentLink")

    adapter = FreeCADAdapter()
    document = adapter.read(
        _rewrite_document_xml(_native_assembly_fixture(), custom_types)
    )
    assert document.assembly is not None
    assert len(document.assembly.instances) == 1
    assert len(document.assembly.mates) == 1
    assert document.assembly.attributes["freecad"]["type_id"] == (
        "Vendor::FutureAssemblyRoot"
    )
    assert document.assembly.instances[0].attributes["freecad"]["type_id"] == (
        "Vendor::FutureOccurrenceLink"
    )
    assert document.assembly.mate_groups[0].attributes["freecad"]["type_id"] == (
        "Vendor::FutureConstraintCollection"
    )
    output = io.BytesIO()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    types = {
        item.get("name", ""): item.get("type", "")
        for item in root.findall("./Objects/Object")
    }
    assert "Vendor::FutureAssemblyRoot" in types.values()
    assert "Vendor::FutureConstraintCollection" in types.values()
    assert "Vendor::FutureOccurrenceLink" in types.values()
    assert "Vendor::FutureFixedObject" in types.values()
    assert "Vendor::FutureKinematicObject" in types.values()
    link = next(name for name, type_id in types.items() if type_id.endswith("Link"))
    assert (
        root.find(
            f"./ObjectData/Object[@name='{link}']/Properties/"
            "Property[@name='ComponentLink']/XLink"
        )
        is not None
    )


def test_native_assembly_preserves_unrepresented_objects_and_streams() -> None:
    adapter = FreeCADAdapter()
    document = adapter.read(_native_assembly_fixture())
    assert document.metadata["freecad"]["entries"] == [
        {"source_stream": "Blob.bin", "data": b"opaque"}
    ]
    output = io.BytesIO()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        names = set(archive.namelist())
        assert archive.read("Blob.bin") == b"opaque"
        root = ET.fromstring(archive.read("Document.xml"))
    declarations = {
        item.get("name", ""): item.get("type", "")
        for item in root.findall("./Objects/Object")
    }
    assert declarations["Opaque"] == "App::FeaturePython"
    assert "Assembly::AssemblyObject" in declarations.values()
    assert "App::Link" in declarations.values()
    objects = {
        item.get("name", ""): item for item in root.findall("./ObjectData/Object")
    }
    blob = objects["Opaque"].find("./Properties/Property[@name='Blob']/File")
    assert blob is not None
    assert blob.get("file") == "Blob.bin"
    assert any(
        item.find("./Properties/Property[@name='JointType']") is not None
        for item in objects.values()
    )
    references = {
        node.get("file", "")
        for node in root.findall(".//*[@file]")
        if node.tag != "XLink" and node.get("file", "")
    }
    assert references <= names


def test_native_assembly_writes_exact_joint_references_and_ground_lock() -> None:
    adapter = FreeCADAdapter()
    document = adapter.read(_native_assembly_fixture())
    output = io.BytesIO()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    types = {
        item.get("name", ""): item.get("type", "")
        for item in root.findall("./Objects/Object")
    }
    objects = {
        item.get("name", ""): item for item in root.findall("./ObjectData/Object")
    }
    assembly_name = next(
        name for name, type_id in types.items() if type_id == "Assembly::AssemblyObject"
    )
    link_name = next(name for name, type_id in types.items() if type_id == "App::Link")
    link_properties = {
        item.get("name", ""): item
        for item in objects[link_name].findall("./Properties/Property")
    }
    assert int(link_properties["Placement"].get("status", "0")) & 4
    assert int(link_properties["LinkPlacement"].get("status", "0")) & 4
    grounded = [
        item
        for item in objects.values()
        if item.find("./Properties/Property[@name='ObjectToGround']") is not None
    ]
    assert len(grounded) == 1
    grounded_name = grounded[0].get("name", "")
    grounded_link_property = grounded[0].find(
        "./Properties/Property[@name='ObjectToGround']"
    )
    assert grounded_link_property is not None
    grounded_link = grounded_link_property.find("./Link")
    grounded_proxy = grounded[0].find("./Properties/Property[@name='Proxy']/Python")
    assert types[grounded_name] == "App::FeaturePython"
    assert grounded_link_property.get("type") == "App::PropertyLink"
    assert grounded_link is not None
    assert grounded_link.get("value") == link_name
    assert grounded_proxy is not None
    assert grounded_proxy.attrib == {
        "value": "bnVsbA==",
        "encoded": "yes",
        "json": "yes",
    }
    joints = [
        item
        for item in objects.values()
        if item.find("./Properties/Property[@name='JointType']") is not None
    ]
    assert len(joints) == 1
    joint_name = joints[0].get("name", "")
    reference1 = joints[0].find("./Properties/Property[@name='Reference1']/XLink")
    reference2 = joints[0].find("./Properties/Property[@name='Reference2']/XLink")
    assert reference1 is not None
    assert reference2 is not None
    assert reference1.get("name") == assembly_name
    assert reference2.get("name") == assembly_name
    assert [item.get("value") for item in reference1.findall("./Sub")] == [
        f"{link_name}.Face1",
        f"{link_name}.Edge1",
    ]
    assert [item.get("value") for item in reference2.findall("./Sub")] == [
        f"{link_name}.Face2"
    ]
    joint_groups = [
        name for name, type_id in types.items() if type_id == "Assembly::JointGroup"
    ]
    assert len(joint_groups) == 1
    group_links = objects[joint_groups[0]].findall(
        "./Properties/Property[@name='Group']/LinkList/Link"
    )
    assert [item.get("value") for item in group_links] == [
        grounded_name,
        joint_name,
    ]
    assert not any(
        item.find("./Properties/Property[@name='MateGroupId']") is not None
        for item in objects.values()
    )


def test_native_assembly_writes_component_geometry_and_reopens() -> None:
    adapter = FreeCADAdapter()
    document = adapter.read(_native_assembly_fixture(brep_model_brep(triangle_brep())))
    output = io.BytesIO()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
        types = {
            obj.get("name", ""): obj.get("type", "")
            for obj in root.findall("./Objects/Object")
        }
        component_groups = []
        for obj in root.findall("./ObjectData/Object"):
            definition_id = obj.find(
                "./Properties/Property[@name='DefinitionId']/String"
            )
            group = obj.find("./Properties/Property[@name='Group']/LinkList")
            if definition_id is not None and group is not None:
                component_groups.append([link.get("value", "") for link in group])
        assert any(group for group in component_groups)
        assert "Part::Feature" in types.values()
        shape_entries = [
            name for name in archive.namelist() if name.endswith(".Shape.brp")
        ]
        assert shape_entries
        assert all(archive.read(name) for name in shape_entries)
    restored = adapter.read(output.getvalue())
    assert restored == document
    assert restored.validate() == ()


def test_external_component_identity_includes_source_document(tmp_path) -> None:
    first = tmp_path / "First.FCStd"
    second = tmp_path / "Second.FCStd"
    first.write_bytes(_native_part_fixture())
    second.write_bytes(_native_part_fixture())
    assembly = tmp_path / "Assembly.FCStd"
    assembly.write_bytes(
        _native_external_assembly_fixture(
            (
                ("First", "App::Link", first.name, "Body"),
                ("Second", "App::Link", second.name, "Body"),
            )
        )
    )
    document = FreeCADAdapter().read(assembly)
    assert document.assembly is not None
    assert len(document.assembly.definitions) == 3
    assert len(document.assembly.documents) == 2
    assert (
        len({instance.definition_id for instance in document.assembly.instances}) == 2
    )
    assert not any(
        diagnostic.code == "freecad.unresolved_external_documents"
        for diagnostic in document.diagnostics
    )


def test_native_assembly_preserves_grouped_and_standalone_external_links(
    tmp_path,
) -> None:
    first = tmp_path / "First.FCStd"
    second = tmp_path / "Second.FCStd"
    first.write_bytes(_native_part_fixture())
    second.write_bytes(_native_part_fixture())
    source = tmp_path / "Mixed.FCStd"
    source.write_bytes(
        _native_external_assembly_fixture(
            (
                ("Grouped", "App::Link", first.name, "Body"),
                ("Standalone", "App::Link", second.name, "Body"),
            ),
            grouped_names=("Grouped",),
        )
    )
    adapter = FreeCADAdapter()
    document = adapter.read(source)
    assert document.assembly is not None
    assert [item.name for item in document.assembly.instances] == [
        "Grouped",
        "Standalone",
    ]
    assert len(document.assembly.documents) == 2
    output = tmp_path / "portable" / "Mixed.FCStd"
    result = adapter.write(document, output)
    assert result.metadata["component_file_count"] == 2
    with zipfile.ZipFile(output) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    links = [
        item.get("name", "")
        for item in root.findall("./Objects/Object")
        if item.get("type") in {"App::Link", "Assembly::AssemblyLink"}
    ]
    files = {
        item.get("file", "")
        for item in root.findall(".//XLink[@file]")
        if item.get("file", "")
    }
    assert len(links) == 2
    assert len(files) == 2
    assert all((output.parent / filename).is_file() for filename in files)
    restored = adapter.read(output)
    assert restored.assembly is not None
    assert len(restored.assembly.instances) == 2
    assert len(restored.assembly.documents) == 2


def test_native_link_only_document_writes_portable_external_files(tmp_path) -> None:
    source_directory = tmp_path / "source"
    child = source_directory / "nested" / "Child.FCStd"
    child.parent.mkdir(parents=True)
    child.write_bytes(_native_part_fixture())
    root = source_directory / "LinkOnly.FCStd"
    root.write_bytes(_native_link_only_fixture("nested/Child.FCStd"))
    adapter = FreeCADAdapter()
    document = adapter.read(root)
    assert document.assembly is None
    assert [
        item["file"] for item in document.metadata["freecad"]["external_documents"]
    ] == ["nested/Child.FCStd"]
    without_brep = adapter.read(root, ReadOptions(include_brep=False))
    linked_without_brep = without_brep.metadata["freecad"]["external_documents"][0][
        "document"
    ]
    assert not any(
        payload.role == PayloadRole.BREP
        for payload in linked_without_brep.brep_payloads
    )
    staging = tmp_path / "staging"
    destination = staging / "Portable.FCStd"
    result = adapter.write(document, destination)
    staging.rename(tmp_path / "relocated")
    destination = tmp_path / "relocated" / "Portable.FCStd"
    bundled = destination.parent / "Portable" / "Child.FCStd"
    assert bundled.is_file()
    assert result.metadata["external_document_file_count"] == 1
    assert result.metadata["external_document_bytes_written"] == bundled.stat().st_size
    with zipfile.ZipFile(destination) as archive:
        root_xml = ET.fromstring(archive.read("Document.xml"))
        linked = root_xml.find(
            "./ObjectData/Object[@name='PartLink']/Properties/"
            "Property[@name='LinkedObject']/XLink"
        )
        assert linked is not None
        assert linked.get("file") == "Portable/Child.FCStd"
        assert linked.get("stamp") == ""
        native_only = destination.parent / "NativeOnly.FCStd"
        with zipfile.ZipFile(native_only, "w", zipfile.ZIP_DEFLATED) as output:
            for info in archive.infolist():
                if info.filename != "interchange/document.json":
                    output.writestr(info, archive.read(info))
    restored = adapter.read(native_only)
    assert restored.assembly is None
    assert not any(
        diagnostic.code == "freecad.unresolved_external_documents"
        for diagnostic in restored.diagnostics
    )
    portable_stream = io.BytesIO()
    portable_result = adapter.write(document, portable_stream)
    assert portable_result.application_usable is False
    assert portable_result.metadata["carrier_embedded_reference_count"] == 1
    assert any(
        diagnostic.code == "freecad.references_embedded_without_files"
        for diagnostic in portable_result.diagnostics
    )
    portable_restored = adapter.read(portable_stream.getvalue())
    assert (
        portable_restored.metadata["freecad"]["external_documents"][0]["document"]
        == document.metadata["freecad"]["external_documents"][0]["document"]
    )
    nonportable = io.BytesIO()
    adapter.write(
        document,
        nonportable,
        WriteOptions(values={"portable": False}),
    )
    with zipfile.ZipFile(io.BytesIO(nonportable.getvalue())) as archive:
        nonportable_xml = ET.fromstring(archive.read("Document.xml"))
    original_link = nonportable_xml.find(
        "./ObjectData/Object[@name='PartLink']/Properties/"
        "Property[@name='LinkedObject']/XLink"
    )
    assert original_link is not None
    assert original_link.get("file") == "nested/Child.FCStd"


def test_nonportable_freecad_replay_requires_explicit_opt_in(tmp_path) -> None:
    child = tmp_path / "nested" / "Child.FCStd"
    child.parent.mkdir()
    child.write_bytes(_native_part_fixture())
    source = tmp_path / "LinkOnly.FCStd"
    source.write_bytes(_native_link_only_fixture("nested/Child.FCStd"))
    document = open_document(source)
    blocked = tmp_path / "blocked.FCStd"
    with pytest.raises(ApplicationUsabilityError) as captured:
        registry.write(
            document,
            blocked,
            options=WriteOptions(values={"portable": False}),
        )
    assert captured.value.requirements == ("referenced FreeCAD component files",)
    assert not blocked.exists()
    explicit = tmp_path / "explicit.FCStd"
    result = registry.write(
        document,
        explicit,
        options=WriteOptions(
            values={
                "portable": False,
                "allow_carrier": True,
                "require_self_contained": False,
            },
        ),
    )
    assert result.requirements == ("referenced FreeCAD component files",)
    assert result.metadata["native_self_contained"] is False
    assert result.metadata["referenced_files_written"] == 0
    assert result.near_lossless is False
    assert explicit.read_bytes() == source.read_bytes()


def test_native_freecad_part_exact_replay_remains_default_usable(tmp_path) -> None:
    source = tmp_path / "source.FCStd"
    source.write_bytes(_native_part_fixture())
    destination = tmp_path / "replay.FCStd"
    result = write_document(open_document(source), destination)
    assert result.metadata["mode"] == "exact_native_roundtrip"
    assert result.metadata["native_self_contained"] is True
    assert result.requirements == ()
    assert result.near_lossless is True
    assert destination.read_bytes() == source.read_bytes()


def _forged_native_brep_document(document, data: bytes):
    payload = next(
        value for value in document.brep_payloads if value.role is PayloadRole.BREP
    )
    forged_payload = replace(
        payload,
        data=data,
        sha256=hashlib.sha256(data).hexdigest(),
    )
    forged = replace(
        document,
        brep_payloads=tuple(
            forged_payload if value.id == payload.id else value
            for value in document.brep_payloads
        ),
    )
    return freecad_adapter_module._annotate_native_sources(forged)


@pytest.mark.parametrize("rebuild", (False, True))
def test_recomputed_semantic_digest_cannot_authorize_changed_native_brep(
    rebuild: bool,
) -> None:
    document = FreeCADAdapter().read(_native_part_fixture())
    forged_data = b"\nCASCADE Topology V1, (c) Matra-Datavision\nchanged-invalid\n"
    forged = _forged_native_brep_document(document, forged_data)
    assert freecad_adapter_module._unchanged_native_source(forged) is None
    output = io.BytesIO()
    result = FreeCADAdapter().write(
        forged,
        output,
        WriteOptions(values={"rebuild": rebuild}),
    )
    transfers = {value.capability: value for value in result.transfers}
    assert result.metadata.get("mode") != "exact_native_roundtrip"
    assert transfers[Capability.BREP].mode is TransferMode.CARRIER
    assert transfers[Capability.BREP].carrier_reason is CarrierReason.SOURCE_OPAQUE
    assert result.application_usable is False
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
        native_shape_files = tuple(
            value.get("file", "")
            for value in root.findall(".//Part[@file]")
            if value.get("file", "")
        )
        assert all(archive.read(name) != forged_data for name in native_shape_files)
    restored = FreeCADAdapter().read(output.getvalue())
    forged_payload_id = next(
        value.id for value in forged.brep_payloads if value.role is PayloadRole.BREP
    )
    restored_payload = next(
        value for value in restored.brep_payloads if value.id == forged_payload_id
    )
    assert restored_payload.data == forged_data


def test_root_envelope_cannot_authorize_changed_nested_brep(tmp_path) -> None:
    child = tmp_path / "Child.FCStd"
    child.write_bytes(_native_part_fixture())
    parent = tmp_path / "Parent.FCStd"
    parent.write_bytes(
        _native_external_assembly_fixture(
            (("Child", "Assembly::AssemblyLink", child.name, "Body"),)
        )
    )
    document = FreeCADAdapter().read(parent)
    assert document.assembly is not None
    nested_entry = next(
        value
        for value in document.assembly.documents
        if any(
            payload.role is PayloadRole.BREP
            for payload in getattr(value.document, "brep_payloads", ())
        )
    )
    forged_data = b"\nCASCADE Topology V1, (c) Matra-Datavision\nnested-invalid\n"
    forged_nested = _forged_native_brep_document(nested_entry.document, forged_data)
    assembly = replace(
        document.assembly,
        documents=tuple(
            (
                replace(value, document=forged_nested)
                if value.id == nested_entry.id
                else value
            )
            for value in document.assembly.documents
        ),
    )
    forged = freecad_adapter_module._annotate_native_sources(
        replace(document, assembly=assembly)
    )
    destination = tmp_path / "rebuilt" / "Parent.FCStd"
    result = write_document(forged, destination, values={"rebuild": True})
    transfers = {value.capability: value for value in result.transfers}
    assert transfers[Capability.BREP].mode is TransferMode.CARRIER
    assert transfers[Capability.BREP].carrier_reason is CarrierReason.SOURCE_OPAQUE
    assert result.application_usable is False
    component_files = tuple(destination.parent.rglob("*.FCStd"))
    assert destination in component_files
    assert len(component_files) > 1
    for component_file in component_files:
        with zipfile.ZipFile(component_file) as archive:
            root = ET.fromstring(archive.read("Document.xml"))
            native_shape_files = tuple(
                value.get("file", "")
                for value in root.findall(".//Part[@file]")
                if value.get("file", "")
            )
            assert all(archive.read(name) != forged_data for name in native_shape_files)


def test_native_assembly_link_recursively_restores_subassembly(tmp_path) -> None:
    child = tmp_path / "Child.FCStd"
    child.write_bytes(_native_assembly_fixture())
    parent = tmp_path / "Parent.FCStd"
    parent.write_bytes(
        _native_external_assembly_fixture(
            (("Child", "Assembly::AssemblyLink", child.name, "Assembly"),)
        )
    )
    document = FreeCADAdapter().read(parent)
    assert document.assembly is not None
    definition = next(
        item
        for item in document.assembly.definitions
        if item.id != document.assembly.root_definition_id
    )
    assert str(definition.kind) == "assembly"
    nested = document.assembly.document(definition.document_id)
    assert nested.assembly is not None
    assert len(nested.assembly.instances) == 1


def test_native_fcstd_rejects_missing_referenced_data() -> None:
    source = _native_part_fixture()
    stripped = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(source)) as input_archive:
        document_xml = input_archive.read("Document.xml")
    with zipfile.ZipFile(stripped, "w", zipfile.ZIP_DEFLATED) as output_archive:
        output_archive.writestr("Document.xml", document_xml)
    adapter = FreeCADAdapter()
    assert adapter.probe(stripped.getvalue()).confidence == 0.0
    with pytest.raises(FreeCADAdapterError, match="missing referenced data"):
        adapter.read(stripped.getvalue())


def test_native_fcstd_rejects_unsafe_object_names_on_read_and_write() -> None:
    properties = (
        _native_property("Label", "App::PropertyString", "String", {"value": "Bad"}),
    )
    unsafe = _native_archive((("../Bad", "App::FeaturePython", (), properties),), {})
    adapter = FreeCADAdapter()
    assert adapter.probe(unsafe).confidence == 0.0
    with pytest.raises(FreeCADAdapterError, match="unsafe or invalid"):
        adapter.read(unsafe)
    document = adapter.read(_native_part_fixture())
    freecad = dict(document.metadata["freecad"])
    objects = [dict(value) for value in freecad["objects"]]
    objects[0]["name"] = "../Bad"
    freecad["objects"] = objects
    invalid = replace(document, metadata={"freecad": freecad})
    output = io.BytesIO()
    with pytest.raises(ValueError, match="unsafe or invalid"):
        adapter.write(invalid, output)
    assert output.getvalue() == b""


def test_native_fcstd_rejects_excessive_xml_nesting_without_recursion() -> None:
    depth = 1200
    xml = (
        b'<?xml version="1.0" encoding="utf-8"?>'
        b'<Document SchemaVersion="4" ProgramVersion="1.0" FileVersion="1">'
        b'<Objects Count="1" Dependencies="1">'
        b'<ObjectDeps Name="Deep" Count="0"/>'
        b'<Object type="App::FeaturePython" name="Deep" id="1"/>'
        b'</Objects><ObjectData Count="1"><Object name="Deep">'
        b'<Properties Count="1" TransientCount="0">'
        b'<Property name="Deep" type="App::PropertyString">'
        + b"<N>" * depth
        + b"</N>" * depth
        + b"</Property></Properties></Object></ObjectData></Document>"
    )
    source = io.BytesIO()
    with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Document.xml", xml)
    adapter = FreeCADAdapter()
    assert adapter.probe(source.getvalue()).confidence == 0.0
    with pytest.raises(FreeCADAdapterError, match="nesting exceeds safe limits"):
        adapter.read(source.getvalue())


def test_kit_carrier_rejects_malformed_manifest_before_native_fallback() -> None:
    adapter = FreeCADAdapter()
    document = adapter.read(_native_part_fixture())
    valid = io.BytesIO()
    adapter.write(document, valid, WriteOptions(values={"rebuild": True}))
    malformed = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(valid.getvalue())) as source:
        with zipfile.ZipFile(malformed, "w", zipfile.ZIP_DEFLATED) as output:
            for info in source.infolist():
                if info.filename != "interchange/document.json":
                    output.writestr(info, source.read(info))
            output.writestr("interchange/document.json", b"{")
    assert adapter.probe(malformed.getvalue()).confidence == 0.0
    with pytest.raises(FreeCADAdapterError, match="corrupt"):
        adapter.read(malformed.getvalue())


@pytest.mark.parametrize("changed_copy", ("entry", "xml"))
def test_kit_carrier_rejects_divergent_valid_manifest_copies(
    changed_copy: str,
) -> None:
    adapter = FreeCADAdapter()
    valid = io.BytesIO()
    adapter.write(neutral_document(), valid)
    with zipfile.ZipFile(io.BytesIO(valid.getvalue())) as source:
        entries = {info.filename: source.read(info) for info in source.infolist()}
    changed = json.loads(entries["interchange/document.json"])
    changed["source"]["path"] = "different-source"
    canonical = json.dumps(
        changed, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if changed_copy == "entry":
        entries["interchange/document.json"] = canonical + b"\n"
    else:
        root = ET.fromstring(entries["Document.xml"])
        data_property = root.find(".//Property[@name='KitManifestData']/String")
        digest_property = root.find(".//Property[@name='KitManifestSHA256']/String")
        assert data_property is not None
        assert digest_property is not None
        data_property.set(
            "value", base64.b64encode(zlib.compress(canonical, 9)).decode("ascii")
        )
        digest_property.set("value", hashlib.sha256(canonical).hexdigest())
        entries["Document.xml"] = ET.tostring(
            root, encoding="utf-8", xml_declaration=True
        )
    divergent = io.BytesIO()
    with zipfile.ZipFile(divergent, "w", zipfile.ZIP_DEFLATED) as output:
        for name, value in entries.items():
            output.writestr(name, value)
    result = adapter.probe(divergent.getvalue())
    assert result.confidence == 0.0
    assert "copies do not match" in result.reason
    with pytest.raises(FreeCADAdapterError, match="copies do not match"):
        adapter.read(divergent.getvalue())


def test_kit_carrier_uses_document_xml_manifest_when_direct_entry_is_absent() -> None:
    adapter = FreeCADAdapter()
    document = neutral_document()
    valid = io.BytesIO()
    adapter.write(document, valid, WriteOptions(values={"rebuild": True}))
    legacy = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(valid.getvalue())) as source:
        with zipfile.ZipFile(legacy, "w", zipfile.ZIP_DEFLATED) as output:
            for info in source.infolist():
                if info.filename != "interchange/document.json":
                    output.writestr(info, source.read(info))
    assert adapter.probe(legacy.getvalue()).confidence == 1.0
    assert adapter.read(legacy.getvalue()) == document


def test_freecad_carrier_selects_configurations_by_id_and_name() -> None:
    configurations = (
        Configuration("configuration:a", "Shared", active=True),
        Configuration("configuration:b", "Second"),
        Configuration("configuration:c", "Shared"),
    )
    document = replace(neutral_document(), configurations=configurations)
    output = io.BytesIO()
    adapter = FreeCADAdapter()
    adapter.write(document, output)
    by_id = adapter.read(
        output.getvalue(), ReadOptions(configuration="configuration:b")
    )
    assert [item.id for item in by_id.configurations if item.active] == [
        "configuration:b"
    ]
    by_name = adapter.read(output.getvalue(), ReadOptions(configuration="Shared"))
    assert [item.id for item in by_name.configurations if item.active] == [
        "configuration:a",
        "configuration:c",
    ]


def test_freecad_rejects_unknown_carrier_and_native_configurations() -> None:
    adapter = FreeCADAdapter()
    carrier = io.BytesIO()
    adapter.write(neutral_document(), carrier)
    for source in (carrier.getvalue(), _native_part_fixture()):
        with pytest.raises(FreeCADAdapterError, match="configuration"):
            adapter.read(source, ReadOptions(configuration="missing-configuration"))


def test_native_freecad_selects_configuration_by_id_and_name() -> None:
    adapter = FreeCADAdapter()
    source = _native_part_fixture()
    configuration = adapter.read(source).configurations[0]
    for selected in (configuration.id, configuration.name):
        restored = adapter.read(source, ReadOptions(configuration=selected))
        assert [item.id for item in restored.configurations if item.active] == [
            configuration.id
        ]


def test_kit_carrier_probe_restores_and_validates_manifest_document() -> None:
    adapter = FreeCADAdapter()
    document = adapter.read(_native_part_fixture())
    valid = io.BytesIO()
    adapter.write(document, valid, WriteOptions(values={"rebuild": True}))
    invalid = io.BytesIO()
    invalid_manifest = b'{"foo":"bar"}'
    with zipfile.ZipFile(io.BytesIO(valid.getvalue())) as source:
        root = ET.fromstring(source.read("Document.xml"))
        data_property = root.find(".//Property[@name='KitManifestData']/String")
        digest_property = root.find(".//Property[@name='KitManifestSHA256']/String")
        assert data_property is not None
        assert digest_property is not None
        data_property.set(
            "value",
            base64.b64encode(zlib.compress(invalid_manifest, 9)).decode("ascii"),
        )
        digest_property.set("value", hashlib.sha256(invalid_manifest).hexdigest())
        with zipfile.ZipFile(invalid, "w", zipfile.ZIP_DEFLATED) as output:
            for info in source.infolist():
                if info.filename not in {
                    "Document.xml",
                    "interchange/document.json",
                }:
                    output.writestr(info, source.read(info))
            output.writestr(
                "Document.xml",
                ET.tostring(root, encoding="utf-8", xml_declaration=True),
            )
            output.writestr("interchange/document.json", invalid_manifest)
    result = adapter.probe(invalid.getvalue())
    assert result.confidence == 0.0
    assert "cannot be restored" in result.reason
    with pytest.raises(FreeCADAdapterError, match="cannot be restored"):
        adapter.read(invalid.getvalue())


@pytest.mark.parametrize(
    "document_xml",
    (None, b"not XML", b"<Document/>"),
    ids=("missing", "invalid", "empty"),
)
def test_kit_carrier_requires_valid_document_xml(document_xml: bytes | None) -> None:
    adapter = FreeCADAdapter()
    document = adapter.read(_native_part_fixture())
    valid = io.BytesIO()
    adapter.write(document, valid, WriteOptions(values={"rebuild": True}))
    with zipfile.ZipFile(io.BytesIO(valid.getvalue())) as source:
        manifest = source.read("interchange/document.json")
    invalid = io.BytesIO()
    with zipfile.ZipFile(invalid, "w", zipfile.ZIP_DEFLATED) as output:
        if document_xml is not None:
            output.writestr("Document.xml", document_xml)
        output.writestr("interchange/document.json", manifest)
    result = adapter.probe(invalid.getvalue())
    assert result.confidence == 0.0
    assert "Document.xml" in result.reason
    with pytest.raises(FreeCADAdapterError, match="Document.xml"):
        adapter.read(invalid.getvalue())


def test_kit_carrier_requires_every_non_xlink_referenced_stream() -> None:
    adapter = FreeCADAdapter()
    document = adapter.read(_native_part_fixture(brep_model_brep(triangle_brep())))
    valid = io.BytesIO()
    adapter.write(document, valid, WriteOptions(values={"rebuild": True}))
    invalid = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(valid.getvalue())) as source:
        root = ET.fromstring(source.read("Document.xml"))
        referenced = [
            node.get("file", "")
            for node in root.findall(".//*[@file]")
            if node.tag != "XLink" and node.get("file", "")
        ]
        assert referenced
        missing = referenced[0]
        with zipfile.ZipFile(invalid, "w", zipfile.ZIP_DEFLATED) as output:
            for info in source.infolist():
                if info.filename != missing:
                    output.writestr(info, source.read(info))
    result = adapter.probe(invalid.getvalue())
    assert result.confidence == 0.0
    assert "missing referenced data" in result.reason
    with pytest.raises(FreeCADAdapterError, match="missing referenced data"):
        adapter.read(invalid.getvalue())


def test_kit_carrier_rejects_deep_json_in_entry_and_embedded_property() -> None:
    raw = ('{"metadata":' + "[" * 2000 + "0" + "]" * 2000 + "}").encode("utf-8")
    native = _native_part_fixture()
    with zipfile.ZipFile(io.BytesIO(native)) as source:
        document_xml = source.read("Document.xml")
        native_entries = [
            (info.filename, source.read(info))
            for info in source.infolist()
            if info.filename != "Document.xml"
        ]
    direct = io.BytesIO()
    with zipfile.ZipFile(direct, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Document.xml", document_xml)
        for name, data in native_entries:
            archive.writestr(name, data)
        archive.writestr("interchange/document.json", raw)
    root = ET.fromstring(document_xml)
    properties = root.find("./ObjectData/Object/Properties")
    assert properties is not None
    properties.set("Count", str(int(properties.get("Count", "0")) + 3))
    encoded = base64.b64encode(zlib.compress(raw, 9)).decode("ascii")
    properties.extend(
        (
            _native_property(
                "KitManifestData",
                "App::PropertyString",
                "String",
                {"value": encoded},
            ),
            _native_property(
                "KitManifestEncoding",
                "App::PropertyString",
                "String",
                {"value": "zlib+base64+utf-8"},
            ),
            _native_property(
                "KitManifestSHA256",
                "App::PropertyString",
                "String",
                {"value": hashlib.sha256(raw).hexdigest()},
            ),
        )
    )
    embedded = io.BytesIO()
    with zipfile.ZipFile(embedded, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "Document.xml", ET.tostring(root, encoding="utf-8", xml_declaration=True)
        )
        for name, data in native_entries:
            archive.writestr(name, data)
    adapter = FreeCADAdapter()
    for hostile in (direct.getvalue(), embedded.getvalue()):
        result = adapter.probe(hostile)
        assert result.confidence == 0.0
        assert "JSON nesting exceeds safe limits" in result.reason
        with pytest.raises(
            FreeCADAdapterError, match="JSON nesting exceeds safe limits"
        ):
            adapter.read(hostile)


@pytest.mark.parametrize(
    ("entry_name", "entry_data", "message"),
    (
        ("../Bad.bin", b"bad", "unsafe entry name"),
        ("Bomb.bin", b"\0" * (1024 * 1024), "compression ratio is unsafe"),
    ),
    ids=("unsafe_path", "compression_bomb"),
)
def test_kit_carrier_probe_and_read_apply_archive_limits(
    entry_name: str, entry_data: bytes, message: str
) -> None:
    adapter = FreeCADAdapter()
    document = adapter.read(_native_part_fixture())
    valid = io.BytesIO()
    adapter.write(document, valid, WriteOptions(values={"rebuild": True}))
    hostile = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(valid.getvalue())) as source:
        with zipfile.ZipFile(hostile, "w", zipfile.ZIP_DEFLATED) as output:
            output.writestr("Document.xml", source.read("Document.xml"))
            output.writestr(
                "interchange/document.json",
                source.read("interchange/document.json"),
            )
            output.writestr(entry_name, entry_data)
    assert adapter.probe(hostile.getvalue()).confidence == 0.0
    with pytest.raises(FreeCADAdapterError, match=message):
        adapter.read(hostile.getvalue())


def test_native_probe_rejects_encrypted_referenced_entry_without_raising() -> None:
    data = bytearray(_native_part_fixture())
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        shape = archive.getinfo("Pad.Shape.brp")
    flags = struct.unpack_from("<H", data, shape.header_offset + 6)[0] | 0x1
    struct.pack_into("<H", data, shape.header_offset + 6, flags)
    offset = 0
    while True:
        offset = data.find(b"PK\x01\x02", offset)
        if offset < 0:
            break
        name_length = struct.unpack_from("<H", data, offset + 28)[0]
        extra_length = struct.unpack_from("<H", data, offset + 30)[0]
        comment_length = struct.unpack_from("<H", data, offset + 32)[0]
        name = bytes(data[offset + 46 : offset + 46 + name_length]).decode("utf-8")
        if name == "Pad.Shape.brp":
            central_flags = struct.unpack_from("<H", data, offset + 8)[0] | 0x1
            struct.pack_into("<H", data, offset + 8, central_flags)
            break
        offset += 46 + name_length + extra_length + comment_length
    assert FreeCADAdapter().probe(bytes(data)).confidence == 0.0


def test_freecad_supports_only_writable_binary_destinations() -> None:
    document = FreeCADAdapter().read(_native_part_fixture())
    adapter = FreeCADAdapter()
    assert adapter.supports(document, io.BytesIO())
    assert not adapter.supports(document, io.StringIO())
    assert not adapter.supports(document, io.BufferedReader(io.BytesIO()))


def test_native_read_can_exclude_brep_payloads() -> None:
    document = FreeCADAdapter().read(
        _native_assembly_fixture(), ReadOptions(include_brep=False)
    )
    assert not any(
        payload.role == PayloadRole.BREP for payload in document.brep_payloads
    )
    assert document.assembly is not None
    assert all(
        not any(
            payload.role == PayloadRole.BREP for payload in item.document.brep_payloads
        )
        for item in document.assembly.documents
    )


def test_native_partdesign_without_brep_has_no_dangling_file_references() -> None:
    source = FREECAD_EXAMPLES / "PartDesignExample.FCStd"
    if not source.is_file():
        pytest.skip("bundled FreeCAD PartDesign example is unavailable")
    adapter = FreeCADAdapter()
    document = adapter.read(source, ReadOptions(include_brep=False))
    assert not any(
        payload.role == PayloadRole.BREP for payload in document.brep_payloads
    )
    output = io.BytesIO()
    adapter.write(document, output)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        names = set(archive.namelist())
        root = ET.fromstring(archive.read("Document.xml"))
    references = [
        node.get("file", "")
        for node in root.findall(".//*[@file]")
        if node.tag != "XLink" and node.get("file", "")
    ]
    assert references
    assert set(references) <= names
    native_shapes = [
        property_element
        for property_element in root.findall(".//Property")
        if property_element.get("type")
        in {"Part::PropertyPartShape", "Part::PropertyPartShapeHidden"}
    ]
    assert native_shapes
    parts = [property_element.find("./Part") for property_element in native_shapes]
    assert all(part is None or not part.get("file", "") for part in parts)


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


@pytest.mark.parametrize(
    "name",
    (
        "ArchDetail.FCStd",
        "AssemblyExample.FCStd",
        "BIMExample.FCStd",
        "draft_test_objects.FCStd",
        "EngineBlock.FCStd",
        "FEMExample.FCStd",
        "PartDesignExample.FCStd",
    ),
)
def test_native_freecad_example_corpus(name: str) -> None:
    source = FREECAD_EXAMPLES / name
    if not source.is_file():
        pytest.skip(f"bundled FreeCAD example {name} is unavailable")
    document = FreeCADAdapter().read(source)
    assert document.validate() == ()


def test_native_assembly_fcstd_restores_components_and_mates(tmp_path) -> None:
    source = FREECAD_EXAMPLES / "AssemblyExample.FCStd"
    if not source.is_file():
        pytest.skip("bundled FreeCAD assembly example is unavailable")
    document = FreeCADAdapter().read(source)
    assert document.validate() == ()
    assert document.assembly is not None
    assert len(document.assembly.definitions) == 14
    assert len(document.assembly.instances) == 13
    assert len(document.assembly.mates) == 16
    assert len(document.brep_payloads) == 15
    assert document.brep is None
    source_shapes = tuple(
        payload.data
        for payload in document.brep_payloads
        if payload.role == PayloadRole.BREP and payload.data is not None
    )
    assert len(source_shapes) == 13
    assert all(is_structurally_valid_ascii_brep(data) for data in source_shapes)
    base_pin = document.assembly.instances[0]
    assert base_pin.fixed
    assert base_pin.transform.values[3:12:4] == (
        -206.51702880859375,
        40.255699157714844,
        364.26800537109375,
    )
    revolute = next(mate for mate in document.assembly.mates if mate.name == "Revolute")
    entities = {entity.id: entity for entity in document.assembly.mate_entities}
    assert [
        entities[entity_id].source_entity_id for entity_id in revolute.entity_ids
    ] == [
        "Face1",
        "Edge2",
        "Edge107",
        "Edge107",
    ]
    assert str(revolute.kind) == "hinge"
    output = tmp_path / "Assembly.FCStd"
    result = convert(source, output)
    assert result.near_lossless
    transfers = {transfer.capability: transfer for transfer in result.transfers}
    assert transfers[Capability.BREP].mode is TransferMode.NATIVE
    assert transfers[Capability.NATIVE_PAYLOADS].mode is TransferMode.NATIVE
    component_files = sorted((tmp_path / "Assembly").glob("*.FCStd"))
    assert len(component_files) == 13
    emitted_shapes = []
    for component_file in component_files:
        with zipfile.ZipFile(component_file) as archive:
            root = ET.fromstring(archive.read("Document.xml"))
            assert any(
                item.get("type") == "Part::Feature"
                for item in root.findall("./Objects/Object")
            )
            shape_entries = [
                name for name in archive.namelist() if name.endswith(".Shape.brp")
            ]
            assert shape_entries
            assert all(archive.read(name) for name in shape_entries)
            emitted_shapes.extend(archive.read(name) for name in shape_entries)
    assert sorted(hashlib.sha256(data).digest() for data in emitted_shapes) == sorted(
        hashlib.sha256(data).digest() for data in source_shapes
    )
    assert FreeCADAdapter().read(output) == document

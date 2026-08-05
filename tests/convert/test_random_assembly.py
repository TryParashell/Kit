# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections import Counter
import itertools
import os
from pathlib import Path, PureWindowsPath
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import pytest

from convert import open_document, write_document
from interchange import (
    CadDocument,
    ComponentKind,
    Matrix4,
    PayloadRole,
    ValueKind,
)

RANDOM = Path(__file__).parents[2] / "examples" / "Random" / "V8_engine.SLDASM"
ORACLE = Path(os.environ.get("KIT_FREECAD_ORACLE", ""))


@pytest.fixture(scope="module")
def random_document() -> CadDocument:
    return open_document(RANDOM)


def _multiply(left: Matrix4, right: Matrix4) -> Matrix4:
    return Matrix4(
        tuple(
            sum(
                left.values[row * 4 + index] * right.values[index * 4 + column]
                for index in range(4)
            )
            for row in range(4)
            for column in range(4)
        )
    )


def _expanded_instances(
    document: CadDocument,
) -> tuple[tuple[object, Matrix4], ...]:
    assembly = document.assembly
    assert assembly is not None
    children: dict[str, list[object]] = {}
    for instance in assembly.instances:
        children.setdefault(instance.owner_definition_id, []).append(instance)
    result: list[tuple[object, Matrix4]] = []

    def visit(definition_id: str, parent: Matrix4) -> None:
        for instance in children.get(definition_id, []):
            world = _multiply(parent, instance.transform)
            result.append((instance, world))
            visit(instance.definition_id, world)

    visit(assembly.root_definition_id, Matrix4())
    return tuple(result)


def _document_counts(document: CadDocument) -> tuple[int, int]:
    sketches = len(document.sketches)
    timeline = len(document.feature_timeline)
    assembly = document.assembly
    if assembly is None:
        return sketches, timeline
    documents = {item.id: item.document for item in assembly.documents}
    for definition in assembly.definitions:
        child = documents.get(definition.document_id)
        if child is None:
            continue
        child_sketches, child_timeline = _document_counts(child)
        sketches += child_sketches
        timeline += child_timeline
    return sketches, timeline


def _placed_mesh_bounds(document: CadDocument) -> tuple[float, ...]:
    assembly = document.assembly
    assert assembly is not None
    definitions = {item.id: item for item in assembly.definitions}
    meshes = {item.id: item for item in document.meshes}
    corners_by_definition: dict[str, tuple[tuple[float, float, float], ...]] = {}
    for definition in assembly.definitions:
        points = [
            (vertex.x, vertex.y, vertex.z)
            for mesh_id in definition.mesh_ids
            for vertex in meshes[mesh_id].vertices
        ]
        if not points:
            continue
        minimum = tuple(min(point[index] for point in points) for index in range(3))
        maximum = tuple(max(point[index] for point in points) for index in range(3))
        corners_by_definition[definition.id] = tuple(
            itertools.product(
                (minimum[0], maximum[0]),
                (minimum[1], maximum[1]),
                (minimum[2], maximum[2]),
            )
        )
    placed = [
        world.transform_point(corner)
        for instance, world in _expanded_instances(document)
        if definitions[instance.definition_id].kind == ComponentKind.PART
        for corner in corners_by_definition[instance.definition_id]
    ]
    return tuple(
        [min(point[index] for point in placed) for index in range(3)]
        + [max(point[index] for point in placed) for index in range(3)]
    )


def test_random_assembly_public_sdk_recovers_complete_neutral_graph(
    random_document: CadDocument,
) -> None:
    document = random_document
    assembly = document.assembly
    assert assembly is not None
    assert document.source.format_id == "solidworks.sldasm"
    assert document.validate() == ()
    assert (len(document.sketches), len(document.feature_timeline)) == (3, 327)
    assert len(
        {
            feature.attributes["native_object_id"]
            for feature in document.feature_timeline
        }
    ) == len(document.feature_timeline)
    assert all(
        feature.attributes["native_type"] and feature.attributes["xml_tag"]
        for feature in document.feature_timeline
    )
    assert (len(document.parameters), len(document.brep_payloads)) == (3, 15)
    assert Counter(payload.role for payload in document.brep_payloads) == {
        PayloadRole.BREP: 12,
        PayloadRole.ASSEMBLY_STRUCTURE: 3,
    }
    assert (
        len(assembly.definitions),
        len(assembly.instances),
        len(assembly.documents),
        len(document.meshes),
    ) == (68, 288, 53, 65)
    assert Counter(definition.kind for definition in assembly.definitions) == {
        ComponentKind.PART: 65,
        ComponentKind.ASSEMBLY: 3,
    }
    expanded = _expanded_instances(document)
    definitions = {item.id: item for item in assembly.definitions}
    assert len(expanded) == 358
    assert (
        sum(
            definitions[instance.definition_id].kind == ComponentKind.PART
            for instance, _ in expanded
        )
        == 342
    )
    assert Counter(item.document.source.format_id for item in assembly.documents) == {
        "solidworks.sldprt": 51,
        "solidworks.sldasm": 2,
    }
    linked_counts = (
        sum(len(item.document.sketches) for item in assembly.documents),
        sum(len(item.document.feature_timeline) for item in assembly.documents),
        sum(len(item.document.parameters) for item in assembly.documents),
        sum(len(item.document.brep_payloads) for item in assembly.documents),
    )
    assert linked_counts == (391, 2147, 1695, 303)
    global_variables = {
        (Path(str(item.document.source.path)).name, parameter.name): parameter
        for item in assembly.documents
        for parameter in item.document.parameters
        if parameter.id.startswith("sldprt:parameter:equation:")
    }
    assert {key[1] for key in global_variables} == {"d", "r1", "r2"}
    assert {key[0] for key in global_variables} == {"Camshaft.SLDPRT"}
    assert {
        name: global_variables[("Camshaft.SLDPRT", name)].value.value
        for name in ("d", "r1", "r2")
    } == {"d": 8.0, "r1": 18.0, "r2": 10.0}
    assert all(
        parameter.value.kind is ValueKind.NUMBER
        for parameter in global_variables.values()
    )
    driven = [
        parameter
        for item in assembly.documents
        for parameter in item.document.parameters
        if parameter.expression is not None
        and any(
            reference in {item.id for item in global_variables.values()}
            for reference in parameter.expression.references
        )
    ]
    assert len(driven) == 22
    assert Counter(
        payload.role
        for item in assembly.documents
        for payload in item.document.brep_payloads
    ) == {
        PayloadRole.BREP: 301,
        PayloadRole.ASSEMBLY_STRUCTURE: 2,
    }
    assert linked_counts[:2] == (
        assembly.attributes["linked_sketch_count"],
        assembly.attributes["linked_feature_count"],
    )
    nested = {
        PureWindowsPath(item.document.source.path).name: item.document.assembly
        for item in assembly.documents
        if item.document.assembly is not None
    }
    assert set(nested) == {"Conrod.SLDASM", "Piston.SLDASM"}
    assert len(nested["Conrod.SLDASM"].mates) == 13
    assert len(nested["Piston.SLDASM"].mates) == 6
    assert _document_counts(document) == (394, 2474)


def test_random_assembly_preserves_meshes_mates_and_millimeter_transforms(
    random_document: CadDocument,
) -> None:
    assembly = random_document.assembly
    assert assembly is not None
    assert sum(len(mesh.vertices) for mesh in random_document.meshes) == 492148
    assert sum(len(mesh.triangles) for mesh in random_document.meshes) == 391218
    part_definitions = [
        item for item in assembly.definitions if item.kind == ComponentKind.PART
    ]
    assert len(part_definitions) == 65
    assert all(len(item.mesh_ids) == 1 for item in part_definitions)
    assert {mesh_id for item in part_definitions for mesh_id in item.mesh_ids} == {
        mesh.id for mesh in random_document.meshes
    }
    assert (
        len(assembly.mate_entities),
        len(assembly.mates),
        len(assembly.mate_groups),
    ) == (1261, 632, 3)
    assert Counter(mate.owner_definition_id for mate in assembly.mates) == {
        "sldasm:definition:2": 613,
        "sldasm:definition:218": 6,
        "sldasm:definition:231": 13,
    }
    assert [len(group.mate_ids) for group in assembly.mate_groups] == [6, 2, 9]
    for instance in assembly.instances:
        native = instance.attributes["native_transform"]
        expected = (
            native[0],
            native[4],
            native[8],
            native[12] * 1000.0,
            native[1],
            native[5],
            native[9],
            native[13] * 1000.0,
            native[2],
            native[6],
            native[10],
            native[14] * 1000.0,
            0.0,
            0.0,
            0.0,
            native[15],
        )
        assert instance.transform.values == pytest.approx(expected, abs=1e-12)
    assert max(
        abs(instance.transform.values[index])
        for instance in assembly.instances
        for index in (3, 7, 11)
    ) == pytest.approx(395.0340546095202)
    assert _placed_mesh_bounds(random_document) == pytest.approx(
        (
            -266.5,
            -220.00028984690346,
            -275.1418883526141,
            589.9999737739564,
            455.0340560996356,
            275.1418883526132,
        ),
        abs=1e-8,
    )


def test_random_assembly_writes_external_component_files(
    random_document: CadDocument, tmp_path: Path
) -> None:
    output = tmp_path / "V8_engine.FCStd"
    result = write_document(random_document, output, allow_carrier=True)
    assert result.application_usable is True
    assert result.vendor_loadable is True
    assert result.near_lossless is False
    component_directory = tmp_path / "V8_engine"
    components = tuple(component_directory.glob("*.FCStd"))
    assert len(components) == 67
    assert result.metadata["component_file_count"] == 67
    timeline_count = 0
    for document_path in (output, *components):
        with zipfile.ZipFile(document_path) as archive:
            document_root = ET.fromstring(archive.read("Document.xml"))
        for item in document_root.findall("./ObjectData/Object"):
            role = item.find("./Properties/Property[@name='KitRole']/String")
            if role is not None and role.get("value") != "profile-extrusion":
                timeline_count += 1
    assert timeline_count == 2474
    with zipfile.ZipFile(output) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    objects = {
        item.get("name", ""): item.get("type", "")
        for item in root.findall("./Objects/Object")
    }
    assembly_links = [
        item
        for item in root.findall("./ObjectData/Object")
        if objects.get(item.get("name", "")) == "Assembly::AssemblyLink"
    ]
    occurrences = [
        item
        for item in root.findall("./ObjectData/Object")
        if item.find("./Properties/Property[@name='InstanceId']") is not None
    ]
    linked_files = {
        item.find("./Properties/Property[@name='LinkedObject']/XLink").get("file")
        for item in assembly_links
    }
    data = {item.get("name", ""): item for item in root.findall("./ObjectData/Object")}
    assembly_root = next(
        item
        for item in data.values()
        if item.find("./Properties/Property[@name='RootDefinitionId']") is not None
    )
    direct_occurrences = [
        data[item.get("value")]
        for item in assembly_root.findall(
            "./Properties/Property[@name='Group']/LinkList/Link"
        )
        if data[item.get("value")].find("./Properties/Property[@name='InstanceId']")
        is not None
    ]
    assert len(assembly_links) == 16
    assert len(direct_occurrences) == 278
    assert len(occurrences) == 358
    assert len(linked_files) == 2
    assert all(filename.startswith("V8_engine/") for filename in linked_files)
    assert {Path(filename).stem.split("_", 1)[0] for filename in linked_files} == {
        "Conrod",
        "Piston",
    }
    proxy_count = 0
    component_roots: dict[str, ET.Element] = {}
    for assembly_link in assembly_links:
        parent_link = assembly_link.find(
            "./Properties/Property[@name='LinkedObject']/XLink"
        )
        children = [
            data[item.get("value")]
            for item in assembly_link.findall(
                "./Properties/Property[@name='Group']/LinkList/Link"
            )
        ]
        assert children
        proxy_count += len(children)
        component_root = component_roots.get(parent_link.get("file"))
        if component_root is None:
            with zipfile.ZipFile(tmp_path / Path(parent_link.get("file"))) as archive:
                component_root = ET.fromstring(archive.read("Document.xml"))
            component_roots[parent_link.get("file")] = component_root
        for child in children:
            linked = child.find("./Properties/Property[@name='LinkedObject']/XLink")
            assert linked.get("file") == parent_link.get("file")
            assert linked.get("stamp") == parent_link.get("stamp")
            source = component_root.find(
                f"./ObjectData/Object[@name='{linked.get('name')}']"
            )
            assert source is not None
            assert source.find("./Properties/Property[@name='InstanceId']") is not None
    assert proxy_count == 80
    for filename in linked_files:
        component = tmp_path / Path(filename)
        restored = open_document(component)
        assert restored.assembly is not None
        with zipfile.ZipFile(component) as archive:
            component_root = ET.fromstring(archive.read("Document.xml"))
        target = component_root.find(
            "./ObjectData/Object[@name='KitMetadata']/Properties/"
            "Property[@name='ExternalLinkTarget']/String"
        )
        assert target is not None
        target_object = component_root.find(
            f"./Objects/Object[@name='{target.get('value')}']"
        )
        assert target_object is not None
        assert target_object.get("type") == "Assembly::AssemblyObject"
        component_types = {
            item.get("name", ""): item.get("type", "")
            for item in component_root.findall("./Objects/Object")
        }
        component_links = [
            item
            for item in component_root.findall("./ObjectData/Object")
            if component_types.get(item.get("name", "")) == "App::Link"
            and item.find("./Properties/Property[@name='InstanceId']") is not None
        ]
        assert component_links
        for component_link in component_links:
            linked = component_link.find(
                "./Properties/Property[@name='LinkedObject']/XLink"
            )
            assert linked is not None
            assert linked.get("file")
            linked_component = component.parent / linked.get("file")
            with zipfile.ZipFile(linked_component) as archive:
                linked_root = ET.fromstring(archive.read("Document.xml"))
            linked_target = linked_root.find(
                f"./Objects/Object[@name='{linked.get('name')}']"
            )
            assert linked_target is not None
            assert linked_target.get("type") == "Part::Feature"


@pytest.mark.skipif(not ORACLE.is_file(), reason="KIT_FREECAD_ORACLE is unavailable")
def test_random_assembly_freecad_loads_recomputes_and_preserves_placed_extent(
    random_document: CadDocument, tmp_path: Path
) -> None:
    output = tmp_path / "V8_engine.FCStd"
    write_document(random_document, output)
    expected_bounds = _placed_mesh_bounds(random_document)
    code = f"""
import FreeCAD as App
d=App.open(r'{output}')
root=next(o for o in d.Objects if o.TypeId=='Assembly::AssemblyObject' and hasattr(o,'RootDefinitionId') and o.RootDefinitionId=='sldasm:definition:2')
d.recompute()
first_links=tuple(sorted(o.Name for o in d.Objects if o.TypeId in ('App::Link','Assembly::AssemblyLink')))
d.recompute()
links=[o for o in d.Objects if o.TypeId in ('App::Link','Assembly::AssemblyLink')]
stable_links=first_links==tuple(sorted(o.Name for o in links))
leaf=[o for o in links if o.TypeId=='App::Link' and hasattr(o,'Shape') and not o.Shape.isNull()]
sources={{(o.getLinkedObject(True).Document.Name,o.getLinkedObject(True).Name):o.getLinkedObject(True) for o in leaf}}
points=[]
for link in leaf:
    box=link.getLinkedObject(True).Shape.BoundBox
    placement=link.Placement
    parent=link.getParentGeoFeatureGroup()
    while parent is not None and parent != root:
        placement=parent.Placement*placement
        parent=parent.getParentGeoFeatureGroup()
    for x in (box.XMin,box.XMax):
        for y in (box.YMin,box.YMax):
            for z in (box.ZMin,box.ZMax):
                point=placement.multVec(App.Vector(x,y,z))
                points.append((point.x,point.y,point.z))
bounds=tuple([min(point[index] for point in points) for index in range(3)]+[max(point[index] for point in points) for index in range(3)])
documents=tuple(App.listDocuments().values())
breps=[o for document in documents for o in document.Objects if o.TypeId=='Part::Feature' and getattr(o,'Representation','')=='faceted']
sketches=[o for document in documents for o in document.Objects if o.TypeId=='Sketcher::SketchObject']
timeline=[o for document in documents for o in document.Objects if hasattr(o,'KitRole') and o.KitRole!='profile-extrusion']
mates=[o for o in d.Objects if hasattr(o,'MateId')]
all_mates=[o for document in documents for o in document.Objects if hasattr(o,'MateId')]
active_mates=[o for o in all_mates if not o.Suppressed]
valid_mates=all(o.Reference1[0] is not None and o.Reference2[0] is not None for o in active_mates)
mate_groups=[o for document in documents for o in document.Objects if hasattr(o,'MateGroupId')]
assemblies=[o for document in documents for o in document.Objects if o.TypeId=='Assembly::AssemblyObject']
print('KIT_RANDOM',len(documents),len(links),len(leaf),len(sources),len(breps),sum(len(o.Shape.Faces) for o in breps),sum(o.Shape.isValid() for o in breps),len(sketches),len(timeline),len(mates),len(all_mates),len(mate_groups),len(assemblies),stable_links,valid_mates,*bounds,flush=True)
"""
    completed = subprocess.run(
        [str(ORACLE), "-c", code],
        capture_output=True,
        text=True,
        timeout=300,
    )
    output_text = completed.stdout + completed.stderr
    assert completed.returncode == 0, output_text[-8000:]
    for message in (
        "The graph must be a DAG",
        "links are out of scope",
        "pending remove",
        "Time stamp changed on link",
    ):
        assert message not in output_text
    lines = [
        value
        for value in completed.stdout.splitlines()
        if value.startswith("KIT_RANDOM")
    ]
    assert lines, completed.stdout[-4000:] + completed.stderr[-4000:]
    line = lines[-1]
    values = line.split()[1:]
    assert tuple(int(value) for value in values[:13]) == (
        68,
        358,
        342,
        65,
        65,
        391218,
        65,
        394,
        2474,
        613,
        632,
        3,
        3,
    )
    assert values[13:15] == ["True", "True"]
    assert tuple(float(value) for value in values[15:]) == pytest.approx(
        expected_bounds, abs=1e-4
    )
    assert "Errors in neighbourhood of mesh found" not in output_text

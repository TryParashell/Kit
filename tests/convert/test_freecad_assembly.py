from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import struct
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import pytest

from convert.adapters.freecad import read_freecad, write_freecad
from interchange import CadSource, ComponentDocument, Matrix4, Mesh, Vector3
from tests.interchange.test_assembly import assembly_document
from tests.interchange.test_document import document


ORACLE = Path(os.environ.get("KIT_FREECAD_ORACLE", ""))


def _property(node: ET.Element, name: str) -> ET.Element:
    result = node.find(f"./Properties/Property[@name='{name}']")
    assert result is not None
    return result


def _mesh_document():
    source = assembly_document()
    assembly = source.assembly
    assert assembly is not None
    mesh = Mesh(
        "mesh:part",
        "Part geometry",
        (
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
            Vector3(1.0, 1.0, 0.0),
        ),
        ((0, 1, 2), (2, 1, 3)),
    )
    definitions = list(assembly.definitions)
    definitions[2] = replace(
        definitions[2],
        document_id="",
        body_ids=(),
        mesh_ids=(mesh.id,),
    )
    part_instance = replace(
        assembly.instances[1],
        owner_definition_id=assembly.root_definition_id,
        transform=assembly.instances[0].transform,
    )
    entities = tuple(
        replace(entity, instance_path=(part_instance.id,)) if index else entity
        for index, entity in enumerate(assembly.mate_entities)
    )
    return replace(
        source,
        meshes=(mesh,),
        assembly=replace(
            assembly,
            definitions=tuple(definitions),
            instances=(part_instance,),
            documents=(),
            mate_entities=entities,
        ),
    )


def _nested_assembly_document():
    source = assembly_document()
    assembly = source.assembly
    assert assembly is not None
    part_mesh = Mesh(
        "mesh:nested-part",
        "Nested part geometry",
        (
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
        ),
        ((0, 1, 2),),
    )
    part_document = replace(assembly.documents[0].document, meshes=(part_mesh,))
    part_link = replace(assembly.documents[0], document=part_document)
    nested_assembly = replace(
        assembly,
        root_definition_id="definition:subassembly",
        definitions=tuple(
            item
            for item in assembly.definitions
            if item.id in {"definition:subassembly", "definition:part"}
        ),
        instances=(assembly.instances[1],),
        documents=(part_link,),
        mate_entities=(),
        mates=(),
        mate_groups=(),
    )
    nested = replace(
        document(),
        source=CadSource("test.assembly", "nested", "2" * 64),
        assembly=nested_assembly,
    )
    definitions = tuple(
        (
            replace(item, document_id="document:subassembly")
            if item.id == "definition:subassembly"
            else item
        )
        for item in assembly.definitions
    )
    return replace(
        source,
        assembly=replace(
            assembly,
            definitions=definitions,
            documents=(
                part_link,
                ComponentDocument("document:subassembly", nested),
            ),
        ),
    )


def test_fcstd_assembly_has_component_links_placements_and_mates(tmp_path) -> None:
    output = tmp_path / "assembly.FCStd"
    write_freecad(assembly_document(), output)
    with zipfile.ZipFile(output) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    objects = root.findall("./Objects/Object")
    types = [item.get("type") for item in objects]
    assert types.count("Assembly::AssemblyObject") == 1
    assert types.count("Assembly::JointGroup") == 1
    assert types.count("App::Origin") == 1
    links = [item for item in objects if item.get("type") == "App::Link"]
    assert len(links) == 1
    data = {item.get("name", ""): item for item in root.findall("./ObjectData/Object")}
    link_data = [data[item.get("name", "")] for item in links]
    assert all(
        _property(item, "LinkTransform").find("Bool").get("value") == "true"
        for item in link_data
    )
    placement = _property(link_data[0], "Placement").find("PropertyPlacement")
    assert placement is not None
    assert (
        float(placement.get("Px", "0")),
        float(placement.get("Py", "0")),
        float(placement.get("Pz", "0")),
    ) == pytest.approx((100.0, 20.0, 30.0))
    mate = next(
        item
        for item in data.values()
        if item.find("./Properties/Property[@name='MateId']") is not None
    )
    joint_type = _property(mate, "JointType").find("Integer")
    entity_ids = _property(mate, "EntityIds").findall("./StringList/String")
    component_links = _property(mate, "ComponentLinks").findall("./StringList/String")
    assert joint_type is not None and joint_type.get("value") == "0"
    proxy = _property(mate, "Proxy").find("Python")
    assert proxy is not None
    assert proxy.attrib == {
        "value": "bnVsbA==",
        "encoded": "yes",
        "module": "JointObject",
        "class": "Joint",
    }
    assert [item.get("value") for item in entity_ids] == [
        "mate-entity:assembly",
        "mate-entity:part",
    ]
    assembly_root = next(
        item
        for item in data.values()
        if item.find("./Properties/Property[@name='RootDefinitionId']") is not None
    )
    root_origin = _property(assembly_root, "Origin").find("Link").get("value")
    assert len(component_links) == 2
    assert component_links[0].get("value") == root_origin
    reference1 = _property(mate, "Reference1").find("XLink")
    reference2 = _property(mate, "Reference2").find("XLink")
    assert reference1 is not None
    assert reference2 is not None
    assert reference1.get("name") == root_origin
    assert reference2.get("name") == links[0].get("name")
    assert [item.get("value") for item in reference1.findall("Sub")] == ["", ""]
    assert _property(mate, "Suppressed").find("Bool").get("value") == "false"
    assert _property(mate, "Detach1").find("Bool").get("value") == "false"
    assert _property(mate, "Detach2").find("Bool").get("value") == "false"
    assert (
        _property(assembly_root, "OccurrenceCount").find("Integer").get("value") == "1"
    )
    root_children = {
        item.get("value")
        for item in _property(assembly_root, "Group").findall("./LinkList/Link")
    }
    metadata_groups = {
        name
        for name in data
        if name.endswith(("_Definitions", "_Components", "_MateEntities"))
    }
    assert metadata_groups.isdisjoint(root_children)


def test_fcstd_mate_connectors_preserve_reference_and_detached_frame_state(
    tmp_path,
) -> None:
    source = assembly_document()
    assembly = source.assembly
    assert assembly is not None
    frame = Matrix4(
        (
            1.0,
            0.0,
            0.0,
            1.0,
            0.0,
            1.0,
            0.0,
            2.0,
            0.0,
            0.0,
            1.0,
            3.0,
            0.0,
            0.0,
            0.0,
            1.0,
        )
    )
    target_path = assembly.mate_entities[1].instance_path
    entities = (
        replace(
            assembly.mate_entities[0],
            instance_path=target_path,
            source_entity_id="Face1",
            frame=frame,
        ),
        replace(assembly.mate_entities[1], source_entity_id="", frame=frame),
    )
    source = replace(source, assembly=replace(assembly, mate_entities=entities))
    output = tmp_path / "connector_state.FCStd"
    write_freecad(source, output)
    with zipfile.ZipFile(output) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    mate = next(
        item
        for item in root.findall("./ObjectData/Object")
        if item.find("./Properties/Property[@name='MateId']") is not None
    )
    reference1 = _property(mate, "Reference1").find("XLink")
    reference2 = _property(mate, "Reference2").find("XLink")
    assert reference1 is not None
    assert reference2 is not None
    assert reference1.get("name") == reference2.get("name")
    assert [item.get("value") for item in reference1.findall("Sub")] == [
        "Face1",
        "Face1",
    ]
    assert [item.get("value") for item in reference2.findall("Sub")] == ["", ""]
    assert _property(mate, "Detach1").find("Bool").get("value") == "false"
    assert _property(mate, "Detach2").find("Bool").get("value") == "true"
    assert _property(mate, "Suppressed").find("Bool").get("value") == "false"
    component_links = _property(mate, "ComponentLinks").findall("./StringList/String")
    assert len(component_links) == 1


def test_fcstd_assembly_emits_reusable_mesh_definition(tmp_path) -> None:
    source = _mesh_document()
    output = tmp_path / "mesh_assembly.FCStd"
    write_freecad(source, output)
    component = tmp_path / "mesh_assembly" / "Piston.FCStd"
    with zipfile.ZipFile(component) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
        mesh = next(
            item
            for item in root.findall("./Objects/Object")
            if item.get("type") == "Mesh::Feature"
        )
        data = next(
            item
            for item in root.findall("./ObjectData/Object")
            if item.get("name") == mesh.get("name")
        )
        brep = _property(data, "BRep").find("Link").get("value")
        target = root.find(
            "./ObjectData/Object[@name='KitMetadata']/Properties/"
            "Property[@name='ExternalLinkTarget']/String"
        ).get("value")
        target_data = root.find(f"./ObjectData/Object[@name='{target}']")
        target_dependencies = next(
            item
            for item in root.findall("./Objects/ObjectDeps")
            if item.get("Name") == target
        )
        filename = _property(data, "Mesh").find("Mesh").get("file")
        payload = archive.read(filename)
    assert target == brep
    target_groups = {
        _property(target_data, name).find("Link").get("value")
        for name in ("Sketches", "FeatureTimeline")
    }
    assert target_groups.issubset(
        {item.get("Name") for item in target_dependencies.findall("Dep")}
    )
    assert _property(data, "Visibility").find("Bool").get("value") == "true"
    magic, version = struct.unpack_from("<II", payload)
    vertex_count, triangle_count = struct.unpack_from("<II", payload, 264)
    first_triangle = struct.unpack_from("<iiiiii", payload, 320)
    second_triangle = struct.unpack_from("<iiiiii", payload, 344)
    assert (magic, version) == (0xA0B0C0D0, 0x00010000)
    assert (vertex_count, triangle_count) == (4, 2)
    assert first_triangle == (0, 1, 2, -1, 1, -1)
    assert second_triangle == (2, 1, 3, 0, -1, -1)


def test_fcstd_keeps_nested_definition_mates_out_of_parent_assembly(tmp_path) -> None:
    source = assembly_document()
    assembly = source.assembly
    assert assembly is not None
    first_subassembly = assembly.instances[0]
    second_subassembly = replace(
        first_subassembly,
        id="instance:subassembly:2",
        name="Piston-2",
        order=1,
    )
    entities = tuple(
        replace(
            entity,
            owner_definition_id="definition:subassembly",
            instance_path=("instance:part",) if index else (),
        )
        for index, entity in enumerate(assembly.mate_entities)
    )
    mate = replace(assembly.mates[0], owner_definition_id="definition:subassembly")
    source = replace(
        source,
        assembly=replace(
            assembly,
            instances=(
                first_subassembly,
                second_subassembly,
                assembly.instances[1],
            ),
            mate_entities=entities,
            mates=(mate,),
        ),
    )
    output = tmp_path / "repeated.FCStd"
    write_freecad(source, output)
    with zipfile.ZipFile(output) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    data = root.findall("./ObjectData/Object")
    mates = [
        item
        for item in data
        if item.find("./Properties/Property[@name='MateId']") is not None
    ]
    assert mates == []
    assembly_root = next(
        item
        for item in data
        if item.find("./Properties/Property[@name='RootDefinitionId']") is not None
    )
    assert _property(assembly_root, "MateCount").find("Integer").get("value") == "0"
    restored = read_freecad(output)
    assert restored.assembly is not None
    assert restored.assembly.mates == (mate,)
    assert restored.assembly.mate_entities == entities


def test_fcstd_preserves_nested_assembly_history_in_component_file(tmp_path) -> None:
    output = tmp_path / "nested_history.FCStd"
    write_freecad(_nested_assembly_document(), output)
    component = tmp_path / "nested_history" / "Piston.FCStd"
    with zipfile.ZipFile(component) as archive:
        component_root = ET.fromstring(archive.read("Document.xml"))
    component_objects = component_root.findall("./Objects/Object")
    component_types = {
        item.get("name", ""): item.get("type", "") for item in component_objects
    }
    component_data = {
        item.get("name", ""): item
        for item in component_root.findall("./ObjectData/Object")
    }
    assert (
        sum(
            item.get("type") == "Assembly::AssemblyObject" for item in component_objects
        )
        == 1
    )
    assert any(item.get("type") == "Part::Extrusion" for item in component_objects)
    component_target = component_root.find(
        "./ObjectData/Object[@name='KitMetadata']/Properties/"
        "Property[@name='ExternalLinkTarget']/String"
    ).get("value")
    source_assembly = component_data[component_target]
    source_children = [
        item.get("value")
        for item in _property(source_assembly, "Group").findall("./LinkList/Link")
        if component_data[item.get("value")].find(
            "./Properties/Property[@name='InstanceId']"
        )
        is not None
    ]
    assert len(source_children) == 1
    assert component_types[source_children[0]] == "App::Link"
    source_sketches = _property(source_assembly, "Sketches").find("Link").get("value")
    source_timeline = (
        _property(source_assembly, "FeatureTimeline").find("Link").get("value")
    )
    source_dependencies = next(
        item
        for item in component_root.findall("./Objects/ObjectDeps")
        if item.get("Name") == component_target
    )
    assert {source_sketches, source_timeline}.issubset(
        {item.get("Name") for item in source_dependencies.findall("Dep")}
    )
    with zipfile.ZipFile(output) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    objects = root.findall("./Objects/Object")
    types = {item.get("name", ""): item.get("type", "") for item in objects}
    data = {item.get("name", ""): item for item in root.findall("./ObjectData/Object")}
    assembly_link_name = next(
        name for name, type_id in types.items() if type_id == "Assembly::AssemblyLink"
    )
    assembly_link = data[assembly_link_name]
    extensions = assembly_link.find("Extensions")
    assert extensions is not None
    assert [item.get("type") for item in extensions.findall("Extension")] == [
        "App::OriginGroupExtension"
    ]
    origin = _property(assembly_link, "Origin").find("Link").get("value")
    children = [
        item.get("value")
        for item in _property(assembly_link, "Group").findall("./LinkList/Link")
    ]
    assert types[origin] == "App::Origin"
    assert len(children) == 1
    proxy = data[children[0]]
    assert types[children[0]] == component_types[source_children[0]]
    parent_xlink = _property(assembly_link, "LinkedObject").find("XLink")
    proxy_xlink = _property(proxy, "LinkedObject").find("XLink")
    assert proxy_xlink.get("file") == parent_xlink.get("file")
    assert proxy_xlink.get("stamp") == parent_xlink.get("stamp")
    assert proxy_xlink.get("name") == source_children[0]
    assert [
        item.get("value")
        for item in _property(proxy, "InstancePath").findall("./StringList/String")
    ] == ["instance:subassembly", "instance:part"]
    assembly_link_node = next(
        item for item in objects if item.get("name") == assembly_link_name
    )
    assert assembly_link_node.get("Touched") == "1"
    dependency = next(
        item
        for item in root.findall("./Objects/ObjectDeps")
        if item.get("Name") == assembly_link_name
    )
    assert {item.get("Name") for item in dependency.findall("Dep")} == {
        origin,
        children[0],
    }
    assembly_placement = _property(assembly_link, "Placement").find("PropertyPlacement")
    assert assembly_placement is not None
    assert (
        float(assembly_placement.get("Px", "0")),
        float(assembly_placement.get("Py", "0")),
        float(assembly_placement.get("Pz", "0")),
    ) == pytest.approx((100.0, 20.0, 30.0))
    assert _property(assembly_link, "Visibility").find("Bool").get("value") == "true"
    proxy_placement = _property(proxy, "Placement").find("PropertyPlacement")
    assert (
        float(proxy_placement.get("Px", "0")),
        float(proxy_placement.get("Py", "0")),
        float(proxy_placement.get("Pz", "0")),
    ) == pytest.approx((0.0, 0.0, 0.0))
    mate = next(
        item
        for item in data.values()
        if item.find("./Properties/Property[@name='MateId']") is not None
    )
    reference = _property(mate, "Reference2").find("XLink")
    assert reference.get("name") == assembly_link_name
    assert [item.get("value") for item in reference.findall("Sub")] == [
        f"{children[0]}.",
        f"{children[0]}.",
    ]
    assembly_root = next(
        item
        for item in data.values()
        if item.find("./Properties/Property[@name='RootDefinitionId']") is not None
    )
    root_children = {
        item.get("value")
        for item in _property(assembly_root, "Group").findall("./LinkList/Link")
    }
    assert assembly_link_name in root_children
    metadata_groups = {
        name
        for name in data
        if name.endswith(("_Definitions", "_Components", "_MateEntities"))
    }
    assert metadata_groups.isdisjoint(root_children)


@pytest.mark.skipif(not ORACLE.is_file(), reason="KIT_FREECAD_ORACLE is unavailable")
def test_freecad_loads_assembly_tree_without_runtime_conversion(tmp_path) -> None:
    output = tmp_path / "assembly.FCStd"
    write_freecad(_mesh_document(), output)
    code = (
        "import FreeCAD as App;"
        f"d=App.open(r'{output}');"
        "d.recompute();d.recompute();"
        "links=[o for o in d.Objects if o.TypeId=='App::Link'];"
        "mates=[o for o in d.Objects if hasattr(o,'MateId')];"
        "shapelinks=[o for o in links if o.LinkedObject is not None "
        "and hasattr(o.LinkedObject,'Shape') and not o.LinkedObject.Shape.isNull()];"
        "documents=tuple(App.listDocuments().values());"
        "sources=[o for document in documents for o in document.Objects "
        "if o.TypeId=='Mesh::Feature'];"
        "target=shapelinks[0].LinkedObject;"
        "print('KIT_ASSEMBLY',len(links),len(mates),"
        "links[0].Placement.Base.x,links[0].Placement.Base.y,"
        "links[0].Placement.Base.z,links[0].LinkedObject is not None,"
        "len(shapelinks),len(target.Shape.Faces),"
        "target.Shape.BoundBox.XLength,target.TypeId,"
        "getattr(target,'Representation',''),"
        "len(sources),all(o.Visibility for o in sources),"
        "not any('Touched' in o.State for o in d.Objects))"
    )
    completed = subprocess.run(
        [str(ORACLE), "-c", code],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output_text = completed.stdout + completed.stderr
    for message in (
        "The graph must be a DAG",
        "links are out of scope",
        "pending remove",
        "Time stamp changed on link",
    ):
        assert message not in output_text
    line = next(
        value
        for value in completed.stdout.splitlines()
        if value.startswith("KIT_ASSEMBLY")
    )
    values = line.split()[1:]
    assert values[:2] == ["1", "1"]
    assert tuple(float(value) for value in values[2:5]) == pytest.approx(
        (100.0, 20.0, 30.0)
    )
    assert values[5:8] == ["True", "1", "2"]
    assert float(values[8]) == pytest.approx(1.0)
    assert values[9:] == [
        "Part::Feature",
        "faceted",
        "0",
        "True",
        "True",
    ]


@pytest.mark.skipif(not ORACLE.is_file(), reason="KIT_FREECAD_ORACLE is unavailable")
def test_freecad_loads_native_nested_assembly_link_group(tmp_path) -> None:
    output = tmp_path / "nested.FCStd"
    write_freecad(_nested_assembly_document(), output)
    code = (
        "import FreeCAD as App;"
        f"d=App.open(r'{output}');"
        "links=[o for o in d.Objects if o.TypeId=='Assembly::AssemblyLink'];"
        "a=links[0];"
        "before=tuple(o.Name for o in a.Group);"
        "d.recompute();"
        "first=tuple(o.Name for o in a.Group);"
        "d.recompute();"
        "second=tuple(o.Name for o in a.Group);"
        "children=[o for o in a.Group if o.TypeId=='App::Link'];"
        "c=children[0];"
        "print('KIT_NESTED',len(links),a.Origin is not None,len(children),"
        "before==first==second,c.getParentGeoFeatureGroup()==a,"
        "c.LinkedObject in a.LinkedObject.Group,"
        "c.LinkedObject.Document==a.LinkedObject.Document,a.Placement.Base.x,"
        "a.Placement.Base.y,a.Placement.Base.z,c.Placement.Base.x,"
        "c.Placement.Base.y,c.Placement.Base.z,c.LinkedObject is not None,"
        "a.LinkedObject is not None,a.Visibility,c.Visibility)"
    )
    completed = subprocess.run(
        [str(ORACLE), "-c", code],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output_text = completed.stdout + completed.stderr
    for message in (
        "The graph must be a DAG",
        "links are out of scope",
        "pending remove",
        "Time stamp changed on link",
    ):
        assert message not in output_text
    line = next(
        value
        for value in completed.stdout.splitlines()
        if value.startswith("KIT_NESTED")
    )
    assert line.split()[1:] == [
        "1",
        "True",
        "1",
        "True",
        "True",
        "True",
        "True",
        "100.0",
        "20.0",
        "30.0",
        "0.0",
        "0.0",
        "0.0",
        "True",
        "True",
        "True",
        "True",
    ]

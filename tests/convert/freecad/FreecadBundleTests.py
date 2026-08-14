# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import io
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import convert.adapters.freecad.Adapter as freecad_adapter
from convert.adapters.freecad import read_freecad, write_freecad
from interchange import Capability, ComponentDocument, Mesh, Vector3
from tests.interchange.assembly.AssemblyTests import assembly_document


def _xml(path: Path) -> ET.Element:
    with zipfile.ZipFile(path) as archive:
        return ET.fromstring(archive.read("Document.xml"))


def _linked_object(root: ET.Element) -> ET.Element:
    result = next(
        value
        for value in root.findall(
            "./ObjectData/Object/Properties/Property[@name='LinkedObject']/XLink"
        )
        if value.get("file")
    )
    return result


def _document_timestamp(root: ET.Element, property_name: str) -> str:
    result = root.find(f"./Properties/Property[@name='{property_name}']/String")
    assert result is not None
    return result.get("value", "")


def _representation(root: ET.Element, target: str) -> str:
    result = root.find(
        f"./ObjectData/Object[@name='{target}']/Properties/"
        "Property[@name='Representation']/String"
    )
    assert result is not None
    return result.get("value", "")


def _mesh_source(linked: bool):
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
        ),
        ((0, 1, 2),),
    )
    definitions = tuple(
        (
            replace(
                definition,
                document_id=definition.document_id if linked else "",
                body_ids=definition.body_ids if linked else (),
                mesh_ids=(mesh.id,),
                source_path="C:\\Toolbox\\Piston.SLDPRT",
                source_format_id="solidworks.sldprt",
            )
            if definition.id == "definition:part"
            else definition
        )
        for definition in assembly.definitions
    )
    instances = (
        assembly.instances[0],
        replace(
            assembly.instances[1],
            owner_definition_id=assembly.root_definition_id,
        ),
    )
    mate_entities = (
        assembly.mate_entities[0],
        replace(
            assembly.mate_entities[1],
            instance_path=(assembly.instances[1].id,),
        ),
    )
    return (
        replace(
            source,
            meshes=(mesh,),
            assembly=replace(
                assembly,
                definitions=definitions,
                instances=instances,
                documents=assembly.documents if linked else (),
                mate_entities=mate_entities,
            ),
        ),
        mesh,
    )


def test_path_assembly_writes_relative_component_with_document_and_mesh(
    tmp_path: Path,
) -> None:
    source, mesh = _mesh_source(linked=True)
    output = tmp_path / "assembly.FCStd"
    result = write_freecad(source, output)
    component = tmp_path / "assembly" / "Piston.FCStd"
    assert component.is_file()
    root = _xml(output)
    link = _linked_object(root)
    assert link.get("file") == "assembly/Piston.FCStd"
    stamp = datetime.fromtimestamp(component.stat().st_mtime, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    assert link.get("stamp") == stamp
    component_root = _xml(component)
    for property_name in ("CreationDate", "LastModifiedDate"):
        assert _document_timestamp(component_root, property_name) == stamp
    assert _document_timestamp(root, "LastModifiedDate") == stamp
    target = component_root.find(
        "./ObjectData/Object[@name='KitMetadata']/Properties/"
        "Property[@name='ExternalLinkTarget']/String"
    )
    assert target is not None
    assert link.get("name") == target.get("value")
    target_object = component_root.find(
        f"./Objects/Object[@name='{target.get('value')}']"
    )
    assert target_object is not None
    assert target_object.get("type") == "Part::Feature"
    assert _representation(component_root, target.get("value", "")) == "faceted"
    assembly = source.assembly
    assert assembly is not None
    linked = assembly.documents[0].document
    restored = read_freecad(component)
    assert restored == replace(
        linked,
        meshes=(mesh,),
        capabilities=linked.capabilities | {Capability.TESSELLATION},
    )
    assert result.metadata["component_file_count"] == 1
    assert result.metadata["component_bytes_written"] == component.stat().st_size


def test_path_assembly_overwrite_advances_one_bundle_timestamp(
    tmp_path: Path, monkeypatch
) -> None:
    fixed = datetime(2026, 8, 1, 18, 0, 0, tzinfo=timezone.utc)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed if tz is not None else fixed.replace(tzinfo=None)

    monkeypatch.setattr(freecad_adapter, "datetime", FixedDateTime)
    source, _ = _mesh_source(linked=True)
    output = tmp_path / "assembly.FCStd"
    component = tmp_path / "assembly" / "Piston.FCStd"
    write_freecad(source, output)
    first_root = _xml(output)
    first_component = _xml(component)
    first_stamp = "2026-08-01T18:00:00Z"
    assert _linked_object(first_root).get("stamp") == first_stamp
    for root in (first_root, first_component):
        assert _document_timestamp(root, "CreationDate") == first_stamp
        assert _document_timestamp(root, "LastModifiedDate") == first_stamp
    write_freecad(source, output, overwrite=True)
    second_root = _xml(output)
    second_component = _xml(component)
    second_stamp = "2026-08-01T18:00:01Z"
    assert _linked_object(second_root).get("stamp") == second_stamp
    for root in (second_root, second_component):
        assert _document_timestamp(root, "CreationDate") == second_stamp
        assert _document_timestamp(root, "LastModifiedDate") == second_stamp
    second_epoch = fixed.timestamp() + 1.0
    assert output.stat().st_mtime == second_epoch
    assert component.stat().st_mtime == second_epoch


def test_nested_assembly_links_to_sibling_part_component(tmp_path: Path) -> None:
    source, _ = _mesh_source(linked=True)
    assembly = source.assembly
    assert assembly is not None
    nested, _ = _mesh_source(linked=True)
    nested_assembly = nested.assembly
    assert nested_assembly is not None
    nested = replace(
        nested,
        meshes=(),
        assembly=replace(
            nested_assembly,
            definitions=tuple(
                (
                    replace(definition, mesh_ids=())
                    if definition.id == "definition:part"
                    else definition
                )
                for definition in nested_assembly.definitions
            ),
        ),
    )
    definitions = tuple(
        (
            replace(definition, document_id="document:subassembly")
            if definition.id == "definition:subassembly"
            else definition
        )
        for definition in assembly.definitions
    )
    source = replace(
        source,
        assembly=replace(
            assembly,
            definitions=definitions,
            documents=(
                *assembly.documents,
                ComponentDocument("document:subassembly", nested),
            ),
        ),
    )
    output = tmp_path / "nested.FCStd"
    write_freecad(source, output)
    assembly_component = tmp_path / "nested" / "Piston.FCStd"
    part_component = tmp_path / "nested" / "Piston_2.FCStd"
    assembly_root = _xml(assembly_component)
    part_root = _xml(part_component)
    link = _linked_object(assembly_root)
    assert link.get("file") == "Piston_2.FCStd"
    target = link.get("name", "")
    target_object = part_root.find(f"./Objects/Object[@name='{target}']")
    assert target_object is not None
    assert target_object.get("type") == "Part::Feature"
    assert _representation(part_root, target) == "faceted"
    assembly_target = assembly_root.find(
        "./ObjectData/Object[@name='KitMetadata']/Properties/"
        "Property[@name='ExternalLinkTarget']/String"
    )
    assert assembly_target is not None
    assembly_object = assembly_root.find(
        f"./Objects/Object[@name='{assembly_target.get('value')}']"
    )
    assert assembly_object is not None
    assert assembly_object.get("type") == "Assembly::AssemblyObject"


def test_path_assembly_writes_mesh_only_missing_component(tmp_path: Path) -> None:
    source, mesh = _mesh_source(linked=False)
    output = tmp_path / "toolbox.FCStd"
    write_freecad(source, output)
    component = tmp_path / "toolbox" / "Piston.FCStd"
    root = _xml(output)
    link = _linked_object(root)
    assert link.get("file") == "toolbox/Piston.FCStd"
    restored = read_freecad(component)
    assert restored.meshes == (mesh,)
    assert restored.feature_timeline == ()
    assert restored.assembly is None
    assert restored.source.path == "C:\\Toolbox\\Piston.SLDPRT"


def test_binary_assembly_remains_embedded() -> None:
    stream = io.BytesIO()
    result = write_freecad(assembly_document(), stream)
    stream.seek(0)
    with zipfile.ZipFile(stream) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    links = root.findall(
        "./ObjectData/Object/Properties/Property[@name='LinkedObject']/XLink"
    )
    assert links
    assert all(not link.get("file") for link in links)
    assert result.path is None
    assert result.metadata["component_file_count"] == 0
    assert result.metadata["component_bytes_written"] == 0

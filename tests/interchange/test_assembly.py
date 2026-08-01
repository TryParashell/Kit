from __future__ import annotations

from dataclasses import replace

import pytest

from interchange import (
    AssemblyData,
    CadDocument,
    CadDocumentValidationError,
    CadSource,
    Capability,
    ComponentDefinition,
    ComponentDocument,
    ComponentInstance,
    ComponentKind,
    Configuration,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateKind,
    Matrix4,
    Mesh,
    Vector3,
)

from tests.interchange.test_document import document


def assembly_document() -> CadDocument:
    part = document()
    root = ComponentDefinition("definition:root", "Engine", ComponentKind.ASSEMBLY)
    subassembly = ComponentDefinition(
        "definition:subassembly", "Piston", ComponentKind.ASSEMBLY
    )
    part_definition = ComponentDefinition(
        "definition:part",
        "Piston",
        ComponentKind.PART,
        document_id="document:part",
        body_ids=("body:1",),
    )
    subassembly_instance = ComponentInstance(
        "instance:subassembly",
        "Piston-1",
        subassembly.id,
        root.id,
        Matrix4(
            (
                1.0,
                0.0,
                0.0,
                100.0,
                0.0,
                1.0,
                0.0,
                20.0,
                0.0,
                0.0,
                1.0,
                30.0,
                0.0,
                0.0,
                0.0,
                1.0,
            )
        ),
    )
    part_instance = ComponentInstance(
        "instance:part", "Piston-1", part_definition.id, subassembly.id
    )
    first_entity = MateEntity(
        "mate-entity:assembly",
        root.id,
        (),
        MateEntityKind.PLANE,
        source_entity_id="plane:front",
    )
    second_entity = MateEntity(
        "mate-entity:part",
        root.id,
        (subassembly_instance.id, part_instance.id),
        MateEntityKind.PLANE,
        source_entity_id="plane:xy",
    )
    mate = MateConstraint(
        "mate:1",
        "Coincident1",
        MateKind.COINCIDENT,
        root.id,
        (first_entity.id, second_entity.id),
    )
    assembly = AssemblyData(
        root.id,
        (root, subassembly, part_definition),
        (subassembly_instance, part_instance),
        documents=(ComponentDocument("document:part", part),),
        mate_entities=(first_entity, second_entity),
        mates=(mate,),
    )
    return CadDocument(
        source=CadSource("test.assembly", "memory", "1" * 64),
        configurations=(Configuration("config:default", "Default", True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        capabilities=frozenset({Capability.ASSEMBLIES}),
        assembly=assembly,
    )


def test_assembly_json_roundtrip_preserves_embedded_documents() -> None:
    source = assembly_document()
    source.assert_valid()
    restored = CadDocument.from_json(source.to_json())
    assert restored == source
    assert restored.assembly is not None
    embedded = restored.assembly.document("document:part")
    assert isinstance(embedded, CadDocument)
    assert embedded == document()
    assert restored.assembly.children("definition:root") == (
        restored.assembly.instances[0],
    )


def test_matrix4_uses_canonical_homogeneous_layout() -> None:
    transform = assembly_document().assembly.instances[0].transform
    assert transform.transform_point((1.0, 2.0, 3.0)) == (101.0, 22.0, 33.0)
    assert transform.rows()[0] == (1.0, 0.0, 0.0, 100.0)


def test_component_definition_cycle_is_rejected() -> None:
    source = assembly_document()
    assembly = source.assembly
    assert assembly is not None
    cycle = ComponentInstance(
        "instance:cycle",
        "Engine-1",
        assembly.root_definition_id,
        "definition:subassembly",
    )
    invalid = replace(
        source, assembly=replace(assembly, instances=(*assembly.instances, cycle))
    )
    with pytest.raises(CadDocumentValidationError, match="contains a cycle"):
        invalid.assert_valid()


def test_disconnected_mate_path_and_invalid_transform_are_rejected() -> None:
    source = assembly_document()
    assembly = source.assembly
    assert assembly is not None
    invalid_instance = replace(assembly.instances[0], transform=Matrix4((1.0,) * 15))
    invalid_entity = replace(
        assembly.mate_entities[1], instance_path=("instance:part",)
    )
    invalid = replace(
        source,
        assembly=replace(
            assembly,
            instances=(invalid_instance, *assembly.instances[1:]),
            mate_entities=(assembly.mate_entities[0], invalid_entity),
        ),
    )
    errors = invalid.validate()
    assert "component instance instance:subassembly has an invalid transform" in errors
    assert "mate entity mate-entity:part has a disconnected instance path" in errors


def test_assembly_mesh_roundtrip_preserves_geometry_and_definition_links() -> None:
    source = assembly_document()
    assembly = source.assembly
    assert assembly is not None
    mesh = Mesh(
        "mesh:1",
        "Piston face",
        (Vector3(0.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)),
        ((0, 1, 2),),
        normals=(Vector3(0.0, 0.0, 1.0),) * 3,
    )
    definitions = tuple(
        (
            replace(definition, mesh_ids=(mesh.id,))
            if definition.id == "definition:part"
            else definition
        )
        for definition in assembly.definitions
    )
    extended = replace(
        source,
        meshes=(mesh,),
        assembly=replace(assembly, definitions=definitions),
    )
    extended.assert_valid()
    restored = CadDocument.from_json(extended.to_json())
    assert restored == extended


def test_assembly_mesh_validation_rejects_nonfinite_and_invalid_indices() -> None:
    source = assembly_document()
    assembly = source.assembly
    assert assembly is not None
    mesh = Mesh(
        "mesh:invalid",
        "Invalid",
        (Vector3(float("nan"), 0.0, 0.0),),
        ((0, 1, 2),),
        normals=(Vector3(0.0, 0.0, 1.0), Vector3(0.0, 0.0, 1.0)),
    )
    invalid = replace(source, meshes=(mesh,))
    errors = invalid.validate()
    assert "mesh mesh:invalid contains a non-finite vertex" in errors
    assert "mesh mesh:invalid has a mismatched normal count" in errors
    assert "mesh mesh:invalid contains an invalid triangle" in errors


def test_assembly_validation_includes_linked_document_errors() -> None:
    source = assembly_document()
    assembly = source.assembly
    assert assembly is not None
    linked = assembly.documents[0]
    invalid_linked = replace(linked.document, configurations=())
    invalid = replace(
        source,
        assembly=replace(
            assembly,
            documents=(replace(linked, document=invalid_linked),),
        ),
    )
    assert (
        "component document document:part: document has no configuration"
        in invalid.validate()
    )

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace
from io import BytesIO
import struct

from convert.adapters.solidworks.adapter import (
    _UNSYNTHESISED_ASSEMBLY_STREAMS,
    _generated_streams,
    _native_attestation,
    _replay_compatibility,
    write_sldprt,
)
from convert.adapters.solidworks.assembly import (
    MATE_ADVISORY_LOSS_REASONS,
    MATE_BLOCKING_LOSS_REASONS,
    MATE_LOSS_ENTITY_FRAME,
    MATE_LOSS_ENTITY_REFERENCE,
    MATE_LOSS_EXPRESSION,
    MATE_LOSS_REASONS,
    MATE_LOSS_VALUE_MISSING,
    MATE_REJECTION_REASONS,
    encode_native_assembly,
)
from convert.adapters.solidworks.native import (
    decode_native_model_header,
    encode_native_assembly_envelope,
    encode_native_part,
)
from interchange import (
    Capability,
    MateAlignment,
    MateKind,
    Matrix4,
    ParameterValue,
    ValueKind,
    frozen_mapping,
)
from tests.interchange.test_assembly import assembly_document
from tests.interchange.test_document import document

_ASSEMBLY_ENVELOPE_STREAMS = (
    "Contents/CMgrHdr2",
    "Contents/CnfgObjs",
    "Contents/Config-0-Attachment",
    "Contents/Config-0-ModelHeader",
    "Contents/CusProps",
    "Contents/OleItems",
    "Contents/View Orientation Data",
    "Contents/eModelLic",
    "Header2",
    "ModelStamps",
    "_MO_VERSION_13000/AssyVisualData",
    "_MO_VERSION_13000/Biography",
    "_MO_VERSION_13000/History",
    "docProps/Config-0-Cutlist-Properties.xml",
    "docProps/Config-0-Properties.xml",
    "docProps/OpenTime.xml",
    "swXmlContents/Tables",
)
_PERSISTENT_ASSEMBLY_MATE = "moPlaneSurfIdRep_c,1,2, "
_PERSISTENT_ROOT_MATE = "moPlaneSurfIdRep_c,3,4, "


def _persistent_mate_document(**mate_overrides):
    source = assembly_document()
    assembly = source.assembly
    root_entity, component_entity = assembly.mate_entities
    root_entity = replace(
        root_entity,
        source_entity_id=_PERSISTENT_ROOT_MATE,
        attributes=frozen_mapping({"persistent_references": (_PERSISTENT_ROOT_MATE,)}),
    )
    component_entity = replace(
        component_entity,
        source_entity_id=_PERSISTENT_ASSEMBLY_MATE,
        attributes=frozen_mapping(
            {"persistent_references": (_PERSISTENT_ASSEMBLY_MATE,)}
        ),
    )
    mate = replace(
        assembly.mates[0],
        entity_ids=(component_entity.id, root_entity.id),
        alignment=MateAlignment.ALIGNED,
        **mate_overrides,
    )
    return replace(
        source,
        assembly=replace(
            assembly,
            mate_entities=(component_entity, root_entity),
            mates=(mate,),
        ),
    )


def _encode(source):
    assembly = source.assembly
    return encode_native_assembly(assembly, source.configurations, "Engine")


def test_generated_assembly_emits_the_full_envelope_stream_group() -> None:
    generated = _generated_streams(assembly_document())
    for name in _ASSEMBLY_ENVELOPE_STREAMS:
        assert name in generated.streams
    assert "swXmlContents/COMPINSTANCETREE" in generated.streams
    assert generated.streams["Contents/OleItems"] == b"\0\0\0\0"
    assert generated.streams["Contents/eModelLic"] == b"\0\0\0\0"
    assert generated.streams["Contents/Config-0-Attachment"] == b"\0\0"
    assert generated.streams["_MO_VERSION_13000/AssyVisualData"] == b"\0\0\0\0"
    assert generated.streams["swXmlContents/Tables"] == b""
    assert b"moAssyFilePropContainer_c" in generated.streams["Contents/CusProps"]
    assert (
        generated.streams["docProps/Config-0-Cutlist-Properties.xml"]
        == b'<Configuration id="0" Name="Default"/>\r\n'
    )


def test_generated_assembly_header_decodes_to_the_component_and_mate_tree() -> None:
    generated = _generated_streams(assembly_document())
    assert (
        generated.streams["Header2"]
        == generated.streams["Contents/Config-0-ModelHeader"]
    )
    header = decode_native_model_header(generated.streams["Header2"])
    assert header.user_name == "Kit"
    assert header.reference_name == "Assem1"
    assert header.configuration_name == "Default"
    assert header.document_path.casefold().endswith(".sldasm")
    names = tuple(name for _, name in header.objects)
    assert names[:6] == (
        "Annotations",
        "Front Plane",
        "Top Plane",
        "Right Plane",
        "Origin",
        "Lights, Cameras and Scene",
    )
    assert "Mates" in names
    assert names[-3:] == ("Piston-1", "Piston-1", "Coincident1")
    assert tuple(object_id for object_id, _ in header.objects) == tuple(
        range(2, 2 + len(header.objects))
    )


def test_assembly_envelope_reports_incomplete_for_unencodable_object_names() -> None:
    source = assembly_document()
    envelope = encode_native_assembly_envelope(source, "Engine", ("Piston-1",), ("",))
    assert envelope.omitted_object_names == ("",)
    assert envelope.envelope_complete is False
    complete = encode_native_assembly_envelope(
        source, "Engine", ("Piston-1",), ("Coincident1",)
    )
    assert complete.omitted_object_names == ()
    assert complete.envelope_complete is True


def test_part_header_objects_are_unchanged_by_the_assembly_refactor() -> None:
    part = encode_native_part(document(), "Part")
    header = decode_native_model_header(part.envelope_streams["Header2"])
    assert header.reference_name == "Part1"
    assert tuple(name for _, name in header.objects) == (
        "Annotations",
        "Front Plane",
        "Top Plane",
        "Right Plane",
        "Origin",
        "Lights and Cameras",
        "Design Binder",
        "Comments",
        "Solid Bodies",
        "Surface Bodies",
        "Material <not specified>",
        "Ambient",
        "Directional1",
        "Directional2",
        "Directional3",
        "Equations",
        "Notes",
        "Notes1___EndTag___",
        "Markups",
        "Sensors",
        "Favorites",
        "History",
        "Selection Sets",
    )
    assert header.document_path == ""


def test_generated_assembly_is_vendor_loadable_without_claiming_usability() -> None:
    output = BytesIO()
    result = write_sldprt(assembly_document(), output)
    assert result.vendor_loadable is True
    assert result.application_usable is False
    assert result.metadata["compatibility"] == "native-assembly-with-kit-neutral"
    assert result.metadata["native_assembly"] is True
    assert result.metadata["native_self_contained"] is False
    message = next(
        item.message
        for item in result.diagnostics
        if item.code == "sldasm.unexpressed_native_records"
    )
    for name in _UNSYNTHESISED_ASSEMBLY_STREAMS:
        assert f"absent_vendor_stream:{name}" in message


def test_generated_assembly_attestation_replays_its_own_compatibility() -> None:
    output = BytesIO()
    write_sldprt(assembly_document(), output)
    data = output.getvalue()
    attestation = _native_attestation(data)
    assert attestation is not None
    assert attestation["compatibility"] == "native-assembly-with-kit-neutral"
    assert attestation["vendor_loadable"] is True
    assert attestation["application_usable"] is False
    assert _replay_compatibility(data) == "native-assembly-with-kit-neutral"


def test_incomplete_component_structure_withholds_vendor_loadable() -> None:
    source = assembly_document()
    assembly = source.assembly
    broken = replace(
        source,
        assembly=replace(
            assembly,
            definitions=(
                replace(assembly.definitions[0]),
                replace(assembly.definitions[1], kind="drawing"),
                assembly.definitions[2],
            ),
        ),
    )
    generated = _generated_streams(broken)
    assert generated.vendor_loadable is False
    assert generated.application_usable is False
    assert generated.compatibility == "kit-neutral-only"
    assert "component_structure_incomplete:1" in generated.unexpressed


def test_advisory_mate_losses_do_not_void_the_native_mate_records() -> None:
    source = _persistent_mate_document()
    assembly = source.assembly
    framed = replace(
        source,
        assembly=replace(
            assembly,
            mate_entities=(
                replace(
                    assembly.mate_entities[0],
                    frame=Matrix4(
                        (
                            1.0,
                            0.0,
                            0.0,
                            5.0,
                            0.0,
                            1.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            1.0,
                            0.0,
                            0.0,
                            0.0,
                            0.0,
                            1.0,
                        )
                    ),
                ),
                assembly.mate_entities[1],
            ),
            mates=(replace(assembly.mates[0], parameter_ids=("parameter:offset",)),),
        ),
    )
    encoding = _encode(framed)
    reasons = {
        reason
        for values in encoding.generated_mate_losses.values()
        for reason in values
    }
    assert MATE_LOSS_ENTITY_FRAME in reasons
    assert MATE_LOSS_EXPRESSION in reasons
    assert reasons <= MATE_ADVISORY_LOSS_REASONS
    assert encoding.mates_complete is True
    assert encoding.unsupported_mate_ids == ()
    generated = _generated_streams(framed)
    assert Capability.ASSEMBLY_MATES in generated.native_capabilities
    assert generated.vendor_loadable is True


def test_blocking_mate_value_loss_voids_the_native_mate_records() -> None:
    blocked = _persistent_mate_document(kind=MateKind.DISTANCE, value=None)
    encoding = _encode(blocked)
    reasons = {
        reason
        for values in encoding.generated_mate_losses.values()
        for reason in values
    }
    assert reasons == {MATE_LOSS_VALUE_MISSING}
    assert MATE_LOSS_VALUE_MISSING in MATE_BLOCKING_LOSS_REASONS
    assert encoding.mates_complete is False
    generated = _generated_streams(blocked)
    assert Capability.ASSEMBLY_MATES not in generated.native_capabilities
    assert generated.application_usable is False


def test_resolved_expression_value_is_written_into_the_native_dimension() -> None:
    driven = _persistent_mate_document(
        kind=MateKind.DISTANCE,
        value=ParameterValue(12.5, ValueKind.LENGTH, "mm"),
        parameter_ids=("parameter:offset",),
    )
    encoding = _encode(driven)
    assert encoding.mates_complete is True
    stream = encoding.mate_streams["Contents/Config-0-MatesList"]
    assert struct.pack("<d", 0.0125) in stream


def test_unencodable_mate_entity_reference_reports_a_precise_reason() -> None:
    source = assembly_document()
    encoding = _encode(source)
    assert encoding.mates_complete is False
    assert encoding.unsupported_mate_ids == ("mate:1",)
    assert encoding.unsupported_mate_reasons == {
        "mate:1": (MATE_LOSS_ENTITY_REFERENCE,)
    }


def test_mate_loss_reason_groups_partition_the_registry() -> None:
    assert MATE_BLOCKING_LOSS_REASONS & MATE_ADVISORY_LOSS_REASONS == frozenset()
    assert MATE_BLOCKING_LOSS_REASONS & MATE_REJECTION_REASONS == frozenset()
    assert MATE_ADVISORY_LOSS_REASONS & MATE_REJECTION_REASONS == frozenset()
    assert (
        MATE_BLOCKING_LOSS_REASONS | MATE_ADVISORY_LOSS_REASONS | MATE_REJECTION_REASONS
    ) == MATE_LOSS_REASONS

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

from convert import write_document
from convert.adapters.solidworks.adapter import (
    _ASSEMBLY_READER_REQUIRED_STREAMS,
    _generated_streams,
    _native_attestation,
    _replay_compatibility,
    write_sldprt,
)
from convert.adapters.solidworks.assembly_core import AsmCoreItem, EncodeAsmCore
from convert.adapters.solidworks.archive import encode_string
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
from convert.adapters.solidworks.container import SldprtArchive
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
    "Contents/CMgr",
    "Contents/CMgrHdr2",
    "Contents/CnfgObjs",
    "Contents/Config-0",
    "Contents/Config-0-Attachment",
    "Contents/Config-0-ModelHeader",
    "Contents/Config-0-ResolvedFeatures",
    "Contents/CusProps",
    "Contents/Definition",
    "Contents/OleItems",
    "Contents/View Orientation Data",
    "Contents/eModelLic",
    "Header2",
    "ModelStamps",
    "_MO_VERSION_18000/AssyVisualData",
    "_MO_VERSION_18000/Biography",
    "_MO_VERSION_18000/History",
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
    assert generated.streams["_MO_VERSION_18000/AssyVisualData"] == b"\0\0\0\0"
    assert generated.streams["swXmlContents/Tables"] == b""
    assert b"moAssyFilePropContainer_c" in generated.streams["Contents/CusProps"]
    assert (
        generated.streams["docProps/Config-0-Cutlist-Properties.xml"]
        == b'<Configuration id="0" Name="Default"/>\r\n'
    )


def test_generated_assembly_header_is_the_coupled_native_history_header() -> None:
    generated = _generated_streams(assembly_document())
    assert (
        generated.streams["Header2"]
        == generated.streams["Contents/Config-0-ModelHeader"]
    )
    assert len(generated.streams["Header2"]) > 2000
    assert "Engine".encode("utf-16le") in generated.streams["Header2"]
    assert "Piston-1".encode("utf-16le") in generated.streams["Header2"]


# unsupported fixed state must fail before vendor loadability is claimed
def test_fixed_component_fails_closed() -> None:
    SourceData = assembly_document()
    AssemblyValue = SourceData.assembly
    FixedData = replace(
        SourceData,
        assembly=replace(
            AssemblyValue,
            instances=(
                replace(AssemblyValue.instances[0], fixed=True),
                *AssemblyValue.instances[1:],
            ),
        ),
    )
    GeneratedData = _generated_streams(FixedData)
    assert GeneratedData.vendor_loadable is False
    assert GeneratedData.application_usable is False
    assert GeneratedData.compatibility == "kit-neutral-only"
    assert "component_structure_incomplete:1" in GeneratedData.unexpressed


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


def test_generated_assembly_is_vendor_loadable_with_no_reader_gaps() -> None:
    output = BytesIO()
    result = write_sldprt(assembly_document(), output)
    assert result.vendor_loadable is True
    assert result.application_usable is False
    assert result.metadata["compatibility"] == "native-assembly-with-kit-neutral"
    assert result.metadata["native_assembly"] is True
    assert result.metadata["native_self_contained"] is False
    assert all(
        item.code != "sldasm.vendor_reader_rejects" for item in result.diagnostics
    )
    for name in _ASSEMBLY_READER_REQUIRED_STREAMS:
        assert name in SldprtArchive.from_bytes(output.getvalue()).streams


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


# six unique component records verify the recovered distinct-path recurrence
def test_distinct_component_core_scales_without_opaque_payloads() -> None:
    CoreItems = tuple(
        AsmCoreItem(
            f"unit_{ItemIndex}-1",
            f"C:\\generated\\unit_{ItemIndex}.SLDPRT",
            (ItemIndex - 1) * 0.05,
        )
        for ItemIndex in range(1, 7)
    )
    StreamsMap = EncodeAsmCore("SixDistinct", "Default", CoreItems)
    HeaderData = StreamsMap["Contents/Config-0-ModelHeader"]
    assert StreamsMap["Header2"] == HeaderData
    assert len(StreamsMap["Contents/Config-0-ResolvedFeatures"]) == 5722
    assert len(StreamsMap["Contents/Config-0-MatesList"]) == 6
    for ItemValue in CoreItems:
        assert ItemValue.OccurName.encode("utf-16le") in HeaderData
        assert ItemValue.CompPath.encode("utf-16le") in HeaderData
    assert struct.pack("<d", 0.25) in StreamsMap["Contents/Config-0"]
    assert StreamsMap["Contents/Definition"][3479:3483] == struct.pack(
        "<i", len(CoreItems)
    )


# same-file recurrence must replace the traced definition count semantically
def test_repeated_component_core_writes_the_actual_definition_count() -> None:
    CoreItems = tuple(
        AsmCoreItem(
            f"unit_1-{ItemIndex}",
            "C:\\generated\\unit_1.SLDPRT",
            (ItemIndex - 1) * 0.05,
            FileStamp=1001,
        )
        for ItemIndex in range(1, 7)
    )
    StreamsMap = EncodeAsmCore("SixRepeated", "Default", CoreItems)
    assert StreamsMap["Contents/Definition"][3479:3483] == struct.pack(
        "<i", len(CoreItems)
    )


# rotation recurrence preserves every component transform field
def test_recurrence_cores_write_translation_and_rotation_values() -> None:
    BasisVals = (0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    RouteItems = (
        tuple(
            AsmCoreItem(
                f"repeat-1-{ItemIndex}",
                "C:\\generated\\repeat.SLDPRT",
                0.123 if ItemIndex == 1 else 0.456 + ItemIndex,
                0.234 if ItemIndex == 1 else 0.567 + ItemIndex,
                0.345 if ItemIndex == 1 else 0.678 + ItemIndex,
            )
            for ItemIndex in range(1, 5)
        ),
        tuple(
            AsmCoreItem(
                f"distinct-{ItemIndex}-1",
                f"C:\\generated\\distinct-{ItemIndex}.SLDPRT",
                0.123 if ItemIndex == 1 else 0.456 + ItemIndex,
                0.234 if ItemIndex == 1 else 0.567 + ItemIndex,
                0.345 if ItemIndex == 1 else 0.678 + ItemIndex,
                FileStamp=2000 + ItemIndex,
            )
            for ItemIndex in range(1, 4)
        ),
        (
            AsmCoreItem(
                "hybrid-1-1",
                "C:\\generated\\hybrid-1.SLDPRT",
                0.123,
                0.234,
                0.345,
                FileStamp=3001,
            ),
            AsmCoreItem(
                "hybrid-1-2",
                "C:\\generated\\hybrid-1.SLDPRT",
                2.456,
                2.567,
                2.678,
                FileStamp=3001,
            ),
            AsmCoreItem(
                "hybrid-2-1",
                "C:\\generated\\hybrid-2.SLDPRT",
                3.456,
                3.567,
                3.678,
                FileStamp=3002,
            ),
            AsmCoreItem(
                "hybrid-3-1",
                "C:\\generated\\hybrid-3.SLDPRT",
                4.456,
                4.567,
                4.678,
                FileStamp=3003,
            ),
        ),
    )
    for RouteIndex, CoreItems in enumerate(RouteItems, 1):
        RotatedItems = (replace(CoreItems[0], BasisVals=BasisVals), *CoreItems[1:])
        PlainConfig = EncodeAsmCore(
            f"TransformRoute{RouteIndex}", "Default", CoreItems
        )["Contents/Config-0"]
        RotatedConfig = EncodeAsmCore(
            f"TransformRoute{RouteIndex}", "Default", RotatedItems
        )["Contents/Config-0"]
        assert len(RotatedConfig) == len(PlainConfig) + 72
        assert struct.unpack_from("<I", RotatedConfig, 18)[0] == (
            struct.unpack_from("<I", PlainConfig, 18)[0] + 72
        )
        assert struct.pack("<9d", *BasisVals) in RotatedConfig
        for ExpectedValue in (0.123, 0.234, 0.345):
            assert struct.pack("<d", ExpectedValue) in RotatedConfig


# mixed component paths verify independent occurrence and unique-file growth
def test_mixed_component_core_scales_without_opaque_payloads() -> None:
    PathNumbers = (1, 1, 2, 2, 3, 3, 4)
    OccurNumbers = (1, 2, 1, 2, 1, 2, 1)
    CoreItems = tuple(
        AsmCoreItem(
            f"unit_{PathNumber}-{OccurNumber}",
            f"C:\\generated\\unit_{PathNumber}.SLDPRT",
            (ItemIndex - 1) * 0.05,
            FileStamp=1000 + PathNumber,
        )
        for ItemIndex, (PathNumber, OccurNumber) in enumerate(
            zip(PathNumbers, OccurNumbers, strict=True), 1
        )
    )
    StreamsMap = EncodeAsmCore("SevenMixed", "Default", CoreItems)
    SixStreams = EncodeAsmCore("SevenMixed", "Default", CoreItems[:-1])
    HeaderData = StreamsMap["Contents/Config-0-ModelHeader"]
    assert len(StreamsMap["Contents/CMgr"]) - len(SixStreams["Contents/CMgr"]) == 378
    assert (
        len(StreamsMap["Contents/Config-0"]) - len(SixStreams["Contents/Config-0"])
        == 502
    )
    assert (
        len(StreamsMap["Contents/Config-0-ResolvedFeatures"])
        - len(SixStreams["Contents/Config-0-ResolvedFeatures"])
        == 56
    )
    AddedFile = "C:\\generated\\unit_4.SLDPRT"
    assert len(HeaderData) - len(SixStreams["Contents/Config-0-ModelHeader"]) == (
        58 + 79 + len(encode_string(AddedFile))
    )
    for ItemValue in CoreItems:
        assert ItemValue.OccurName.encode("utf-16le") in HeaderData
    for PathNumber in set(PathNumbers):
        PathData = f"C:\\generated\\unit_{PathNumber}.SLDPRT".encode("utf-16le")
        assert HeaderData.count(PathData) == 1
        assert struct.pack("<I", 1000 + PathNumber) in HeaderData
    assert struct.pack("<d", 0.3) in StreamsMap["Contents/Config-0"]
    assert StreamsMap["Contents/Definition"][3479:3483] == struct.pack(
        "<i", len(CoreItems)
    )


# shared internal identities preserve the recovered degenerate mixed-file grammar
def test_shared_identity_mixed_core_uses_the_typed_vendor_recurrence() -> None:
    CoreItems = tuple(
        AsmCoreItem(
            f"unit_{ItemIndex // 2 + 1}-{ItemIndex % 2 + 1}",
            f"C:\\generated\\unit_{ItemIndex // 2 + 1}.SLDPRT",
            ItemIndex * 0.05,
            FileStamp=123456,
        )
        for ItemIndex in range(6)
    )
    SevenItems = (
        *CoreItems,
        AsmCoreItem(
            "unit_4-1",
            "C:\\generated\\unit_4.SLDPRT",
            0.3,
            FileStamp=123456,
        ),
    )
    SixStreams = EncodeAsmCore("SharedIdentity", "Default", CoreItems)
    SevenStreams = EncodeAsmCore("SharedIdentity", "Default", SevenItems)
    assert (
        len(SevenStreams["Contents/Config-0"]) - len(SixStreams["Contents/Config-0"])
        == 422
    )
    assert SixStreams["Contents/Definition"][3479:3483] == struct.pack(
        "<i", len(CoreItems)
    )
    assert SevenStreams["Contents/Definition"][3479:3483] == struct.pack(
        "<i", len(SevenItems)
    )


# public staged writes must serialize final sibling paths into native headers
def test_public_assembly_bundle_has_no_staging_paths(tmp_path) -> None:
    OutputPath = tmp_path / "final" / "Engine.SLDASM"
    write_document(assembly_document(), OutputPath)
    HeaderData = b"".join(
        SldprtArchive.open(PathValue).streams["Contents/Config-0-ModelHeader"]
        for PathValue in OutputPath.parent.iterdir()
        if PathValue.suffix.casefold() == ".sldasm"
    )
    assert ".kit-".encode("utf-16le") not in HeaderData
    assert str(OutputPath.parent.resolve()).encode("utf-16le") in HeaderData
    MemberPath = next(
        PathValue
        for PathValue in OutputPath.parent.iterdir()
        if PathValue != OutputPath
    )
    MemberPath.write_bytes(b"stale")
    write_document(assembly_document(), OutputPath, overwrite=True)
    assert MemberPath.read_bytes() != b"stale"
    HeaderData = b"".join(
        SldprtArchive.open(PathValue).streams["Contents/Config-0-ModelHeader"]
        for PathValue in OutputPath.parent.iterdir()
        if PathValue.suffix.casefold() == ".sldasm"
    )
    for MemberPath in OutputPath.parent.iterdir():
        if MemberPath == OutputPath:
            continue
        StampData = SldprtArchive.open(MemberPath).streams["ModelStamps"]
        assert StampData[:4] in HeaderData


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
    assert generated.compatibility == "native-assembly-with-kit-neutral"
    assert "component_structure_incomplete:1" not in generated.unexpressed


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

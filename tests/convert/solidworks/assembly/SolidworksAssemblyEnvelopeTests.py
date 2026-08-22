# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import replace as ReplaceData
from io import BytesIO
from pathlib import Path as FilePath
import struct as StructLib
from convert import write_document as WriteDocument
from convert.adapters.solidworks.core.Adapter import (
    GeneratedB as GeneratedStreams,
    KAsmReaderRequiredStreams as Streams,
    Native as NativeAttestation,
    Replay as ReplayCompatibility,
    write_sldprt as WriteSldprt,
)
from convert.adapters.solidworks.assembly.AssemblyCore import AsmCoreItem, EncodeAsmCore
from convert.adapters.solidworks.container.Archive import encode_string as EncodeString
from convert.adapters.solidworks.assembly.Assembly import (
    KMateAdvisoryLossReasons as Reasons,
    KMateBlockingLossReasons as ReasonsA,
    KMateLossEntityFrame as Frame,
    KMateLossEntityRef as Reference,
    KMateLossExpression as Expression,
    KMateLossReasons as ReasonsB,
    KMateLossValueMissing as Missing,
    KMateRejectionReasons as ReasonsC,
    NativeAssemblyEncoding,
    encode_native_assembly as EncodeNativeAssembly,
)
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.core.Native import (
    decode_native_model_header as DecodeNativeModelHeader,
    encode_native_assembly_envelope as EncodeNAE,
    encode_native_part as EncodeNativePart,
)
from interchange import (
    Capability,
    CadDocument,
    MateAlignment,
    MateKind,
    Matrix4 as MatrixFour,
    ParameterValue,
    ValueKind,
    frozen_mapping as FrozenMapping,
)
from tests.interchange.assembly.AssemblyTests import (
    assembly_document as AssemblyDocument,
)
from tests.interchange.document.DocumentTests import document as Document

# centralizes shared evidence so every related assertion uses one value
KStreams = (
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

# centralizes shared evidence so every related assertion uses one value
KMateInfo = "moPlaneSurfIdRep_c,1,2, "

# centralizes shared evidence so every related assertion uses one value
KMateInfoA = "moPlaneSurfIdRep_c,3,4, "


# keeps this focused behavior isolated so regressions remain immediately visible
def PersistentMD(**MateOverrides: object) -> CadDocument:
    SourceDoc = AssemblyDocument()
    Assembly = SourceDoc.assembly
    assert Assembly is not None
    RootEntity, ComponentEntity = Assembly.mate_entities
    RootEntity = ReplaceData(
        RootEntity,
        source_entity_id=KMateInfoA,
        attributes=FrozenMapping({"persistent_references": (KMateInfoA,)}),
    )
    ComponentEntity = ReplaceData(
        ComponentEntity,
        source_entity_id=KMateInfo,
        attributes=FrozenMapping({"persistent_references": (KMateInfo,)}),
    )
    MateInfo = ReplaceData(
        Assembly.mates[0],
        EntityIds=(ComponentEntity.EntityId, RootEntity.EntityId),
        alignment=MateAlignment.ALIGNED,
        **MateOverrides,
    )
    return ReplaceData(
        SourceDoc,
        assembly=ReplaceData(
            Assembly,
            mate_entities=(ComponentEntity, RootEntity),
            mates=(MateInfo,),
        ),
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def Encode(SourceDoc: CadDocument) -> NativeAssemblyEncoding:
    Assembly = SourceDoc.Assembly
    assert Assembly is not None
    return EncodeNativeAssembly(Assembly, SourceDoc.Configurations, "Engine")


# keeps this focused behavior isolated so regressions remain immediately visible
def TestGAETFESG() -> None:
    Generated = GeneratedStreams(AssemblyDocument())
    for NameText in KStreams:
        assert NameText in Generated.streams
    assert "swXmlContents/COMPINSTANCETREE" in Generated.streams
    assert Generated.streams["Contents/OleItems"] == b"\x00\x00\x00\x00"
    assert Generated.streams["Contents/eModelLic"] == b"\x00\x00\x00\x00"
    assert Generated.streams["Contents/Config-0-Attachment"] == b"\x00\x00"
    assert Generated.streams["_MO_VERSION_18000/AssyVisualData"] == b"\x00\x00\x00\x00"
    assert Generated.streams["swXmlContents/Tables"] == b""
    assert b"moAssyFilePropContainer_c" in Generated.streams["Contents/CusProps"]
    assert (
        Generated.streams["docProps/Config-0-Cutlist-Properties.xml"]
        == b'<Configuration id="0" Name="Default"/>\r\n'
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestGAHITCNHH() -> None:
    Generated = GeneratedStreams(AssemblyDocument())
    assert (
        Generated.streams["Header2"]
        == Generated.streams["Contents/Config-0-ModelHeader"]
    )
    assert len(Generated.streams["Header2"]) > 2000
    assert "Engine".encode("utf-16le") in Generated.streams["Header2"]
    assert "Piston-1".encode("utf-16le") in Generated.streams["Header2"]


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFCFC() -> None:
    SourceData = AssemblyDocument()
    AssemblyValue = SourceData.assembly
    assert AssemblyValue is not None
    FixedData = ReplaceData(
        SourceData,
        assembly=ReplaceData(
            AssemblyValue,
            instances=(
                ReplaceData(AssemblyValue.instances[0], fixed=True),
                *AssemblyValue.instances[1:],
            ),
        ),
    )
    GeneratedData = GeneratedStreams(FixedData)
    assert GeneratedData.vendor_loadable is False
    assert GeneratedData.application_usable is False
    assert GeneratedData.compatibility == "kit-neutral-only"
    assert "component_structure_incomplete:1" in GeneratedData.unexpressed


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAERIFUON() -> None:
    SourceDoc = AssemblyDocument()
    Envelope = EncodeNAE(SourceDoc, "Engine", ("Piston-1",), ("",))
    assert Envelope.omitted_object_names == ("",)
    assert Envelope.envelope_complete is False
    Complete = EncodeNAE(SourceDoc, "Engine", ("Piston-1",), ("Coincident1",))
    assert Complete.omitted_object_names == ()
    assert Complete.envelope_complete is True


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPHOAUBTAR() -> None:
    PartDoc = EncodeNativePart(Document(), "Part")
    Header = DecodeNativeModelHeader(PartDoc.envelope_streams["Header2"])
    assert Header.reference_name == "Part1"
    assert tuple((NameText for _, NameText in Header.objects)) == (
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
    assert Header.document_path == ""


# keeps this focused behavior isolated so regressions remain immediately visible
def TestGAIVLWNRG() -> None:
    Output = BytesIO()
    ResultInfo = WriteSldprt(AssemblyDocument(), Output)
    assert ResultInfo.IsVendorLoadable is True
    assert ResultInfo.IsAppUsable is False
    assert ResultInfo.MetadataMap["compatibility"] == "native-assembly-with-kit-neutral"
    assert ResultInfo.MetadataMap["native_assembly"] is True
    assert ResultInfo.MetadataMap["native_self_contained"] is False
    assert all(
        (
            ItemValueA.code != "sldasm.vendor_reader_rejects"
            for ItemValueA in ResultInfo.Diagnostics
        )
    )
    for NameText in Streams:
        assert NameText in SldprtArchive.from_bytes(Output.getvalue()).streams


# keeps this focused behavior isolated so regressions remain immediately visible
def TestGAARIOC() -> None:
    Output = BytesIO()
    WriteSldprt(AssemblyDocument(), Output)
    DataValue = Output.getvalue()
    Attestation = NativeAttestation(DataValue)
    assert Attestation is not None
    assert Attestation["compatibility"] == "native-assembly-with-kit-neutral"
    assert Attestation["vendor_loadable"] is True
    assert Attestation["application_usable"] is False
    assert ReplayCompatibility(DataValue) == "native-assembly-with-kit-neutral"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDCCSWOP() -> None:
    CoreItems = tuple(
        (
            AsmCoreItem(
                f"unit_{ItemIndex}-1",
                f"C:\\generated\\unit_{ItemIndex}.SLDPRT",
                (ItemIndex - 1) * 0.05,
            )
            for ItemIndex in range(1, 7)
        )
    )
    StreamsMap = EncodeAsmCore("SixDistinct", "Default", CoreItems)
    HeaderData = StreamsMap["Contents/Config-0-ModelHeader"]
    assert StreamsMap["Header2"] == HeaderData
    assert len(StreamsMap["Contents/Config-0-ResolvedFeatures"]) == 5722
    assert len(StreamsMap["Contents/Config-0-MatesList"]) == 6
    for ItemValue in CoreItems:
        assert ItemValue.OccurName.encode("utf-16le") in HeaderData
        assert ItemValue.CompPath.encode("utf-16le") in HeaderData
    assert StructLib.pack("<d", 0.25) in StreamsMap["Contents/Config-0"]
    assert StreamsMap["Contents/Definition"][3479:3483] == StructLib.pack(
        "<i", len(CoreItems)
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRCCWTADC() -> None:
    CoreItems = tuple(
        (
            AsmCoreItem(
                f"unit_1-{ItemIndex}",
                "C:\\generated\\unit_1.SLDPRT",
                (ItemIndex - 1) * 0.05,
                FileStamp=1001,
            )
            for ItemIndex in range(1, 7)
        )
    )
    StreamsMap = EncodeAsmCore("SixRepeated", "Default", CoreItems)
    assert StreamsMap["Contents/Definition"][3479:3483] == StructLib.pack(
        "<i", len(CoreItems)
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRCWTARV() -> None:
    BasisVals = (0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    RouteItems = (
        tuple(
            (
                AsmCoreItem(
                    f"repeat-1-{ItemIndex}",
                    "C:\\generated\\repeat.SLDPRT",
                    0.123 if ItemIndex == 1 else 0.456 + ItemIndex,
                    0.234 if ItemIndex == 1 else 0.567 + ItemIndex,
                    0.345 if ItemIndex == 1 else 0.678 + ItemIndex,
                )
                for ItemIndex in range(1, 5)
            )
        ),
        tuple(
            (
                AsmCoreItem(
                    f"distinct-{ItemIndex}-1",
                    f"C:\\generated\\distinct-{ItemIndex}.SLDPRT",
                    0.123 if ItemIndex == 1 else 0.456 + ItemIndex,
                    0.234 if ItemIndex == 1 else 0.567 + ItemIndex,
                    0.345 if ItemIndex == 1 else 0.678 + ItemIndex,
                    FileStamp=2000 + ItemIndex,
                )
                for ItemIndex in range(1, 4)
            )
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
        RotatedItems = (ReplaceData(CoreItems[0], BasisVals=BasisVals), *CoreItems[1:])
        PlainConfig = EncodeAsmCore(
            f"TransformRoute{RouteIndex}", "Default", CoreItems
        )["Contents/Config-0"]
        RotatedConfig = EncodeAsmCore(
            f"TransformRoute{RouteIndex}", "Default", RotatedItems
        )["Contents/Config-0"]
        assert len(RotatedConfig) == len(PlainConfig) + 72
        assert (
            StructLib.unpack_from("<I", RotatedConfig, 18)[0]
            == StructLib.unpack_from("<I", PlainConfig, 18)[0] + 72
        )
        assert StructLib.pack("<9d", *BasisVals) in RotatedConfig
        for ExpectedValue in (0.123, 0.234, 0.345):
            assert StructLib.pack("<d", ExpectedValue) in RotatedConfig


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMCCSWOP() -> None:
    PathNumbers = (1, 1, 2, 2, 3, 3, 4)
    OccurNumbers = (1, 2, 1, 2, 1, 2, 1)
    CoreItems = tuple(
        (
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
    assert len(HeaderData) - len(
        SixStreams["Contents/Config-0-ModelHeader"]
    ) == 58 + 79 + len(EncodeString(AddedFile))
    for ItemValue in CoreItems:
        assert ItemValue.OccurName.encode("utf-16le") in HeaderData
    for PathNumber in set(PathNumbers):
        PathData = f"C:\\generated\\unit_{PathNumber}.SLDPRT".encode("utf-16le")
        assert HeaderData.count(PathData) == 1
        assert StructLib.pack("<I", 1000 + PathNumber) in HeaderData
    assert StructLib.pack("<d", 0.3) in StreamsMap["Contents/Config-0"]
    assert StreamsMap["Contents/Definition"][3479:3483] == StructLib.pack(
        "<i", len(CoreItems)
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSIMCUTTVR() -> None:
    CoreItems = tuple(
        (
            AsmCoreItem(
                f"unit_{ItemIndex // 2 + 1}-{ItemIndex % 2 + 1}",
                f"C:\\generated\\unit_{ItemIndex // 2 + 1}.SLDPRT",
                ItemIndex * 0.05,
                FileStamp=123456,
            )
            for ItemIndex in range(6)
        )
    )
    SevenItems = (
        *CoreItems,
        AsmCoreItem("unit_4-1", "C:\\generated\\unit_4.SLDPRT", 0.3, FileStamp=123456),
    )
    SixStreams = EncodeAsmCore("SharedIdentity", "Default", CoreItems)
    SevenStreams = EncodeAsmCore("SharedIdentity", "Default", SevenItems)
    assert (
        len(SevenStreams["Contents/Config-0"]) - len(SixStreams["Contents/Config-0"])
        == 422
    )
    assert SixStreams["Contents/Definition"][3479:3483] == StructLib.pack(
        "<i", len(CoreItems)
    )
    assert SevenStreams["Contents/Definition"][3479:3483] == StructLib.pack(
        "<i", len(SevenItems)
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPABHNSP(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "final" / "Engine.SLDASM"
    WriteDocument(AssemblyDocument(), OutputPath)
    HeaderData = b"".join(
        (
            SldprtArchive.open(PathValue).streams["Contents/Config-0-ModelHeader"]
            for PathValue in OutputPath.parent.iterdir()
            if PathValue.suffix.casefold() == ".sldasm"
        )
    )
    assert ".kit-".encode("utf-16le") not in HeaderData
    assert str(OutputPath.parent.resolve()).encode("utf-16le") in HeaderData
    MemberPath = next(
        (
            PathValue
            for PathValue in OutputPath.parent.iterdir()
            if PathValue != OutputPath
        )
    )
    MemberPath.write_bytes(b"stale")
    WriteDocument(AssemblyDocument(), OutputPath, overwrite=True)
    assert MemberPath.read_bytes() != b"stale"
    HeaderData = b"".join(
        (
            SldprtArchive.open(PathValue).streams["Contents/Config-0-ModelHeader"]
            for PathValue in OutputPath.parent.iterdir()
            if PathValue.suffix.casefold() == ".sldasm"
        )
    )
    for MemberPath in OutputPath.parent.iterdir():
        if MemberPath == OutputPath:
            continue
        StampData = SldprtArchive.open(MemberPath).streams["ModelStamps"]
        assert StampData[:4] in HeaderData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestICSWVL() -> None:
    SourceDoc = AssemblyDocument()
    Assembly = SourceDoc.assembly
    assert Assembly is not None
    Broken = ReplaceData(
        SourceDoc,
        assembly=ReplaceData(
            Assembly,
            definitions=(
                ReplaceData(Assembly.definitions[0]),
                ReplaceData(Assembly.definitions[1], kind="drawing"),
                Assembly.definitions[2],
            ),
        ),
    )
    Generated = GeneratedStreams(Broken)
    assert Generated.vendor_loadable is False
    assert Generated.application_usable is False
    assert Generated.compatibility == "kit-neutral-only"
    assert "component_structure_incomplete:1" in Generated.unexpressed


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAMLDNVTNMR() -> None:
    SourceDoc = PersistentMD()
    Assembly = SourceDoc.assembly
    assert Assembly is not None
    Framed = ReplaceData(
        SourceDoc,
        assembly=ReplaceData(
            Assembly,
            mate_entities=(
                ReplaceData(
                    Assembly.mate_entities[0],
                    frame=MatrixFour(
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
                Assembly.mate_entities[1],
            ),
            mates=(
                ReplaceData(Assembly.mates[0], parameter_ids=("parameter:offset",)),
            ),
        ),
    )
    Encoding = Encode(Framed)
    ReasonsD = {
        Reason
        for ValueList in Encoding.generated_mate_losses.values()
        for Reason in ValueList
    }
    assert Frame in ReasonsD
    assert Expression in ReasonsD
    assert ReasonsD <= Reasons
    assert Encoding.mates_complete is True
    assert Encoding.unsupported_mate_ids == ()
    Generated = GeneratedStreams(Framed)
    assert Capability.ASSEMBLY_MATES in Generated.native_capabilities
    assert Generated.compatibility == "native-assembly-with-kit-neutral"
    assert "component_structure_incomplete:1" not in Generated.unexpressed


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBMVLVTNMR() -> None:
    Blocked = PersistentMD(kind=MateKind.DISTANCE, value=None)
    Encoding = Encode(Blocked)
    ReasonsD = {
        Reason
        for ValueList in Encoding.generated_mate_losses.values()
        for Reason in ValueList
    }
    assert ReasonsD == {Missing}
    assert Missing in ReasonsA
    assert Encoding.mates_complete is False
    Generated = GeneratedStreams(Blocked)
    assert Capability.ASSEMBLY_MATES not in Generated.native_capabilities
    assert Generated.application_usable is False


# keeps this focused behavior isolated so regressions remain immediately visible
def TestREVIWITND() -> None:
    Driven = PersistentMD(
        kind=MateKind.DISTANCE,
        value=ParameterValue(12.5, ValueKind.LENGTH, "mm"),
        parameter_ids=("parameter:offset",),
    )
    Encoding = Encode(Driven)
    assert Encoding.mates_complete is True
    Stream = Encoding.mate_streams["Contents/Config-0-MatesList"]
    assert StructLib.pack("<d", 0.0125) in Stream


# keeps this focused behavior isolated so regressions remain immediately visible
def TestUMERRAPR() -> None:
    SourceDoc = AssemblyDocument()
    Encoding = Encode(SourceDoc)
    assert Encoding.mates_complete is False
    assert Encoding.unsupported_mate_ids == ("mate:1",)
    assert Encoding.unsupported_mate_reasons == {"mate:1": (Reference,)}


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMLRGPTR() -> None:
    assert ReasonsA & Reasons == frozenset()
    assert ReasonsA & ReasonsC == frozenset()
    assert Reasons & ReasonsC == frozenset()
    assert ReasonsA | Reasons | ReasonsC == ReasonsB

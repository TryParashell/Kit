# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass as DataClass
from functools import lru_cache as LruCache
import hashlib as Hashlib
from pathlib import Path as PathValue
import re as RegexLib
import struct as Struct
from typing import Mapping as TypeMap

import pytest as Pytest

from convert.adapters.base.ContractTypes import (
    KSourceType as SourceData,
    KTargetType as TargetData,
)
from convert.adapters.base.TransferContract import CarrierReason
from convert.adapters.solidworks import SldprtFormatError
from convert.api.ApiContext import KAdapterRegistry as Registry
from convert.api.ApiConvert import ConvertFile as Convert
from convert.api.ApiOpen import OpenDocument
from convert.engine.EngineResult import ConversionResult
from interchange.assembly.AssemblyData import AssemblyData
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentPayload import GetPayloadIds
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordParameter import Parameter
from interchange.records.RecordProvenance import Provenance


# mesh comparisons need stable names so nested document signatures remain statically concrete
@DataClass(frozen=True, slots=True)
class MeshSig:
    EntityId: str
    EntityName: str
    VertexCount: int
    TriangleCount: int
    NormalCount: int
    ContentDigest: str
    Provenance: Provenance | None
    Attributes: TypeMap[str, object]


# payload comparisons need validated bytes and explicit fields instead of anonymous tuple positions
@DataClass(frozen=True, slots=True)
class BrepSig:
    EntityId: str
    FormatId: str
    EntityKind: str
    SchemaText: str
    SourceDigest: str
    ByteCount: int | None
    ContentDigest: str | None
    SourceStream: str
    Provenance: Provenance | None
    Attributes: TypeMap[str, object]
    ValueRole: PayloadRole
    FileExtension: str


# assembly recursion needs a named contract so embedded documents retain their concrete signature
@DataClass(frozen=True, slots=True)
class AssemblySig:
    RootDefinitionId: str
    Definitions: tuple[ComponentDef, ...]
    Instances: tuple[ComponentInst, ...]
    Documents: tuple[tuple[str, DocumentSig], ...]
    MateEntities: tuple[MateEntity, ...]
    Mates: tuple[MateConstraint, ...]
    MateGroups: tuple[MateGroup, ...]
    Attributes: TypeMap[str, object]


# document equality needs an explicit cross format contract rather than a partially unknown tuple
@DataClass(frozen=True, slots=True)
class DocumentSig:
    Configurations: tuple[Configuration, ...]
    Parameters: tuple[Parameter, ...]
    SupportPlanes: tuple[SupportPlane, ...]
    Sketches: tuple[Sketch, ...]
    Selections: tuple[Selection, ...]
    FeatureTimeline: tuple[FeatureStep, ...]
    Bodies: tuple[DesignBody, ...]
    Meshes: tuple[MeshSig, ...]
    BrepPayloads: tuple[BrepSig, ...]
    Capabilities: frozenset[Capability]
    Units: UnitSystem
    SchemaVersion: str
    Assembly: AssemblySig | None


# output flags need runtime validation because writer metadata is an extensible object mapping
def IsMetaFlag(Metadata: TypeMap[str, object], KeyValue: str) -> bool:
    FlagValue = Metadata.get(KeyValue)
    if not isinstance(FlagValue, bool):
        raise TypeError(f"output metadata {KeyValue!r} must be a bool")
    return FlagValue


# referenced file accounting needs an integer distinct from boolean metadata values
def GetMetaCount(Metadata: TypeMap[str, object], KeyValue: str) -> int:
    CountValue = Metadata.get(KeyValue)
    if not isinstance(CountValue, int) or isinstance(CountValue, bool):
        raise TypeError(f"output metadata {KeyValue!r} must be an int")
    return CountValue


# compatibility branches need a validated text discriminator before policy checks
def GetMetaText(Metadata: TypeMap[str, object], KeyValue: str) -> str:
    TextValue = Metadata.get(KeyValue)
    if not isinstance(TextValue, str):
        raise TypeError(f"output metadata {KeyValue!r} must be a string")
    return TextValue


# this binding exists because shared behavior needs one stable value
KRootValue = PathValue(__file__).parents[3]

# this binding exists because shared behavior needs one stable value
KReadme = KRootValue / "README.md"

# this binding exists because shared behavior needs one stable value
KExamples = KRootValue / "examples"

# this binding exists because shared behavior needs one stable value
KFormatBySuffix = {
    ".SLDPRT": "solidworks.sldprt",
    ".SLDASM": "solidworks.sldasm",
    ".FCStd": "freecad.fcstd",
    ".CATPart": "catia.v5",
    ".CATProduct": "catia.v5",
}

# this binding exists because shared behavior needs one stable value
KPartSuffixes = (".SLDPRT", ".FCStd", ".CATPart")

# this binding exists because shared behavior needs one stable value
KAssemblySuffixes = (".SLDASM", ".FCStd", ".CATProduct")

# this binding exists because shared behavior needs one stable value
KSupportedSuffixes = frozenset(KFormatBySuffix)

# this binding exists because shared behavior needs one stable value
KExpectedSuffixCounts = {
    ".SLDPRT": 111,
    ".SLDASM": 9,
    ".FCStd": 68,
    ".CATPart": 27,
    ".CATProduct": 3,
}

# this binding exists because shared behavior needs one stable value
KFcstdAssemblies = frozenset(
    {
        KExamples / "Random" / "V8_engine" / "Conrod_2.FCStd",
        KExamples / "Random" / "V8_engine" / "Piston_2.FCStd",
        KExamples / "Random" / "V8_engine.FCStd",
    }
)

# these sources exercise every supported part format reader
KPartSources = (
    (
        "sldprt",
        ".SLDPRT",
        KExamples / ".SLDPRT" / "example.SLDPRT",
        False,
    ),
    (
        "fcstd_part",
        ".FCStd",
        KExamples / "Random" / "V8_engine" / "hex bolt gradeb_iso.FCStd",
        False,
    ),
    (
        "catpart",
        ".CATPart",
        KExamples / ".CATPart" / "Banjo.CATPart",
        False,
    ),
)

# these sources exercise every supported assembly format reader
KAssemblySources = (
    ("sldasm", ".SLDASM", KExamples / "Random" / "Pistons" / "Piston.SLDASM", True),
    (
        "fcstd_assembly",
        ".FCStd",
        KExamples / "Random" / "V8_engine" / "Conrod_2.FCStd",
        True,
    ),
    (
        "catproduct",
        ".CATProduct",
        KExamples / ".CATProduct" / "Brake_Pedal_Assembly - Backup 2.CATProduct",
        True,
    ),
)

# this ordered source matrix preserves part before assembly test execution
KMatrixSources = KPartSources + KAssemblySources

# this binding exists because shared behavior needs one stable value
KMatrixCases = tuple(
    (NameValue, SourceSuffix, Source, IsAssembly, DestinationSuffix)
    for NameValue, SourceSuffix, Source, IsAssembly in KMatrixSources
    for DestinationSuffix in (KAssemblySuffixes if IsAssembly else KPartSuffixes)
)

# this binding exists because shared behavior needs one stable value
KCorpusFiles = tuple(
    sorted(
        PathValueA
        for PathValueA in KExamples.rglob("*")
        if PathValueA.is_file()
        and PathValueA.suffix.casefold()
        in {Value.casefold() for Value in KSupportedSuffixes}
    )
)

# this binding exists because shared behavior needs one stable value
KMissingReferenceFiles = {
    KExamples
    / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
    / "ENSAMBLAJE DE MOTOR V8.SLDASM": "ENSAMBLAJE TURBO.SLDASM",
}

# this binding exists because shared behavior needs one stable value
KSupportedFiles = tuple(
    PathValueA
    for PathValueA in KCorpusFiles
    if PathValueA not in KMissingReferenceFiles
)


# this definition exists because focused behavior needs one stable owner
def AssemblyS(Assembly: AssemblyData | None) -> AssemblySig | None:
    if Assembly is None:
        return None
    Documents: list[tuple[str, DocumentSig]] = []
    for Component in Assembly.Documents:
        Embedded = Component.Document
        Documents.append((Component.EntityId, DocumentS(Embedded)))
    return AssemblySig(
        Assembly.RootDefinitionId,
        Assembly.Definitions,
        Assembly.Instances,
        tuple(Documents),
        Assembly.MateEntities,
        Assembly.Mates,
        Assembly.MateGroups,
        Assembly.Attributes,
    )


# this definition exists because focused behavior needs one stable owner
def DocumentS(Document: CadDocument) -> DocumentSig:
    EmbeddedFormat: object = Document.Source.Attributes.get("embedded_source_format_id")
    EnvelopeIndexes: frozenset[int] = (
        GetPayloadIds(Document) if isinstance(EmbeddedFormat, str) else frozenset[int]()
    )
    return DocumentSig(
        Document.Configurations,
        Document.Parameters,
        Document.SupportPlanes,
        Document.Sketches,
        Document.Selections,
        Document.FeatureTimeline,
        Document.Bodies,
        tuple(MeshSignature(MeshValue) for MeshValue in Document.Meshes),
        tuple(
            BrepSignature(Payload)
            for Index, Payload in enumerate(Document.BrepPayloads)
            if Index not in EnvelopeIndexes
        ),
        Document.Capabilities,
        Document.Units,
        Document.SchemaVersion,
        AssemblyS(Document.Assembly),
    )


# this definition exists because focused behavior needs one stable owner
def MeshSignature(MeshValue: SurfaceMesh) -> MeshSig:
    Digest = Hashlib.sha256()
    for Vertex in MeshValue.Vertices:
        Digest.update(Struct.pack("!ddd", Vertex.XCoord, Vertex.YCoord, Vertex.ZCoord))
    for Triangle in MeshValue.Triangles:
        Digest.update(Struct.pack("!qqq", *Triangle))
    for Normal in MeshValue.Normals:
        Digest.update(Struct.pack("!ddd", Normal.XCoord, Normal.YCoord, Normal.ZCoord))
    return MeshSig(
        MeshValue.EntityId,
        MeshValue.EntityName,
        len(MeshValue.Vertices),
        len(MeshValue.Triangles),
        len(MeshValue.Normals),
        Digest.hexdigest(),
        MeshValue.Provenance,
        MeshValue.Attributes,
    )


# this definition exists because focused behavior needs one stable owner
def BrepSignature(Payload: BrepPayload) -> BrepSig:
    PayloadId = Payload.EntityId
    Attributes: TypeMap[str, object] = Payload.Attributes
    PayloadData = Payload.PayloadData
    if Payload.FormatId == "catia.v5.cfv2" and Payload.EntityKind == "native_document":
        PayloadId = "catia:native-document"
        Attributes = {
            KeyValue: Value
            for KeyValue, Value in Attributes.items()
            if KeyValue != "catia.replay_semantic_sha256"
        }
    elif (
        Payload.FormatId == "catia.v5.sha256"
        and Payload.EntityKind == "native_document_binding"
    ):
        PayloadId = "catia:native-document-binding"
    return BrepSig(
        PayloadId,
        Payload.FormatId,
        Payload.EntityKind,
        Payload.SchemaText,
        Payload.SourceDigest,
        len(PayloadData) if PayloadData is not None else None,
        Hashlib.sha256(PayloadData).hexdigest() if PayloadData is not None else None,
        Payload.SourceStream,
        Payload.Provenance,
        Attributes,
        Payload.ValueRole,
        Payload.FileExtension,
    )


# this definition exists because focused behavior needs one stable owner
def Suffix(PathValueA: PathValue) -> str:
    return next(
        Value
        for Value in KFormatBySuffix
        if Value.casefold() == PathValueA.suffix.casefold()
    )


# this definition exists because focused behavior needs one stable owner
def IsAssemblyFile(Source: PathValue) -> bool:
    SuffixA = Suffix(Source)
    return SuffixA in {".SLDASM", ".CATProduct"} or Source in KFcstdAssemblies


# this definition exists because focused behavior needs one stable owner
def AssertTarget(
    Document: CadDocument,
    SuffixA: str,
    Source: PathValue | bytes,
    IsAssembly: bool,
) -> None:
    assert (Document.Assembly is not None) == IsAssembly
    if SuffixA in {".SLDPRT", ".SLDASM"}:
        assert Document.Source.FormatId == KFormatBySuffix[SuffixA]
    elif SuffixA in {".CATPart", ".CATProduct"}:
        assert Document.Metadata["catia.document_type"] == SuffixA[1:]
    else:
        assert Registry.select_reader(Source).info.format_id == "freecad.fcstd"


# this helper verifies the cross format transfer and losslessness contract
def AssertTransfer(Result: ConversionResult, SuffixA: str) -> None:
    assert not Result.application_usable or Result.vendor_loadable
    ExpectedNearLossless = (
        Result.application_usable
        and Result.vendor_loadable
        and not Result.requirements
        and not Result.dropped
        and all(
            Transfer.carrier_reason is CarrierReason.TARGET_UNSUPPORTED
            for Transfer in Result.transfers
            if Transfer.carrier_reason is not None
        )
    )
    assert Result.near_lossless is ExpectedNearLossless
    GeometryTransfers = {
        Transfer.capability
        for Transfer in Result.transfers
        if Transfer.capability in {Capability.BREP, Capability.TESSELLATION}
    }
    if SuffixA == ".FCStd" and GeometryTransfers and Result.application_usable:
        assert GeometryTransfers & Result.output.native_capabilities


# this helper verifies native metadata types and emitted reference files
def AssertMetaShape(Result: ConversionResult, IsAssembly: bool) -> None:
    Metadata = Result.output.metadata
    IsMetaFlag(Metadata, "vendor_loadable")
    IsMetaFlag(Metadata, "native_geometry")
    IsMetaFlag(Metadata, "native_history")
    IsMetaFlag(Metadata, "native_assembly")
    NativeSelfContained = IsMetaFlag(Metadata, "native_self_contained")
    ReferencedFilesWritten = GetMetaCount(Metadata, "referenced_files_written")
    assert ReferencedFilesWritten >= 0
    if ReferencedFilesWritten:
        assert IsAssembly
        PathValueA = Result.output.path
        assert PathValueA is not None
        Siblings = tuple(
            ItemValue
            for ItemValue in PathValueA.parent.iterdir()
            if ItemValue.is_file() and ItemValue != PathValueA
        )
        assert len(Siblings) == ReferencedFilesWritten
        assert all(ItemValue.stat().st_size > 0 for ItemValue in Siblings)
        assert NativeSelfContained is Result.application_usable


# this helper verifies native capability claims against emitted metadata
def AssertNative(Result: ConversionResult, IsAssembly: bool) -> None:
    Metadata = Result.output.metadata
    Compatibility = GetMetaText(Metadata, "compatibility")
    VendorLoadable = IsMetaFlag(Metadata, "vendor_loadable")
    NativeGeometry = IsMetaFlag(Metadata, "native_geometry")
    NativeHistory = IsMetaFlag(Metadata, "native_history")
    NativeAssembly = IsMetaFlag(Metadata, "native_assembly")
    NativeSelfContained = IsMetaFlag(Metadata, "native_self_contained")
    if Compatibility == "native-exact":
        assert VendorLoadable is True
        assert NativeGeometry is True
        assert NativeHistory is True
        assert NativeAssembly is IsAssembly
        assert NativeSelfContained is (not IsAssembly)
        return
    Native = Result.output.native_capabilities
    if NativeGeometry:
        assert Capability.BREP in Native
    if NativeHistory:
        History = tuple(
            Transfer
            for Transfer in Result.output.transfers
            if Transfer.capability is Capability.PARAMETRIC_HISTORY
        )
        assert not History or Capability.PARAMETRIC_HISTORY in Native
    if NativeAssembly:
        assert IsAssembly
        assert Capability.ASSEMBLIES in Native
    if NativeSelfContained:
        assert Result.application_usable is True
        assert Result.vendor_loadable is True


# this helper applies the complete target verification rules to one result
def AssertTVR(
    Result: ConversionResult,
    SuffixA: str,
    IsAssembly: bool,
) -> None:
    AssertTransfer(Result, SuffixA)
    if SuffixA not in {".SLDPRT", ".SLDASM", ".CATPart", ".CATProduct"}:
        return
    AssertMetaShape(Result, IsAssembly)
    AssertNative(Result, IsAssembly)


# this definition exists because focused behavior needs one stable owner
def ConvertWAG(Source: SourceData, Destination: TargetData) -> ConversionResult:
    Result = Convert(Source, Destination)
    assert Result.requirements == ()
    assert Result.dropped == frozenset()
    assert Result.roundtrip_safe is True
    return Result


# this definition exists because focused behavior needs one stable owner
@LruCache(maxsize=len(KMatrixSources))
def MatrixDocument(Source: PathValue) -> CadDocument:
    return OpenDocument(Source)


# this definition exists because focused behavior needs one stable owner
def TestSFMRADK() -> None:
    Supported = KReadme.read_text(encoding="utf-8").split("## Supported formats", 1)[1]
    Supported = Supported.split("\n## ", 1)[0]
    ReadmeSuffixes = set(RegexLib.findall(r"`(\.[A-Za-z0-9]+)`", Supported))
    assert ReadmeSuffixes == set(KFormatBySuffix)
    assert set(KPartSuffixes) | set(KAssemblySuffixes) == ReadmeSuffixes
    assert set(KPartSuffixes) & set(KAssemblySuffixes) == {".FCStd"}
    Counts = Counter(Suffix(PathValueA) for PathValueA in KCorpusFiles)
    MissingSuffixes = tuple(
        SuffixName
        for SuffixName, ExpectedCount in KExpectedSuffixCounts.items()
        if Counts[SuffixName] == 0 and ExpectedCount
    )
    for SuffixName, ExpectedCount in KExpectedSuffixCounts.items():
        if SuffixName not in MissingSuffixes:
            assert Counts[SuffixName] == ExpectedCount
    if MissingSuffixes:
        Pytest.skip(
            "bundled example corpus is unavailable for " + ", ".join(MissingSuffixes)
        )
    assert len(KCorpusFiles) == 218
    assert len(KSupportedFiles) == 217
    assert Counts == KExpectedSuffixCounts
    assert len(KFcstdAssemblies) == 3
    assert KFcstdAssemblies <= set(KSupportedFiles)
    assert set(KMissingReferenceFiles) <= set(KCorpusFiles)


# this test swaps one representative of each source type through every compatible format
@Pytest.mark.parametrize(
    ("NameValue", "SourceSuffix", "Source", "IsAssembly", "DestinationSuffix"),
    KMatrixCases,
    ids=[f"{CaseValue[0]}-to-{CaseValue[4][1:].lower()}" for CaseValue in KMatrixCases],
)
def TestEVFSRBD(
    NameValue: str,
    SourceSuffix: str,
    Source: PathValue,
    IsAssembly: bool,
    DestinationSuffix: str,
    TmpPath: PathValue,
) -> None:
    Original = (
        MatrixDocument(Source)
        if Source.is_file()
        else Pytest.skip(f"bundled example source is unavailable: {Source.name}")
    )
    assert (Original.Assembly is not None) == IsAssembly
    OriginalSignature = DocumentS(Original)
    ForwardDirectory = TmpPath / f"{NameValue}_forward"
    ForwardDirectory.mkdir()
    Destination = ForwardDirectory / f"{NameValue}_swapped{DestinationSuffix}"
    Result = ConvertWAG(Source, Destination)
    Restored = OpenDocument(Destination)
    assert Result.source_format == KFormatBySuffix[SourceSuffix]
    assert Result.destination_format == KFormatBySuffix[DestinationSuffix]
    assert Result.output.path == Destination.resolve()
    assert Result.output.bytes_written == Destination.stat().st_size
    assert Restored.GetErrors() == ()
    assert DocumentS(Restored) == OriginalSignature
    AssertTarget(Restored, DestinationSuffix, Destination, IsAssembly)
    AssertTVR(Result, DestinationSuffix, IsAssembly)
    ReverseDirectory = TmpPath / f"{NameValue}_reverse"
    ReverseDirectory.mkdir()
    Reverse = ReverseDirectory / f"{NameValue}_reversed{SourceSuffix}"
    ReverseResult = ConvertWAG(Destination, Reverse)
    ReversedDocument = OpenDocument(Reverse)
    assert ReverseResult.source_format == KFormatBySuffix[DestinationSuffix]
    assert ReverseResult.destination_format == KFormatBySuffix[SourceSuffix]
    assert ReverseResult.output.bytes_written == Reverse.stat().st_size
    assert ReversedDocument.GetErrors() == ()
    assert DocumentS(ReversedDocument) == OriginalSignature
    AssertTarget(ReversedDocument, SourceSuffix, Reverse, IsAssembly)
    AssertTVR(ReverseResult, SourceSuffix, IsAssembly)


# this test verifies missing assembly references fail with the unresolved filename
@Pytest.mark.parametrize(
    "Source",
    tuple(KMissingReferenceFiles),
    ids=lambda PathValueA: str(PathValueA.relative_to(KExamples)),
)
def TestAMIRFARBN(Source: PathValue) -> None:
    Missing = KMissingReferenceFiles[Source]
    assert not tuple(KExamples.rglob(Missing))
    with Pytest.raises(SldprtFormatError) as Captured:
        OpenDocument(Source)
    Message = str(Captured.value)
    assert Message.startswith("nested assembly mate source is unavailable: ")
    assert Message.endswith(Missing)


# this test verifies every bundled source can be read through its registered adapter
@Pytest.mark.parametrize(
    "Source",
    KSupportedFiles,
    ids=lambda PathValueA: str(PathValueA.relative_to(KExamples)),
)
def TestESESTEVFAB(
    Source: PathValue,
) -> None:
    SourceSuffix = Suffix(Source)
    Document = OpenDocument(Source)
    IsAssembly = Document.Assembly is not None
    assert Document.GetErrors() == ()
    assert IsAssembly is IsAssemblyFile(Source)
    AssertTarget(Document, SourceSuffix, Source, IsAssembly)

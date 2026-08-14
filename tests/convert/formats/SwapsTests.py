# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections import Counter
from functools import lru_cache as LruCache
import gc as GcValue
import hashlib as Hashlib
from pathlib import Path as PathValue
import re as RegexLib
import shutil as Shutil
import struct as Struct

import pytest as Pytest

from convert import (
    CarrierReason,
    convert as Convert,
    open_document as OpenDocument,
    registry as Registry,
)
from convert.adapters.solidworks import SldprtFormatError
from interchange import (
    AssemblyData,
    CadDocument,
    Capability,
    source_payload_indexes as SourcePayloadIndexes,
)

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
def AssemblyS(Assembly: AssemblyData | None):
    if Assembly is None:
        return None
    return (
        Assembly.root_definition_id,
        Assembly.definitions,
        Assembly.instances,
        tuple(
            (Component.id, DocumentS(Component.document))
            for Component in Assembly.documents
        ),
        Assembly.mate_entities,
        Assembly.mates,
        Assembly.mate_groups,
        Assembly.attributes,
    )


# this definition exists because focused behavior needs one stable owner
def DocumentS(Document: CadDocument):
    EnvelopeIndexes = (
        SourcePayloadIndexes(Document)
        if isinstance(Document.source.attributes.get("embedded_source_format_id"), str)
        else frozenset()
    )
    return (
        Document.configurations,
        Document.parameters,
        Document.support_planes,
        Document.sketches,
        Document.selections,
        Document.feature_timeline,
        Document.bodies,
        tuple(MeshSignature(MeshValue) for MeshValue in Document.meshes),
        tuple(
            BrepSignature(Payload)
            for Index, Payload in enumerate(Document.brep_payloads)
            if Index not in EnvelopeIndexes
        ),
        Document.capabilities,
        Document.units,
        Document.schema_version,
        AssemblyS(Document.assembly),
    )


# this definition exists because focused behavior needs one stable owner
def MeshSignature(MeshValue):
    Digest = Hashlib.sha256()
    for Vertex in MeshValue.vertices:
        Digest.update(Struct.pack("!ddd", Vertex.x, Vertex.y, Vertex.z))
    for Triangle in MeshValue.triangles:
        Digest.update(Struct.pack("!qqq", *Triangle))
    for Normal in MeshValue.normals:
        Digest.update(Struct.pack("!ddd", Normal.x, Normal.y, Normal.z))
    return (
        MeshValue.id,
        MeshValue.name,
        len(MeshValue.vertices),
        len(MeshValue.triangles),
        len(MeshValue.normals),
        Digest.hexdigest(),
        MeshValue.provenance,
        MeshValue.attributes,
    )


# this definition exists because focused behavior needs one stable owner
def BrepSignature(Payload):
    PayloadId = Payload.id
    Attributes = Payload.attributes
    if Payload.format_id == "catia.v5.cfv2" and Payload.kind == "native_document":
        PayloadId = "catia:native-document"
        Attributes = {
            KeyValue: Value
            for KeyValue, Value in Attributes.items()
            if KeyValue != "catia.replay_semantic_sha256"
        }
    elif (
        Payload.format_id == "catia.v5.sha256"
        and Payload.kind == "native_document_binding"
    ):
        PayloadId = "catia:native-document-binding"
    return (
        PayloadId,
        Payload.format_id,
        Payload.kind,
        Payload.schema,
        Payload.sha256,
        len(Payload.data) if Payload.data is not None else None,
        (
            Hashlib.sha256(Payload.data).hexdigest()
            if Payload.data is not None
            else None
        ),
        Payload.source_stream,
        Payload.provenance,
        Attributes,
        Payload.role,
        Payload.file_extension,
    )


# this definition exists because focused behavior needs one stable owner
def Suffix(PathValueA: PathValue) -> str:
    return next(
        Value
        for Value in KFormatBySuffix
        if Value.casefold() == PathValueA.suffix.casefold()
    )


# this definition exists because focused behavior needs one stable owner
def TargetSuffixes(Document: CadDocument) -> tuple[str, ...]:
    return KAssemblySuffixes if Document.assembly is not None else KPartSuffixes


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
    assert (Document.assembly is not None) == IsAssembly
    if SuffixA in {".SLDPRT", ".SLDASM"}:
        assert Document.source.format_id == KFormatBySuffix[SuffixA]
    elif SuffixA in {".CATPart", ".CATProduct"}:
        assert Document.metadata["catia.document_type"] == SuffixA[1:]
    else:
        assert Registry.select_reader(Source).info.format_id == "freecad.fcstd"


# this helper verifies the cross format transfer and losslessness contract
def AssertTransfer(Result, SuffixA: str) -> None:
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
def AssertMetaShape(Result, IsAssembly: bool) -> None:
    Metadata = Result.output.metadata
    assert isinstance(Metadata["vendor_loadable"], bool)
    assert isinstance(Metadata["native_geometry"], bool)
    assert isinstance(Metadata["native_history"], bool)
    assert isinstance(Metadata["native_assembly"], bool)
    assert isinstance(Metadata["native_self_contained"], bool)
    ReferencedFilesWritten = Metadata["referenced_files_written"]
    assert isinstance(ReferencedFilesWritten, int)
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
        assert Metadata["native_self_contained"] is Result.application_usable


# this helper verifies native capability claims against emitted metadata
def AssertNative(Result, IsAssembly: bool) -> None:
    Metadata = Result.output.metadata
    if Metadata["compatibility"] == "native-exact":
        assert Metadata["vendor_loadable"] is True
        assert Metadata["native_geometry"] is True
        assert Metadata["native_history"] is True
        assert Metadata["native_assembly"] is IsAssembly
        assert Metadata["native_self_contained"] is (not IsAssembly)
        return
    Native = Result.output.native_capabilities
    if Metadata["native_geometry"]:
        assert Capability.BREP in Native
    if Metadata["native_history"]:
        History = tuple(
            Transfer
            for Transfer in Result.output.transfers
            if Transfer.capability is Capability.PARAMETRIC_HISTORY
        )
        assert not History or Capability.PARAMETRIC_HISTORY in Native
    if Metadata["native_assembly"]:
        assert IsAssembly
        assert Capability.ASSEMBLIES in Native
    if Metadata["native_self_contained"]:
        assert Result.application_usable is True
        assert Result.vendor_loadable is True


# this helper applies the complete target verification rules to one result
def AssertTVR(
    Result,
    SuffixA: str,
    IsAssembly: bool,
) -> None:
    AssertTransfer(Result, SuffixA)
    if SuffixA not in {".SLDPRT", ".SLDASM", ".CATPart", ".CATProduct"}:
        return
    AssertMetaShape(Result, IsAssembly)
    AssertNative(Result, IsAssembly)


# this definition exists because focused behavior needs one stable owner
def ConvertWAG(Source, Destination):
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


# this helper verifies one forward conversion and its restored document
def VerifyForward(
    Source,
    SourceSuffix,
    DestinationSuffix,
    OriginalSignature,
    TmpPath,
    Index,
    IsAssembly,
):
    ForwardDirectory = TmpPath / f"forward_{Index}"
    ForwardDirectory.mkdir()
    Destination = ForwardDirectory / f"converted{DestinationSuffix}"
    Forward = Convert(Source, Destination)
    assert Forward.source_format == KFormatBySuffix[SourceSuffix]
    assert Forward.destination_format == KFormatBySuffix[DestinationSuffix]
    assert Forward.output.bytes_written == Destination.stat().st_size
    assert Forward.requirements == ()
    assert Forward.dropped == frozenset()
    assert Forward.roundtrip_safe is True
    AssertTVR(Forward, DestinationSuffix, IsAssembly)
    del Forward
    GcValue.collect()
    Restored = OpenDocument(Destination)
    assert Restored.validate() == ()
    assert DocumentS(Restored) == OriginalSignature
    AssertTarget(Restored, DestinationSuffix, Destination, IsAssembly)
    del Restored
    GcValue.collect()
    return ForwardDirectory, Destination


# this helper verifies one reverse conversion and its restored document
def VerifyReverse(
    Destination,
    SourceSuffix,
    DestinationSuffix,
    OriginalSignature,
    TmpPath,
    Index,
    IsAssembly,
):
    ReverseDirectory = TmpPath / f"reverse_{Index}"
    ReverseDirectory.mkdir()
    Reverse = ReverseDirectory / f"converted{SourceSuffix}"
    Backward = Convert(Destination, Reverse)
    assert Backward.source_format == KFormatBySuffix[DestinationSuffix]
    assert Backward.destination_format == KFormatBySuffix[SourceSuffix]
    assert Backward.output.bytes_written == Reverse.stat().st_size
    assert Backward.requirements == ()
    assert Backward.dropped == frozenset()
    assert Backward.roundtrip_safe is True
    AssertTVR(Backward, SourceSuffix, IsAssembly)
    del Backward
    GcValue.collect()
    ReversedDocument = OpenDocument(Reverse)
    assert ReversedDocument.validate() == ()
    assert DocumentS(ReversedDocument) == OriginalSignature
    AssertTarget(ReversedDocument, SourceSuffix, Reverse, IsAssembly)
    del ReversedDocument
    GcValue.collect()
    return ReverseDirectory


# this test exhaustively swaps each example through every compatible format
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
    assert (Original.assembly is not None) == IsAssembly
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
    assert Restored.validate() == ()
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
    assert ReversedDocument.validate() == ()
    assert DocumentS(ReversedDocument) == OriginalSignature
    AssertTarget(ReversedDocument, SourceSuffix, Reverse, IsAssembly)
    AssertTVR(ReverseResult, SourceSuffix, IsAssembly)


# this definition exists because focused behavior needs one stable owner
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


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    "Source",
    KSupportedFiles,
    ids=lambda PathValueA: str(PathValueA.relative_to(KExamples)),
)
def TestESESTEVFAB(
    Source: PathValue,
    TmpPath: PathValue,
) -> None:
    SourceSuffix = Suffix(Source)
    Original = OpenDocument(Source)
    IsAssembly = Original.assembly is not None
    assert IsAssembly is IsAssemblyFile(Source)
    OriginalSignature = DocumentS(Original)
    TargetSuffixesA = TargetSuffixes(Original)
    del Original
    GcValue.collect()
    for Index, DestinationSuffix in enumerate(TargetSuffixesA):
        ForwardDirectory, Destination = VerifyForward(
            Source,
            SourceSuffix,
            DestinationSuffix,
            OriginalSignature,
            TmpPath,
            Index,
            IsAssembly,
        )
        ReverseDirectory = VerifyReverse(
            Destination,
            SourceSuffix,
            DestinationSuffix,
            OriginalSignature,
            TmpPath,
            Index,
            IsAssembly,
        )
        Shutil.rmtree(ForwardDirectory)
        Shutil.rmtree(ReverseDirectory)

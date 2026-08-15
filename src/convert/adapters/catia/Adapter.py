# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from collections.abc import Callable
from contextlib import suppress as Suppress
from dataclasses import replace as Replace
import hashlib as Hashlib
import os as OsModule
from pathlib import Path as FilePath
import re as RegexLib
import struct as Struct
from types import MappingProxyType
import zlib as ZlibValue
from convert.adapters.base import (
    AdapterInfo,
    Destination as Target,
    ProbeResult,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
    is_binary_destination as IsBinaryTarget,
)
from convert.geometry.Opencascade import decode_ascii_brep as DecodeOpencascadeBrep
from convert.geometry.Parasolid import decode_brep_model as DecodeParasolidBrep
from interchange import (
    Body as BodyRecord,
    BrepModel,
    BrepPayload,
    CadDocument as CadDoc,
    CadSource,
    Configuration as Config,
    Diagnostic as DiagnosticInfo,
    FeatureKind,
    FeatureStep,
    NativeFeatureDefinition,
    PayloadRole,
    Provenance,
    ProvenanceSpan,
    Severity,
    SupportPlane,
    Transform,
    Vector3 as VectorThree,
    frozen_mapping as FrozenMapping,
    filter_document as FilterDoc,
    infer_capabilities as InferCapabilities,
    semantic_metadata as SemanticMeta,
    with_wrapper_metadata as WithWrapperMeta,
)
from convert.adapters.catia.Assembly import (
    NativeProductTable as ProductTable,
    decode_product_table as DecodeProductTable,
    native_product_assembly as NativeProductAsm,
)
from convert.adapters.catia.Container import (
    Cfv2Archive as CfvTwoArchive,
    Cfv2Declaration as CfvTwoDecl,
    Cfv2Directory as CfvTwoFolder,
    Cfv2FormatError as CfvTwoFormatError,
    Cfv2Stream as CfvTwoStream,
    OsmxArchive,
    OsmxFormatError,
    OsmxSymbol,
    append_cfv2_stream as AppendCfvTwoStream,
    build_cfv2 as BuildCfvTwo,
    build_declaration as BuildDecl,
)
from convert.adapters.catia.Format import (
    DOCUMENT_TYPE_BY_SUFFIX as DocTypeBySuffix,
    INFO as InfoValue,
    PART_DOCUMENT_TYPE as PartDocType,
    PRODUCT_DOCUMENT_TYPE as ProductDocType,
    SUFFIX_BY_DOCUMENT_TYPE as SuffixByDocType,
)

# this binding exists because shared behavior needs one stable value
KFormatId = InfoValue.format_id

# this binding exists because shared behavior needs one stable value
KManifestName = "KitInterchange"

# this binding exists because shared behavior needs one stable value
KManifestMagic = b"KITCFV2\x01"

# this binding exists because shared behavior needs one stable value
KMaxManifestBytes = 512 * 1024 * 1024

# this binding exists because shared behavior needs one stable value
KMaxManifestJsonDepth = 256

# this binding exists because shared behavior needs one stable value
KPartStream = "1000_00000002_2"

# this binding exists because shared behavior needs one stable value
KProductStream = "1000_00000001_1"

# this binding exists because shared behavior needs one stable value
KPartSuffix = SuffixByDocType[PartDocType]

# this binding exists because shared behavior needs one stable value
KProductSuffix = SuffixByDocType[ProductDocType]

# this binding exists because shared behavior needs one stable value
KNativeDocId = "catia:native-document"

# this binding exists because shared behavior needs one stable value
KNativeDocBindingId = "catia:native-document-binding"

# this binding exists because shared behavior needs one stable value
KSavedDocPrefix = "catia:preserved-native-document:"

# this binding exists because shared behavior needs one stable value
KSavedBindingPrefix = "catia:preserved-native-document-binding:"

# this binding exists because shared behavior needs one stable value
KReplaySemanticAttr = "catia.replay_semantic_sha256"

# this binding exists because shared behavior needs one stable value
KOpencascadeFormatIds = frozenset({"freecad.brep", "opencascade", "opencascade.brep"})

# this binding exists because shared behavior needs one stable value
KParasolidFormatIds = frozenset({"parasolid", "parasolid.x_b", "parasolid.x_t"})

# this binding exists because shared behavior needs one stable value
KNeutralBrepFormatIds = KOpencascadeFormatIds | KParasolidFormatIds

# this binding exists because shared behavior needs one stable value
KWrapperMetaKeys = frozenset(
    {
        "catia.container_classes",
        "catia.container_compatibility",
        "catia.document_type",
        "catia.embedded_source_application_version",
        "catia.embedded_source_attributes",
        "catia.embedded_source_container_version",
        "catia.embedded_source_format_id",
        "catia.embedded_source_path",
        "catia.embedded_source_sha256",
        "catia.nested_directory_count",
        "catia.outer_directory_length",
        "catia.outer_directory_offset",
        "catia.outer_streams",
        "catia.roundtrip_sha256",
    }
)


# this definition exists because focused behavior needs one stable owner
class CatiaAdapterA(RuntimeError):
    __slots__ = ()


# this definition exists because focused behavior needs one stable owner
class CatiaMetadata:

    # this definition exists because focused behavior needs one stable owner
    @property
    def info(self) -> AdapterInfo:
        return InfoValue

    # this definition exists because focused behavior needs one stable owner
    def probe(self, Source: Source) -> ProbeResult:
        try:
            DataValue, _ = SourceBytesMut(Source)
            Archive = CfvTwoArchive.from_bytes(DataValue)
            Manifest = ManifestBytes(Archive)
            if Manifest is not None:
                ManifestDoc(Manifest)
                return ProbeResult(KFormatId, 1.0, "Kit manifest in V5_CFV2")
            Declarations = Archive.declarations()
            if Declarations:
                return ProbeResult(KFormatId, 1.0, "native CATIA container graph")
            return ProbeResult(KFormatId, 0.9, "valid V5_CFV2 stream directory")
        except (
            CatiaAdapterA,
            CfvTwoFormatError,
            OSError,
            TypeError,
            ValueError,
            ZlibValue.error,
        ) as ErrorInfo:
            return ProbeResult(KFormatId, 0.0, str(ErrorInfo))


# this definition exists because focused behavior needs one stable owner
class CatiaReader:

    # this definition exists because focused behavior needs one stable owner
    def read(self, Source: Source, Options: ReadOptions | None = None) -> CadDoc:
        Settings = Options or ReadOptions()
        DataValue, Label = SourceBytesMut(Source)
        Archive = CfvTwoArchive.from_bytes(DataValue)
        Manifest = ManifestBytes(Archive)
        if Manifest is not None:
            return EmbeddedDoc(Archive, DataValue, Label, Manifest, Settings)
        DocType = DetectDocType(Archive, Label)
        Payloads = NativePayloads(Archive, DataValue, DocType, Settings)
        if DocType == ProductDocType:
            AsmValue, AsmDiagnostics = NativeProductAsm(
                Archive, Label, Settings, self.read
            )
        else:
            AsmValue, AsmDiagnostics = (None, ())
        PartMeta, SupportPlanes, FeatureTimeline, Bodies, PartDiagnostics = (
            NativePartData(Archive, DocType)
        )
        Version = AppVersion(DataValue)
        MetaValue = {
            "catia.document_type": DocType,
            "catia.outer_directory_offset": Archive.outer.offset,
            "catia.outer_directory_length": Archive.outer.length,
            "catia.outer_streams": tuple(
                (
                    (Stream.name, Stream.logical_length)
                    for Stream in Archive.outer.streams
                )
            ),
            "catia.nested_directory_count": len(Archive.nested),
            "catia.container_classes": tuple(
                (
                    (
                        Value.ordinal,
                        Value.class_name,
                        Value.base_class,
                        Value.stream_name,
                    )
                    for Value in Archive.declarations()
                )
            ),
            **ContainerMeta(Archive),
            **PartMeta,
        }
        DocValue = CadDoc(
            source=CadSource(
                KFormatId,
                Label,
                Hashlib.sha256(DataValue).hexdigest(),
                container_version="V5_CFV2",
                application_version=Version,
            ),
            configurations=Selected(
                (Config("catia:default", "Default", active=True),),
                Settings.configuration,
            ),
            parameters=(),
            support_planes=SupportPlanes,
            sketches=(),
            selections=(),
            feature_timeline=FeatureTimeline,
            bodies=Bodies,
            brep_payloads=Payloads,
            brep=TypedBrep(Payloads, Bodies),
            diagnostics=AsmDiagnostics + PartDiagnostics,
            capabilities=frozenset(),
            metadata=WithWrapperMeta(MetaValue, KWrapperMetaKeys),
            assembly=AsmValue,
        )
        DocValue = Replace(
            DocValue, capabilities=InferCapabilities(DocValue, roundtrip_metadata=True)
        )
        Digest = SemanticDigest(DocValue)
        DocValue = Replace(
            DocValue,
            metadata=FrozenMapping(
                {**DocValue.metadata, "catia.roundtrip_sha256": Digest}
            ),
        )
        if Settings.strict:
            DocValue.assert_valid()
        return DocValue


# this definition exists because focused behavior needs one stable owner
class CatiaSupport:

    # this definition exists because focused behavior needs one stable owner
    def supports(self, DocValue: CadDocument, Target: Destination) -> bool:
        if isinstance(Target, (str, FilePath)):
            Expected = KProductSuffix if DocValue.assembly is not None else KPartSuffix
            return FilePath(Target).suffix.casefold() == Expected
        return IsBinaryTarget(Target)


# this definition exists because focused behavior needs one stable owner
class CatiaWriter:

    # this definition exists because focused behavior needs one stable owner
    def write(
        self,
        DocValue: CadDocument,
        Target: Destination,
        Options: WriteOptions | None = None,
    ) -> WriteResult:
        Settings = Options or WriteOptions()
        if Settings.validate:
            DocValue.assert_valid()
        DocType = TargetType(DocValue, Target)
        NativeChoice = UnchangedNative(DocValue, DocType)
        if NativeChoice is not None and CanReplayNative(Settings, DocValue):
            return WriteReplay(DocValue, Target, Settings, DocType, NativeChoice[0])
        if Settings.values.get("allow_non_native", True) is not True:
            raise CatiaAdapterA(
                "generated CATIA writing requires WriteOptions(values={'allow_non_native': True})"
            )
        CarrierDoc = CarrierManifest(DocValue)
        NativeBase = (
            NativeBaseA(DocValue, DocType)
            if CanReplayNative(Settings, DocValue)
            else None
        )
        if NativeBase is not None:
            return WriteNativeBase(
                DocValue, Target, Settings, DocType, CarrierDoc, NativeBase
            )
        return WriteCarrier(DocValue, Target, Settings, DocType, CarrierDoc)


# this definition exists because focused behavior needs one stable owner
class CatiaAdapter(CatiaMetadata, CatiaReader, CatiaSupport, CatiaWriter):
    __slots__ = ()


# this definition exists because focused behavior needs one stable owner
def CanReplayNative(Settings: WriteOptions, DocValue: CadDocument) -> bool:
    return not Settings.values.get("rebuild", False) and not (
        Settings.values.get("portable") is True and DocValue.assembly is not None
    )


# this definition exists because focused behavior needs one stable owner
def WriteReplay(
    DocValue: CadDocument,
    Target: Destination,
    Settings: WriteOptions,
    DocType: str,
    Native: bytes,
) -> WriteResult:
    Compatibility = Replay(Native)
    NativeExact = Compatibility == "native-exact"
    NativeBaseSaved = Compatibility == "native-base-neutral-overlay"
    ModeValue = "exact_native_roundtrip" if NativeExact else "exact_carrier_roundtrip"
    PathValue = WriteBytes(Target, Native, Settings.overwrite)
    Requirements = (
        ("referenced CATIA component files",) if DocValue.assembly is not None else ()
    )
    Metadata = {
        "mode": ModeValue,
        "compatibility": Compatibility,
        "vendor_loadable": NativeExact,
        "native_geometry": NativeExact,
        "native_history": NativeExact,
        "native_assembly": NativeExact and DocValue.assembly is not None,
        "native_self_contained": NativeExact and DocValue.assembly is None,
        "native_base_preserved": NativeBaseSaved,
        "native_streams_preserved": NativeBaseSaved,
        "referenced_files_written": 0,
        "container": "V5_CFV2",
        "document_type": DocType,
    }
    return WriteResult(
        PathValue,
        KFormatId,
        len(Native),
        diagnostics=DocValue.diagnostics,
        metadata=MappingProxyType(Metadata),
        requirements=Requirements,
        application_usable=NativeExact,
        vendor_loadable=NativeExact,
    )


# this definition exists because focused behavior needs one stable owner
def WriteNativeBase(
    DocValue: CadDocument,
    Target: Destination,
    Settings: WriteOptions,
    DocType: str,
    CarrierDoc: CadDocument,
    NativeBase: bytes,
) -> WriteResult:
    DataValue = AppendCfvTwoStream(NativeBase, KManifestName, PackManifest(CarrierDoc))
    Restored = Restore(DataValue)
    if Restored != CarrierDoc or Replay(DataValue) != "native-base-neutral-overlay":
        raise CatiaAdapterA("CATIA native-base output failed semantic validation")
    PathValue = WriteBytes(Target, DataValue, Settings.overwrite)
    DiagValue = DiagnosticInfo(
        "catia.native_base_preserved",
        "The native CATIA streams are byte-exact; changed geometry, history, sketches, and assembly semantics remain neutral Kit data rather than native CATIA feature records.",
        Severity.WARNING,
    )
    Requirements = (
        ("referenced CATIA component files",) if DocValue.assembly is not None else ()
    )
    Metadata = NativeBaseMeta(DocValue, DocType, CarrierDoc, NativeBase)
    return WriteResult(
        PathValue,
        KFormatId,
        len(DataValue),
        diagnostics=(*DocValue.diagnostics, DiagValue),
        metadata=MappingProxyType(Metadata),
        requirements=Requirements,
        application_usable=False,
        vendor_loadable=False,
    )


# this definition exists because focused behavior needs one stable owner
def NativeBaseMeta(
    DocValue: CadDocument,
    DocType: str,
    CarrierDoc: CadDocument,
    NativeBase: bytes,
) -> dict[str, object]:
    return {
        "mode": "native_base_with_neutral_edits",
        "compatibility": "native-base-neutral-overlay",
        "vendor_loadable": False,
        "native_geometry": False,
        "native_history": False,
        "native_assembly": False,
        "native_self_contained": False,
        "native_base_vendor_loadable": True,
        "native_base_preserved": True,
        "native_streams_preserved": True,
        "neutral_geometry_embedded": DocValue.brep is not None
        or any(Payload.role == PayloadRole.BREP for Payload in DocValue.brep_payloads),
        "neutral_history_embedded": bool(
            DocValue.parameters
            or DocValue.support_planes
            or DocValue.sketches
            or DocValue.selections
            or DocValue.feature_timeline
            or DocValue.bodies
        ),
        "neutral_assembly_embedded": DocValue.assembly is not None,
        "referenced_files_written": 0,
        "container": "V5_CFV2",
        "document_type": DocType,
        "native_base_sha256": Hashlib.sha256(NativeBase).hexdigest(),
        "manifest_sha256": Hashlib.sha256(
            CarrierDoc.to_json(indent=None).encode("utf-8")
        ).hexdigest(),
    }


# this definition exists because focused behavior needs one stable owner
def WriteCarrier(
    DocValue: CadDocument,
    Target: Destination,
    Settings: WriteOptions,
    DocType: str,
    CarrierDoc: CadDocument,
) -> WriteResult:
    DataValue = Generated(CarrierDoc, DocType)
    if Restore(DataValue) != CarrierDoc:
        raise CatiaAdapterA("generated CATIA manifest failed semantic validation")
    PathValue = WriteBytes(Target, DataValue, Settings.overwrite)
    DiagValue = DiagnosticInfo(
        "catia.native_feature_graph_embedded",
        "Geometry and parametric data are embedded in CFV2 streams; native CATIA feature classes require exact CATIA source preservation.",
        Severity.WARNING,
    )
    Archive = CfvTwoArchive.from_bytes(DataValue)
    Metadata = {
        "mode": "generated_cfv2",
        "compatibility": "kit-neutral-only",
        "vendor_loadable": False,
        "native_geometry": False,
        "native_history": False,
        "native_assembly": False,
        "native_self_contained": False,
        "referenced_files_written": 0,
        "native_feature_graph": False,
        "container": "V5_CFV2",
        "document_type": DocType,
        "outer_stream_count": len(Archive.outer.streams),
        "nested_directory_count": len(Archive.nested),
        "manifest_sha256": Hashlib.sha256(
            CarrierDoc.to_json(indent=None).encode("utf-8")
        ).hexdigest(),
    }
    return WriteResult(
        PathValue,
        KFormatId,
        len(DataValue),
        diagnostics=(*DocValue.diagnostics, DiagValue),
        metadata=MappingProxyType(Metadata),
        application_usable=False,
        vendor_loadable=False,
    )


# this definition exists because focused behavior needs one stable owner
def SourceBytesMut(Source: Source) -> tuple[bytes, str]:
    if isinstance(Source, (bytes, bytearray)):
        return (bytes(Source), "<memory>")
    if isinstance(Source, (str, FilePath)):
        PathValue = FilePath(Source).expanduser().resolve()
        return (PathValue.read_bytes(), str(PathValue))
    Reader = getattr(Source, "read", None)
    if not callable(Reader):
        raise TypeError("CATIA source must be a path, bytes, or binary stream")
    TellMethod = getattr(Source, "tell", None)
    SeekMethod = getattr(Source, "seek", None)
    Position: int | None = None
    if callable(TellMethod) and callable(SeekMethod):
        PositionValue: object = TellMethod()
        if isinstance(PositionValue, int):
            Position = PositionValue
    Value = Reader()
    if Position is not None and callable(SeekMethod):
        SeekMethod(Position)
    if not isinstance(Value, (bytes, bytearray)):
        raise TypeError("CATIA source stream must be binary")
    return (bytes(Value), getattr(Source, "name", "<stream>"))


# this definition exists because focused behavior needs one stable owner
def WriteBytes(
    Target: Destination, DataValue: bytes, Overwrite: bool
) -> FilePath | None:
    if not isinstance(Target, (str, FilePath)):
        Writer = getattr(Target, "write", None)
        if not callable(Writer):
            raise TypeError("CATIA destination must be a path or binary stream")
        Written = Writer(DataValue)
        if Written is not None and Written != len(DataValue):
            raise OSError("short CATIA stream write")
        return None
    PathValue = FilePath(Target).expanduser().resolve()
    if PathValue.exists() and (not Overwrite):
        raise FileExistsError(PathValue)
    PathValue.parent.mkdir(parents=True, exist_ok=True)
    Temporary = PathValue.with_name(PathValue.name + f".{OsModule.getpid()}.tmp")
    try:
        with Temporary.open("xb") as Handle:
            Handle.write(DataValue)
            Handle.flush()
            OsModule.fsync(Handle.fileno())
        OsModule.replace(Temporary, PathValue)
    except BaseException:
        with Suppress(FileNotFoundError):
            Temporary.unlink()
        raise
    return PathValue


# this definition exists because focused behavior needs one stable owner
def Generated(DocValue: CadDocument, DocType: str) -> bytes:
    Manifest = PackManifest(DocValue)
    TypeData = DocType.encode("ascii")
    Nested = BuildCfvTwo(((KManifestName, Manifest), ("KitDocumentType", TypeData)))
    if DocType == ProductDocType:
        Selected = KProductStream
        Declarations = BuildDecl("CATProdCont", "CATFeatCont", Selected, Ordinal=1)
    else:
        Selected = KPartStream
        Declarations = b"".join(
            (
                BuildDecl("CATProdCont", "CATFeatCont", KProductStream, Ordinal=1),
                BuildDecl("CATPrtCont", "CATProdCont", KPartStream, Ordinal=2),
            )
        )
    Summary = SummaryStream(DocType)
    Streams: list[tuple[str, bytes]] = [("Format", TypeData), ("Data", Declarations)]
    if DocType == PartDocType:
        Streams.append((KProductStream, BuildCfvTwo((("KitProduct", b"Part"),))))
    Streams.extend(((Selected, Nested), ("CATSummaryInformation", Summary)))
    return BuildCfvTwo(tuple(Streams))


# this definition exists because focused behavior needs one stable owner
def SummaryStream(DocType: str) -> bytes:
    NameValue = b"CATSummaryInformation"
    Version = b"FirstStreamed<Version>5/<Version><Release>28/<Release><ServicePack>6/<ServicePack><BuildDate>03-10-2020.20.00/<BuildDate><HotFix>0/<HotFix>LastSaveVersion<Version>5/<Version><Release>28/<Release><ServicePack>6/<ServicePack><BuildDate>03-10-2020.20.00/<BuildDate><HotFix>0/<HotFix>MinimalVersionToReadCATIAV5R28"
    return b"".join(
        (
            b"FINJPL  ",
            Struct.pack(">I", 16842755),
            Struct.pack(">I", len(NameValue)),
            b"\x00",
            NameValue,
            b"DASSAULT-SYSTEMES",
            DocType.encode("ascii"),
            Version,
        )
    )


# this definition exists because focused behavior needs one stable owner
def PackManifest(DocValue: CadDocument) -> bytes:
    RawValue = DocValue.to_json(indent=None).encode("utf-8")
    if len(RawValue) > KMaxManifestBytes:
        raise CatiaAdapterA("CATIA Kit manifest exceeds the size limit")
    Compressed = ZlibValue.compress(RawValue, level=9)
    return b"".join(
        (
            KManifestMagic,
            Struct.pack(">Q", len(RawValue)),
            Hashlib.sha256(RawValue).digest(),
            Compressed,
        )
    )


# this definition exists because focused behavior needs one stable owner
def UnpackManifest(DataValue: bytes) -> str:
    Header = len(KManifestMagic) + 8 + 32
    if len(DataValue) < Header or not DataValue.startswith(KManifestMagic):
        raise ValueError("invalid CATIA Kit manifest header")
    Length = Struct.unpack_from(">Q", DataValue, len(KManifestMagic))[0]
    if Length > KMaxManifestBytes:
        raise ValueError("CATIA Kit manifest exceeds the size limit")
    Expected = DataValue[len(KManifestMagic) + 8 : Header]
    Decompressor = ZlibValue.decompressobj()
    RawValue = Decompressor.decompress(DataValue[Header:], Length + 1)
    if len(RawValue) > Length or Decompressor.unconsumed_tail:
        raise ValueError("CATIA Kit manifest exceeds its declared length")
    if not Decompressor.eof:
        raise ValueError("CATIA Kit manifest compression stream is incomplete")
    if Decompressor.unused_data:
        raise ValueError("CATIA Kit manifest has trailing compressed data")
    if len(RawValue) != Length or Hashlib.sha256(RawValue).digest() != Expected:
        raise ValueError("CATIA Kit manifest checksum mismatch")
    return RawValue.decode("utf-8")


# this definition exists because focused behavior needs one stable owner
def ManifestJson(DataValue: bytes) -> str:
    try:
        Source = UnpackManifest(DataValue)
        Depth = 0
        Quoted = False
        Escaped = False
        for Character in Source:
            if Quoted:
                if Escaped:
                    Escaped = False
                elif Character == "\\":
                    Escaped = True
                elif Character == '"':
                    Quoted = False
                continue
            if Character == '"':
                Quoted = True
            elif Character in "[{":
                Depth += 1
                if Depth > KMaxManifestJsonDepth:
                    raise CatiaAdapterA(
                        "invalid Kit document in V5_CFV2: JSON nesting exceeds the depth limit"
                    )
            elif Character in "]}":
                Depth -= 1
        return Source
    except CatiaAdapterA:
        raise
    except RecursionError as ErrorInfo:
        raise CatiaAdapterA(
            "invalid Kit document in V5_CFV2: JSON nesting exceeds the depth limit"
        ) from ErrorInfo
    except (TypeError, ValueError, ZlibValue.error) as ErrorInfo:
        raise CatiaAdapterA(
            f"invalid Kit document in V5_CFV2: {ErrorInfo}"
        ) from ErrorInfo


# this definition exists because focused behavior needs one stable owner
def ManifestDoc(DataValue: bytes) -> CadDoc:
    try:
        return CadDoc.from_json(ManifestJson(DataValue))
    except CatiaAdapterA:
        raise
    except RecursionError as ErrorInfo:
        raise CatiaAdapterA(
            "invalid Kit document in V5_CFV2: JSON nesting exceeds the depth limit"
        ) from ErrorInfo
    except (TypeError, ValueError, ZlibValue.error) as ErrorInfo:
        raise CatiaAdapterA(
            f"invalid Kit document in V5_CFV2: {ErrorInfo}"
        ) from ErrorInfo


# this definition exists because focused behavior needs one stable owner
def ManifestBytes(Archive: Cfv2Archive) -> bytes | None:
    Matches = tuple(
        (
            (Folder, Stream)
            for Folder in (Archive.outer, *Archive.nested)
            for Stream in Folder.streams
            if Stream.name == KManifestName
        )
    )
    if not Matches:
        return None
    if len(Matches) != 1:
        raise CfvTwoFormatError("multiple CATIA Kit manifests")
    Folder, Stream = Matches[0]
    return Archive.stream_bytes(Stream, Folder)


# this definition exists because focused behavior needs one stable owner
def Restore(DataValue: bytes) -> CadDoc:
    Archive = CfvTwoArchive.from_bytes(DataValue)
    Manifest = ManifestBytes(Archive)
    if Manifest is None:
        raise CatiaAdapterA("generated V5_CFV2 has no Kit manifest")
    return ManifestDoc(Manifest)


# this definition exists because focused behavior needs one stable owner
def CarrierManifest(DocValue: CadDocument) -> CadDoc:
    CurrentEnvelope = DocValue.source.format_id == KFormatId and isinstance(
        DocValue.source.attributes.get("embedded_source_format_id"), str
    )
    if CurrentEnvelope:
        return Replace(
            DocValue,
            brep_payloads=tuple(
                (
                    Payload
                    for Payload in DocValue.brep_payloads
                    if not IsCatiaEnvelope(Payload)
                )
            ),
        )
    Documents = tuple(
        (Payload for Payload in DocValue.brep_payloads if IsNativeDocA(Payload))
    )
    Bindings = tuple(
        (Payload for Payload in DocValue.brep_payloads if IsNativeDoc(Payload))
    )
    if len(Documents) != 1 or len(Bindings) != 1:
        return DocValue
    NativeDoc = Documents[0]
    NativeBinding = Bindings[0]
    if not IsBindingMatch(NativeBinding, NativeDoc):
        return DocValue
    Token = NativeDoc.sha256
    Occupied = {
        Payload.id
        for Payload in DocValue.brep_payloads
        if Payload is not NativeDoc and Payload is not NativeBinding
    }
    Sequence = 1
    while {f"{KSavedDocPrefix}{Token}", f"{KSavedBindingPrefix}{Token}"} & Occupied:
        Sequence += 1
        Token = f"{NativeDoc.sha256}:{Sequence}"
    ReplayDigest = (
        SavedReplay(DocValue, NativeDoc, NativeBinding)
        if IsNativeChoice(DocValue, NativeDoc)
        else None
    )
    Attributes = dict(NativeDoc.attributes)
    if ReplayDigest is not None:
        Attributes[KReplaySemanticAttr] = ReplayDigest
    SavedDoc = Replace(
        NativeDoc, id=f"{KSavedDocPrefix}{Token}", attributes=FrozenMapping(Attributes)
    )
    SavedBinding = Replace(NativeBinding, id=f"{KSavedBindingPrefix}{Token}")
    return Replace(
        DocValue,
        brep_payloads=tuple(
            (
                (
                    SavedDoc
                    if Payload is NativeDoc
                    else SavedBinding if Payload is NativeBinding else Payload
                )
                for Payload in DocValue.brep_payloads
            )
        ),
    )


# this definition exists because focused behavior needs one stable owner
def EmbeddedDoc(
    Archive: Cfv2Archive,
    DataValue: bytes,
    Label: str,
    Manifest: bytes,
    Settings: ReadOptions,
) -> CadDoc:
    Embedded = ManifestDoc(Manifest)
    Configurations = Selected(Embedded.configurations, Settings.configuration)
    DocType = DetectDocType(Archive, Label)
    ExpectedType = ProductDocType if Embedded.assembly is not None else PartDocType
    if DocType != ExpectedType:
        raise CatiaAdapterA(f"{ExpectedType} content cannot be read as {DocType}")
    Original = Embedded.source
    MetaValue = dict(Embedded.metadata)
    MetaValue.update(
        {
            "catia.document_type": DocType,
            "catia.outer_directory_offset": Archive.outer.offset,
            "catia.outer_directory_length": Archive.outer.length,
            "catia.outer_streams": tuple(
                (
                    (Stream.name, Stream.logical_length)
                    for Stream in Archive.outer.streams
                )
            ),
            "catia.nested_directory_count": len(Archive.nested),
            "catia.container_classes": tuple(
                (
                    (
                        Value.ordinal,
                        Value.class_name,
                        Value.base_class,
                        Value.stream_name,
                    )
                    for Value in Archive.declarations()
                )
            ),
            "catia.embedded_source_format_id": Original.format_id,
            "catia.embedded_source_path": Original.path,
            "catia.embedded_source_sha256": Original.sha256,
            "catia.embedded_source_container_version": Original.container_version,
            "catia.embedded_source_application_version": Original.application_version,
            "catia.embedded_source_attributes": dict(Original.attributes),
            "catia.container_compatibility": Replay(DataValue),
        }
    )
    Filtered = FilterDoc(
        Replace(
            Embedded,
            configurations=Configurations,
            brep_payloads=tuple(
                (
                    Payload
                    for Payload in Embedded.brep_payloads
                    if not IsCatiaEnvelope(Payload)
                )
            ),
        ),
        include_brep=Settings.include_brep,
        include_tessellation=Settings.include_tessellation,
        keep_payload_records=True,
    )
    Retained = Filtered.brep_payloads
    Physical = NativeDocB(
        Archive, DataValue, DocType, IncludeData=Settings.include_brep
    )
    Binding = NativeDoc(DataValue, IncludeData=Settings.include_brep)
    Payloads = (*Retained, Binding, Physical)
    DocValue = Replace(
        Filtered,
        source=CadSource(
            KFormatId,
            Label,
            Hashlib.sha256(DataValue).hexdigest(),
            container_version="V5_CFV2",
            application_version=AppVersion(DataValue),
            attributes=FrozenMapping(
                {
                    "embedded_source_format_id": Original.format_id,
                    "embedded_source_sha256": Original.sha256,
                }
            ),
        ),
        brep_payloads=tuple(Payloads),
        brep=(
            Filtered.brep
            if Filtered.brep is not None
            else TypedBrep(Retained, Filtered.bodies)
        ),
        metadata=WithWrapperMeta(MetaValue, KWrapperMetaKeys),
    )
    Digest = SemanticDigest(DocValue)
    DocValue = Replace(
        DocValue,
        metadata=FrozenMapping({**DocValue.metadata, "catia.roundtrip_sha256": Digest}),
    )
    if Settings.strict:
        DocValue.assert_valid()
    return DocValue


# this definition exists because focused behavior needs one stable owner
def Selected(
    Configurations: tuple[Configuration, ...], Selected: str | None
) -> tuple[Config, ...]:
    if Selected is None:
        return Configurations
    Matches = {
        ConfigValue.id
        for ConfigValue in Configurations
        if Selected in {ConfigValue.id, ConfigValue.name}
    }
    if not Matches:
        raise CatiaAdapterA(f"configuration {Selected!r} is unavailable")
    return tuple(
        (
            Replace(ConfigValue, active=ConfigValue.id in Matches)
            for ConfigValue in Configurations
        )
    )


# this definition exists because focused behavior needs one stable owner
def TypedBrep(
    Payloads: tuple[BrepPayload, ...], Bodies: tuple[Body, ...]
) -> BrepModel | None:
    Eligible = tuple(
        (
            Payload
            for Payload in Payloads
            if Payload.role == PayloadRole.BREP
            and Payload.format_id.casefold().strip() in KNeutralBrepFormatIds
        )
    )
    if any((IsDeltaPayload(Payload) for Payload in Eligible)):
        return None
    BodyIds = frozenset((BodyValue.id for BodyValue in Bodies))
    Models = tuple(
        (
            Model
            for Index, Payload in enumerate(Eligible)
            if (Model := DecodeTypedBrep(Payload, Index, BodyIds)) is not None
            and (not Model.validate(BodyIds))
        )
    )
    return Models[0] if len(Models) == 1 else None


# this definition exists because focused behavior needs one stable owner
def DecodeTypedBrep(
    Payload: BrepPayload, Index: int, BodyIds: frozenset[str]
) -> BrepModel | None:
    if Payload.data is None:
        return None
    FormatId = Payload.format_id.casefold().strip()
    if FormatId in KParasolidFormatIds:
        return DecodeParasolidBrep(Payload.data)
    BodyId = Payload.attributes.get("body_id")
    DesignBodyId = BodyId if isinstance(BodyId, str) and BodyId in BodyIds else ""
    if not DesignBodyId and len(BodyIds) == 1:
        DesignBodyId = next(iter(BodyIds))
    return DecodeOpencascadeBrep(
        Payload.data,
        id_prefix=f"catia-occ:{Index}",
        design_body_id=DesignBodyId,
        attributes={
            "format_id": Payload.format_id,
            "payload_id": Payload.id,
            "source_stream": Payload.source_stream,
        },
    )


# this definition exists because focused behavior needs one stable owner
def IsDeltaPayload(Payload: BrepPayload) -> bool:
    Description = Payload.attributes.get("description")
    TextValue = " ".join(
        (
            Value
            for Value in (
                Payload.kind,
                Payload.schema,
                Payload.source_stream,
                Description if isinstance(Description, str) else "",
            )
            if Value
        )
    ).casefold()
    return "delta" in TextValue or (
        Payload.data is not None and b"delta" in Payload.data[:8192].lower()
    )


# this definition exists because focused behavior needs one stable owner
def DetectDocType(Archive: Cfv2Archive, Label: str) -> str:
    Detected = DeclaredDocType(Archive)
    FormatType = FormatDocType(Archive)
    if Detected and FormatType and Detected != FormatType:
        raise CatiaAdapterA("CATIA container has contradictory document roots")
    Detected = Detected or FormatType or ProductFallback(Archive)
    Suffix = FilePath(Label).suffix.casefold()
    if Detected:
        Expected = SuffixByDocType[Detected]
        if Suffix in DocTypeBySuffix and Suffix != Expected:
            raise CatiaAdapterA(f"{Detected} content requires a .{Detected} source")
        return Detected
    if Suffix in DocTypeBySuffix:
        return DocTypeBySuffix[Suffix]
    raise CatiaAdapterA("cannot distinguish CATPart from CATProduct")


# this definition exists because focused behavior needs one stable owner
def DeclaredDocType(Archive: Cfv2Archive) -> str:
    Declarations = Archive.declarations()
    PartDeclarations = tuple(
        (Value for Value in Declarations if Value.class_name == "CATPrtCont")
    )
    ProductDeclarations = tuple(
        (Value for Value in Declarations if Value.class_name == "CATProdCont")
    )
    if len(PartDeclarations) > 1 or len(ProductDeclarations) > 1:
        raise CatiaAdapterA("CATIA container has contradictory document roots")
    if PartDeclarations:
        if (
            ProductDeclarations
            and PartDeclarations[0].base_class != ProductDeclarations[0].class_name
        ):
            raise CatiaAdapterA("CATIA container has contradictory document roots")
        PartRole = DeclaredRole(Archive, PartDeclarations[0])
        ProductRole = (
            DeclaredRole(Archive, ProductDeclarations[0])
            if ProductDeclarations
            else PayloadRole.AUXILIARY
        )
        if PartRole == PayloadRole.ASSEMBLY_STRUCTURE or ProductRole in {
            PayloadRole.BREP,
            PayloadRole.FEATURE_HISTORY,
            PayloadRole.TESSELLATION,
        }:
            raise CatiaAdapterA("CATIA container has contradictory document roots")
        return PartDocType
    if ProductDeclarations:
        if DeclaredRole(Archive, ProductDeclarations[0]) == PayloadRole.FEATURE_HISTORY:
            raise CatiaAdapterA("CATIA container has contradictory document roots")
        return ProductDocType
    return ""


# this definition exists because focused behavior needs one stable owner
def FormatDocType(Archive: Cfv2Archive) -> str:
    FormatStream = Archive.named_stream("Format")
    if FormatStream is None:
        return ""
    PartMarker = PartDocType.encode("ascii") in FormatStream
    ProductMarker = ProductDocType.encode("ascii") in FormatStream
    if PartMarker and ProductMarker:
        raise CatiaAdapterA("CATIA Format stream has conflicting markers")
    if PartMarker:
        return PartDocType
    return ProductDocType if ProductMarker else ""


# this definition exists because focused behavior needs one stable owner
def ProductFallback(Archive: Cfv2Archive) -> str:
    try:
        DecodeProductTable(Archive)
    except CfvTwoFormatError:
        return ""
    return ProductDocType


# this definition exists because focused behavior needs one stable owner
def DeclaredRole(Archive: Cfv2Archive, DeclValue: Cfv2Declaration) -> PayloadRole:
    Stream = Archive.outer.stream(DeclValue.stream_name)
    if Stream is None:
        return PayloadRole.AUXILIARY
    Payload = Archive.stream_bytes(Stream, Archive.outer)
    return NativeContaineA(DeclValue, Payload)[3]


# this definition exists because focused behavior needs one stable owner
def TargetType(DocValue: CadDocument, Target: Destination) -> str:
    Suffix = (
        FilePath(Target).suffix.casefold()
        if isinstance(Target, (str, FilePath))
        else KProductSuffix if DocValue.assembly is not None else KPartSuffix
    )
    if Suffix not in DocTypeBySuffix:
        raise ValueError("CATIA destination must end in .CATPart or .CATProduct")
    if DocValue.assembly is None and Suffix != KPartSuffix:
        raise ValueError("part documents require a .CATPart destination")
    if DocValue.assembly is not None and Suffix != KProductSuffix:
        raise ValueError("assembly documents require a .CATProduct destination")
    return DocTypeBySuffix[Suffix]


# this definition exists because focused behavior needs one stable owner
def ContainerMeta(Archive: Cfv2Archive) -> dict[str, object]:
    Declarations: list[dict[str, object]] = []
    for DeclValue in Archive.declarations():
        Stream = Archive.outer.stream(DeclValue.stream_name)
        if Stream is None:
            continue
        Payload = Archive.stream_bytes(Stream, Archive.outer)
        Declarations.append(
            {
                "ordinal": DeclValue.ordinal,
                "class_name": DeclValue.class_name,
                "base_class": DeclValue.base_class,
                "stream_name": DeclValue.stream_name,
                "descriptor_offset": Stream.descriptor_offset,
                "logical_length": Stream.logical_length,
                "extent_count": len(Stream.extents),
                "sha256": Hashlib.sha256(Payload).hexdigest(),
            }
        )
    OuterStreams = tuple(
        (
            {
                "index": Index,
                "name": Stream.name,
                "logical_length": Stream.logical_length,
                "descriptor_offset": Stream.descriptor_offset,
                "extents": tuple(
                    (
                        {
                            "physical_offset": Archive.outer.physical_base
                            + Extent.physical_offset,
                            "physical_length": Extent.physical_length,
                            "logical_offset": Extent.logical_offset,
                            "flags": Extent.flags,
                        }
                        for Extent in Stream.extents
                    )
                ),
            }
            for Index, Stream in enumerate(Archive.outer.streams)
        )
    )
    NestedDirectories = tuple(
        (
            {
                "physical_base": Folder.physical_base,
                "offset": Folder.offset,
                "length": Folder.length,
                "streams": tuple(
                    ((Stream.name, Stream.logical_length) for Stream in Folder.streams)
                ),
            }
            for Folder in Archive.nested
        )
    )
    return {
        "catia.container_declarations": tuple(Declarations),
        "catia.outer_stream_records": OuterStreams,
        "catia.nested_directories": NestedDirectories,
    }


# this definition exists because focused behavior needs one stable owner
def Replay(DataValue: bytes) -> str:
    Archive = CfvTwoArchive.from_bytes(DataValue)
    Manifest = ManifestBytes(Archive)
    if Manifest is None:
        return "native-exact"
    DocValue = ManifestDoc(Manifest)
    if IsNativeBase(Archive, DocValue):
        return "native-base-neutral-overlay"
    return "kit-neutral-only"


# this definition exists because focused behavior needs one stable owner
def IsNativeBase(Archive: Cfv2Archive, DocValue: CadDocument) -> bool:
    ManifestMatches = tuple(
        (
            (Folder, Stream)
            for Folder in (Archive.outer, *Archive.nested)
            for Stream in Folder.streams
            if Stream.name == KManifestName
        )
    )
    if len(ManifestMatches) != 1 or ManifestMatches[0][0] is not Archive.outer:
        return False
    Matches = 0
    for Payload in DocValue.brep_payloads:
        if not IsSavedDocA(Payload) or Payload.data is None:
            continue
        if Hashlib.sha256(Payload.data).hexdigest() != Payload.sha256:
            continue
        Binding = MatchingDoc(DocValue, Payload)
        if Binding is None:
            continue
        try:
            BaseValue = CfvTwoArchive.from_bytes(Payload.data)
            if ManifestBytes(BaseValue) is not None:
                continue
            if (
                DetectDocType(BaseValue, f"candidate.{Payload.schema}")
                != Payload.schema
            ):
                continue
            if IsOverlayNative(Archive, BaseValue, ManifestMatches[0][1]):
                Matches += 1
        except (CatiaAdapterA, CfvTwoFormatError, TypeError, ValueError):
            continue
    return Matches == 1


# this definition exists because focused behavior needs one stable owner
def IsOverlayNative(
    Overlay: Cfv2Archive, BaseValue: Cfv2Archive, ManifestStream: Cfv2Stream
) -> bool:
    Manifest = Overlay.stream_bytes(ManifestStream, Overlay.outer)
    if Overlay.outer.offset != BaseValue.outer.offset + len(Manifest):
        return False
    if (
        Overlay.data[16 : BaseValue.outer.offset]
        != BaseValue.data[16 : BaseValue.outer.offset]
    ):
        return False
    if Overlay.data[BaseValue.outer.offset : Overlay.outer.offset] != Manifest:
        return False
    BaseFolder = BaseValue.data[
        BaseValue.outer.offset : BaseValue.outer.offset + BaseValue.outer.length
    ]
    OverlayFolder = Overlay.data[
        Overlay.outer.offset : Overlay.outer.offset + Overlay.outer.length
    ]
    DescriptorLength = Overlay.outer.length - BaseValue.outer.length
    DescriptorOffset = ManifestStream.descriptor_offset - Overlay.outer.offset
    if (
        DescriptorLength <= 0
        or DescriptorOffset < 0
        or DescriptorOffset + DescriptorLength > len(OverlayFolder)
    ):
        return False
    RetainedFolder = b"".join(
        (
            OverlayFolder[:DescriptorOffset],
            OverlayFolder[DescriptorOffset + DescriptorLength :],
        )
    )
    if RetainedFolder != BaseFolder:
        return False
    BaseStreams = tuple(
        (
            (Stream.name, BaseValue.stream_bytes(Stream, BaseValue.outer))
            for Stream in BaseValue.outer.streams
        )
    )
    OverlayStreams = tuple(
        (
            (Stream.name, Overlay.stream_bytes(Stream, Overlay.outer))
            for Stream in Overlay.outer.streams
            if Stream.name != KManifestName
        )
    )
    return OverlayStreams == BaseStreams


# this definition exists because focused behavior needs one stable owner
def NativePartData(Archive: Cfv2Archive, DocType: str) -> tuple[
    dict[str, object],
    tuple[SupportPlane, ...],
    tuple[FeatureStep, ...],
    tuple[BodyRecord, ...],
    tuple[DiagnosticInfo, ...],
]:
    if DocType != PartDocType:
        return ({}, (), (), (), ())
    PartDecl, PartStream, PartGraph = DeclaredOsmx(Archive, PayloadRole.FEATURE_HISTORY)
    ProductDecl, ProductStream, ProductGraph = DeclaredOsmx(
        Archive, PayloadRole.ASSEMBLY_STRUCTURE
    )
    ProductSymbol = ProductGraph.first_after("ASMPRODUCT")
    PartSymbol = PartGraph.first_after("MechanicalPart")
    BodySymbol = PartGraph.first_after("MMAlias")
    ProductName = ProductSymbol.value if ProductSymbol is not None else ""
    InternalPartName = PartSymbol.value if PartSymbol is not None else ""
    BodyName = (
        BodySymbol.value
        if BodySymbol is not None and BodySymbol.value
        else ProductName or InternalPartName or "PartBody"
    )
    NativeSymbols = tuple(
        dict.fromkeys((Symbol.value for Symbol in PartGraph.symbols if Symbol.value))
    )
    Planes = PartPlanes(Archive.outer, PartStream, PartGraph)
    FeatureId = "catia:feature:graph"
    Feature = FeatureStep(
        id=FeatureId,
        name="CATIA native feature graph",
        kind=FeatureKind.NATIVE,
        order=0,
        definition=NativeFeatureDefinition(
            format_id="catia.v5.osmx",
            type_id=PartDecl.class_name,
            object_data=FrozenMapping(
                {
                    "native_payload_id": "catia:native-feature-graph",
                    "symbols": PartGraph.values,
                    "version": PartGraph.version,
                    "symbol_table_offset": PartGraph.symbol_table_offset,
                    "symbol_data_offset": PartGraph.symbol_data_offset,
                }
            ),
        ),
        provenance=StreamSource(
            Archive.outer,
            PartStream,
            f"{PartDecl.class_name}:{PartDecl.ordinal}",
            "native-feature-graph",
        ),
        attributes=FrozenMapping(
            {
                "native_symbols": NativeSymbols,
                "native_payload_id": "catia:native-feature-graph",
                "symbol_count": len(PartGraph.symbols),
            }
        ),
    )
    BodyValue = BodyRecord(
        id="catia:body:1",
        name=BodyName,
        final_feature_id=FeatureId,
        provenance=(
            SymbolSource(Archive.outer, PartStream, BodySymbol, "body-alias")
            if BodySymbol is not None
            else Feature.provenance
        ),
        attributes=FrozenMapping(
            {"native_class": "MMAlias", "native_part_name": InternalPartName}
        ),
    )
    MetaValue: dict[str, object] = {
        "catia.product_name": ProductName,
        "catia.internal_part_name": InternalPartName,
        "catia.body_name": BodyName,
        "catia.native_symbols": NativeSymbols,
        "catia.product_symbols": ProductGraph.values,
        "catia.part_symbols": PartGraph.values,
        "catia.osmx_streams": (
            OsmxMeta(ProductStream, ProductGraph, ProductDecl.class_name),
            OsmxMeta(PartStream, PartGraph, PartDecl.class_name),
        ),
    }
    DiagValue = DiagnosticInfo(
        "catia.part.native_graph_retained",
        "The exact native feature graph, symbol table, bodies, and reference planes are retained; proprietary object records remain native.",
        Severity.INFO,
        entity_id=FeatureId,
        provenance=Feature.provenance,
        attributes=FrozenMapping(
            {"native_symbols": NativeSymbols, "symbol_count": len(PartGraph.symbols)}
        ),
    )
    return (MetaValue, Planes, (Feature,), (BodyValue,), (DiagValue,))


# this definition exists because focused behavior needs one stable owner
def DeclaredOsmx(
    Archive: Cfv2Archive, RoleValue: PayloadRole
) -> tuple[CfvTwoDecl, CfvTwoStream, OsmxArchive]:
    Matches: list[tuple[CfvTwoDecl, CfvTwoStream, OsmxArchive]] = []
    for DeclValue in Archive.declarations():
        Stream = Archive.outer.stream(DeclValue.stream_name)
        if Stream is None:
            continue
        DataValue = Archive.stream_bytes(Stream, Archive.outer)
        if OsmxPayloadRole(DataValue) != RoleValue:
            continue
        Matches.append((DeclValue, Stream, OsmxArchive.from_bytes(DataValue)))
    if len(Matches) != 1:
        raise CatiaAdapterA(
            f"CATIA container requires one {RoleValue.value} OSMX declaration"
        )
    return Matches[0]


# this definition exists because focused behavior needs one stable owner
def OsmxMeta(
    Stream: Cfv2Stream, Graph: OsmxArchive, ClassName: str
) -> dict[str, object]:
    return {
        "class_name": ClassName,
        "stream_name": Stream.name,
        "logical_length": Stream.logical_length,
        "version": Graph.version,
        "symbol_table_offset": Graph.symbol_table_offset,
        "symbol_data_offset": Graph.symbol_data_offset,
        "symbol_count": len(Graph.symbols),
        "sha256": Hashlib.sha256(Graph.data).hexdigest(),
    }


# this definition exists because focused behavior needs one stable owner
def PartPlanes(
    Folder: Cfv2Directory, Stream: Cfv2Stream, Graph: OsmxArchive
) -> tuple[SupportPlane, ...]:
    Transforms = (
        Transform(),
        Transform(
            x_axis=VectorThree(0.0, 1.0, 0.0),
            y_axis=VectorThree(0.0, 0.0, 1.0),
            z_axis=VectorThree(1.0, 0.0, 0.0),
        ),
        Transform(
            x_axis=VectorThree(0.0, 0.0, 1.0),
            y_axis=VectorThree(1.0, 0.0, 0.0),
            z_axis=VectorThree(0.0, 1.0, 0.0),
        ),
    )
    Values = Graph.values
    try:
        PlaneTypeIndex = Values.index("GSMPlane")
        AlgorithmIdIndex = Values.index("_PartAlgoConfigUUID")
    except ValueError:
        return ()
    Indices = (PlaneTypeIndex + 1, AlgorithmIdIndex - 2, AlgorithmIdIndex - 1)
    if any((Index < 0 or Index >= len(Graph.symbols) for Index in Indices)):
        return ()
    Symbols = tuple((Graph.symbols[Index] for Index in Indices))
    if len({Symbol.value for Symbol in Symbols if Symbol.value}) != len(Transforms):
        return ()
    return tuple(
        (
            SupportPlane(
                id=f"catia:plane:{Index}",
                name=Symbol.value,
                transform=PlaneTransform,
                provenance=SymbolSource(Folder, Stream, Symbol, "reference-plane"),
                attributes=FrozenMapping(
                    {"native_class": "GSMPlane", "principal_index": Index - 1}
                ),
            )
            for Index, (Symbol, PlaneTransform) in enumerate(
                zip(Symbols, Transforms, strict=True), start=1
            )
        )
    )


# this definition exists because focused behavior needs one stable owner
def SymbolSource(
    Folder: Cfv2Directory, Stream: Cfv2Stream, Symbol: OsmxSymbol, RecordKind: str
) -> Provenance:
    return Provenance(
        adapter=KFormatId,
        native_id=f"{Stream.name}:{Symbol.offset}",
        spans=LogicalSpans(
            Folder, Stream, Symbol.offset, len(Symbol.value), RecordKind
        ),
    )


# this definition exists because focused behavior needs one stable owner
def StreamSource(
    Folder: Cfv2Directory, Stream: Cfv2Stream, NativeId: str, RecordKind: str
) -> Provenance:
    return Provenance(
        adapter=KFormatId,
        native_id=NativeId,
        spans=tuple(
            (
                ProvenanceSpan(
                    Stream.name,
                    Folder.physical_base + Extent.physical_offset,
                    Extent.physical_length,
                    RecordKind,
                )
                for Extent in Stream.extents
            )
        ),
    )


# this definition exists because focused behavior needs one stable owner
def LogicalSpans(
    Folder: Cfv2Directory,
    Stream: Cfv2Stream,
    LogicalOffset: int,
    Length: int,
    RecordKind: str,
) -> tuple[ProvenanceSpan, ...]:
    EndValue = LogicalOffset + Length
    Spans: list[ProvenanceSpan] = []
    for Extent in Stream.extents:
        ExtentStart = Extent.logical_offset
        ExtentEnd = ExtentStart + Extent.physical_length
        OverlapStart = max(LogicalOffset, ExtentStart)
        OverlapEnd = min(EndValue, ExtentEnd)
        if OverlapStart >= OverlapEnd:
            continue
        Spans.append(
            ProvenanceSpan(
                Stream.name,
                Folder.physical_base
                + Extent.physical_offset
                + OverlapStart
                - ExtentStart,
                OverlapEnd - OverlapStart,
                RecordKind,
            )
        )
    if sum((SpanValue.length for SpanValue in Spans)) != Length:
        raise CatiaAdapterA("CATIA logical provenance span is incomplete")
    return tuple(Spans)


# this definition exists because focused behavior needs one stable owner
def NativePayloads(
    Archive: Cfv2Archive, DataValue: bytes, DocType: str, Settings: ReadOptions
) -> tuple[BrepPayload, ...]:
    Payloads = [
        NativeDocB(Archive, DataValue, DocType, IncludeData=Settings.include_brep),
        NativeDoc(DataValue, IncludeData=Settings.include_brep),
    ]
    PayloadIds: set[str] = {Payload.id for Payload in Payloads}
    for DeclValue in Archive.declarations():
        Stream = Archive.outer.stream(DeclValue.stream_name)
        if Stream is None:
            continue
        Payload = Archive.stream_bytes(Stream, Archive.outer)
        PayloadId, FormatId, KindValue, RoleValue, FileExtension = NativeContaineA(
            DeclValue, Payload
        )
        if PayloadId in PayloadIds:
            PayloadId = f"{PayloadId}:{DeclValue.ordinal}"
        PayloadIds.add(PayloadId)
        DataIncluded = CanIncludeData(RoleValue, Settings)
        Payloads.append(
            BrepPayload(
                PayloadId,
                FormatId,
                KindValue,
                DeclValue.class_name,
                Hashlib.sha256(Payload).hexdigest(),
                Payload if DataIncluded else None,
                source_stream=Stream.name,
                provenance=StreamSource(
                    Archive.outer,
                    Stream,
                    f"{DeclValue.class_name}:{DeclValue.ordinal}",
                    KindValue,
                ),
                attributes=FrozenMapping(
                    {
                        "declaration_ordinal": DeclValue.ordinal,
                        "base_class": DeclValue.base_class,
                        "logical_length": Stream.logical_length,
                        "extent_count": len(Stream.extents),
                    }
                ),
                role=RoleValue,
                file_extension=FileExtension,
            )
        )
    return tuple(Payloads)


# this definition exists because focused behavior needs one stable owner
def CanIncludeData(RoleValue: PayloadRole, Settings: ReadOptions) -> bool:
    if RoleValue == PayloadRole.BREP:
        return Settings.include_brep
    if RoleValue == PayloadRole.TESSELLATION:
        return Settings.include_tessellation
    return True


# this definition exists because focused behavior needs one stable owner
def IsCatiaEnvelope(Payload: BrepPayload) -> bool:
    return IsNativeDocA(Payload) or IsNativeDoc(Payload)


# this definition exists because focused behavior needs one stable owner
def IsCatiaDocA(Payload: BrepPayload) -> bool:
    return (
        Payload.kind == "native_document"
        and Payload.role == PayloadRole.DOCUMENT
        and (Payload.format_id == "catia.v5.cfv2")
    )


# this definition exists because focused behavior needs one stable owner
def IsNativeDocA(Payload: BrepPayload) -> bool:
    return Payload.id == KNativeDocId and IsCatiaDocA(Payload)


# this definition exists because focused behavior needs one stable owner
def IsSavedDocA(Payload: BrepPayload) -> bool:
    return Payload.id.startswith(KSavedDocPrefix) and IsCatiaDocA(Payload)


# this definition exists because focused behavior needs one stable owner
def IsCatiaDoc(Payload: BrepPayload) -> bool:
    return (
        Payload.format_id == "catia.v5.sha256"
        and Payload.kind == "native_document_binding"
        and (Payload.schema == "sha256")
        and (
            Payload.role == PayloadRole.DOCUMENT
            or Payload.role == PayloadRole.VERIFICATION
        )
    )


# this definition exists because focused behavior needs one stable owner
def IsNativeDoc(Payload: BrepPayload) -> bool:
    return Payload.id == KNativeDocBindingId and IsCatiaDoc(Payload)


# this definition exists because focused behavior needs one stable owner
def IsSavedDoc(Payload: BrepPayload) -> bool:
    return Payload.id.startswith(KSavedBindingPrefix) and IsCatiaDoc(Payload)


# this definition exists because focused behavior needs one stable owner
def NativeContaineA(
    DeclValue: Cfv2Declaration, Payload: bytes
) -> tuple[str, str, str, PayloadRole, str]:
    OsmxRole = OsmxPayloadRole(Payload)
    if OsmxRole == PayloadRole.FEATURE_HISTORY:
        return (
            "catia:native-feature-graph",
            "catia.v5.osmx",
            "native_feature_graph",
            OsmxRole,
            ".osmx",
        )
    if OsmxRole == PayloadRole.ASSEMBLY_STRUCTURE:
        return (
            "catia:native-product-graph",
            "catia.v5.osmx",
            "native_product_graph",
            OsmxRole,
            ".osmx",
        )
    if IsCgmPayload(Payload):
        return (
            "catia:native-cgm",
            "catia.cgm",
            "native_brep",
            PayloadRole.BREP,
            ".cgm",
        )
    if IsMfbrpPayload(Payload):
        return (
            "catia:native-brep-topology",
            "catia.v5.mfbrp",
            "brep_topology",
            PayloadRole.BREP,
            ".mfbrp",
        )
    if IsBrepMode(Payload):
        return (
            "catia:native-brep-mode",
            "catia.v5.brep-mode",
            "brep_mode",
            PayloadRole.BREP,
            ".bin",
        )
    if IsCgrPayload(Payload):
        return (
            "catia:native-tessellation",
            "catia.cgr",
            "native_tessellation",
            PayloadRole.TESSELLATION,
            ".cgr",
        )
    return (
        f"catia:native-container:{DeclValue.ordinal}",
        "catia.v5.cfv2.stream",
        "native_container",
        PayloadRole.AUXILIARY,
        ".bin",
    )


# this definition exists because focused behavior needs one stable owner
def OsmxPayloadRole(Payload: bytes) -> PayloadRole:
    if not Payload.startswith(b"OSMX"):
        return PayloadRole.AUXILIARY
    try:
        Values = set(OsmxArchive.from_bytes(Payload).values)
    except (OsmxFormatError, TypeError, ValueError):
        return PayloadRole.AUXILIARY
    PartValue = "MechanicalPart" in Values
    Product = "ASMPRODUCT" in Values
    if PartValue == Product:
        return PayloadRole.AUXILIARY
    return PayloadRole.FEATURE_HISTORY if PartValue else PayloadRole.ASSEMBLY_STRUCTURE


# this definition exists because focused behavior needs one stable owner
def IsCgmPayload(Payload: bytes) -> bool:
    if len(Payload) < 17 or Payload[0] != 1:
        return False
    if Struct.unpack_from("<I", Payload, 1)[0] != len(Payload) - 5:
        return False
    Cursor = 5
    Labels: list[bytes] = []
    for _ in range(2):
        if Cursor + 4 > len(Payload):
            return False
        Length = Struct.unpack_from("<I", Payload, Cursor)[0]
        Cursor += 4
        if not Length or Cursor + Length > len(Payload):
            return False
        Labels.append(Payload[Cursor : Cursor + Length])
        Cursor += Length
    return Labels[0] == Labels[1]


# this definition exists because focused behavior needs one stable owner
def IsMfbrpPayload(Payload: bytes) -> bool:
    return Payload.startswith(
        b"\x0f\x00\x01\x00\x00\x00\x00\x04\x00\x00\x00\x02\x00\x05\x00\x00\x008\x00\x00"
    )


# this definition exists because focused behavior needs one stable owner
def IsBrepMode(Payload: bytes) -> bool:
    return Payload.startswith(
        b"\x04\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00"
    )


# this definition exists because focused behavior needs one stable owner
def IsCgrPayload(Payload: bytes) -> bool:
    if not Payload.startswith(b"V5_CFV2\x00"):
        return False
    try:
        Archive = CfvTwoArchive.from_bytes(Payload)
    except (CfvTwoFormatError, TypeError, ValueError):
        return False
    Names = {Stream.name for Stream in Archive.outer.streams}
    return {"SceneGraph", "SurfacicReps"} <= Names


# this definition exists because focused behavior needs one stable owner
def NativeDocB(
    Archive: Cfv2Archive, DataValue: bytes, DocType: str, IncludeData: bool
) -> BrepPayload:
    return BrepPayload(
        KNativeDocId,
        "catia.v5.cfv2",
        "native_document",
        DocType,
        Hashlib.sha256(DataValue).hexdigest(),
        DataValue if IncludeData else None,
        source_stream="V5_CFV2",
        provenance=Provenance(
            adapter=KFormatId,
            native_id=DocType,
            spans=(ProvenanceSpan("V5_CFV2", 0, len(DataValue), "native-document"),),
        ),
        attributes=FrozenMapping(
            {
                "outer_directory_offset": Archive.outer.offset,
                "outer_directory_length": Archive.outer.length,
            }
        ),
        role=PayloadRole.DOCUMENT,
        file_extension=KProductSuffix if DocType == ProductDocType else KPartSuffix,
    )


# this definition exists because focused behavior needs one stable owner
def NativeDoc(DataValue: bytes, *, IncludeData: bool = True) -> BrepPayload:
    NativeDigest = Hashlib.sha256(DataValue).digest()
    return BrepPayload(
        KNativeDocBindingId,
        "catia.v5.sha256",
        "native_document_binding",
        "sha256",
        Hashlib.sha256(NativeDigest).hexdigest(),
        NativeDigest if IncludeData else None,
        source_stream="V5_CFV2",
        provenance=Provenance(
            adapter=KFormatId,
            native_id=Hashlib.sha256(DataValue).hexdigest(),
            spans=(
                ProvenanceSpan("V5_CFV2", 0, len(DataValue), "native-document-binding"),
            ),
        ),
        role=PayloadRole.VERIFICATION,
        file_extension=".sha256",
    )


# this definition exists because focused behavior needs one stable owner
def AppVersion(DataValue: bytes) -> str:
    Match = RegexLib.search(b"V5R\\d+(?:SP\\d+)?(?:HF\\d+)?", DataValue)
    return Match.group().decode("ascii") if Match else "CATIA V5"


# this definition exists because focused behavior needs one stable owner
def NativeBaseA(DocValue: CadDocument, DocType: str) -> bytes | None:
    Candidates = sorted(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if (IsNativeDocA(Payload) or IsSavedDocA(Payload))
            and Payload.schema == DocType
            and (Payload.data is not None)
        ),
        key=IsSavedDocA,
    )
    for Payload in Candidates:
        DataValue = Payload.data
        if DataValue is None or Hashlib.sha256(DataValue).hexdigest() != Payload.sha256:
            continue
        if MatchingDoc(DocValue, Payload) is None:
            continue
        try:
            Archive = CfvTwoArchive.from_bytes(DataValue)
            if ManifestBytes(Archive) is not None:
                continue
            if DetectDocType(Archive, f"candidate.{DocType}") != DocType:
                continue
        except (CatiaAdapterA, CfvTwoFormatError, TypeError, ValueError):
            continue
        return DataValue
    return None


# this definition exists because focused behavior needs one stable owner
def UnchangedNative(DocValue: CadDocument, DocType: str) -> tuple[bytes, bool] | None:
    Expected = DocValue.metadata.get("catia.roundtrip_sha256")
    if not isinstance(Expected, str) or Expected != SemanticDigest(DocValue):
        return None
    Matches = sorted(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if (IsNativeDocA(Payload) or IsSavedDocA(Payload))
            and Payload.schema == DocType
            and (Payload.data is not None)
        ),
        key=IsNativeDocA,
    )
    for Payload in Matches:
        DataValue = Payload.data
        if DataValue is None or Hashlib.sha256(DataValue).hexdigest() != Payload.sha256:
            continue
        Binding = MatchingDoc(DocValue, Payload)
        if Binding is None:
            continue
        if IsSavedDocA(Payload):
            ReplayDigest = Payload.attributes.get(KReplaySemanticAttr)
            if not isinstance(ReplayDigest, str) or ReplayDigest != SavedReplay(
                DocValue, Payload, Binding
            ):
                continue
        if IsNativePayload(DocValue, DataValue, DocType, Payload, Binding):
            return (DataValue, IsSavedDocA(Payload))
    return None


# this definition exists because focused behavior needs one stable owner
def IsNativeChoice(DocValue: CadDocument, Payload: BrepPayload) -> bool:
    Expected = DocValue.metadata.get("catia.roundtrip_sha256")
    if not isinstance(Expected, str) or Expected != SemanticDigest(DocValue):
        return False
    DataValue = Payload.data
    if DataValue is None or Hashlib.sha256(DataValue).hexdigest() != Payload.sha256:
        return False
    Binding = MatchingDoc(DocValue, Payload)
    if Binding is None:
        return False
    return IsNativePayload(DocValue, DataValue, Payload.schema, Payload, Binding)


# this definition exists because focused behavior needs one stable owner
def MatchingDoc(DocValue: CadDocument, NativeDoc: BrepPayload) -> BrepPayload | None:
    if IsNativeDocA(NativeDoc):
        BindingId = KNativeDocBindingId
    elif IsSavedDocA(NativeDoc):
        Token = NativeDoc.id.removeprefix(KSavedDocPrefix)
        BindingId = f"{KSavedBindingPrefix}{Token}"
    else:
        return None
    Matches = tuple(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.id == BindingId
            and IsCatiaDoc(Payload)
            and IsBindingMatch(Payload, NativeDoc)
        )
    )
    if len(Matches) != 1:
        return None
    return Matches[0]


# this definition exists because focused behavior needs one stable owner
def IsBindingMatch(Binding: BrepPayload, NativeDoc: BrepPayload) -> bool:
    try:
        NativeDigest = bytes.fromhex(NativeDoc.sha256)
    except ValueError:
        return False
    if len(NativeDigest) != Hashlib.sha256().digest_size:
        return False
    if (
        NativeDoc.data is not None
        and Hashlib.sha256(NativeDoc.data).digest() != NativeDigest
    ):
        return False
    if Binding.data is not None and Binding.data != NativeDigest:
        return False
    return Binding.sha256 == Hashlib.sha256(NativeDigest).hexdigest()


# this definition exists because focused behavior needs one stable owner
def SavedReplay(
    DocValue: CadDocument, NativeDoc: BrepPayload, Binding: BrepPayload
) -> str:
    IgnoredIds = {NativeDoc.id, Binding.id}
    Stripped = Replace(
        DocValue,
        brep_payloads=tuple(
            (
                Payload
                for Payload in DocValue.brep_payloads
                if Payload.id not in IgnoredIds
            )
        ),
    )
    return CarrierSemantic(Stripped)


# this definition exists because focused behavior needs one stable owner
def IsNativePayload(
    DocValue: CadDocument,
    DataValue: bytes,
    DocType: str,
    NativeDoc: BrepPayload,
    Binding: BrepPayload,
) -> bool:
    try:
        Archive = CfvTwoArchive.from_bytes(DataValue)
        if DetectDocType(Archive, f"candidate.{DocType}") != DocType:
            return False
        if not IsNativeBinding(NativeDoc, Binding, DataValue):
            return False
        Manifest = ManifestBytes(Archive)
        if Manifest is not None:
            Embedded = ManifestDoc(Manifest)
            return CarrierSemantic(Embedded) == CarrierSemantic(DocValue)
        if DocType == ProductDocType and not IsProductMatch(
            DocValue, DecodeProductTable(Archive)
        ):
            return False
        IncludeTessellation = any(
            (
                Payload.role == PayloadRole.TESSELLATION and Payload.data is not None
                for Payload in DocValue.brep_payloads
            )
        )
        if DocType == PartDocType:
            Parsed = CatiaAdapter().read(
                DataValue,
                ReadOptions(
                    include_brep=True, include_tessellation=IncludeTessellation
                ),
            )
            if PartSemantic(Parsed) != PartSemantic(DocValue):
                return False
        Choice = NativePayloads(
            Archive,
            DataValue,
            DocType,
            ReadOptions(include_brep=True, include_tessellation=IncludeTessellation),
        )
    except (CatiaAdapterA, CfvTwoFormatError, TypeError, ValueError, ZlibValue.error):
        return False
    ChoiceNative = {
        Payload.id: PayloadDigest(Payload)
        for Payload in Choice
        if not IsCatiaDocA(Payload) and (not IsCatiaDoc(Payload))
    }
    Expected = {
        Payload.id: PayloadDigest(Payload)
        for Payload in DocValue.brep_payloads
        if Payload.id in ChoiceNative
    }
    return Expected == ChoiceNative


# this definition exists because focused behavior needs one stable owner
def IsProductMatch(DocValue: CadDocument, Table: ProductTable) -> bool:
    AsmValue = DocValue.assembly
    if AsmValue is None:
        return False
    Definitions = {ItemValue.id: ItemValue for ItemValue in AsmValue.definitions}
    RootValue = Definitions.get(AsmValue.root_definition_id)
    if RootValue is None or RootValue.name != Table.root_name:
        return False
    Expected = tuple(
        (
            (Definitions[ItemValue.definition_id].name, ItemValue.name)
            for ItemValue in AsmValue.instances
        )
    )
    Actual = tuple(
        (
            (ItemValue.definition_name, ItemValue.instance_name)
            for ItemValue in Table.occurrences
        )
    )
    return Expected == Actual


# this definition exists because focused behavior needs one stable owner
def PayloadDigest(Payload: BrepPayload) -> tuple[str, str, str, str, str, str]:
    return (
        Payload.format_id,
        Payload.kind,
        Payload.schema,
        Payload.role.value,
        Payload.file_extension,
        (
            Hashlib.sha256(Payload.data).hexdigest()
            if Payload.data is not None
            else Payload.sha256
        ),
    )


# this definition exists because focused behavior needs one stable owner
def IsNativeBinding(
    NativeDoc: BrepPayload, Binding: BrepPayload, DataValue: bytes
) -> bool:
    NativeDigest = Hashlib.sha256(DataValue).digest()
    return (
        NativeDoc.data == DataValue
        and NativeDoc.sha256 == NativeDigest.hex()
        and (Binding.data == NativeDigest)
        and (Binding.sha256 == Hashlib.sha256(NativeDigest).hexdigest())
    )


# this definition exists because focused behavior needs one stable owner
def SemanticDigest(DocValue: CadDocument) -> str:
    return DocDigest(DocValue, IsNativeDocA)


# this definition exists because focused behavior needs one stable owner
def CarrierSemantic(DocValue: CadDocument) -> str:
    return DocDigest(DocValue, IsCatiaEnvelope)


# this definition exists because focused behavior needs one stable owner
def PartSemantic(DocValue: CadDocument) -> str:

    # this callback exists because local behavior needs one focused transformation
    return DocDigest(
        DocValue, lambda Payload: IsCatiaDocA(Payload) or IsCatiaDoc(Payload)
    )


# this definition exists because focused behavior needs one stable owner
def DocDigest(
    DocValue: CadDocument, IgnoredPayload: Callable[[BrepPayload], bool]
) -> str:
    Value = DigestDoc(DocValue, IgnoredPayload)
    return Hashlib.sha256(Value.to_json(indent=None).encode("utf-8")).hexdigest()


# this definition exists because focused behavior needs one stable owner
def DigestDoc(
    DocValue: CadDocument, IgnoredPayload: Callable[[BrepPayload], bool]
) -> CadDoc:
    Payloads = tuple(
        (
            Replace(
                Payload,
                data=None,
                sha256=(
                    Hashlib.sha256(Payload.data).hexdigest()
                    if Payload.data is not None
                    else Payload.sha256
                ),
            )
            for Payload in DocValue.brep_payloads
            if not IgnoredPayload(Payload)
        )
    )
    Nested = DocValue.assembly
    if Nested is not None:
        Nested = Replace(
            Nested,
            documents=tuple(
                (
                    Replace(
                        ItemValue,
                        document=DigestDoc(ItemValue.document, IgnoredPayload),
                    )
                    for ItemValue in Nested.documents
                )
            ),
        )
    return Replace(
        DocValue,
        source=CadSource("", "", ""),
        brep_payloads=Payloads,
        metadata=SemanticMeta(DocValue.metadata),
        assembly=Nested,
    )


# this definition exists because focused behavior needs one stable owner
def ReadCatia(Source: Source, Options: ReadOptions | None = None) -> CadDoc:
    return CatiaAdapter().read(Source, Options)


# this definition exists because focused behavior needs one stable owner
def WriteCatia(
    DocValue: CadDocument,
    Target: Destination,
    *,
    Overwrite: bool = False,
    Validate: bool = True,
    AllowNonNative: bool = True,
    **LegacyValues: object,
) -> WriteResult:
    LegacyCopy = dict(LegacyValues)
    Overwrite = bool(LegacyCopy.pop("overwrite", Overwrite))
    Validate = bool(LegacyCopy.pop("validate", Validate))
    AllowNonNative = bool(LegacyCopy.pop("allow_non_native", AllowNonNative))
    if LegacyCopy:
        Unexpected = next(iter(LegacyCopy))
        raise TypeError(
            f"WriteCatia() got an unexpected keyword argument {Unexpected!r}"
        )
    return CatiaAdapter().write(
        DocValue,
        Target,
        WriteOptions(
            overwrite=Overwrite,
            validate=Validate,
            values=FrozenMapping({"allow_non_native": AllowNonNative}),
        ),
    )


# this binding exists because shared behavior needs one stable value
Body = BodyRecord

# this binding exists because shared behavior needs one stable value
CadDocument = CadDoc

# this binding exists because shared behavior needs one stable value
CatiaAdapterError = CatiaAdapterA

# this binding exists because shared behavior needs one stable value
Cfv2Archive = CfvTwoArchive

# this binding exists because shared behavior needs one stable value
Cfv2Declaration = CfvTwoDecl

# this binding exists because shared behavior needs one stable value
Cfv2Directory = CfvTwoFolder

# this binding exists because shared behavior needs one stable value
Cfv2FormatError = CfvTwoFormatError

# this binding exists because shared behavior needs one stable value
Cfv2Stream = CfvTwoStream

# this binding exists because shared behavior needs one stable value
Configuration = Config

# this binding exists because shared behavior needs one stable value
DOCUMENT_TYPE_BY_SUFFIX = DocTypeBySuffix

# this binding exists because shared behavior needs one stable value
Destination = Target

# this binding exists because shared behavior needs one stable value
Diagnostic = DiagnosticInfo

# this binding exists because shared behavior needs one stable value
INFO = InfoValue

# this binding exists because shared behavior needs one stable value
PART_DOCUMENT_TYPE = PartDocType

# this binding exists because shared behavior needs one stable value
PRODUCT_DOCUMENT_TYPE = ProductDocType

# this binding exists because shared behavior needs one stable value
Path = FilePath

# this binding exists because shared behavior needs one stable value
SUFFIX_BY_DOCUMENT_TYPE = SuffixByDocType

# this binding exists because shared behavior needs one stable value
Vector3 = VectorThree

# this binding exists because shared behavior needs one stable value
_PARASOLID_FORMAT_IDS = KParasolidFormatIds

# this binding exists because shared behavior needs one stable value
_PART_STREAM = KPartStream

# this binding exists because shared behavior needs one stable value
_PART_SUFFIX = KPartSuffix

# this binding exists because shared behavior needs one stable value
_PRESERVED_BINDING_PREFIX = KSavedBindingPrefix

# this binding exists because shared behavior needs one stable value
_PRESERVED_DOCUMENT_PREFIX = KSavedDocPrefix

# this binding exists because shared behavior needs one stable value
_PRODUCT_STREAM = KProductStream

# this binding exists because shared behavior needs one stable value
_PRODUCT_SUFFIX = KProductSuffix

# this binding exists because shared behavior needs one stable value
_REPLAY_SEMANTIC_ATTRIBUTE = KReplaySemanticAttr

# this binding exists because shared behavior needs one stable value
_WRAPPER_METADATA_KEYS = KWrapperMetaKeys

# this binding exists because shared behavior needs one stable value
_application_version = AppVersion

# this binding exists because shared behavior needs one stable value
_binding_matches_payload = IsBindingMatch

# this binding exists because shared behavior needs one stable value
_carrier_manifest_document = CarrierManifest

# this binding exists because shared behavior needs one stable value
_carrier_semantic_digest = CarrierSemantic

# this binding exists because shared behavior needs one stable value
_catia_envelope_payload = IsCatiaEnvelope

# this binding exists because shared behavior needs one stable value
_container_metadata = ContainerMeta

# this binding exists because shared behavior needs one stable value
_declared_container_role = DeclaredRole

# this binding exists because shared behavior needs one stable value
_declared_osmx_role = DeclaredOsmx

# this binding exists because shared behavior needs one stable value
_decode_typed_brep = DecodeTypedBrep

# this binding exists because shared behavior needs one stable value
_destination_type = TargetType

# this binding exists because shared behavior needs one stable value
_digest_document = DigestDoc

# this binding exists because shared behavior needs one stable value
_document_digest = DocDigest

# this binding exists because shared behavior needs one stable value
_document_type = DetectDocType

# this binding exists because shared behavior needs one stable value
_embedded_document = EmbeddedDoc

# this binding exists because shared behavior needs one stable value
_generated_archive = Generated

# this binding exists because shared behavior needs one stable value
_is_brep_mode_payload = IsBrepMode

# this binding exists because shared behavior needs one stable value
_is_catia_document_binding = IsCatiaDoc

# this binding exists because shared behavior needs one stable value
_is_catia_document_payload = IsCatiaDocA

# this binding exists because shared behavior needs one stable value
_is_cgm_payload = IsCgmPayload

# this binding exists because shared behavior needs one stable value
_is_cgr_payload = IsCgrPayload

# this binding exists because shared behavior needs one stable value
_is_delta_payload = IsDeltaPayload

# this binding exists because shared behavior needs one stable value
_is_mfbrp_payload = IsMfbrpPayload

# this binding exists because shared behavior needs one stable value
_is_native_document_binding = IsNativeDoc

# this binding exists because shared behavior needs one stable value
_is_native_document_payload = IsNativeDocA

# this binding exists because shared behavior needs one stable value
_is_preserved_document_binding = IsSavedDoc

# this binding exists because shared behavior needs one stable value
_is_preserved_document_payload = IsSavedDocA

# this binding exists because shared behavior needs one stable value
_logical_spans = LogicalSpans

# this binding exists because shared behavior needs one stable value
_manifest_bytes = ManifestBytes

# this binding exists because shared behavior needs one stable value
_manifest_document = ManifestDoc

# this binding exists because shared behavior needs one stable value
_manifest_json = ManifestJson

# this binding exists because shared behavior needs one stable value
_matching_document_binding = MatchingDoc

# this binding exists because shared behavior needs one stable value
_native_base_overlay_matches = IsNativeBase

# this binding exists because shared behavior needs one stable value
_native_base_payload = NativeBaseA

# this binding exists because shared behavior needs one stable value
_native_candidate_is_unchanged = IsNativeChoice

# this binding exists because shared behavior needs one stable value
_native_container_data_included = CanIncludeData

# this binding exists because shared behavior needs one stable value
_native_container_specification = NativeContaineA

# this binding exists because shared behavior needs one stable value
_native_document_binding = NativeDoc

# this binding exists because shared behavior needs one stable value
_native_document_binding_matches = IsNativeBinding

# this binding exists because shared behavior needs one stable value
_native_document_payload = NativeDocB

# this binding exists because shared behavior needs one stable value
_native_part_data = NativePartData

# this binding exists because shared behavior needs one stable value
_native_payload_matches_document = IsNativePayload

# this binding exists because shared behavior needs one stable value
_native_payloads = NativePayloads

# this binding exists because shared behavior needs one stable value
_osmx_metadata = OsmxMeta

# this binding exists because shared behavior needs one stable value
_osmx_payload_role = OsmxPayloadRole

# this binding exists because shared behavior needs one stable value
_overlay_preserves_native_base = IsOverlayNative

# this binding exists because shared behavior needs one stable value
_pack_manifest = PackManifest

# this binding exists because shared behavior needs one stable value
_part_planes = PartPlanes

# this binding exists because shared behavior needs one stable value
_part_semantic_digest = PartSemantic

# this binding exists because shared behavior needs one stable value
_payload_signature = PayloadDigest

# this binding exists because shared behavior needs one stable value
_preserved_replay_digest = SavedReplay

# this binding exists because shared behavior needs one stable value
_replay_compatibility = Replay

# this binding exists because shared behavior needs one stable value
_restore_generated = Restore

# this binding exists because shared behavior needs one stable value
_selected_configurations = Selected

# this binding exists because shared behavior needs one stable value
_semantic_digest = SemanticDigest

# this binding exists because shared behavior needs one stable value
_source_bytes = SourceBytesMut

# this binding exists because shared behavior needs one stable value
_stream_provenance = StreamSource

# this binding exists because shared behavior needs one stable value
_summary_stream = SummaryStream

# this binding exists because shared behavior needs one stable value
_symbol_provenance = SymbolSource

# this binding exists because shared behavior needs one stable value
_typed_brep = TypedBrep

# this binding exists because shared behavior needs one stable value
_unchanged_native_payload = UnchangedNative

# this binding exists because shared behavior needs one stable value
_unpack_manifest = UnpackManifest

# this binding exists because shared behavior needs one stable value
_write_bytes = WriteBytes

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
append_cfv2_stream = AppendCfvTwoStream

# this binding exists because shared behavior needs one stable value
build_cfv2 = BuildCfvTwo

# this binding exists because shared behavior needs one stable value
build_declaration = BuildDecl

# this binding exists because shared behavior needs one stable value
decode_opencascade_brep = DecodeOpencascadeBrep

# this binding exists because shared behavior needs one stable value
decode_parasolid_brep = DecodeParasolidBrep

# this binding exists because shared behavior needs one stable value
decode_product_table = DecodeProductTable

# this binding exists because shared behavior needs one stable value
filter_document = FilterDoc

# this binding exists because shared behavior needs one stable value
frozen_mapping = FrozenMapping

# this binding exists because shared behavior needs one stable value
hashlib = Hashlib

# this binding exists because shared behavior needs one stable value
infer_capabilities = InferCapabilities

# this binding exists because shared behavior needs one stable value
is_binary_destination = IsBinaryTarget

# this binding exists because shared behavior needs one stable value
native_product_assembly = NativeProductAsm

# this binding exists because shared behavior needs one stable value
os = OsModule

# this binding exists because shared behavior needs one stable value
re = RegexLib

# this binding exists because shared behavior needs one stable value
read_catia = ReadCatia

# this binding exists because shared behavior needs one stable value
replace = Replace

# this binding exists because shared behavior needs one stable value
semantic_metadata = SemanticMeta

# this binding exists because shared behavior needs one stable value
struct = Struct

# this binding exists because shared behavior needs one stable value
suppress = Suppress

# this binding exists because shared behavior needs one stable value
with_wrapper_metadata = WithWrapperMeta

# this binding exists because shared behavior needs one stable value
write_catia = WriteCatia

# this binding exists because shared behavior needs one stable value
zlib = ZlibValue

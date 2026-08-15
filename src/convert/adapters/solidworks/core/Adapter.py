# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from collections import Counter, defaultdict as Defaultdict
from contextlib import suppress as Suppress
from dataclasses import dataclass as DataClass, field as Field, replace as Replace
import hashlib as Hashlib
from io import BytesIO as BytesIo
import json as JsonValue
import math as MathValue
import os as OsModule
from pathlib import Path as FilePath, PureWindowsPath
import re as RegexLib
import struct as Struct
import tempfile as Tempfile
from typing import Any as AnyValue, Mapping, Sequence
import xml.etree.ElementTree as XmlTree
from convert.adapters.base import (
    AdapterInfo,
    CapabilityTransfer,
    CarrierReason,
    Destination as Target,
    ProbeResult,
    ReadOptions,
    Source,
    TransferMode,
    WriteOptions,
    WriteResult,
    is_binary_destination as IsBinaryTarget,
)
from interchange import (
    ArcEllipseGeometry as ArcEllipseGeom,
    ArcGeometry as ArcGeom,
    ArcParabolaGeometry as ArcParabolaGeom,
    AssemblyData as AsmData,
    Body as BodyValue,
    BooleanOperation as BoolOperation,
    BoundingBox,
    BrepModel,
    BrepPayload,
    CadDocument as CadDoc,
    CadSource,
    Capability,
    ChamferFeature,
    CircleGeometry as CircleGeom,
    CombineFeature,
    ComponentDefinition,
    ComponentDocument as ComponentDoc,
    ComponentInstance,
    ComponentKind,
    Configuration as Config,
    ConstraintReference as RuleRef,
    Diagnostic as DiagValue,
    DomeFeature,
    ExtrusionEndCondition,
    ExtrusionFeature,
    Expression,
    EllipseGeometry as EllipseGeom,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    GeometryKind as GeomKind,
    HoleFeature,
    LineGeometry as LineGeom,
    MateAlignment,
    MateConstraint as MateRule,
    MateEntity,
    MateEntityKind,
    MateGroup,
    MateKind,
    Matrix4 as MatrixFour,
    Mesh as MeshValue,
    MoveBodyFeature,
    NativeFeatureDefinition,
    NativeGeometry as NativeGeom,
    Parameter as Param,
    ParameterRole as ParamRole,
    ParameterValue as ParamValue,
    PointGeometry as PointGeom,
    PayloadRole,
    Provenance,
    ProvenanceSpan,
    ReferencePlaneFeature as RefPlaneFeature,
    RevolutionFeature,
    ScaleFeature,
    Selection,
    SelectionPathElement as SelectionPathElem,
    Severity,
    ShellFeature,
    Sketch as SketchData,
    SketchConstraint as SketchRule,
    SketchEntity,
    SplineGeometry as SplineGeom,
    SupportPlane,
    TopologySummary,
    Transform,
    UnitSystem,
    ValueKind,
    Vector2 as VectorTwo,
    Vector3 as VectorThree,
    frozen_mapping as FrozenMapping,
    filter_document as FilterDoc,
    infer_capabilities as InferCapabilities,
    retained_capabilities as RetainedCapabilities,
    semantic_metadata as SemanticMeta,
    source_payload_indexes as SourcePayloadIndexes,
    with_wrapper_metadata as WithWrapperMeta,
)
from convert.adapters.solidworks.assembly.Assembly import (
    MATE_VALUE_SEMANTICS as MateValueSemantics,
    NATIVE_MATE_ALIGNMENT_BY_CODE as NativeMateAlignmentByCode,
    NATIVE_MATE_ENTITY_MARKERS as NativeMateEntityMarkers,
    NATIVE_MATE_NEUTRAL_KIND_ALIASES as NativeMateNeutralKind,
    NativeAssembly as NativeAsm,
    NativeAssemblyDefinition as NativeAsmDefinition,
    NativeAssemblyEncoding as NativeAsmEncoding,
    NativeAssemblyOccurrence as NativeAsmItem,
    NativeMate,
    NativeMateEntity,
    NativeMateList,
    decode_mate_list as DecodeMateList,
    decode_native_assembly as DecodeNativeAsm,
    encode_native_assembly as EncodeNativeAsm,
)
from convert.adapters.solidworks.assembly.AssemblyCore import AsmCoreItem, EncodeAsmCore
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
    build_sldprt as BuildSldprt,
)
from convert.adapters.solidworks.container.Format import (
    COMPONENT_TREE_STREAM as ComponentTreeStream,
    CONTAINER_VERSIONS as ContainerVersions,
    CONTENT_TYPES_STREAM as ContentTypesStream,
    DISPLAY_LISTS_STREAM as DisplayListsStream,
    FEATURES_STREAM as FeaturesStream,
    FORMAT_ID_BY_SUFFIX as FormatIdBySuffix,
    INFO as InfoValue,
    KEYWORDS_STREAM as KeywordsStream,
    KIT_DOCUMENT_STREAM as KitDocStream,
    KIT_NATIVE_STREAM as KitNativeStream,
    KIT_RESOLVED_STREAM as KitResolvedStream,
    MATES_STREAM_NAME as MatesStreamName,
    MATES_STREAM_SUFFIX as MatesStreamSuffix,
    PARTITION_STREAM as PartitionStream,
    PLANE_FEATURE_TYPES as PlaneFeatureTypes,
    RELATIONSHIPS_STREAM as RelationshipsStream,
    RESOLVED_FEATURES_STREAM as ResolvedFeaturesStream,
    SOLIDWORKS_STREAM as SolidworksStream,
    SOLID_BODY_FEATURE_TYPES as SolidBodyFeatureTypes,
    SUFFIX_BY_FORMAT_ID as SuffixByFormatId,
)
from convert.adapters.solidworks.core.FeatureKindByNative import KFeatureKindByNative
from convert.adapters.solidworks.core.Native import (
    NativeDimension,
    NativeFeature,
    XmlFeature,
    NativeMarker,
    NativeModel,
    NativeOperation,
    NativePlane,
    NativeProfile,
    NativeSketch,
    NativeAssemblyEnvelope as NativeAsmEnvelope,
    DIRECTION_AXIS_ROLE as DirectionAxisRole,
    decode_native_model as DecodeNativeModel,
    encode_native_assembly_envelope as EncodeNativeAsmEnvelope,
    encode_native_part as EncodeNativePart,
    operation_axis_subelement as OperationAxisSubElem,
)
from convert.adapters.solidworks.container.Parasolid import (
    ParasolidPayload,
    ParasolidWriteError,
    contains_parasolid_payload as ContainsParasolidPayload,
    decode_brep_model as DecodeBrepModel,
    decode_partition_stream as DecodePartitionStream,
    encode_blank_partition_stream as EncodeBlankPartition,
    encode_brep_model as EncodeBrepModel,
    encode_partition_stream as EncodePartitionStream,
    is_native_parasolid_payload as IsNativeParasolidPayload,
)

# this binding exists because shared behavior needs one stable value
KFormatId = InfoValue.format_id

# this binding exists because shared behavior needs one stable value
KAsmFormatId = InfoValue.aliases[0]

# this binding exists because shared behavior needs one stable value
KSourceBytesKey = "solidworks_source_bytes"

# this binding exists because shared behavior needs one stable value
KSourceShaTwoFiveSixKey = "solidworks_source_sha256"

# this binding exists because shared behavior needs one stable value
KSourceSemanticShaTwoFive = "solidworks_source_semantic_sha256"

# this binding exists because shared behavior needs one stable value
KSourceFormatKey = "solidworks_source_format_id"

# this binding exists because shared behavior needs one stable value
KAsmReaderRequiredStreams = (
    "Contents/CMgr",
    "Contents/Config-0",
    ResolvedFeaturesStream,
    "Contents/Definition",
)

# this binding exists because shared behavior needs one stable value
KAsmDonorCarriedStreams = (
    *KAsmReaderRequiredStreams,
    "Contents/Config-0-ModelHeader",
    "Header2",
)

# this binding exists because shared behavior needs one stable value
KAsmRewritableDonorStreaA = frozenset(
    {KitDocStream, KitNativeStream, KitResolvedStream, ComponentTreeStream}
)

# this binding exists because shared behavior needs one stable value
KAttestedCompatibilities = frozenset(
    {
        "kit-neutral-only",
        "native-assembly-with-kit-neutral",
        "native-brep-with-kit-neutral",
        "native-metadata-with-kit-neutral",
        "native-source-with-kit-neutral",
        "native-template",
    }
)

# this binding exists because shared behavior needs one stable value
KSourceKeys = frozenset(
    {
        KSourceBytesKey,
        KSourceShaTwoFiveSixKey,
        KSourceSemanticShaTwoFive,
        KSourceFormatKey,
    }
)

# this binding exists because shared behavior needs one stable value
KNumberText = RegexLib.compile("[-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][-+]?\\d+)?")

# this binding exists because shared behavior needs one stable value
KResolvedConfigStream = RegexLib.compile("^Contents/Config-(\\d+)-ResolvedFeatures$")

# this binding exists because shared behavior needs one stable value
KTargetUnsupported = frozenset(
    {Capability.NATIVE_PAYLOADS, Capability.PROVENANCE, Capability.ROUNDTRIP_METADATA}
)


# this definition exists because focused behavior needs one stable owner
@DataClass(frozen=True, slots=True)
class Generated:
    streams: dict[str, bytes]
    native_brep: str
    native_capabilities: frozenset[Capability]
    compatibility: str
    application_usable: bool
    vendor_loadable: bool
    mixed_capabilities: frozenset[Capability] = frozenset()
    unexpressed: tuple[str, ...] = ()
    donor_notes: tuple[str, ...] = ()
    reader_gaps: tuple[str, ...] = ()


# this definition exists because focused behavior needs one stable owner
@DataClass(frozen=True, slots=True)
class AsmTemplate:
    locals().setdefault("__annotations__", {})
    __annotations__["capabilities"] = "frozenset[Capability]"
    __annotations__["divergences"] = "tuple[str, ...]"


# this definition exists because focused behavior needs one stable owner
@DataClass(frozen=True, slots=True)
class AsmBundle:
    locals().setdefault("__annotations__", {})
    __annotations__["names"] = "Mapping[str, str]"
    __annotations__["payloads"] = "Mapping[Path, bytes]"
    StampValues: Mapping[str, int]
    __annotations__["complete"] = "bool"
    NativeCaps: frozenset[Capability] = frozenset()


# this binding exists because shared behavior needs one stable value
KWrapperMetaKeys = KSourceKeys | frozenset(
    {
        "adapter",
        "embedded_source_format_id",
        "embedded_source_path",
        "embedded_source_sha256",
        "file_id",
        "solidworks.container_compatibility",
        "stream_names",
    }
)


# this definition exists because focused behavior needs one stable owner
class SldprtAdapter:
    __slots__ = ()

    @property
    def info(self) -> AdapterInfo:
        return InfoAction(self)

    def probe(self, SourceValue: Source) -> ProbeResult:
        return Probe(self, SourceValue)

    def read(
        self, SourceValue: Source, Options: ReadOptions | None = None
    ) -> CadDoc:
        return ReadAction(self, SourceValue, Options)

    def supports(self, DocValue: CadDocument, TargetValue: Target) -> bool:
        return IsSupports(self, DocValue, TargetValue)

    def write(
        self,
        DocValue: CadDocument,
        TargetValue: Target,
        Options: WriteOptions | None = None,
    ) -> WriteResult:
        return Write(self, DocValue, TargetValue, Options)


# adapter metadata stays isolated so discovery can inspect capabilities without reading documents
def InfoAction(Instance) -> AdapterInfo:
    return InfoValue


# probing stays independent so format detection never performs a full conversion
def Probe(Instance, Source: Source) -> ProbeResult:
    try:
        DataValue, Label = SourceBytes(Source)
        if len(DataValue) < 8:
            return ProbeResult(
                KFormatId, 0.0, "file is shorter than the container header"
            )
        Version = Struct.unpack_from(">I", DataValue, 4)[0]
        if Version not in ContainerVersions:
            return ProbeResult(
                KFormatId, 0.0, f"unsupported container version {Version}"
            )
        Archive = SldprtArchive.from_bytes(DataValue, Label)
    except (OSError, SldprtFormatError, TypeError, ValueError) as ErrorInfo:
        return ProbeResult(KFormatId, 0.0, str(ErrorInfo))
    Names = Archive.streams
    if KeywordsStream in Names and any(
        (KResolvedConfigStream.fullmatch(NameValue) for NameValue in Names)
    ):
        return ProbeResult(
            KFormatId, 1.0, "native history and resolved-feature streams found"
        )
    return ProbeResult(
        KFormatId, 0.6, "recognized SOLIDWORKS compound stream container"
    )


# adapter reading dispatches embedded assembly and native part paths through one contract
def ReadAction(Instance, Source: Source, Options: ReadOptions | None = None) -> CadDoc:
    Settings = Options or ReadOptions()
    DataValue, Label = SourceBytes(Source)
    Archive = SldprtArchive.from_bytes(DataValue, Label)
    Embedded = Archive.get(KitDocStream)
    if Embedded is not None:
        DocValue = EmbeddedDoc(Instance, Archive, DataValue, Label, Embedded, Settings)
        ValidateSource(Label, DocValue.assembly is not None)
        return DocValue
    if Archive.get(ComponentTreeStream) is not None:
        DocValue = RetainSource(
            AsmDoc(Instance, Archive, DataValue, Label, Settings), DataValue
        )
        ValidateSource(Label, True)
        return DocValue
    return ReadNativePart(Instance, Archive, DataValue, Label, Settings)


# destination checks belong on the adapter so callers can reject incompatible targets early
def IsSupports(Instance, DocValue: CadDocument, Target: Destination) -> bool:
    PathValue = TargetPath(Target)
    if PathValue is None:
        return IsBinaryTarget(Target)
    Expected = SuffixByFormatId[TargetFormatId(DocValue)]
    return PathValue.suffix.casefold() == Expected


# adapter writing delegates policy and persistence to the focused write composition
def Write(
    Instance,
    DocValue: CadDocument,
    Target: Destination,
    Options: WriteOptions | None = None,
) -> WriteResult:
    return WriteDocument(Instance, DocValue, Target, Options)


# generated writing needs one immutable input bundle so selection policy cannot drift across phases
@DataClass(frozen=True, slots=True)
class GenWriteInput:
    Template: bytes | None
    Bundle: AsmBundle
    PortableCarrier: bool
    BundleNames: Mapping[str, str]
    BundleStamps: Mapping[str, int]
    ModelName: str


# write outcomes share one contract so saved and generated paths produce identical result assembly
@DataClass(frozen=True, slots=True)
class WritePlan:
    DataValue: bytes
    Diagnostics: tuple[DiagValue, ...]
    Transfers: tuple[CapabilityTransfer, ...]
    ModeValue: str
    NativeContent: str
    NativeBrep: str
    Compatibility: str
    AppUsable: bool
    VendorLoadable: bool
    Bundle: AsmBundle
    PortableCarrier: bool


# generation input selection owns carrier policy bundle discovery and caller supplied identities
def GetGenInputs(
    DocValue: CadDocument, PathValue: FilePath | None, Settings: WriteOptions
) -> GenWriteInput:
    Template = SourceTemplate(DocValue, PathValue)
    if Settings.values.get("allow_non_native", True) is not True:
        KindValue = "edited native-backed" if Template is not None else "source-less"
        raise SldprtFormatError(
            f"{KindValue} SOLIDWORKS writing requires WriteOptions(values={{'allow_non_native': True}})"
        )
    Bundle = AsmBundle({}, {}, {}, False)
    if (
        DocValue.assembly is not None
        and PathValue is not None
        and Settings.values.get("portable") is True
    ):
        Bundle = AsmBundleA(DocValue, PathValue, Settings)
    PortableCarrier = (
        DocValue.assembly is not None
        and Settings.values.get("portable") is True
        and Settings.values.get("allow_carrier") is True
        and (not Bundle.complete)
    )
    ConfiguredNames = Settings.values.get("bundle_names")
    BundleNames = (
        Bundle.names
        if Bundle.names
        else ConfiguredNames if isinstance(ConfiguredNames, Mapping) else {}
    )
    ConfiguredStamps = Settings.values.get("bundle_stamps")
    BundleStamps = (
        Bundle.StampValues
        if Bundle.StampValues
        else ConfiguredStamps if isinstance(ConfiguredStamps, Mapping) else {}
    )
    ConfiguredName = Settings.values.get("model_name")
    ModelName = ConfiguredName if isinstance(ConfiguredName, str) else ""
    return GenWriteInput(
        Template, Bundle, PortableCarrier, BundleNames, BundleStamps, ModelName
    )


# generation diagnostics remain centralized so every unsupported native feature gets one stable warning
def GetGenDiags(
    Generated: Generated, Diagnostics: tuple[DiagValue, ...]
) -> tuple[DiagValue, ...]:
    if not Generated.application_usable:
        Diagnostics = (
            *Diagnostics,
            DiagValue(
                code="sldprt.neutral_write",
                message="one or more neutral edits are retained in the Kit stream because their native SOLIDWORKS records could not be reproduced",
                severity=Severity.WARNING,
            ),
        )
    if Generated.unexpressed:
        Diagnostics = (
            *Diagnostics,
            DiagValue(
                code="sldasm.unexpressed_native_records",
                message="generated SOLIDWORKS assembly does not express "
                + ", ".join(Generated.unexpressed),
                severity=Severity.WARNING,
            ),
        )
    if Generated.reader_gaps:
        Diagnostics = (
            *Diagnostics,
            DiagValue(
                code="sldasm.vendor_reader_rejects",
                message="SOLIDWORKS assembly is not reported loadable because the vendor reader contract is unsatisfied: "
                + ", ".join(Generated.reader_gaps),
                severity=Severity.WARNING,
            ),
        )
    if Generated.donor_notes:
        Diagnostics = (
            *Diagnostics,
            DiagValue(
                code=(
                    "sldprt.donor_partial"
                    if Generated.vendor_loadable
                    else "sldprt.donor_declined"
                ),
                message=(
                    "native SOLIDWORKS feature records omit "
                    if Generated.vendor_loadable
                    else "native SOLIDWORKS feature records were not written because "
                )
                + "; ".join(Generated.donor_notes),
                severity=Severity.WARNING,
            ),
        )
    if Generated.native_brep.startswith("unsupported:"):
        Diagnostics = (
            *Diagnostics,
            DiagValue(
                code="sldprt.native_brep_unsupported",
                message=Generated.native_brep.removeprefix("unsupported:"),
                severity=Severity.WARNING,
            ),
        )
    return Diagnostics


# native content classification stays isolated because metadata consumers depend on its exact vocabulary
def GetNativeType(
    Generated: Generated, Template: bytes | None, IsAssembly: bool
) -> str:
    if Template is not None:
        return "source-preserved"
    if Generated.native_brep == "generated":
        return "neutral-brep" if IsAssembly else "native-metadata-and-neutral-brep"
    if Generated.native_brep == "preserved":
        return (
            "parasolid-import" if IsAssembly else "native-metadata-and-parasolid-import"
        )
    return "none" if IsAssembly else "native-metadata"


# generated write planning composes first principles streams attestation and deterministic container bytes
def BuildGenPlan(
    DocValue: CadDocument,
    PathValue: FilePath | None,
    Settings: WriteOptions,
    RequiredCaps: frozenset[Capability],
) -> WritePlan:
    InputValue = GetGenInputs(DocValue, PathValue, Settings)
    GeneratedValue = GeneratedB(
        DocValue,
        InputValue.Template,
        InputValue.BundleNames,
        BundleComplete=InputValue.Bundle.complete if InputValue.Bundle.names else None,
        BundleCapabilities=InputValue.Bundle.NativeCaps,
        BundleStamps=InputValue.BundleStamps,
        ModelName=InputValue.ModelName,
    )
    if InputValue.PortableCarrier:
        GeneratedValue = Replace(
            GeneratedValue,
            compatibility=(
                "native-source-with-kit-neutral"
                if GeneratedValue.compatibility == "native-template"
                else GeneratedValue.compatibility
            ),
            application_usable=False,
            vendor_loadable=False,
        )
    Transfers = SolidworksA(
        RequiredCaps,
        GeneratedValue.native_capabilities,
        GeneratedValue.mixed_capabilities,
    )
    Streams = GeneratedValue.streams
    Streams[KitNativeStream] = NativeBytes(
        Streams,
        GeneratedValue.compatibility,
        GeneratedValue.application_usable,
        GeneratedValue.vendor_loadable,
        Transfers,
        GeneratedValue.native_brep,
    )
    FileId = (
        SldprtArchive.from_bytes(InputValue.Template).file_id
        if InputValue.Template is not None
        else None
    )
    DataValue = BuildSldprt(Streams, file_id=FileId, template=InputValue.Template)
    NativeContent = GetNativeType(
        GeneratedValue, InputValue.Template, DocValue.assembly is not None
    )
    Diagnostics = GetGenDiags(GeneratedValue, DocValue.diagnostics)
    return WritePlan(
        DataValue,
        Diagnostics,
        Transfers,
        "template" if InputValue.Template is not None else "generated",
        NativeContent,
        GeneratedValue.native_brep,
        GeneratedValue.compatibility,
        GeneratedValue.application_usable,
        GeneratedValue.vendor_loadable,
        InputValue.Bundle,
        InputValue.PortableCarrier,
    )


# exact replay planning preserves prior attestation while keeping fallback capability losses explicit
def BuildSavedPlan(
    SavedData: bytes,
    RequiredCaps: frozenset[Capability],
    Diagnostics: tuple[DiagValue, ...],
) -> WritePlan:
    Compatibility = Replay(SavedData)
    Attestation = Native(SavedData)
    NativeBrep = "exact"
    NativeContent = "exact"
    if Compatibility == "native-exact":

        # exact replay supports every required capability without reclassification
        Transfers = tuple(
            (
                CapabilityTransfer(Capability, TransferMode.NATIVE)
                for Capability in sorted(RequiredCaps, key=lambda Value: Value.value)
            )
        )
        AppUsable = True
        VendorLoadable = True
    elif Attestation is not None:
        Transfers = Attested(Attestation, RequiredCaps)
        AppUsable = Attestation["application_usable"]
        VendorLoadable = Attestation["vendor_loadable"]
        NativeBrep = str(Attestation.get("native_brep", "template"))
        NativeContent = "source-preserved"
    else:
        Transfers = SolidworksA(RequiredCaps, frozenset())
        AppUsable = False
        VendorLoadable = False
    return WritePlan(
        SavedData,
        Diagnostics,
        Transfers,
        "exact",
        NativeContent,
        NativeBrep,
        Compatibility,
        AppUsable,
        VendorLoadable,
        AsmBundle({}, {}, {}, False),
        False,
    )


# write result construction stays separate because persistence and attestation metadata share one output boundary
def MakeWriteResult(
    DocValue: CadDocument,
    Output: FilePath | None,
    FormatId: str,
    PlanValue: WritePlan,
    RequiredCaps: frozenset[Capability],
) -> WriteResult:
    Archive = SldprtArchive.from_bytes(PlanValue.DataValue, Output or "<memory>")
    NativeEdits = all(
        (
            Transfer.mode is TransferMode.NATIVE
            or Transfer.carrier_reason is CarrierReason.TARGET_UNSUPPORTED
            for Transfer in PlanValue.Transfers
        )
    )
    Requirements = (
        ("referenced SOLIDWORKS component files",)
        if DocValue.assembly is not None
        and (not PlanValue.Bundle.complete)
        and (not PlanValue.PortableCarrier)
        else ()
    )
    NativeCaps = {
        Transfer.capability
        for Transfer in PlanValue.Transfers
        if Transfer.mode is TransferMode.NATIVE
    }
    Metadata = FrozenMapping(
        {
            "mode": PlanValue.ModeValue,
            "format_id": FormatId,
            "compatibility": PlanValue.Compatibility,
            "native_content": PlanValue.NativeContent,
            "neutral_edits_are_native": NativeEdits,
            "vendor_loadable": PlanValue.VendorLoadable,
            "application_usable": PlanValue.AppUsable,
            "native_geometry": PlanValue.NativeBrep
            in {
                "exact",
                "feature-rebuilt",
                "generated",
                "preserved",
                "patched",
                "template",
            },
            "native_brep": PlanValue.NativeBrep,
            "native_history": Capability.PARAMETRIC_HISTORY not in RequiredCaps
            or Capability.PARAMETRIC_HISTORY in NativeCaps,
            "native_assembly": DocValue.assembly is not None
            and Capability.ASSEMBLIES in NativeCaps,
            "native_self_contained": PlanValue.AppUsable
            and (DocValue.assembly is None or PlanValue.Bundle.complete),
            "referenced_files_written": len(PlanValue.Bundle.payloads),
            "container_version": Archive.format_version,
            "file_id": Archive.file_id,
            "stream_count": len(Archive.records),
            "runtime": "python-stdlib",
        }
    )
    return WriteResult(
        path=Output,
        adapter=FormatId,
        bytes_written=len(PlanValue.DataValue),
        diagnostics=PlanValue.Diagnostics,
        metadata=Metadata,
        transfers=PlanValue.Transfers,
        requirements=Requirements,
        application_usable=PlanValue.AppUsable,
        vendor_loadable=PlanValue.VendorLoadable,
    )


# public writing composes validation planning persistence and result attestation without mixing their policies
def WriteDocument(
    Instance: SldprtAdapter,
    DocValue: CadDocument,
    Target: Destination,
    Options: WriteOptions | None,
) -> WriteResult:
    Settings = Options or WriteOptions()
    if Settings.validate:
        DocValue.assert_valid()
    ExpectedFormat = KAsmFormatId if DocValue.assembly is not None else KFormatId
    if (
        Settings.destination_format is not None
        and Settings.destination_format != ExpectedFormat
    ):
        raise ValueError(
            f"{Settings.destination_format} does not support this document kind"
        )
    if not Instance.supports(DocValue, Target):
        Expected = SuffixByFormatId[ExpectedFormat].upper()
        raise ValueError(f"SOLIDWORKS destination must end in {Expected}")
    PathValue = TargetPath(Target)
    FormatId = TargetFormatId(DocValue)
    SavedData = (
        None
        if DocValue.assembly is not None
        and (
            Settings.values.get("portable") is True
            or Settings.values.get("bundle_member") is True
        )
        else SavedSource(DocValue, PathValue)
    )
    RequiredCaps = Required(DocValue)
    PlanValue = (
        BuildGenPlan(DocValue, PathValue, Settings, RequiredCaps)
        if SavedData is None
        else BuildSavedPlan(SavedData, RequiredCaps, DocValue.diagnostics)
    )
    Output = WriteTargetMut(Target, PlanValue.DataValue, Settings.overwrite)
    for BundlePath, Payload in PlanValue.Bundle.payloads.items():
        WriteTargetMut(BundlePath, Payload, Settings.overwrite)
    return MakeWriteResult(DocValue, Output, FormatId, PlanValue, RequiredCaps)


# native part reconstruction stays separate because assembly and embedded documents bypass this model path
def ReadNativePart(
    Instance: SldprtAdapter,
    Archive: SldprtArchive,
    DataValue: bytes,
    Label: str,
    Settings: ReadOptions,
) -> CadDoc:
    Model = NativePartModel(Archive, Settings.configuration)
    ConfigValues = Configurations(Model, Settings.configuration)
    ParamValues = Parameters(Model)
    ParamIds = {Param.id for Param in ParamValues}
    PlaneValues = Planes(Model, ParamIds)
    SketchValues = Sketches(Model, ParamIds)
    SelectValues = Selections(Model)
    TimeValues = Timeline(Model, SelectValues)
    Payloads, PayloadDiags = BrepPayloads(Archive, Settings)
    BrepValue = TypedBrep(Payloads)
    SolidOpIds = frozenset(
        (
            FeatureId(Operation.object_id)
            for Operation in Model.operations
            if Operation.kind != "surface"
        )
    )
    FinalFeature = FinalBodyId(TimeValues, SolidOpIds)
    BodyFeature = SolidBody(Model.features)
    Bodies = (
        BodyValue(
            id="sldprt:body:1",
            name=BodyFeature.name if BodyFeature is not None else "Body 1",
            final_feature_id=FinalFeature,
            topology=TopologySummary(
                solid_count=1 if SolidOpIds else 0, bounding_box=BoundingBoxA(Model)
            ),
            provenance=FeatureA(BodyFeature) if BodyFeature is not None else None,
            attributes=FrozenMapping(
                {
                    "native_object_id": (
                        BodyFeature.object_id if BodyFeature is not None else None
                    ),
                    "parasolid_payload_ids": tuple(
                        (Payload.id for Payload in Payloads)
                    ),
                }
            ),
        ),
    )
    Diagnostics = (
        tuple(
            (
                DiagValue(
                    code="sldprt.native_record_unresolved",
                    message=Message,
                    severity=Severity.INFO,
                )
                for Message in Model.diagnostics
            )
        )
        + PayloadDiags
    )
    DocValue = CadDoc(
        source=CadSource(
            format_id=KFormatId,
            path=Label,
            sha256=Hashlib.sha256(DataValue).hexdigest(),
            container_version=str(Archive.format_version),
            attributes=FrozenMapping(
                {"file_id": Archive.file_id, "stream_count": len(Archive.records)}
            ),
        ),
        configurations=ConfigValues,
        parameters=ParamValues,
        support_planes=PlaneValues,
        sketches=SketchValues,
        selections=SelectValues,
        feature_timeline=TimeValues,
        bodies=Bodies,
        brep=BrepValue,
        brep_payloads=Payloads,
        diagnostics=Diagnostics,
        capabilities=Instance.info.capabilities,
        metadata=FrozenMapping(
            {
                "adapter": KFormatId,
                "file_id": Archive.file_id,
                "native_class_names": tuple(
                    dict.fromkeys((ItemValue.name for ItemValue in Model.classes))
                ),
                "native_feature_count": len(Model.features),
                "native_name_record_count": len(Model.names),
                "native_scalar_count": len(Model.scalars),
                "stream_names": tuple((Record.name for Record in Archive.records)),
            }
        ),
        units=UnitSystem.MILLIMETER,
    )
    DocValue.assert_valid()
    ValidateSource(Label, False)
    return RetainSource(DocValue, DataValue)


# this definition exists because focused behavior needs one stable owner
def ReadSldprt(
    Source: Source,
    *,
    Config: str | None = None,
    IncludeBrep: bool = True,
    IncludeTessellation: bool = True,
    Strict: bool = True,
    **LegacyValues: object,
) -> CadDoc:
    Config = LegacyValues.get("configuration", Config)
    IncludeBrep = LegacyValues.get("include_brep", IncludeBrep)
    IncludeTessellation = LegacyValues.get("include_tessellation", IncludeTessellation)
    Strict = LegacyValues.get("strict", Strict)
    UnknownValues = set(LegacyValues) - {
        "configuration",
        "include_brep",
        "include_tessellation",
        "strict",
    }
    if UnknownValues:
        Unexpected = next(iter(UnknownValues))
        raise TypeError(
            f"ReadSldprt() got an unexpected keyword argument {Unexpected!r}"
        )
    return SldprtAdapter().read(
        Source,
        ReadOptions(
            configuration=Config,
            include_brep=IncludeBrep,
            include_tessellation=IncludeTessellation,
            strict=Strict,
        ),
    )


# this definition exists because focused behavior needs one stable owner
def WriteSldprt(
    DocValue: CadDocument,
    Target: Destination,
    *,
    Overwrite: bool = False,
    Validate: bool = True,
    AllowNonNative: bool = True,
    **LegacyValues: object,
) -> WriteResult:
    AllowNonNative = LegacyValues.get("allow_non_native", AllowNonNative)
    UnknownValues = set(LegacyValues) - {"allow_non_native"}
    if UnknownValues:
        Unexpected = next(iter(UnknownValues))
        raise TypeError(
            f"WriteSldprt() got an unexpected keyword argument {Unexpected!r}"
        )
    return SldprtAdapter().write(
        DocValue,
        Target,
        WriteOptions(
            overwrite=Overwrite,
            validate=Validate,
            values=FrozenMapping({"allow_non_native": AllowNonNative}),
        ),
    )


# this definition exists because focused behavior needs one stable owner
def EmbeddedDoc(
    Adapter: SldprtAdapter,
    Archive: SldprtArchive,
    DataValue: bytes,
    Label: str,
    Embedded: bytes,
    Settings: ReadOptions,
) -> CadDoc:
    try:
        DocValue = CadDoc.from_json(Embedded.decode("utf-8"))
    except (UnicodeDecodeError, TypeError, ValueError) as ErrorInfo:
        raise SldprtFormatError("embedded Kit document is invalid") from ErrorInfo
    Configurations = DocValue.configurations
    if Settings.configuration is not None:
        Matches = {
            ItemValue.id
            for ItemValue in Configurations
            if Settings.configuration in {ItemValue.id, ItemValue.name}
        }
        if not Matches:
            raise SldprtFormatError(
                f"configuration {Settings.configuration!r} is unavailable"
            )
        Configurations = tuple(
            (
                Replace(ItemValue, active=ItemValue.id in Matches)
                for ItemValue in Configurations
            )
        )
    Original = DocValue.source
    FormatId = KAsmFormatId if DocValue.assembly is not None else KFormatId
    MetaValue = dict(DocValue.metadata)
    MetaValue.update(
        {
            "adapter": FormatId,
            "file_id": Archive.file_id,
            "stream_names": tuple((Record.name for Record in Archive.records)),
            "embedded_source_format_id": Original.format_id,
            "embedded_source_path": Original.path,
            "embedded_source_sha256": Original.sha256,
            "solidworks.container_compatibility": Replay(DataValue),
        }
    )
    DocValue = Replace(
        DocValue,
        source=CadSource(
            format_id=FormatId,
            path=Label,
            sha256=Hashlib.sha256(DataValue).hexdigest(),
            container_version=str(Archive.format_version),
            attributes=FrozenMapping(
                {
                    "file_id": Archive.file_id,
                    "stream_count": len(Archive.records),
                    "embedded_source_format_id": Original.format_id,
                }
            ),
        ),
        configurations=Configurations,
        metadata=FrozenMapping(MetaValue),
    )
    DocValue = FilterDoc(
        DocValue,
        include_brep=Settings.include_brep,
        include_tessellation=Settings.include_tessellation,
        keep_payload_records=False,
    )
    if Settings.strict:
        DocValue.assert_valid()
    return RetainSource(
        DocValue, DataValue, RetainCapabilities=True, OptionsValue=Settings
    )


# this definition exists because focused behavior needs one stable owner
def DocWithout(DocValue: CadDocument) -> CadDoc:
    return Replace(
        DocValue,
        metadata=FrozenMapping(
            {
                KeyValue: Value
                for KeyValue, Value in DocValue.metadata.items()
                if KeyValue not in KSourceKeys
            }
        ),
    )


# this definition exists because focused behavior needs one stable owner
def SemanticShaTwo(DocValue: CadDocument) -> str:
    Value = SemanticDoc(DocValue).to_json(indent=None).encode("utf-8")
    return Hashlib.sha256(Value).hexdigest()


# this definition exists because focused behavior needs one stable owner
def SemanticDoc(DocValue: CadDocument) -> CadDoc:
    EnvelopeIndexes = SourcePayloadIndexes(DocValue)
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
            for Index, Payload in enumerate(DocValue.brep_payloads)
            if Index not in EnvelopeIndexes
        )
    )
    AsmValue = DocValue.assembly
    if AsmValue is not None:
        AsmValue = Replace(
            AsmValue,
            documents=tuple(
                (
                    Replace(
                        ItemValue,
                        document=(
                            SemanticDoc(ItemValue.document)
                            if isinstance(ItemValue.document, CadDoc)
                            else ItemValue.document
                        ),
                    )
                    for ItemValue in AsmValue.documents
                )
            ),
        )
    return Replace(
        DocValue,
        source=CadSource("", "", ""),
        brep_payloads=Payloads,
        metadata=SemanticMeta(DocValue.metadata),
        assembly=AsmValue,
    )


# this definition exists because focused behavior needs one stable owner
def RetainSource(
    DocValue: CadDocument,
    DataValue: bytes,
    *,
    RetainCapabilities: bool = False,
    OptionsValue: ReadOptions | None = None,
) -> CadDoc:
    Capabilities = DocValue.capabilities
    SelectedOptions = OptionsValue or ReadOptions()
    Portable = DocWithout(DocValue)
    Portable = Replace(
        Portable, metadata=WithWrapperMeta(Portable.metadata, KWrapperMetaKeys)
    )
    SelectedCapabilities = (
        RetainedCapabilities(
            Portable,
            Capabilities,
            include_brep=SelectedOptions.include_brep,
            include_tessellation=SelectedOptions.include_tessellation,
        )
        if RetainCapabilities
        else InferCapabilities(Portable, roundtrip_metadata=True)
    )
    Portable = Replace(Portable, capabilities=SelectedCapabilities)
    MetaValue = dict(Portable.metadata)
    MetaValue.update(
        {
            KSourceBytesKey: bytes(DataValue),
            KSourceShaTwoFiveSixKey: Hashlib.sha256(DataValue).hexdigest(),
            KSourceSemanticShaTwoFive: SemanticShaTwo(Portable),
            KSourceFormatKey: DocValue.source.format_id,
        }
    )
    return Replace(Portable, metadata=WithWrapperMeta(MetaValue, KWrapperMetaKeys))


# this definition exists because focused behavior needs one stable owner
def IsGeomBrep(Payload: BrepPayload) -> bool:
    return Payload.role == PayloadRole.BREP and Payload.data is not None


# this definition exists because focused behavior needs one stable owner
def SavedSource(DocValue: CadDocument, Target: Path | None) -> bytes | None:
    DataValue = SourceTemplate(DocValue, Target)
    if DataValue is None:
        return None
    Semantic = DocValue.metadata.get(KSourceSemanticShaTwoFive)
    if Semantic != SemanticShaTwo(DocValue):
        return None
    if Replay(DataValue) == "native-exact" and (
        not IsNativeSourceD(DocValue, DataValue)
    ):
        return None
    return DataValue


# this definition exists because focused behavior needs one stable owner
def SourceTemplate(DocValue: CadDocument, Target: Path | None) -> bytes | None:
    DataValue = DocValue.metadata.get(KSourceBytesKey)
    if not isinstance(DataValue, bytes):
        return None
    Expected = DocValue.metadata.get(KSourceShaTwoFiveSixKey)
    if Expected != Hashlib.sha256(DataValue).hexdigest():
        return None
    SourceFormat = DocValue.metadata.get(KSourceFormatKey)
    if Target is not None:
        ExpectedSuffix = SuffixByFormatId.get(SourceFormat)
        if ExpectedSuffix is None or Target.suffix.casefold() != ExpectedSuffix:
            return None
    try:
        SldprtArchive.from_bytes(DataValue)
    except SldprtFormatError:
        return None
    return DataValue


# this definition exists because focused behavior needs one stable owner
def IsNativeSourceD(DocValue: CadDocument, DataValue: bytes) -> bool:
    Active = tuple((Config.name for Config in DocValue.configurations if Config.active))
    if len(Active) > 1:
        return False
    Source = BytesIo(DataValue)
    setattr(Source, "name", DocValue.source.path)
    try:
        Choice = SldprtAdapter().read(
            Source,
            ReadOptions(
                configuration=Active[0] if Active else None,
                include_brep=Capability.BREP in DocValue.capabilities,
                include_tessellation=Capability.TESSELLATION in DocValue.capabilities,
            ),
        )
    except (OSError, SldprtFormatError, TypeError, ValueError):
        return False
    return SemanticShaTwo(Choice) == SemanticShaTwo(DocValue)


# this definition exists because focused behavior needs one stable owner
def Required(DocValue: CadDocument) -> frozenset[Capability]:
    return DocValue.capabilities | InferCapabilities(
        DocValue,
        roundtrip_metadata=Capability.ROUNDTRIP_METADATA in DocValue.capabilities,
    )


# this state exists because bundle planning and emission share mutable results
@DataClass(slots=True)
class BundleState:
    Names: dict[str, str]
    Payloads: dict[PathValue, bytes]
    Stamps: dict[str, int]
    UsedNames: set[str]
    Complete: bool
    Capabilities: set[Capability]
    Targets: list[tuple[ComponentDefinition, CadDoc, str, PathValue, PathValue]]


# this definition exists because component documents may require nested extraction
def BundleComponent(
    DocValue: CadDocument,
    Definition: ComponentDefinition,
    Documents: Mapping[str, AnyValue],
) -> CadDoc | None:
    Component = Documents.get(Definition.document_id)
    if (
        not isinstance(Component, CadDoc)
        and str(Definition.kind) == ComponentKind.ASSEMBLY.value
    ):
        Component = NestedAsmDoc(DocValue, Definition.id)
    return Component if isinstance(Component, CadDoc) else None


# this definition exists because bundle members need unique vendor suffix names
def BundleNameMut(
    Definition: ComponentDefinition,
    Component: CadDocument,
    KeyValue: str,
    UsedNamesMut: set[str],
) -> str:
    Suffix = SuffixByFormatId[
        KAsmFormatId if Component.assembly is not None else KFormatId
    ]
    SourceName = PureWindowsPath(
        str(
            Definition.attributes.get("native_source_path")
            or Definition.source_path
            or Component.source.path
        )
    ).name
    Choice = PathValue(SourceName).name if SourceName else ""
    if PathValue(Choice).suffix.casefold() != Suffix:
        Choice = f"{Definition.name or KeyValue}{Suffix}"
    StemValue = PathValue(Choice).stem or "component"
    Index = 1
    while Choice.casefold() in UsedNamesMut:
        Index += 1
        Choice = f"{StemValue}-{Index}{Suffix}"
    UsedNamesMut.add(Choice.casefold())
    return Choice


# this definition exists because bundle planning assigns all cross document paths
def PlanBundleMut(
    DocValue: CadDocument,
    Definitions: Sequence[ComponentDefinition],
    Documents: Mapping[str, AnyValue],
    Target: PathValue,
    FinalPath: PathValue,
    StateMut: BundleState,
) -> None:
    for Definition in Definitions:
        KeyValue = Definition.document_id or Definition.id
        if KeyValue in StateMut.Names:
            StateMut.Names[Definition.id] = StateMut.Names[KeyValue]
            continue
        Component = BundleComponent(DocValue, Definition, Documents)
        if Component is None:
            StateMut.Complete = False
            continue
        Choice = BundleNameMut(Definition, Component, KeyValue, StateMut.UsedNames)
        TargetValue = (Target.parent / Choice).resolve()
        FinalTarget = (FinalPath.parent / Choice).resolve()
        TargetName = str(FinalTarget)
        StateMut.Names[KeyValue] = TargetName
        StateMut.Names[Definition.id] = TargetName
        if Definition.document_id:
            StateMut.Names[Definition.document_id] = TargetName
        StateMut.Targets.append(
            (Definition, Component, Choice, TargetValue, FinalTarget)
        )


# this predicate exists because nested members require emitted child stamps first
def IsBundleReady(
    TargetValue: tuple[ComponentDefinition, CadDoc, str, PathValue, PathValue],
    Names: Mapping[str, str],
    Stamps: Mapping[str, int],
) -> bool:
    Component = TargetValue[1]
    if Component.assembly is None:
        return True
    for ChildValue in Component.assembly.definitions:
        if ChildValue.id == Component.assembly.root_definition_id:
            continue
        ChildName = Names.get(ChildValue.document_id or ChildValue.id) or Names.get(
            ChildValue.id
        )
        if not ChildName or str(PureWindowsPath(ChildName)).casefold() not in Stamps:
            return False
    return True


# this definition exists because bundle member writes need isolated options
def BundleMember(
    Component: CadDocument,
    Choice: str,
    Settings: WriteOptions,
    Names: Mapping[str, str],
    Stamps: Mapping[str, int],
) -> tuple[AnyValue, bytes]:
    Buffer = BytesIo()
    Values = dict(Settings.values)
    Values["portable"] = False
    Values["bundle_member"] = Component.assembly is not None
    Values["bundle_names"] = FrozenMapping(Names)
    Values["bundle_stamps"] = FrozenMapping(Stamps)
    Values["model_name"] = PathValue(Choice).stem
    Result = SldprtAdapter().write(
        Component,
        Buffer,
        WriteOptions(
            overwrite=True, validate=Settings.validate, values=FrozenMapping(Values)
        ),
    )
    return (Result, Buffer.getvalue())


# this definition exists because bundle member bytes and stamps must stay atomic
def StoreMemberMut(
    Payload: bytes,
    TargetValue: PathValue,
    FinalTarget: PathValue,
    FinalOverwrite: bool,
    StateMut: BundleState,
) -> None:
    MemberArchive = SldprtArchive.from_bytes(Payload)
    StampData = MemberArchive.streams.get("ModelStamps", b"")
    if len(StampData) >= 4:
        StampKey = str(PureWindowsPath(FinalTarget)).casefold()
        StateMut.Stamps[StampKey] = Struct.unpack_from("<I", StampData)[0]
    if not FinalTarget.exists():
        StateMut.Payloads[TargetValue] = Payload
        return
    if FinalTarget.read_bytes() == Payload:
        return
    if not FinalOverwrite:
        raise FileExistsError(FinalTarget)
    StateMut.Payloads[TargetValue] = Payload


# this definition exists because dependency ordering needs deterministic selection
def FindReadyTarget(
    PendingTargets: Sequence[
        tuple[ComponentDefinition, CadDoc, str, PathValue, PathValue]
    ],
    State: BundleState,
) -> int | None:
    for TargetIndex, TargetValue in enumerate(PendingTargets):
        if IsBundleReady(TargetValue, State.Names, State.Stamps):
            return TargetIndex
    return None


# this definition exists because bundle emission mutates one accumulated result
def BuildBundleMut(
    Settings: WriteOptions,
    AvailableNames: set[str],
    FinalOverwrite: bool,
    StateMut: BundleState,
) -> None:
    PendingTargets = list(StateMut.Targets)
    while PendingTargets:
        ReadyIndex = FindReadyTarget(PendingTargets, StateMut)
        if ReadyIndex is None:
            StateMut.Complete = False
            ReadyIndex = 0
        Ignored, Component, Choice, TargetValue, FinalTarget = PendingTargets.pop(
            ReadyIndex
        )
        Result, Payload = BundleMember(
            Component, Choice, Settings, StateMut.Names, StateMut.Stamps
        )
        StoreMemberMut(Payload, TargetValue, FinalTarget, FinalOverwrite, StateMut)
        NativeResult = (
            Result.application_usable
            and Result.vendor_loadable
            and (not Result.requirements or IsBundleSatisfi(Component, AvailableNames))
        )
        if NativeResult:
            StateMut.Capabilities.update(Result.native_capabilities)
        else:
            StateMut.Complete = False


# this definition exists because focused behavior needs one stable owner
def AsmBundleA(
    DocValue: CadDocument, Target: Path, Settings: WriteOptions
) -> AsmBundle:
    AsmValue = DocValue.assembly
    if AsmValue is None:
        return AsmBundle({}, {}, {}, False)
    Definitions = tuple(
        (
            Definition
            for Definition in AsmValue.definitions
            if Definition.id != AsmValue.root_definition_id
        )
    )
    FinalValue = Settings.values.get("final_destination")
    FinalPath = (
        PathValue(FinalValue).expanduser().resolve()
        if isinstance(FinalValue, (str, PathValue))
        else Target
    )
    StateMut = BundleState({}, {}, {}, {Target.name.casefold()}, True, set(), [])
    Documents = {Component.id: Component.document for Component in AsmValue.documents}
    PlanBundleMut(DocValue, Definitions, Documents, Target, FinalPath, StateMut)
    AvailableNames = {
        PureWindowsPath(NameValue).name.casefold()
        for NameValue in StateMut.Names.values()
    }
    FinalOverwrite = (
        Settings.overwrite or Settings.values.get("final_overwrite") is True
    )
    BuildBundleMut(Settings, AvailableNames, FinalOverwrite, StateMut)
    if any(
        (
            (Definition.document_id or Definition.id) not in StateMut.Names
            for Definition in Definitions
        )
    ):
        StateMut.Complete = False
    return AsmBundle(
        FrozenMapping(StateMut.Names),
        FrozenMapping(StateMut.Payloads),
        FrozenMapping(StateMut.Stamps),
        StateMut.Complete,
        frozenset(StateMut.Capabilities),
    )


# this definition exists because nested assemblies need their transitive definitions
def ReachableDefs(AsmValue: AsmData, RootDefinitionId: str) -> set[str]:
    Reachable = {RootDefinitionId}
    Pending = [RootDefinitionId]
    while Pending:
        OwnerId = Pending.pop()
        for Instance in AsmValue.instances:
            if Instance.owner_definition_id != OwnerId:
                continue
            if Instance.definition_id not in Reachable:
                Reachable.add(Instance.definition_id)
                Pending.append(Instance.definition_id)
    return Reachable


# this definition exists because nested assembly subsets share one ownership boundary
def NestedAsmData(
    AsmValue: AsmData, RootDefinitionId: str, Reachable: set[str]
) -> tuple[AsmData, set[str]]:
    SelectedDefinitions = tuple(
        (
            (
                Replace(Definition, document_id="")
                if Definition.id == RootDefinitionId
                else Definition
            )
            for Definition in AsmValue.definitions
            if Definition.id in Reachable
        )
    )
    SelectedInstances = tuple(
        (
            Instance
            for Instance in AsmValue.instances
            if Instance.owner_definition_id in Reachable
            and Instance.definition_id in Reachable
        )
    )
    SelectedMates = tuple(
        (
            MateValue
            for MateValue in AsmValue.mates
            if MateValue.owner_definition_id in Reachable
        )
    )
    EntityIds = {
        EntityId for MateValue in SelectedMates for EntityId in MateValue.entity_ids
    }
    SelectedEntities = tuple(
        (
            Entity
            for Entity in AsmValue.mate_entities
            if Entity.id in EntityIds and Entity.owner_definition_id in Reachable
        )
    )
    SelectedGroups = tuple(
        (
            Group
            for Group in AsmValue.mate_groups
            if Group.owner_definition_id in Reachable
        )
    )
    DocIds = {
        Definition.document_id
        for Definition in SelectedDefinitions
        if Definition.id != RootDefinitionId and Definition.document_id
    }
    SelectedDocuments = tuple(
        (Component for Component in AsmValue.documents if Component.id in DocIds)
    )
    SelectedMeshIds = {
        MeshId for Definition in SelectedDefinitions for MeshId in Definition.mesh_ids
    }
    NestedAsm = AsmData(
        root_definition_id=RootDefinitionId,
        definitions=SelectedDefinitions,
        instances=SelectedInstances,
        documents=SelectedDocuments,
        mate_entities=SelectedEntities,
        mates=SelectedMates,
        mate_groups=SelectedGroups,
        attributes=AsmValue.attributes,
    )
    return (NestedAsm, SelectedMeshIds)


# this definition exists because nested mates need owner scoped binary payloads
def NestedPayloads(
    DocValue: CadDocument, RootDefinitionId: str
) -> tuple[BrepPayload, ...]:
    SelectedPayloads: list[BrepPayload] = []
    NativeRootId = NativeId(RootDefinitionId, "sldasm:definition:")
    if NativeRootId is not None:
        for Payload in DocValue.brep_payloads:
            if (
                Payload.role is not PayloadRole.ASSEMBLY_STRUCTURE
                or Payload.format_id.casefold() != "solidworks.mates"
                or Payload.data is None
            ):
                continue
            try:
                OwnerId = int(Payload.attributes.get("owner_definition_id", -1))
            except (TypeError, ValueError):
                continue
            if OwnerId != NativeRootId:
                continue
            SourceStream = Payload.source_stream.rsplit("::", 1)[-1]
            SelectedPayloads.append(Replace(Payload, source_stream=SourceStream))
    return tuple(SelectedPayloads)


# this definition exists because focused behavior needs one stable owner
def NestedAsmDoc(DocValue: CadDocument, RootDefinitionId: str) -> CadDoc | None:
    AsmValue = DocValue.assembly
    if AsmValue is None:
        return None
    Definitions = {Definition.id: Definition for Definition in AsmValue.definitions}
    RootValue = Definitions.get(RootDefinitionId)
    if RootValue is None or str(RootValue.kind) != ComponentKind.ASSEMBLY.value:
        return None
    Reachable = ReachableDefs(AsmValue, RootDefinitionId)
    NestedAsm, SelectedMeshIds = NestedAsmData(AsmValue, RootDefinitionId, Reachable)
    SelectedPayloads = NestedPayloads(DocValue, RootDefinitionId)
    SourcePath = RootValue.source_path or f"{RootValue.name}.SLDASM"
    Nested = Replace(
        DocValue,
        source=CadSource(KAsmFormatId, SourcePath, ""),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep=None,
        brep_payloads=tuple(SelectedPayloads),
        meshes=tuple(
            (
                MeshValue
                for MeshValue in DocValue.meshes
                if MeshValue.id in SelectedMeshIds
            )
        ),
        assembly=NestedAsm,
        metadata=FrozenMapping(
            {
                KeyValue: Value
                for KeyValue, Value in DocValue.metadata.items()
                if KeyValue not in KSourceKeys
            }
        ),
    )
    return Replace(
        Nested,
        capabilities=InferCapabilities(
            Nested,
            roundtrip_metadata=Capability.ROUNDTRIP_METADATA in DocValue.capabilities,
        ),
    )


# this definition exists because focused behavior needs one stable owner
def IsBundleSatisfi(DocValue: CadDocument, AvailableNames: set[str]) -> bool:
    if DocValue.assembly is None:
        return True
    for Definition in DocValue.assembly.definitions:
        if Definition.id == DocValue.assembly.root_definition_id:
            continue
        Source = str(
            Definition.attributes.get("native_source_path") or Definition.source_path
        )
        NameValue = PureWindowsPath(Source).name.casefold()
        if not NameValue or NameValue not in AvailableNames:
            return False
    return True


# this definition exists because focused behavior needs one stable owner
def SolidworksA(
    Required: frozenset[Capability],
    Native: frozenset[Capability],
    Mixed: frozenset[Capability] = frozenset(),
) -> tuple[CapabilityTransfer, ...]:

    # this callback exists because local behavior needs one focused transformation
    return tuple(
        (
            CapabilityTransfer(
                Capability,
                (
                    TransferMode.NATIVE
                    if Capability in Native
                    else (
                        TransferMode.MIXED
                        if Capability in Mixed
                        else TransferMode.CARRIER
                    )
                ),
                (
                    None
                    if Capability in Native
                    else (
                        CarrierReason.TARGET_UNSUPPORTED
                        if Capability in Mixed or Capability in KTargetUnsupported
                        else CarrierReason.WRITER_UNIMPLEMENTED
                    )
                ),
            )
            for Capability in sorted(Required, key=lambda Value: Value.value)
        )
    )


# this definition exists because focused behavior needs one stable owner
def NativeStreamSha(Streams: Mapping[str, bytes]) -> str:
    Digest = Hashlib.sha256()

    # this callback exists because local behavior needs one focused transformation
    for NameValue in sorted(
        (
            NameValue
            for NameValue in Streams
            if NameValue not in {KitDocStream, KitNativeStream}
        ),
        key=lambda Value: (Value.casefold(), Value),
    ):
        Encoded = NameValue.encode("utf-8")
        DataValue = Streams[NameValue]
        Digest.update(Struct.pack(">I", len(Encoded)))
        Digest.update(Encoded)
        Digest.update(Struct.pack(">Q", len(DataValue)))
        Digest.update(DataValue)
    return Digest.hexdigest()


# this definition exists because focused behavior needs one stable owner
def NativeBytes(
    Streams: Mapping[str, bytes],
    Compatibility: str,
    AppUsable: bool,
    VendorLoadable: bool,
    Transfers: tuple[CapabilityTransfer, ...],
    NativeBrep: str,
) -> bytes:
    Embedded = Streams[KitDocStream]
    DocValue = CadDoc.from_json(Embedded.decode("utf-8"))
    Value = {
        "version": 2,
        "compatibility": Compatibility,
        "application_usable": AppUsable,
        "vendor_loadable": VendorLoadable,
        "native_brep": NativeBrep,
        "native_stream_sha256": NativeStreamSha(Streams),
        "embedded_sha256": Hashlib.sha256(Embedded).hexdigest(),
        "semantic_sha256": SemanticShaTwo(DocValue),
        "transfers": [
            {
                "capability": Transfer.capability.value,
                "mode": Transfer.mode.value,
                "carrier_reason": (
                    Transfer.carrier_reason.value
                    if Transfer.carrier_reason is not None
                    else None
                ),
            }
            for Transfer in Transfers
        ],
    }
    return JsonValue.dumps(Value, sort_keys=True, separators=(",", ":")).encode("utf-8")


# this definition exists because attestation envelopes need authenticated decoding
def NativeEnvelope(
    DataValue: bytes,
) -> tuple[SldprtArchive, dict[str, AnyValue], CadDocument] | None:
    try:
        Archive = SldprtArchive.from_bytes(DataValue)
        RawValue = Archive.require(KitNativeStream)
        Embedded = Archive.require(KitDocStream)
        Value = JsonValue.loads(RawValue.decode("utf-8"))
        DocValue = CadDoc.from_json(Embedded.decode("utf-8"))
    except (KeyError, SldprtFormatError, TypeError, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(Value, dict) or Value.get("version") != 2:
        return None
    if Value.get("embedded_sha256") != Hashlib.sha256(Embedded).hexdigest():
        return None
    if Value.get("semantic_sha256") != SemanticShaTwo(DocValue):
        return None
    if Value.get("native_stream_sha256") != NativeStreamSha(Archive.streams):
        return None
    if not isinstance(Value.get("application_usable"), bool) or not isinstance(
        Value.get("vendor_loadable"), bool
    ):
        return None
    if Value["application_usable"] and (not Value["vendor_loadable"]):
        return None
    Compatibility = Value.get("compatibility")
    if (
        not isinstance(Compatibility, str)
        or Compatibility not in KAttestedCompatibilities
    ):
        return None
    return (Archive, Value, DocValue)


# this definition exists because capability records need exact typed decoding
def ParseTransfers(
    Value: Mapping[str, AnyValue],
) -> tuple[CapabilityTransfer, ...] | None:
    Records = Value.get("transfers")
    if not isinstance(Records, list):
        return None
    try:
        Parsed = tuple(
            (
                CapabilityTransfer(
                    Capability(Record["capability"]),
                    TransferMode(Record["mode"]),
                    (
                        CarrierReason(Record["carrier_reason"])
                        if Record.get("carrier_reason") is not None
                        else None
                    ),
                )
                for Record in Records
                if isinstance(Record, dict)
            )
        )
    except (KeyError, TypeError, ValueError):
        return None
    if len(Parsed) != len(Records) or len(
        {ItemValue.capability for ItemValue in Parsed}
    ) != len(Parsed):
        return None
    return Parsed


# this predicate exists because regenerated proof must match every attested claim
def IsProofMatch(
    Value: Mapping[str, AnyValue],
    Compatibility: str,
    Proof: Generated,
) -> bool:
    return (
        Compatibility == Proof.compatibility
        and Value["application_usable"] is Proof.application_usable
        and Value["vendor_loadable"] is Proof.vendor_loadable
        and (Value.get("native_brep") == Proof.native_brep)
    )


# this definition exists because focused behavior needs one stable owner
def Native(DataValue: bytes) -> dict[str, AnyValue] | None:
    Envelope = NativeEnvelope(DataValue)
    if Envelope is None:
        return None
    Archive, Value, DocValue = Envelope
    Parsed = ParseTransfers(Value)
    if Parsed is None:
        return None
    Compatibility = str(Value["compatibility"])
    AttestedNativeCaps = frozenset(
        (
            TransferItem.capability
            for TransferItem in Parsed
            if TransferItem.mode is TransferMode.NATIVE
        )
    )
    Proof = AttestedNative(DocValue, Archive, Compatibility, AttestedNativeCaps)
    if Proof is None:
        return None
    ExpectedTransfers = SolidworksA(
        Required(DocValue), Proof.native_capabilities, Proof.mixed_capabilities
    )
    if Parsed != ExpectedTransfers or not IsProofMatch(Value, Compatibility, Proof):
        return None
    Value["parsed_transfers"] = Parsed
    return Value


# this definition exists because focused behavior needs one stable owner
def AttestedNative(
    DocValue: CadDocument,
    Archive: SldprtArchive,
    Compatibility: str,
    AttestedNativeCaps: frozenset[Capability],
) -> Generated | None:
    Streams = Archive.streams
    Before = NativeStreamSha(Streams)
    BundleNames = AttestedBundle(DocValue, Archive)
    try:
        if Compatibility in {
            "native-brep-with-kit-neutral",
            "native-metadata-with-kit-neutral",
        }:
            Proof = GeneratedB(
                DocValue,
                BundleNames=BundleNames,
                BundleComplete=Capability.COMPONENT_DOCUMENTS in AttestedNativeCaps,
                BundleCapabilities=AttestedNativeCaps,
            )
        elif KeywordsStream in Streams and ResolvedFeaturesStream in Streams:
            Proof = PatchNativeMut(DocValue, Streams, {})
        else:
            Proof = GeneratedB(
                DocValue,
                BundleNames=BundleNames,
                BundleComplete=Capability.COMPONENT_DOCUMENTS in AttestedNativeCaps,
                BundleCapabilities=AttestedNativeCaps,
            )
    except (KeyError, SldprtFormatError, TypeError, ValueError, Struct.error):
        return None
    if NativeStreamSha(Proof.streams) != Before:
        return None
    return Proof


# this definition exists because focused behavior needs one stable owner
def AttestedBundle(DocValue: CadDocument, Archive: SldprtArchive) -> Mapping[str, str]:
    AsmValue = DocValue.assembly
    if AsmValue is None or ComponentTreeStream not in Archive.streams:
        return {}
    RootName = AsmValue.definition(AsmValue.root_definition_id).name
    ModelName = RootName or PureWindowsPath(DocValue.source.path).stem or "Assembly"
    try:
        Encoding = EncodeNativeAsm(AsmValue, DocValue.configurations, ModelName)
        Native = DecodeNativeAsm(Archive, include_tessellation=False)
    except (KeyError, SldprtFormatError, TypeError, ValueError, Struct.error):
        return {}
    Definitions = {ItemValue.object_id: ItemValue for ItemValue in Native.definitions}
    Result: dict[str, str] = {}
    for Definition in AsmValue.definitions:
        if Definition.id == AsmValue.root_definition_id:
            continue
        NativeId = Encoding.definition_ids.get(Definition.id)
        Target = Definitions.get(NativeId) if NativeId is not None else None
        if Target is None or not Target.source_path:
            continue
        Result[Definition.id] = Target.source_path
        if Definition.document_id:
            Result[Definition.document_id] = Target.source_path
    return Result


# this definition exists because focused behavior needs one stable owner
def Attested(
    Attestation: Mapping[str, Any], Required: frozenset[Capability]
) -> tuple[CapabilityTransfer, ...]:
    Parsed = Attestation.get("parsed_transfers")
    if not isinstance(Parsed, tuple):
        return SolidworksA(Required, frozenset())
    ByCapability = {ItemValue.capability: ItemValue for ItemValue in Parsed}
    if set(ByCapability) != set(Required):
        return SolidworksA(Required, frozenset())

    # this callback exists because local behavior needs one focused transformation
    return tuple(
        (
            ByCapability[Capability]
            for Capability in sorted(Required, key=lambda Value: Value.value)
        )
    )


# this definition exists because focused behavior needs one stable owner
def Replay(DataValue: bytes) -> str:
    Archive = SldprtArchive.from_bytes(DataValue)
    if KitDocStream not in Archive.streams:
        return "native-exact"
    Attestation = Native(DataValue)
    return (
        str(Attestation["compatibility"])
        if Attestation is not None
        else "kit-neutral-only"
    )


# this state exists because native generation has format specific branches
@DataClass(slots=True)
class GeneratedState:
    Streams: dict[str, bytes]
    Encoding: NativeAsmEncoding | None = None
    PartCapabilities: frozenset[Capability] = frozenset()
    MixedCapabilities: frozenset[Capability] = frozenset()
    PartPartition: bytes | None = None
    PartObjectIds: Mapping[str, int] = Field(default_factory=FrozenMapping)
    PartAppUsable: bool = False
    PartVendorLoadable: bool = False
    PartDonorNotes: tuple[str, ...] = ()
    AsmEnvelopeComplete: bool = False
    AsmNotes: tuple[str, ...] = ()


# this definition exists because source envelopes must not duplicate embedded payloads
def PortableDoc(DocValue: CadDocument) -> CadDocument:
    Portable = DocWithout(DocValue)
    if isinstance(DocValue.source.attributes.get("embedded_source_format_id"), str):
        EnvelopeIndexes = SourcePayloadIndexes(DocValue)
        Portable = Replace(
            Portable,
            brep_payloads=tuple(
                (
                    Payload
                    for Index, Payload in enumerate(Portable.brep_payloads)
                    if Index not in EnvelopeIndexes
                )
            ),
        )
    return Portable


# this definition exists because native part streams have one cohesive encoder
def BuildPartMut(
    Portable: CadDocument, ModelName: str, StateMut: GeneratedState
) -> None:
    PartValue = EncodeNativePart(Portable, ModelName)
    StateMut.Streams.update(PartValue.envelope_streams)
    StateMut.Streams[KeywordsStream] = PartValue.keywords
    StateMut.Streams[FeaturesStream] = PartValue.features
    StateMut.Streams.update(
        {
            f"Contents/Config-{Index}-ResolvedFeatures": LaneValue
            for Index, LaneValue in PartValue.configuration_lanes
        }
    )
    if PartValue.kit_resolved_features is not None:
        StateMut.Streams[KitResolvedStream] = PartValue.kit_resolved_features
    StateMut.PartCapabilities = PartValue.native_capabilities
    StateMut.MixedCapabilities = PartValue.mixed_capabilities
    StateMut.PartPartition = PartValue.partition
    StateMut.PartObjectIds = PartValue.object_ids
    StateMut.PartAppUsable = PartValue.application_usable
    StateMut.PartVendorLoadable = PartValue.vendor_loadable
    StateMut.PartDonorNotes = PartValue.donor_notes


# this definition exists because native assembly streams require coordinated records
def BuildAsmMut(
    Portable: CadDocument,
    ModelName: str,
    BundleNames: Mapping[str, str] | None,
    BundleStamps: Mapping[str, int] | None,
    StateMut: GeneratedState,
) -> None:
    AsmValue = Portable.assembly
    if AsmValue is None:
        return
    RootName = AsmValue.definition(AsmValue.root_definition_id).name
    AsmName = RootName or ModelName or "Assembly"
    Encoding = EncodeNativeAsm(AsmValue, Portable.configurations, AsmName, BundleNames)
    SavedMates, MatesComplete = SavedGenerated(Portable, Encoding)
    if MatesComplete:
        Encoding = Replace(
            Encoding,
            mate_streams=SavedMates,
            mates_complete=True,
            unsupported_mate_ids=(),
            generated_mate_ids=(),
        )
    Envelope = EncodeNativeAsmEnvelope(
        Portable,
        AsmName,
        GeneratedItem(AsmValue),
        tuple((MateValue.name for MateValue in AsmValue.mates)),
    )
    StateMut.Streams.update(Envelope.streams)
    StateMut.Streams[ComponentTreeStream] = Encoding.component_tree
    try:
        StateMut.Streams.update(
            AsmCoreStreams(AsmValue, Encoding, AsmName, BundleStamps)
        )
        CoreError = ""
    except SldprtFormatError as ErrorData:
        CoreError = str(ErrorData)
    StateMut.Streams.update(Encoding.mate_streams)
    StateMut.Encoding = Encoding
    StateMut.AsmEnvelopeComplete = Envelope.envelope_complete
    StateMut.AsmNotes = (
        *GeneratedAsmA(Encoding, Envelope, StateMut.Streams),
        *((f"native_assembly_core_declined:{CoreError}",) if CoreError else ()),
    )


# this definition exists because geometry selection bridges part and neutral encoders
def BuildGeomMut(
    Portable: CadDocument, StateMut: GeneratedState
) -> tuple[bytes | None, str]:
    if StateMut.PartPartition is not None:
        Payload = StateMut.PartPartition
        NativeBrep = "generated"
    else:
        Payload, NativeBrep = Parasolid(Portable, StateMut.PartObjectIds)
        if (
            Portable.assembly is None
            and StateMut.PartVendorLoadable
            and (Capability.BREP in StateMut.PartCapabilities)
        ):
            Payload = None
            NativeBrep = "feature-rebuilt"
    if Payload is not None:
        StateMut.Streams[PartitionStream] = Payload
    return (Payload, NativeBrep)


# this definition exists because generated capability proof has multiple carriers
def GeneratedCaps(
    Portable: CadDocument,
    State: GeneratedState,
    Payload: bytes | None,
    NativeBrep: str,
    BundleNames: Mapping[str, str] | None,
    BundleComplete: bool | None,
    BundleCapabilities: frozenset[Capability],
) -> frozenset[Capability]:
    NativeCaps = set(
        GeneratedAsm(
            Portable.assembly, State.Encoding, State.Streams, Portable.configurations
        )
        if Portable.assembly is not None and State.Encoding is not None
        else State.PartCapabilities
    )
    if (
        Portable.assembly is not None
        and (BundleComplete if BundleComplete is not None else BundleNames is not None)
        and all(
            (
                DefinitionItem.id == Portable.assembly.root_definition_id
                or DefinitionItem.document_id in BundleNames
                or DefinitionItem.id in BundleNames
                for DefinitionItem in Portable.assembly.definitions
            )
        )
    ):
        NativeCaps.add(Capability.COMPONENT_DOCUMENTS)
        NativeCaps.update(BundleCapabilities)
    if (
        Portable.assembly is None
        and Payload is not None
        and (NativeBrep in {"generated", "preserved"})
    ):
        NativeCaps.update({Capability.BREP, Capability.NATIVE_PAYLOADS})
    return frozenset(NativeCaps)


# this definition exists because final usability depends on attested native records
def GeneratedProof(
    Portable: CadDocument,
    State: GeneratedState,
    NativeBrep: str,
    NativeCapabilities: frozenset[Capability],
) -> Generated:
    ProofTransfers = SolidworksA(
        Required(Portable), NativeCapabilities, State.MixedCapabilities
    )
    NativeAsmRecords = (
        Portable.assembly is not None
        and State.AsmEnvelopeComplete
        and (State.Encoding is not None)
        and State.Encoding.structure_complete
        and (Capability.ASSEMBLIES in NativeCapabilities)
    )
    if Portable.assembly is None:
        VendorLoadable = State.PartVendorLoadable
        NativeRecordsUsable = State.PartAppUsable
    else:
        VendorLoadable = NativeAsmRecords and (not AsmReaderGaps(State.Streams))
        NativeRecordsUsable = VendorLoadable and (
            not Portable.assembly.mates
            or Capability.ASSEMBLY_MATES in NativeCapabilities
        )
    AppUsable = NativeRecordsUsable and all(
        (
            Transfer.mode is TransferMode.NATIVE
            or Transfer.carrier_reason is CarrierReason.TARGET_UNSUPPORTED
            for Transfer in ProofTransfers
        )
    )
    return Generated(
        State.Streams,
        NativeBrep,
        NativeCapabilities,
        (
            "native-brep-with-kit-neutral"
            if NativeBrep in {"generated", "preserved"}
            else (
                "native-metadata-with-kit-neutral"
                if Portable.assembly is None
                else (
                    "native-assembly-with-kit-neutral"
                    if NativeAsmRecords
                    else "kit-neutral-only"
                )
            )
        ),
        AppUsable,
        VendorLoadable,
        State.MixedCapabilities,
        State.AsmNotes,
        State.PartDonorNotes,
        AsmReaderGaps(State.Streams) if Portable.assembly is not None else (),
    )


# this definition exists because focused behavior needs one stable owner
def GeneratedB(
    DocValue: CadDocument,
    Template: bytes | None = None,
    BundleNames: Mapping[str, str] | None = None,
    BundleComplete: bool | None = None,
    BundleCapabilities: frozenset[Capability] = frozenset(),
    BundleStamps: Mapping[str, int] | None = None,
    ModelName: str = "",
) -> Generated:
    Portable = PortableDoc(DocValue)
    Embedded = Portable.to_json(indent=None).encode("utf-8")
    if Template is not None:
        Streams = SldprtArchive.from_bytes(Template).streams
        Streams[KitDocStream] = Embedded
        return PatchNativeMut(DocValue, Streams, BundleNames or {})
    Config = next(
        (ItemValue.name for ItemValue in Portable.configurations if ItemValue.active),
        Portable.configurations[0].name if Portable.configurations else "Default",
    )
    ModelNameA = ModelName or PureWindowsPath(Portable.source.path).stem
    Streams = {
        **Solidworks(),
        SolidworksStream: SolidworksXml(ModelNameA, Config),
        KitDocStream: Embedded,
    }
    StateMut = GeneratedState(Streams)
    if Portable.assembly is None:
        BuildPartMut(Portable, ModelNameA, StateMut)
    else:
        BuildAsmMut(Portable, ModelNameA, BundleNames, BundleStamps, StateMut)
    Payload, NativeBrep = BuildGeomMut(Portable, StateMut)
    NativeCapabilities = GeneratedCaps(
        Portable,
        StateMut,
        Payload,
        NativeBrep,
        BundleNames,
        BundleComplete,
        BundleCapabilities,
    )
    return GeneratedProof(Portable, StateMut, NativeBrep, NativeCapabilities)


# this definition exists because focused behavior needs one stable owner
def AsmReaderGaps(
    Streams: Mapping[str, bytes],
    Donor: Mapping[str, bytes] | None = None,
    Rewritable: frozenset[str] = frozenset(),
) -> tuple[str, ...]:
    GapsValue = [
        f"absent_vendor_stream:{NameValue}"
        for NameValue in KAsmReaderRequiredStreams
        if NameValue not in Streams
    ]
    if Donor is None:
        return tuple(GapsValue)
    GapsValue.extend(
        (
            f"donor_stream_absent:{NameValue}"
            for NameValue in KAsmDonorCarriedStreams
            if NameValue not in Donor
        )
    )
    for NameValue in sorted(set(Streams) | set(Donor)):
        if NameValue in Rewritable:
            continue
        if NameValue not in Donor:
            GapsValue.append(f"donor_stream_added:{NameValue}")
        elif NameValue not in Streams:
            GapsValue.append(f"donor_stream_removed:{NameValue}")
        elif Streams[NameValue] != Donor[NameValue]:
            GapsValue.append(f"donor_stream_rewritten:{NameValue}")
    return tuple(GapsValue)


# this definition exists because focused behavior needs one stable owner
def GeneratedAsmA(
    Encoding: NativeAssemblyEncoding,
    Envelope: NativeAssemblyEnvelope,
    Streams: Mapping[str, bytes],
) -> tuple[str, ...]:
    Counts: Counter[str] = Counter()
    for Reasons in Encoding.unsupported_mate_reasons.values():
        Counts.update(Reasons)
    for Reasons in Encoding.generated_mate_losses.values():
        Counts.update(Reasons)
    Notes = [f"{Reason}:{Count}" for Reason, Count in sorted(Counts.items())]
    if Envelope.omitted_object_names:
        Notes.append(
            f"header_object_name_unencodable:{len(Envelope.omitted_object_names)}"
        )
    if not Encoding.structure_complete:
        Notes.append("component_structure_incomplete:1")
    if Encoding.generated_mate_ids:
        Notes.append(
            f"vendor_unread_synthesised_mate:{len(Encoding.generated_mate_ids)}"
        )
    return tuple(Notes)


# this definition exists because focused behavior needs one stable owner
def GeneratedItem(AsmValue: AssemblyData) -> tuple[str, ...]:
    Labels: list[str] = []
    for Index, Instance in enumerate(AsmValue.instances):
        RefValue = GeneratedRef(Instance, Index + 1)
        Suffix = f"-{RefValue}"
        BaseName = (
            Instance.name[: -len(Suffix)]
            if Instance.name.endswith(Suffix)
            else Instance.name
        )
        Labels.append(f"{BaseName}{Suffix}")
    return tuple(Labels)


# this definition exists because focused behavior needs one stable owner
def HasAffineFrame(MatrixValues: tuple[float, ...]) -> bool:
    return (
        len(MatrixValues) == 16
        and all((MathValue.isfinite(MatrixValue) for MatrixValue in MatrixValues))
        and all(
            (
                MathValue.isclose(
                    MatrixValues[ValueIndex], ExpectedValue, rel_tol=0.0, abs_tol=1e-12
                )
                for ValueIndex, ExpectedValue in zip(
                    (12, 13, 14, 15), (0.0, 0.0, 0.0, 1.0), strict=True
                )
            )
        )
    )


# this definition exists because focused behavior needs one stable owner
def AsmCoreStreams(
    AsmValue: AssemblyData,
    EncodingValue: NativeAssemblyEncoding,
    ModelName: str,
    StampValues: Mapping[str, int] | None = None,
) -> Mapping[str, bytes]:
    DirectItems = AsmValue.children(AsmValue.root_definition_id)
    if not DirectItems:
        raise SldprtFormatError(
            "first-principles assembly history requires a direct component"
        )
    XmlRoot = XmlTree.fromstring(EncodingValue.component_tree)
    XmlSpace = {"sw": "http://www.solidworks.com/sw2003/schema"}
    OccurNames = GeneratedItem(AsmValue)
    CoreItems: list[AsmCoreItem] = []
    StampMap = StampValues or {}
    ConfigName = ""
    for InstanceItem in DirectItems:
        InstanceIndex = AsmValue.instances.index(InstanceItem)
        TargetId = EncodingValue.definition_ids[InstanceItem.definition_id]
        ModelNode = next(
            (
                NodeItem
                for NodeItem in XmlRoot.findall("sw:swModelList/sw:swModel", XmlSpace)
                if NodeItem.attrib.get("id") == str(TargetId)
            ),
            None,
        )
        if ModelNode is None:
            raise SldprtFormatError(
                "assembly component model is absent from native tree"
            )
        FileId = ModelNode.attrib.get("swFileRef", "")
        FileNode = next(
            (
                NodeItem
                for NodeItem in XmlRoot.findall("sw:swHeader/sw:swFile", XmlSpace)
                if NodeItem.attrib.get("id") == FileId
            ),
            None,
        )
        if FileNode is None or not (CompPath := FileNode.attrib.get("swPath", "")):
            raise SldprtFormatError(
                "assembly component file is absent from native tree"
            )
        InstanceConfig = (
            InstanceItem.configuration_name
            or AsmValue.definition(InstanceItem.definition_id).configuration_name
        )
        if not ConfigName:
            ConfigName = "Default"
        MatrixValues = InstanceItem.transform.values
        if not HasAffineFrame(MatrixValues):
            raise SldprtFormatError(
                "native assembly history requires an affine component transform"
            )
        CoreItems.append(
            AsmCoreItem(
                OccurNames[InstanceIndex],
                CompPath,
                MatrixValues[3] / 1000.0,
                MatrixValues[7] / 1000.0,
                MatrixValues[11] / 1000.0,
                InstanceConfig or "Default",
                StampMap.get(str(PureWindowsPath(CompPath)).casefold(), 0),
                (
                    MatrixValues[0],
                    MatrixValues[4],
                    MatrixValues[8],
                    MatrixValues[1],
                    MatrixValues[5],
                    MatrixValues[9],
                    MatrixValues[2],
                    MatrixValues[6],
                    MatrixValues[10],
                ),
            )
        )
    return EncodeAsmCore(ModelName, ConfigName, tuple(CoreItems))


# this definition exists because saved mate streams need strict donor selection
def SavedMateLists(
    DocValue: CadDocument, RootId: int
) -> dict[str, tuple[BrepPayload, NativeMateList]]:
    Candidates: dict[str, tuple[BrepPayload, NativeMateList]] = {}
    for Payload in DocValue.brep_payloads:
        if (
            Payload.role is not PayloadRole.ASSEMBLY_STRUCTURE
            or Payload.format_id.casefold() != "solidworks.mates"
            or Payload.data is None
            or ("::" in Payload.source_stream)
        ):
            continue
        LeafValue = Payload.source_stream.replace("\\", "/").rsplit("/", 1)[-1]
        if LeafValue.casefold() != MatesStreamName.casefold() and (
            not LeafValue.casefold().endswith(MatesStreamSuffix.casefold())
        ):
            continue
        try:
            OwnerId = int(Payload.attributes.get("owner_definition_id", -1))
            Decoded = DecodeMateList(Payload.data, Payload.source_stream, OwnerId)
        except (SldprtFormatError, TypeError, ValueError, Struct.error):
            continue
        if OwnerId != RootId or Payload.source_stream in Candidates:
            continue
        Candidates[Payload.source_stream] = (Payload, Decoded)
    return Candidates


# this predicate exists because saved mate payload ownership must be complete
def IsSavedPayloads(
    AsmValue: AsmData,
    Candidates: Mapping[str, tuple[BrepPayload, NativeMateList]],
) -> bool:
    PayloadIds = {Payload.id for Payload, Ignored in Candidates.values()}
    DesiredPayloadIds = {
        str(Value)
        for Value in (
            *(
                MateValue.attributes.get("native_payload_id")
                for MateValue in AsmValue.mates
            ),
            *(
                Group.attributes.get("native_payload_id")
                for Group in AsmValue.mate_groups
            ),
        )
        if isinstance(Value, str) and Value
    }
    return DesiredPayloadIds == PayloadIds


# this predicate exists because saved mate records must match neutral semantics
def IsSavedMatches(
    AsmValue: AsmData,
    Candidates: Mapping[str, tuple[BrepPayload, NativeMateList]],
) -> bool:
    DesiredMates = {
        (
            str(MateValue.attributes.get("native_payload_id", "")),
            GeneratedA(MateValue.attributes.get("native_record_offset")),
        ): MateValue
        for MateValue in AsmValue.mates
    }
    DesiredEntities = {Entity.id: Entity for Entity in AsmValue.mate_entities}
    MatchedMates: set[str] = set()
    MatchedGroupOffsets: set[tuple[str, int]] = set()
    for Payload, MateList in Candidates.values():
        for NativeMate in MateList.mates:
            KeyValue = (Payload.id, NativeMate.record_offset)
            if NativeMate.kind == "group":
                MatchedGroupOffsets.add(KeyValue)
                continue
            MateValue = DesiredMates.get(KeyValue)
            if MateValue is None or not IsSavedNativeMa(
                MateValue, NativeMate, DesiredEntities
            ):
                return False
            MatchedMates.add(MateValue.id)
    if MatchedMates != {MateValue.id for MateValue in AsmValue.mates}:
        return False
    ExpectedGroupOffsets = {
        (
            str(Group.attributes.get("native_payload_id", "")),
            GeneratedA(Group.attributes.get(NameValue)),
        )
        for Group in AsmValue.mate_groups
        for NameValue in ("start_record_offset", "end_record_offset")
    }
    return MatchedGroupOffsets == ExpectedGroupOffsets


# this definition exists because focused behavior needs one stable owner
def SavedGenerated(
    DocValue: CadDocument, Encoding: NativeAssemblyEncoding
) -> tuple[dict[str, bytes], bool]:
    AsmValue = DocValue.assembly
    if AsmValue is None or Encoding.mates_complete:
        return (dict(Encoding.mate_streams), Encoding.mates_complete)
    RootId = Encoding.definition_ids[AsmValue.root_definition_id]
    Candidates = SavedMateLists(DocValue, RootId)
    if (
        not Candidates
        or not IsSavedPayloads(AsmValue, Candidates)
        or not IsSavedMatches(AsmValue, Candidates)
    ):
        return ({}, False)
    return (
        {
            Payload.source_stream: bytes(Payload.data)
            for Payload, Ignored in Candidates.values()
        },
        True,
    )


# this definition exists because focused behavior needs one stable owner
def IsSavedNativeMa(
    MateValue: MateConstraint, Native: NativeMate, Entities: Mapping[str, MateEntity]
) -> bool:
    if (
        MateValue.name != Native.name
        or MateValue.kind != NeutralMateKinA(Native.kind)
        or MateValue.alignment != NeutralMate(Native)
        or (MateParamValue(MateValue.value) != MateParamValue(NeutralMateA(Native)))
        or MateValue.suppressed
        or (not MateValue.driving)
        or MateValue.parameter_ids
        or (len(MateValue.entity_ids) != len(Native.entities))
    ):
        return False
    for EntityId, NativeEntity in zip(MateValue.entity_ids, Native.entities):
        Entity = Entities.get(EntityId)
        if Entity is None:
            return False
        ComponentPath = Entity.attributes.get("component_path", "")
        Persistent = Entity.attributes.get("persistent_references", ())
        if (
            ComponentPath != NativeEntity.component_path
            or Persistent != NativeEntity.persistent_references
            or Entity.source_entity_id
            != (
                NativeEntity.persistent_references[-1]
                if NativeEntity.persistent_references
                else ""
            )
        ):
            return False
    return True


# this definition exists because focused behavior needs one stable owner
def GeneratedAsm(
    AsmValue: AssemblyData,
    Encoding: NativeAssemblyEncoding,
    Streams: Mapping[str, bytes],
    Configurations: Sequence[Configuration],
) -> frozenset[Capability]:
    try:
        Native = DecodeNativeAsm(
            SldprtArchive.from_bytes(BuildSldprt(dict(Streams))),
            include_tessellation=False,
        )
    except (KeyError, SldprtFormatError, TypeError, ValueError, Struct.error):
        return frozenset()
    Result: set[Capability] = set()
    if Encoding.structure_complete and IsGeneratedAsmB(AsmValue, Encoding, Native):
        Result.add(Capability.ASSEMBLIES)
        if len(AsmValue.definitions) > 1:
            Result.add(Capability.EXTERNAL_REFERENCES)

    # this callback exists because local behavior needs one focused transformation
    OrderedConfigs = tuple(
        sorted(
            Configurations,
            key=lambda ConfigItem: (
                not ConfigItem.active,
                Configurations.index(ConfigItem),
            ),
        )
    )
    if tuple(
        ((ConfigItem.name, ConfigItem.active) for ConfigItem in OrderedConfigs)
    ) == tuple(
        (
            (ConfigItem.name, ConfigItem.most_recent)
            for ConfigItem in Native.configurations
        )
    ):
        Result.add(Capability.CONFIGURATIONS)
    if (
        Encoding.mates_complete
        and (not Encoding.generated_mate_ids)
        and AsmValue.mates
        and (len(Native.mate_lists) == len(Encoding.mate_streams))
        and all(
            (
                ItemValue.declared_count == len(ItemValue.mates)
                for ItemValue in Native.mate_lists
            )
        )
        and (
            sum(
                (
                    1
                    for ItemValue in Native.mate_lists
                    for MateValue in ItemValue.mates
                    if MateValue.kind != "group"
                )
            )
            == len(AsmValue.mates)
        )
    ):
        Result.add(Capability.ASSEMBLY_MATES)
    return frozenset(Result)


# this predicate exists because native definitions must preserve semantic identity
def IsAsmDef(Source: ComponentDefinition, Target: NativeAsmDefinition) -> bool:
    ExpectedKind = (
        "ASSEMBLY" if str(Source.kind) == ComponentKind.ASSEMBLY.value else "PART"
    )
    if (
        Target.name != Source.name
        or Target.document_type != ExpectedKind
        or Target.configuration_name != (Source.configuration_name or "Default")
    ):
        return False
    if Source.bounding_box is None:
        return True
    ExpectedBox = tuple(
        (
            Value / 1000.0
            for Value in (
                Source.bounding_box.minimum.x,
                Source.bounding_box.minimum.y,
                Source.bounding_box.minimum.z,
                Source.bounding_box.maximum.x,
                Source.bounding_box.maximum.y,
                Source.bounding_box.maximum.z,
            )
        )
    )
    return Target.bounding_box_m == ExpectedBox


# this predicate exists because encoded definitions must match source definitions
def IsAsmDefs(
    AsmValue: AssemblyData, Encoding: NativeAssemblyEncoding, Native: NativeAssembly
) -> bool:
    Definitions = {ItemValue.object_id: ItemValue for ItemValue in Native.definitions}
    if Native.root_definition_id != Encoding.definition_ids.get(
        AsmValue.root_definition_id
    ):
        return False
    if set(Definitions) != set(Encoding.definition_ids.values()):
        return False
    for Source in AsmValue.definitions:
        Target = Definitions.get(Encoding.definition_ids[Source.id])
        if Target is None or not IsAsmDef(Source, Target):
            return False
    return True


# this predicate exists because native occurrences must preserve every source field
def IsAsmItem(
    AsmValue: AssemblyData,
    Encoding: NativeAssemblyEncoding,
    Source: ComponentInstance,
    Target: NativeAsmItem,
    Index: int,
) -> bool:
    RefValue = GeneratedRef(Source, Index + 1)
    Suffix = f"-{RefValue}"
    BaseName = (
        Source.name[: -len(Suffix)] if Source.name.endswith(Suffix) else Source.name
    )
    ConfigName = (
        Source.configuration_name
        or AsmValue.definition(Source.definition_id).configuration_name
        or "Default"
    )
    return (
        Target.name == BaseName
        and Target.reference_number == RefValue
        and Target.owner_definition_id
        == Encoding.definition_ids[Source.owner_definition_id]
        and (Target.definition_id == Encoding.definition_ids[Source.definition_id])
        and (Target.configuration_name == ConfigName)
        and (Target.configuration_id == GeneratedA(Source.configuration_id))
        and (Target.transform == NativeAsmMatrix(Source.transform))
        and (Target.suppressed == Source.suppressed)
        and (Target.hidden == Source.hidden)
        and (Target.flexible == Source.flexible)
        and (Target.exclude_from_bom == Source.exclude_from_bom)
    )


# this predicate exists because sibling occurrence order is part of assembly identity
def IsAsmOrder(
    AsmValue: AssemblyData,
    Encoding: NativeAssemblyEncoding,
    Native: NativeAssembly,
    ByOwner: Mapping[str, list[tuple[int, int, ComponentInstance]]],
) -> bool:
    NativeByOwner: Defaultdict[int, list[NativeAsmItem]] = Defaultdict(list)
    for Target in Native.occurrences:
        NativeByOwner[Target.owner_definition_id].append(Target)
    for OwnerId, Values in ByOwner.items():

        # this callback exists because native sibling ordering needs a stable key
        Expected = [
            Encoding.occurrence_ids[ItemValue.id]
            for Ignored, Ignored, ItemValue in sorted(
                Values, key=lambda Value: (Value[0], Value[1])
            )
        ]
        Actual = [
            ItemValue.object_id
            for ItemValue in NativeByOwner[Encoding.definition_ids[OwnerId]]
        ]
        if Actual != Expected:
            return False
    return True


# this predicate exists because encoded occurrences must match source occurrences
def IsAsmItems(
    AsmValue: AssemblyData, Encoding: NativeAssemblyEncoding, Native: NativeAssembly
) -> bool:
    Occurrences = {ItemValue.object_id: ItemValue for ItemValue in Native.occurrences}
    if set(Occurrences) != set(Encoding.occurrence_ids.values()):
        return False
    ByOwner: Defaultdict[str, list[tuple[int, int, ComponentInstance]]] = Defaultdict(
        list
    )
    for Index, Source in enumerate(AsmValue.instances):
        ByOwner[Source.owner_definition_id].append((Source.order, Index, Source))
        Target = Occurrences.get(Encoding.occurrence_ids[Source.id])
        if Target is None or not IsAsmItem(AsmValue, Encoding, Source, Target, Index):
            return False
    return IsAsmOrder(AsmValue, Encoding, Native, ByOwner)


# this predicate exists because generated assemblies need complete semantic proof
def IsGeneratedAsmB(
    AsmValue: AssemblyData, Encoding: NativeAssemblyEncoding, Native: NativeAssembly
) -> bool:
    return IsAsmDefs(AsmValue, Encoding, Native) and IsAsmItems(
        AsmValue, Encoding, Native
    )


# this definition exists because focused behavior needs one stable owner
def GeneratedRef(Instance: ComponentInstance, Fallback: int) -> int:
    for Value in (
        Instance.reference_number,
        Instance.attributes.get("native_reference_number"),
    ):
        if isinstance(Value, bool):
            continue
        try:
            Number = int(Value)
        except (TypeError, ValueError):
            continue
        if Number > 0:
            return Number
    Match = RegexLib.search("-(\\d+)$", Instance.name)
    return int(Match.group(1)) if Match is not None else Fallback


# this definition exists because focused behavior needs one stable owner
def GeneratedA(Value: Any) -> int:
    if isinstance(Value, bool):
        return 0
    try:
        return int(Value)
    except (TypeError, ValueError):
        return 0


# this definition exists because native model patching needs before and after snapshots
def PatchModelsMut(
    DocValue: CadDocument, StreamsMut: dict[str, bytes]
) -> tuple[NativeModel, NativeModel]:
    SelectedStream = ResolvedStream(StreamsMut, ResolvedFeaturesStream)
    OriginalModel = DecodeNativeModel(
        StreamsMut[KeywordsStream],
        StreamsMut[SelectedStream],
        resolved_stream=SelectedStream,
    )
    Keywords = KeywordsRoot(StreamsMut[KeywordsStream])
    Resolved = bytearray(StreamsMut[SelectedStream])
    KeywordsChanged = IsPatchFeatuMut(DocValue, OriginalModel, Keywords[1], Resolved)
    KeywordsChanged = (
        IsPatchParamete(DocValue, OriginalModel, Keywords[1], Resolved)
        or KeywordsChanged
    )
    PatchSupport(DocValue, OriginalModel, Resolved)
    PatchSketchGeom(DocValue, OriginalModel, Resolved)
    if KeywordsChanged:
        StreamsMut[KeywordsStream] = KeywordsBytes(*Keywords)
    StreamsMut[SelectedStream] = bytes(Resolved)
    PatchedModel = DecodeNativeModel(
        StreamsMut[KeywordsStream],
        StreamsMut[SelectedStream],
        resolved_stream=SelectedStream,
    )
    return (OriginalModel, PatchedModel)


# this definition exists because parameter parity contributes two native capabilities
def AddParamCapsMut(
    DocValue: CadDocument,
    PatchedParameters: Sequence[Parameter],
    NativeMut: set[Capability],
) -> None:
    if ParamValues(DocValue.parameters) != ParamValues(PatchedParameters):
        return
    NativeMut.add(Capability.PARAMETERS)
    if not any((Param.expression is not None for Param in DocValue.parameters)):
        NativeMut.add(Capability.EXPRESSIONS)


# this definition exists because patched part semantics determine native capabilities
def NativePartCaps(
    DocValue: CadDocument, OriginalModel: NativeModel, PatchedModel: NativeModel
) -> set[Capability]:
    Native: set[Capability] = set()
    PatchedParameters = Parameters(PatchedModel)
    ParamIds = {Param.id for Param in PatchedParameters}
    PatchedPlanes = Planes(PatchedModel, ParamIds)
    PatchedSketches = Sketches(PatchedModel, ParamIds)
    PatchedSelections = Selections(PatchedModel)
    PatchedTimeline = Timeline(PatchedModel, PatchedSelections)
    OriginalParameters = Parameters(OriginalModel)
    OriginalSketches = Sketches(
        OriginalModel, {Param.id for Param in OriginalParameters}
    )
    OriginalSelections = Selections(OriginalModel)
    OriginalTimeline = Timeline(OriginalModel, OriginalSelections)
    AddParamCapsMut(DocValue, PatchedParameters, Native)
    if PlaneValues(DocValue.support_planes) == PlaneValues(PatchedPlanes):
        Native.add(Capability.SUPPORT_PLANES)
    DesiredSketchValues = SketchValues(DocValue.sketches)
    if DesiredSketchValues == SketchValues(
        PatchedSketches
    ) or DesiredSketchValues == SketchValues(OriginalSketches):
        Native.add(Capability.EDITABLE_SKETCHES)
    DesiredFeatures = FeatureValues(DocValue.feature_timeline, DocValue.parameters)
    if DesiredFeatures == FeatureValues(
        PatchedTimeline, PatchedParameters
    ) and IsNativeFeature(DocValue.feature_timeline, OriginalTimeline):
        Native.add(Capability.PARAMETRIC_HISTORY)
    if SelectionValues(DocValue.selections) == SelectionValues(OriginalSelections):
        Native.add(Capability.SELECTIONS)
    OriginalConfigs = Configurations(OriginalModel, None)
    if ConfigValues(DocValue.configurations) == ConfigValues(OriginalConfigs):
        Native.add(Capability.CONFIGURATIONS)
    if DocValue.assembly is None and BodyValues(DocValue.bodies) == NativeBody(
        OriginalModel, OriginalTimeline
    ):
        Native.add(Capability.BODY_STRUCTURE)
    return Native


# this definition exists because brep patching contributes independent capabilities
def PatchBrepMut(
    DocValue: CadDocument,
    StreamsMut: dict[str, bytes],
    OriginalStreams: Mapping[str, bytes],
    NativeMut: set[Capability],
) -> tuple[str, bool]:
    NativeBrep, BrepNative, PayloadsNative = PatchTemplatMut(
        DocValue, StreamsMut, OriginalStreams
    )
    if BrepNative:
        NativeMut.add(Capability.BREP)
    if PayloadsNative:
        NativeMut.add(Capability.NATIVE_PAYLOADS)
    if DocValue.assembly is None and DocValue.meshes == ():
        NativeMut.add(Capability.TESSELLATION)
    return (NativeBrep, BrepNative)


# this definition exists because assembly patching contributes nested capabilities
def PatchAsmCapsMut(
    DocValue: CadDocument,
    StreamsMut: dict[str, bytes],
    BundleNames: Mapping[str, str],
    BrepNative: bool,
    NativeMut: set[Capability],
) -> tuple[str, ...]:
    if DocValue.assembly is None:
        return ()
    Patch = PatchNativeAMut(DocValue, StreamsMut, BundleNames)
    NativeMut.update(Patch.capabilities)
    if Capability.COMPONENT_DOCUMENTS in Patch.capabilities and BrepNative:
        NativeMut.add(Capability.NATIVE_PAYLOADS)
    return Patch.divergences


# this definition exists because template results differ for parts and assemblies
def PatchResult(
    DocValue: CadDocument,
    Streams: dict[str, bytes],
    OriginalStreams: Mapping[str, bytes],
    NativeBrep: str,
    Native: set[Capability],
    Divergences: tuple[str, ...],
) -> Generated:
    Usable = not (Required(DocValue) - Native - KTargetUnsupported)
    if DocValue.assembly is None:
        return Generated(
            Streams,
            NativeBrep,
            frozenset(Native),
            "native-template" if Usable else "native-source-with-kit-neutral",
            Usable,
            Usable,
        )
    ReaderGaps = (
        AsmReaderGaps(Streams, OriginalStreams, KAsmRewritableDonorStreaA) + Divergences
    )
    Loadable = not ReaderGaps
    return Generated(
        Streams,
        NativeBrep,
        frozenset(Native),
        "native-template" if Usable and Loadable else "native-source-with-kit-neutral",
        Usable and Loadable,
        Loadable,
        reader_gaps=ReaderGaps,
    )


# this definition exists because focused behavior needs one stable owner
def PatchNativeMut(
    DocValue: CadDocument, Streams: dict[str, bytes], BundleNames: Mapping[str, str]
) -> Generated:
    OriginalStreams = dict(Streams)
    if KeywordsStream not in Streams or ResolvedFeaturesStream not in Streams:
        return Generated(
            Streams,
            "template",
            frozenset(),
            "native-source-with-kit-neutral",
            False,
            False,
        )
    OriginalModel, PatchedModel = PatchModelsMut(DocValue, Streams)
    Native = NativePartCaps(DocValue, OriginalModel, PatchedModel)
    NativeBrep, BrepNative = PatchBrepMut(DocValue, Streams, OriginalStreams, Native)
    Divergences = PatchAsmCapsMut(DocValue, Streams, BundleNames, BrepNative, Native)
    return PatchResult(
        DocValue, Streams, OriginalStreams, NativeBrep, Native, Divergences
    )


# this definition exists because focused behavior needs one stable owner
def KeywordsRoot(DataValue: bytes) -> tuple[bytes, XmlTree.Element, bytes]:
    Start = DataValue.find(b"<?xml")
    if Start < 0:
        Start = DataValue.find(b"<")
    if Start < 0:
        raise SldprtFormatError("keyword stream contains no XML document")
    Prefix = DataValue[:Start]
    RawValue = DataValue[Start:]
    Trailing = (
        b"\r\n"
        if RawValue.endswith(b"\r\n")
        else b"\n" if RawValue.endswith(b"\n") else b""
    )
    try:
        RootValue = XmlTree.fromstring(RawValue)
    except XmlTree.ParseError as ErrorInfo:
        raise SldprtFormatError(f"invalid keyword XML: {ErrorInfo}") from ErrorInfo
    return (Prefix, RootValue, Trailing)


# this definition exists because focused behavior needs one stable owner
def KeywordsBytes(Prefix: bytes, RootValue: ET.Element, Trailing: bytes) -> bytes:
    return (
        Prefix
        + XmlTree.tostring(RootValue, encoding="utf-8", xml_declaration=True)
        + Trailing
    )


# this definition exists because focused behavior needs one stable owner
def XmlElementsById(RootValue: ET.Element) -> dict[int, XmlTree.Element]:
    Result: dict[int, XmlTree.Element] = {}
    for ElemValue in RootValue.iter():
        RawValue = ElemValue.attrib.get("id")
        if RawValue is None:
            continue
        try:
            Result[int(RawValue)] = ElemValue
        except ValueError:
            continue
    return Result


# this definition exists because focused behavior needs one stable owner
def NativeId(Value: str, Prefix: str) -> int | None:
    if not Value.startswith(Prefix):
        return None
    try:
        return int(Value.removeprefix(Prefix).split(":", 1)[0])
    except ValueError:
        return None


# native names merge feature plane and sketch identifiers before binary patching
def NativeNames(DocValue: CadDocument) -> dict[int, str]:
    Desired: dict[int, str] = {}
    Sources = (
        (DocValue.feature_timeline, "sldprt:feature:"),
        (DocValue.support_planes, "sldprt:plane:"),
        (DocValue.sketches, "sldprt:sketch:"),
    )
    for Items, Prefix in Sources:
        for ItemValue in Items:
            ObjectId = NativeId(ItemValue.id, Prefix)
            if ObjectId is not None and ObjectId not in Desired:
                Desired[ObjectId] = ItemValue.name
    return Desired


# this definition exists because focused behavior needs one stable owner
def IsPatchFeatuMut(
    DocValue: CadDocument,
    Model: NativeModel,
    RootValue: ET.Element,
    Resolved: bytearray,
) -> bool:
    Desired = NativeNames(DocValue)
    Elements = XmlElementsById(RootValue)
    Features = {Feature.object_id: Feature for Feature in Model.features}
    Changed = False
    for ObjectId, NameValue in Desired.items():
        Feature = Features.get(ObjectId)
        if Feature is None or NameValue == Feature.name:
            continue
        Record = next(
            (
                Choice
                for Choice in Model.names
                if Choice.object_id == ObjectId
                and Choice.offset == Feature.native_offset
            ),
            None,
        )
        Encoded = NameValue.encode("utf-16le")
        if Record is None or len(Encoded) != len(Feature.name.encode("utf-16le")):
            continue
        Start = Record.text_end - len(Feature.name.encode("utf-16le"))
        if bytes(Resolved[Start : Record.text_end]).decode("utf-16le") != Feature.name:
            continue
        Resolved[Start : Record.text_end] = Encoded
        ElemValue = Elements.get(ObjectId)
        if ElemValue is not None:
            ElemValue.attrib["Name"] = NameValue
        Changed = True
    return Changed


# this definition exists because focused behavior needs one stable owner
def ParamA(Param: Parameter) -> float | None:
    Value = Param.value.value
    if isinstance(Value, bool) or not isinstance(Value, (int, float)):
        return None
    Number = float(Value)
    if not MathValue.isfinite(Number) or Param.value.kind is not ValueKind.LENGTH:
        return None
    Factor = {
        "": 1.0,
        "mm": 1.0,
        "millimeter": 1.0,
        "millimeters": 1.0,
        "cm": 10.0,
        "m": 1000.0,
        "in": 25.4,
        "inch": 25.4,
        "inches": 25.4,
    }.get(Param.value.unit.casefold())
    return Number * Factor if Factor is not None else None


# this definition exists because focused behavior needs one stable owner
def DimensionText(Source: str, Millimeters: float) -> str:
    Value = format(Millimeters, ".15g")
    return KNumberText.sub(Value, Source, count=1)


# parameter lookup isolates native feature ownership from scalar replacement
def ParamDimMap(Model: NativeModel) -> dict[str, tuple[int, NativeDimension]]:
    Result: dict[str, tuple[int, NativeDimension]] = {}
    for Feature in Model.features:
        for Dimension, ParamId in ParamEntries(Feature.object_id, Feature.dimensions):
            Result[ParamId] = (Feature.object_id, Dimension)
    return Result


# scalar patching validates one compatible parameter before mutating native bytes
def IsPatchParamMut(
    ParamId: str,
    Source: Parameter,
    Target: Parameter,
    Record: tuple[int, NativeDimension] | None,
    Elements: Mapping[int, ET.Element],
    Resolved: bytearray,
) -> bool:
    TargetMm = ParamA(Target)
    SourceMm = ParamA(Source)
    if (
        TargetMm is None
        or SourceMm is None
        or MathValue.isclose(TargetMm, SourceMm, rel_tol=1e-12, abs_tol=1e-12)
    ):
        return False
    if (Target.name, Target.role, Target.owner_id, Target.expression) != (
        Source.name,
        Source.role,
        Source.owner_id,
        Source.expression,
    ):
        return False
    if Record is None or Record[1].native_offset is None:
        return False
    ObjectId, Dimension = Record
    Struct.pack_into("<d", Resolved, Dimension.native_offset, TargetMm / 1000.0)
    ElemValue = Elements.get(ObjectId)
    if ElemValue is None:
        return False
    ItemValue = (
        int(ParamId.rsplit(":", 1)[-1]) - 1
        if ParamId.rsplit(":", 1)[-1].isdigit() and ParamId.count(":") > 3
        else 0
    )
    Matches = tuple(
        (
            Child
            for Child in ElemValue
            if Child.tag.rsplit("}", 1)[-1] == "Dimension"
            and Child.attrib.get("Name", "") == Dimension.name
        )
    )
    if ItemValue >= len(Matches):
        return False
    setattr(
        Matches[ItemValue],
        "text",
        DimensionText(Matches[ItemValue].text or Dimension.source_text, TargetMm),
    )
    return True


# this definition exists because focused behavior needs one stable owner
def IsPatchParamete(
    DocValue: CadDocument,
    Model: NativeModel,
    RootValue: ET.Element,
    Resolved: bytearray,
) -> bool:
    Original = {Param.id: Param for Param in Parameters(Model)}
    Desired = {Param.id: Param for Param in DocValue.parameters}
    if set(Original) != set(Desired):
        return False
    Elements = XmlElementsById(RootValue)
    Dimensions = ParamDimMap(Model)
    Changed = False
    for ParamId, Target in Desired.items():
        Changed = (
            IsPatchParamMut(
                ParamId,
                Original[ParamId],
                Target,
                Dimensions.get(ParamId),
                Elements,
                Resolved,
            )
            or Changed
        )
    return Changed


# this definition exists because focused behavior needs one stable owner
def VectorValues(Vector: Vector3) -> tuple[float, float, float]:
    return (Vector.x, Vector.y, Vector.z)


# this definition exists because focused behavior needs one stable owner
def IsUnitVector(Values: tuple[float, float, float]) -> bool:
    return all((MathValue.isfinite(Value) for Value in Values)) and MathValue.isclose(
        sum((Value * Value for Value in Values)), 1.0, rel_tol=1e-09, abs_tol=1e-09
    )


# this definition exists because focused behavior needs one stable owner
def IsOrthonormal(Transform: Transform) -> bool:
    AxesValue = (
        VectorValues(Transform.x_axis),
        VectorValues(Transform.y_axis),
        VectorValues(Transform.z_axis),
    )
    return all((IsUnitVector(AxisValue) for AxisValue in AxesValue)) and all(
        (
            MathValue.isclose(
                sum((LeftValue[Index] * Right[Index] for Index in range(3))),
                0.0,
                abs_tol=1e-09,
            )
            for LeftValue, Right in (
                (AxesValue[0], AxesValue[1]),
                (AxesValue[0], AxesValue[2]),
                (AxesValue[1], AxesValue[2]),
            )
        )
    )


# plane patching validates one frame before writing its native layout
def PatchPlaneMut(
    Source: SupportPlane, Target: SupportPlane, Resolved: bytearray
) -> None:
    if Target.transform == Source.transform:
        return
    if (Target.name, Target.support_selection_id, Target.offset_parameter_id) != (
        Source.name,
        Source.support_selection_id,
        Source.offset_parameter_id,
    ) or not IsOrthonormal(Target.transform):
        return
    Offset = Source.attributes.get("native_frame_offset")
    Length = Source.attributes.get("native_frame_length")
    if not isinstance(Offset, int) or Length not in {81, 121}:
        return
    Origin = tuple((Value / 1000.0 for Value in VectorValues(Target.transform.origin)))
    XAxis = VectorValues(Target.transform.x_axis)
    YAxis = VectorValues(Target.transform.y_axis)
    ZAxis = VectorValues(Target.transform.z_axis)
    if not all((MathValue.isfinite(Value) for Value in Origin)):
        return
    if Length == 81:
        if (
            XAxis != (1.0, 0.0, 0.0)
            or YAxis != (0.0, 1.0, 0.0)
            or ZAxis != (0.0, 0.0, 1.0)
        ):
            return
        Struct.pack_into("<3d", Resolved, Offset, *Origin)
        Struct.pack_into("<3d", Resolved, Offset + 57, 0.0, -Origin[2], 1.0)
        return
    Struct.pack_into("<3d", Resolved, Offset, *Origin)
    Struct.pack_into("<3d", Resolved, Offset + 24, *ZAxis)
    for Index, RowValue in enumerate(zip(XAxis, YAxis, ZAxis, strict=True)):
        Struct.pack_into("<3d", Resolved, Offset + 49 + Index * 24, *RowValue)


# this definition exists because focused behavior needs one stable owner
def PatchSupport(
    DocValue: CadDocument, Model: NativeModel, Resolved: bytearray
) -> None:
    ParamValues = Parameters(Model)
    Original = {
        Plane.id: Plane for Plane in Planes(Model, {Param.id for Param in ParamValues})
    }
    Desired = {Plane.id: Plane for Plane in DocValue.support_planes}
    if set(Original) != set(Desired):
        return
    for PlaneId, Target in Desired.items():
        PatchPlaneMut(Original[PlaneId], Target, Resolved)


# this definition exists because focused behavior needs one stable owner
def Coordinate(DataValue: bytes | bytearray, MarkerOffset: int) -> int | None:
    for Relative in (56, 64):
        Offset = MarkerOffset + Relative
        if DataValue[Offset : Offset + 2] == b"\x1e\x00" and Offset + 18 <= len(
            DataValue
        ):
            return Offset + 2
    return None


# this definition exists because focused behavior needs one stable owner
def IsPatchCoordina(
    Resolved: bytearray, MarkerOffset: int, Point: tuple[float, float]
) -> bool:
    if not all((MathValue.isfinite(Value) for Value in Point)):
        return False
    Offset = Coordinate(Resolved, MarkerOffset)
    if Offset is None:
        return False
    Struct.pack_into("<2d", Resolved, Offset, Point[0] / 1000.0, Point[1] / 1000.0)
    return True


# this definition exists because focused behavior needs one stable owner
def PointValues(Value: Vector2) -> tuple[float, float]:
    return (Value.x, Value.y)


# point patching isolates marker coordinates from profile geometry changes
def PatchPointsMut(
    Sketch: NativeSketch,
    Sources: Mapping[str, SketchEntity],
    Targets: Mapping[str, SketchEntity],
    Resolved: bytearray,
) -> None:
    for EntityId, TargetEntity in Targets.items():
        SourceEntity = Sources[EntityId]
        if TargetEntity.geometry == SourceEntity.geometry:
            continue
        if (TargetEntity.kind, TargetEntity.construction, TargetEntity.fixed) != (
            SourceEntity.kind,
            SourceEntity.construction,
            SourceEntity.fixed,
        ):
            continue
        if isinstance(SourceEntity.geometry, PointGeom) and isinstance(
            TargetEntity.geometry, PointGeom
        ):
            MarkerOffset = NativeId(
                EntityId, f"sldprt:sketch:{Sketch.object_id}:native:"
            )
            if MarkerOffset is not None:
                IsPatchCoordina(
                    Resolved, MarkerOffset, PointValues(TargetEntity.geometry.point)
                )


# profile patching isolates circle and rectangle byte layouts from sketch selection
def PatchShapesMut(
    Sketch: NativeSketch,
    Sources: Mapping[str, SketchEntity],
    Targets: Mapping[str, SketchEntity],
    Resolved: bytearray,
) -> None:
    for ProfileIndex, Profile in enumerate(Sketch.profiles):
        if Profile.kind == "rectangle":
            PatchRectangle(Resolved, Sketch, ProfileIndex, Profile, Targets)
            continue
        if Profile.kind != "circle":
            continue
        EntityId = ProfileId(Sketch.object_id, ProfileIndex)
        SourceEntity = Sources.get(EntityId)
        TargetEntity = Targets.get(EntityId)
        if (
            SourceEntity is None
            or TargetEntity is None
            or TargetEntity.geometry == SourceEntity.geometry
            or not isinstance(TargetEntity.geometry, CircleGeom)
            or len(Profile.marker_offsets) < 2
        ):
            continue
        Center = PointValues(TargetEntity.geometry.center)
        SourceCenter = Profile.coordinates[:2]
        SourceEdge = next(
            (
                Marker.coordinates_mm
                for Marker in Sketch.markers
                if Marker.offset == Profile.marker_offsets[1]
                and Marker.coordinates_mm is not None
            ),
            None,
        )
        if SourceEdge is None or TargetEntity.geometry.radius <= 0.0:
            continue
        DxValue = SourceEdge[0] - SourceCenter[0]
        DyValue = SourceEdge[1] - SourceCenter[1]
        Length = MathValue.hypot(DxValue, DyValue)
        if Length <= 1e-12:
            DxValue, DyValue, Length = (1.0, 0.0, 1.0)
        EdgeValue = (
            Center[0] + DxValue / Length * TargetEntity.geometry.radius,
            Center[1] + DyValue / Length * TargetEntity.geometry.radius,
        )
        IsPatchCoordina(Resolved, Profile.marker_offsets[0], Center)
        IsPatchCoordina(Resolved, Profile.marker_offsets[1], EdgeValue)


# this definition exists because focused behavior needs one stable owner
def PatchSketchGeom(
    DocValue: CadDocument, Model: NativeModel, Resolved: bytearray
) -> None:
    ParamValues = Parameters(Model)
    OriginalSketches = Sketches(Model, {Param.id for Param in ParamValues})
    Original = {Sketch.id: Sketch for Sketch in OriginalSketches}
    Native = {SketchId(Sketch.object_id): Sketch for Sketch in Model.sketches}
    Desired = {Sketch.id: Sketch for Sketch in DocValue.sketches}
    if set(Original) != set(Desired):
        return
    for SketchKey, Target in Desired.items():
        Source = Original[SketchKey]
        NativeSketch = Native[SketchKey]
        if (
            Target.support_plane_id != Source.support_plane_id
            or Target.constraints != Source.constraints
            or Target.parameter_ids != Source.parameter_ids
            or (Target.closed_profile_entity_ids != Source.closed_profile_entity_ids)
            or (Target.suppressed != Source.suppressed)
        ):
            continue
        SourceEntities = {Entity.id: Entity for Entity in Source.entities}
        TargetEntities = {Entity.id: Entity for Entity in Target.entities}
        if set(SourceEntities) != set(TargetEntities):
            continue
        PatchPointsMut(NativeSketch, SourceEntities, TargetEntities, Resolved)
        PatchShapesMut(NativeSketch, SourceEntities, TargetEntities, Resolved)


# this definition exists because focused behavior needs one stable owner
def PatchRectangle(
    Resolved: bytearray,
    Sketch: NativeSketch,
    ProfileIndex: int,
    Profile: NativeProfile,
    Entities: Mapping[str, SketchEntity],
) -> None:
    Lines: list[LineGeom] = []
    for EdgeIndex in range(4):
        Entity = Entities.get(ProfileEdgeId(Sketch.object_id, ProfileIndex, EdgeIndex))
        if Entity is None or not isinstance(Entity.geometry, LineGeom):
            return
        Lines.append(Entity.geometry)
    Points = tuple(
        (
            PointValues(Lines[0].start),
            PointValues(Lines[0].end),
            PointValues(Lines[1].end),
            PointValues(Lines[2].end),
        )
    )[0]
    if (
        PointValues(Lines[1].start) != Points[1]
        or PointValues(Lines[2].start) != Points[2]
        or PointValues(Lines[3].start) != Points[3]
        or (PointValues(Lines[3].end) != Points[0])
    ):
        return
    XsValue = sorted({Point[0] for Point in Points})
    YsValue = sorted({Point[1] for Point in Points})
    if len(XsValue) != 2 or len(YsValue) != 2:
        return
    XZero, YZero, XOneValue, YOneValue = Profile.coordinates
    SourceCorners = (
        (XZero, YZero),
        (XOneValue, YZero),
        (XOneValue, YOneValue),
        (XZero, YOneValue),
    )
    for Marker in Sketch.markers:
        if Marker.coordinates_mm is None:
            continue
        for Source, Target in zip(SourceCorners, Points, strict=True):
            if all(
                (
                    MathValue.isclose(LeftValue, Right, abs_tol=1e-09)
                    for LeftValue, Right in zip(
                        Marker.coordinates_mm, Source, strict=True
                    )
                )
            ):
                IsPatchCoordina(Resolved, Marker.offset, Target)
                break


# this definition exists because focused behavior needs one stable owner
def RoundNumber(Value: float) -> float:
    return round(Value, 10)


# this definition exists because focused behavior needs one stable owner
def ParamValues(Parameters: Sequence[Parameter]) -> tuple[AnyValue, ...]:
    return tuple(
        (
            (
                Param.id,
                Param.name,
                (
                    RoundNumber(Value)
                    if (Value := ParamA(Param)) is not None
                    else Param.value
                ),
                Param.role,
                Param.expression,
                Param.owner_id,
            )
            for Param in Parameters
        )
    )


# this definition exists because focused behavior needs one stable owner
def TransformValues(Transform: Transform) -> tuple[float, ...]:
    return tuple(
        (
            RoundNumber(Value)
            for Vector in (
                Transform.origin,
                Transform.x_axis,
                Transform.y_axis,
                Transform.z_axis,
            )
            for Value in VectorValues(Vector)
        )
    )


# this definition exists because focused behavior needs one stable owner
def PlaneValues(Planes: Sequence[SupportPlane]) -> tuple[AnyValue, ...]:
    return tuple(
        (
            (
                Plane.id,
                Plane.name,
                TransformValues(Plane.transform),
                Plane.support_selection_id,
                Plane.offset_parameter_id,
            )
            for Plane in Planes
        )
    )


# this definition exists because focused behavior needs one stable owner
def GeomValues(GeomValue: Any) -> AnyValue:
    if isinstance(GeomValue, PointGeom):
        return (
            "point",
            tuple((RoundNumber(Value) for Value in PointValues(GeomValue.point))),
        )
    if isinstance(GeomValue, LineGeom):
        return (
            "line",
            tuple((RoundNumber(Value) for Value in PointValues(GeomValue.start))),
            tuple((RoundNumber(Value) for Value in PointValues(GeomValue.end))),
        )
    if isinstance(GeomValue, CircleGeom):
        return (
            "circle",
            tuple((RoundNumber(Value) for Value in PointValues(GeomValue.center))),
            RoundNumber(GeomValue.radius),
        )
    return GeomValue


# this definition exists because focused behavior needs one stable owner
def SketchValues(Sketches: Sequence[SketchData]) -> tuple[AnyValue, ...]:
    return tuple(
        (
            (
                Sketch.id,
                Sketch.name,
                Sketch.support_plane_id,
                tuple(
                    (
                        (
                            Entity.id,
                            Entity.kind,
                            GeomValues(Entity.geometry),
                            Entity.construction,
                            Entity.fixed,
                        )
                        for Entity in Sketch.entities
                    )
                ),
                tuple(
                    (
                        (
                            RuleValue.id,
                            RuleValue.kind,
                            RuleValue.references,
                            RuleValue.parameter_id,
                            RuleValue.driving,
                            RuleValue.suppressed,
                        )
                        for RuleValue in Sketch.constraints
                    )
                ),
                Sketch.parameter_ids,
                Sketch.closed_profile_entity_ids,
                Sketch.suppressed,
            )
            for Sketch in Sketches
        )
    )


# this definition exists because focused behavior needs one stable owner
def DefinitionValue(
    Definition: Any, ParamValue: ParameterValue | None = None
) -> AnyValue:
    if isinstance(Definition, ExtrusionFeature):
        Length = ParamValue or Definition.length
        return (
            "extrusion",
            RoundNumber(float(Length.value)),
            Length.kind,
            Length.unit,
            Definition.end_condition,
            Definition.reversed,
        )
    if isinstance(Definition, FilletFeature):
        Radius = ParamValue or Definition.radius
        return ("fillet", RoundNumber(float(Radius.value)), Radius.kind, Radius.unit)
    if isinstance(Definition, NativeFeatureDefinition):
        return ("native", Definition.format_id, Definition.type_id)
    return Definition


# this definition exists because focused behavior needs one stable owner
def FeatureValues(
    Features: Sequence[FeatureStep], Parameters: Sequence[Parameter] = ()
) -> tuple[AnyValue, ...]:
    ParamById = {Param.id: Param for Param in Parameters}
    return tuple(
        (
            (
                Feature.id,
                Feature.name,
                Feature.kind,
                Feature.order,
                Feature.input_feature_ids,
                Feature.sketch_id,
                Feature.parameter_ids,
                Feature.operation,
                DefinitionValue(
                    Feature.definition,
                    next(
                        (
                            ParamById[ParamId].value
                            for ParamId in Feature.parameter_ids
                            if ParamId in ParamById
                        ),
                        None,
                    ),
                ),
                Feature.selection_ids,
                Feature.suppressed,
                Feature.configuration_states,
            )
            for Feature in Features
        )
    )


# this definition exists because focused behavior needs one stable owner
def IsNativeFeature(
    Desired: Sequence[FeatureStep], Original: Sequence[FeatureStep]
) -> bool:
    Originals = {Feature.id: Feature for Feature in Original}
    for Feature in Desired:
        Source = Originals.get(Feature.id)
        if Source is None:
            return False
        if (
            isinstance(Source.definition, NativeFeatureDefinition)
            and Feature.definition != Source.definition
        ):
            return False
    return True


# this definition exists because focused behavior needs one stable owner
def SelectionValues(Selections: Sequence[Selection]) -> tuple[AnyValue, ...]:
    return tuple(
        (
            (Selection.id, Selection.name, Selection.path, dict(Selection.query))
            for Selection in Selections
        )
    )


# this definition exists because focused behavior needs one stable owner
def ConfigValues(Configurations: Sequence[Configuration]) -> tuple[AnyValue, ...]:
    return tuple(
        (
            (
                Config.id,
                Config.name,
                Config.active,
                Config.parent_id,
                Config.overrides,
                Config.suppressed_feature_ids,
            )
            for Config in Configurations
        )
    )


# this definition exists because focused behavior needs one stable owner
def BodyValues(Bodies: Sequence[Body]) -> tuple[AnyValue, ...]:
    return tuple(
        (
            (
                BodyValue.id,
                BodyValue.name,
                BodyValue.final_feature_id,
                BodyValue.topology,
                BodyValue.material_id,
            )
            for BodyValue in Bodies
        )
    )


# this definition exists because focused behavior needs one stable owner
def NativeBody(
    Model: NativeModel, Timeline: tuple[FeatureStep, ...]
) -> tuple[AnyValue, ...]:
    BodyFeature = SolidBody(Model.features)
    BodyItem = BodyValue(
        id="sldprt:body:1",
        name=BodyFeature.name if BodyFeature is not None else "Body 1",
        final_feature_id=FinalBodyId(
            Timeline,
            frozenset(
                (FeatureId(Operation.object_id) for Operation in Model.operations)
            ),
        ),
        topology=TopologySummary(
            solid_count=1 if Model.operations else 0, bounding_box=BoundingBoxA(Model)
        ),
    )
    return BodyValues((BodyItem,))


# this definition exists because focused behavior needs one stable owner
def PayloadValues(Payloads: Sequence[BrepPayload]) -> tuple[AnyValue, ...]:
    return tuple(
        (
            (
                Payload.id,
                Payload.format_id,
                Payload.kind,
                Payload.schema,
                Payload.sha256,
                Payload.data,
                Payload.source_stream,
                Payload.role,
                Payload.file_extension,
            )
            for Payload in Payloads
        )
    )


# this definition exists because focused behavior needs one stable owner
def PatchTemplatMut(
    DocValue: CadDocument,
    Streams: dict[str, bytes],
    OriginalStreams: Mapping[str, bytes],
) -> tuple[str, bool, bool]:
    Archive = SldprtArchive.from_bytes(BuildSldprt(OriginalStreams))
    OriginalPayloads, Ignored = BrepPayloads(Archive, ReadOptions(strict=False))
    DesiredIndexes = SourcePayloadIndexes(DocValue)
    DesiredPayloads = tuple(
        (
            Payload
            for Index, Payload in enumerate(DocValue.brep_payloads)
            if Index not in DesiredIndexes and Payload.role is PayloadRole.BREP
        )
    )
    PayloadsNative = PayloadValues(DesiredPayloads) == PayloadValues(OriginalPayloads)
    OriginalBrep = TypedBrep(OriginalPayloads)
    if DocValue.brep == OriginalBrep and PayloadsNative:
        return ("template", True, True)
    Payload, State = Parasolid(DocValue)
    if Payload is None:
        Status = (
            State
            if State.startswith("unsupported:")
            else "unsupported:geometry has no writable Parasolid representation"
        )
        return (Status, False, PayloadsNative)
    Streams[PartitionStream] = Payload
    return ("patched", True, PayloadsNative)


# this definition exists because bundled assemblies need rewritten component paths
def PatchPathsMut(
    AsmValue: AssemblyData,
    StreamsMut: dict[str, bytes],
    BundleNames: Mapping[str, str],
) -> None:
    if not BundleNames:
        return
    Prefix, RootValue, Trailing = KeywordsRoot(StreamsMut[ComponentTreeStream])
    PathByFileId = {
        int(Definition.attributes["native_file_id"]): BundleNames.get(
            Definition.document_id
        )
        or BundleNames[Definition.id]
        for Definition in AsmValue.definitions
        if (Definition.document_id in BundleNames or Definition.id in BundleNames)
        and isinstance(Definition.attributes.get("native_file_id"), int)
    }
    Changed = False
    for ElemValue in RootValue.iter():
        if ElemValue.tag.rsplit("}", 1)[-1] != "swFile":
            continue
        try:
            FileId = int(ElemValue.attrib.get("id", ""))
        except ValueError:
            continue
        Target = PathByFileId.get(FileId)
        if Target is not None and ElemValue.attrib.get("swPath") != Target:
            ElemValue.attrib["swPath"] = Target
            Changed = True
    if Changed:
        StreamsMut[ComponentTreeStream] = KeywordsBytes(Prefix, RootValue, Trailing)


# this definition exists because patched assembly streams need one guarded decoder
def DecodePatchAsm(
    Streams: Mapping[str, bytes],
) -> tuple[SldprtArchive, NativeAssembly] | None:
    try:
        Archive = SldprtArchive.from_bytes(BuildSldprt(dict(Streams)))
        Native = DecodeNativeAsm(Archive, include_tessellation=True)
    except SldprtFormatError:
        return None
    return (Archive, Native)


# this definition exists because donor assembly patches require staged redecoding
def PatchAsmDataMut(
    DocValue: CadDocument, StreamsMut: dict[str, bytes]
) -> tuple[SldprtArchive, NativeAssembly, tuple[str, ...], tuple[str, ...]] | None:
    AsmValue = DocValue.assembly
    Decoded = DecodePatchAsm(StreamsMut)
    if AsmValue is None or Decoded is None:
        return None
    Archive, Native = Decoded
    DonorDivergences = DivergedDonor(AsmValue, Native)
    RewrittenInstances = PatchAsmMut(AsmValue, Native, StreamsMut)
    if RewrittenInstances:
        Decoded = DecodePatchAsm(StreamsMut)
        if Decoded is None:
            return None
        Archive, Native = Decoded
    RewrittenMates = PatchAsmMateMut(AsmValue, Native, StreamsMut, DocValue.source.path)
    if RewrittenMates:
        Decoded = DecodePatchAsm(StreamsMut)
        if Decoded is None:
            return None
        Archive, Native = Decoded
    return (Archive, Native, DonorDivergences, RewrittenMates)


# this definition exists because assembly structure and documents prove base capabilities
def AsmBaseCaps(
    AsmValue: AssemblyData,
    Native: NativeAssembly,
    BundleNames: Mapping[str, str],
) -> set[Capability]:
    Result: set[Capability] = set()
    if AsmStructure(AsmValue) == NativeAsmValues(Native):
        Result.add(Capability.ASSEMBLIES)
    Definitions = {Definition.id: Definition for Definition in AsmValue.definitions}
    DocIds = {Component.id for Component in AsmValue.documents}
    SavedDocuments = all(
        (
            isinstance(Component.document, CadDoc)
            and SavedSource(Component.document, None) is not None
            for Component in AsmValue.documents
        )
    )
    BundledDocuments = bool(DocIds) and DocIds <= set(BundleNames)
    if SavedDocuments or BundledDocuments:
        Result.add(Capability.COMPONENT_DOCUMENTS)
        if all(
            (
                not Component.document.bodies
                or Capability.BODY_STRUCTURE in Component.document.capabilities
                for Component in AsmValue.documents
                if isinstance(Component.document, CadDoc)
            )
        ):
            Result.add(Capability.BODY_STRUCTURE)
    if any((Definition.source_path for Definition in Definitions.values())):
        Result.add(Capability.EXTERNAL_REFERENCES)
    return Result


# this predicate exists because root mate records need exact neutral equivalence
def IsRootMates(
    DocValue: CadDocument,
    Native: NativeAssembly,
    Archive: SldprtArchive,
    HasDocuments: bool,
) -> bool:
    AsmValue = DocValue.assembly
    if AsmValue is None:
        return False
    IdentityDefinitions = {
        Definition.object_id: Definition.object_id for Definition in Native.definitions
    }
    IdentityOccurrences = {
        ItemValue.object_id: ItemValue.object_id for ItemValue in Native.occurrences
    }
    Ignored, Entities, Mates, Groups = AsmMates(
        Native,
        (
            (
                Native,
                Archive,
                IdentityDefinitions,
                IdentityOccurrences,
                DocValue.source.path,
            ),
        ),
    )
    DesiredEntities = {Entity.id: Entity for Entity in AsmValue.mate_entities}
    RootEntityIds = {
        EntityId for MateValue in Mates for EntityId in MateValue.entity_ids
    }
    SelectedEntities = tuple(
        (
            DesiredEntities[Entity.id]
            for Entity in Entities
            if Entity.id in RootEntityIds and Entity.id in DesiredEntities
        )
    )
    DesiredMates = {MateValue.id: MateValue for MateValue in AsmValue.mates}
    SelectedMates = tuple(
        (
            DesiredMates[MateValue.id]
            for MateValue in Mates
            if MateValue.id in DesiredMates
        )
    )
    DesiredGroups = {Group.id: Group for Group in AsmValue.mate_groups}
    SelectedGroups = tuple(
        (DesiredGroups[Group.id] for Group in Groups if Group.id in DesiredGroups)
    )
    RootMatesNative = MateValues(
        SelectedEntities, SelectedMates, SelectedGroups
    ) == MateValues(Entities, Mates, Groups)
    AllRootRecordsFound = (
        len(SelectedEntities) == len(Entities)
        and len(SelectedMates) == len(Mates)
        and (len(SelectedGroups) == len(Groups))
    )
    NestedMatesNative = len(AsmValue.mates) == len(Mates) or HasDocuments
    return RootMatesNative and AllRootRecordsFound and NestedMatesNative


# this definition exists because mates and tessellation extend assembly capabilities
def AsmFinalCapsMut(
    DocValue: CadDocument,
    Native: NativeAssembly,
    Archive: SldprtArchive,
    ResultMut: set[Capability],
) -> None:
    if IsRootMates(
        DocValue,
        Native,
        Archive,
        Capability.COMPONENT_DOCUMENTS in ResultMut,
    ):
        ResultMut.add(Capability.ASSEMBLY_MATES)
    NativeMeshes, Ignored = AsmMeshes(Native)
    if MeshValues(DocValue.meshes) == MeshValues(NativeMeshes):
        ResultMut.add(Capability.TESSELLATION)


# this definition exists because focused behavior needs one stable owner
def PatchNativeAMut(
    DocValue: CadDocument, Streams: dict[str, bytes], BundleNames: Mapping[str, str]
) -> AsmTemplate:
    AsmValue = DocValue.assembly
    if AsmValue is None or ComponentTreeStream not in Streams:
        return AsmTemplate(frozenset(), ("donor_component_tree_absent",))
    PatchPathsMut(AsmValue, Streams, BundleNames)
    Patched = PatchAsmDataMut(DocValue, Streams)
    if Patched is None:
        return AsmTemplate(frozenset(), ("donor_component_tree_unreadable",))
    Archive, Native, DonorDivergences, RewrittenMates = Patched
    Result = AsmBaseCaps(AsmValue, Native, BundleNames)
    AsmFinalCapsMut(DocValue, Native, Archive, Result)
    Divergences = DonorDivergences + tuple(
        (f"donor_mate_diverged:{ItemValue}" for ItemValue in RewrittenMates)
    )
    if Capability.ASSEMBLIES not in Result and not Divergences:
        Divergences = ("donor_structure_diverged",)
    return AsmTemplate(frozenset(Result), Divergences)


# this definition exists because focused behavior needs one stable owner
def AsmRefElements(RootValue: XmlTree.Element) -> dict[int, XmlTree.Element]:
    Elements: dict[int, XmlTree.Element] = {}
    for ElemValue in RootValue.iter():
        if ElemValue.tag.rsplit("}", 1)[-1] != "swReference":
            continue
        try:
            Elements[int(ElemValue.attrib.get("id", ""))] = ElemValue
        except ValueError:
            continue
    return Elements


# this definition exists because focused behavior needs one stable owner
def PatchAsmMut(
    AsmValue: AssemblyData, Native: NativeAssembly, Streams: dict[str, bytes]
) -> tuple[str, ...]:
    Original = {Instance.id: Instance for Instance in AsmInstances(Native)}
    Desired = {Instance.id: Instance for Instance in AsmValue.instances}
    if not set(Original) <= set(Desired):
        return ()
    Prefix, RootValue, Trailing = KeywordsRoot(Streams[ComponentTreeStream])
    Elements = AsmRefElements(RootValue)
    Rewritten: list[str] = []
    for InstanceId, Target in Desired.items():
        Source = Original[InstanceId]
        InstanceNativeId = NativeId(InstanceId, "sldasm:instance:")
        ElemValue = Elements.get(InstanceNativeId or -1)
        if ElemValue is None:
            continue
        if (
            Target.owner_definition_id != Source.owner_definition_id
            or Target.order != Source.order
            or Target.fixed != Source.fixed
        ):
            continue
        InstanceValues = {
            "swModelRef": str(
                NativeId(Target.definition_id, "sldasm:definition:")
                or ElemValue.attrib.get("swModelRef", "")
            ),
            "swReferenceNumber": Target.reference_number,
            "swConfigurationName": Target.configuration_name,
            "swConfigurationId": Target.configuration_id,
            "swTransform": " ".join(
                (format(Value, ".17g") for Value in NativeAsmMatrix(Target.transform))
            ),
            "swSuppressed": YesText(Target.suppressed),
            "swHidden": YesText(Target.hidden),
            "swFlexible": YesText(Target.flexible),
            "swExcludeFromBOM": YesText(Target.exclude_from_bom),
        }
        RefNumber = Target.reference_number or Source.reference_number
        Suffix = f"-{RefNumber}"
        TargetName = (
            Target.name[: -len(Suffix)]
            if Target.name.endswith(Suffix)
            else Source.name[: -len(f"-{Source.reference_number}")]
        )
        InstanceValues["swName"] = TargetName
        for KeyValue, Value in InstanceValues.items():
            if ElemValue.attrib.get(KeyValue) != Value:
                ElemValue.attrib[KeyValue] = Value
                if InstanceId not in Rewritten:
                    Rewritten.append(InstanceId)
    if Rewritten:
        Streams[ComponentTreeStream] = KeywordsBytes(Prefix, RootValue, Trailing)
    return tuple(Rewritten)


# this definition exists because focused behavior needs one stable owner
def NativeAsmMatrix(Matrix: Matrix4) -> tuple[float, ...]:
    Values = Matrix.values
    Result = [0.0] * 16
    Result[0], Result[4], Result[8], Result[12] = (
        Values[0],
        Values[1],
        Values[2],
        Values[3] / 1000.0,
    )
    Result[1], Result[5], Result[9], Result[13] = (
        Values[4],
        Values[5],
        Values[6],
        Values[7] / 1000.0,
    )
    Result[2], Result[6], Result[10], Result[14] = (
        Values[8],
        Values[9],
        Values[10],
        Values[11] / 1000.0,
    )
    Result[3], Result[7], Result[11], Result[15] = (
        Values[12],
        Values[13],
        Values[14],
        Values[15],
    )
    if not all((MathValue.isfinite(Value) for Value in Result)):
        raise SldprtFormatError("component transform contains a non-finite value")
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def YesText(Value: bool) -> str:
    return "YES" if Value else "NO"


# this definition exists because focused behavior needs one stable owner
def ReadAsmMates(
    Native: NativeAssembly,
    Streams: Mapping[str, bytes],
    SourcePath: str,
) -> dict[str, MateRule]:
    DefinitionMap = {
        Definition.object_id: Definition.object_id for Definition in Native.definitions
    }
    ItemMap = {
        ItemValue.object_id: ItemValue.object_id for ItemValue in Native.occurrences
    }
    Ignored, Ignored, OriginalMates, Ignored = AsmMates(
        Native,
        (
            (
                Native,
                SldprtArchive.from_bytes(BuildSldprt(Streams)),
                DefinitionMap,
                ItemMap,
                SourcePath,
            ),
        ),
    )
    return {MateValue.id: MateValue for MateValue in OriginalMates}


# this predicate exists because mate identity fields must remain donor stable
def IsSameMate(Source: MateRule, Target: MateRule) -> bool:
    return (
        Target.name == Source.name
        and Target.kind == Source.kind
        and Target.owner_definition_id == Source.owner_definition_id
        and (Target.entity_ids == Source.entity_ids)
        and (Target.order == Source.order)
        and (Target.parameter_ids == Source.parameter_ids)
        and (Target.suppressed == Source.suppressed)
        and (Target.driving == Source.driving)
    )


# this definition exists because native mate lookup has one binary identity format
def NativeMateItem(
    Native: NativeAssembly, MateId: str
) -> tuple[NativeMateList, NativeMate] | None:
    Parts = MateId.split(":")
    if len(Parts) != 5:
        return None
    try:
        ListIndex = int(Parts[3])
        MateOrder = int(Parts[4])
    except ValueError:
        return None
    if not 0 <= ListIndex < len(Native.mate_lists):
        return None
    MateList = Native.mate_lists[ListIndex]
    MateValue = next(
        (ItemValue for ItemValue in MateList.mates if ItemValue.order == MateOrder),
        None,
    )
    return (MateList, MateValue) if MateValue is not None else None


# this predicate exists because native mate values require offset aware mutation
def IsPatchValueMut(
    BufferMut: bytearray, MateValue: NativeMate, TargetValue: ParameterValue | None
) -> bool:
    Values = NativeMateB(TargetValue, MateValue)
    if Values is None:
        return False
    for Index, NativeValue in enumerate(Values):
        Struct.pack_into(
            "<d", BufferMut, MateValue.dimensions[Index].value_offset, NativeValue
        )
    return True


# this predicate exists because native mate alignment has a coded binary field
def IsPatchAlignMut(
    BufferMut: bytearray, MateValue: NativeMate, TargetValue: AnyValue
) -> bool:
    AlignmentCode = next(
        (
            CodeValue
            for CodeValue, Alignment in NativeMateAlignmentByCode.items()
            if Alignment.kind == str(TargetValue)
            or Alignment.kind == getattr(TargetValue, "value", None)
        ),
        None,
    )
    Offset = NativeMateA(BufferMut, MateValue)
    if AlignmentCode is None or Offset is None:
        return False
    Struct.pack_into("<H", BufferMut, Offset, AlignmentCode)
    return True


# this definition exists because focused behavior needs one stable owner
def PatchAsmMateMut(
    AsmValue: AssemblyData,
    Native: NativeAssembly,
    Streams: dict[str, bytes],
    SourcePath: str,
) -> tuple[str, ...]:
    Original = ReadAsmMates(Native, Streams, SourcePath)
    Desired = {MateValue.id: MateValue for MateValue in AsmValue.mates}
    if set(Original) != set(Desired):
        return ()
    Buffers: dict[str, bytearray] = {}
    Rewritten: list[str] = []
    for MateId, Target in Desired.items():
        Source = Original[MateId]
        if not IsSameMate(Source, Target):
            continue
        NativeItem = NativeMateItem(Native, MateId)
        if NativeItem is None:
            continue
        MateList, NativeMate = NativeItem
        Buffer = Buffers.setdefault(
            MateList.stream, bytearray(Streams[MateList.stream])
        )
        ValueChanged = Target.value != Source.value and IsPatchValueMut(
            Buffer, NativeMate, Target.value
        )
        AlignChanged = Target.alignment != Source.alignment and IsPatchAlignMut(
            Buffer, NativeMate, Target.alignment
        )
        if (ValueChanged or AlignChanged) and MateId not in Rewritten:
            Rewritten.append(MateId)
    for Stream, Buffer in Buffers.items():
        Streams[Stream] = bytes(Buffer)
    return tuple(Rewritten)


# this definition exists because focused behavior needs one stable owner
def NativeMateB(
    Value: ParameterValue | None, MateValue: NativeMate
) -> tuple[float, ...] | None:
    if Value is None or not MateValue.dimensions:
        return None
    if isinstance(Value.value, bool) or not isinstance(Value.value, (int, float)):
        return None
    Number = float(Value.value)
    if not MathValue.isfinite(Number):
        return None
    Semantic = MateValueSemantics.get(MateValue.kind)
    if Semantic == "length" and Value.kind is ValueKind.LENGTH:
        Factor = {"": 1.0, "mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4}.get(
            Value.unit.casefold()
        )
        return (Number * Factor / 1000.0,) if Factor is not None else None
    if Semantic == "angle" and Value.kind is ValueKind.ANGLE:
        Factor = {"": 1.0, "rad": 1.0, "deg": MathValue.pi / 180.0}.get(
            Value.unit.casefold()
        )
        return (Number * Factor,) if Factor is not None else None
    if (
        Semantic == "ratio"
        and Value.kind is ValueKind.NUMBER
        and (len(MateValue.dimensions) >= 2)
    ):
        Denominator = MateValue.dimensions[1].value
        return (Number * Denominator, Denominator)
    return None


# this definition exists because focused behavior needs one stable owner
def NativeMateA(DataValue: bytes | bytearray, MateValue: NativeMate) -> int | None:
    Start = MateValue.record_offset
    EndValue = Start + MateValue.record_length
    Encoded = MateValue.name.encode("utf-16le")
    TextStart = bytes(DataValue).find(Encoded, Start, EndValue)
    if TextStart < 0:
        return None
    Offset = TextStart + len(Encoded) + 159
    return Offset if Offset + 2 <= EndValue else None


# this definition exists because focused behavior needs one stable owner
def Definition(Definition: ComponentDefinition) -> tuple[AnyValue, ...]:
    return (
        Definition.id,
        Definition.name,
        Definition.kind,
        Definition.configuration_name,
    )


# this definition exists because focused behavior needs one stable owner
def InstanceValues(Instance: ComponentInstance) -> tuple[AnyValue, ...]:
    return (
        Instance.id,
        Instance.name,
        Instance.definition_id,
        Instance.owner_definition_id,
        tuple((RoundNumber(Value) for Value in Instance.transform.values)),
        Instance.order,
        Instance.reference_number,
        Instance.configuration_name,
        Instance.configuration_id,
        Instance.suppressed,
        Instance.hidden,
        Instance.fixed,
        Instance.flexible,
        Instance.exclude_from_bom,
    )


# this definition exists because focused behavior needs one stable owner
def AsmStructure(AsmValue: AssemblyData) -> tuple[AnyValue, ...]:
    return (
        AsmValue.root_definition_id,
        tuple(
            (Definition(DefinitionValue) for DefinitionValue in AsmValue.definitions)
        ),
        tuple((InstanceValues(Instance) for Instance in AsmValue.instances)),
    )


# this definition exists because focused behavior needs one stable owner
def NativeAsmData(Native: NativeAssembly) -> AsmData:
    return AsmData(
        AsmDefinitionId(Native.root_definition_id),
        AsmDefinitions(Native, {}, {}, {}, {}, "<memory>"),
        AsmInstances(Native),
    )


# this definition exists because focused behavior needs one stable owner
def NativeAsmValues(Native: NativeAssembly) -> tuple[AnyValue, ...]:
    return AsmStructure(NativeAsmData(Native))


# this definition exists because focused behavior needs one stable owner
def DivergedKeys(
    Donor: Mapping[str, Any], Desired: Mapping[str, Any]
) -> tuple[str, ...]:
    return tuple(sorted(set(Donor) ^ set(Desired))) + tuple(
        (
            KeyValue
            for KeyValue in sorted(set(Donor) & set(Desired))
            if Donor[KeyValue] != Desired[KeyValue]
        )
    )


# this definition exists because focused behavior needs one stable owner
def DivergedDonor(AsmValue: AssemblyData, Native: NativeAssembly) -> tuple[str, ...]:
    Donor = NativeAsmData(Native)
    Names: list[str] = []
    if AsmValue.root_definition_id != Donor.root_definition_id:
        Names.append("donor_root_definition_diverged")
    if tuple((ItemValue.id for ItemValue in Donor.definitions)) != tuple(
        (ItemValue.id for ItemValue in AsmValue.definitions)
    ):
        Names.append("donor_definition_order_diverged")
    if tuple((ItemValue.id for ItemValue in Donor.instances)) != tuple(
        (ItemValue.id for ItemValue in AsmValue.instances)
    ):
        Names.append("donor_instance_order_diverged")
    Names.extend(
        (
            f"donor_definition_diverged:{KeyValue}"
            for KeyValue in DivergedKeys(
                {
                    ItemValue.id: Definition(ItemValue)
                    for ItemValue in Donor.definitions
                },
                {
                    ItemValue.id: Definition(ItemValue)
                    for ItemValue in AsmValue.definitions
                },
            )
        )
    )
    Names.extend(
        (
            f"donor_instance_diverged:{KeyValue}"
            for KeyValue in DivergedKeys(
                {
                    ItemValue.id: InstanceValues(ItemValue)
                    for ItemValue in Donor.instances
                },
                {
                    ItemValue.id: InstanceValues(ItemValue)
                    for ItemValue in AsmValue.instances
                },
            )
        )
    )
    return tuple(Names)


# this definition exists because focused behavior needs one stable owner
def MateValues(
    Entities: Sequence[MateEntity],
    Mates: Sequence[MateConstraint],
    Groups: Sequence[MateGroup],
) -> tuple[AnyValue, ...]:
    return (
        tuple(
            (
                (
                    Entity.id,
                    Entity.owner_definition_id,
                    Entity.instance_path,
                    Entity.kind,
                    Entity.source_entity_id,
                    Entity.selection_id,
                    Entity.frame,
                    Entity.radius,
                )
                for Entity in Entities
            )
        ),
        tuple(
            (
                (
                    MateValue.id,
                    MateValue.name,
                    MateValue.kind,
                    MateValue.owner_definition_id,
                    MateValue.entity_ids,
                    MateValue.order,
                    MateParamValue(MateValue.value),
                    MateValue.parameter_ids,
                    MateValue.alignment,
                    MateValue.suppressed,
                    MateValue.driving,
                )
                for MateValue in Mates
            )
        ),
        tuple(
            (
                (
                    Group.id,
                    Group.name,
                    Group.owner_definition_id,
                    Group.mate_ids,
                    Group.parent_group_id,
                    Group.order,
                )
                for Group in Groups
            )
        ),
    )


# this definition exists because focused behavior needs one stable owner
def MateParamValue(Value: ParameterValue | None) -> AnyValue:
    if (
        Value is None
        or isinstance(Value.value, bool)
        or (not isinstance(Value.value, (int, float)))
    ):
        return Value
    Number = float(Value.value)
    if Value.kind is ValueKind.LENGTH:
        Factor = {"": 1.0, "mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4}.get(
            Value.unit.casefold()
        )
        if Factor is not None:
            return (ValueKind.LENGTH, RoundNumber(Number * Factor))
    if Value.kind is ValueKind.ANGLE:
        Factor = {"": 1.0, "rad": 1.0, "deg": MathValue.pi / 180.0}.get(
            Value.unit.casefold()
        )
        if Factor is not None:
            return (ValueKind.ANGLE, RoundNumber(Number * Factor))
    if Value.kind is ValueKind.NUMBER:
        return (ValueKind.NUMBER, RoundNumber(Number))
    return Value


# this definition exists because focused behavior needs one stable owner
def MeshValues(Meshes: Sequence[Mesh]) -> tuple[AnyValue, ...]:
    return tuple(
        (
            (
                MeshValue.id,
                MeshValue.name,
                MeshValue.vertices,
                MeshValue.triangles,
                MeshValue.normals,
            )
            for MeshValue in Meshes
        )
    )


# this definition exists because preserved parasolid payloads need validated extraction
def ParasolidData(DocValue: CadDocument) -> tuple[bytes, ...]:
    Candidates: list[bytes] = []
    for Payload in DocValue.brep_payloads:
        if (
            Payload.role != PayloadRole.BREP
            or Payload.format_id.casefold() != "parasolid"
            or Payload.data is None
        ):
            continue
        try:
            Decoded = DecodePartitionStream(Payload.data, Payload.source_stream)
        except SldprtFormatError:
            continue
        Candidates.extend(
            (
                ItemValue.data
                for ItemValue in Decoded
                if IsNativeParasolidPayload(ItemValue.data)
            )
        )
    return tuple(Candidates)


# this definition exists because parasolid bodies need native feature ownership ids
def BrepFeatureIds(
    DocValue: CadDocument, ObjectIds: Mapping[str, int]
) -> dict[str, int]:
    if DocValue.brep is None:
        return {}
    FeatureIds: dict[str, int] = {}
    DesignBodies = {BodyValue.id: BodyValue for BodyValue in DocValue.bodies}
    SingleFeatureId = (
        DocValue.bodies[0].final_feature_id if len(DocValue.bodies) == 1 else ""
    )
    for BrepBody in DocValue.brep.bodies:
        FeatureId = str(BrepBody.attributes.get("feature_id", ""))
        if not FeatureId and BrepBody.design_body_id in DesignBodies:
            FeatureId = DesignBodies[BrepBody.design_body_id].final_feature_id
        if not FeatureId and len(DocValue.brep.bodies) == 1:
            FeatureId = SingleFeatureId
        NativeId = ObjectIds.get(f"feature:{FeatureId}")
        if NativeId is not None:
            FeatureIds[BrepBody.id] = NativeId
    return FeatureIds


# this definition exists because focused behavior needs one stable owner
def Parasolid(
    DocValue: CadDocument, ObjectIds: Mapping[str, int] | None = None
) -> tuple[bytes | None, str]:
    Candidates = ParasolidData(DocValue)
    if Candidates:
        return (EncodePartitionStream(max(Candidates, key=len)), "preserved")
    if DocValue.assembly is not None:
        return (None, "none")
    if DocValue.brep is None:
        if (
            not DocValue.feature_timeline
            and (not DocValue.sketches)
            and (not DocValue.bodies)
            and (not DocValue.meshes)
        ):
            return (EncodeBlankPartition(), "generated")
        return (EncodeBlankPartition(), "none")
    FeatureIds = BrepFeatureIds(DocValue, ObjectIds or {})
    try:
        return (
            EncodePartitionStream(
                EncodeBrepModel(
                    DocValue.brep,
                    solidworks_feature_ids=(
                        FeatureIds
                        if len(FeatureIds) == len(DocValue.brep.bodies)
                        else None
                    ),
                )
            ),
            "generated",
        )
    except ParasolidWriteError as ErrorInfo:
        return (None, f"unsupported:{ErrorInfo}")


# this definition exists because focused behavior needs one stable owner
def SolidworksXml(Model: str, Config: str) -> bytes:
    ModelValue = XmlAttr(Model)
    ConfigValue = XmlAttr(Config)
    return f'<?xml version="1.0"?><swSolidWorks><swModel swName="{ModelValue}" swConfigurationName="{ConfigValue}"/></swSolidWorks>'.encode(
        "utf-8"
    )


# this definition exists because focused behavior needs one stable owner
def Solidworks() -> dict[str, bytes]:
    return {
        ContentTypesStream: b'<?xml version="1.0"?>\r\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/custom.xml" ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/></Types>\r\n',
        RelationshipsStream: b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties" Target="docProps/custom.xml"/></Relationships>\r\n',
        "docProps/app.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Template>Normal.dotm</Template><TotalTime>1526</TotalTime><Application>SOLIDWORKS</Application><DocSecurity>0</DocSecurity><Company>Dassault Systèmes SolidWorks Corporation</Company><LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc><HyperlinksChanged>false</HyperlinksChanged><AppVersion>23.0000</AppVersion></Properties>\r\n'.encode(
            "utf-8"
        ),
        "docProps/core.xml": b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:lastModifiedBy>Kit</dc:lastModifiedBy><dcterms:created>2026-08-02T17:13:26Z</dcterms:created><dcterms:modified>2026-08-02T17:13:27Z</dcterms:modified></cp:coreProperties>\r\n',
        "docProps/custom.xml": b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><propertySection xmlns="" name="DocumentSummaryInformation" fmtid="{D5CDD502-2E9C-101B-9397-08002B2CF9AE}"><property name="" pid="1" TypeID="0"><vt:i2>65001</vt:i2></property><property name="" pid="22" TypeID="0"><vt:bool>No</vt:bool></property><propertyNameDictionaryElement name="" pid="0"></propertyNameDictionaryElement></propertySection><propertySection xmlns="" name="UserDefinedProperties" fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"><property name="" pid="1" TypeID="0"><vt:i2>65001</vt:i2></property><propertyNameDictionaryElement name="" pid="0"></propertyNameDictionaryElement></propertySection></Properties>\r\n',
    }


# this definition exists because focused behavior needs one stable owner
def XmlAttr(Value: str) -> str:
    return (
        Value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# this definition exists because focused behavior needs one stable owner
def TargetFormatId(DocValue: CadDocument) -> str:
    return KAsmFormatId if DocValue.assembly is not None else KFormatId


# this definition exists because focused behavior needs one stable owner
def TargetPath(Target: Destination) -> PathValue | None:
    if isinstance(Target, (str, PathValue)):
        return PathValue(Target).expanduser().resolve()
    return None


# this definition exists because focused behavior needs one stable owner
def WriteTargetMut(
    Target: Destination, DataValue: bytes, Overwrite: bool
) -> PathValue | None:
    PathValue = TargetPath(Target)
    if PathValue is None:
        try:
            Written = Target.write(DataValue)
        except TypeError as ErrorInfo:
            raise TypeError(
                "SLDPRT destination stream must accept bytes"
            ) from ErrorInfo
        if isinstance(Written, int) and Written != len(DataValue):
            raise OSError("SLDPRT destination stream accepted a partial write")
        return None
    if PathValue.exists() and (not Overwrite):
        raise FileExistsError(PathValue)
    PathValue.parent.mkdir(parents=True, exist_ok=True)
    Descriptor, TemporaryName = Tempfile.mkstemp(
        prefix=f".{PathValue.name}.", suffix=".tmp", dir=PathValue.parent
    )
    try:
        with OsModule.fdopen(Descriptor, "wb") as Stream:
            Stream.write(DataValue)
            Stream.flush()
            OsModule.fsync(Stream.fileno())
        OsModule.replace(TemporaryName, PathValue)
    except BaseException:
        with Suppress(FileNotFoundError):
            OsModule.unlink(TemporaryName)
        raise
    return PathValue


# this definition exists because assembly part metadata shares one decode pass
def AsmPartFields(
    Archive: SldprtArchive, Settings: ReadOptions
) -> tuple[AnyValue, ...]:
    SelectedStream = ResolvedStream(Archive.streams, ResolvedFeaturesStream)
    Model = DecodeNativeModel(
        Archive.require(KeywordsStream),
        Archive.require(SelectedStream),
        resolved_stream=SelectedStream,
    )
    ConfigValues = Configurations(Model, Settings.configuration)
    ParamValues = Parameters(Model)
    ParamIds = {Param.id for Param in ParamValues}
    PlaneValues = Planes(Model, ParamIds)
    SketchValues = Sketches(Model, ParamIds)
    SelectValues = Selections(Model)
    TimeValues = Timeline(Model, SelectValues)
    return (
        Model,
        ConfigValues,
        ParamValues,
        PlaneValues,
        SketchValues,
        SelectValues,
        TimeValues,
    )


# this definition exists because focused behavior needs one stable owner
def AsmDoc(
    Adapter: SldprtAdapter,
    Archive: SldprtArchive,
    DataValue: bytes,
    Label: str,
    Settings: ReadOptions,
) -> CadDoc:
    Native = DecodeNativeAsm(Archive, include_tessellation=True)
    (
        Model,
        ConfigValues,
        ParamValues,
        PlaneValues,
        SketchValues,
        SelectValues,
        TimeValues,
    ) = AsmPartFields(Archive, Settings)
    Meshes, MeshIds = AsmMeshes(Native)
    Index = ComponentFile(Label, Settings)
    ResolveComponents = Settings.values.get("resolve_components", True) is not False
    Documents, DocIds, ResolvedPaths, DocDiagnostics = AsmDocuments(
        Adapter, Native, Index if ResolveComponents else {}, Settings
    )
    Definitions = AsmDefinitions(
        Native,
        DocIds,
        ResolvedPaths,
        {DocValue.id: DocValue.document for DocValue in Documents},
        MeshIds,
        Label,
    )
    Instances = AsmInstances(Native)
    MateSourceValues, SourceDiagnostics = MateSources(
        Native, Archive, Label, Index, Settings
    )
    MatePayloads, MateEntities, Mates, MateGroups = AsmMates(Native, MateSourceValues)
    FlatMateValues = FlattenedMates(Native, Mates)
    PayloadSettings = ReadOptions(
        configuration=Settings.configuration,
        include_brep=Settings.include_brep,
        include_tessellation=Settings.include_tessellation,
        strict=False,
        values=Settings.values,
    )
    BrepValues, PayloadDiagnostics = BrepPayloads(Archive, PayloadSettings)
    CompanionPayloads = (
        Companion(Label)
        if Settings.include_brep
        and Settings.values.get("discover_companions", True) is not False
        else ()
    )
    Unresolved = tuple(
        (
            Definition
            for Definition in Native.definitions
            if Definition.document_type == "PART"
            and Definition.object_id not in DocIds
            and (Definition.object_id not in MeshIds)
        )
    )
    if Unresolved and Settings.strict and ResolveComponents:
        Names = ", ".join((Definition.name for Definition in Unresolved))
        raise SldprtFormatError(
            f"assembly component sources and tessellation are unavailable: {Names}"
        )
    Diagnostics = (
        tuple(
            (
                DiagValue(
                    code="sldasm.native_record_unresolved",
                    message=Message,
                    severity=Severity.INFO,
                )
                for Message in Model.diagnostics
            )
        )
        + PayloadDiagnostics
        + DocDiagnostics
        + SourceDiagnostics
    )
    PathRecords = Flattened(Native)
    LinkedDocuments = {DocValue.id: DocValue.document for DocValue in Documents}
    LinkedPartDocuments = tuple(
        (
            DocValue
            for DocValue in Documents
            if DocValue.document.source.format_id == KFormatId
        )
    )
    LinkedAsmDocuments = tuple(
        (
            DocValue
            for DocValue in Documents
            if DocValue.document.source.format_id == KAsmFormatId
        )
    )
    AsmValue = AsmData(
        root_definition_id=AsmDefinitionId(Native.root_definition_id),
        definitions=Definitions,
        instances=Instances,
        documents=Documents,
        mate_entities=MateEntities,
        mates=Mates,
        mate_groups=MateGroups,
        attributes=FrozenMapping(
            {
                "application_version": Native.application_version,
                "configurations": tuple(
                    (
                        {
                            "native_object_id": Config.object_id,
                            "native_configuration_id": Config.configuration_id,
                            "name": Config.name,
                            "reference": Config.reference,
                            "model_id": Config.model_id,
                            "most_recent": Config.most_recent,
                            "needs_update": Config.needs_update,
                            "native_attributes": Config.attributes,
                        }
                        for Config in Native.configurations
                    )
                ),
                "display_states": tuple(
                    (
                        {
                            "native_object_id": State.object_id,
                            "name": State.name,
                            "configuration_id": State.configuration_id,
                            "native_attributes": State.attributes,
                        }
                        for State in Native.display_states
                    )
                ),
                "flattened_occurrences": PathRecords,
                "flattened_occurrence_count": len(PathRecords),
                "flattened_mate_occurrences": FlatMateValues,
                "flattened_mate_occurrence_count": len(FlatMateValues),
                "native_file_count": len(Native.files),
                "native_definition_count": len(Native.definitions),
                "native_instance_count": len(Native.occurrences),
                "linked_document_count": len(Documents),
                "linked_part_document_count": len(LinkedPartDocuments),
                "linked_assembly_document_count": len(LinkedAsmDocuments),
                "linked_sketch_count": sum(
                    (len(DocValue.sketches) for DocValue in LinkedDocuments.values())
                ),
                "linked_feature_count": sum(
                    (
                        len(DocValue.feature_timeline)
                        for DocValue in LinkedDocuments.values()
                    )
                ),
            }
        ),
    )
    DocValue = CadDoc(
        source=CadSource(
            format_id=KAsmFormatId,
            path=Label,
            sha256=Hashlib.sha256(DataValue).hexdigest(),
            container_version=str(Archive.format_version),
            application_version=str(Native.application_version),
            attributes=FrozenMapping(
                {"file_id": Archive.file_id, "stream_count": len(Archive.records)}
            ),
        ),
        configurations=ConfigValues,
        parameters=ParamValues,
        support_planes=PlaneValues,
        sketches=SketchValues,
        selections=SelectValues,
        feature_timeline=TimeValues,
        bodies=(),
        meshes=Meshes,
        brep_payloads=(*BrepValues, *MatePayloads, *CompanionPayloads),
        diagnostics=Diagnostics,
        capabilities=Adapter.info.capabilities,
        metadata=FrozenMapping(
            {
                "adapter": KAsmFormatId,
                "file_id": Archive.file_id,
                "native_class_names": tuple(
                    dict.fromkeys((ItemValue.name for ItemValue in Model.classes))
                ),
                "native_feature_count": len(Model.features),
                "native_name_record_count": len(Model.names),
                "native_scalar_count": len(Model.scalars),
                "stream_names": tuple((Record.name for Record in Archive.records)),
                "assembly_definition_count": len(Definitions),
                "assembly_instance_count": len(Instances),
                "assembly_flattened_occurrence_count": len(PathRecords),
                "assembly_mate_count": len(Mates),
                "assembly_flattened_mate_count": len(FlatMateValues),
                "assembly_mesh_count": len(Meshes),
            }
        ),
        units=UnitSystem.MILLIMETER,
        assembly=AsmValue,
    )
    DocValue.assert_valid()
    return DocValue


# this definition exists because focused behavior needs one stable owner
def ComponentFile(
    Label: str, Settings: ReadOptions
) -> dict[str, tuple[PathValue, ...]]:
    RequestedRoot = Settings.values.get("component_search_root")
    if RequestedRoot:
        RootValue = PathValue(str(RequestedRoot)).expanduser().resolve()
    else:
        Source = PathValue(Label)
        if not Source.is_file():
            return {}
        RootValue = Source.resolve().parent
    if not RootValue.is_dir():
        return {}
    Result: Defaultdict[str, list[PathValue]] = Defaultdict(list)
    for FilePath in RootValue.rglob("*"):
        if FilePath.is_file() and FilePath.suffix.casefold() in FormatIdBySuffix:
            Result[FilePath.name.casefold()].append(FilePath.resolve())

    # this callback exists because local behavior needs one focused transformation
    return {
        NameValue: tuple(sorted(Paths, key=lambda PathValue: str(PathValue).casefold()))
        for NameValue, Paths in Result.items()
    }


# this definition exists because focused behavior needs one stable owner
def ResolvedPath(
    SourcePath: str, Index: dict[str, tuple[Path, ...]]
) -> PathValue | None:
    Native = PureWindowsPath(SourcePath)
    Candidates = Index.get(Native.name.casefold(), ())
    if not Candidates:
        return None
    NativeParts = tuple((PartValue.casefold() for PartValue in Native.parts))

    # this definition exists because focused behavior needs one stable owner
    def Score(Choice: Path) -> tuple[int, str]:
        ChoiceParts = tuple((PartValue.casefold() for PartValue in Choice.parts))
        Matches = 0
        for LeftValue, Right in zip(reversed(NativeParts), reversed(ChoiceParts)):
            if LeftValue != Right:
                break
            Matches += 1
        return (Matches, str(Choice).casefold())

    return max(Candidates, key=Score)


# this definition exists because assembly source discovery must retain diagnostics
def FindAsmSources(Native: NativeAssembly, Index: dict[str, tuple[Path, ...]]) -> tuple[
    dict[PathValue, list[NativeAsmDefinition]],
    dict[int, PathValue],
    list[DiagValue],
]:
    RootId = Native.root_definition_id
    DefinitionsByPath: Defaultdict[PathValue, list[NativeAsmDefinition]] = Defaultdict(
        list
    )
    ResolvedPaths: dict[int, PathValue] = {}
    Diagnostics: list[DiagValue] = []
    for Definition in Native.definitions:
        if Definition.object_id == RootId:
            continue
        Resolved = ResolvedPath(Definition.source_path, Index)
        if Resolved is None:
            Diagnostics.append(
                DiagValue(
                    code="sldasm.component_source_missing",
                    message=f"component source is unavailable: {Definition.source_path}",
                    severity=Severity.INFO,
                    attributes=FrozenMapping(
                        {
                            "native_definition_id": Definition.object_id,
                            "configuration": Definition.configuration_name,
                        }
                    ),
                )
            )
            continue
        ResolvedPaths[Definition.object_id] = Resolved
        DefinitionsByPath[Resolved].append(Definition)
    return (dict(DefinitionsByPath), ResolvedPaths, Diagnostics)


# this definition exists because focused behavior needs one stable owner
def AsmDocuments(
    Adapter: SldprtAdapter,
    Native: NativeAssembly,
    Index: dict[str, tuple[Path, ...]],
    Settings: ReadOptions,
) -> tuple[
    tuple[ComponentDoc, ...],
    dict[int, str],
    dict[int, PathValue],
    tuple[DiagValue, ...],
]:
    if not Index:
        return ((), {}, {}, ())
    DefinitionsByPath, ResolvedPaths, Diagnostics = FindAsmSources(Native, Index)
    Documents: list[ComponentDoc] = []
    DocIds: dict[int, str] = {}

    # this callback exists because local behavior needs one focused transformation
    for Resolved, Definitions in sorted(
        DefinitionsByPath.items(), key=lambda ItemValue: str(ItemValue[0]).casefold()
    ):
        Representative = Definitions[0]
        Values = dict(Settings.values)
        Values["resolve_components"] = False
        Values["discover_companions"] = False
        Options = ReadOptions(
            configuration=Representative.configuration_name or None,
            include_brep=Settings.include_brep,
            include_tessellation=Representative.document_type == "ASSEMBLY",
            strict=Settings.strict,
            values=FrozenMapping(Values),
        )
        try:
            DocValue = Adapter.read(Resolved, Options)
        except (OSError, SldprtFormatError, TypeError, ValueError) as ErrorInfo:
            if Settings.strict:
                raise
            Diagnostics.append(
                DiagValue(
                    code="sldasm.component_decode_failed",
                    message=f"cannot decode {Resolved}: {ErrorInfo}",
                    severity=Severity.WARNING,
                    attributes=FrozenMapping(
                        {
                            "native_definition_ids": tuple(
                                (Definition.object_id for Definition in Definitions)
                            )
                        }
                    ),
                )
            )
            continue
        DocId = f"sldasm:document:{DocValue.source.sha256[:20]}"
        Documents.append(ComponentDoc(DocId, DocValue))
        for Definition in Definitions:
            DocIds[Definition.object_id] = DocId
    return (tuple(Documents), DocIds, ResolvedPaths, tuple(Diagnostics))


# this definition exists because component faces share one indexed mesh accumulator
def MeshGeometry(Component: AnyValue) -> tuple[AnyValue, ...]:
    Vertices: list[VectorThree] = []
    Normals: list[VectorThree] = []
    Triangles: list[tuple[int, int, int]] = []
    Faces: list[dict[str, AnyValue]] = []
    for FaceValue in Component.faces:
        VertexStart = len(Vertices)
        TriangleStart = len(Triangles)
        Vertices.extend((VectorThree(*Point) for Point in FaceValue.positions_mm))
        Normals.extend((VectorThree(*Normal) for Normal in FaceValue.normals))
        Triangles.extend(
            (
                tuple((Index + VertexStart for Index in Triangle))
                for Triangle in FaceValue.triangle_indices
            )
        )
        Faces.append(
            {
                "face_id": FaceValue.face_id,
                "vertex_start": VertexStart,
                "vertex_count": len(FaceValue.positions_mm),
                "triangle_start": TriangleStart,
                "triangle_count": len(FaceValue.triangle_indices),
                "strip_lengths": FaceValue.strip_lengths,
                "source_offset": FaceValue.offset,
                "source_length": FaceValue.record_length,
            }
        )
    return (Vertices, Normals, Triangles, Faces)


# this definition exists because focused behavior needs one stable owner
def AsmMeshes(Native: NativeAssembly) -> tuple[tuple[MeshValue, ...], dict[int, str]]:
    DefinitionByPath = {
        ItemValue.path.casefold(): ItemValue.definition_id
        for ItemValue in Native.occurrence_paths
    }
    ItemById = {ItemValue.object_id: ItemValue for ItemValue in Native.occurrences}
    Identity = {ObjectId: ObjectId for ObjectId in ItemById}
    DefinitionById = {
        Definition.object_id: Definition for Definition in Native.definitions
    }
    Result: list[MeshValue] = []
    MeshIds: dict[int, str] = {}
    for Component in Native.display_components:
        DefinitionId = DefinitionByPath.get(Component.occurrence_path.casefold())
        if DefinitionId is None:
            try:
                PathValue = MateInstance(Native, Identity, Component.occurrence_path)
            except SldprtFormatError:
                PathValue = ()
            if PathValue:
                DefinitionId = ItemById[PathValue[-1]].definition_id
        if DefinitionId is None or DefinitionId in MeshIds:
            continue
        Vertices, Normals, Triangles, Faces = MeshGeometry(Component)
        Definition = DefinitionById[DefinitionId]
        MeshId = f"sldasm:mesh:{DefinitionId}"
        Result.append(
            MeshValue(
                id=MeshId,
                name=f"{Definition.name} tessellation",
                vertices=tuple(Vertices),
                triangles=tuple(Triangles),
                normals=tuple(Normals),
                provenance=Provenance(
                    adapter=KAsmFormatId,
                    native_id=str(DefinitionId),
                    spans=(
                        ProvenanceSpan(
                            DisplayListsStream,
                            Component.record_offset,
                            Component.record_length,
                            "component-tessellation",
                        ),
                    ),
                ),
                attributes=FrozenMapping(
                    {
                        "occurrence_path": Component.occurrence_path,
                        "source_path": Component.source_path,
                        "faces": tuple(Faces),
                    }
                ),
            )
        )
        MeshIds[DefinitionId] = MeshId
    return (tuple(Result), MeshIds)


# this definition exists because focused behavior needs one stable owner
def AsmDefinitions(
    Native: NativeAssembly,
    DocIds: dict[int, str],
    ResolvedPaths: dict[int, Path],
    Documents: dict[str, CadDocument],
    MeshIds: dict[int, str],
    Label: str,
) -> tuple[ComponentDefinition, ...]:
    Result: list[ComponentDefinition] = []
    for Definition in Native.definitions:
        DocId = DocIds.get(Definition.object_id, "")
        DocValue = Documents.get(DocId)
        SourcePath = ResolvedPaths.get(Definition.object_id)
        if (
            Definition.object_id == Native.root_definition_id
            and PathValue(Label).is_file()
        ):
            SourcePath = PathValue(Label).resolve()
        KindValue = (
            ComponentKind.ASSEMBLY
            if Definition.document_type == "ASSEMBLY"
            else (
                ComponentKind.PART
                if Definition.document_type == "PART"
                else ComponentKind.NATIVE
            )
        )
        Result.append(
            ComponentDefinition(
                id=AsmDefinitionId(Definition.object_id),
                name=Definition.name,
                kind=KindValue,
                document_id=DocId,
                configuration_name=Definition.configuration_name,
                configuration_id=str(Definition.configuration_id),
                bounding_box=AsmBoundingBox(Definition.bounding_box_m),
                body_ids=(
                    tuple((BodyValue.id for BodyValue in DocValue.bodies))
                    if DocValue is not None and KindValue == ComponentKind.PART
                    else ()
                ),
                mesh_ids=(
                    (MeshIds[Definition.object_id],)
                    if Definition.object_id in MeshIds
                    else ()
                ),
                source_path=(
                    str(SourcePath)
                    if SourcePath is not None
                    else Definition.source_path
                ),
                source_format_id=(
                    KAsmFormatId if KindValue == ComponentKind.ASSEMBLY else KFormatId
                ),
                source_sha256=DocValue.source.sha256 if DocValue is not None else "",
                provenance=Provenance(
                    adapter=KAsmFormatId,
                    native_id=str(Definition.object_id),
                    spans=(
                        ProvenanceSpan(
                            ComponentTreeStream, 0, 0, "component-definition"
                        ),
                    ),
                ),
                attributes=FrozenMapping(
                    {
                        "native_object_id": Definition.object_id,
                        "native_file_id": Definition.file_id,
                        "native_source_path": Definition.source_path,
                        "alternate_configuration_name": Definition.alternate_configuration_name,
                        "last_modified_stamp": Definition.last_modified_stamp,
                        "configuration_flags": Definition.configuration_flags,
                        "child_occurrence_ids": Definition.child_occurrence_ids,
                        "native_attributes": Definition.attributes,
                    }
                ),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def AsmInstances(Native: NativeAssembly) -> tuple[ComponentInstance, ...]:
    return tuple(
        (
            ComponentInstance(
                id=AsmInstanceId(ItemValue.object_id),
                name=f"{ItemValue.name}-{ItemValue.reference_number}",
                definition_id=AsmDefinitionId(ItemValue.definition_id),
                owner_definition_id=AsmDefinitionId(ItemValue.owner_definition_id),
                transform=AsmMatrix(ItemValue.transform),
                order=ItemValue.order,
                reference_number=str(ItemValue.reference_number),
                configuration_name=ItemValue.configuration_name,
                configuration_id=str(ItemValue.configuration_id),
                suppressed=ItemValue.suppressed,
                hidden=ItemValue.hidden,
                fixed=False,
                flexible=ItemValue.flexible,
                exclude_from_bom=ItemValue.exclude_from_bom,
                provenance=Provenance(
                    adapter=KAsmFormatId,
                    native_id=str(ItemValue.object_id),
                    spans=(
                        ProvenanceSpan(ComponentTreeStream, 0, 0, "component-instance"),
                    ),
                ),
                attributes=FrozenMapping(
                    {
                        "native_feature_id": ItemValue.feature_id,
                        "native_reference_number": ItemValue.reference_number,
                        "component_reference": ItemValue.component_reference,
                        "native_transform": ItemValue.transform,
                        "transform_stamp": ItemValue.transform_stamp,
                        "virtual": ItemValue.virtual,
                        "zone": ItemValue.zone,
                        "display_mode": ItemValue.display_mode,
                        "display_quality": ItemValue.display_quality,
                        "edges_in_shaded_mode": ItemValue.edges_in_shaded_mode,
                        "native_attributes": ItemValue.attributes,
                    }
                ),
            )
            for ItemValue in Native.occurrences
        )
    )


# this definition exists because focused behavior needs one stable owner
def MateSources(
    RootValue: NativeAssembly,
    Archive: SldprtArchive,
    Label: str,
    Index: dict[str, tuple[Path, ...]],
    Settings: ReadOptions,
) -> tuple[
    tuple[tuple[NativeAsm, SldprtArchive, dict[int, int], dict[int, int], str], ...],
    tuple[DiagValue, ...],
]:
    Sources = [
        (
            RootValue,
            Archive,
            {
                Definition.object_id: Definition.object_id
                for Definition in RootValue.definitions
            },
            {
                ItemValue.object_id: ItemValue.object_id
                for ItemValue in RootValue.occurrences
            },
            Label,
        )
    ]
    Diagnostics: list[DiagValue] = []
    for Target in RootValue.definitions:
        if (
            Target.document_type != "ASSEMBLY"
            or Target.object_id == RootValue.root_definition_id
        ):
            continue
        Resolved = ResolvedPath(Target.source_path, Index)
        if Resolved is None:
            Message = (
                f"nested assembly mate source is unavailable: {Target.source_path}"
            )
            if Settings.strict:
                raise SldprtFormatError(Message)
            Diagnostics.append(
                DiagValue(
                    code="sldasm.nested_mates_missing",
                    message=Message,
                    severity=Severity.WARNING,
                )
            )
            continue
        NestedArchive = SldprtArchive.open(Resolved)
        Nested = DecodeNativeAsm(NestedArchive, include_tessellation=False)
        try:
            DefinitionMap = NestedMap(RootValue, Nested, Target.object_id)
            ItemMap = NestedItemMap(RootValue, Nested, DefinitionMap)
        except SldprtFormatError as ErrorInfo:
            if Settings.strict:
                raise
            Diagnostics.append(
                DiagValue(
                    code="sldasm.nested_mates_unmapped",
                    message=f"cannot map nested mates from {Resolved}: {ErrorInfo}",
                    severity=Severity.WARNING,
                )
            )
            continue
        Sources.append((Nested, NestedArchive, DefinitionMap, ItemMap, str(Resolved)))
    return (tuple(Sources), tuple(Diagnostics))


# this definition exists because focused behavior needs one stable owner
def NativeKey(Definition: NativeAssemblyDefinition) -> tuple[str, str, str]:
    return (
        PureWindowsPath(Definition.source_path).name.casefold(),
        Definition.configuration_name.casefold(),
        Definition.document_type.casefold(),
    )


# this definition exists because focused behavior needs one stable owner
def NestedMap(
    RootValue: NativeAssembly, Nested: NativeAssembly, TargetRootId: int
) -> dict[int, int]:
    Result = {Nested.root_definition_id: TargetRootId}
    Targets: Defaultdict[tuple[str, str, str], list[NativeAsmDefinition]] = Defaultdict(
        list
    )
    for Definition in RootValue.definitions:
        Targets[NativeKey(Definition)].append(Definition)
    for Definition in Nested.definitions:
        if Definition.object_id == Nested.root_definition_id:
            continue
        Candidates = Targets.get(NativeKey(Definition), [])
        if len(Candidates) != 1:
            raise SldprtFormatError(
                f"nested definition {Definition.name!r} has {len(Candidates)} root mappings"
            )
        Result[Definition.object_id] = Candidates[0].object_id
    return Result


# this definition exists because focused behavior needs one stable owner
def NestedItemMap(
    RootValue: NativeAssembly, Nested: NativeAssembly, DefinitionMap: dict[int, int]
) -> dict[int, int]:
    Result: dict[int, int] = {}
    for ItemValue in Nested.occurrences:
        OwnerId = DefinitionMap[ItemValue.owner_definition_id]
        DefinitionId = DefinitionMap[ItemValue.definition_id]
        Candidates = tuple(
            (
                Target
                for Target in RootValue.occurrences
                if Target.owner_definition_id == OwnerId
                and Target.definition_id == DefinitionId
                and (Target.name.casefold() == ItemValue.name.casefold())
                and (Target.reference_number == ItemValue.reference_number)
                and (Target.feature_id == ItemValue.feature_id)
            )
        )
        if len(Candidates) != 1:
            raise SldprtFormatError(
                f"nested occurrence {ItemValue.name}-{ItemValue.reference_number} has {len(Candidates)} root mappings"
            )
        Result[ItemValue.object_id] = Candidates[0].object_id
    return Result


# this definition exists because focused behavior needs one stable owner
def AsmMates(
    RootValue: NativeAssembly,
    Sources: tuple[
        tuple[NativeAssembly, SldprtArchive, dict[int, int], dict[int, int], str], ...
    ],
) -> tuple[
    tuple[BrepPayload, ...],
    tuple[MateEntity, ...],
    tuple[MateRule, ...],
    tuple[MateGroup, ...],
]:
    Payloads: list[BrepPayload] = []
    Entities: list[MateEntity] = []
    Mates: list[MateRule] = []
    Groups: list[MateGroup] = []
    for SourceIndex, (
        Source,
        Archive,
        DefinitionMap,
        ItemMap,
        SourceLabel,
    ) in enumerate(Sources):
        for ListIndex, MateList in enumerate(Source.mate_lists):
            OwnerId = DefinitionMap[MateList.owner_definition_id]
            StreamData = Archive.require(MateList.stream)
            StreamName = (
                MateList.stream
                if SourceIndex == 0
                else f"{SourceLabel}::{MateList.stream}"
            )
            PayloadId = f"sldasm:mates:{OwnerId}:{ListIndex}"
            Payloads.append(
                MatePayload(
                    PayloadId, StreamName, StreamData, MateList, OwnerId, SourceLabel
                )
            )
            MateIdsByOrder: dict[int, str] = {}
            for MateValue in MateList.mates:
                if MateValue.kind == "group":
                    continue
                MateId = f"sldasm:mate:{OwnerId}:{ListIndex}:{MateValue.order}"
                EntityIds: list[str] = []
                for EntityIndex, NativeEntity in enumerate(MateValue.entities):
                    EntityId = f"{MateId}:entity:{EntityIndex}"
                    EntityIds.append(EntityId)
                    Entities.append(
                        AsmMateEntity(
                            EntityId,
                            OwnerId,
                            Source,
                            ItemMap,
                            NativeEntity,
                            MateValue,
                            StreamName,
                            SourceLabel,
                        )
                    )
                Mates.append(
                    MateRule(
                        id=MateId,
                        name=MateValue.name,
                        kind=NeutralMateKinA(MateValue.kind),
                        owner_definition_id=AsmDefinitionId(OwnerId),
                        entity_ids=tuple(EntityIds),
                        order=MateValue.order,
                        value=NeutralMateA(MateValue),
                        alignment=NeutralMate(MateValue),
                        suppressed=False,
                        driving=True,
                        provenance=MateProvenance(MateValue, StreamName),
                        attributes=FrozenMapping(
                            {
                                "native_kind": MateValue.kind,
                                "native_class_name": MateValue.class_name,
                                "native_class_token": MateValue.class_token,
                                "native_owner_definition_id": MateValue.owner_definition_id,
                                "native_record_offset": MateValue.record_offset,
                                "native_record_length": MateValue.record_length,
                                "native_payload_id": PayloadId,
                                "serialized_strings": MateValue.serialized_strings,
                                "source_document": SourceLabel,
                                "native_alignment_code": MateValue.alignment_code,
                                "native_dimensions": tuple(
                                    (
                                        {
                                            "name": Dimension.name,
                                            "value": Dimension.value,
                                            "value_offset": Dimension.value_offset,
                                        }
                                        for Dimension in MateValue.dimensions
                                    )
                                ),
                                "native_value_m": MateValue.value_m,
                                "native_value_offset": MateValue.value_offset,
                            }
                        ),
                    )
                )
                MateIdsByOrder[MateValue.order] = MateId
            Groups.extend(
                MateGroups(MateList, OwnerId, MateIdsByOrder, StreamName, PayloadId)
            )
    return (tuple(Payloads), tuple(Entities), tuple(Mates), tuple(Groups))


# this definition exists because focused behavior needs one stable owner
def MatePayload(
    PayloadId: str,
    StreamName: str,
    DataValue: bytes,
    MateList: NativeMateList,
    OwnerId: int,
    SourceLabel: str,
) -> BrepPayload:
    return BrepPayload(
        id=PayloadId,
        format_id="solidworks.mates",
        kind="mate-list",
        schema="solidworks.serialized-object-stream",
        sha256=Hashlib.sha256(DataValue).hexdigest(),
        data=DataValue,
        source_stream=StreamName,
        provenance=Provenance(
            adapter=KAsmFormatId,
            native_id=str(MateList.native_id),
            spans=(ProvenanceSpan(StreamName, 0, len(DataValue), "mate-list"),),
        ),
        attributes=FrozenMapping(
            {
                "native_id": MateList.native_id,
                "declared_count": MateList.declared_count,
                "owner_definition_id": OwnerId,
                "source_document": SourceLabel,
                "records": tuple(
                    (
                        {
                            "name": MateValue.name,
                            "kind": MateValue.kind,
                            "class_name": MateValue.class_name,
                            "class_token": MateValue.class_token,
                            "offset": MateValue.record_offset,
                            "length": MateValue.record_length,
                        }
                        for MateValue in MateList.mates
                    )
                ),
            }
        ),
        role=PayloadRole.ASSEMBLY_STRUCTURE,
        file_extension=".bin",
    )


# this definition exists because focused behavior needs one stable owner
def AsmMateEntity(
    EntityId: str,
    OwnerId: int,
    Source: NativeAssembly,
    ItemMap: dict[int, int],
    Entity: NativeMateEntity,
    MateValue: NativeMate,
    StreamName: str,
    SourceLabel: str,
) -> MateEntity:
    PathValue = MateInstance(Source, ItemMap, Entity.component_path)
    SourceEntityId = (
        Entity.persistent_references[-1] if Entity.persistent_references else ""
    )
    return MateEntity(
        id=EntityId,
        owner_definition_id=AsmDefinitionId(OwnerId),
        instance_path=tuple((AsmInstanceId(Value) for Value in PathValue)),
        kind=NeutralMateKind(SourceEntityId),
        source_entity_id=SourceEntityId,
        provenance=MateProvenance(MateValue, StreamName),
        attributes=FrozenMapping(
            {
                "component_path": Entity.component_path,
                "persistent_references": Entity.persistent_references,
                "source_path": Entity.source_path,
                "configuration_name": Entity.configuration_name,
                "source_document": SourceLabel,
            }
        ),
    )


# this definition exists because focused behavior needs one stable owner
def MateInstance(
    Source: NativeAssembly, ItemMap: dict[int, int], ComponentPath: str
) -> tuple[int, ...]:
    if not ComponentPath:
        return ()
    Children: Defaultdict[int, list[NativeAsmItem]] = Defaultdict(list)
    for ItemValue in Source.occurrences:
        Children[ItemValue.owner_definition_id].append(ItemValue)
    OwnerId = Source.root_definition_id
    Result: list[int] = []
    for RawSegment in ComponentPath.split("/"):
        Segment = RawSegment.split("@", 1)[0].strip().casefold()
        Candidates = tuple(
            (
                ItemValue
                for ItemValue in Children.get(OwnerId, [])
                if Segment
                in {
                    ItemValue.name.strip().casefold(),
                    f"{ItemValue.name}-{ItemValue.reference_number}".strip().casefold(),
                }
            )
        )
        if not Candidates:
            return ()
        if len(Candidates) != 1:
            raise SldprtFormatError(
                f"mate component path segment {RawSegment!r} has {len(Candidates)} hierarchy mappings"
            )
        ItemValue = Candidates[0]
        Mapped = ItemMap.get(ItemValue.object_id)
        if Mapped is None:
            raise SldprtFormatError(
                f"mate component path references unmapped occurrence {ItemValue.object_id}"
            )
        Result.append(Mapped)
        OwnerId = ItemValue.definition_id
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def NeutralMateKinA(Value: str) -> MateKind:
    Alias = NativeMateNeutralKind.get(Value)
    if Alias is not None:
        return MateKind(Alias)
    try:
        return MateKind(Value)
    except ValueError:
        return MateKind.NATIVE


# this definition exists because focused behavior needs one stable owner
def NeutralMate(MateValue: NativeMate) -> MateAlignment:
    Alignment = NativeMateAlignmentByCode.get(MateValue.alignment_code)
    if Alignment is None:
        return MateAlignment.UNKNOWN
    return MateAlignment(Alignment.kind)


# this definition exists because focused behavior needs one stable owner
def NeutralMateA(MateValue: NativeMate) -> ParamValue | None:
    Dimensions = MateValue.dimensions
    if not Dimensions:
        return None
    Semantic = MateValueSemantics.get(MateValue.kind)
    if Semantic == "angle":
        return ParamValue(Dimensions[0].value, ValueKind.ANGLE, "rad")
    if Semantic == "length":
        return ParamValue(Dimensions[0].value * 1000.0, ValueKind.LENGTH, "mm")
    if Semantic == "ratio" and len(Dimensions) >= 2:
        Denominator = Dimensions[1].value
        if Denominator != 0.0:
            return ParamValue(Dimensions[0].value / Denominator, ValueKind.NUMBER, "")
    return None


# this definition exists because focused behavior needs one stable owner
def NeutralMateKind(Value: str) -> MateEntityKind:
    Lowered = Value.casefold()
    for Marker, KindValue in NativeMateEntityMarkers:
        if Marker in Lowered:
            return MateEntityKind(KindValue)
    return MateEntityKind.NATIVE


# this definition exists because focused behavior needs one stable owner
def MateProvenance(MateValue: NativeMate, StreamName: str) -> Provenance:
    return Provenance(
        adapter=KAsmFormatId,
        native_id=MateValue.name,
        spans=(
            ProvenanceSpan(
                StreamName,
                MateValue.record_offset,
                MateValue.record_length,
                "mate-record",
            ),
        ),
    )


# this definition exists because focused behavior needs one stable owner
def MateGroups(
    MateList: NativeMateList,
    OwnerId: int,
    MateIdsByOrder: dict[int, str],
    StreamName: str,
    PayloadId: str,
) -> tuple[MateGroup, ...]:
    Result: list[MateGroup] = []
    Records = MateList.mates
    Markers = tuple((Record for Record in Records if Record.kind == "group"))
    for PairIndex in range(0, len(Markers) - 1, 2):
        Marker = Markers[PairIndex]
        EndValue = Markers[PairIndex + 1]
        NextStart = (
            Markers[PairIndex + 2].order
            if PairIndex + 2 < len(Markers)
            else len(Records)
        )
        Members: list[str] = []
        for Choice in Records:
            if (
                Choice.order <= EndValue.order
                or Choice.order >= NextStart
                or Choice.kind == "group"
            ):
                continue
            MateId = MateIdsByOrder.get(Choice.order)
            if MateId is not None:
                Members.append(MateId)
            if Choice.kind == "lock_to_sketch":
                break
        Result.append(
            MateGroup(
                id=f"sldasm:mate-group:{OwnerId}:{Marker.order}",
                name=Marker.name,
                owner_definition_id=AsmDefinitionId(OwnerId),
                mate_ids=tuple(Members),
                order=Marker.order,
                provenance=Provenance(
                    adapter=KAsmFormatId,
                    native_id=Marker.name,
                    spans=(
                        ProvenanceSpan(
                            StreamName,
                            Marker.record_offset,
                            Marker.record_length,
                            "mate-group-start",
                        ),
                        ProvenanceSpan(
                            StreamName,
                            EndValue.record_offset,
                            EndValue.record_length,
                            "mate-group-end",
                        ),
                    ),
                ),
                attributes=FrozenMapping(
                    {
                        "native_payload_id": PayloadId,
                        "start_record_offset": Marker.record_offset,
                        "start_record_length": Marker.record_length,
                        "end_record_offset": EndValue.record_offset,
                        "end_record_length": EndValue.record_length,
                    }
                ),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def Flattened(Native: NativeAssembly) -> tuple[dict[str, AnyValue], ...]:
    Identity = {
        ItemValue.object_id: ItemValue.object_id for ItemValue in Native.occurrences
    }
    return tuple(
        (
            {
                "occurrence_id": AsmInstanceId(ItemValue.occurrence_id),
                "definition_id": AsmDefinitionId(ItemValue.definition_id),
                "path": ItemValue.path,
                "instance_path": tuple(
                    (
                        AsmInstanceId(Value)
                        for Value in MateInstance(Native, Identity, ItemValue.path)
                    )
                ),
                "depth": ItemValue.depth,
            }
            for ItemValue in Native.occurrence_paths
        )
    )


# this definition exists because focused behavior needs one stable owner
def FlattenedMates(
    Native: NativeAssembly, Mates: tuple[MateConstraint, ...]
) -> tuple[dict[str, AnyValue], ...]:
    Identity = {
        ItemValue.object_id: ItemValue.object_id for ItemValue in Native.occurrences
    }
    OwnerPaths: Defaultdict[int, list[tuple[str, tuple[str, ...]]]] = Defaultdict(list)
    OwnerPaths[Native.root_definition_id].append(("", ()))
    for ItemValue in Native.occurrence_paths:
        PathValue = tuple(
            (
                AsmInstanceId(Value)
                for Value in MateInstance(Native, Identity, ItemValue.path)
            )
        )
        OwnerPaths[ItemValue.definition_id].append((ItemValue.path, PathValue))
    Result: list[dict[str, AnyValue]] = []
    for MateValue in Mates:
        OwnerId = int(MateValue.owner_definition_id.rsplit(":", 1)[-1])
        for Index, (PathValue, InstancePath) in enumerate(OwnerPaths.get(OwnerId, [])):
            Result.append(
                {
                    "id": f"{MateValue.id}:occurrence:{Index}",
                    "mate_id": MateValue.id,
                    "owner_definition_id": MateValue.owner_definition_id,
                    "owner_occurrence_path": PathValue,
                    "owner_instance_path": InstancePath,
                }
            )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def Companion(Label: str) -> tuple[BrepPayload, ...]:
    Source = PathValue(Label)
    if not Source.is_file():
        return ()
    Source = Source.resolve()
    Specifications = (
        ("ACIS", ".sat", "acis.sat"),
        ("Parasolid", ".x_t", "parasolid.x_t"),
    )
    Result: list[BrepPayload] = []
    for FolderName, Suffix, FormatId in Specifications:
        Folder = Source.parent / FolderName
        if not Folder.is_dir():
            continue
        Choice = next(
            (
                PathValue
                for PathValue in Folder.iterdir()
                if PathValue.is_file()
                and PathValue.stem.casefold() == Source.stem.casefold()
                and (PathValue.suffix.casefold() == Suffix)
            ),
            None,
        )
        if Choice is None:
            continue
        DataValue = Choice.read_bytes()
        Attributes: dict[str, AnyValue] = {
            "companion_path": str(Choice.resolve()),
            "source_assembly": str(Source),
        }
        if FormatId == "acis.sat":
            Header = DataValue.splitlines()[0].decode("ascii", errors="replace").split()
            if len(Header) >= 3 and Header[2].isdigit():
                Attributes["body_count"] = int(Header[2])
        Result.append(
            BrepPayload(
                id=f"sldasm:resolved:{FormatId}",
                format_id=FormatId,
                kind="resolved-assembly",
                schema=FormatId,
                sha256=Hashlib.sha256(DataValue).hexdigest(),
                data=DataValue,
                source_stream=str(Choice.resolve()),
                provenance=Provenance(
                    adapter=KAsmFormatId,
                    native_id=Choice.name,
                    spans=(
                        ProvenanceSpan(
                            str(Choice.resolve()),
                            0,
                            len(DataValue),
                            "resolved-assembly-brep",
                        ),
                    ),
                ),
                attributes=FrozenMapping(Attributes),
                role=PayloadRole.BREP,
                file_extension=Suffix,
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def AsmMatrix(Values: tuple[float, ...]) -> MatrixFour:
    return MatrixFour(
        (
            Values[0],
            Values[4],
            Values[8],
            Values[12] * 1000.0,
            Values[1],
            Values[5],
            Values[9],
            Values[13] * 1000.0,
            Values[2],
            Values[6],
            Values[10],
            Values[14] * 1000.0,
            Values[3],
            Values[7],
            Values[11],
            Values[15],
        )
    )


# this definition exists because focused behavior needs one stable owner
def AsmBoundingBox(
    Values: tuple[float, float, float, float, float, float] | None,
) -> BoundingBox | None:
    if Values is None:
        return None
    return BoundingBox(
        VectorThree(*(Value * 1000.0 for Value in Values[:3])),
        VectorThree(*(Value * 1000.0 for Value in Values[3:])),
    )


# this definition exists because focused behavior needs one stable owner
def AsmDefinitionId(NativeId: int) -> str:
    return f"sldasm:definition:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def AsmInstanceId(NativeId: int) -> str:
    return f"sldasm:instance:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def ValidateSource(Label: str, IsAsm: bool) -> None:
    Suffix = PathValue(Label).suffix.casefold()
    ExpectedFormat = KAsmFormatId if IsAsm else KFormatId
    Expected = SuffixByFormatId[ExpectedFormat]
    if Suffix in FormatIdBySuffix and Suffix != Expected:
        KindValue = "assembly" if IsAsm else "part"
        raise SldprtFormatError(
            f"SOLIDWORKS {KindValue} content requires a {Expected.upper()} source"
        )


# stream restoration remains best effort for nonseekable and closed inputs
def RestoreStream(SourceData: Source, Position: int | None) -> None:
    SeekValue = getattr(SourceData, "seek", None)
    if Position is None or not callable(SeekValue):
        return
    try:
        SeekValue(Position)
    except (OSError, ValueError):
        return


# this definition exists because focused behavior needs one stable owner
def SourceBytes(Source: Source) -> tuple[bytes, str]:
    if isinstance(Source, (str, FilePath)):
        LocalPath = FilePath(Source).expanduser().resolve()
        return (LocalPath.read_bytes(), str(LocalPath))
    if isinstance(Source, (bytes, bytearray)):
        return (bytes(Source), "<memory>")
    Position = None
    TellValue = getattr(Source, "tell", None)
    if callable(TellValue):
        try:
            Position = TellValue()
        except (OSError, ValueError):
            Position = None
    Value = Source.read()
    RestoreStream(Source, Position)
    if not isinstance(Value, (bytes, bytearray)):
        raise TypeError("SLDPRT source stream must yield bytes")
    NameValue = getattr(Source, "name", "<stream>")
    return (bytes(Value), str(NameValue))


# this definition exists because focused behavior needs one stable owner
def ResolvedStream(Streams: Mapping[str, bytes], LaneValue: str) -> str:
    return KitResolvedStream if KitResolvedStream in Streams else LaneValue


# this definition exists because focused behavior needs one stable owner
def NativePartModel(Archive: SldprtArchive, Requested: str | None) -> NativeModel:
    Keywords = Archive.require(KeywordsStream)
    Lanes = {
        int(Match.group(1)): NameValue
        for NameValue in Archive.streams
        if (Match := KResolvedConfigStream.fullmatch(NameValue)) is not None
    }
    if not Lanes:
        raise SldprtFormatError("required native resolved-feature stream is missing")
    InitialId = 0 if 0 in Lanes else min(Lanes)
    InitialStream = ResolvedStream(Archive.streams, Lanes[InitialId])
    Initial = DecodeNativeModel(
        Keywords,
        Archive.require(InitialStream),
        configuration_id=InitialId,
        resolved_stream=InitialStream,
    )
    SelectedId = InitialId
    if Requested is not None:
        Selected = next(
            (
                ItemValue.configuration_id
                for ItemValue in Initial.configurations
                if ItemValue.name == Requested
            ),
            None,
        )
        if Selected is None:
            raise SldprtFormatError(
                f"configuration {Requested!r} is unavailable; choices are {sorted((ItemValue.name for ItemValue in Initial.configurations))}"
            )
        SelectedId = Selected
    if SelectedId not in Lanes:
        raise SldprtFormatError(
            f"native data for configuration {SelectedId} is unavailable; available lanes are {sorted(Lanes)}"
        )
    SelectedStream = ResolvedStream(Archive.streams, Lanes[SelectedId])
    ConfigStream = f"Contents/Config-{SelectedId}"
    return DecodeNativeModel(
        Keywords,
        Archive.require(SelectedStream),
        Archive.get(ConfigStream) or b"",
        configuration_id=SelectedId,
        resolved_stream=SelectedStream,
        configuration_stream=ConfigStream,
    )


# this definition exists because focused behavior needs one stable owner
def Configurations(Model: NativeModel, Requested: str | None) -> tuple[Config, ...]:
    Available = {ItemValue.name for ItemValue in Model.configurations}
    if Requested is not None and Requested not in Available:
        raise SldprtFormatError(
            f"configuration {Requested!r} is unavailable; choices are {sorted(Available)}"
        )
    Active = Requested or next(
        (
            ItemValue.name
            for ItemValue in Model.configurations
            if ItemValue.configuration_id == Model.active_configuration_id
        ),
        Model.configurations[0].name,
    )
    return tuple(
        (
            Config(
                id=ConfigId(ItemValue.configuration_id),
                name=ItemValue.name,
                active=ItemValue.name == Active,
                attributes=FrozenMapping(
                    {
                        "native_object_id": ItemValue.object_id,
                        "native_configuration_id": ItemValue.configuration_id,
                        "native_properties": ItemValue.properties,
                    }
                ),
            )
            for ItemValue in Model.configurations
        )
    )


# this definition exists because focused behavior needs one stable owner
def Parameters(Model: NativeModel) -> tuple[Param, ...]:
    Parameters: list[Param] = []
    DimensionIds: dict[tuple[str, str], str] = {}
    for Feature in Model.features:
        for Dimension, ParamId in ParamEntries(Feature.object_id, Feature.dimensions):
            NativeValue = (
                Dimension.native_value
                if Dimension.native_value is not None
                else Dimension.value_mm / 1000.0
            )
            Parameters.append(
                Param(
                    id=ParamId,
                    name=Dimension.name,
                    value=DimensionParam(Dimension),
                    role=(
                        ParamRole.DRIVEN
                        if Dimension.native_role == "display"
                        else ParamRole.DRIVING
                    ),
                    owner_id=FeatureId(Feature.object_id),
                    provenance=(
                        ProvenanceA(
                            f"{Feature.object_id}:{Dimension.name}",
                            Dimension.native_offset,
                            8,
                            "dimension-scalar",
                            Stream=Feature.native_stream,
                        )
                        if Dimension.native_offset is not None
                        else FeatureA(Feature)
                    ),
                    attributes=FrozenMapping(
                        {
                            "source_text": Dimension.source_text,
                            "dimension_kind": Dimension.kind,
                            "native_value": NativeValue,
                            "native_unit": "rad" if Dimension.kind == "angle" else "m",
                            "native_role": Dimension.native_role or "unresolved",
                            "native_operands": tuple(
                                (
                                    {
                                        "offset": Operand.offset,
                                        "kind_code": Operand.kind_code,
                                        "entity_index": Operand.entity_index,
                                    }
                                    for Operand in Dimension.operands
                                )
                            ),
                        }
                    ),
                )
            )
            DimensionIds.setdefault((Feature.name, Dimension.name), ParamId)
    return ApplyNativeMut(Parameters, Model, DimensionIds)


# this definition exists because focused behavior needs one stable owner
def DimensionParam(Dimension: NativeDimension) -> ParamValue:
    if Dimension.kind == "angle":
        return ParamValue(Dimension.value_mm, ValueKind.ANGLE, "deg")
    return ParamValue(Dimension.value_mm, ValueKind.LENGTH, "mm")


# this definition exists because focused behavior needs one stable owner
def ApplyNativeMut(
    Parameters: list[Parameter],
    Model: NativeModel,
    DimensionIds: dict[tuple[str, str], str],
) -> tuple[Param, ...]:
    if not Model.equations:
        return tuple(Parameters)
    GlobalIds = {
        Equation.lhs: f"sldprt:parameter:equation:{Equation.lhs}"
        for Equation in Model.equations
        if "@" not in Equation.lhs
    }
    Values: dict[str, ParamValue] = {}
    ParamIndexes = {Param.id: Index for Index, Param in enumerate(Parameters)}
    for Equation in Model.equations:
        RefIds = tuple(
            (
                GlobalIds[RefValue]
                for RefValue in Equation.references
                if RefValue in GlobalIds
            )
        )
        ExprValue = Expression(Equation.rhs, RefIds, "solidworks")
        ProvenanceValue = Provenance(
            adapter=KFormatId,
            native_id=f"equation:{Equation.native_offset}",
            spans=(
                ProvenanceSpan(
                    Equation.native_stream,
                    Equation.native_offset,
                    Equation.native_length,
                    "equation",
                ),
            ),
        )
        if "@" in Equation.lhs:
            DimensionName, FeatureName = Equation.lhs.split("@", 1)
            ParamId = DimensionIds.get((FeatureName, DimensionName))
            if ParamId is None or ParamId not in ParamIndexes:
                continue
            Index = ParamIndexes[ParamId]
            Parameters[Index] = Replace(
                Parameters[Index],
                role=ParamRole.DERIVED,
                expression=ExprValue,
                provenance=ProvenanceValue,
                attributes=FrozenMapping(
                    {
                        **dict(Parameters[Index].attributes),
                        "equation_source": Equation.source,
                        "equation_configuration_id": Equation.configuration_id,
                    }
                ),
            )
            continue
        Value = NativeEquation(Equation.rhs, Values)
        if Value is None:
            Value = ParamValue(Equation.rhs, ValueKind.STRING)
        Values[Equation.lhs] = Value
        ParamItem = Param(
            id=GlobalIds[Equation.lhs],
            name=Equation.lhs,
            value=Value,
            role=ParamRole.DERIVED if Equation.references else ParamRole.DRIVING,
            expression=ExprValue,
            owner_id=FeatureId(16),
            provenance=ProvenanceValue,
            attributes=FrozenMapping(
                {
                    "equation_source": Equation.source,
                    "equation_configuration_id": Equation.configuration_id,
                }
            ),
        )
        if ParamItem.id in ParamIndexes:
            Parameters[ParamIndexes[ParamItem.id]] = ParamItem
        else:
            ParamIndexes[ParamItem.id] = len(Parameters)
            Parameters.append(ParamItem)
    return tuple(Parameters)


# this definition exists because focused behavior needs one stable owner
def NativeEquation(
    RhsValue: str, Values: Mapping[str, ParameterValue]
) -> ParamValue | None:
    Literal = RegexLib.fullmatch(
        "\\s*([-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+))\\s*mm\\s*",
        RhsValue,
        RegexLib.IGNORECASE,
    )
    if Literal is not None:
        return ParamValue(float(Literal.group(1)), ValueKind.LENGTH, "mm")
    Number = RegexLib.fullmatch("\\s*([-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+))\\s*", RhsValue)
    if Number is not None:
        return ParamValue(float(Number.group(1)), ValueKind.NUMBER, "")
    Quotient = RegexLib.fullmatch(
        '\\s*"([^"\\r\\n]+)"\\s*/\\s*([-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+))\\s*', RhsValue
    )
    if Quotient is None:
        return None
    Source = Values.get(Quotient.group(1))
    if (
        Source is None
        or Source.kind not in {ValueKind.LENGTH, ValueKind.NUMBER}
        or (not isinstance(Source.value, (int, float)))
    ):
        return None
    Divisor = float(Quotient.group(2))
    if not MathValue.isfinite(Divisor) or Divisor == 0.0:
        return None
    return ParamValue(float(Source.value) / Divisor, Source.kind, Source.unit)


# this definition exists because focused behavior needs one stable owner
def Planes(Model: NativeModel, ParamIds: set[str]) -> tuple[SupportPlane, ...]:
    Result: list[SupportPlane] = []

    # this callback exists because local behavior needs one focused transformation
    for Plane in sorted(
        Model.planes,
        key=lambda ItemValue: (
            next(
                (
                    Feature.native_offset
                    for Feature in Model.features
                    if Feature.object_id == ItemValue.object_id
                ),
                None,
            )
            is None,
            next(
                (
                    Feature.native_offset
                    for Feature in Model.features
                    if Feature.object_id == ItemValue.object_id
                ),
                1 << 62,
            ),
        ),
    ):
        OffsetId = ParamId(Plane.object_id, "D1")
        Result.append(
            SupportPlane(
                id=PlaneId(Plane.object_id),
                name=Plane.name,
                transform=Transform(
                    origin=VectorThree(*Plane.origin_mm),
                    x_axis=VectorThree(*Plane.u_axis),
                    y_axis=VectorThree(*Plane.v_axis),
                    z_axis=VectorThree(*Plane.normal),
                ),
                offset_parameter_id=OffsetId if OffsetId in ParamIds else None,
                provenance=(
                    ProvenanceA(
                        str(Plane.object_id),
                        Plane.native_offset,
                        Plane.native_length or 1,
                        "support-plane-frame",
                        Stream=Plane.native_stream,
                    )
                    if Plane.native_offset is not None
                    else ProvenanceA(
                        str(Plane.object_id), None, None, "principal-plane"
                    )
                ),
                attributes=FrozenMapping(
                    {
                        "native_object_id": Plane.object_id,
                        "native_frame_offset": Plane.native_offset,
                        "native_frame_length": Plane.native_length,
                        "principal": Plane.principal,
                        "native_reference_ids": Plane.reference_ids,
                    }
                ),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def Sketches(Model: NativeModel, ParamIds: set[str]) -> tuple[SketchData, ...]:

    # this callback exists because local behavior needs one focused transformation
    return tuple(
        (
            SketchA(Sketch, ParamIds)
            for Sketch in sorted(
                Model.sketches, key=lambda ItemValue: ItemValue.native_offset
            )
        )
    )


# this definition exists because profile primitives share one entity mapping pass
def ProfileSketch(Sketch: NativeSketch) -> tuple[AnyValue, ...]:
    Entities: list[SketchEntity] = []
    RefMap: dict[str, str] = {}
    ProfileEntities: dict[int, str] = {}
    ProfileOffsets = {
        Offset for Profile in Sketch.profiles for Offset in Profile.marker_offsets
    }
    for ProfileIndex, Profile in enumerate(Sketch.profiles):
        if Profile.kind == "rectangle":
            XZero, YZero, XOneValue, YOneValue = Profile.coordinates
            Endpoints = (
                ((XZero, YZero), (XOneValue, YZero)),
                ((XOneValue, YZero), (XOneValue, YOneValue)),
                ((XOneValue, YOneValue), (XZero, YOneValue)),
                ((XZero, YOneValue), (XZero, YZero)),
            )
            for EdgeIndex, (Start, EndValue) in enumerate(Endpoints):
                EntityId = ProfileEdgeId(Sketch.object_id, ProfileIndex, EdgeIndex)
                MarkerOffset = (
                    Profile.marker_offsets[EdgeIndex]
                    if EdgeIndex < len(Profile.marker_offsets)
                    else None
                )
                Entities.append(
                    SketchEntity(
                        id=EntityId,
                        kind=GeomKind.LINE,
                        geometry=LineGeom(VectorTwo(*Start), VectorTwo(*EndValue)),
                        provenance=(
                            ProvenanceA(
                                f"{Sketch.object_id}:{MarkerOffset}",
                                MarkerOffset,
                                92,
                                "sketch-profile-line",
                                Stream=Sketch.native_stream,
                            )
                            if MarkerOffset is not None
                            else FeatureSpan(Sketch)
                        ),
                        attributes=FrozenMapping(
                            {"profile_index": ProfileIndex, "edge_index": EdgeIndex}
                        ),
                    )
                )
                RefMap[
                    f"{Sketch.object_id}:profile:{ProfileIndex}:edge:{EdgeIndex}"
                ] = EntityId
                if MarkerOffset is not None:
                    ProfileEntities[MarkerOffset] = EntityId
        elif Profile.kind == "circle":
            FirstCoord, SecondCoord, Radius = Profile.coordinates
            EntityId = ProfileId(Sketch.object_id, ProfileIndex)
            Entities.append(
                SketchEntity(
                    id=EntityId,
                    kind=GeomKind.CIRCLE,
                    geometry=CircleGeom(VectorTwo(FirstCoord, SecondCoord), Radius),
                    provenance=Provenance(
                        adapter=KFormatId,
                        native_id=f"{Sketch.object_id}:profile:{ProfileIndex}",
                        spans=tuple(
                            (
                                ProvenanceSpan(
                                    Sketch.native_stream,
                                    Offset,
                                    142,
                                    "sketch-circle-marker",
                                )
                                for Offset in Profile.marker_offsets
                            )
                        ),
                    ),
                    attributes=FrozenMapping({"profile_index": ProfileIndex}),
                )
            )
            RefMap[f"{Sketch.object_id}:profile:{ProfileIndex}"] = EntityId
            ProfileEntities.update(
                {Offset: EntityId for Offset in Profile.marker_offsets}
            )
    return (Entities, RefMap, ProfileEntities, ProfileOffsets)


# this definition exists because native markers share coordinate reference context
def SketchMarkers(
    Sketch: NativeSketch,
    ProfileOffsets: set[int],
    ProfileEntities: Mapping[int, str],
) -> tuple[list[SketchEntity], dict[int, str]]:
    Entities: list[SketchEntity] = []
    CoordinatesByPrefix = {
        Prefix: tuple(
            (
                Marker.coordinates_mm
                for Marker in Sketch.markers
                if Marker.prefix == Prefix
            )
        )
        for Prefix in {Marker.prefix for Marker in Sketch.markers}
    }
    CoordinatesByIndex = tuple((Marker.coordinates_mm for Marker in Sketch.markers))
    MarkerSemantics = tuple((MarkerCurve(Marker) for Marker in Sketch.markers))
    CurveRefIndices = {
        RefValue
        for Marker, Semantic in zip(Sketch.markers, MarkerSemantics, strict=True)
        for RefValue in MarkerCurveRef(Marker, Semantic)
    } | {
        RefValue
        for Marker in Sketch.markers
        for RefValue in MarkerObjectRef(Marker.data)
    }
    MarkerEntities: dict[int, str] = {}
    for MarkerIndex, (Marker, Semantic) in enumerate(
        zip(Sketch.markers, MarkerSemantics, strict=True)
    ):
        if Marker.offset in ProfileOffsets:
            EntityId = ProfileEntities.get(Marker.offset)
            if EntityId is not None:
                MarkerEntities[MarkerIndex] = EntityId
            continue
        if (
            MarkerIndex in CurveRefIndices
            and Marker.coordinates_mm is not None
            and (Marker.locus == "05000100")
        ):
            continue
        if (
            Marker.coordinates_mm is not None
            and Marker.object_index is None
            and (Marker.locus == "05000100")
        ):
            continue
        if Marker.endpoint_indices is None and b"sgSlot_c" in Marker.data:
            continue
        Entity = MarkerEntity(
            Sketch, Marker, CoordinatesByPrefix, CoordinatesByIndex, Semantic
        )
        Entities.append(Entity)
        MarkerEntities[MarkerIndex] = Entity.id
    return (Entities, MarkerEntities)


# this definition exists because dimension operands extend marker reference lookup
def MarkerRefsMut(
    Sketch: NativeSketch,
    MarkerEntities: Mapping[int, str],
    RefMapMut: dict[str, str],
) -> None:
    for Dimension in Sketch.dimensions:
        if Dimension.kind != "length":
            continue
        for Operand in Dimension.operands:
            EntityId = MarkerEntities.get(Operand.entity_index)
            if EntityId is not None:
                RefMapMut[f"native:{Operand.kind_code:04x}:{Operand.entity_index}"] = (
                    EntityId
                )


# this definition exists because profile loops need canonical closed entity groups
def ClosedSketch(Sketch: NativeSketch) -> tuple[tuple[str, ...], ...]:
    ClosedProfiles: list[tuple[str, ...]] = []
    for ProfileIndex, Profile in enumerate(Sketch.profiles):
        if Profile.kind == "rectangle":
            ClosedProfiles.append(
                tuple(
                    (
                        ProfileEdgeId(Sketch.object_id, ProfileIndex, EdgeIndex)
                        for EdgeIndex in range(4)
                    )
                )
            )
        elif Profile.kind == "circle":
            ClosedProfiles.append((ProfileId(Sketch.object_id, ProfileIndex),))
    return tuple(ClosedProfiles)


# this definition exists because focused behavior needs one stable owner
def SketchA(Sketch: NativeSketch, ParamIds: set[str]) -> SketchData:
    Entities, RefMap, ProfileEntities, ProfileOffsets = ProfileSketch(Sketch)
    MarkerValues, MarkerEntities = SketchMarkers(
        Sketch, ProfileOffsets, ProfileEntities
    )
    Entities.extend(MarkerValues)
    RefMap.update(
        {
            f"native-index:{Index}": EntityId
            for Index, EntityId in MarkerEntities.items()
        }
    )
    MarkerRefsMut(Sketch, MarkerEntities, RefMap)
    Constraints = SketchB(Sketch, RefMap, ParamIds)
    ClosedProfiles = ClosedSketch(Sketch)
    SketchParamIds = tuple(
        (
            ParamId
            for Dimension, ParamId in ParamEntries(Sketch.object_id, Sketch.dimensions)
            if ParamId in ParamIds
        )
    )
    return SketchData(
        id=SketchId(Sketch.object_id),
        name=Sketch.name,
        support_plane_id=PlaneId(Sketch.support_plane_id),
        entities=tuple(Entities),
        constraints=Constraints,
        parameter_ids=SketchParamIds,
        closed_profile_entity_ids=ClosedProfiles,
        provenance=FeatureSpan(Sketch),
        attributes=FrozenMapping(
            {
                "native_object_id": Sketch.object_id,
                "native_marker_count": len(Sketch.markers),
                "native_profile_count": len(Sketch.profiles),
                "support_plane_native_id": Sketch.support_plane_id,
                "support_plane_source": Sketch.support_source,
                "unframed_support_plane_native_id": Sketch.unframed_support_plane_id,
            }
        ),
    )


# this definition exists because point and line markers share coordinate resolution
def MarkerLinear(
    Marker: NativeMarker,
    CoordinatesByPrefix: dict[str, tuple[tuple[float, float] | None, ...]],
    CoordinatesByIndex: tuple[tuple[float, float] | None, ...],
    ResolvedSemantic: str,
) -> tuple[AnyValue, AnyValue] | None:
    if ResolvedSemantic == "point" and Marker.coordinates_mm is not None:
        return (GeomKind.POINT, PointGeom(VectorTwo(*Marker.coordinates_mm)))
    if ResolvedSemantic != "line" or Marker.endpoint_indices is None:
        return None
    Coordinates = (
        CoordinatesByIndex
        if ResolvedSemantic != Marker.semantic
        or (Marker.profile_role == 2 and Marker.native_kind == 2)
        else CoordinatesByPrefix[Marker.prefix]
    )
    Start = CoordinateRef(Coordinates, Marker.endpoint_indices[0])
    EndValue = CoordinateRef(Coordinates, Marker.endpoint_indices[1])
    if Start is not None and EndValue is not None and (Start != EndValue):
        return (GeomKind.LINE, LineGeom(VectorTwo(*Start), VectorTwo(*EndValue)))
    return (GeomKind.NATIVE, NativeMarkerA(Marker))


# this definition exists because curved markers share native fallback semantics
def MarkerCurved(
    Marker: NativeMarker,
    CoordinatesByIndex: tuple[tuple[float, float] | None, ...],
    ResolvedSemantic: str,
) -> tuple[AnyValue, AnyValue]:
    KindValue: AnyValue = GeomKind.NATIVE
    GeomValue: AnyValue = None
    if ResolvedSemantic in {"circle", "arc"}:
        Circular = MarkerCircular(Marker, CoordinatesByIndex, ResolvedSemantic)
        if Circular is not None:
            return Circular
    elif ResolvedSemantic == "ellipse":
        KindValue = GeomKind.ELLIPSE
        GeomValue = MarkerEllipse(Marker, CoordinatesByIndex)
    elif ResolvedSemantic == "arc_ellipse":
        KindValue = GeomKind.ARC_ELLIPSE
        GeomValue = MarkerArcGeom(Marker, CoordinatesByIndex)
    elif ResolvedSemantic == "parabola":
        KindValue = GeomKind.ARC_PARABOLA
        GeomValue = MarkerParabola(Marker, CoordinatesByIndex)
    elif ResolvedSemantic == "spline":
        KindValue = GeomKind.SPLINE
        GeomValue = MarkerSpline(Marker, CoordinatesByIndex)
    if GeomValue is None:
        return (GeomKind.NATIVE, NativeMarkerA(Marker, ResolvedSemantic))
    return (KindValue, GeomValue)


# this definition exists because marker geometry needs ordered semantic dispatch
def MarkerGeometry(
    Marker: NativeMarker,
    CoordinatesByPrefix: dict[str, tuple[tuple[float, float] | None, ...]],
    CoordinatesByIndex: tuple[tuple[float, float] | None, ...],
    ResolvedSemantic: str,
) -> tuple[AnyValue, AnyValue]:
    Linear = MarkerLinear(
        Marker, CoordinatesByPrefix, CoordinatesByIndex, ResolvedSemantic
    )
    if Linear is not None:
        return Linear
    return MarkerCurved(Marker, CoordinatesByIndex, ResolvedSemantic)


# this definition exists because focused behavior needs one stable owner
def MarkerEntity(
    Sketch: NativeSketch,
    Marker: NativeMarker,
    CoordinatesByPrefix: dict[str, tuple[tuple[float, float] | None, ...]],
    CoordinatesByIndex: tuple[tuple[float, float] | None, ...],
    Semantic: str | None = None,
) -> SketchEntity:
    EntityId = MarkerId(Sketch.object_id, Marker.offset)
    ResolvedSemantic = Semantic or Marker.semantic
    KindValue, GeomValue = MarkerGeometry(
        Marker, CoordinatesByPrefix, CoordinatesByIndex, ResolvedSemantic
    )
    return SketchEntity(
        id=EntityId,
        kind=KindValue,
        geometry=GeomValue,
        construction=Marker.construction,
        provenance=ProvenanceA(
            f"{Sketch.object_id}:{Marker.offset}",
            Marker.offset,
            Marker.length,
            "sketch-native-marker",
            Stream=Sketch.native_stream,
        ),
        attributes=FrozenMapping(
            {
                "native_kind": Marker.native_kind,
                "native_locus": Marker.locus,
                "profile_role": Marker.profile_role,
                "state": Marker.state,
                "object_index": Marker.object_index,
                "local_id": Marker.local_id,
                "endpoint_indices": Marker.endpoint_indices,
                "semantic": ResolvedSemantic,
                "marker_prefix": Marker.prefix,
            }
        ),
    )


# this definition exists because focused behavior needs one stable owner
def MarkerCurve(Marker: NativeMarker) -> str:
    Endpoints = Marker.endpoint_indices
    if Endpoints is None:
        return Marker.semantic
    if Marker.semantic == "line" and b"cptsSplineList_c" not in Marker.data[:192]:
        return "line"
    if len(Marker.data) >= 102 and Marker.data[86:102] == b"\xfe\xff\xff\xff" * 4:
        return "circle" if Endpoints[0] == Endpoints[1] else "arc"
    if (
        Marker.length == 92 or (Marker.length == 104 and Endpoints[0] != Endpoints[1])
    ) and (Marker.locus == "05000100" or Marker.profile_role == 1):
        return "line"
    if Marker.length in {112, 116}:
        return "circle" if Endpoints[0] == Endpoints[1] else "arc"
    if Marker.length == 104:
        return "ellipse"
    if Marker.length == 108:
        return "arc_ellipse"
    if Marker.length == 124:
        return "parabola"
    if Marker.length == 128:
        return "conic"
    if Marker.length > 128:
        return "spline"
    return Marker.semantic


# this definition exists because focused behavior needs one stable owner
def MarkerCurveRef(Marker: NativeMarker, Semantic: str) -> tuple[int, ...]:
    Result = list(Marker.endpoint_indices or ())
    if Semantic in {"circle", "arc"} and len(Marker.data) >= 86:
        Result.append(Struct.unpack_from("<H", Marker.data, 84)[0])
    elif Semantic in {"ellipse", "arc_ellipse"} and len(Marker.data) >= 94:
        Result.extend(Struct.unpack_from("<5H", Marker.data, 84))
    elif Semantic == "parabola" and len(Marker.data) >= 88:
        Result.extend(Struct.unpack_from("<2I", Marker.data, 80))
    elif Semantic == "conic" and len(Marker.data) >= 96:
        Result.extend(Struct.unpack_from("<2I", Marker.data, 88))
    elif Semantic == "spline":
        Result.extend(MarkerSplineRef(Marker.data))
    return tuple(dict.fromkeys(Result))


# this definition exists because focused behavior needs one stable owner
def MarkerSplineRef(DataValue: bytes) -> tuple[int, ...]:
    Result: list[int] = []
    for Offset in range(max(0, len(DataValue) - 11)):
        if DataValue[Offset : Offset + 2] != b"\xa7\x80":
            continue
        if DataValue[Offset + 4 : Offset + 12] != b"\xff\xff\xff\xff\x00\x00\x00\x00":
            continue
        Result.append(Struct.unpack_from("<H", DataValue, Offset + 2)[0])
    return tuple(dict.fromkeys(Result))


# this definition exists because focused behavior needs one stable owner
def MarkerObjectRef(DataValue: bytes) -> tuple[int, ...]:
    Result: list[int] = []
    for Offset in range(max(0, len(DataValue) - 11)):
        if (
            DataValue[Offset] not in {167, 178, 183, 199}
            or DataValue[Offset + 1] != 128
        ):
            continue
        if DataValue[Offset + 4 : Offset + 12] != b"\xff\xff\xff\xff\x00\x00\x00\x00":
            continue
        Result.append(Struct.unpack_from("<H", DataValue, Offset + 2)[0])
    return tuple(dict.fromkeys(Result))


# this definition exists because focused behavior needs one stable owner
def MarkerCircular(
    Marker: NativeMarker,
    Coordinates: tuple[tuple[float, float] | None, ...],
    Semantic: str,
) -> tuple[GeomKind, CircleGeom | ArcGeom] | None:
    if Marker.endpoint_indices is None or len(Marker.data) < 86:
        return None
    Center = CoordinateRef(Coordinates, Struct.unpack_from("<H", Marker.data, 84)[0])
    Start = CoordinateRef(Coordinates, Marker.endpoint_indices[0])
    EndValue = CoordinateRef(Coordinates, Marker.endpoint_indices[1])
    if Center is None or Start is None:
        return None
    Radius = MathValue.dist(Center, Start)
    if not MathValue.isfinite(Radius) or Radius <= 1e-12:
        return None
    if Semantic == "circle":
        return (GeomKind.CIRCLE, CircleGeom(VectorTwo(*Center), Radius))
    if EndValue is None:
        return None
    StartAngle = MathValue.atan2(Start[1] - Center[1], Start[0] - Center[0])
    EndAngle = MathValue.atan2(EndValue[1] - Center[1], EndValue[0] - Center[0])
    if Struct.unpack_from("<I", Marker.data, 80)[0] == 4294967295:
        StartAngle, EndAngle = (EndAngle, StartAngle)
    return (GeomKind.ARC, ArcGeom(VectorTwo(*Center), Radius, StartAngle, EndAngle))


# this definition exists because focused behavior needs one stable owner
def MarkerEllipse(
    Marker: NativeMarker, Coordinates: tuple[tuple[float, float] | None, ...]
) -> EllipseGeom | None:
    if len(Marker.data) < 90:
        return None
    CenterIndex, MajorIndex, MinorIndex = Struct.unpack_from("<3H", Marker.data, 84)
    Center = CoordinateRef(Coordinates, CenterIndex)
    Major = CoordinateRef(Coordinates, MajorIndex)
    Minor = CoordinateRef(Coordinates, MinorIndex)
    if Center is None or Major is None or Minor is None:
        return None
    MajorRadius = MathValue.dist(Center, Major)
    MinorRadius = MathValue.dist(Center, Minor)
    if MajorRadius <= 1e-12 or MinorRadius <= 1e-12:
        return None
    return EllipseGeom(
        VectorTwo(*Center),
        VectorTwo(
            (Major[0] - Center[0]) / MajorRadius, (Major[1] - Center[1]) / MajorRadius
        ),
        MajorRadius,
        MinorRadius,
    )


# this definition exists because focused behavior needs one stable owner
def MarkerArcGeom(
    Marker: NativeMarker, Coordinates: tuple[tuple[float, float] | None, ...]
) -> ArcEllipseGeom | None:
    Ellipse = MarkerEllipse(Marker, Coordinates)
    if Ellipse is None or Marker.endpoint_indices is None:
        return None
    Start = CoordinateRef(Coordinates, Marker.endpoint_indices[0])
    EndValue = CoordinateRef(Coordinates, Marker.endpoint_indices[1])
    if Start is None or EndValue is None:
        return None
    FirstParam = Ellipse.major_axis
    SecondParam = VectorTwo(-FirstParam.y, FirstParam.x)

    # this definition exists because focused behavior needs one stable owner
    def Param(Point: tuple[float, float]) -> float:
        Delta = VectorTwo(Point[0] - Ellipse.center.x, Point[1] - Ellipse.center.y)
        return MathValue.atan2(
            (Delta.x * SecondParam.x + Delta.y * SecondParam.y) / Ellipse.minor_radius,
            (Delta.x * FirstParam.x + Delta.y * FirstParam.y) / Ellipse.major_radius,
        )

    return ArcEllipseGeom(
        Ellipse.center,
        Ellipse.major_axis,
        Ellipse.major_radius,
        Ellipse.minor_radius,
        Param(Start),
        Param(EndValue),
    )


# this definition exists because focused behavior needs one stable owner
def MarkerSpline(
    Marker: NativeMarker, Coordinates: tuple[tuple[float, float] | None, ...]
) -> SplineGeom | None:
    References = MarkerSplineRef(Marker.data)
    Points = tuple(
        (
            Point
            for Index in References
            if (Point := CoordinateRef(Coordinates, Index)) is not None
        )
    )
    if len(Points) < 2:
        return None
    Degree = min(3, len(Points) - 1)
    return SplineGeom(tuple((VectorTwo(*Point) for Point in Points)), Degree)


# this definition exists because focused behavior needs one stable owner
def MarkerParabola(
    Marker: NativeMarker, Coordinates: tuple[tuple[float, float] | None, ...]
) -> ArcParabolaGeom | None:
    if Marker.endpoint_indices is None or len(Marker.data) < 88:
        return None
    FocusIndex, ApexIndex = Struct.unpack_from("<2I", Marker.data, 80)
    Focus = CoordinateRef(Coordinates, FocusIndex)
    ApexValue = CoordinateRef(Coordinates, ApexIndex)
    Start = CoordinateRef(Coordinates, Marker.endpoint_indices[0])
    EndValue = CoordinateRef(Coordinates, Marker.endpoint_indices[1])
    if Focus is None or ApexValue is None or Start is None or (EndValue is None):
        return None
    FocalLength = MathValue.dist(Focus, ApexValue)
    if not MathValue.isfinite(FocalLength) or FocalLength <= 1e-12:
        return None
    AxisValue = VectorTwo(
        (Focus[0] - ApexValue[0]) / FocalLength, (Focus[1] - ApexValue[1]) / FocalLength
    )
    Perpendicular = VectorTwo(-AxisValue.y, AxisValue.x)

    # this definition exists because focused behavior needs one stable owner
    def Param(Point: tuple[float, float]) -> float:
        Delta = VectorTwo(Point[0] - ApexValue[0], Point[1] - ApexValue[1])
        return (Delta.x * Perpendicular.x + Delta.y * Perpendicular.y) / (
            2.0 * FocalLength
        )

    Limits = sorted((Param(Start), Param(EndValue)))
    return ArcParabolaGeom(
        VectorTwo(*ApexValue), AxisValue, FocalLength, Limits[0], Limits[1]
    )


# this definition exists because focused behavior needs one stable owner
def CoordinateRef(
    Coordinates: tuple[tuple[float, float] | None, ...], Index: int
) -> tuple[float, float] | None:
    return Coordinates[Index] if 0 <= Index < len(Coordinates) else None


# this definition exists because focused behavior needs one stable owner
def NativeMarkerA(Marker: NativeMarker, EntityType: str | None = None) -> NativeGeom:
    return NativeGeom(
        format_id=KFormatId,
        entity_type=EntityType or Marker.semantic,
        data=FrozenMapping(
            {
                "native_kind": Marker.native_kind,
                "locus": Marker.locus,
                "coordinates_mm": Marker.coordinates_mm,
                "endpoint_indices": Marker.endpoint_indices,
                "record_data": Marker.data,
            }
        ),
    )


# this state exists because sketch rule resolution shares occurrence counters
@DataClass(slots=True)
class RuleContext:
    Candidates: Mapping[float, list[tuple[str, str]]]
    DimensionsByName: Mapping[str, list[NativeDimension]]
    ParamIdsByName: Mapping[str, list[str]]
    DimensionUsage: Defaultdict[float, int]
    ParamUsage: Defaultdict[str, int]
    RuleIdUsage: Defaultdict[str, int]
    ParamIds: set[str]


# this definition exists because rule resolution needs indexed dimensions and profiles
def RuleContextA(Sketch: NativeSketch, ParamIds: set[str]) -> RuleContext:
    Candidates: Defaultdict[float, list[tuple[str, str]]] = Defaultdict(list)
    for ProfileIndex, Profile in enumerate(Sketch.profiles):
        if Profile.kind != "rectangle":
            continue
        Width = round(Profile.coordinates[2] - Profile.coordinates[0], 9)
        Height = round(Profile.coordinates[3] - Profile.coordinates[1], 9)
        Candidates[Width].append(
            (ProfileEdgeId(Sketch.object_id, ProfileIndex, 0), "distance_x")
        )
        Candidates[Height].append(
            (ProfileEdgeId(Sketch.object_id, ProfileIndex, 1), "distance_y")
        )
    DimensionsByName: Defaultdict[str, list[NativeDimension]] = Defaultdict(list)
    ParamIdsByName: Defaultdict[str, list[str]] = Defaultdict(list)
    for Dimension, ParamId in ParamEntries(Sketch.object_id, Sketch.dimensions):
        DimensionsByName[Dimension.name].append(Dimension)
        ParamIdsByName[Dimension.name].append(ParamId)
    return RuleContext(
        Candidates,
        DimensionsByName,
        ParamIdsByName,
        Defaultdict(int),
        Defaultdict(int),
        Defaultdict(int),
        ParamIds,
    )


# this definition exists because each native rule needs deterministic occurrence binding
def RulePartsMut(
    RuleValue: AnyValue, RefMap: Mapping[str, str], ContextMut: RuleContext
) -> tuple[AnyValue, ...]:
    ResolvedRefs = [RefMap.get(RefValue) for RefValue in RuleValue.references]
    References = (
        [RuleRef(RefValue) for RefValue in ResolvedRefs]
        if ResolvedRefs and all(ResolvedRefs)
        else []
    )
    KindValue = RuleValue.kind
    NativeName = (
        RuleValue.parameter.rsplit(":", 1)[-1]
        if RuleValue.parameter is not None
        else ""
    )
    ItemValue = ContextMut.ParamUsage[NativeName] if NativeName else 0
    Dimensions = ContextMut.DimensionsByName.get(NativeName, [])
    Dimension = Dimensions[min(ItemValue, len(Dimensions) - 1)] if Dimensions else None
    if not References and RuleValue.parameter is not None and Dimension is not None:
        KeyValue = round(Dimension.value_mm, 9)
        Available = ContextMut.Candidates.get(KeyValue, [])
        if Available:
            Index = ContextMut.DimensionUsage[KeyValue] % len(Available)
            EntityId, KindValue = Available[Index]
            ContextMut.DimensionUsage[KeyValue] += 1
            References = [RuleRef(EntityId)]
    ParamId = None
    if RuleValue.parameter is not None:
        AvailableIds = ContextMut.ParamIdsByName.get(NativeName, [])
        if AvailableIds:
            Choice = AvailableIds[min(ItemValue, len(AvailableIds) - 1)]
            ParamId = Choice if Choice in ContextMut.ParamIds else None
        ContextMut.ParamUsage[NativeName] += 1
    ContextMut.RuleIdUsage[RuleValue.id] += 1
    RuleId = f"sldprt:constraint:{RuleValue.id}"
    if ContextMut.RuleIdUsage[RuleValue.id] > 1:
        RuleId += f":{ContextMut.RuleIdUsage[RuleValue.id]}"
    return (References, KindValue, NativeName, ItemValue, Dimension, ParamId, RuleId)


# this definition exists because resolved rule parts need one neutral constructor
def BuildSketchRule(
    Sketch: NativeSketch,
    RuleValue: AnyValue,
    RefMap: Mapping[str, str],
    ContextMut: RuleContext,
) -> SketchRule:
    References, KindValue, NativeName, ItemValue, Dimension, ParamId, RuleId = (
        RulePartsMut(RuleValue, RefMap, ContextMut)
    )
    return SketchRule(
        id=RuleId,
        kind=KindValue,
        references=tuple(References),
        parameter_id=ParamId,
        driving=Dimension.native_role != "display" if Dimension else True,
        provenance=(
            ProvenanceA(
                RuleValue.id,
                RuleValue.native_offset,
                8,
                "sketch-constraint",
                Stream=Sketch.native_stream,
            )
            if RuleValue.native_offset is not None
            else None
        ),
        attributes=FrozenMapping(
            {
                "native_code": RuleValue.native_code,
                "native_references": RuleValue.references,
                "native_value": RuleValue.value,
                "parameter_occurrence": ItemValue + 1 if NativeName else None,
            }
        ),
    )


# this definition exists because rectangle closure needs inferred coincidence rules
def ProfileRules(Sketch: NativeSketch) -> tuple[SketchRule, ...]:
    Result: list[SketchRule] = []
    for ProfileIndex, Profile in enumerate(Sketch.profiles):
        if Profile.kind != "rectangle":
            continue
        for EdgeIndex in range(4):
            Current = ProfileEdgeId(Sketch.object_id, ProfileIndex, EdgeIndex)
            Following = ProfileEdgeId(
                Sketch.object_id, ProfileIndex, (EdgeIndex + 1) % 4
            )
            Result.append(
                SketchRule(
                    id=f"sldprt:constraint:{Sketch.object_id}:profile:{ProfileIndex}:coincident:{EdgeIndex}",
                    kind="coincident",
                    references=(RuleRef(Current, "end"), RuleRef(Following, "start")),
                    attributes=FrozenMapping({"inferred": True}),
                )
            )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def SketchB(
    Sketch: NativeSketch, RefMap: dict[str, str], ParamIds: set[str]
) -> tuple[SketchRule, ...]:
    ContextMut = RuleContextA(Sketch, ParamIds)
    ExplicitRules = tuple(
        (
            BuildSketchRule(Sketch, RuleValue, RefMap, ContextMut)
            for RuleValue in Sketch.constraints
        )
    )
    return (*ExplicitRules, *ProfileRules(Sketch))


# this definition exists because focused behavior needs one stable owner
def Selections(Model: NativeModel) -> tuple[Selection, ...]:
    Result: list[Selection] = []
    for Operation in Model.operations:
        if not Operation.selection_offsets:
            continue
        for Producer, LocalId, Offsets in OperationA(Operation):
            SelectionId = OperationId(Operation, Producer, LocalId)
            KindValue = Operation.selection_kind
            Result.append(
                Selection(
                    id=SelectionId,
                    name=f"{Operation.name} {KindValue} {LocalId}",
                    path=(
                        SelectionPathElem(
                            entity_kind="feature",
                            entity_id=FeatureId(Producer),
                            subelement=f"{KindValue}:{LocalId}",
                        ),
                    ),
                    query=FrozenMapping(
                        {
                            "native_producer_id": Producer,
                            "native_local_id": LocalId,
                            "native_identity": "7dc39425ad49b2547dc39425ad49b254",
                            "topology_role": (
                                "extrusion_terminal_profile_boundary"
                                if Operation.kind == "fillet"
                                else f"native_{KindValue}"
                            ),
                        }
                    ),
                    provenance=Provenance(
                        adapter=KFormatId,
                        native_id=f"{Operation.object_id}:{KindValue}:{LocalId}",
                        spans=tuple(
                            (
                                ProvenanceSpan(
                                    Operation.native_stream,
                                    Offset,
                                    38,
                                    f"{KindValue}-selection",
                                )
                                for Offset in Offsets
                            )
                        ),
                    ),
                )
            )
    return (*Result, *DirectionAxis(Model))


# this definition exists because focused behavior needs one stable owner
def DirectionAxis(Model: NativeModel) -> tuple[Selection, ...]:
    SketchById = {Sketch.object_id: Sketch for Sketch in Model.sketches}
    Result: list[Selection] = []
    for Operation in Model.operations:
        if Operation.profile_id is None:
            continue
        Sketch = SketchById.get(Operation.profile_id)
        SubElem = OperationAxisSubElem(Operation, Sketch)
        if Sketch is None or SubElem is None:
            continue
        Result.append(
            Selection(
                id=f"sldprt:selection:{Operation.object_id}:axis:{Sketch.object_id}:{SubElem}",
                name=f"{Operation.name} direction {SubElem}",
                path=(
                    SelectionPathElem(
                        entity_kind="native", entity_id=Sketch.name, subelement=SubElem
                    ),
                ),
                query=FrozenMapping(
                    {
                        "native_owner_id": Operation.object_id,
                        "native_target_id": Sketch.object_id,
                        "topology_role": DirectionAxisRole,
                    }
                ),
                provenance=Provenance(
                    adapter=KFormatId,
                    native_id=f"{Operation.object_id}:axis:{SubElem}",
                    spans=(
                        ProvenanceSpan(
                            Operation.native_stream,
                            Operation.native_offset,
                            Operation.native_end - Operation.native_offset,
                            "direction-axis",
                        ),
                    ),
                ),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def OperationA(
    Operation: NativeOperation,
) -> tuple[tuple[int, int, tuple[int, ...]], ...]:
    References = Operation.selection_references
    if not References:
        Producer = Operation.dependencies[-1] if Operation.dependencies else 0
        References = tuple(
            ((Producer, LocalId) for LocalId in Operation.selected_local_ids)
        )
    Aligned = len(Operation.selection_offsets) == len(References)
    return tuple(
        (
            (
                Producer,
                LocalId,
                (
                    (Operation.selection_offsets[Index],)
                    if Aligned
                    else Operation.selection_offsets
                ),
            )
            for Index, (Producer, LocalId) in enumerate(References)
        )
    )


# this definition exists because focused behavior needs one stable owner
def OperationId(Operation: NativeOperation, Producer: int, LocalId: int) -> str:
    Duplicate = (
        sum(
            (
                RefLocal == LocalId
                for Ignored, RefLocal in Operation.selection_references
            )
        )
        > 1
    )
    return SelectionId(
        Operation.object_id,
        LocalId,
        Operation.selection_kind,
        Producer if Duplicate else None,
    )


# this definition exists because focused behavior needs one stable owner
def TimelineInputs(
    Feature: NativeFeature,
    Operation: NativeOperation | None,
    Sketch: NativeSketch | None,
    PlaneById: Mapping[int, NativePlane],
    PrincipalIds: set[int],
    PreviousValue: int | None,
) -> list[int]:
    if Operation is not None:
        return list(Operation.dependencies)
    if Sketch is not None:
        return [Sketch.support_plane_id]
    if Feature.object_id not in PlaneById:
        return []
    RefIds = list(PlaneById[Feature.object_id].reference_ids)
    if (
        not RefIds
        and Feature.object_id not in PrincipalIds
        and PreviousValue is not None
    ):
        RefIds.append(PreviousValue)
    return RefIds


# this definition exists because operation kinds need neutral boolean semantics
def TimelineOp(
    Operation: NativeOperation | None, SelectionIds: set[str]
) -> tuple[BoolOperation | str | None, tuple[str, ...]]:
    if Operation is None:
        return (None, ())
    KindMap: dict[str, BoolOperation | None] = {
        "join": BoolOperation.JOIN,
        "cut": BoolOperation.CUT,
        "revolve_join": BoolOperation.JOIN,
        "revolve_cut": BoolOperation.CUT,
        "hole": BoolOperation.CUT,
        "combine_join": BoolOperation.JOIN,
        "surface": BoolOperation.CREATE,
        "fillet": None,
        "chamfer": None,
        "shell": None,
        "dome": None,
        "scale": None,
        "move_body": None,
    }
    OperationValue = KindMap.get(Operation.kind, Operation.kind)
    Selected = tuple(
        (
            SelectionId
            for Producer, LocalId, Ignored in OperationA(Operation)
            for SelectionId in (OperationId(Operation, Producer, LocalId),)
            if SelectionId in SelectionIds
        )
    )
    return (OperationValue, Selected)


# this definition exists because focused behavior needs one stable owner
def Timeline(
    Model: NativeModel, Selections: tuple[Selection, ...]
) -> tuple[FeatureStep, ...]:
    OperationById = {Operation.object_id: Operation for Operation in Model.operations}
    SketchById = {Sketch.object_id: Sketch for Sketch in Model.sketches}
    PlaneById = {Plane.object_id: Plane for Plane in Model.planes}
    FeatureIds = {Feature.object_id for Feature in Model.features}
    OrderById = {
        Feature.object_id: Order for Order, Feature in enumerate(Model.features)
    }
    SelectionIds = {Selection.id for Selection in Selections}
    PrincipalPlaneIds = {Plane.object_id for Plane in Model.planes if Plane.principal}
    PreviousOperation: int | None = None
    Result: list[FeatureStep] = []
    for Order, Feature in enumerate(Model.features):
        Operation = OperationById.get(Feature.object_id)
        Sketch = SketchById.get(Feature.object_id)
        Inputs = TimelineInputs(
            Feature, Operation, Sketch, PlaneById, PrincipalPlaneIds, PreviousOperation
        )
        Dependencies = tuple(
            (
                FeatureId(NativeId)
                for NativeId in dict.fromkeys(Inputs)
                if NativeId in FeatureIds and OrderById[NativeId] < Order
            )
        )
        ParamIds = tuple(
            (
                ParamId
                for Dimension, ParamId in ParamEntries(
                    Feature.object_id, Feature.dimensions
                )
            )
        )
        Attributes: dict[str, AnyValue] = {
            "native_object_id": Feature.object_id,
            "native_type": Feature.kind,
            "xml_tag": Feature.xml_tag,
            "native_properties": Feature.properties,
        }
        OperationValue, Selected = TimelineOp(Operation, SelectionIds)
        if Operation is not None:
            Attributes.update(OperationAttrs(Operation))
            if Operation.kind != "surface":
                PreviousOperation = Operation.object_id
        Result.append(
            FeatureStep(
                id=FeatureId(Feature.object_id),
                name=Feature.name,
                kind=FeatureKindA(Feature),
                order=Order,
                input_feature_ids=Dependencies,
                sketch_id=(
                    SketchId(Operation.profile_id)
                    if Operation is not None and Operation.profile_id in SketchById
                    else SketchId(Feature.object_id) if Sketch is not None else None
                ),
                parameter_ids=ParamIds,
                operation=OperationValue,
                definition=BuildFeature(Feature, Operation, SketchById, PlaneById),
                selection_ids=Selected,
                provenance=FeatureA(Feature),
                attributes=FrozenMapping(Attributes),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def SolidBody(Features: tuple[NativeFeature, ...]) -> NativeFeature | None:
    return next(
        (
            Feature
            for Feature in Features
            if Feature.kind.casefold().strip() in SolidBodyFeatureTypes
        ),
        None,
    )


# this definition exists because focused behavior needs one stable owner
def FinalBodyId(
    Timeline: tuple[FeatureStep, ...], OperationFeatureIds: frozenset[str]
) -> str:
    Choice = next(
        (
            Feature
            for Feature in reversed(Timeline)
            if Feature.id in OperationFeatureIds
            or (
                isinstance(Feature.kind, FeatureKind)
                and Feature.kind != FeatureKind.REFERENCE
                and (Feature.kind != FeatureKind.SURFACE)
                and (Feature.kind != FeatureKind.NATIVE)
            )
        ),
        None,
    )
    if Choice is not None:
        return Choice.id
    return Timeline[-1].id if Timeline else ""


# this definition exists because focused behavior needs one stable owner
def OperationAttrs(Operation: NativeOperation) -> dict[str, AnyValue]:
    Result: dict[str, AnyValue] = {
        "profile_native_id": Operation.profile_id,
        "native_dependencies": Operation.dependencies,
        "family_code": Operation.family_code,
        "operation_code": Operation.operation_code,
        "schema_code": Operation.schema_code,
        "direction_code": Operation.direction_code,
        "termination_code": Operation.termination_code,
        "native_selection_offsets": Operation.selection_offsets,
        "selected_local_ids": Operation.selected_local_ids,
        "native_selection_references": Operation.selection_references,
        "selection_kind": Operation.selection_kind,
        "mode": Operation.mode,
    }
    if Operation.length_mm is not None:
        Result.update(
            {
                "length_mm": Operation.length_mm,
                "direction_multiplier": (
                    -1 if Operation.kind in {"cut", "revolve_cut", "hole"} else 1
                ),
                "end_condition": (
                    "blind"
                    if Operation.termination_code == 0
                    else f"native:{Operation.termination_code}"
                ),
            }
        )
    if Operation.radius_mm is not None:
        Result["radius_mm"] = Operation.radius_mm
    if Operation.angle_degrees is not None:
        Result["angle_degrees"] = Operation.angle_degrees
    if Operation.diameter_mm is not None:
        Result["diameter_mm"] = Operation.diameter_mm
    if Operation.second_length_mm is not None:
        Result["second_length_mm"] = Operation.second_length_mm
    if Operation.axis_marker_offset is not None:
        Result["axis_marker_offset"] = Operation.axis_marker_offset
    if Operation.axis_source_kind is not None:
        Result["axis_source_kind"] = Operation.axis_source_kind
    if Operation.axis_source_id is not None:
        Result["axis_source_id"] = Operation.axis_source_id
    if Operation.axis_source_offset is not None:
        Result["axis_source_offset"] = Operation.axis_source_offset
    if Operation.end_spec_offset is not None:
        Result["end_spec_offset"] = Operation.end_spec_offset
    if Operation.translation_mm is not None:
        Result["translation_mm"] = Operation.translation_mm
    if Operation.scale_factors is not None:
        Result["scale_factors"] = Operation.scale_factors
    return Result


# this definition exists because unknown features need lossless native metadata
def NativeFallback(
    Feature: NativeFeature, Operation: NativeOperation | None
) -> NativeFeatureDefinition:
    return NativeFeatureDefinition(
        format_id=KFormatId,
        type_id=Feature.kind or Feature.xml_tag,
        object_data=FrozenMapping(
            {
                "native_object_id": Feature.object_id,
                "native_class": Feature.class_name,
                "native_stream": Feature.native_stream,
                "xml_tag": Feature.xml_tag,
                "properties": Feature.properties,
                "dimensions": tuple(
                    (
                        {
                            "name": Dimension.name,
                            "value_mm": Dimension.value_mm,
                            "kind": Dimension.kind,
                            "source_text": Dimension.source_text,
                            "native_value": Dimension.native_value,
                            "native_offset": Dimension.native_offset,
                            "native_role": Dimension.native_role,
                            "operands": tuple(
                                (
                                    {
                                        "offset": Operand.offset,
                                        "kind_code": Operand.kind_code,
                                        "entity_index": Operand.entity_index,
                                    }
                                    for Operand in Dimension.operands
                                )
                            ),
                        }
                        for Dimension in Feature.dimensions
                    )
                ),
                "record_data": Feature.data,
                "operation": (
                    OperationAttrs(Operation) if Operation is not None else None
                ),
            }
        ),
    )


# this definition exists because focused behavior needs one stable owner
def BuildRevolve(
    Operation: NativeOperation | None, Sketches: Mapping[int, NativeSketch]
) -> RevolutionFeature | None:
    if (
        Operation is not None
        and Operation.kind in {"revolve_join", "revolve_cut"}
        and (Operation.angle_degrees is not None)
        and (Operation.profile_id in Sketches)
        and (Operation.axis_marker_offset is not None)
    ):
        return RevolutionFeature(
            angle=ParamValue(Operation.angle_degrees, ValueKind.ANGLE, "deg"),
            axis_entity_id=MarkerId(Operation.profile_id, Operation.axis_marker_offset),
            reversed=Operation.kind == "revolve_cut",
        )
    if (
        Operation is not None
        and Operation.kind in {"revolve_join", "revolve_cut"}
        and (Operation.angle_degrees is not None)
        and (Operation.axis_source_kind is not None)
        and (Operation.axis_source_id is not None)
    ):
        return RevolutionFeature(
            angle=ParamValue(Operation.angle_degrees, ValueKind.ANGLE, "deg"),
            axis_entity_id=AxisSourceId(
                Operation.axis_source_kind, Operation.axis_source_id
            ),
            reversed=Operation.kind == "revolve_cut",
        )
    return None


# this definition exists because focused behavior needs one stable owner
def BuildExtrude(Operation: NativeOperation | None) -> ExtrusionFeature | None:
    if (
        Operation is None
        or Operation.kind not in {"join", "cut", "surface"}
        or Operation.length_mm is None
    ):
        return None
    return ExtrusionFeature(
        length=ParamValue(Operation.length_mm, ValueKind.LENGTH, "mm"),
        end_condition=(
            ExtrusionEndCondition.BLIND
            if Operation.termination_code == 0
            else f"native:{Operation.termination_code}"
        ),
        reversed=Operation.kind == "cut",
        second_length=(
            ParamValue(Operation.second_length_mm, ValueKind.LENGTH, "mm")
            if Operation.second_length_mm is not None
            else None
        ),
    )


# this definition exists because detail operations share dimensional construction
def BuildDetail(
    Operation: NativeOperation | None,
) -> HoleFeature | FilletFeature | ChamferFeature | ShellFeature | None:
    if Operation is None:
        return None
    if (
        Operation.kind == "hole"
        and Operation.diameter_mm is not None
        and Operation.length_mm is not None
    ):
        return HoleFeature(
            diameter=ParamValue(Operation.diameter_mm, ValueKind.LENGTH, "mm"),
            depth=ParamValue(Operation.length_mm, ValueKind.LENGTH, "mm"),
        )
    if Operation.kind == "fillet" and Operation.radius_mm is not None:
        return FilletFeature(
            radius=ParamValue(Operation.radius_mm, ValueKind.LENGTH, "mm")
        )
    if (
        Operation.kind == "chamfer"
        and Operation.length_mm is not None
        and Operation.mode == "equal_distance"
    ):
        return ChamferFeature(
            distance=ParamValue(Operation.length_mm, ValueKind.LENGTH, "mm")
        )
    if Operation.kind == "shell" and Operation.length_mm is not None:
        return ShellFeature(
            thickness=ParamValue(Operation.length_mm, ValueKind.LENGTH, "mm")
        )
    return None


# this definition exists because focused behavior needs one stable owner
def BuildFeature(
    Feature: NativeFeature,
    Operation: NativeOperation | None,
    Sketches: Mapping[int, NativeSketch],
    Planes: Mapping[int, NativePlane],
) -> (
    ExtrusionFeature
    | FilletFeature
    | RevolutionFeature
    | HoleFeature
    | ChamferFeature
    | ShellFeature
    | RefPlaneFeature
    | DomeFeature
    | MoveBodyFeature
    | CombineFeature
    | ScaleFeature
    | NativeFeatureDefinition
):
    Extrusion = BuildExtrude(Operation)
    if Extrusion is not None:
        return Extrusion
    Revolution = BuildRevolve(Operation, Sketches)
    if Revolution is not None:
        return Revolution
    DetailValue = BuildDetail(Operation)
    if DetailValue is not None:
        return DetailValue
    if (
        Operation is not None
        and Operation.kind == "dome"
        and (Operation.length_mm is not None)
    ):
        return DomeFeature(
            height=ParamValue(Operation.length_mm, ValueKind.LENGTH, "mm")
        )
    if Operation is not None and Operation.kind == "move_body":
        Translation = Operation.translation_mm
        if Translation is not None:
            return MoveBodyFeature(translation=VectorThree(*Translation))
    if Operation is not None and Operation.kind == "combine_join":
        return CombineFeature(BoolOperation.JOIN)
    if Operation is not None and Operation.kind == "scale":
        Factors = Operation.scale_factors
        if Factors is not None:
            return ScaleFeature(VectorThree(*Factors))
    Plane = Planes.get(Feature.object_id)
    RefIds = Plane.reference_ids if Plane is not None else ()
    Offset = OperationValue(Feature.dimensions, "offset")
    if Plane is not None and len(RefIds) == 1 and (Offset is not None):
        return RefPlaneFeature(
            support_plane_id=PlaneId(Feature.object_id),
            reference_plane_id=PlaneId(RefIds[0]),
            offset=ParamValue(Offset, ValueKind.LENGTH, "mm"),
        )
    return NativeFallback(Feature, Operation)


# this definition exists because focused behavior needs one stable owner
def OperationValue(
    Dimensions: tuple[NativeDimension, ...], KindValue: str
) -> float | None:
    return next(
        (Dimension.value_mm for Dimension in Dimensions if Dimension.kind == KindValue),
        None,
    )


# this definition exists because focused behavior needs one stable owner
def FeatureKindA(Feature: NativeFeature | XmlFeature) -> FeatureKind:
    if getattr(Feature, "class_name", "") in {"moSketchHole", "moHoleWzd_c"}:
        return FeatureKind.HOLE
    return KFeatureKindByNative.get(Feature.kind.casefold().strip(), FeatureKind.NATIVE)


# this definition exists because focused behavior needs one stable owner
def BrepPayloads(
    Archive: SldprtArchive, Options: ReadOptions
) -> tuple[tuple[BrepPayload, ...], tuple[DiagValue, ...]]:
    if not Options.include_brep:
        return ((), ())
    Payloads: list[BrepPayload] = []
    Diagnostics: list[DiagValue] = []
    for Record in Archive.records:
        if not ContainsParasolidPayload(Record.data):
            continue
        try:
            Decoded = DecodePartitionStream(Record.data, Record.name)
        except SldprtFormatError as ErrorInfo:
            if Options.strict:
                raise
            Diagnostics.append(
                DiagValue(
                    code="sldprt.parasolid_decode_failed",
                    message=str(ErrorInfo),
                    severity=Severity.WARNING,
                    attributes=FrozenMapping({"stream": Record.name}),
                )
            )
            continue
        for Native in Decoded:
            Payloads.append(BrepPayloadA(len(Payloads), Native))
    if not Payloads and Options.strict:
        raise SldprtFormatError("SLDPRT contains no readable Parasolid payload")
    return (tuple(Payloads), tuple(Diagnostics))


# this definition exists because focused behavior needs one stable owner
def BrepPayloadA(Index: int, Native: ParasolidPayload) -> BrepPayload:
    return BrepPayload(
        id=f"sldprt:brep:{Index}",
        format_id="parasolid",
        kind=Native.kind,
        schema=Native.schema,
        sha256=Native.sha256,
        data=Native.data,
        source_stream=Native.stream,
        provenance=Provenance(
            adapter=KFormatId,
            native_id=f"{Native.stream}:{Native.wrapper_offset}",
            spans=(
                ProvenanceSpan(
                    Native.stream,
                    Native.wrapper_offset,
                    Native.compressed_offset
                    + Native.compressed_size
                    - Native.wrapper_offset,
                    "parasolid-wrapper",
                ),
            ),
        ),
        attributes=FrozenMapping(
            {
                "description": Native.description,
                "wrapper_offset": Native.wrapper_offset,
                "magic_offset": Native.magic_offset,
                "compressed_offset": Native.compressed_offset,
                "compressed_size": Native.compressed_size,
                "uncompressed_size": Native.uncompressed_size,
            }
        ),
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )


# this definition exists because focused behavior needs one stable owner
def TypedBrep(Payloads: Sequence[BrepPayload]) -> BrepModel | None:
    Groups: dict[str, list[BrepPayload]] = {}
    for Index, Payload in enumerate(Payloads):
        Groups.setdefault(Payload.source_stream or f"payload:{Index}", []).append(
            Payload
        )
    Models: list[BrepModel] = []
    for Group in Groups.values():
        Decoded = tuple(
            (
                Model
                for Payload in Group
                if Payload.data is not None
                and (Model := DecodeBrepModel(Payload.data)) is not None
            )
        )
        if len(Decoded) == 1:
            Models.append(Decoded[0])
    return Models[0] if len(Models) == 1 else None


# this definition exists because focused behavior needs one stable owner
def BoundingBoxA(Model: NativeModel) -> BoundingBox | None:
    SketchById = {Sketch.object_id: Sketch for Sketch in Model.sketches}
    PlaneById = {Plane.object_id: Plane for Plane in Model.planes}
    Points: list[tuple[float, float, float]] = []
    for Operation in Model.operations:
        if Operation.kind != "join" or Operation.profile_id is None:
            continue
        Sketch = SketchById.get(Operation.profile_id)
        if Sketch is None:
            continue
        Plane = PlaneById.get(Sketch.support_plane_id)
        if Plane is None or Operation.length_mm is None:
            continue
        Direction = tuple((Value * Operation.length_mm for Value in Plane.normal))
        for Profile in Sketch.profiles:
            for Local in ProfileExtrema(Profile):
                BaseValue = tuple(
                    (
                        Plane.origin_mm[Index]
                        + Plane.u_axis[Index] * Local[0]
                        + Plane.v_axis[Index] * Local[1]
                        for Index in range(3)
                    )
                )
                Points.append(BaseValue)
                Points.append(
                    tuple((BaseValue[Index] + Direction[Index] for Index in range(3)))
                )
    if not Points:
        return None
    return BoundingBox(
        minimum=VectorThree(
            *(min((Point[Index] for Point in Points)) for Index in range(3))
        ),
        maximum=VectorThree(
            *(max((Point[Index] for Point in Points)) for Index in range(3))
        ),
    )


# this definition exists because focused behavior needs one stable owner
def ProfileExtrema(Profile: NativeProfile) -> tuple[tuple[float, float], ...]:
    if Profile.kind == "rectangle":
        XZero, YZero, XOneValue, YOneValue = Profile.coordinates
        return (
            (XZero, YZero),
            (XZero, YOneValue),
            (XOneValue, YZero),
            (XOneValue, YOneValue),
        )
    if Profile.kind == "circle":
        FirstCoord, SecondCoord, Radius = Profile.coordinates
        return (
            (FirstCoord - Radius, SecondCoord),
            (FirstCoord + Radius, SecondCoord),
            (FirstCoord, SecondCoord - Radius),
            (FirstCoord, SecondCoord + Radius),
        )
    return ()


# this definition exists because focused behavior needs one stable owner
def FeatureA(Feature: NativeFeature) -> Provenance:
    return ProvenanceA(
        str(Feature.object_id),
        Feature.native_offset,
        (
            Feature.native_end - Feature.native_offset
            if Feature.native_offset is not None and Feature.native_end is not None
            else None
        ),
        "feature-record",
        Confidence=1.0 if Feature.native_offset is not None else 0.6,
        Stream=Feature.native_stream,
    )


# this definition exists because focused behavior needs one stable owner
def FeatureSpan(Sketch: NativeSketch) -> Provenance:
    return ProvenanceA(
        str(Sketch.object_id),
        Sketch.native_offset,
        Sketch.native_end - Sketch.native_offset,
        "sketch-record",
        Stream=Sketch.native_stream,
    )


# this definition exists because focused behavior needs one stable owner
def ProvenanceA(
    NativeId: str,
    Offset: int | None,
    Length: int | None,
    KindValue: str,
    *,
    Confidence: float = 1.0,
    Stream: str = ResolvedFeaturesStream,
) -> Provenance:
    Spans = (
        (ProvenanceSpan(Stream, Offset, Length or 0, KindValue),)
        if Offset is not None
        else ()
    )
    return Provenance(
        adapter=KFormatId, native_id=NativeId, confidence=Confidence, spans=Spans
    )


# this definition exists because focused behavior needs one stable owner
def ConfigId(NativeId: int) -> str:
    return f"sldprt:configuration:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def FeatureId(NativeId: int) -> str:
    return f"sldprt:feature:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def PlaneId(NativeId: int) -> str:
    return f"sldprt:plane:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def SketchId(NativeId: int) -> str:
    return f"sldprt:sketch:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def ParamId(NativeId: int, NameValue: str) -> str:
    return f"sldprt:parameter:{NativeId}:{NameValue}"


# this definition exists because focused behavior needs one stable owner
def ParamEntries(
    NativeId: int, Dimensions: tuple[NativeDimension, ...]
) -> tuple[tuple[NativeDimension, str], ...]:
    Occurrences: Defaultdict[str, int] = Defaultdict(int)
    Result: list[tuple[NativeDimension, str]] = []
    for Dimension in Dimensions:
        Occurrences[Dimension.name] += 1
        ItemValue = Occurrences[Dimension.name]
        ParamKey = ParamId(NativeId, Dimension.name)
        if ItemValue > 1:
            ParamKey += f":{ItemValue}"
        Result.append((Dimension, ParamKey))
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def SelectionId(
    NativeId: int, LocalId: int, KindValue: str = "edge", ProducerId: int | None = None
) -> str:
    Producer = f":{ProducerId}" if ProducerId is not None else ""
    return f"sldprt:selection:{NativeId}:{KindValue}{Producer}:{LocalId}"


# this definition exists because focused behavior needs one stable owner
def ProfileId(NativeId: int, ProfileIndex: int) -> str:
    return f"sldprt:sketch:{NativeId}:profile:{ProfileIndex}"


# this definition exists because focused behavior needs one stable owner
def ProfileEdgeId(NativeId: int, ProfileIndex: int, EdgeIndex: int) -> str:
    return f"sldprt:sketch:{NativeId}:profile:{ProfileIndex}:edge:{EdgeIndex}"


# this definition exists because focused behavior needs one stable owner
def AxisSourceId(KindValue: str, NativeId: int) -> str:
    return f"sldprt:{KindValue}:{NativeId}"


# this definition exists because focused behavior needs one stable owner
def MarkerId(NativeId: int, Offset: int) -> str:
    return f"sldprt:sketch:{NativeId}:native:{Offset}"


# this binding exists because shared behavior needs one stable value
Any = AnyValue

# this binding exists because shared behavior needs one stable value
ArcEllipseGeometry = ArcEllipseGeom

# this binding exists because shared behavior needs one stable value
ArcGeometry = ArcGeom

# this binding exists because shared behavior needs one stable value
ArcParabolaGeometry = ArcParabolaGeom

# this binding exists because shared behavior needs one stable value
AssemblyData = AsmData

# this binding exists because shared behavior needs one stable value
Body = BodyValue

# this binding exists because shared behavior needs one stable value
BooleanOperation = BoolOperation

# this binding exists because shared behavior needs one stable value
BytesIO = BytesIo

# this binding exists because shared behavior needs one stable value
COMPONENT_TREE_STREAM = ComponentTreeStream

# this binding exists because shared behavior needs one stable value
CONTAINER_VERSIONS = ContainerVersions

# this binding exists because shared behavior needs one stable value
CONTENT_TYPES_STREAM = ContentTypesStream

# this binding exists because shared behavior needs one stable value
CadDocument = CadDoc

# this binding exists because shared behavior needs one stable value
CircleGeometry = CircleGeom

# this binding exists because shared behavior needs one stable value
ComponentDocument = ComponentDoc

# this binding exists because shared behavior needs one stable value
Configuration = Config

# this binding exists because shared behavior needs one stable value
ConstraintReference = RuleRef

# this binding exists because shared behavior needs one stable value
DIRECTION_AXIS_ROLE = DirectionAxisRole

# this binding exists because shared behavior needs one stable value
DISPLAY_LISTS_STREAM = DisplayListsStream

# this binding exists because shared behavior needs one stable value
Destination = Target

# this binding exists because shared behavior needs one stable value
Diagnostic = DiagValue

# this binding exists because shared behavior needs one stable value
ET = XmlTree

# this binding exists because shared behavior needs one stable value
EllipseGeometry = EllipseGeom

# this binding exists because shared behavior needs one stable value
FEATURES_STREAM = FeaturesStream

# this binding exists because shared behavior needs one stable value
FORMAT_ID_BY_SUFFIX = FormatIdBySuffix

# this binding exists because shared behavior needs one stable value
GeometryKind = GeomKind

# this binding exists because shared behavior needs one stable value
INFO = InfoValue

# this binding exists because shared behavior needs one stable value
KEYWORDS_STREAM = KeywordsStream

# this binding exists because shared behavior needs one stable value
KIT_DOCUMENT_STREAM = KitDocStream

# this binding exists because shared behavior needs one stable value
KIT_NATIVE_STREAM = KitNativeStream

# this binding exists because shared behavior needs one stable value
KIT_RESOLVED_STREAM = KitResolvedStream

# this binding exists because shared behavior needs one stable value
LineGeometry = LineGeom

# this binding exists because shared behavior needs one stable value
MATES_STREAM_NAME = MatesStreamName

# this binding exists because shared behavior needs one stable value
MATES_STREAM_SUFFIX = MatesStreamSuffix

# this binding exists because shared behavior needs one stable value
MATE_VALUE_SEMANTICS = MateValueSemantics

# this binding exists because shared behavior needs one stable value
MateConstraint = MateRule

# this binding exists because shared behavior needs one stable value
Matrix4 = MatrixFour

# this binding exists because shared behavior needs one stable value
Mesh = MeshValue

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ALIGNMENT_BY_CODE = NativeMateAlignmentByCode

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_ENTITY_MARKERS = NativeMateEntityMarkers

# this binding exists because shared behavior needs one stable value
NATIVE_MATE_NEUTRAL_KIND_ALIASES = NativeMateNeutralKind

# this binding exists because shared behavior needs one stable value
NativeAssembly = NativeAsm

# this binding exists because shared behavior needs one stable value
NativeAssemblyDefinition = NativeAsmDefinition

# this binding exists because shared behavior needs one stable value
NativeAssemblyEncoding = NativeAsmEncoding

# this binding exists because shared behavior needs one stable value
NativeAssemblyEnvelope = NativeAsmEnvelope

# this binding exists because shared behavior needs one stable value
NativeAssemblyOccurrence = NativeAsmItem

# this binding exists because shared behavior needs one stable value
NativeGeometry = NativeGeom

# this binding exists because shared behavior needs one stable value
PARTITION_STREAM = PartitionStream

# this binding exists because shared behavior needs one stable value
PLANE_FEATURE_TYPES = PlaneFeatureTypes

# this binding exists because shared behavior needs one stable value
Parameter = Param

# this binding exists because shared behavior needs one stable value
ParameterRole = ParamRole

# this binding exists because shared behavior needs one stable value
ParameterValue = ParamValue

# this binding exists because shared behavior needs one stable value
Path = FilePath

# this binding exists because shared behavior needs one stable value
PathValue = FilePath

# this binding exists because shared behavior needs one stable value
PointGeometry = PointGeom

# this binding exists because shared behavior needs one stable value
RELATIONSHIPS_STREAM = RelationshipsStream

# this binding exists because shared behavior needs one stable value
RESOLVED_FEATURES_STREAM = ResolvedFeaturesStream

# this binding exists because shared behavior needs one stable value
ReferencePlaneFeature = RefPlaneFeature

# this binding exists because shared behavior needs one stable value
SOLIDWORKS_STREAM = SolidworksStream

# this binding exists because shared behavior needs one stable value
SOLID_BODY_FEATURE_TYPES = SolidBodyFeatureTypes

# this binding exists because shared behavior needs one stable value
SUFFIX_BY_FORMAT_ID = SuffixByFormatId

# this binding exists because shared behavior needs one stable value
SelectionPathElement = SelectionPathElem

# this binding exists because shared behavior needs one stable value
SketchConstraint = SketchRule

# this binding exists because shared behavior needs one stable value
SplineGeometry = SplineGeom

# this binding exists because shared behavior needs one stable value
Vector2 = VectorTwo

# this binding exists because shared behavior needs one stable value
Vector3 = VectorThree

# this binding exists because shared behavior needs one stable value
_ASSEMBLY_DONOR_CARRIED_STREAMS = KAsmDonorCarriedStreams

# this binding exists because shared behavior needs one stable value
_ASSEMBLY_FORMAT_ID = KAsmFormatId

# this binding exists because shared behavior needs one stable value
_ASSEMBLY_READER_REQUIRED_STREAMS = KAsmReaderRequiredStreams

# this binding exists because shared behavior needs one stable value
_ASSEMBLY_REWRITABLE_DONOR_STREAMS = KAsmRewritableDonorStreaA

# this binding exists because shared behavior needs one stable value
_ATTESTED_COMPATIBILITIES = KAttestedCompatibilities

# this binding exists because shared behavior needs one stable value
_AssemblyBundle = AsmBundle

# this binding exists because shared behavior needs one stable value
_AssemblyTemplatePatch = AsmTemplate

# this binding exists because shared behavior needs one stable value
_FEATURE_KIND_BY_NATIVE = KFeatureKindByNative

# this binding exists because shared behavior needs one stable value
_FORMAT_ID = KFormatId

# this binding exists because shared behavior needs one stable value
_GeneratedStreams = Generated

# this binding exists because shared behavior needs one stable value
_NUMBER_TEXT = KNumberText

# this binding exists because shared behavior needs one stable value
_RESOLVED_CONFIGURATION_STREAM = KResolvedConfigStream

# this binding exists because shared behavior needs one stable value
_SOURCE_BYTES_KEY = KSourceBytesKey

# this binding exists because shared behavior needs one stable value
_SOURCE_FORMAT_KEY = KSourceFormatKey

# this binding exists because shared behavior needs one stable value
_SOURCE_KEYS = KSourceKeys

# this binding exists because shared behavior needs one stable value
_SOURCE_SEMANTIC_SHA256_KEY = KSourceSemanticShaTwoFive

# this binding exists because shared behavior needs one stable value
_SOURCE_SHA256_KEY = KSourceShaTwoFiveSixKey

# this binding exists because shared behavior needs one stable value
_TARGET_UNSUPPORTED_CAPABILITIES = KTargetUnsupported

# this binding exists because shared behavior needs one stable value
_WRAPPER_METADATA_KEYS = KWrapperMetaKeys

# this binding exists because shared behavior needs one stable value
_apply_native_equations = ApplyNativeMut

# this binding exists because shared behavior needs one stable value
_assembly_bounding_box = AsmBoundingBox

# this binding exists because shared behavior needs one stable value
_assembly_bundle = AsmBundleA

# this binding exists because shared behavior needs one stable value
_assembly_definition_id = AsmDefinitionId

# this binding exists because shared behavior needs one stable value
_assembly_definitions = AsmDefinitions

# this binding exists because shared behavior needs one stable value
_assembly_document = AsmDoc

# this binding exists because shared behavior needs one stable value
_assembly_documents = AsmDocuments

# this binding exists because shared behavior needs one stable value
_assembly_instance_id = AsmInstanceId

# this binding exists because shared behavior needs one stable value
_assembly_instances = AsmInstances

# this binding exists because shared behavior needs one stable value
_assembly_mate_entity = AsmMateEntity

# this binding exists because shared behavior needs one stable value
_assembly_mates = AsmMates

# this binding exists because shared behavior needs one stable value
_assembly_matrix = AsmMatrix

# this binding exists because shared behavior needs one stable value
_assembly_meshes = AsmMeshes

# this binding exists because shared behavior needs one stable value
_assembly_reader_gaps = AsmReaderGaps

# this binding exists because shared behavior needs one stable value
_assembly_structure_values = AsmStructure

# this binding exists because shared behavior needs one stable value
_attested_generated_bundle_names = AttestedBundle

# this binding exists because shared behavior needs one stable value
_attested_native_proof = AttestedNative

# this binding exists because shared behavior needs one stable value
_attested_transfers = Attested

# this binding exists because shared behavior needs one stable value
_axis_source_id = AxisSourceId

# this binding exists because shared behavior needs one stable value
_body_values = BodyValues

# this binding exists because shared behavior needs one stable value
_bounding_box = BoundingBoxA

# this binding exists because shared behavior needs one stable value
_brep_payload = BrepPayloadA

# this binding exists because shared behavior needs one stable value
_brep_payloads = BrepPayloads

# this binding exists because shared behavior needs one stable value
_bundle_requirements_satisfied = IsBundleSatisfi

# this binding exists because shared behavior needs one stable value
_companion_payloads = Companion

# this binding exists because shared behavior needs one stable value
_component_file_index = ComponentFile

# this binding exists because shared behavior needs one stable value
_configuration_id = ConfigId

# this binding exists because shared behavior needs one stable value
_configuration_values = ConfigValues

# this binding exists because shared behavior needs one stable value
_configurations = Configurations

# this binding exists because shared behavior needs one stable value
_coordinate_offset = Coordinate

# this binding exists because shared behavior needs one stable value
_coordinate_reference = CoordinateRef

# this binding exists because shared behavior needs one stable value
_definition_structure_values = Definition

# this binding exists because shared behavior needs one stable value
_definition_value = DefinitionValue

# this binding exists because shared behavior needs one stable value
_destination_format_id = TargetFormatId

# this binding exists because shared behavior needs one stable value
_destination_path = TargetPath

# this binding exists because shared behavior needs one stable value
_dimension_parameter_value = DimensionParam

# this binding exists because shared behavior needs one stable value
_dimension_text = DimensionText

# this binding exists because shared behavior needs one stable value
_direction_axis_selections = DirectionAxis

# this binding exists because shared behavior needs one stable value
_diverged_donor_records = DivergedDonor

# this binding exists because shared behavior needs one stable value
_diverged_keys = DivergedKeys

# this binding exists because shared behavior needs one stable value
_document_without_source = DocWithout

# this binding exists because shared behavior needs one stable value
_embedded_document = EmbeddedDoc

# this binding exists because shared behavior needs one stable value
_feature_definition = BuildFeature

# this binding exists because shared behavior needs one stable value
_feature_id = FeatureId

# this binding exists because shared behavior needs one stable value
_feature_kind = FeatureKindA

# this binding exists because shared behavior needs one stable value
_feature_provenance = FeatureA

# this binding exists because shared behavior needs one stable value
_feature_span_provenance = FeatureSpan

# this binding exists because shared behavior needs one stable value
_feature_values = FeatureValues

# this binding exists because shared behavior needs one stable value
_final_body_feature_id = FinalBodyId

# this binding exists because shared behavior needs one stable value
_flattened_mates = FlattenedMates

# this binding exists because shared behavior needs one stable value
_flattened_occurrences = Flattened

# this binding exists because shared behavior needs one stable value
_generated_assembly_capabilities = GeneratedAsm

# this binding exists because shared behavior needs one stable value
_generated_assembly_notes = GeneratedAsmA

# this binding exists because shared behavior needs one stable value
_generated_assembly_structure_matches = IsGeneratedAsmB

# this binding exists because shared behavior needs one stable value
_generated_integer = GeneratedA

# this binding exists because shared behavior needs one stable value
_generated_occurrence_labels = GeneratedItem

# this binding exists because shared behavior needs one stable value
_generated_reference_number = GeneratedRef

# this binding exists because shared behavior needs one stable value
_generated_streams = GeneratedB

# this binding exists because shared behavior needs one stable value
_geometry_values = GeomValues

# this binding exists because shared behavior needs one stable value
_instance_structure_values = InstanceValues

# this binding exists because shared behavior needs one stable value
_is_geometry_brep_payload = IsGeomBrep

# this binding exists because shared behavior needs one stable value
_keywords_bytes = KeywordsBytes

# this binding exists because shared behavior needs one stable value
_keywords_root = KeywordsRoot

# this binding exists because shared behavior needs one stable value
_marker_arc_ellipse_geometry = MarkerArcGeom

# this binding exists because shared behavior needs one stable value
_marker_circular_geometry = MarkerCircular

# this binding exists because shared behavior needs one stable value
_marker_curve_reference_indices = MarkerCurveRef

# this binding exists because shared behavior needs one stable value
_marker_curve_semantic = MarkerCurve

# this binding exists because shared behavior needs one stable value
_marker_ellipse_geometry = MarkerEllipse

# this binding exists because shared behavior needs one stable value
_marker_entity = MarkerEntity

# this binding exists because shared behavior needs one stable value
_marker_id = MarkerId

# this binding exists because shared behavior needs one stable value
_marker_object_reference_indices = MarkerObjectRef

# this binding exists because shared behavior needs one stable value
_marker_parabola_geometry = MarkerParabola

# this binding exists because shared behavior needs one stable value
_marker_spline_geometry = MarkerSpline

# this binding exists because shared behavior needs one stable value
_marker_spline_reference_indices = MarkerSplineRef

# this binding exists because shared behavior needs one stable value
_mate_groups = MateGroups

# this binding exists because shared behavior needs one stable value
_mate_instance_path = MateInstance

# this binding exists because shared behavior needs one stable value
_mate_parameter_value = MateParamValue

# this binding exists because shared behavior needs one stable value
_mate_payload = MatePayload

# this binding exists because shared behavior needs one stable value
_mate_provenance = MateProvenance

# this binding exists because shared behavior needs one stable value
_mate_sources = MateSources

# this binding exists because shared behavior needs one stable value
_mate_values = MateValues

# this binding exists because shared behavior needs one stable value
_mesh_values = MeshValues

# this binding exists because shared behavior needs one stable value
_native_assembly_data = NativeAsmData

# this binding exists because shared behavior needs one stable value
_native_assembly_matrix = NativeAsmMatrix

# this binding exists because shared behavior needs one stable value
_native_assembly_structure_values = NativeAsmValues

# this binding exists because shared behavior needs one stable value
_native_attestation = Native

# this binding exists because shared behavior needs one stable value
_native_attestation_bytes = NativeBytes

# this binding exists because shared behavior needs one stable value
_native_body_values = NativeBody

# this binding exists because shared behavior needs one stable value
_native_definition_key = NativeKey

# this binding exists because shared behavior needs one stable value
_native_equation_value = NativeEquation

# this binding exists because shared behavior needs one stable value
_native_feature_definitions_unchanged = IsNativeFeature

# this binding exists because shared behavior needs one stable value
_native_id = NativeId

# this binding exists because shared behavior needs one stable value
_native_marker_geometry = NativeMarkerA

# this binding exists because shared behavior needs one stable value
_native_mate_alignment_offset = NativeMateA

# this binding exists because shared behavior needs one stable value
_native_mate_values = NativeMateB

# this binding exists because shared behavior needs one stable value
_native_part_model = NativePartModel

# this binding exists because shared behavior needs one stable value
_native_source_matches_document = IsNativeSourceD

# this binding exists because shared behavior needs one stable value
_native_stream_sha256 = NativeStreamSha

# this binding exists because shared behavior needs one stable value
_nested_assembly_document = NestedAsmDoc

# this binding exists because shared behavior needs one stable value
_nested_definition_map = NestedMap

# this binding exists because shared behavior needs one stable value
_nested_occurrence_map = NestedItemMap

# this binding exists because shared behavior needs one stable value
_neutral_mate_alignment = NeutralMate

# this binding exists because shared behavior needs one stable value
_neutral_mate_entity_kind = NeutralMateKind

# this binding exists because shared behavior needs one stable value
_neutral_mate_kind = NeutralMateKinA

# this binding exists because shared behavior needs one stable value
_neutral_mate_value = NeutralMateA

# this binding exists because shared behavior needs one stable value
_operation_attributes = OperationAttrs

# this binding exists because shared behavior needs one stable value
_operation_dimension_value = OperationValue

# this binding exists because shared behavior needs one stable value
_operation_selection_entries = OperationA

# this binding exists because shared behavior needs one stable value
_operation_selection_id = OperationId

# this binding exists because shared behavior needs one stable value
_orthonormal_transform = IsOrthonormal

# this binding exists because shared behavior needs one stable value
_parameter_entries = ParamEntries

# this binding exists because shared behavior needs one stable value
_parameter_id = ParamId

# this binding exists because shared behavior needs one stable value
_parameter_millimeters = ParamA

# this binding exists because shared behavior needs one stable value
_parameter_values = ParamValues

# this binding exists because shared behavior needs one stable value
_parameters = Parameters

# this binding exists because shared behavior needs one stable value
_parasolid_payload = Parasolid

# this binding exists because shared behavior needs one stable value
_patch_assembly_instances = PatchAsmMut

# this binding exists because shared behavior needs one stable value
_patch_assembly_mates = PatchAsmMateMut

# this binding exists because shared behavior needs one stable value
_patch_coordinate = IsPatchCoordina

# this binding exists because shared behavior needs one stable value
_patch_feature_names = IsPatchFeatuMut

# this binding exists because shared behavior needs one stable value
_patch_native_assembly = PatchNativeAMut

# this binding exists because shared behavior needs one stable value
_patch_native_template = PatchNativeMut

# this binding exists because shared behavior needs one stable value
_patch_parameters = IsPatchParamete

# this binding exists because shared behavior needs one stable value
_patch_rectangle_profile = PatchRectangle

# this binding exists because shared behavior needs one stable value
_patch_sketch_geometry = PatchSketchGeom

# this binding exists because shared behavior needs one stable value
_patch_support_planes = PatchSupport

# this binding exists because shared behavior needs one stable value
_patch_template_brep = PatchTemplatMut

# this binding exists because shared behavior needs one stable value
_payload_values = PayloadValues

# this binding exists because shared behavior needs one stable value
_plane_id = PlaneId

# this binding exists because shared behavior needs one stable value
_plane_values = PlaneValues

# this binding exists because shared behavior needs one stable value
_planes = Planes

# this binding exists because shared behavior needs one stable value
_point_values = PointValues

# this binding exists because shared behavior needs one stable value
_preserved_generated_mate_streams = SavedGenerated

# this binding exists because shared behavior needs one stable value
_preserved_native_mate_matches = IsSavedNativeMa

# this binding exists because shared behavior needs one stable value
_preserved_source = SavedSource

# this binding exists because shared behavior needs one stable value
_profile_edge_id = ProfileEdgeId

# this binding exists because shared behavior needs one stable value
_profile_extrema = ProfileExtrema

# this binding exists because shared behavior needs one stable value
_profile_id = ProfileId

# this binding exists because shared behavior needs one stable value
_provenance = ProvenanceA

# this binding exists because shared behavior needs one stable value
_replay_compatibility = Replay

# this binding exists because shared behavior needs one stable value
_required_capabilities = Required

# this binding exists because shared behavior needs one stable value
_resolved_component_path = ResolvedPath

# this binding exists because shared behavior needs one stable value
_resolved_features_stream = ResolvedStream

# this binding exists because shared behavior needs one stable value
_retain_source = RetainSource

# this binding exists because shared behavior needs one stable value
_round_number = RoundNumber

# this binding exists because shared behavior needs one stable value
_selection_id = SelectionId

# this binding exists because shared behavior needs one stable value
_selection_values = SelectionValues

# this binding exists because shared behavior needs one stable value
_selections = Selections

# this binding exists because shared behavior needs one stable value
_semantic_document = SemanticDoc

# this binding exists because shared behavior needs one stable value
_semantic_sha256 = SemanticShaTwo

# this binding exists because shared behavior needs one stable value
_sketch = SketchA

# this binding exists because shared behavior needs one stable value
_sketch_constraints = SketchB

# this binding exists because shared behavior needs one stable value
_sketch_id = SketchId

# this binding exists because shared behavior needs one stable value
_sketch_values = SketchValues

# this binding exists because shared behavior needs one stable value
_sketches = Sketches

# this binding exists because shared behavior needs one stable value
_solid_body_feature = SolidBody

# this binding exists because shared behavior needs one stable value
_solidworks_package_streams = Solidworks

# this binding exists because shared behavior needs one stable value
_solidworks_transfers = SolidworksA

# this binding exists because shared behavior needs one stable value
_solidworks_xml = SolidworksXml

# this binding exists because shared behavior needs one stable value
_source_bytes = SourceBytes

# this binding exists because shared behavior needs one stable value
_source_template = SourceTemplate

# this binding exists because shared behavior needs one stable value
_timeline = Timeline

# this binding exists because shared behavior needs one stable value
_transform_values = TransformValues

# this binding exists because shared behavior needs one stable value
_typed_brep = TypedBrep

# this binding exists because shared behavior needs one stable value
_unit_vector = IsUnitVector

# this binding exists because shared behavior needs one stable value
_validate_source_suffix = ValidateSource

# this binding exists because shared behavior needs one stable value
_vector_values = VectorValues

# this binding exists because shared behavior needs one stable value
_write_destination = WriteTargetMut

# this binding exists because shared behavior needs one stable value
_xml_attribute = XmlAttr

# this binding exists because shared behavior needs one stable value
_xml_elements_by_id = XmlElementsById

# this binding exists because shared behavior needs one stable value
_yes_text = YesText

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
build_sldprt = BuildSldprt

# this binding exists because shared behavior needs one stable value
contains_parasolid_payload = ContainsParasolidPayload

# this binding exists because shared behavior needs one stable value
dataclass = DataClass

# this binding exists because shared behavior needs one stable value
decode_brep_model = DecodeBrepModel

# this binding exists because shared behavior needs one stable value
decode_mate_list = DecodeMateList

# this binding exists because shared behavior needs one stable value
decode_native_assembly = DecodeNativeAsm

# this binding exists because shared behavior needs one stable value
decode_native_model = DecodeNativeModel

# this binding exists because shared behavior needs one stable value
decode_partition_stream = DecodePartitionStream

# this binding exists because shared behavior needs one stable value
defaultdict = Defaultdict

# this binding exists because shared behavior needs one stable value
encode_blank_partition_stream = EncodeBlankPartition

# this binding exists because shared behavior needs one stable value
encode_brep_model = EncodeBrepModel

# this binding exists because shared behavior needs one stable value
encode_native_assembly = EncodeNativeAsm

# this binding exists because shared behavior needs one stable value
encode_native_assembly_envelope = EncodeNativeAsmEnvelope

# this binding exists because shared behavior needs one stable value
encode_native_part = EncodeNativePart

# this binding exists because shared behavior needs one stable value
encode_partition_stream = EncodePartitionStream

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
is_native_parasolid_payload = IsNativeParasolidPayload

# this binding exists because shared behavior needs one stable value
json = JsonValue

# this binding exists because shared behavior needs one stable value
math = MathValue

# this binding exists because shared behavior needs one stable value
operation_axis_subelement = OperationAxisSubElem

# this binding exists because shared behavior needs one stable value
os = OsModule

# this binding exists because shared behavior needs one stable value
re = RegexLib

# this binding exists because shared behavior needs one stable value
read_sldprt = ReadSldprt

# this binding exists because shared behavior needs one stable value
replace = Replace

# this binding exists because shared behavior needs one stable value
retained_capabilities = RetainedCapabilities

# this binding exists because shared behavior needs one stable value
semantic_metadata = SemanticMeta

# this binding exists because shared behavior needs one stable value
source_payload_indexes = SourcePayloadIndexes

# this binding exists because shared behavior needs one stable value
struct = Struct

# this binding exists because shared behavior needs one stable value
suppress = Suppress

# this binding exists because shared behavior needs one stable value
tempfile = Tempfile

# this binding exists because shared behavior needs one stable value
with_wrapper_metadata = WithWrapperMeta

# this binding exists because shared behavior needs one stable value
write_sldprt = WriteSldprt

# this binding exists because shared behavior needs one stable value
ApplyNative = ApplyNativeMut

# this binding exists because shared behavior needs one stable value
BundleSatisfied = IsBundleSatisfi

# this binding exists because shared behavior needs one stable value
GeneratedAsmB = IsGeneratedAsmB

# this binding exists because shared behavior needs one stable value
NativeFeatureA = IsNativeFeature

# this binding exists because shared behavior needs one stable value
NativeSourceDoc = IsNativeSourceD

# this binding exists because shared behavior needs one stable value
Orthonormal = IsOrthonormal

# this binding exists because shared behavior needs one stable value
PatchAsm = PatchAsmMut

# this binding exists because shared behavior needs one stable value
PatchAsmMates = PatchAsmMateMut

# this binding exists because shared behavior needs one stable value
PatchCoordinate = IsPatchCoordina

# this binding exists because shared behavior needs one stable value
PatchFeature = IsPatchFeatuMut

# this binding exists because shared behavior needs one stable value
PatchNative = PatchNativeMut

# this binding exists because shared behavior needs one stable value
PatchNativeAsm = PatchNativeAMut

# this binding exists because shared behavior needs one stable value
PatchParameters = IsPatchParamete

# this binding exists because shared behavior needs one stable value
PatchTemplate = PatchTemplatMut

# this binding exists because shared behavior needs one stable value
SavedNativeMate = IsSavedNativeMa

# this binding exists because shared behavior needs one stable value
UnitVector = IsUnitVector

# this binding exists because shared behavior needs one stable value
WriteTarget = WriteTargetMut

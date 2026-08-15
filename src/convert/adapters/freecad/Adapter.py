# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from contextlib import suppress as Suppress
from dataclasses import replace as Replace
from datetime import datetime as Datetime, timezone as Timezone
from enum import Enum
import hashlib as Hashlib
import io as IoStream
import json as JsonValue
import math as MathValue
import os as OsModule
from pathlib import Path as FilePath
import re as RegexLib
import tempfile as Tempfile
from typing import TypeGuard
import xml.etree.ElementTree as XmlTree
import zipfile as Zipfile
from convert.adapters.base import (
    AdapterInfo,
    CarrierReason,
    CapabilityTransfer,
    Destination as Target,
    ProbeResult,
    ReadOptions,
    Source,
    TransferMode,
    WriteOptions,
    WriteResult,
    is_binary_destination as IsBinaryTarget,
    is_windows_device_name as IsWindowsDeviceName,
)
from interchange import (
    BrepPayload,
    CadDocument as CadDoc,
    CadSource,
    Capability,
    ChamferFeature,
    ComponentDefinition,
    ComponentKind,
    Configuration as Config,
    Diagnostic as DiagValue,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    Mesh as MeshValue,
    PayloadRole,
    Severity,
    filter_document as FilterDoc,
    frozen_mapping as FrozenMapping,
    infer_capabilities as InferCapabilities,
    semantic_metadata as SemanticMeta,
    source_payload_indexes as SourcePayloadIndexes,
)
from interchange.serialization.EncodeData import ToData
from interchange.serialization.WireData import ValidateWireMap
from convert.adapters.freecad.Archive import (
    DOCUMENT_ENTRY as DocEntry,
    MANIFEST_ENTRY as ManifestEntry,
    NATIVE_DOCUMENT_SHA256_ATTRIBUTE as KNativeDocHashAttr,
    NativeBrepKey,
    MAX_ENTRY_SIZE as MaxEntrySize,
    MAX_EXTERNAL_FILES as MaxOuterFiles,
    MAX_TOTAL_SIZE as MaxTotalSize,
    native_brep_key as ManifestNativeBrepKey,
    validated_archive_members as ValidatedArchiveMembers,
    validated_document_xml as ValidatedDocXml,
    build_fcstd_archive as BuildFcstdArchive,
    extract_manifest_from_fcstd as ExtractManifestFromFcstd,
    native_expression_parts as NativeExpressionParts,
    native_shape_feature_count as NativeShapeFeatureCount,
    native_sketch_carrier_reasons as NativeSketchCarrier,
    native_sketch_parts as NativeSketchParts,
)
from convert.adapters.freecad.Brep import (
    FreeCADBrepWriteError as FreeCadBrepWriteError,
    brep_model_brep as BrepModelBrep,
    proven_ascii_brep as ProvenAsciiBrep,
)
from convert.adapters.freecad.Format import (
    CAPABILITY_CARRIER_REASONS as CapabilityCarrierReasons,
    INFO as InfoValue,
    SUFFIX as Suffix,
)
from convert.adapters.freecad.Native import (
    NativeFreeCADError as NativeFreeCadError,
    probe_native_fcstd as ProbeNativeFcstd,
    read_native_fcstd as ReadNativeFcstd,
)
from convert.adapters.freecad.Protocol import (
    FEATURE_WRITE_KINDS as FeatureWriteKinds,
    FREECAD_BREP_FORMAT_IDS as FreecadBrepFormatIds,
    MATE_WRITE_KINDS as MateWriteKinds,
    XML_TRUE_VALUES as XmlTrueValues,
)


# mapping payloads require string keys before archive fields can be inspected safely
def IsPayloadMap(Value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(Value, Mapping)


# sequence payloads require a concrete element contract before archive fields are traversed
def IsPayloadSeq(Value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(Value, Sequence) and not isinstance(
        Value, (str, bytes, bytearray)
    )


# this binding exists because shared behavior needs one stable value
KNativeDocId = "freecad:native-document"

# this binding exists because shared behavior needs one stable value
KNativeDocBindingId = "freecad:native-document-binding"

# this binding exists because shared behavior needs one stable value
KReplaySemanticAttr = "freecad.replay_semantic_sha256"

# this binding exists because shared behavior needs one stable value
KNativeExtrusionEnd = frozenset(
    {
        ExtrusionEndCondition.BLIND.value,
        ExtrusionEndCondition.TWO_LENGTHS.value,
        ExtrusionEndCondition.MID_PLANE.value,
    }
)

# this binding exists because shared behavior needs one stable value
KFeatureWriteValues = frozenset((KindValue.value for KindValue in FeatureWriteKinds))

# this binding exists because shared behavior needs one stable value
KMateWriteValues = frozenset((KindValue.value for KindValue in MateWriteKinds))


# this definition exists because focused behavior needs one stable owner
class FreeCadAdapterA(RuntimeError):

    # this definition exists because focused behavior needs one stable owner
    def __init__(self, Message: str) -> None:
        super().__init__(Message)


# this definition exists because focused behavior needs one stable owner
def DocToManifest(DocValue: CadDoc) -> dict[str, object]:
    RawManifest: object = ToData(DocValue)
    if not IsPayloadMap(RawManifest):
        raise TypeError("CadDocument.to_dict() must produce a mapping")
    Manifest = dict(RawManifest)
    if Manifest.get("$type") == "CadDocument":
        RawDocument: object = DocValue.to_dict()
        if not IsPayloadMap(RawDocument):
            raise TypeError("CadDocument.to_dict() must produce a mapping")
        Required = set(RawDocument)
        Missing = sorted(Required.difference(Manifest))
        if Missing:
            raise ValueError("CadDocument manifest is missing: " + ", ".join(Missing))
    return Manifest


# this definition exists because focused behavior needs one stable owner
def SourceBytes(Source: Source) -> bytes:
    if isinstance(Source, bytes):
        return Source
    if isinstance(Source, bytearray):
        return bytes(Source)
    if isinstance(Source, (str, FilePath)):
        return FilePath(Source).expanduser().resolve().read_bytes()
    Reader = getattr(Source, "read", None)
    if callable(Reader):
        Position = None
        TellValue = getattr(Source, "tell", None)
        SeekValue = getattr(Source, "seek", None)
        if callable(TellValue):
            try:
                Position = TellValue()
            except (OSError, ValueError):
                Position = None
        DataValue = Reader()
        if Position is not None and callable(SeekValue):
            with Suppress(OSError, ValueError):
                SeekValue(Position)
        if isinstance(DataValue, str):
            raise TypeError("FCStd input must be opened in binary mode")
        if isinstance(DataValue, (bytes, bytearray)):
            return bytes(DataValue)
    raise TypeError("source must be a path, bytes, or binary stream")


# this definition exists because focused behavior needs one stable owner
def ResolveTarget(Target: Destination) -> FilePath | None:
    if isinstance(Target, (str, FilePath)):
        return FilePath(Target).expanduser().resolve()
    return None


# this definition exists because focused behavior needs one stable owner
def SourcePath(Source: Source) -> str:
    if isinstance(Source, (str, FilePath)):
        return str(FilePath(Source).expanduser().resolve())
    NameValue = getattr(Source, "name", "")
    return str(NameValue) if isinstance(NameValue, (str, FilePath)) else ""


# this definition recursively filters linked documents while preserving invalid metadata
def FilterOuters(Outer: object, Settings: ReadOptions) -> tuple[list[object], bool]:
    if not IsPayloadSeq(Outer):
        return ([], False)
    StrippedOuter: list[object] = []
    Changed = False
    for Value in Outer:
        if not IsPayloadMap(Value):
            StrippedOuter.append(Value)
            continue
        Linked = Value.get("document")
        Mapped = IsPayloadMap(Linked)
        if Mapped:
            try:
                Linked = CadDoc.from_dict(ValidateWireMap(Linked))
            except (TypeError, ValueError, RecursionError):
                StrippedOuter.append(Value)
                continue
        if not isinstance(Linked, CadDoc):
            StrippedOuter.append(Value)
            continue
        ItemValue = dict(Value)
        Stripped = FilteredDoc(Linked, Settings)
        ItemValue["document"] = Stripped.to_dict() if Mapped else Stripped
        StrippedOuter.append(ItemValue)
        Changed = True
    return (StrippedOuter, Changed)


# this definition updates only the external document metadata when filtering changes it
def FilterOuterMeta(
    MetaValue: Mapping[str, object], Settings: ReadOptions
) -> Mapping[str, object]:
    FreecadValue = MetaValue.get("freecad")
    Freecad: Mapping[str, object] = FreecadValue if IsPayloadMap(FreecadValue) else {}
    Outer = Freecad.get("external_documents", [])
    StrippedOuter, Changed = FilterOuters(Outer, Settings)
    if not Changed:
        return MetaValue
    FreecadCopy = dict(Freecad)
    FreecadCopy["external_documents"] = StrippedOuter
    MetaCopy = dict(MetaValue)
    MetaCopy["freecad"] = FreecadCopy
    return MetaCopy


# this definition applies read filters to a document and its linked documents
def FilteredDoc(DocValue: CadDocument, Settings: ReadOptions) -> CadDoc:
    Filtered = FilterDoc(
        DocValue,
        include_brep=Settings.IncludeBrep,
        include_tessellation=Settings.IncludeMesh,
        keep_payload_records=False,
    )
    MetaValue: Mapping[str, object] = FilterOuterMeta(Filtered.metadata, Settings)
    return Replace(Filtered, metadata=MetaValue)


# this definition exists because focused behavior needs one stable owner
def IsNativeDoc(Payload: BrepPayload) -> bool:
    return (
        Payload.id == KNativeDocId
        and Payload.format_id == InfoValue.format_id
        and (Payload.kind == "native_document")
        and (Payload.role == PayloadRole.DOCUMENT)
    )


# this definition exists because focused behavior needs one stable owner
def IsNativeDocA(Payload: BrepPayload) -> bool:
    return (
        Payload.id == KNativeDocBindingId
        and Payload.format_id == f"{InfoValue.format_id}.sha256"
        and (Payload.kind == "native_document_binding")
        and (Payload.schema == "sha256")
        and (Payload.role == PayloadRole.VERIFICATION)
    )


# this definition exists because focused behavior needs one stable owner
def IsNative(Payload: BrepPayload) -> bool:
    return IsNativeDoc(Payload) or IsNativeDocA(Payload)


# this definition exists because focused behavior needs one stable owner
def NativeDocPair(DocValue: CadDocument) -> tuple[BrepPayload, BrepPayload] | None:
    Documents = tuple(
        (Payload for Payload in DocValue.brep_payloads if IsNativeDoc(Payload))
    )
    Bindings = tuple(
        (Payload for Payload in DocValue.brep_payloads if IsNativeDocA(Payload))
    )
    if len(Documents) != 1 or len(Bindings) != 1:
        return None
    NativeDoc = Documents[0]
    Binding = Bindings[0]
    try:
        NativeDigest = bytes.fromhex(NativeDoc.sha256)
    except ValueError:
        return None
    if len(NativeDigest) != Hashlib.sha256().digest_size:
        return None
    if (
        NativeDoc.data is None
        or Hashlib.sha256(NativeDoc.data).digest() != NativeDigest
        or Binding.data != NativeDigest
        or (Binding.sha256 != Hashlib.sha256(NativeDigest).hexdigest())
    ):
        return None
    return (NativeDoc, Binding)


# this definition exists because focused behavior needs one stable owner
def MappedOuter(
    MetaValue: Mapping[str, object], Transform: Callable[[CadDocument], CadDocument]
) -> Mapping[str, object]:
    Freecad = MetaValue.get("freecad", {})
    if not IsPayloadMap(Freecad):
        return MetaValue
    Values = Freecad.get("external_documents", [])
    if not IsPayloadSeq(Values):
        return MetaValue
    Changed = False
    Mapped: list[object] = []
    for Value in Values:
        if not IsPayloadMap(Value):
            Mapped.append(Value)
            continue
        Linked = Value.get("document")
        if not isinstance(Linked, CadDoc):
            Mapped.append(Value)
            continue
        ItemValue = dict(Value)
        ItemValue["document"] = Transform(Linked)
        Mapped.append(ItemValue)
        Changed = True
    if not Changed:
        return MetaValue
    FreecadCopy = dict(Freecad)
    FreecadCopy["external_documents"] = Mapped
    Result = dict(MetaValue)
    Result["freecad"] = FreecadCopy
    return FrozenMapping(Result)


# this definition exists because focused behavior needs one stable owner
def SemanticDoc(DocValue: CadDocument) -> CadDoc:
    EnvelopeIndexes = SourcePayloadIndexes(DocValue)
    AsmValue = DocValue.assembly
    if AsmValue is not None:
        AsmValue = Replace(
            AsmValue,
            documents=tuple(
                (
                    Replace(
                        ItemValue,
                        document=SemanticDoc(ItemValue.document),
                    )
                    for ItemValue in AsmValue.documents
                )
            ),
        )
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
                attributes=FrozenMapping(
                    {
                        KeyValue: Value
                        for KeyValue, Value in Payload.attributes.items()
                        if KeyValue != KReplaySemanticAttr
                    }
                ),
            )
            for Index, Payload in enumerate(DocValue.brep_payloads)
            if Index not in EnvelopeIndexes and (not IsNative(Payload))
        )
    )
    MetaValue = MappedOuter(DocValue.metadata, SemanticDoc)
    return Replace(
        DocValue,
        source=CadSource("", "", ""),
        brep_payloads=Payloads,
        metadata=SemanticMeta(MetaValue),
        assembly=AsmValue,
    )


# this definition exists because focused behavior needs one stable owner
def SemanticDigest(DocValue: CadDocument) -> str:
    DataValue = SemanticDoc(DocValue).to_json(indent=None).encode("utf-8")
    return Hashlib.sha256(DataValue).hexdigest()


# this definition exists because focused behavior needs one stable owner
def AnnotateNative(DocValue: CadDocument) -> CadDoc:
    AsmValue = DocValue.assembly
    if AsmValue is not None:
        AsmValue = Replace(
            AsmValue,
            documents=tuple(
                (
                    Replace(
                        ItemValue,
                        document=AnnotateNative(ItemValue.document),
                    )
                    for ItemValue in AsmValue.documents
                )
            ),
        )
    MetaValue = MappedOuter(DocValue.metadata, AnnotateNative)
    Annotated = Replace(DocValue, metadata=MetaValue, assembly=AsmValue)
    PairValue = NativeDocPair(Annotated)
    if PairValue is None:
        return Annotated
    NativeDoc, _ = PairValue
    Digest = SemanticDigest(Annotated)
    Payloads = tuple(
        (
            (
                Replace(
                    Payload,
                    attributes=FrozenMapping(
                        {**Payload.attributes, KReplaySemanticAttr: Digest}
                    ),
                )
                if Payload.id == NativeDoc.id and IsNativeDoc(Payload)
                else Payload
            )
            for Payload in Annotated.brep_payloads
        )
    )
    return Replace(Annotated, brep_payloads=Payloads)


# this definition exists because focused behavior needs one stable owner
def UnchangedNative(DocValue: CadDocument) -> bytes | None:
    PairValue = NativeDocPair(DocValue)
    if PairValue is None:
        return None
    NativeDoc, _ = PairValue
    Expected = NativeDoc.attributes.get(KReplaySemanticAttr)
    if not isinstance(Expected, str) or Expected != SemanticDigest(DocValue):
        return None
    DataValue = NativeDoc.data
    if DataValue is None:
        return None
    try:
        Archive, _ = ValidatedArchiveMembers(DataValue)
        Archive.close()
    except (OSError, ValueError, Zipfile.BadZipFile):
        return None
    try:
        Reparsed = ReadNativeFcstd(DataValue, DocValue.source.path)
    except (NativeFreeCadError, OSError, TypeError, ValueError):
        return None
    if SemanticDigest(Reparsed) != Expected:
        return None
    return DataValue


# this definition exists because focused behavior needs one stable owner
def EnumText(Value: str | Enum | None) -> str:
    return str(Value.value if isinstance(Value, Enum) else Value or "").casefold()


# this definition exists because focused behavior needs one stable owner
def DocTree(DocValue: CadDocument) -> tuple[CadDoc, ...]:
    Pending = [DocValue]
    Result: list[CadDoc] = []
    SeenValue: set[int] = set()
    while Pending:
        ItemValue = Pending.pop()
        Identity = id(ItemValue)
        if Identity in SeenValue:
            continue
        SeenValue.add(Identity)
        Result.append(ItemValue)
        if ItemValue.assembly is not None:
            Pending.extend(
                (
                    Component.document
                    for Component in reversed(ItemValue.assembly.documents)
                )
            )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def HasNativeGraph(DocValue: CadDocument) -> bool:
    Freecad = DocValue.metadata.get("freecad", {})
    if not IsPayloadMap(Freecad):
        return False
    Objects = Freecad.get("objects", ())
    return IsPayloadSeq(Objects) and bool(Objects)


# this definition exists because focused behavior needs one stable owner
def HasFeatureEdges(DocValue: CadDocument, Feature: FeatureStep) -> bool:
    Attributes = Feature.Attributes
    for NameValue in (
        "selected_native_local_edge_ids",
        "native_local_edge_ids",
        "edge_ids",
        "edges",
    ):
        Values = Attributes.get(NameValue, ())
        if IsPayloadSeq(Values) and any(
            (isinstance(Value, (int, float)) and Value > 0 for Value in Values)
        ):
            return True
    Selections = {Selection.id: Selection for Selection in DocValue.selections}
    for SelectionId in Feature.SelectionIds:
        Selection = Selections.get(SelectionId)
        if Selection is None:
            continue
        if any(
            (
                RegexLib.fullmatch(
                    "(?:Edge|edge:)(\\d+)", ItemValue.subelement, RegexLib.IGNORECASE
                )
                for ItemValue in Selection.path
            )
        ):
            return True
        if (
            Selection.query.get("topology_role")
            == "extrusion_terminal_profile_boundary"
        ):
            return True
        for NameValue in ("edge_index", "native_local_id", "index"):
            QueryValue = Selection.query.get(NameValue)
            if isinstance(QueryValue, (int, float)) and QueryValue > 0:
                return True
    return False


# this definition exists because focused behavior needs one stable owner
def IsExtrusion(Feature: FeatureStep) -> bool:
    Definition = Feature.Definition
    if not isinstance(Definition, ExtrusionFeature):
        return False
    if EnumText(Definition.end_condition) not in KNativeExtrusionEnd:
        return False
    if (
        Definition.second_end_condition is not None
        and EnumText(Definition.second_end_condition) not in KNativeExtrusionEnd
    ):
        return False
    if any(
        (
            Value is not None
            for Value in (
                Definition.offset,
                Definition.second_offset,
                Definition.draft_angle,
                Definition.second_draft_angle,
            )
        )
    ):
        return False
    if Definition.up_to_reference or Definition.second_up_to_reference:
        return False
    return EnumText(Feature.Operation) in {"", "create", "join", "cut", "intersect"}


# this definition rejects records that do not represent transferable timeline features
def IsFeatureNeeded(
    Feature: FeatureStep,
    DependentFeatureIds: set[str],
    FinalFeatureIds: Collection[str | None],
) -> bool:
    KindValue = EnumText(Feature.EntityKind)
    if KindValue == FeatureKind.IMPORTED.value:
        return False
    NativeType = str(Feature.Attributes.get("native_type", "")).casefold()
    if KindValue == FeatureKind.REFERENCE.value and NativeType in {"plane", "sketch"}:
        return False
    IsUnusedNative = (
        KindValue == FeatureKind.NATIVE.value
        and Feature.EntityId not in DependentFeatureIds
        and Feature.EntityId not in FinalFeatureIds
        and not Feature.InputFeatureIds
        and Feature.SketchId is None
        and not Feature.ParameterIds
        and not Feature.SelectionIds
    )
    return not IsUnusedNative


# this definition selects only timeline features that require transfer accounting
def FeatureSet(DocValue: CadDocument) -> tuple[FeatureStep, ...]:
    DependentFeatureIds = {
        FeatureId
        for Feature in DocValue.feature_timeline
        for FeatureId in Feature.InputFeatureIds
    }
    FinalFeatureIds = {BodyValue.final_feature_id for BodyValue in DocValue.bodies}
    return tuple(
        Feature
        for Feature in DocValue.feature_timeline
        if IsFeatureNeeded(Feature, DependentFeatureIds, FinalFeatureIds)
    )


# this definition identifies feature kinds that the native writer can reconstruct
def CanWriteFeature(
    DocValue: CadDocument, Feature: FeatureStep, SketchNative: Mapping[str, bool]
) -> bool:
    KindValue = EnumText(Feature.EntityKind)
    if Feature.IsSuppressed or KindValue not in KFeatureWriteValues:
        return False
    if KindValue == FeatureKind.EXTRUSION.value:
        return (
            bool(Feature.SketchId)
            and SketchNative.get(Feature.SketchId or "", False)
            and IsExtrusion(Feature)
        )
    if KindValue == FeatureKind.FILLET.value:
        Definition = Feature.Definition
        return (
            isinstance(Definition, FilletFeature)
            and not Definition.variable_radius_parameter_ids
            and bool(Feature.InputFeatureIds)
            and HasFeatureEdges(DocValue, Feature)
        )
    if KindValue == FeatureKind.CHAMFER.value:
        Definition = Feature.Definition
        return (
            isinstance(Definition, ChamferFeature)
            and Definition.mode == "equal_distance"
            and Definition.second_distance is None
            and Definition.angle is None
            and bool(Feature.InputFeatureIds)
            and HasFeatureEdges(DocValue, Feature)
        )
    return False


# this definition explains why a timeline feature requires carrier preservation
def FeatureReasons(
    Feature: FeatureStep, SketchCarrierReasons: Mapping[str, CarrierReason]
) -> frozenset[CarrierReason]:
    KindValue = EnumText(Feature.EntityKind)
    if Feature.IsSuppressed or KindValue == FeatureKind.REFERENCE.value:
        return frozenset({CarrierReason.TARGET_UNSUPPORTED})
    if KindValue == FeatureKind.NATIVE.value:
        return frozenset({CarrierReason.SOURCE_OPAQUE})
    Reasons: set[CarrierReason] = set()
    if KindValue == FeatureKind.EXTRUSION.value:
        SketchReason = SketchCarrierReasons.get(Feature.SketchId or "")
        if SketchReason is not None:
            Reasons.add(SketchReason)
        if not Feature.SketchId or not IsExtrusion(Feature):
            Reasons.add(CarrierReason.WRITER_UNIMPLEMENTED)
    return frozenset(Reasons or {CarrierReason.WRITER_UNIMPLEMENTED})


# this definition counts native and carrier feature transfer paths
def FeatureParts(
    DocValue: CadDocument,
    SketchNative: Mapping[str, bool],
    SketchCarrierReasons: Mapping[str, CarrierReason],
) -> tuple[int, int, frozenset[CarrierReason]]:
    Features = FeatureSet(DocValue)
    if HasNativeGraph(DocValue) and DocValue.assembly is None:
        return (len(Features), 0, frozenset())
    Carrier = 0
    Reasons: set[CarrierReason] = set()
    for Feature in Features:
        if CanWriteFeature(DocValue, Feature, SketchNative):
            continue
        Carrier += 1
        Reasons.update(FeatureReasons(Feature, SketchCarrierReasons))
    return (len(Features), Carrier, frozenset(Reasons))


# this definition exists because focused behavior needs one stable owner
def SelectionParts(DocValue: CadDocument) -> tuple[int, int]:
    Targets = {
        *(Plane.id for Plane in DocValue.support_planes),
        *(Sketch.id for Sketch in DocValue.sketches),
        *(Feature.id for Feature in DocValue.feature_timeline),
        *(BodyValue.id for BodyValue in DocValue.bodies),
    }
    Native = 0
    Carrier = 0
    for Selection in DocValue.selections:
        NativePath = bool(Selection.path) and all(
            (ItemValue.entity_id in Targets for ItemValue in Selection.path)
        )
        NativePoint = Selection.point is not None
        if NativePath or NativePoint:
            Native += 1
        else:
            Carrier += 1
        if Selection.query:
            Carrier += 1
    return (Native, Carrier)


# this definition exists because focused behavior needs one stable owner
def ConfigParts(DocValue: CadDocument) -> tuple[int, int]:
    Native = 0
    Carrier = 0
    for Config in DocValue.configurations:
        if (
            len(DocValue.configurations) == 1
            and Config.active
            and (Config.parent_id is None)
            and (not Config.overrides)
            and (not Config.suppressed_feature_ids)
        ):
            Native += 1
        else:
            Carrier += 1
    return (Native, Carrier)


# this definition exists because focused behavior needs one stable owner
def MateParts(DocValue: CadDocument) -> tuple[int, int]:
    AsmValue = DocValue.assembly
    if AsmValue is None:
        return (0, 0)
    Entities = {Entity.id: Entity for Entity in AsmValue.mate_entities}
    InstanceIds = {Instance.id for Instance in AsmValue.instances}
    Native = 0
    Carrier = 0
    for MateValue in AsmValue.mates:
        Attributes = MateValue.attributes
        References = Attributes.get("references", ())
        HasNativeReferences = IsPayloadSeq(References) and (len(References) >= 2)
        Linked = [Entities.get(EntityId) for EntityId in MateValue.entity_ids[:2]]
        HasItemReferences = len(Linked) == 2 and all(
            (
                Entity is not None
                and bool(Entity.instance_path)
                and all(
                    (InstanceId in InstanceIds for InstanceId in Entity.instance_path)
                )
                for Entity in Linked
            )
        )
        if EnumText(MateValue.kind) in KMateWriteValues and (
            HasNativeReferences or HasItemReferences
        ):
            Native += 1
        else:
            Carrier += 1
    return (Native, Carrier)


# this definition exists because focused behavior needs one stable owner
def IsExactPayload(Payload: BrepPayload) -> bool:
    DataValue = Payload.PayloadData
    Provenance = Payload.Provenance
    Attributes = Payload.Attributes
    FreecadObject = Attributes.get("freecad_object")
    FreecadObjectType = Attributes.get("freecad_object_type")
    FreecadProp = Attributes.get("freecad_property")
    NativeDigestText = Attributes.get(KNativeDocHashAttr)
    PropDataValue: object = Attributes.get("freecad_property_data")
    PropData: Mapping[str, object] = (
        PropDataValue if IsPayloadMap(PropDataValue) else {}
    )
    PropAttributesValue = PropData.get("attributes")
    PropAttributes: Mapping[str, object] = (
        PropAttributesValue if IsPayloadMap(PropAttributesValue) else {}
    )
    PropChildrenValue = PropData.get("children")
    PropChildren = PropChildrenValue if IsPayloadSeq(PropChildrenValue) else ()
    PartFiles = tuple(
        (
            ChildAttributes.get("file")
            for Child in PropChildren
            if IsPayloadMap(Child)
            and Child.get("tag") == "Part"
            and IsPayloadMap((ChildAttributes := Child.get("attributes")))
        )
    )
    return (
        Payload.ValueRole == PayloadRole.BREP
        and DataValue is not None
        and (Payload.FormatId.casefold() in FreecadBrepFormatIds)
        and (Payload.EntityKind == "shape")
        and Payload.SchemaText.startswith("CASCADE Topology V")
        and (Payload.SourceDigest == Hashlib.sha256(DataValue).hexdigest())
        and (Provenance is not None)
        and (Provenance.Adapter == InfoValue.format_id)
        and (Provenance.Confidence == 1.0)
        and isinstance(FreecadObject, str)
        and bool(FreecadObject)
        and isinstance(FreecadObjectType, str)
        and bool(FreecadObjectType)
        and isinstance(FreecadProp, str)
        and bool(FreecadProp)
        and isinstance(NativeDigestText, str)
        and (RegexLib.fullmatch("[0-9a-f]{64}", NativeDigestText) is not None)
        and (Provenance.NativeId == f"{FreecadObject}.{FreecadProp}")
        and (Payload.SourceStream == f"{FreecadObject}.{FreecadProp}.brp")
        and (PropData.get("tag") == "Property")
        and (PropAttributes.get("name") == FreecadProp)
        and (PropAttributes.get("type") == "Part::PropertyPartShape")
        and (PartFiles == (Payload.SourceStream,))
    )


# this definition exists because focused behavior needs one stable owner
def ManifestBrep(DocValue: CadDocument) -> tuple[Mapping[str, object], ...]:
    Values = DocToManifest(DocValue).get("brep_payloads", ())
    if IsPayloadMap(Values):
        Values = Values.get("$tuple", ())
    if not IsPayloadSeq(Values):
        return ()
    Result = tuple((Value for Value in Values if IsPayloadMap(Value)))
    return Result if len(Result) == len(DocValue.brep_payloads) else ()


# this definition exists because focused behavior needs one stable owner
def NativeDocShaTwo(DocValue: CadDocument) -> str:
    PairValue = NativeDocPair(DocValue)
    if PairValue is not None and PairValue[0].data is not None:
        return Hashlib.sha256(PairValue[0].data).hexdigest()
    Values = {
        Value
        for Payload in DocValue.brep_payloads
        if isinstance((Value := Payload.attributes.get(KNativeDocHashAttr)), str)
        and RegexLib.fullmatch("[0-9a-f]{64}", Value) is not None
    }
    return next(iter(Values)) if len(Values) == 1 else ""


# this definition exists because focused behavior needs one stable owner
def XmlElemData(NodeValue: ET.Element) -> dict[str, object]:
    Result: dict[str, object] = {
        "tag": NodeValue.tag,
        "attributes": dict(sorted(NodeValue.attrib.items())),
    }
    TextValue = (NodeValue.text or "").strip()
    if TextValue:
        Result["text"] = TextValue
    Children = [XmlElemData(Child) for Child in NodeValue]
    if Children:
        Result["children"] = Children
    return Result


# this definition exists because focused behavior needs one stable owner
def ArchiveMember(
    Archive: zipfile.ZipFile, Members: Mapping[str, zipfile.ZipInfo], NameValue: str
) -> bytes | None:
    InfoValue = Members.get(NameValue)
    if InfoValue is None or InfoValue.is_dir():
        return None
    try:
        return Archive.read(InfoValue)
    except (OSError, RuntimeError, NotImplementedError, Zipfile.BadZipFile):
        return None


# this definition locates the exact native property represented by a payload
def FindPayloadProp(Payload: BrepPayload, RootValue: ET.Element) -> ET.Element | None:
    Attributes = Payload.attributes
    ObjectName = str(Attributes["freecad_object"])
    ObjectType = str(Attributes["freecad_object_type"])
    PropName = str(Attributes["freecad_property"])
    Declarations = tuple(
        (
            Value
            for Value in RootValue.findall("./Objects/Object")
            if Value.get("name") == ObjectName and Value.get("type") == ObjectType
        )
    )
    Objects = tuple(
        (
            Value
            for Value in RootValue.findall("./ObjectData/Object")
            if Value.get("name") == ObjectName
        )
    )
    if len(Declarations) != 1 or len(Objects) != 1:
        return None
    Properties = tuple(
        (
            Value
            for Value in Objects[0].findall("./Properties/Property")
            if Value.get("name") == PropName
        )
    )
    return Properties[0] if len(Properties) == 1 else None


# this definition verifies every sidecar referenced by a native payload property
def HasSidecars(
    Payload: BrepPayload,
    Archive: zipfile.ZipFile,
    Members: Mapping[str, zipfile.ZipInfo],
    PropElem: ET.Element,
) -> bool:
    Attributes = Payload.attributes
    ReferencedSidecars = tuple(
        (
            NameValue
            for Child in PropElem.findall(".//*[@file]")
            if (NameValue := Child.get("file", ""))
            and NameValue != Payload.source_stream
        )
    )
    Sidecars = Attributes.get("freecad_sidecars", ())
    if not IsPayloadSeq(Sidecars):
        return False
    if len(Sidecars) != len(ReferencedSidecars):
        return False
    for Sidecar, SourceStream in zip(Sidecars, ReferencedSidecars, strict=True):
        if not IsPayloadMap(Sidecar):
            return False
        SidecarData = Sidecar.get("data")
        if (
            Sidecar.get("source_stream") != SourceStream
            or not isinstance(SidecarData, bytes)
            or ArchiveMember(Archive, Members, SourceStream) != SidecarData
        ):
            return False
    return True


# this definition verifies that a payload exactly matches its native archive records
def IsPayloadMatch(
    Payload: BrepPayload,
    Archive: zipfile.ZipFile,
    Members: Mapping[str, zipfile.ZipInfo],
    RootValue: ET.Element,
    NativeDigestText: str,
) -> bool:
    if not IsExactPayload(Payload) or Payload.data is None:
        return False
    if ArchiveMember(Archive, Members, Payload.source_stream) != Payload.data:
        return False
    Attributes = Payload.attributes
    if Attributes[KNativeDocHashAttr] != NativeDigestText:
        return False
    PropElem = FindPayloadProp(Payload, RootValue)
    return (
        PropElem is not None
        and XmlElemData(PropElem) == Attributes["freecad_property_data"]
        and HasSidecars(Payload, Archive, Members, PropElem)
    )


# this definition exists because focused behavior needs one stable owner
def TrustedNative(DocValue: CadDocument) -> frozenset[NativeBrepKey]:
    Trusted: set[NativeBrepKey] = set()
    for ItemValue in DocTree(DocValue):
        NativeSource = UnchangedNative(ItemValue)
        MappedPayloads = ManifestBrep(ItemValue)
        if NativeSource is None or not MappedPayloads:
            continue
        try:
            Archive, Members = ValidatedArchiveMembers(NativeSource)
            RootValue, _ = ValidatedDocXml(Archive, Members)
        except (OSError, TypeError, ValueError, Zipfile.BadZipFile):
            continue
        try:
            NativeDigestText = Hashlib.sha256(NativeSource).hexdigest()
            for Payload, Mapped in zip(
                ItemValue.brep_payloads, MappedPayloads, strict=True
            ):
                if not IsPayloadMatch(
                    Payload, Archive, Members, RootValue, NativeDigestText
                ):
                    continue
                if Payload.data is None:
                    continue
                KeyValue = ManifestNativeBrepKey(Mapped, Payload.data, NativeDigestText)
                if KeyValue is not None:
                    Trusted.add(KeyValue)
        finally:
            Archive.close()
    return frozenset(Trusted)


# this definition exists because focused behavior needs one stable owner
def PayloadNative(
    Payload: BrepPayload,
    MappedPayload: Mapping[str, object] | None = None,
    NativeDigestText: str = "",
    TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset(),
) -> bytes | None:
    if not (
        Payload.role == PayloadRole.BREP
        and Payload.data is not None
        and (Payload.format_id.casefold() in FreecadBrepFormatIds)
    ):
        return None
    if MappedPayload is not None:
        KeyValue = ManifestNativeBrepKey(MappedPayload, Payload.data, NativeDigestText)
        if KeyValue in TrustedNativeBreps:
            return Payload.data
    return ProvenAsciiBrep(Payload.data)


# this definition exists because focused behavior needs one stable owner
def IsBrepPayload(
    Payload: BrepPayload,
    MappedPayload: Mapping[str, object] | None = None,
    NativeDigestText: str = "",
    TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset(),
) -> bool:
    return (
        PayloadNative(Payload, MappedPayload, NativeDigestText, TrustedNativeBreps)
        is not None
    )


# this definition exists because focused behavior needs one stable owner
def IsNeutralBrep(DocValue: CadDocument) -> bool:
    if DocValue.brep is None:
        return False
    try:
        BrepModelBrep(DocValue.brep)
    except FreeCadBrepWriteError:
        return False
    return True


# this definition exists because focused behavior needs one stable owner
def MeshCoord(Value: object) -> float:
    if not isinstance(Value, (int, float)):
        raise TypeError("mesh coordinates must be numeric")
    return float(Value)


# this definition exists because mesh indexing requires exactly three validated integer offsets
def IsMeshTriangle(Value: object) -> TypeGuard[tuple[int, int, int]]:
    match Value:
        case (int(), int(), int()):
            return True
        case _:
            return False


# this definition exists because focused behavior needs one stable owner
def IsMeshUsable(MeshValue: MeshValue) -> bool:
    Points = tuple(
        (
            (
                MeshCoord(Value.XCoord),
                MeshCoord(Value.YCoord),
                MeshCoord(Value.ZCoord),
            )
            for Value in MeshValue.Vertices
        )
    )
    if not Points or any((not all(map(MathValue.isfinite, Point)) for Point in Points)):
        return False
    for Triangle in MeshValue.Triangles:
        if not IsMeshTriangle(Triangle):
            continue
        if len(set(Triangle)) != 3 or any(
            (Index < 0 or Index >= len(Points) for Index in Triangle)
        ):
            continue
        First, Second, Third = (Points[Triangle[Index]] for Index in range(3))
        LeftValue = (
            Second[0] - First[0],
            Second[1] - First[1],
            Second[2] - First[2],
        )
        Right = (
            Third[0] - First[0],
            Third[1] - First[1],
            Third[2] - First[2],
        )
        Cross = (
            LeftValue[1] * Right[2] - LeftValue[2] * Right[1],
            LeftValue[2] * Right[0] - LeftValue[0] * Right[2],
            LeftValue[0] * Right[1] - LeftValue[1] * Right[0],
        )
        if Cross[0] ** 2 + Cross[1] ** 2 + Cross[2] ** 2 > 1e-24:
            return True
    return False


# this definition exists because focused behavior needs one stable owner
def IsNativeGeom(
    DocValue: CadDocument, TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset()
) -> bool:
    Items = [DocValue]
    if DocValue.assembly is not None:
        Documents = {
            ItemValue.id: ItemValue.document
            for ItemValue in DocValue.assembly.documents
        }
        for Definition in DocValue.assembly.definitions:
            if Definition.id == DocValue.assembly.root_definition_id:
                continue
            Component = ComponentDoc(DocValue, Definition, Documents)
            if Component is not None:
                Items.append(Component)
    for ItemValue in Items:
        if ItemValue.assembly is not None:
            continue
        MappedPayloads = ManifestBrep(ItemValue)
        MappedByIdentity = (
            {
                id(Payload): Mapped
                for Payload, Mapped in zip(
                    ItemValue.brep_payloads, MappedPayloads, strict=True
                )
            }
            if MappedPayloads
            else {}
        )
        NativeDigestText = NativeDocShaTwo(ItemValue)
        RawBreps = tuple(
            (
                Payload
                for Payload in ItemValue.brep_payloads
                if Payload.role == PayloadRole.BREP and Payload.data is not None
            )
        )
        if ItemValue.brep is None and (not RawBreps):
            continue
        if ItemValue.brep is not None and IsNeutralBrep(ItemValue):
            continue
        if any(
            (
                IsBrepPayload(
                    Payload,
                    MappedByIdentity.get(id(Payload)),
                    NativeDigestText,
                    TrustedNativeBreps,
                )
                for Payload in RawBreps
            )
        ):
            continue
        if any((IsMeshUsable(MeshValue) for MeshValue in ItemValue.meshes)):
            continue
        if (
            ItemValue.Source.FormatId.casefold() != InfoValue.FormatId.casefold()
            and NativeShapeFeatureCount(DocToManifest(ItemValue)) > 0
        ):
            continue
        return False
    return True


# this definition exists because focused behavior needs one stable owner
def TransferModeA(Parts: Sequence[bool]) -> TransferMode:
    if Parts and all(Parts):
        return TransferMode.NATIVE
    if any(Parts):
        return TransferMode.MIXED
    return TransferMode.CARRIER


# this definition exists because focused behavior needs one stable owner
def CarrierReasonA(
    Capability: Capability, Reasons: Mapping[Capability, set[CarrierReason]]
) -> CarrierReason:
    Values = Reasons[Capability]
    for Reason in (
        CarrierReason.SOURCE_OPAQUE,
        CarrierReason.WRITER_UNIMPLEMENTED,
        CarrierReason.TARGET_UNSUPPORTED,
    ):
        if Reason in Values:
            return Reason
    return CapabilityCarrierReasons[Capability]


# this definition selects the strongest carrier reason for one sketch
def SketchReason(
    ReasonValues: Iterable[str],
) -> tuple[CarrierReason, set[CarrierReason]]:
    Reasons = {CarrierReason(Value) for Value in ReasonValues} or {
        CarrierReason.WRITER_UNIMPLEMENTED
    }
    for Reason in (
        CarrierReason.SOURCE_OPAQUE,
        CarrierReason.WRITER_UNIMPLEMENTED,
        CarrierReason.TARGET_UNSUPPORTED,
    ):
        if Reason in Reasons:
            return (Reason, Reasons)
    return (CarrierReason.WRITER_UNIMPLEMENTED, Reasons)


# this definition records native and carrier sketch transfer parts
def AddSketchMut(
    ItemValue: CadDocument,
    Manifest: Mapping[str, object],
    Parts: dict[Capability, list[bool]],
    CarrierReasons: dict[Capability, set[CarrierReason]],
) -> tuple[dict[str, bool], dict[str, CarrierReason]]:
    SketchNative: dict[str, bool] = {}
    SketchReasons: dict[str, CarrierReason] = {}
    SketchParts = NativeSketchParts(Manifest)
    ReasonParts = NativeSketchCarrier(Manifest)
    for SketchValue, Counts, ReasonValues in zip(
        ItemValue.sketches, SketchParts, ReasonParts, strict=True
    ):
        NativeCount, CarrierCount = Counts
        Parts[Capability.EDITABLE_SKETCHES].extend(
            [True] * NativeCount + [False] * CarrierCount
        )
        if CarrierCount:
            PrimaryReason, Reasons = SketchReason(ReasonValues)
            SketchReasons[SketchValue.id] = PrimaryReason
            CarrierReasons[Capability.EDITABLE_SKETCHES].update(Reasons)
        SketchNative[SketchValue.id] = CarrierCount == 0
    return (SketchNative, SketchReasons)


# this definition records feature selection configuration and expression transfer parts
def AddBasicMut(
    ItemValue: CadDocument,
    Manifest: Mapping[str, object],
    SourceNative: bool,
    SketchNative: Mapping[str, bool],
    SketchReasons: Mapping[str, CarrierReason],
    Parts: dict[Capability, list[bool]],
    CarrierReasons: dict[Capability, set[CarrierReason]],
) -> None:
    Parts[Capability.PARAMETERS].extend(True for _ in ItemValue.parameters)
    NativeCount, CarrierCount, Reasons = FeatureParts(
        ItemValue, SketchNative, SketchReasons
    )
    Parts[Capability.PARAMETRIC_HISTORY].extend(
        [True] * NativeCount + [False] * CarrierCount
    )
    CarrierReasons[Capability.PARAMETRIC_HISTORY].update(Reasons)
    Parts[Capability.SUPPORT_PLANES].extend(True for _ in ItemValue.support_planes)
    SelectionCounts = (
        (len(ItemValue.selections), 0) if SourceNative else SelectionParts(ItemValue)
    )
    Parts[Capability.SELECTIONS].extend(
        [True] * SelectionCounts[0] + [False] * SelectionCounts[1]
    )
    Parts[Capability.BODY_STRUCTURE].extend(True for _ in ItemValue.bodies)
    ConfigCounts = ConfigParts(ItemValue)
    Parts[Capability.CONFIGURATIONS].extend(
        [True] * ConfigCounts[0] + [False] * ConfigCounts[1]
    )
    ExpressionCounts = (
        (sum(Param.expression is not None for Param in ItemValue.parameters), 0)
        if SourceNative
        else NativeExpressionParts(Manifest)
    )
    Parts[Capability.EXPRESSIONS].extend(
        [True] * ExpressionCounts[0] + [False] * ExpressionCounts[1]
    )


# this definition records geometric and tessellation transfer parts
def AddGeomMut(
    ItemValue: CadDocument,
    Manifest: Mapping[str, object],
    MappedByIdentity: Mapping[int, Mapping[str, object]],
    NativeDigestText: str,
    TrustedNativeBreps: frozenset[NativeBrepKey],
    Parts: dict[Capability, list[bool]],
    CarrierReasons: dict[Capability, set[CarrierReason]],
) -> None:
    RawBreps = [
        IsBrepPayload(
            Payload,
            MappedByIdentity.get(id(Payload)),
            NativeDigestText,
            TrustedNativeBreps,
        )
        for Payload in ItemValue.brep_payloads
        if Payload.role == PayloadRole.BREP and Payload.data is not None
    ]
    if ItemValue.brep is not None:
        NativeBrep = IsNeutralBrep(ItemValue) or any(RawBreps)
        Parts[Capability.BREP].append(NativeBrep)
        if not NativeBrep:
            CarrierReasons[Capability.BREP].add(CarrierReason.WRITER_UNIMPLEMENTED)
    else:
        Parts[Capability.BREP].extend(RawBreps)
        if any(not Value for Value in RawBreps):
            CarrierReasons[Capability.BREP].add(CarrierReason.SOURCE_OPAQUE)
    RebuiltCount = (
        NativeShapeFeatureCount(Manifest)
        if ItemValue.Source.FormatId.casefold() != InfoValue.FormatId.casefold()
        else 0
    )
    if RebuiltCount and not all(Parts[Capability.BREP]):
        Parts[Capability.BREP].extend(True for _ in range(RebuiltCount))
    Parts[Capability.TESSELLATION].extend(True for _ in ItemValue.meshes)
    Parts[Capability.TESSELLATION].extend(
        False
        for Payload in ItemValue.brep_payloads
        if Payload.role == PayloadRole.TESSELLATION and Payload.data is not None
    )


# this definition records assembly material and external reference transfer parts
def AddRefsMut(
    ItemValue: CadDocument,
    TargetPath: FilePath | None,
    Portable: bool,
    Parts: dict[Capability, list[bool]],
) -> None:
    if ItemValue.assembly is not None:
        Parts[Capability.ASSEMBLIES].append(True)
        NativeCount, CarrierCount = MateParts(ItemValue)
        Parts[Capability.ASSEMBLY_MATES].extend(
            [True] * NativeCount + [False] * CarrierCount
        )
        NativeDocuments = TargetPath is not None
        Parts[Capability.COMPONENT_DOCUMENTS].extend(
            NativeDocuments for _ in ItemValue.assembly.documents
        )
        CanWriteOuter = TargetPath is not None and Portable
        Parts[Capability.EXTERNAL_REFERENCES].extend(
            CanWriteOuter
            for Definition in ItemValue.assembly.definitions
            if Definition.source_path
        )
    Parts[Capability.EXTERNAL_REFERENCES].extend(
        TargetPath is not None and Portable for _ in NativeOuter(ItemValue)
    )
    Parts[Capability.MATERIALS].extend(
        True for BodyValue in ItemValue.bodies if BodyValue.material_id
    )


# this definition records native payload transfer parts and carrier reasons
def AddPayloadMut(
    ItemValue: CadDocument,
    MappedByIdentity: Mapping[int, Mapping[str, object]],
    NativeDigestText: str,
    TrustedNativeBreps: frozenset[NativeBrepKey],
    Parts: dict[Capability, list[bool]],
    CarrierReasons: dict[Capability, set[CarrierReason]],
) -> None:
    EnvelopeIndexes = SourcePayloadIndexes(ItemValue)
    for Index, Payload in enumerate(ItemValue.brep_payloads):
        if Index in EnvelopeIndexes:
            continue
        NativePayload = PayloadNative(
            Payload,
            MappedByIdentity.get(id(Payload)),
            NativeDigestText,
            TrustedNativeBreps,
        )
        if NativePayload is not None:
            Parts[Capability.NATIVE_PAYLOADS].append(True)
            if NativePayload != Payload.data:
                Parts[Capability.NATIVE_PAYLOADS].append(False)
                CarrierReasons[Capability.NATIVE_PAYLOADS].add(
                    CarrierReason.WRITER_UNIMPLEMENTED
                )
            continue
        Parts[Capability.NATIVE_PAYLOADS].append(False)
        Reason = (
            CarrierReason.TARGET_UNSUPPORTED
            if Payload.role == PayloadRole.BREP and ItemValue.brep is not None
            else CarrierReason.SOURCE_OPAQUE
        )
        CarrierReasons[Capability.NATIVE_PAYLOADS].add(Reason)


# this definition records provenance values that require carrier preservation
def AddProvMut(ItemValue: CadDocument, Parts: dict[Capability, list[bool]]) -> None:
    Values = (
        *ItemValue.parameters,
        *ItemValue.support_planes,
        *ItemValue.sketches,
        *ItemValue.selections,
        *ItemValue.feature_timeline,
        *ItemValue.bodies,
        *ItemValue.meshes,
        *ItemValue.brep_payloads,
    )
    Parts[Capability.PROVENANCE].extend(
        False for Value in Values if getattr(Value, "provenance", None) is not None
    )


# this definition adds every capability contribution from one document
def AddDocPartsMut(
    ItemValue: CadDocument,
    TargetPath: FilePath | None,
    Portable: bool,
    TrustedNativeBreps: frozenset[NativeBrepKey],
    Parts: dict[Capability, list[bool]],
    CarrierReasons: dict[Capability, set[CarrierReason]],
) -> None:
    SourceNative = HasNativeGraph(ItemValue)
    Manifest = DocToManifest(ItemValue)
    MappedPayloads = ManifestBrep(ItemValue)
    MappedByIdentity = (
        {
            id(Payload): Mapped
            for Payload, Mapped in zip(
                ItemValue.brep_payloads, MappedPayloads, strict=True
            )
        }
        if MappedPayloads
        else {}
    )
    NativeDigestText = NativeDocShaTwo(ItemValue)
    SketchNative, SketchReasons = AddSketchMut(
        ItemValue, Manifest, Parts, CarrierReasons
    )
    AddBasicMut(
        ItemValue,
        Manifest,
        SourceNative,
        SketchNative,
        SketchReasons,
        Parts,
        CarrierReasons,
    )
    AddGeomMut(
        ItemValue,
        Manifest,
        MappedByIdentity,
        NativeDigestText,
        TrustedNativeBreps,
        Parts,
        CarrierReasons,
    )
    AddRefsMut(ItemValue, TargetPath, Portable, Parts)
    AddPayloadMut(
        ItemValue,
        MappedByIdentity,
        NativeDigestText,
        TrustedNativeBreps,
        Parts,
        CarrierReasons,
    )
    AddProvMut(ItemValue, Parts)


# this definition provides stable capability ordering without inline callbacks
def CapabilityKey(Value: Capability) -> str:
    return Value.value


# this definition computes the capability transfer contract for a freecad write
def CapabilityA(
    DocValue: CadDocument,
    TargetPath: FilePath | None,
    Portable: bool,
    Exact: bool,
    TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset(),
) -> tuple[CapabilityTransfer, ...]:
    Required = DocValue.capabilities | InferCapabilities(
        DocValue,
        roundtrip_metadata=Capability.ROUNDTRIP_METADATA in DocValue.capabilities,
    )
    if Exact:
        return tuple(
            CapabilityTransfer(CapabilityValue, TransferMode.NATIVE)
            for CapabilityValue in sorted(Required, key=CapabilityKey)
        )
    Parts: dict[Capability, list[bool]] = {
        CapabilityValue: [] for CapabilityValue in Capability
    }
    CarrierReasons: dict[Capability, set[CarrierReason]] = {
        CapabilityValue: set() for CapabilityValue in Capability
    }
    for ItemValue in DocTree(DocValue):
        AddDocPartsMut(
            ItemValue, TargetPath, Portable, TrustedNativeBreps, Parts, CarrierReasons
        )
    Parts[Capability.ROUNDTRIP_METADATA].append(False)
    return tuple(
        CapabilityTransfer(
            CapabilityValue,
            (ModeValue := TransferModeA(Parts[CapabilityValue])),
            (
                None
                if ModeValue is TransferMode.NATIVE
                else CarrierReasonA(CapabilityValue, CarrierReasons)
            ),
        )
        for CapabilityValue in sorted(Required, key=CapabilityKey)
    )


# this definition exists because focused behavior needs one stable owner
def WriteBytes(
    Target: Destination, DataValue: bytes, Overwrite: bool
) -> FilePath | None:
    PathValue = ResolveTarget(Target)
    if PathValue is None:
        Writer = getattr(Target, "write", None)
        if not callable(Writer):
            raise TypeError("destination must be a path or binary stream")
        try:
            Written = Writer(DataValue)
        except TypeError as ErrorInfo:
            raise TypeError(
                "FCStd destination must be opened in binary mode"
            ) from ErrorInfo
        if Written is not None and Written != len(DataValue):
            raise OSError(
                f"short FCStd write: expected {len(DataValue)} bytes, wrote {Written}"
            )
        return None
    if PathValue.suffix.casefold() != Suffix.casefold():
        raise ValueError(f"FreeCAD destination must end in {Suffix}")
    if PathValue.exists() and (not Overwrite):
        raise FileExistsError(PathValue)
    PathValue.parent.mkdir(parents=True, exist_ok=True)
    Descriptor, TemporaryName = Tempfile.mkstemp(
        prefix=PathValue.name + ".", suffix=".tmp", dir=PathValue.parent
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


# this definition exists because focused behavior needs one stable owner
def ComponentStem(Value: str) -> str:
    StemValue = RegexLib.sub('[<>:"/\\\\|?*\\x00-\\x1f]', "_", Value).strip(" .")
    StemValue = StemValue or "Component"
    if IsWindowsDeviceName(StemValue):
        StemValue = f"_{StemValue}"
    return StemValue[:120].rstrip(" .") or "Component"


# this definition exists because focused behavior needs one stable owner
def ComponentPaths(DocValue: CadDocument, Target: FilePath) -> dict[str, FilePath]:
    AsmValue = DocValue.assembly
    if AsmValue is None:
        return {}
    Documents = {ItemValue.id for ItemValue in AsmValue.documents}
    Folder = Target.parent / Target.stem
    UsedValue: set[str] = set()
    Result: dict[str, FilePath] = {}
    for Definition in AsmValue.definitions:
        if Definition.id == AsmValue.root_definition_id:
            continue
        if Definition.document_id not in Documents and (not Definition.mesh_ids):
            continue
        BaseValue = ComponentStem(Definition.name or Definition.id)
        Choice = BaseValue
        DuplicateIndex = 1
        while Choice.casefold() in UsedValue:
            DuplicateIndex += 1
            Ending = f"_{DuplicateIndex}"
            Choice = BaseValue[: 120 - len(Ending)].rstrip(" .") + Ending
        UsedValue.add(Choice.casefold())
        Result[Definition.id] = Folder / f"{Choice}{Suffix}"
    return Result


# this definition exists because focused behavior needs one stable owner
def ChooseMeshes(
    DocValue: CadDocument, Definition: ComponentDefinition
) -> tuple[MeshValue, ...]:
    Meshes = {ItemValue.id: ItemValue for ItemValue in DocValue.meshes}
    Missing = [MeshId for MeshId in Definition.mesh_ids if MeshId not in Meshes]
    if Missing:
        raise FreeCadAdapterA(
            f"component definition {Definition.id!r} references missing meshes: "
            + ", ".join(Missing)
        )
    return tuple((Meshes[MeshId] for MeshId in Definition.mesh_ids))


# this definition exists because focused behavior needs one stable owner
def MeshComponent(
    DocValue: CadDocument, Definition: ComponentDefinition, Meshes: tuple[Mesh, ...]
) -> CadDoc:
    Source = CadSource(
        format_id=Definition.source_format_id or DocValue.source.format_id,
        path=Definition.source_path or Definition.name or Definition.id,
        sha256=Definition.source_sha256,
        container_version=DocValue.source.container_version,
        application_version=DocValue.source.application_version,
        attributes=Definition.attributes,
    )
    ConfigName = Definition.configuration_name or "Default"
    ConfigId = Definition.configuration_id or f"{Definition.id}:configuration:default"
    return CadDoc(
        source=Source,
        configurations=(Config(ConfigId, ConfigName, active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        meshes=Meshes,
        capabilities=frozenset({Capability.TESSELLATION}),
        units=DocValue.units,
        schema_version=DocValue.schema_version,
    )


# this definition exists because focused behavior needs one stable owner
def ComponentDoc(
    DocValue: CadDocument,
    Definition: ComponentDefinition,
    Documents: Mapping[str, CadDocument],
) -> CadDoc | None:
    SelectedMeshes = ChooseMeshes(DocValue, Definition)
    Linked = Documents.get(Definition.document_id)
    if Linked is None:
        return (
            MeshComponent(DocValue, Definition, SelectedMeshes)
            if SelectedMeshes
            else None
        )
    SelectedIds = {MeshValue.id for MeshValue in SelectedMeshes}
    Meshes = (
        *SelectedMeshes,
        *(MeshValue for MeshValue in Linked.meshes if MeshValue.id not in SelectedIds),
    )
    Capabilities = Linked.capabilities
    if Meshes:
        Capabilities = Capabilities | {Capability.TESSELLATION}
    return Replace(Linked, meshes=Meshes, capabilities=Capabilities)


# this definition exists because focused behavior needs one stable owner
def XmlString(NodeValue: ET.Element, NameValue: str, Default: str = "") -> str:
    Value = NodeValue.find(f"./Properties/Property[@name='{NameValue}']/String")
    return Default if Value is None else Value.get("value", Default)


# this definition exists because focused behavior needs one stable owner
def IsXmlBool(NodeValue: ET.Element, NameValue: str, Default: bool = False) -> bool:
    Value = NodeValue.find(f"./Properties/Property[@name='{NameValue}']/Bool")
    if Value is None:
        return Default
    return Value.get("value", "false").casefold() in XmlTrueValues


# this definition exists because focused behavior needs one stable owner
def XmlStringList(NodeValue: ET.Element, NameValue: str) -> list[str]:
    return [
        Value.get("value", "")
        for Value in NodeValue.findall(
            f"./Properties/Property[@name='{NameValue}']/StringList/String"
        )
    ]


# this definition exists because focused behavior needs one stable owner
def XmlLinkList(NodeValue: ET.Element, NameValue: str) -> list[str]:
    return [
        Value.get("value", "")
        for Value in NodeValue.findall(
            f"./Properties/Property[@name='{NameValue}']/LinkList/Link"
        )
    ]


# this definition exists because focused behavior needs one stable owner
def XmlNumber(Value: str | None, Default: float) -> float:
    if Value is None:
        return Default
    try:
        return float(Value)
    except (TypeError, ValueError):
        return Default


# this definition exists because focused behavior needs one stable owner
def XmlTransform(NodeValue: ET.Element) -> list[float]:
    Value = NodeValue.find("./Properties/Property[@name='Placement']/PropertyPlacement")
    if Value is None:
        return [
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
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ]
    FirstCoord = XmlNumber(Value.get("Q0"), 0.0)
    SecondCoord = XmlNumber(Value.get("Q1"), 0.0)
    ThirdCoord = XmlNumber(Value.get("Q2"), 0.0)
    WidthValue = XmlNumber(Value.get("Q3"), 1.0)
    NormValue = (
        FirstCoord * FirstCoord
        + SecondCoord * SecondCoord
        + ThirdCoord * ThirdCoord
        + WidthValue * WidthValue
    ) ** 0.5
    if NormValue <= 1e-15:
        FirstCoord, SecondCoord, ThirdCoord, WidthValue = (0.0, 0.0, 0.0, 1.0)
    else:
        FirstCoord, SecondCoord, ThirdCoord, WidthValue = (
            FirstCoord / NormValue,
            SecondCoord / NormValue,
            ThirdCoord / NormValue,
            WidthValue / NormValue,
        )
    XxValue, YyValue, ZzValue = (
        FirstCoord * FirstCoord,
        SecondCoord * SecondCoord,
        ThirdCoord * ThirdCoord,
    )
    XyValue, XzValue, YzValue = (
        FirstCoord * SecondCoord,
        FirstCoord * ThirdCoord,
        SecondCoord * ThirdCoord,
    )
    XwValue, YwValue, ZwValue = (
        FirstCoord * WidthValue,
        SecondCoord * WidthValue,
        ThirdCoord * WidthValue,
    )
    return [
        1.0 - 2.0 * (YyValue + ZzValue),
        2.0 * (XyValue - ZwValue),
        2.0 * (XzValue + YwValue),
        XmlNumber(Value.get("Px"), 0.0),
        2.0 * (XyValue + ZwValue),
        1.0 - 2.0 * (XxValue + ZzValue),
        2.0 * (YzValue - XwValue),
        XmlNumber(Value.get("Py"), 0.0),
        2.0 * (XzValue - YwValue),
        2.0 * (YzValue + XwValue),
        1.0 - 2.0 * (XxValue + YyValue),
        XmlNumber(Value.get("Pz"), 0.0),
        0.0,
        0.0,
        0.0,
        1.0,
    ]


# this definition exists because focused behavior needs one stable owner
def XmlScale(NodeValue: ET.Element) -> list[float]:
    Value = NodeValue.find("./Properties/Property[@name='ScaleVector']/PropertyVector")
    if Value is None:
        return [1.0, 1.0, 1.0]
    return [
        XmlNumber(Value.get("valueX"), 1.0),
        XmlNumber(Value.get("valueY"), 1.0),
        XmlNumber(Value.get("valueZ"), 1.0),
    ]


# this definition exists because focused behavior needs one stable owner
def OuterLink(DataValue: bytes) -> tuple[str, list[dict[str, object]]]:
    with Zipfile.ZipFile(IoStream.BytesIO(DataValue)) as Archive:
        RootValue = XmlTree.fromstring(Archive.read(DocEntry))
    Value = RootValue.find(
        "./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='ExternalLinkTarget']/String"
    )
    Target = "" if Value is None else Value.get("value", "")
    if not Target:
        raise FreeCadAdapterA("component FCStd has no external link target")
    Types = {
        ItemValue.get("name", ""): ItemValue.get("type", "")
        for ItemValue in RootValue.findall("./Objects/Object")
    }
    Objects = {
        ItemValue.get("name", ""): ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
    }

    # this definition exists because focused behavior needs one stable owner
    def ItemAction(NameValue: str, Active: frozenset[str]) -> dict[str, object] | None:
        NodeValue = Objects.get(NameValue)
        TypeId = Types.get(NameValue, "")
        if (
            NodeValue is None
            or NameValue in Active
            or NodeValue.find("./Properties/Property[@name='LinkedObject']/XLink")
            is None
        ):
            return None
        InstanceId = XmlString(NodeValue, "InstanceId")
        if not InstanceId:
            return None
        LinkFields = tuple(
            sorted(
                (
                    PropElem.get("name", "")
                    for PropElem in NodeValue.findall("./Properties/Property")
                    if PropElem.get("name", "")
                )
            )
        )
        RawInstanceData = XmlString(NodeValue, "InstanceDataJSON")
        InstanceData: object = {}
        if RawInstanceData:
            try:
                InstanceData = JsonValue.loads(RawInstanceData)
            except JsonValue.JSONDecodeError:
                InstanceData = {}
        Children = [
            Child
            for ChildName in XmlLinkList(NodeValue, "Group")
            if (Child := ItemAction(ChildName, Active | {NameValue})) is not None
        ]
        return {
            "target": NameValue,
            "type_id": TypeId,
            "link_fields": LinkFields,
            "label": XmlString(NodeValue, "Label", NameValue),
            "instance_id": InstanceId,
            "definition_id": XmlString(NodeValue, "DefinitionId"),
            "owner_definition_id": XmlString(NodeValue, "OwnerDefinitionId"),
            "instance_path": XmlStringList(NodeValue, "InstancePath"),
            "reference_number": XmlString(NodeValue, "ReferenceNumber"),
            "configuration_name": XmlString(NodeValue, "ConfigurationName"),
            "configuration_id": XmlString(NodeValue, "ConfigurationId"),
            "suppressed": IsXmlBool(NodeValue, "Suppressed"),
            "hidden": IsXmlBool(NodeValue, "Hidden"),
            "fixed": IsXmlBool(NodeValue, "Fixed"),
            "flexible": IsXmlBool(NodeValue, "Flexible"),
            "exclude_from_bom": IsXmlBool(NodeValue, "ExcludeFromBOM"),
            "visibility": IsXmlBool(NodeValue, "Visibility", True),
            "rigid": IsXmlBool(NodeValue, "Rigid", True),
            "transform": XmlTransform(NodeValue),
            "scale": XmlScale(NodeValue),
            "instance_data": InstanceData,
            "occurrences": Children,
        }

    TargetNode = Objects.get(Target)
    Occurrences = (
        [
            ItemValue
            for ChildName in XmlLinkList(TargetNode, "Group")
            if (ItemValue := ItemAction(ChildName, frozenset())) is not None
        ]
        if TargetNode is not None
        else []
    )
    return (Target, Occurrences)


# this definition exists because focused behavior needs one stable owner
def OuterLinkTarget(DataValue: bytes) -> str:
    return OuterLink(DataValue)[0]


# this definition exists because focused behavior needs one stable owner
def ParsedTimestamp(Value: str) -> float | None:
    try:
        Parsed = Datetime.strptime(Value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=Timezone.utc
        )
    except ValueError:
        return None
    return Parsed.timestamp()


# this definition exists because focused behavior needs one stable owner
def FileTimestamps(PathValue: FilePath) -> tuple[float, ...]:
    Values: list[float] = []
    try:
        Values.append(PathValue.stat().st_mtime)
    except OSError:
        return ()
    try:
        with Zipfile.ZipFile(PathValue) as Archive:
            RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    except (OSError, KeyError, XmlTree.ParseError, Zipfile.BadZipFile):
        return tuple(Values)
    for PropName in ("CreationDate", "LastModifiedDate"):
        ElemValue = RootValue.find(f"./Properties/Property[@name='{PropName}']/String")
        Parsed = ParsedTimestamp(
            "" if ElemValue is None else ElemValue.get("value", "")
        )
        if Parsed is not None:
            Values.append(Parsed)
    for ElemValue in RootValue.findall(".//XLink"):
        Parsed = ParsedTimestamp(ElemValue.get("stamp", ""))
        if Parsed is not None:
            Values.append(Parsed)
    return tuple(Values)


# this definition exists because focused behavior needs one stable owner
def BundleTimestamp(Target: Path) -> tuple[str, float]:
    NowValue = Datetime.now(Timezone.utc).replace(microsecond=0).timestamp()
    Files = [Target]
    Folder = Target.parent / Target.stem
    if Folder.is_dir():
        try:
            ComponentFiles = tuple(
                (
                    PathValue
                    for PathValue in Folder.iterdir()
                    if PathValue.is_file()
                    and PathValue.suffix.casefold() == Suffix.casefold()
                )
            )
        except OSError:
            ComponentFiles = ()
        Files.extend(ComponentFiles)
    Existing = [
        Timestamp for PathValue in Files for Timestamp in FileTimestamps(PathValue)
    ]
    Epoch = int(NowValue)
    if Existing:
        Epoch = max(Epoch, int(max(Existing)) + 1)
    Modified = Datetime.fromtimestamp(Epoch, Timezone.utc)
    return (Modified.strftime("%Y-%m-%dT%H:%M:%SZ"), float(Epoch))


# this definition exists because focused behavior needs one stable owner
def SourceKeys(
    Definition: ComponentDefinition, Documents: Mapping[str, CadDocument]
) -> frozenset[tuple[str, str, str]]:
    Config = Definition.configuration_id or Definition.configuration_name
    Scope = f"{EnumText(Definition.kind)}:{Config}"
    Values: set[tuple[str, str, str]] = set()

    # this definition exists because focused behavior needs one stable owner
    def AddAction(ShaTwoFiveSix: str, PathValue: str) -> None:
        if ShaTwoFiveSix:
            Values.add(("sha256", ShaTwoFiveSix.casefold(), Scope))
        if PathValue:
            Normalized = OsModule.path.normpath(PathValue).replace("\\", "/").casefold()
            Segments = [Value for Value in Normalized.split("/") if Value]
            Values.add(("path", Normalized, Scope))
            Values.add(("path-tail", "/".join(Segments[-2:]), Scope))

    AddAction(Definition.source_sha256, Definition.source_path)
    if Definition.name:
        Values.add(("name", Definition.name.casefold(), Scope))
    Linked = Documents.get(Definition.document_id)
    if Linked is not None:
        AddAction(Linked.source.sha256, Linked.source.path)
    return frozenset(Values)


# this definition exists because focused behavior needs one stable owner
def MatchLink(
    Definition: ComponentDefinition,
    Documents: Mapping[str, CadDocument],
    RootDefinitions: Mapping[str, ComponentDefinition],
    RootDocuments: Mapping[str, CadDocument],
    Links: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object] | None:
    Sources = SourceKeys(Definition, Documents)
    if not Sources:
        return None
    Matches = [
        LinkValue
        for DefinitionId, LinkValue in Links.items()
        if Sources & SourceKeys(RootDefinitions[DefinitionId], RootDocuments)
    ]
    Identities = {
        (
            str(LinkValue.get("path", "")),
            str(LinkValue.get("target", "")),
            str(LinkValue.get("stamp", "")),
        )
        for LinkValue in Matches
    }
    return Matches[0] if len(Identities) == 1 else None


# this definition exists because focused behavior needs one stable owner
def OuterLinkMap(
    Component: CadDocument,
    ComponentPath: FilePath,
    RootDefinitions: Mapping[str, ComponentDefinition],
    RootDocuments: Mapping[str, CadDocument],
    Links: Mapping[str, Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    AsmValue = Component.assembly
    if AsmValue is None:
        return {}
    Documents = {ItemValue.id: ItemValue.document for ItemValue in AsmValue.documents}
    Result: dict[str, dict[str, object]] = {}
    for Definition in AsmValue.definitions:
        if Definition.id == AsmValue.root_definition_id:
            continue
        LinkValue = MatchLink(
            Definition, Documents, RootDefinitions, RootDocuments, Links
        )
        if LinkValue is None:
            continue
        RawPath = LinkValue.get("path")
        if not isinstance(RawPath, (str, FilePath)):
            continue
        PathValue = FilePath(RawPath)
        RawOccurrences = LinkValue.get("occurrences")
        Occurrences = list(RawOccurrences) if IsPayloadSeq(RawOccurrences) else []
        Result[Definition.id] = {
            "file": FilePath(
                OsModule.path.relpath(PathValue, ComponentPath.parent)
            ).as_posix(),
            "stamp": str(LinkValue.get("stamp", "")),
            "target": str(LinkValue.get("target", "")),
            "occurrences": Occurrences,
        }
    return Result


# this definition orders part documents before dependent assembly documents
def IsAssemblyPlan(
    ItemValue: tuple[str, FilePath, ComponentDefinition, CadDoc],
) -> bool:
    return ItemValue[2].kind == ComponentKind.ASSEMBLY


# this definition resolves writable component documents and their target paths
def ComponentPlans(
    DocValue: CadDocument, Paths: Mapping[str, FilePath]
) -> list[tuple[str, FilePath, ComponentDefinition, CadDoc]]:
    AsmValue = DocValue.assembly
    if AsmValue is None:
        return []
    Documents = {ItemValue.id: ItemValue.document for ItemValue in AsmValue.documents}
    Definitions = {ItemValue.id: ItemValue for ItemValue in AsmValue.definitions}
    Plans: list[tuple[str, FilePath, ComponentDefinition, CadDoc]] = []
    for DefinitionId, PathValue in Paths.items():
        Definition = Definitions[DefinitionId]
        Component = ComponentDoc(DocValue, Definition, Documents)
        if Component is not None:
            Plans.append((DefinitionId, PathValue, Definition, Component))
    Plans.sort(key=IsAssemblyPlan)
    return Plans


# this definition writes component documents and returns their native link manifest
def WriteComponents(
    DocValue: CadDocument,
    Target: FilePath,
    Overwrite: bool,
    Validate: bool,
    DocTimestamp: str,
    TimestampEpoch: float,
    TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset(),
) -> tuple[dict[str, dict[str, object]], int]:
    Paths = ComponentPaths(DocValue, Target)
    if not Overwrite:
        Existing = next(
            (PathValue for PathValue in Paths.values() if PathValue.exists()), None
        )
        if Existing is not None:
            raise FileExistsError(Existing)
    Plans = ComponentPlans(DocValue, Paths)
    Definitions = (
        {ItemValue.id: ItemValue for ItemValue in DocValue.assembly.definitions}
        if DocValue.assembly is not None
        else {}
    )
    Documents = (
        {ItemValue.id: ItemValue.document for ItemValue in DocValue.assembly.documents}
        if DocValue.assembly is not None
        else {}
    )
    ComponentLinks: dict[str, dict[str, object]] = {}
    OuterLinks: dict[str, dict[str, object]] = {}
    BytesWritten = 0
    for DefinitionId, PathValue, Definition, Component in Plans:
        if Validate:
            Component.assert_valid()
        NestedLinks = (
            OuterLinkMap(Component, PathValue, Definitions, Documents, ComponentLinks)
            if Definition.kind == ComponentKind.ASSEMBLY
            else {}
        )
        DataValue = BuildFcstdArchive(
            DocToManifest(Component),
            external_links=NestedLinks,
            document_timestamp=DocTimestamp,
            trusted_native_breps=TrustedNativeBreps,
        )
        TargetA, Occurrences = OuterLink(DataValue)
        WriteBytes(PathValue, DataValue, Overwrite)
        OsModule.utime(PathValue, (TimestampEpoch, TimestampEpoch))
        ComponentLinks[DefinitionId] = {
            "path": PathValue,
            "stamp": DocTimestamp,
            "target": TargetA,
            "occurrences": Occurrences,
        }
        OuterLinks[DefinitionId] = {
            "file": PathValue.relative_to(Target.parent).as_posix(),
            "stamp": DocTimestamp,
            "target": TargetA,
            "occurrences": Occurrences,
        }
        BytesWritten += len(DataValue)
    return (OuterLinks, BytesWritten)


# this definition exists because focused behavior needs one stable owner
def NativePayloadSize(DocValue: CadDoc) -> int:
    Total = 0
    for Payload in DocValue.BrepPayloads:
        DataValue = Payload.PayloadData
        if Payload.ValueRole == PayloadRole.DOCUMENT and DataValue is not None:
            Total += len(DataValue)
    return Total


# this definition exists because focused behavior needs one stable owner
def NativeOuter(DocValue: CadDocument) -> list[tuple[str, CadDoc]]:
    MetaValue = DocValue.metadata
    FreecadValue: object = MetaValue.get("freecad")
    Freecad: Mapping[str, object] = FreecadValue if IsPayloadMap(FreecadValue) else {}
    Values: object = Freecad.get("external_documents")
    if Values is None:
        Values = []
    if not IsPayloadSeq(Values):
        raise FreeCadAdapterA("native FreeCAD external document metadata is invalid")
    Result: list[tuple[str, CadDoc]] = []
    SeenValue: set[str] = set()
    Total = 0
    for Value in Values:
        if not IsPayloadMap(Value):
            raise FreeCadAdapterA(
                "native FreeCAD external document metadata is invalid"
            )
        SourceFile = str(Value.get("file", ""))
        Linked: object = Value.get("document")
        if IsPayloadMap(Linked):
            try:
                Linked = CadDoc.from_dict(ValidateWireMap(Linked))
            except (TypeError, ValueError, RecursionError) as ErrorInfo:
                raise FreeCadAdapterA(
                    "native FreeCAD external document metadata is invalid"
                ) from ErrorInfo
        if not SourceFile or not isinstance(Linked, CadDoc):
            raise FreeCadAdapterA(
                "native FreeCAD external document metadata is invalid"
            )
        if SourceFile in SeenValue:
            raise FreeCadAdapterA(
                "native FreeCAD external document metadata contains duplicates"
            )
        SeenValue.add(SourceFile)
        Total += NativePayloadSize(Linked)
        if len(Result) >= MaxOuterFiles or Total > MaxTotalSize:
            raise FreeCadAdapterA(
                "native FreeCAD external documents exceed safe limits"
            )
        Result.append((SourceFile, Linked))
    return Result


# this definition exists because focused behavior needs one stable owner
def WriteNative(
    DocValue: CadDocument, Target: FilePath, Overwrite: bool, Validate: bool
) -> tuple[dict[str, str], int]:
    Records = NativeOuter(DocValue)
    Folder = Target.parent / Target.stem
    UsedValue: set[str] = set()
    Links: dict[str, str] = {}
    BytesWritten = 0
    for SourceFile, Linked in Records:
        SourceName = FilePath(SourceFile).name
        FileSuffix = FilePath(SourceName).suffix or Suffix
        BaseValue = ComponentStem(FilePath(SourceName).stem)
        Choice = BaseValue
        Index = 1
        while (Choice + FileSuffix).casefold() in UsedValue:
            Index += 1
            Ending = f"_{Index}"
            Choice = BaseValue[: 120 - len(Ending)].rstrip(" .") + Ending
        FileName = Choice + FileSuffix
        UsedValue.add(FileName.casefold())
        Output = Folder / FileName
        Result = FreeCadAdapter().write(
            Linked,
            Output,
            WriteOptions(
                Overwrite=Overwrite,
                Validate=Validate,
                OptionValues={"portable": True},
            ),
        )
        if Result.ByteCount > MaxEntrySize:
            raise FreeCadAdapterA(
                "native FreeCAD external document exceeds safe limits"
            )
        BytesWritten += Result.ByteCount
        if BytesWritten > MaxTotalSize:
            raise FreeCadAdapterA(
                "native FreeCAD external documents exceed safe limits"
            )
        Links[SourceFile] = Output.relative_to(Target.parent).as_posix()
    return (Links, BytesWritten)


# this definition exists because focused behavior needs one stable owner
def ManifestDoc(Value: Mapping[str, object]) -> CadDoc:
    try:
        return CadDoc.from_dict(ValidateWireMap(Value))
    except (TypeError, ValueError, RecursionError) as ErrorInfo:
        raise FreeCadAdapterA(
            "embedded neutral document cannot be restored"
        ) from ErrorInfo


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
        raise FreeCadAdapterA(f"configuration {Selected!r} is unavailable")
    return tuple(
        (
            Replace(ConfigValue, active=ConfigValue.id in Matches)
            for ConfigValue in Configurations
        )
    )


# this definition probes embedded and native freecad archives without vendor runtime
def ProbeSource(Instance: FreeCadAdapter, Source: Source) -> ProbeResult:
    try:
        DataValue = SourceBytes(Source)
        Archive, Members = ValidatedArchiveMembers(DataValue)
        Archive.close()
        if ManifestEntry in Members:
            try:
                ManifestDoc(ExtractManifestFromFcstd(DataValue))
            except (ValueError, FreeCadAdapterA) as ErrorInfo:
                return ProbeResult(Instance.info.FormatId, 0.0, str(ErrorInfo))
            return ProbeResult(Instance.info.FormatId, 1.0, "Kit FCStd archive")
        if "Document.xml" in Members:
            try:
                Value = ExtractManifestFromFcstd(DataValue)
            except ValueError as ErrorInfo:
                if (
                    str(ErrorInfo)
                    != "FCStd archive has no embedded Kit interchange document"
                ):
                    return ProbeResult(Instance.info.FormatId, 0.0, str(ErrorInfo))
            else:
                try:
                    ManifestDoc(Value)
                except FreeCadAdapterA as ErrorInfo:
                    return ProbeResult(Instance.info.FormatId, 0.0, str(ErrorInfo))
                return ProbeResult(Instance.info.FormatId, 1.0, "Kit FCStd archive")
            Confidence, Reason = ProbeNativeFcstd(DataValue)
            return ProbeResult(Instance.info.FormatId, Confidence, Reason)
    except (OSError, TypeError, ValueError, Zipfile.BadZipFile) as ErrorInfo:
        return ProbeResult(Instance.info.FormatId, 0.0, str(ErrorInfo))
    return ProbeResult(
        Instance.info.FormatId, 0.0, "ZIP archive has no FreeCAD document"
    )


# this definition reads an embedded or native archive into the interchange model
def ReadSource(Source: Source, Options: ReadOptions | None = None) -> CadDoc:
    Settings = Options or ReadOptions(IncludeMesh=True)
    DataValue = SourceBytes(Source)
    Native = False
    try:
        Value = ExtractManifestFromFcstd(DataValue)
    except ValueError as ErrorInfo:
        if str(ErrorInfo) != "FCStd archive has no embedded Kit interchange document":
            raise FreeCadAdapterA(str(ErrorInfo)) from ErrorInfo
        try:
            DocValue = ReadNativeFcstd(DataValue, SourcePath(Source))
        except (NativeFreeCadError, TypeError, ValueError) as NativeError:
            raise FreeCadAdapterA(str(NativeError)) from NativeError
        Native = True
    else:
        DocValue = ManifestDoc(Value)
    if Native:
        DocValue = AnnotateNative(DocValue)
    DocValue = Replace(
        DocValue,
        configurations=Selected(DocValue.configurations, Settings.ConfigName),
    )
    DocValue = FilteredDoc(DocValue, Settings)
    if Settings.StrictMode:
        DocValue.assert_valid()
    return DocValue


# this definition validates a freecad path or writable binary destination
def CanWriteTarget(Target: Destination) -> bool:
    PathValue = ResolveTarget(Target)
    if PathValue is not None:
        return PathValue.suffix.casefold() == Suffix.casefold()
    if not IsBinaryTarget(Target):
        return False
    Writable = getattr(Target, "writable", None)
    if callable(Writable):
        try:
            return bool(Writable())
        except (OSError, ValueError):
            return False
    return True


# this definition chooses whether an unchanged native archive remains safe to replay
def SelectNative(
    DocValue: CadDocument,
    Selected: WriteOptions,
    Portable: bool,
    NativeOuters: Sequence[tuple[str, CadDoc]],
) -> bytes | None:
    if Selected.OptionValues.get("rebuild", False) is True:
        return None
    if Portable and (DocValue.assembly is not None or bool(NativeOuters)):
        return None
    return UnchangedNative(DocValue)


# this definition returns the exact native replay result and its reference contract
def ExactResult(
    Instance: FreeCadAdapter,
    DocValue: CadDocument,
    Target: Destination,
    TargetPath: FilePath | None,
    Overwrite: bool,
    Portable: bool,
    NativeOuters: Sequence[tuple[str, CadDoc]],
    NativeSource: bytes,
) -> WriteResult:
    PathValue = WriteBytes(Target, NativeSource, Overwrite)
    OuterRequirements = DocValue.assembly is not None or bool(NativeOuters)
    Requirements = ("referenced FreeCAD component files",) if OuterRequirements else ()
    return WriteResult(
        OutputPath=PathValue,
        AdapterName=Instance.info.FormatId,
        ByteCount=len(NativeSource),
        Diagnostics=DocValue.Diagnostics,
        Transfers=CapabilityA(DocValue, TargetPath, Portable, True),
        MetadataMap={
            "mode": "exact_native_roundtrip",
            "compatibility": "native-exact",
            "vendor_loadable": True,
            "application_usable": True,
            "native_self_contained": not OuterRequirements,
            "referenced_files_written": 0,
            "runtime": "python-stdlib",
        },
        Requirements=Requirements,
        IsAppUsable=True,
        IsVendorLoadable=True,
    )


# this definition writes referenced documents and returns their archive link state
def BundleArtifacts(
    DocValue: CadDocument,
    TargetPath: FilePath | None,
    Overwrite: bool,
    Validate: bool,
    Portable: bool,
    NativeOuters: Sequence[tuple[str, CadDoc]],
    TrustedBreps: frozenset[NativeBrepKey],
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, str],
    int,
    int,
    str | None,
    float | None,
    bool,
]:
    OuterLinks: dict[str, dict[str, object]] = {}
    NativeLinks: dict[str, str] = {}
    ComponentBytes = 0
    NativeBytes = 0
    DocTimestamp: str | None = None
    TimestampEpoch: float | None = None
    CarrierOnly = (
        TargetPath is None
        and Portable
        and (bool(NativeOuters) or DocValue.assembly is not None)
    )
    if TargetPath is not None and DocValue.assembly is not None:
        DocTimestamp, TimestampEpoch = BundleTimestamp(TargetPath)
        OuterLinks, ComponentBytes = WriteComponents(
            DocValue,
            TargetPath,
            Overwrite,
            Validate,
            DocTimestamp,
            TimestampEpoch,
            TrustedBreps,
        )
    if TargetPath is not None and NativeOuters and Portable:
        NativeLinks, NativeBytes = WriteNative(
            DocValue, TargetPath, Overwrite, Validate
        )
    return (
        OuterLinks,
        NativeLinks,
        ComponentBytes,
        NativeBytes,
        DocTimestamp,
        TimestampEpoch,
        CarrierOnly,
    )


# this definition builds stable metadata for a reconstructed freecad archive
def RebuildMeta(
    DocValue: CadDocument,
    OuterLinks: Mapping[str, object],
    ComponentBytes: int,
    NativeLinks: Mapping[str, str],
    NativeBytes: int,
    NativeOuters: Sequence[tuple[str, CadDoc]],
    CarrierOnly: bool,
    AppUsable: bool,
) -> dict[str, object]:
    AsmValue = DocValue.assembly
    return {
        "schema_version": DocValue.schema_version,
        "sketch_count": len(DocValue.sketches),
        "timeline_count": len(DocValue.feature_timeline),
        "native_payload_count": len(DocValue.brep_payloads),
        "assembly_occurrence_count": (
            len(AsmValue.instances) if AsmValue is not None else 0
        ),
        "assembly_mate_count": len(AsmValue.mates) if AsmValue is not None else 0,
        "component_file_count": len(OuterLinks),
        "component_bytes_written": ComponentBytes,
        "external_document_file_count": len(NativeLinks),
        "external_document_bytes_written": NativeBytes,
        "runtime": "python-stdlib",
        "recompute_required": True,
        "native_referenced_files_emitted": not CarrierOnly,
        "carrier_embedded_reference_count": len(NativeOuters)
        + (len(AsmValue.documents) if AsmValue is not None else 0),
        "application_usable": AppUsable,
        "vendor_loadable": True,
    }


# this definition appends the diagnostic required for stream only references
def RebuildDiags(DocValue: CadDocument, CarrierOnly: bool) -> tuple[DiagValue, ...]:
    if not CarrierOnly:
        return DocValue.diagnostics
    return (
        *DocValue.diagnostics,
        DiagValue(
            "freecad.references_embedded_without_files",
            "Referenced documents are retained in the Kit carrier but cannot be exposed as native relative files from a stream destination",
            Severity.WARNING,
        ),
    )


# this definition rebuilds and writes a portable freecad archive
def RebuildResult(
    Instance: FreeCadAdapter,
    DocValue: CadDocument,
    Target: Destination,
    TargetPath: FilePath | None,
    Selected: WriteOptions,
    Overwrite: bool,
    Portable: bool,
    NativeOuters: Sequence[tuple[str, CadDoc]],
    TrustedBreps: frozenset[NativeBrepKey],
) -> WriteResult:
    (
        OuterLinks,
        NativeLinks,
        ComponentBytes,
        NativeBytes,
        DocStamp,
        StampEpoch,
        CarrierOnly,
    ) = BundleArtifacts(
        DocValue,
        TargetPath,
        Overwrite,
        Selected.Validate,
        Portable,
        NativeOuters,
        TrustedBreps,
    )
    DataValue = BuildFcstdArchive(
        DocToManifest(DocValue),
        external_links=OuterLinks,
        native_external_links=NativeLinks,
        document_timestamp=DocStamp,
        trusted_native_breps=TrustedBreps,
    )
    PathValue = WriteBytes(Target, DataValue, Overwrite)
    if PathValue is not None and StampEpoch is not None:
        OsModule.utime(PathValue, (StampEpoch, StampEpoch))
    Transfers = CapabilityA(DocValue, TargetPath, Portable, False, TrustedBreps)
    AppUsable = not CarrierOnly and IsNativeGeom(DocValue, TrustedBreps)
    MetaValue = RebuildMeta(
        DocValue,
        OuterLinks,
        ComponentBytes,
        NativeLinks,
        NativeBytes,
        NativeOuters,
        CarrierOnly,
        AppUsable,
    )
    return WriteResult(
        OutputPath=PathValue,
        AdapterName=Instance.info.FormatId,
        ByteCount=len(DataValue),
        Diagnostics=RebuildDiags(DocValue, CarrierOnly),
        MetadataMap=MetaValue,
        Transfers=Transfers,
        IsAppUsable=AppUsable,
        IsVendorLoadable=True,
    )


# this definition selects exact replay or reconstruction for one write request
def WriteTarget(
    Instance: FreeCadAdapter,
    DocValue: CadDocument,
    Target: Destination,
    Options: WriteOptions | None,
    Overwrite: bool | None,
) -> WriteResult:
    Selected = Options or WriteOptions()
    ShouldOverwrite = Selected.Overwrite if Overwrite is None else Overwrite
    if Selected.Validate:
        DocValue.assert_valid()
    if not Instance.supports(DocValue, Target):
        raise FreeCadAdapterA(
            f"FreeCAD destination must be a {Suffix} path or writable binary stream"
        )
    TargetPath = ResolveTarget(Target)
    if TargetPath is not None and TargetPath.exists() and not ShouldOverwrite:
        raise FileExistsError(TargetPath)
    Portable = Selected.OptionValues.get("portable", True) is True
    NativeOuters = NativeOuter(DocValue)
    TrustedBreps = TrustedNative(DocValue)
    NativeSource = SelectNative(DocValue, Selected, Portable, NativeOuters)
    if NativeSource is not None:
        return ExactResult(
            Instance,
            DocValue,
            Target,
            TargetPath,
            ShouldOverwrite,
            Portable,
            NativeOuters,
            NativeSource,
        )
    return RebuildResult(
        Instance,
        DocValue,
        Target,
        TargetPath,
        Selected,
        ShouldOverwrite,
        Portable,
        NativeOuters,
        TrustedBreps,
    )


# this definition exposes the adapter protocol through thin delegating methods
class FreeCadAdapter:

    # this definition exposes immutable format metadata to adapter discovery
    @property
    def info(self) -> AdapterInfo:
        return InfoValue

    # this definition delegates archive probing to the focused probe implementation
    def probe(self, Source: Source) -> ProbeResult:
        return ProbeSource(self, Source)

    # this definition delegates archive reading to the focused reader implementation
    def read(self, Source: Source, Options: ReadOptions | None = None) -> CadDoc:
        return ReadSource(Source, Options)

    # this definition delegates destination checks to the focused support implementation
    def supports(self, DocValue: CadDocument, Target: Destination) -> bool:
        return CanWriteTarget(Target)

    # this definition delegates archive writing to the focused writer implementation
    def write(
        self,
        DocValue: CadDocument,
        Target: Destination,
        Options: WriteOptions | None = None,
        *,
        Overwrite: bool | None = None,
    ) -> WriteResult:
        return WriteTarget(self, DocValue, Target, Options, Overwrite)


# this definition exists because focused behavior needs one stable owner
def ExtractFreecad(Source: Source) -> dict[str, object]:
    return ExtractManifestFromFcstd(SourceBytes(Source))


# this definition exists because focused behavior needs one stable owner
def ReadFreecad(Source: Source, Options: ReadOptions | None = None) -> CadDoc:
    return FreeCadAdapter().read(Source, Options)


# this definition exists because focused behavior needs one stable owner
def WriteFreecad(
    DocValue: CadDocument,
    Target: Destination,
    *,
    Overwrite: bool = False,
    Validate: bool = True,
) -> WriteResult:
    return FreeCadAdapter().write(
        DocValue, Target, WriteOptions(Overwrite=Overwrite, Validate=Validate)
    )


# this binding exists because shared behavior needs one stable value
CAPABILITY_CARRIER_REASONS = CapabilityCarrierReasons

# this binding exists because shared behavior needs one stable value
CadDocument = CadDoc

# this binding exists because shared behavior needs one stable value
Configuration = Config

# this binding exists because shared behavior needs one stable value
DOCUMENT_ENTRY = DocEntry

# this binding exists because shared behavior needs one stable value
Destination = Target

# this binding exists because shared behavior needs one stable value
Diagnostic = DiagValue

# this binding exists because shared behavior needs one stable value
ET = XmlTree

# this binding exists because shared behavior needs one stable value
FEATURE_WRITE_KINDS = FeatureWriteKinds

# this binding exists because shared behavior needs one stable value
FREECAD_BREP_FORMAT_IDS = FreecadBrepFormatIds

# this binding exists because shared behavior needs one stable value
FreeCADAdapter = FreeCadAdapter

# this binding exists because shared behavior needs one stable value
FreeCADAdapterError = FreeCadAdapterA

# this binding exists because shared behavior needs one stable value
FreeCADBrepWriteError = FreeCadBrepWriteError

# this binding exists because shared behavior needs one stable value
INFO = InfoValue

# this binding exists because shared behavior needs one stable value
MANIFEST_ENTRY = ManifestEntry

# this binding exists because shared behavior needs one stable value
MATE_WRITE_KINDS = MateWriteKinds

# this binding exists because shared behavior needs one stable value
Mesh = MeshValue

# this binding exists because shared behavior needs one stable value
NATIVE_DOCUMENT_SHA256_ATTRIBUTE = KNativeDocHashAttr

# this binding exists because shared behavior needs one stable value
NativeFreeCADError = NativeFreeCadError

# this binding exists because shared behavior needs one stable value
Path = FilePath

# this binding exists because shared behavior needs one stable value
SUFFIX = Suffix

# this binding exists because shared behavior needs one stable value
XML_TRUE_VALUES = XmlTrueValues

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
brep_model_brep = BrepModelBrep

# this binding exists because shared behavior needs one stable value
build_fcstd_archive = BuildFcstdArchive

# this binding exists because shared behavior needs one stable value
datetime = Datetime

# this binding exists because shared behavior needs one stable value
document_to_manifest = DocToManifest

# this binding exists because shared behavior needs one stable value
extract_freecad_manifest = ExtractFreecad

# this binding exists because shared behavior needs one stable value
extract_manifest_from_fcstd = ExtractManifestFromFcstd

# this binding exists because shared behavior needs one stable value
filter_document = FilterDoc

# this binding exists because shared behavior needs one stable value
frozen_mapping = FrozenMapping

# this binding exists because shared behavior needs one stable value
hashlib = Hashlib

# this binding exists because shared behavior needs one stable value
infer_capabilities = InferCapabilities

# this binding exists because shared behavior needs one stable value
io = IoStream

# this binding exists because shared behavior needs one stable value
is_binary_destination = IsBinaryTarget

# this binding exists because shared behavior needs one stable value
is_windows_device_name = IsWindowsDeviceName

# this binding exists because shared behavior needs one stable value
json = JsonValue

# this binding exists because shared behavior needs one stable value
math = MathValue

# this binding exists because shared behavior needs one stable value
native_expression_parts = NativeExpressionParts

# this binding exists because shared behavior needs one stable value
native_shape_feature_count = NativeShapeFeatureCount

# this binding exists because shared behavior needs one stable value
native_sketch_carrier_reasons = NativeSketchCarrier

# this binding exists because shared behavior needs one stable value
native_sketch_parts = NativeSketchParts

# this binding exists because shared behavior needs one stable value
os = OsModule

# this binding exists because shared behavior needs one stable value
probe_native_fcstd = ProbeNativeFcstd

# this binding exists because shared behavior needs one stable value
proven_ascii_brep = ProvenAsciiBrep

# this binding exists because shared behavior needs one stable value
re = RegexLib

# this binding exists because shared behavior needs one stable value
read_freecad = ReadFreecad

# this binding exists because shared behavior needs one stable value
read_native_fcstd = ReadNativeFcstd

# this binding exists because shared behavior needs one stable value
replace = Replace

# this binding exists because shared behavior needs one stable value
semantic_metadata = SemanticMeta

# this binding exists because shared behavior needs one stable value
source_payload_indexes = SourcePayloadIndexes

# this binding exists because shared behavior needs one stable value
suppress = Suppress

# this binding exists because shared behavior needs one stable value
tempfile = Tempfile

# this binding exists because shared behavior needs one stable value
timezone = Timezone

# this binding exists because shared behavior needs one stable value
write_freecad = WriteFreecad

# this binding exists because shared behavior needs one stable value
zipfile = Zipfile

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress as Suppress
from dataclasses import replace as Replace
from datetime import datetime as Datetime, timezone as Timezone
import hashlib as Hashlib
import io as IoStream
import json as JsonValue
import math as MathValue
import os as OsModule
from pathlib import Path as FilePath
import re as RegexLib
import tempfile as Tempfile
from typing import Any as AnyValue
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
from interchange.serialization import ToData
from convert.adapters.freecad.Archive import (
    DOCUMENT_ENTRY as DocEntry,
    MANIFEST_ENTRY as ManifestEntry,
    NATIVE_DOCUMENT_SHA256_ATTRIBUTE as KNativeDocHashAttr,
    NativeBrepKey,
    _MAX_ENTRY_SIZE as MaxEntrySize,
    _MAX_EXTERNAL_FILES as MaxOuterFiles,
    _MAX_TOTAL_SIZE as MaxTotalSize,
    _native_brep_key as ManifestNativeBrepKey,
    _validated_archive_members as ValidatedArchiveMembers,
    _validated_document_xml as ValidatedDocXml,
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
    def InitAction(Instance, Message: str) -> None:
        super().__init__(Message)

    locals()["__init__"] = InitAction


# this definition exists because focused behavior needs one stable owner
def DocToManifest(DocValue: Any) -> dict[str, AnyValue]:
    Manifest = ToData(DocValue)
    if not isinstance(Manifest, dict):
        raise TypeError("CadDocument.to_dict() must produce a mapping")
    if Manifest.get("$type") == "CadDocument":
        Required = set(DocValue.to_dict())
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
            try:
                SeekValue(Position)
            except (OSError, ValueError):
                Position = None
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
def FilterOuters(Outer: AnyValue, Settings: ReadOptions) -> tuple[list[AnyValue], bool]:
    if not isinstance(Outer, Sequence) or isinstance(Outer, (str, bytes, bytearray)):
        return ([], False)
    StrippedOuter: list[AnyValue] = []
    Changed = False
    for Value in Outer:
        if not isinstance(Value, Mapping):
            StrippedOuter.append(Value)
            continue
        Linked = Value.get("document")
        Mapped = isinstance(Linked, Mapping)
        if Mapped:
            try:
                Linked = CadDoc.from_dict(Linked)
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
    MetaValue: Mapping[str, AnyValue], Settings: ReadOptions
) -> Mapping[str, AnyValue]:
    Freecad = MetaValue.get("freecad", {}) if isinstance(MetaValue, Mapping) else {}
    Outer = (
        Freecad.get("external_documents", []) if isinstance(Freecad, Mapping) else []
    )
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
        include_brep=Settings.include_brep,
        include_tessellation=Settings.include_tessellation,
        keep_payload_records=False,
    )
    MetaValue: Mapping[str, AnyValue] = FilterOuterMeta(Filtered.metadata, Settings)
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
    MetaValue: Mapping[str, Any], Transform: Callable[[CadDocument], CadDocument]
) -> Mapping[str, AnyValue]:
    Freecad = MetaValue.get("freecad", {})
    if not isinstance(Freecad, Mapping):
        return MetaValue
    Values = Freecad.get("external_documents", [])
    if not isinstance(Values, Sequence) or isinstance(Values, (str, bytes, bytearray)):
        return MetaValue
    Changed = False
    Mapped: list[AnyValue] = []
    for Value in Values:
        if not isinstance(Value, Mapping):
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
                        document=(
                            AnnotateNative(ItemValue.document)
                            if isinstance(ItemValue.document, CadDoc)
                            else ItemValue.document
                        ),
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
    NativeDoc, Ignored = PairValue
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
    NativeDoc, Ignored = PairValue
    Expected = NativeDoc.attributes.get(KReplaySemanticAttr)
    if not isinstance(Expected, str) or Expected != SemanticDigest(DocValue):
        return None
    DataValue = NativeDoc.data
    if DataValue is None:
        return None
    try:
        Archive, Ignored = ValidatedArchiveMembers(DataValue)
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
def EnumText(Value: Any) -> str:
    return str(getattr(Value, "value", Value) or "").casefold()


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
                    if isinstance(Component.document, CadDoc)
                )
            )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def HasNativeGraph(DocValue: CadDocument) -> bool:
    Freecad = DocValue.metadata.get("freecad", {})
    if not isinstance(Freecad, Mapping):
        return False
    Objects = Freecad.get("objects", ())
    return (
        isinstance(Objects, Sequence)
        and (not isinstance(Objects, (str, bytes, bytearray)))
        and bool(Objects)
    )


# this definition exists because focused behavior needs one stable owner
def HasFeatureEdges(DocValue: CadDocument, Feature: Any) -> bool:
    Attributes = Feature.attributes
    for NameValue in (
        "selected_native_local_edge_ids",
        "native_local_edge_ids",
        "edge_ids",
        "edges",
    ):
        Values = Attributes.get(NameValue, ())
        if (
            isinstance(Values, Sequence)
            and (not isinstance(Values, (str, bytes, bytearray)))
            and any((isinstance(Value, (int, float)) and Value > 0 for Value in Values))
        ):
            return True
    Selections = {Selection.id: Selection for Selection in DocValue.selections}
    for SelectionId in Feature.selection_ids:
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
        if any(
            (
                isinstance(Selection.query.get(NameValue), (int, float))
                and Selection.query[NameValue] > 0
                for NameValue in ("edge_index", "native_local_id", "index")
            )
        ):
            return True
    return False


# this definition exists because focused behavior needs one stable owner
def IsExtrusion(Feature: Any) -> bool:
    Definition = Feature.definition
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
    return EnumText(Feature.operation) in {"", "create", "join", "cut", "intersect"}


# this definition rejects records that do not represent transferable timeline features
def IsFeatureNeeded(
    Feature: AnyValue,
    DependentFeatureIds: set[str],
    FinalFeatureIds: set[str | None],
) -> bool:
    KindValue = EnumText(Feature.kind)
    if KindValue == FeatureKind.IMPORTED.value:
        return False
    NativeType = str(Feature.attributes.get("native_type", "")).casefold()
    if KindValue == FeatureKind.REFERENCE.value and NativeType in {"plane", "sketch"}:
        return False
    IsUnusedNative = (
        KindValue == FeatureKind.NATIVE.value
        and Feature.id not in DependentFeatureIds
        and Feature.id not in FinalFeatureIds
        and not Feature.input_feature_ids
        and Feature.sketch_id is None
        and not Feature.parameter_ids
        and not Feature.selection_ids
    )
    return not IsUnusedNative


# this definition selects only timeline features that require transfer accounting
def FeatureSet(DocValue: CadDocument) -> tuple[AnyValue, ...]:
    DependentFeatureIds = {
        FeatureId
        for Feature in DocValue.feature_timeline
        for FeatureId in Feature.input_feature_ids
    }
    FinalFeatureIds = {BodyValue.final_feature_id for BodyValue in DocValue.bodies}
    return tuple(
        Feature
        for Feature in DocValue.feature_timeline
        if IsFeatureNeeded(Feature, DependentFeatureIds, FinalFeatureIds)
    )


# this definition identifies feature kinds that the native writer can reconstruct
def CanWriteFeature(
    DocValue: CadDocument, Feature: AnyValue, SketchNative: Mapping[str, bool]
) -> bool:
    KindValue = EnumText(Feature.kind)
    if Feature.suppressed or KindValue not in KFeatureWriteValues:
        return False
    if KindValue == FeatureKind.EXTRUSION.value:
        return (
            bool(Feature.sketch_id)
            and SketchNative.get(Feature.sketch_id or "", False)
            and IsExtrusion(Feature)
        )
    if KindValue == FeatureKind.FILLET.value:
        Definition = Feature.definition
        return (
            isinstance(Definition, FilletFeature)
            and not Definition.variable_radius_parameter_ids
            and bool(Feature.input_feature_ids)
            and HasFeatureEdges(DocValue, Feature)
        )
    if KindValue == FeatureKind.CHAMFER.value:
        Definition = Feature.definition
        return (
            isinstance(Definition, ChamferFeature)
            and Definition.mode == "equal_distance"
            and Definition.second_distance is None
            and Definition.angle is None
            and bool(Feature.input_feature_ids)
            and HasFeatureEdges(DocValue, Feature)
        )
    return False


# this definition explains why a timeline feature requires carrier preservation
def FeatureReasons(
    Feature: AnyValue, SketchCarrierReasons: Mapping[str, CarrierReason]
) -> frozenset[CarrierReason]:
    KindValue = EnumText(Feature.kind)
    if Feature.suppressed or KindValue == FeatureKind.REFERENCE.value:
        return frozenset({CarrierReason.TARGET_UNSUPPORTED})
    if KindValue == FeatureKind.NATIVE.value:
        return frozenset({CarrierReason.SOURCE_OPAQUE})
    Reasons: set[CarrierReason] = set()
    if KindValue == FeatureKind.EXTRUSION.value:
        SketchReason = SketchCarrierReasons.get(Feature.sketch_id or "")
        if SketchReason is not None:
            Reasons.add(SketchReason)
        if not Feature.sketch_id or not IsExtrusion(Feature):
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
        HasNativeReferences = (
            isinstance(References, Sequence)
            and (not isinstance(References, (str, bytes, bytearray)))
            and (len(References) >= 2)
        )
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
    DataValue = Payload.data
    Provenance = Payload.provenance
    Attributes = Payload.attributes
    FreecadObject = Attributes.get("freecad_object")
    FreecadObjectType = Attributes.get("freecad_object_type")
    FreecadProp = Attributes.get("freecad_property")
    NativeDigestText = Attributes.get(KNativeDocHashAttr)
    PropData = Attributes.get("freecad_property_data")
    PropAttributes = (
        PropData.get("attributes", {}) if isinstance(PropData, Mapping) else {}
    )
    PropChildren = PropData.get("children", ()) if isinstance(PropData, Mapping) else ()
    PartFiles = tuple(
        (
            ChildAttributes.get("file")
            for Child in PropChildren
            if isinstance(Child, Mapping)
            and Child.get("tag") == "Part"
            and isinstance((ChildAttributes := Child.get("attributes")), Mapping)
        )
    )
    return (
        Payload.role == PayloadRole.BREP
        and DataValue is not None
        and (Payload.format_id.casefold() in FreecadBrepFormatIds)
        and (Payload.kind == "shape")
        and Payload.schema.startswith("CASCADE Topology V")
        and (Payload.sha256 == Hashlib.sha256(DataValue).hexdigest())
        and (Provenance is not None)
        and (Provenance.adapter == InfoValue.format_id)
        and (Provenance.confidence == 1.0)
        and isinstance(FreecadObject, str)
        and bool(FreecadObject)
        and isinstance(FreecadObjectType, str)
        and bool(FreecadObjectType)
        and isinstance(FreecadProp, str)
        and bool(FreecadProp)
        and isinstance(NativeDigestText, str)
        and (RegexLib.fullmatch("[0-9a-f]{64}", NativeDigestText) is not None)
        and (Provenance.native_id == f"{FreecadObject}.{FreecadProp}")
        and (Payload.source_stream == f"{FreecadObject}.{FreecadProp}.brp")
        and isinstance(PropData, Mapping)
        and (PropData.get("tag") == "Property")
        and (PropAttributes.get("name") == FreecadProp)
        and (PropAttributes.get("type") == "Part::PropertyPartShape")
        and (PartFiles == (Payload.source_stream,))
    )


# this definition exists because focused behavior needs one stable owner
def ManifestBrep(DocValue: CadDocument) -> tuple[Mapping[str, AnyValue], ...]:
    Values = DocToManifest(DocValue).get("brep_payloads", ())
    if isinstance(Values, Mapping):
        Values = Values.get("$tuple", ())
    if not isinstance(Values, Sequence) or isinstance(Values, (str, bytes, bytearray)):
        return ()
    Result = tuple((Value for Value in Values if isinstance(Value, Mapping)))
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
def XmlElemData(NodeValue: ET.Element) -> dict[str, AnyValue]:
    Result: dict[str, AnyValue] = {
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
    if not isinstance(Sidecars, Sequence) or isinstance(
        Sidecars, (str, bytes, bytearray)
    ):
        return False
    if len(Sidecars) != len(ReferencedSidecars):
        return False
    for Sidecar, SourceStream in zip(Sidecars, ReferencedSidecars, strict=True):
        if not isinstance(Sidecar, Mapping):
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
            RootValue, Ignored = ValidatedDocXml(Archive, Members)
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
    MappedPayload: Mapping[str, Any] | None = None,
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
    MappedPayload: Mapping[str, Any] | None = None,
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
def IsMeshUsable(MeshValue: Mesh) -> bool:
    Points = tuple(((Value.x, Value.y, Value.z) for Value in MeshValue.vertices))
    if not Points or any((not all(map(MathValue.isfinite, Point)) for Point in Points)):
        return False
    for Triangle in MeshValue.triangles:
        if len(set(Triangle)) != 3 or any(
            (Index < 0 or Index >= len(Points) for Index in Triangle)
        ):
            continue
        First, Second, Third = (Points[Index] for Index in Triangle)
        LeftValue = tuple((Second[Index] - First[Index] for Index in range(3)))
        Right = tuple((Third[Index] - First[Index] for Index in range(3)))
        Cross = (
            LeftValue[1] * Right[2] - LeftValue[2] * Right[1],
            LeftValue[2] * Right[0] - LeftValue[0] * Right[2],
            LeftValue[0] * Right[1] - LeftValue[1] * Right[0],
        )
        if sum((Value * Value for Value in Cross)) > 1e-24:
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
            if isinstance(ItemValue.document, CadDoc)
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
            ItemValue.source.format_id.casefold() != InfoValue.format_id.casefold()
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
    ReasonValues: Sequence[str],
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
    Manifest: Mapping[str, AnyValue],
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
    Manifest: Mapping[str, AnyValue],
    SourceNative: bool,
    SketchNative: Mapping[str, bool],
    SketchReasons: Mapping[str, CarrierReason],
    Parts: dict[Capability, list[bool]],
    CarrierReasons: dict[Capability, set[CarrierReason]],
) -> None:
    Parts[Capability.PARAMETERS].extend(True for Ignored in ItemValue.parameters)
    NativeCount, CarrierCount, Reasons = FeatureParts(
        ItemValue, SketchNative, SketchReasons
    )
    Parts[Capability.PARAMETRIC_HISTORY].extend(
        [True] * NativeCount + [False] * CarrierCount
    )
    CarrierReasons[Capability.PARAMETRIC_HISTORY].update(Reasons)
    Parts[Capability.SUPPORT_PLANES].extend(
        True for Ignored in ItemValue.support_planes
    )
    SelectionCounts = (
        (len(ItemValue.selections), 0) if SourceNative else SelectionParts(ItemValue)
    )
    Parts[Capability.SELECTIONS].extend(
        [True] * SelectionCounts[0] + [False] * SelectionCounts[1]
    )
    Parts[Capability.BODY_STRUCTURE].extend(True for Ignored in ItemValue.bodies)
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
    Manifest: Mapping[str, AnyValue],
    MappedByIdentity: Mapping[int, Mapping[str, AnyValue]],
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
        if ItemValue.source.format_id.casefold() != InfoValue.format_id.casefold()
        else 0
    )
    if RebuiltCount and not all(Parts[Capability.BREP]):
        Parts[Capability.BREP].extend(True for Ignored in range(RebuiltCount))
    Parts[Capability.TESSELLATION].extend(True for Ignored in ItemValue.meshes)
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
            NativeDocuments for Ignored in ItemValue.assembly.documents
        )
        CanWriteOuter = TargetPath is not None and Portable
        Parts[Capability.EXTERNAL_REFERENCES].extend(
            CanWriteOuter
            for Definition in ItemValue.assembly.definitions
            if Definition.source_path
        )
    Parts[Capability.EXTERNAL_REFERENCES].extend(
        TargetPath is not None and Portable for Ignored in NativeOuter(ItemValue)
    )
    Parts[Capability.MATERIALS].extend(
        True for BodyValue in ItemValue.bodies if BodyValue.material_id
    )


# this definition records native payload transfer parts and carrier reasons
def AddPayloadMut(
    ItemValue: CadDocument,
    MappedByIdentity: Mapping[int, Mapping[str, AnyValue]],
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
        False for Value in Values if Value.provenance is not None
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
    Parts = {CapabilityValue: [] for CapabilityValue in Capability}
    CarrierReasons = {CapabilityValue: set() for CapabilityValue in Capability}
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
def OuterLink(DataValue: bytes) -> tuple[str, list[dict[str, AnyValue]]]:
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
    def ItemAction(
        NameValue: str, Active: frozenset[str]
    ) -> dict[str, AnyValue] | None:
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
        InstanceData: AnyValue = {}
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
    Scope = f"{Definition.kind.value}:{Config}"
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
    Links: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, AnyValue] | None:
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
    Links: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, AnyValue]]:
    AsmValue = Component.assembly
    if AsmValue is None:
        return {}
    Documents = {
        ItemValue.id: ItemValue.document
        for ItemValue in AsmValue.documents
        if isinstance(ItemValue.document, CadDoc)
    }
    Result: dict[str, dict[str, AnyValue]] = {}
    for Definition in AsmValue.definitions:
        if Definition.id == AsmValue.root_definition_id:
            continue
        LinkValue = MatchLink(
            Definition, Documents, RootDefinitions, RootDocuments, Links
        )
        if LinkValue is None:
            continue
        PathValue = FilePath(LinkValue["path"])
        Result[Definition.id] = {
            "file": FilePath(
                OsModule.path.relpath(PathValue, ComponentPath.parent)
            ).as_posix(),
            "stamp": str(LinkValue.get("stamp", "")),
            "target": str(LinkValue.get("target", "")),
            "occurrences": list(LinkValue.get("occurrences", [])),
        }
    return Result


# this definition orders part documents before dependent assembly documents
def ComponentPlanKey(
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
    Documents = {
        ItemValue.id: ItemValue.document
        for ItemValue in AsmValue.documents
        if isinstance(ItemValue.document, CadDoc)
    }
    Definitions = {ItemValue.id: ItemValue for ItemValue in AsmValue.definitions}
    Plans: list[tuple[str, FilePath, ComponentDefinition, CadDoc]] = []
    for DefinitionId, PathValue in Paths.items():
        Definition = Definitions[DefinitionId]
        Component = ComponentDoc(DocValue, Definition, Documents)
        if Component is not None:
            Plans.append((DefinitionId, PathValue, Definition, Component))
    Plans.sort(key=ComponentPlanKey)
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
) -> tuple[dict[str, dict[str, AnyValue]], int]:
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
        {
            ItemValue.id: ItemValue.document
            for ItemValue in DocValue.assembly.documents
            if isinstance(ItemValue.document, CadDoc)
        }
        if DocValue.assembly is not None
        else {}
    )
    ComponentLinks: dict[str, dict[str, AnyValue]] = {}
    OuterLinks: dict[str, dict[str, AnyValue]] = {}
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
def NativeOuter(DocValue: CadDocument) -> list[tuple[str, CadDoc]]:
    MetaValue = DocValue.metadata
    Freecad = MetaValue.get("freecad", {}) if isinstance(MetaValue, Mapping) else {}
    Values = (
        Freecad.get("external_documents", []) if isinstance(Freecad, Mapping) else []
    )
    if not isinstance(Values, Sequence) or isinstance(Values, (str, bytes, bytearray)):
        raise FreeCadAdapterA("native FreeCAD external document metadata is invalid")
    Result: list[tuple[str, CadDoc]] = []
    SeenValue: set[str] = set()
    Total = 0
    for Value in Values:
        if not isinstance(Value, Mapping):
            raise FreeCadAdapterA(
                "native FreeCAD external document metadata is invalid"
            )
        SourceFile = str(Value.get("file", ""))
        Linked = Value.get("document")
        if isinstance(Linked, Mapping):
            try:
                Linked = CadDoc.from_dict(Linked)
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
        NativePayloadSize = sum(
            (
                len(Payload.data)
                for Payload in Linked.brep_payloads
                if Payload.role == PayloadRole.DOCUMENT and Payload.data is not None
            )
        )
        Total += NativePayloadSize
        if len(Result) >= MaxOuterFiles or Total > MaxTotalSize:
            raise FreeCadAdapterA(
                "native FreeCAD external documents exceed safe limits"
            )
        Result.append((SourceFile, Linked))
    return Result


# this definition exists because focused behavior needs one stable owner
def WriteNative(
    DocValue: CadDocument, Target: Path, Overwrite: bool, Validate: bool
) -> tuple[dict[str, str], int]:
    Records = NativeOuter(DocValue)
    Folder = Target.parent / Target.stem
    UsedValue: set[str] = set()
    Links: dict[str, str] = {}
    BytesWritten = 0
    for SourceFile, Linked in Records:
        SourceName = FilePath(SourceFile).name
        Suffix = FilePath(SourceName).suffix or Suffix
        BaseValue = ComponentStem(FilePath(SourceName).stem)
        Choice = BaseValue
        Index = 1
        while (Choice + Suffix).casefold() in UsedValue:
            Index += 1
            Ending = f"_{Index}"
            Choice = BaseValue[: 120 - len(Ending)].rstrip(" .") + Ending
        FileName = Choice + Suffix
        UsedValue.add(FileName.casefold())
        Output = Folder / FileName
        Result = FreeCadAdapter().write(
            Linked,
            Output,
            WriteOptions(
                overwrite=Overwrite, validate=Validate, values={"portable": True}
            ),
        )
        if Result.bytes_written > MaxEntrySize:
            raise FreeCadAdapterA(
                "native FreeCAD external document exceeds safe limits"
            )
        BytesWritten += Result.bytes_written
        if BytesWritten > MaxTotalSize:
            raise FreeCadAdapterA(
                "native FreeCAD external documents exceed safe limits"
            )
        Links[SourceFile] = Output.relative_to(Target.parent).as_posix()
    return (Links, BytesWritten)


# this definition exists because focused behavior needs one stable owner
def ManifestDoc(Value: Mapping[str, Any]) -> CadDoc:
    try:
        return CadDoc.from_dict(Value)
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


# this definition exists because focused behavior needs one stable owner
class FreeCadAdapter:

    # this definition exists because focused behavior needs one stable owner
    @property
    def InfoAction(Instance) -> AdapterInfo:
        return InfoValue

    # this definition exists because focused behavior needs one stable owner
    def Probe(Instance, Source: Source) -> ProbeResult:
        try:
            DataValue = SourceBytes(Source)
            Archive, Members = ValidatedArchiveMembers(DataValue)
            Archive.close()
            if ManifestEntry in Members:
                try:
                    Value = ExtractManifestFromFcstd(DataValue)
                    ManifestDoc(Value)
                except (ValueError, FreeCadAdapterA) as ErrorInfo:
                    return ProbeResult(Instance.info.format_id, 0.0, str(ErrorInfo))
                return ProbeResult(Instance.info.format_id, 1.0, "Kit FCStd archive")
            if "Document.xml" in Members:
                try:
                    Value = ExtractManifestFromFcstd(DataValue)
                except ValueError as ErrorInfo:
                    if (
                        str(ErrorInfo)
                        != "FCStd archive has no embedded Kit interchange document"
                    ):
                        return ProbeResult(Instance.info.format_id, 0.0, str(ErrorInfo))
                else:
                    try:
                        ManifestDoc(Value)
                    except FreeCadAdapterA as ErrorInfo:
                        return ProbeResult(Instance.info.format_id, 0.0, str(ErrorInfo))
                    return ProbeResult(
                        Instance.info.format_id, 1.0, "Kit FCStd archive"
                    )
                Confidence, Reason = ProbeNativeFcstd(DataValue)
                return ProbeResult(Instance.info.format_id, Confidence, Reason)
        except (OSError, TypeError, ValueError, Zipfile.BadZipFile) as ErrorInfo:
            return ProbeResult(Instance.info.format_id, 0.0, str(ErrorInfo))
        return ProbeResult(
            Instance.info.format_id, 0.0, "ZIP archive has no FreeCAD document"
        )

    # this definition exists because focused behavior needs one stable owner
    def ReadAction(
        Instance, Source: Source, Options: ReadOptions | None = None
    ) -> CadDoc:
        Settings = Options or ReadOptions(include_tessellation=True)
        DataValue = SourceBytes(Source)
        Native = False
        try:
            Value = ExtractManifestFromFcstd(DataValue)
        except ValueError as ErrorInfo:
            if (
                str(ErrorInfo)
                != "FCStd archive has no embedded Kit interchange document"
            ):
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
            configurations=Selected(DocValue.configurations, Settings.configuration),
        )
        DocValue = FilteredDoc(DocValue, Settings)
        if Settings.strict:
            DocValue.assert_valid()
        return DocValue

    # this definition exists because focused behavior needs one stable owner
    def CanSupport(Instance, DocValue: CadDocument, Target: Destination) -> bool:
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

    # this definition exists because focused behavior needs one stable owner
    def Write(
        Instance,
        DocValue: CadDocument,
        Target: Destination,
        Options: WriteOptions | None = None,
        *,
        Overwrite: bool | None = None,
    ) -> WriteResult:
        Selected = Options or WriteOptions()
        ShouldOverwrite = Selected.overwrite if Overwrite is None else Overwrite
        if Selected.validate:
            DocValue.assert_valid()
        if not Instance.supports(DocValue, Target):
            raise FreeCadAdapterA(
                f"FreeCAD destination must be a {Suffix} path or writable binary stream"
            )
        TargetPath = ResolveTarget(Target)
        if TargetPath is not None and TargetPath.exists() and (not ShouldOverwrite):
            raise FileExistsError(TargetPath)
        Portable = Selected.values.get("portable", True) is True
        NativeOuterDocuments = NativeOuter(DocValue)
        VerifiedNativeSource = UnchangedNative(DocValue)
        TrustedNativeBreps = TrustedNative(DocValue)
        NativeSource = (
            None
            if Selected.values.get("rebuild", False) is True
            or (
                Portable
                and (DocValue.assembly is not None or bool(NativeOuterDocuments))
            )
            else VerifiedNativeSource
        )
        if NativeSource is not None:
            PathValue = WriteBytes(Target, NativeSource, ShouldOverwrite)
            OuterRequirements = DocValue.assembly is not None or bool(
                NativeOuterDocuments
            )
            Requirements = (
                ("referenced FreeCAD component files",) if OuterRequirements else ()
            )
            return WriteResult(
                path=PathValue,
                adapter=Instance.info.format_id,
                bytes_written=len(NativeSource),
                diagnostics=DocValue.diagnostics,
                transfers=CapabilityA(DocValue, TargetPath, Portable, True),
                metadata={
                    "mode": "exact_native_roundtrip",
                    "compatibility": "native-exact",
                    "vendor_loadable": True,
                    "application_usable": True,
                    "native_self_contained": not OuterRequirements,
                    "referenced_files_written": 0,
                    "runtime": "python-stdlib",
                },
                requirements=Requirements,
                application_usable=True,
                vendor_loadable=True,
            )
        OuterLinks: dict[str, dict[str, AnyValue]] = {}
        NativeOuterLinks: dict[str, str] = {}
        ComponentBytesWritten = 0
        NativeOuterBytesWritten = 0
        DocTimestamp: str | None = None
        TimestampEpoch: float | None = None
        CarrierOnlyReferences = (
            TargetPath is None
            and Portable
            and (bool(NativeOuterDocuments) or DocValue.assembly is not None)
        )
        if TargetPath is not None and DocValue.assembly is not None:
            DocTimestamp, TimestampEpoch = BundleTimestamp(TargetPath)
            OuterLinks, ComponentBytesWritten = WriteComponents(
                DocValue,
                TargetPath,
                ShouldOverwrite,
                Selected.validate,
                DocTimestamp,
                TimestampEpoch,
                TrustedNativeBreps,
            )
        if TargetPath is not None and NativeOuterDocuments and Portable:
            NativeOuterLinks, NativeOuterBytesWritten = WriteNative(
                DocValue, TargetPath, ShouldOverwrite, Selected.validate
            )
        Manifest = DocToManifest(DocValue)
        DataValue = BuildFcstdArchive(
            Manifest,
            external_links=OuterLinks,
            native_external_links=NativeOuterLinks,
            document_timestamp=DocTimestamp,
            trusted_native_breps=TrustedNativeBreps,
        )
        PathValue = WriteBytes(Target, DataValue, ShouldOverwrite)
        if PathValue is not None and TimestampEpoch is not None:
            OsModule.utime(PathValue, (TimestampEpoch, TimestampEpoch))
        Transfers = CapabilityA(
            DocValue, TargetPath, Portable, False, TrustedNativeBreps
        )
        AppUsable = not CarrierOnlyReferences and IsNativeGeom(
            DocValue, TrustedNativeBreps
        )
        MetaValue = {
            "schema_version": DocValue.schema_version,
            "sketch_count": len(DocValue.sketches),
            "timeline_count": len(DocValue.feature_timeline),
            "native_payload_count": len(DocValue.brep_payloads),
            "assembly_occurrence_count": (
                len(DocValue.assembly.instances) if DocValue.assembly is not None else 0
            ),
            "assembly_mate_count": (
                len(DocValue.assembly.mates) if DocValue.assembly is not None else 0
            ),
            "component_file_count": len(OuterLinks),
            "component_bytes_written": ComponentBytesWritten,
            "external_document_file_count": len(NativeOuterLinks),
            "external_document_bytes_written": NativeOuterBytesWritten,
            "runtime": "python-stdlib",
            "recompute_required": True,
            "native_referenced_files_emitted": not CarrierOnlyReferences,
            "carrier_embedded_reference_count": len(NativeOuterDocuments)
            + (
                len(DocValue.assembly.documents) if DocValue.assembly is not None else 0
            ),
            "application_usable": AppUsable,
            "vendor_loadable": True,
        }
        Diagnostics = DocValue.diagnostics
        if CarrierOnlyReferences:
            Diagnostics = (
                *Diagnostics,
                DiagValue(
                    "freecad.references_embedded_without_files",
                    "Referenced documents are retained in the Kit carrier but cannot be exposed as native relative files from a stream destination",
                    Severity.WARNING,
                ),
            )
        return WriteResult(
            path=PathValue,
            adapter=Instance.info.format_id,
            bytes_written=len(DataValue),
            diagnostics=Diagnostics,
            metadata=MetaValue,
            transfers=Transfers,
            application_usable=AppUsable,
            vendor_loadable=True,
        )

    locals()["info"] = InfoAction
    locals()["probe"] = Probe
    locals()["read"] = ReadAction
    locals()["supports"] = CanSupport
    locals()["write"] = Write


# this definition exists because focused behavior needs one stable owner
def ExtractFreecad(Source: Source) -> dict[str, AnyValue]:
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
        DocValue, Target, WriteOptions(overwrite=Overwrite, validate=Validate)
    )


# this binding exists because shared behavior needs one stable value
globals()["Any"] = AnyValue

# this binding exists because shared behavior needs one stable value
globals()["CAPABILITY_CARRIER_REASONS"] = CapabilityCarrierReasons

# this binding exists because shared behavior needs one stable value
globals()["CadDocument"] = CadDoc

# this binding exists because shared behavior needs one stable value
globals()["Configuration"] = Config

# this binding exists because shared behavior needs one stable value
globals()["DOCUMENT_ENTRY"] = DocEntry

# this binding exists because shared behavior needs one stable value
globals()["Destination"] = Target

# this binding exists because shared behavior needs one stable value
globals()["Diagnostic"] = DiagValue

# this binding exists because shared behavior needs one stable value
globals()["ET"] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_WRITE_KINDS"] = FeatureWriteKinds

# this binding exists because shared behavior needs one stable value
globals()["FREECAD_BREP_FORMAT_IDS"] = FreecadBrepFormatIds

# this binding exists because shared behavior needs one stable value
globals()["FreeCADAdapter"] = FreeCadAdapter

# this binding exists because shared behavior needs one stable value
globals()["FreeCADAdapterError"] = FreeCadAdapterA

# this binding exists because shared behavior needs one stable value
globals()["FreeCADBrepWriteError"] = FreeCadBrepWriteError

# this binding exists because shared behavior needs one stable value
globals()["INFO"] = InfoValue

# this binding exists because shared behavior needs one stable value
globals()["MANIFEST_ENTRY"] = ManifestEntry

# this binding exists because shared behavior needs one stable value
globals()["MATE_WRITE_KINDS"] = MateWriteKinds

# this binding exists because shared behavior needs one stable value
globals()["Mesh"] = MeshValue

# this binding exists because shared behavior needs one stable value
globals()["NATIVE_DOCUMENT_SHA256_ATTRIBUTE"] = KNativeDocHashAttr

# this binding exists because shared behavior needs one stable value
globals()["NativeFreeCADError"] = NativeFreeCadError

# this binding exists because shared behavior needs one stable value
globals()["Path"] = FilePath

# this binding exists because shared behavior needs one stable value
globals()["SUFFIX"] = Suffix

# this binding exists because shared behavior needs one stable value
globals()["XML_TRUE_VALUES"] = XmlTrueValues

# this binding exists because shared behavior needs one stable value
globals()["_FEATURE_WRITE_VALUES"] = KFeatureWriteValues

# this binding exists because shared behavior needs one stable value
globals()["_MATE_WRITE_VALUES"] = KMateWriteValues

# this binding exists because shared behavior needs one stable value
globals()["_MAX_ENTRY_SIZE"] = MaxEntrySize

# this binding exists because shared behavior needs one stable value
globals()["_MAX_EXTERNAL_FILES"] = MaxOuterFiles

# this binding exists because shared behavior needs one stable value
globals()["_MAX_TOTAL_SIZE"] = MaxTotalSize

# this binding exists because shared behavior needs one stable value
globals()["_NATIVE_DOCUMENT_BINDING_ID"] = KNativeDocBindingId

# this binding exists because shared behavior needs one stable value
globals()["_NATIVE_DOCUMENT_ID"] = KNativeDocId

# this binding exists because shared behavior needs one stable value
globals()["_NATIVE_EXTRUSION_END_CONDITIONS"] = KNativeExtrusionEnd

# this binding exists because shared behavior needs one stable value
globals()["_REPLAY_SEMANTIC_ATTRIBUTE"] = KReplaySemanticAttr

# this binding exists because shared behavior needs one stable value
globals()["_annotate_native_sources"] = AnnotateNative

# this binding exists because shared behavior needs one stable value
globals()["_archive_member_data"] = ArchiveMember

# this binding exists because shared behavior needs one stable value
globals()["_bundle_timestamp"] = BundleTimestamp

# this binding exists because shared behavior needs one stable value
globals()["_capability_transfers"] = CapabilityA

# this binding exists because shared behavior needs one stable value
globals()["_carrier_reason"] = CarrierReasonA

# this binding exists because shared behavior needs one stable value
globals()["_component_document"] = ComponentDoc

# this binding exists because shared behavior needs one stable value
globals()["_component_paths"] = ComponentPaths

# this binding exists because shared behavior needs one stable value
globals()["_component_stem"] = ComponentStem

# this binding exists because shared behavior needs one stable value
globals()["_configuration_parts"] = ConfigParts

# this binding exists because shared behavior needs one stable value
globals()["_definition_sources"] = SourceKeys

# this binding exists because shared behavior needs one stable value
globals()["_destination_path"] = ResolveTarget

# this binding exists because shared behavior needs one stable value
globals()["_document_tree"] = DocTree

# this binding exists because shared behavior needs one stable value
globals()["_enum_text"] = EnumText

# this binding exists because shared behavior needs one stable value
globals()["_existing_timestamps"] = FileTimestamps

# this binding exists because shared behavior needs one stable value
globals()["_external_link_details"] = OuterLink

# this binding exists because shared behavior needs one stable value
globals()["_external_link_target"] = OuterLinkTarget

# this binding exists because shared behavior needs one stable value
globals()["_extrusion_is_native"] = IsExtrusion

# this binding exists because shared behavior needs one stable value
globals()["_feature_has_native_edges"] = HasFeatureEdges

# this binding exists because shared behavior needs one stable value
globals()["_feature_parts"] = FeatureParts

# this binding exists because shared behavior needs one stable value
globals()["_filtered_document"] = FilteredDoc

# this binding exists because shared behavior needs one stable value
globals()["_has_native_freecad_graph"] = HasNativeGraph

# this binding exists because shared behavior needs one stable value
globals()["_is_native_document"] = IsNativeDoc

# this binding exists because shared behavior needs one stable value
globals()["_is_native_document_binding"] = IsNativeDocA

# this binding exists because shared behavior needs one stable value
globals()["_is_native_envelope"] = IsNative

# this binding exists because shared behavior needs one stable value
globals()["_manifest_brep_payloads"] = ManifestBrep

# this binding exists because shared behavior needs one stable value
globals()["_manifest_document"] = ManifestDoc

# this binding exists because shared behavior needs one stable value
globals()["_manifest_native_brep_key"] = ManifestNativeBrepKey

# this binding exists because shared behavior needs one stable value
globals()["_mapped_external_documents"] = MappedOuter

# this binding exists because shared behavior needs one stable value
globals()["_matching_component_link"] = MatchLink

# this binding exists because shared behavior needs one stable value
globals()["_mate_parts"] = MateParts

# this binding exists because shared behavior needs one stable value
globals()["_mesh_component_document"] = MeshComponent

# this binding exists because shared behavior needs one stable value
globals()["_mesh_is_usable"] = IsMeshUsable

# this binding exists because shared behavior needs one stable value
globals()["_native_document_pair"] = NativeDocPair

# this binding exists because shared behavior needs one stable value
globals()["_native_document_sha256"] = NativeDocShaTwo

# this binding exists because shared behavior needs one stable value
globals()["_native_external_documents"] = NativeOuter

# this binding exists because shared behavior needs one stable value
globals()["_native_geometry_is_usable"] = IsNativeGeom

# this binding exists because shared behavior needs one stable value
globals()["_nested_external_links"] = OuterLinkMap

# this binding exists because shared behavior needs one stable value
globals()["_neutral_brep_is_native"] = IsNeutralBrep

# this binding exists because shared behavior needs one stable value
globals()["_parsed_timestamp"] = ParsedTimestamp

# this binding exists because shared behavior needs one stable value
globals()["_payload_is_exact_native_brep"] = IsExactPayload

# this binding exists because shared behavior needs one stable value
globals()["_payload_is_reattachable_brep"] = IsBrepPayload

# this binding exists because shared behavior needs one stable value
globals()["_payload_matches_native_archive"] = IsPayloadMatch

# this binding exists because shared behavior needs one stable value
globals()["_payload_native_brep"] = PayloadNative

# this binding exists because shared behavior needs one stable value
globals()["_selected_configurations"] = Selected

# this binding exists because shared behavior needs one stable value
globals()["_selected_meshes"] = ChooseMeshes

# this binding exists because shared behavior needs one stable value
globals()["_selection_parts"] = SelectionParts

# this binding exists because shared behavior needs one stable value
globals()["_semantic_digest"] = SemanticDigest

# this binding exists because shared behavior needs one stable value
globals()["_semantic_document"] = SemanticDoc

# this binding exists because shared behavior needs one stable value
globals()["_source_bytes"] = SourceBytes

# this binding exists because shared behavior needs one stable value
globals()["_source_path"] = SourcePath

# this binding exists because shared behavior needs one stable value
globals()["_transfer_mode"] = TransferModeA

# this binding exists because shared behavior needs one stable value
globals()["_trusted_native_breps"] = TrustedNative

# this binding exists because shared behavior needs one stable value
globals()["_unchanged_native_source"] = UnchangedNative

# this binding exists because shared behavior needs one stable value
globals()["_validated_archive_members"] = ValidatedArchiveMembers

# this binding exists because shared behavior needs one stable value
globals()["_validated_document_xml"] = ValidatedDocXml

# this binding exists because shared behavior needs one stable value
globals()["_write_bytes"] = WriteBytes

# this binding exists because shared behavior needs one stable value
globals()["_write_components"] = WriteComponents

# this binding exists because shared behavior needs one stable value
globals()["_write_native_external_documents"] = WriteNative

# this binding exists because shared behavior needs one stable value
globals()["_xml_bool"] = IsXmlBool

# this binding exists because shared behavior needs one stable value
globals()["_xml_element_data"] = XmlElemData

# this binding exists because shared behavior needs one stable value
globals()["_xml_link_list"] = XmlLinkList

# this binding exists because shared behavior needs one stable value
globals()["_xml_number"] = XmlNumber

# this binding exists because shared behavior needs one stable value
globals()["_xml_scale"] = XmlScale

# this binding exists because shared behavior needs one stable value
globals()["_xml_string"] = XmlString

# this binding exists because shared behavior needs one stable value
globals()["_xml_string_list"] = XmlStringList

# this binding exists because shared behavior needs one stable value
globals()["_xml_transform"] = XmlTransform

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["brep_model_brep"] = BrepModelBrep

# this binding exists because shared behavior needs one stable value
globals()["build_fcstd_archive"] = BuildFcstdArchive

# this binding exists because shared behavior needs one stable value
globals()["datetime"] = Datetime

# this binding exists because shared behavior needs one stable value
globals()["document_to_manifest"] = DocToManifest

# this binding exists because shared behavior needs one stable value
globals()["extract_freecad_manifest"] = ExtractFreecad

# this binding exists because shared behavior needs one stable value
globals()["extract_manifest_from_fcstd"] = ExtractManifestFromFcstd

# this binding exists because shared behavior needs one stable value
globals()["filter_document"] = FilterDoc

# this binding exists because shared behavior needs one stable value
globals()["frozen_mapping"] = FrozenMapping

# this binding exists because shared behavior needs one stable value
globals()["hashlib"] = Hashlib

# this binding exists because shared behavior needs one stable value
globals()["infer_capabilities"] = InferCapabilities

# this binding exists because shared behavior needs one stable value
globals()["io"] = IoStream

# this binding exists because shared behavior needs one stable value
globals()["is_binary_destination"] = IsBinaryTarget

# this binding exists because shared behavior needs one stable value
globals()["is_windows_device_name"] = IsWindowsDeviceName

# this binding exists because shared behavior needs one stable value
globals()["json"] = JsonValue

# this binding exists because shared behavior needs one stable value
globals()["math"] = MathValue

# this binding exists because shared behavior needs one stable value
globals()["native_expression_parts"] = NativeExpressionParts

# this binding exists because shared behavior needs one stable value
globals()["native_shape_feature_count"] = NativeShapeFeatureCount

# this binding exists because shared behavior needs one stable value
globals()["native_sketch_carrier_reasons"] = NativeSketchCarrier

# this binding exists because shared behavior needs one stable value
globals()["native_sketch_parts"] = NativeSketchParts

# this binding exists because shared behavior needs one stable value
globals()["os"] = OsModule

# this binding exists because shared behavior needs one stable value
globals()["probe_native_fcstd"] = ProbeNativeFcstd

# this binding exists because shared behavior needs one stable value
globals()["proven_ascii_brep"] = ProvenAsciiBrep

# this binding exists because shared behavior needs one stable value
globals()["re"] = RegexLib

# this binding exists because shared behavior needs one stable value
globals()["read_freecad"] = ReadFreecad

# this binding exists because shared behavior needs one stable value
globals()["read_native_fcstd"] = ReadNativeFcstd

# this binding exists because shared behavior needs one stable value
globals()["replace"] = Replace

# this binding exists because shared behavior needs one stable value
globals()["semantic_metadata"] = SemanticMeta

# this binding exists because shared behavior needs one stable value
globals()["source_payload_indexes"] = SourcePayloadIndexes

# this binding exists because shared behavior needs one stable value
globals()["suppress"] = Suppress

# this binding exists because shared behavior needs one stable value
globals()["tempfile"] = Tempfile

# this binding exists because shared behavior needs one stable value
globals()["timezone"] = Timezone

# this binding exists because shared behavior needs one stable value
globals()["write_freecad"] = WriteFreecad

# this binding exists because shared behavior needs one stable value
globals()["zipfile"] = Zipfile

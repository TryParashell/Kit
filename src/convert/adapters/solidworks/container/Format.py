# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from pathlib import PureWindowsPath
import re as RegexLib
from types import MappingProxyType
from typing import Iterable
from convert.adapters.base import AdapterInfo
from interchange import Capability

# this binding exists because shared behavior needs one stable value
KPartFormatId = "solidworks.sldprt"

# this binding exists because shared behavior needs one stable value
KAsmFormatId = "solidworks.sldasm"

# this binding exists because shared behavior needs one stable value
KDrawingFormatId = "solidworks.slddrw"

# this binding exists because shared behavior needs one stable value
KDrawingSuffix = ".slddrw"

# this binding exists because shared behavior needs one stable value
KDrawingFormatName = "SOLIDWORKS drawing"

# this binding exists because shared behavior needs one stable value
KFormatIdBySuffix = MappingProxyType(
    {".sldprt": KPartFormatId, ".sldasm": KAsmFormatId}
)

# this binding exists because shared behavior needs one stable value
KSuffixByFormatId = MappingProxyType(
    {FormatId: Suffix for Suffix, FormatId in KFormatIdBySuffix.items()}
)

# this binding exists because shared behavior needs one stable value
KPartSuffix = KSuffixByFormatId[KPartFormatId]

# this binding exists because shared behavior needs one stable value
KAsmSuffix = KSuffixByFormatId[KAsmFormatId]

# this binding exists because shared behavior needs one stable value
KFormatIds = tuple(KFormatIdBySuffix.values())

# this binding exists because shared behavior needs one stable value
KInfoValue = AdapterInfo(
    format_id=KPartFormatId,
    name="SOLIDWORKS",
    version="1.0",
    extensions=tuple(KFormatIdBySuffix),
    aliases=(KAsmFormatId,),
    capabilities=frozenset(Capability),
    media_types=("application/x-solidworks-part", "application/x-solidworks-assembly"),
    part_extensions=(KPartSuffix,),
    assembly_extensions=(KAsmSuffix,),
)

# this binding exists because shared behavior needs one stable value
KContainerVersions = frozenset({3, 4})

# this binding exists because shared behavior needs one stable value
KComponentTreeStream = "swXmlContents/COMPINSTANCETREE"

# this binding exists because shared behavior needs one stable value
KDisplayListsStream = "Contents/DisplayLists"

# this binding exists because shared behavior needs one stable value
KeywordsStream = "swXmlContents/KeyWords"

# this binding exists because shared behavior needs one stable value
KFeaturesStream = "swXmlContents/Features"

# this binding exists because shared behavior needs one stable value
KResolvedFeaturesStream = "Contents/Config-0-ResolvedFeatures"

# this binding exists because shared behavior needs one stable value
KConfigStream = "Contents/Config-0"

# this binding exists because shared behavior needs one stable value
KPartitionStream = "Contents/Config-0-Partition"

# this binding exists because shared behavior needs one stable value
KSolidworksStream = "Contents/SolidWorks"

# this binding exists because shared behavior needs one stable value
KitDocStream = "Kit/Interchange"

# this binding exists because shared behavior needs one stable value
KitNativeStream = "Kit/Native"

# this binding exists because shared behavior needs one stable value
KitResolvedStream = "Kit/ResolvedFeatures"

# this binding exists because shared behavior needs one stable value
KContentTypesStream = "[Content_Types].xml"

# this binding exists because shared behavior needs one stable value
KRelationshipsStream = "_rels/.rels"

# this binding exists because shared behavior needs one stable value
KMatesStreamName = "MatesList"

# this binding exists because shared behavior needs one stable value
KMatesStreamSuffix = f"-{KMatesStreamName}"

# this binding exists because shared behavior needs one stable value
KResolvedLanePrefix, KResolvedLaneSuffix = KResolvedFeaturesStream.split("0", 1)

# this binding exists because shared behavior needs one stable value
KResolvedFeaturesLane = RegexLib.compile(
    f"^{RegexLib.escape(KResolvedLanePrefix)}(\\d+){RegexLib.escape(KResolvedLaneSuffix)}$"
)

# this binding exists because shared behavior needs one stable value
KDrawingStreamTokens = frozenset(
    {"drsheet", "drview", "drawingsheet", "drawingview", "sheetformat"}
)

# this binding exists because shared behavior needs one stable value
KClassMarker = bytes.fromhex("ffff0100")

# this binding exists because shared behavior needs one stable value
KSerializedStringMarker = bytes.fromhex("fffeff")

# this binding exists because shared behavior needs one stable value
KDimensionScalarHeaders = (
    bytes.fromhex("0000000000000040ffffffff00000000fffeff000000"),
    bytes.fromhex("0000000000000040ffffffff000000000000"),
)

# this binding exists because shared behavior needs one stable value
KCanonicalPlaneFeatureTyA = "plane"

# this binding exists because shared behavior needs one stable value
KOfficialRefPlaneFeature = frozenset({"refplane"})

# this binding exists because shared behavior needs one stable value
KPlaneFeatureTypes = KOfficialRefPlaneFeature | {KCanonicalPlaneFeatureTyA}

# this binding exists because shared behavior needs one stable value
KSolidBodyFeatureTypes = frozenset({"featsolidbodyfolder", "solidbodyfolder"})


# this definition exists because focused behavior needs one stable owner
def DimensionScalar(
    DataValue: bytes, TextEnd: int, EndValue: int, *, TrailingBytes: int = 0
) -> int | None:
    for Header in KDimensionScalarHeaders:
        if DataValue[TextEnd : TextEnd + len(Header)] != Header:
            continue
        ValueOffset = TextEnd + len(Header)
        if ValueOffset + 8 + TrailingBytes <= EndValue:
            return ValueOffset
    return None


# keeps legacy callers compatible while internal identifiers follow current naming rules
def LegacyScalar(
    DataValue: bytes,
    TextEnd: int,
    EndValue: int,
    *,
    TrailingBytes: int = 0,
    **CompatArgs: int,
) -> int | None:
    LegacyKey = "trailing_bytes"
    UnknownKeys = CompatArgs.keys() - {LegacyKey}
    if UnknownKeys:
        UnknownKey = next(iter(UnknownKeys))
        raise TypeError(f"unexpected keyword argument {UnknownKey!r}")
    if LegacyKey in CompatArgs:
        TrailingBytes = CompatArgs[LegacyKey]
    return DimensionScalar(DataValue, TextEnd, EndValue, TrailingBytes=TrailingBytes)


# this definition exists because focused behavior needs one stable owner
def IsCadPath(Value: str) -> bool:
    return PureWindowsPath(Value).suffix.casefold() in KFormatIdBySuffix


# this definition exists because focused behavior needs one stable owner
def IsDrawingPath(Value: str) -> bool:
    return PureWindowsPath(Value).suffix.casefold() == KDrawingSuffix


# this definition exists because focused behavior needs one stable owner
def PartLaneNames(Names: Iterable[str]) -> tuple[str, ...]:
    return tuple(
        (NameValue for NameValue in Names if KResolvedFeaturesLane.fullmatch(NameValue))
    )


# this definition exists because focused behavior needs one stable owner
def DrawingStream(Names: Iterable[str]) -> tuple[str, ...]:
    return tuple(
        (
            NameValue
            for NameValue in Names
            if any((Token in NameValue.casefold() for Token in KDrawingStreamTokens))
        )
    )


# this definition exists because focused behavior needs one stable owner
def UnsupportedDoc(Names: Iterable[str]) -> str:
    Values = tuple(Names)
    if PartLaneNames(Values) or KComponentTreeStream in Values:
        return ""
    if DrawingStream(Values):
        return f"{KDrawingFormatName} content ({KDrawingFormatId}) is not supported; SOLIDWORKS reading requires a part or assembly container"
    return f"SOLIDWORKS container carries neither a part lane ({KResolvedFeaturesStream}) nor an assembly lane ({KComponentTreeStream})"


# this definition exists because focused behavior needs one stable owner
def IsComponentPath(Value: str) -> bool:
    if "^" in Value or IsCadPath(Value):
        return False
    Segments = Value.split("/")
    if not Segments:
        return False
    for Segment in Segments:
        if Segment.count("@") != 1:
            return False
        Instance, Owner = Segment.split("@", 1)
        if not Instance.strip() or not Owner.strip():
            return False
    return True


# this binding exists because shared behavior needs one stable value
ASSEMBLY_FORMAT_ID = KAsmFormatId

# this binding exists because shared behavior needs one stable value
ASSEMBLY_SUFFIX = KAsmSuffix

# this binding exists because shared behavior needs one stable value
CANONICAL_PLANE_FEATURE_TYPE = KCanonicalPlaneFeatureTyA

# this binding exists because shared behavior needs one stable value
CLASS_MARKER = KClassMarker

# this binding exists because shared behavior needs one stable value
COMPONENT_TREE_STREAM = KComponentTreeStream

# this binding exists because shared behavior needs one stable value
CONFIGURATION_STREAM = KConfigStream

# this binding exists because shared behavior needs one stable value
CONTAINER_VERSIONS = KContainerVersions

# this binding exists because shared behavior needs one stable value
CONTENT_TYPES_STREAM = KContentTypesStream

# this binding exists because shared behavior needs one stable value
DIMENSION_SCALAR_HEADERS = KDimensionScalarHeaders

# this binding exists because shared behavior needs one stable value
DISPLAY_LISTS_STREAM = KDisplayListsStream

# this binding exists because shared behavior needs one stable value
DRAWING_FORMAT_ID = KDrawingFormatId

# this binding exists because shared behavior needs one stable value
DRAWING_FORMAT_NAME = KDrawingFormatName

# this binding exists because shared behavior needs one stable value
DRAWING_STREAM_TOKENS = KDrawingStreamTokens

# this binding exists because shared behavior needs one stable value
DRAWING_SUFFIX = KDrawingSuffix

# this binding exists because shared behavior needs one stable value
FEATURES_STREAM = KFeaturesStream

# this binding exists because shared behavior needs one stable value
FORMAT_IDS = KFormatIds

# this binding exists because shared behavior needs one stable value
FORMAT_ID_BY_SUFFIX = KFormatIdBySuffix

# this binding exists because shared behavior needs one stable value
INFO = KInfoValue

# this binding exists because shared behavior needs one stable value
KEYWORDS_STREAM = KeywordsStream

# this binding exists because shared behavior needs one stable value
KIT_DOCUMENT_STREAM = KitDocStream

# this binding exists because shared behavior needs one stable value
KIT_NATIVE_STREAM = KitNativeStream

# this binding exists because shared behavior needs one stable value
KIT_RESOLVED_STREAM = KitResolvedStream

# this binding exists because shared behavior needs one stable value
MATES_STREAM_NAME = KMatesStreamName

# this binding exists because shared behavior needs one stable value
MATES_STREAM_SUFFIX = KMatesStreamSuffix

# this binding exists because shared behavior needs one stable value
OFFICIAL_REFERENCE_PLANE_FEATURE_TYPES = KOfficialRefPlaneFeature

# this binding exists because shared behavior needs one stable value
PARTITION_STREAM = KPartitionStream

# this binding exists because shared behavior needs one stable value
PART_FORMAT_ID = KPartFormatId

# this binding exists because shared behavior needs one stable value
PART_SUFFIX = KPartSuffix

# this binding exists because shared behavior needs one stable value
PLANE_FEATURE_TYPES = KPlaneFeatureTypes

# this binding exists because shared behavior needs one stable value
RELATIONSHIPS_STREAM = KRelationshipsStream

# this binding exists because shared behavior needs one stable value
RESOLVED_FEATURES_LANE = KResolvedFeaturesLane

# this binding exists because shared behavior needs one stable value
RESOLVED_FEATURES_STREAM = KResolvedFeaturesStream

# this binding exists because shared behavior needs one stable value
SERIALIZED_STRING_MARKER = KSerializedStringMarker

# this binding exists because shared behavior needs one stable value
SOLIDWORKS_STREAM = KSolidworksStream

# this binding exists because shared behavior needs one stable value
SOLID_BODY_FEATURE_TYPES = KSolidBodyFeatureTypes

# this binding exists because shared behavior needs one stable value
SUFFIX_BY_FORMAT_ID = KSuffixByFormatId

# this binding exists because shared behavior needs one stable value
_RESOLVED_LANE_PREFIX = KResolvedLanePrefix

# this binding exists because shared behavior needs one stable value
_RESOLVED_LANE_SUFFIX = KResolvedLaneSuffix

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
dimension_scalar_value_offset = LegacyScalar

# this binding exists because shared behavior needs one stable value
drawing_stream_names = DrawingStream

# this binding exists because shared behavior needs one stable value
is_cad_path = IsCadPath

# this binding exists because shared behavior needs one stable value
is_component_path = IsComponentPath

# this binding exists because shared behavior needs one stable value
is_drawing_path = IsDrawingPath

# this binding exists because shared behavior needs one stable value
part_lane_names = PartLaneNames

# this binding exists because shared behavior needs one stable value
re = RegexLib

# this binding exists because shared behavior needs one stable value
unsupported_document_reason = UnsupportedDoc

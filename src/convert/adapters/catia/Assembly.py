# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from collections import defaultdict as Defaultdict
from dataclasses import dataclass as Dataclass
import hashlib as Hashlib
import os as OsModule
from pathlib import Path as FilePath
import stat as StatValue
from typing import Callable, TypeGuard
from convert.adapters.base import ReadOptions
from interchange import (
    AssemblyData as AsmData,
    CadDocument as CadDoc,
    ComponentDefinition,
    ComponentDocument as ComponentDoc,
    ComponentInstance,
    ComponentKind,
    Diagnostic as DiagValue,
    Provenance,
    ProvenanceSpan,
    Severity,
    frozen_mapping as FrozenMapping,
)
from convert.adapters.catia.Container import (
    Cfv2Archive as CfvTwoArchive,
    Cfv2FormatError as CfvTwoFormatError,
    Cfv2Stream as CfvTwoStream,
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
KPartSuffix = SuffixByDocType[PartDocType]

# this binding exists because shared behavior needs one stable value
KProductSuffix = SuffixByDocType[ProductDocType]

# this binding exists because shared behavior needs one stable value
KProductMarker = b"ASMPRODUCT"

# this binding exists because shared behavior needs one stable value
KDefaultMaxFiles = 4096

# this binding exists because shared behavior needs one stable value
KDefaultMaxTotalBytes = 4 * 1024 * 1024 * 1024

# this binding exists because shared behavior needs one stable value
KDefaultMaxDepth = 8


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeProductD:
    value: str
    offset: int
    length: int
    encoding: str


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeProduct:
    definition_name: str
    instance_name: str
    definition_offset: int
    instance_offset: int
    definition_length: int
    instance_length: int
    reference_number: str


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeProductB:
    root_name: str
    stream_name: str
    stream_descriptor_offset: int
    table_offset: int
    tokens: tuple[NativeProductD, ...]
    occurrences: tuple[NativeProduct, ...]
    ambiguous_tokens: tuple[NativeProductD, ...]
    alternatives: tuple[NativeProductC, ...] = ()


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeProductC:
    root_name: str
    stream_name: str
    stream_descriptor_offset: int
    table_offset: int
    tokens: tuple[NativeProductD, ...]


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeProductA:
    name: str
    path: FilePath
    document_type: str
    sha256: str


# this binding exists because shared behavior needs one stable value
KComponentReader = Callable[[FilePath, ReadOptions], CadDoc]


# option tuple narrowing prevents dynamic extension values from leaking unknown element types
def IsObjectTuple(Value: object) -> TypeGuard[tuple[object, ...]]:
    return isinstance(Value, tuple)


# this definition exists because focused behavior needs one stable owner
def DecodeProductA(Archive: Cfv2Archive) -> NativeProductB:
    Candidates: list[tuple[CfvTwoStream, tuple[NativeProductD, ...]]] = []
    for Stream in Archive.outer.streams:
        DataValue = Archive.stream_bytes(Stream, Archive.outer)
        Tokens = ProductTokens(DataValue)
        if Tokens:
            Candidates.append((Stream, Tokens))
    if not Candidates:
        raise CfvTwoFormatError("CATIA product has no ASMPRODUCT table")

    # this callback exists because local behavior needs one focused transformation
    Candidates.sort(
        key=lambda ItemValue: (
            ItemValue[0].name != "Data",
            -len(ItemValue[1]),
            ItemValue[0].name.casefold(),
        )
    )
    Stream, Tokens = Candidates[0]
    if len(Tokens) < 2:
        raise CfvTwoFormatError("CATIA ASMPRODUCT table has no product name")
    Occurrences, AmbiguousTokens = Product(Tokens)
    Alternatives = tuple(
        (
            NativeProductC(
                root_name=Value[1][1].value,
                stream_name=Value[0].name,
                stream_descriptor_offset=Value[0].descriptor_offset,
                table_offset=Value[1][0].offset,
                tokens=Value[1],
            )
            for Value in Candidates[1:]
            if len(Value[1]) >= 2
        )
    )
    return NativeProductB(
        root_name=Tokens[1].value,
        stream_name=Stream.name,
        stream_descriptor_offset=Stream.descriptor_offset,
        table_offset=Tokens[0].offset,
        tokens=Tokens,
        occurrences=Occurrences,
        ambiguous_tokens=AmbiguousTokens,
        alternatives=Alternatives,
    )


# this definition exists because focused behavior needs one stable owner
def PhysicalSpans(
    Archive: Cfv2Archive,
    Table: NativeProductTable,
    LogicalOffset: int,
    Length: int,
    RecordKind: str,
) -> tuple[ProvenanceSpan, ...]:
    Stream = next(
        (
            ItemValue
            for ItemValue in Archive.outer.streams
            if ItemValue.descriptor_offset == Table.stream_descriptor_offset
        ),
        None,
    )
    if Stream is None:
        raise CfvTwoFormatError("CATIA product stream descriptor is unavailable")
    LogicalEnd = LogicalOffset + Length
    Spans: list[ProvenanceSpan] = []
    Covered = 0
    for Extent in Stream.extents:
        ExtentStart = Extent.logical_offset
        ExtentEnd = ExtentStart + Extent.physical_length
        OverlapStart = max(LogicalOffset, ExtentStart)
        OverlapEnd = min(LogicalEnd, ExtentEnd)
        if OverlapStart >= OverlapEnd:
            continue
        PhysicalOffset = (
            Archive.outer.physical_base
            + Extent.physical_offset
            + OverlapStart
            - ExtentStart
        )
        OverlapLength = OverlapEnd - OverlapStart
        Spans.append(
            ProvenanceSpan(Table.stream_name, PhysicalOffset, OverlapLength, RecordKind)
        )
        Covered += OverlapLength
    if Covered != Length:
        raise CfvTwoFormatError("CATIA product token crosses an unavailable extent")
    return tuple(Spans)


# this definition exists because focused behavior needs one stable owner
def NativeProductE(
    Archive: Cfv2Archive, Label: str, Settings: ReadOptions, Reader: ComponentReader
) -> tuple[AsmData, tuple[DiagValue, ...]]:
    Table = DecodeProductA(Archive)
    References, SearchDiagnostics = ComponentRef(Label, Settings)
    Selected, RefCandidates, RefDiagnostics = SelectRefs(Table, References)
    Documents, DocIds, DocDiagnostics = Component(
        Label, Table, Selected, Settings, Reader
    )
    DocumentsById = {ItemValue.id: ItemValue.document for ItemValue in Documents}
    RootId = "catia:assembly:root"
    RootPath = SourcePath(Label)
    Definitions: list[ComponentDefinition] = [
        ComponentDefinition(
            RootId,
            Table.root_name,
            ComponentKind.ASSEMBLY,
            source_path=str(RootPath) if RootPath is not None else Label,
            source_format_id=KFormatId,
            source_sha256=(
                Hashlib.sha256(Archive.data).hexdigest() if Archive.data else ""
            ),
            provenance=Provenance(
                KFormatId,
                "ASMPRODUCT",
                spans=PhysicalSpans(
                    Archive,
                    Table,
                    Table.tokens[1].offset,
                    Table.tokens[1].length,
                    "product-name",
                ),
            ),
            attributes=FrozenMapping(
                {
                    "native_structure": "ASMPRODUCT",
                    "native_string_table_logical_offset": Table.table_offset,
                    "native_string_table_physical_offset": PhysicalSpans(
                        Archive, Table, Table.table_offset, 1, "string-table-prefix"
                    )[0].offset,
                }
            ),
        )
    ]
    DefinitionIds: dict[str, str] = {}
    FirstOccurrences: dict[str, NativeProduct] = {}
    for ItemValue in Table.occurrences:
        FirstOccurrences.setdefault(ItemValue.definition_name, ItemValue)
    for DefinitionName in dict.fromkeys(
        (ItemValue.definition_name for ItemValue in Table.occurrences)
    ):
        DefinitionId = f"catia:definition:{len(DefinitionIds) + 1}"
        DefinitionIds[DefinitionName] = DefinitionId
        RefValue = Selected.get(DefinitionName)
        DocId = DocIds.get(DefinitionName, "")
        DocValue = DocumentsById.get(DocId)
        KindValue = (
            ComponentKind.ASSEMBLY
            if RefValue is not None and RefValue.document_type == ProductDocType
            else (
                ComponentKind.PART
                if RefValue is not None and RefValue.document_type == PartDocType
                else ComponentKind.REFERENCE
            )
        )
        Definitions.append(
            ComponentDefinition(
                DefinitionId,
                DefinitionName,
                KindValue,
                document_id=DocId,
                body_ids=(
                    tuple((BodyValue.id for BodyValue in DocValue.bodies))
                    if DocValue is not None and KindValue == ComponentKind.PART
                    else ()
                ),
                source_path=str(RefValue.path) if RefValue is not None else "",
                source_format_id=KFormatId if RefValue is not None else "",
                source_sha256=RefValue.sha256 if RefValue is not None else "",
                provenance=Provenance(
                    KFormatId,
                    DefinitionName,
                    spans=PhysicalSpans(
                        Archive,
                        Table,
                        FirstOccurrences[DefinitionName].definition_offset,
                        FirstOccurrences[DefinitionName].definition_length,
                        "component-definition",
                    ),
                ),
                attributes=FrozenMapping(
                    {
                        "native_reference_name": DefinitionName,
                        "source_resolved": RefValue is not None,
                        "source_ambiguous": len(RefCandidates.get(DefinitionName, ()))
                        > 1,
                        "native_reference_candidates": tuple(
                            (
                                {
                                    "path": str(Choice.path),
                                    "document_type": Choice.document_type,
                                    "sha256": Choice.sha256,
                                }
                                for Choice in RefCandidates.get(DefinitionName, ())
                            )
                        ),
                    }
                ),
            )
        )
    Instances = tuple(
        (
            ComponentInstance(
                f"catia:instance:{Order + 1}",
                ItemValue.instance_name,
                DefinitionIds[ItemValue.definition_name],
                RootId,
                order=Order,
                reference_number=ItemValue.reference_number,
                provenance=Provenance(
                    KFormatId,
                    ItemValue.instance_name,
                    spans=PhysicalSpans(
                        Archive,
                        Table,
                        ItemValue.instance_offset,
                        ItemValue.instance_length,
                        "component-instance",
                    ),
                ),
                attributes=FrozenMapping(
                    {
                        "native_definition_name": ItemValue.definition_name,
                        "native_string_logical_offset": ItemValue.instance_offset,
                        "native_string_physical_offset": PhysicalSpans(
                            Archive,
                            Table,
                            ItemValue.instance_offset,
                            ItemValue.instance_length,
                            "component-instance",
                        )[0].offset,
                        "transform_resolved": False,
                        "transform_source": "exact_native_payload",
                    }
                ),
            )
            for Order, ItemValue in enumerate(Table.occurrences)
        )
    )
    Diagnostics = ProductDiags(
        Table,
        DefinitionIds,
        Selected,
        Instances,
        (*SearchDiagnostics, *RefDiagnostics, *DocDiagnostics),
    )
    AsmValue = AsmData(
        root_definition_id=RootId,
        definitions=tuple(Definitions),
        instances=Instances,
        documents=Documents,
        attributes=FrozenMapping(
            {
                "native_structure": "ASMPRODUCT",
                "native_stream": Table.stream_name,
                "native_string_table_logical_offset": Table.table_offset,
                "native_string_table_physical_offset": PhysicalSpans(
                    Archive, Table, Table.table_offset, 1, "string-table-prefix"
                )[0].offset,
                "native_string_count": len(Table.tokens),
                "native_instance_count": len(Instances),
                "native_definition_count": len(DefinitionIds),
                "resolved_definition_count": len(Selected),
                "linked_document_count": len(Documents),
                "linked_sketch_count": sum(
                    (len(ItemValue.document.sketches) for ItemValue in Documents)
                ),
                "linked_feature_count": sum(
                    (
                        len(ItemValue.document.feature_timeline)
                        for ItemValue in Documents
                    )
                ),
                "transform_status": "native-only",
                "constraint_status": "native-only",
                "native_table_candidates": (
                    TableChoice(Table),
                    *(TableChoice(Choice) for Choice in Table.alternatives),
                ),
                "native_unresolved_tokens": tuple(
                    (TokenRecord(Token) for Token in Table.ambiguous_tokens)
                ),
                "native_reference_candidates": tuple(
                    (
                        {
                            "definition_name": NameValue,
                            "candidates": tuple(
                                (
                                    {
                                        "path": str(Choice.path),
                                        "document_type": Choice.document_type,
                                        "sha256": Choice.sha256,
                                    }
                                    for Choice in Candidates
                                )
                            ),
                        }
                        for NameValue, Candidates in RefCandidates.items()
                        if Candidates
                    )
                ),
            }
        ),
    )
    return (AsmValue, Diagnostics)


# this definition exists because focused behavior needs one stable owner
def ProductDiags(
    Table: NativeProductTable,
    DefinitionIds: dict[str, str],
    Selected: dict[str, NativeProductReference],
    Instances: tuple[ComponentInstance, ...],
    Initial: tuple[DiagValue, ...],
) -> tuple[DiagValue, ...]:
    Missing = tuple(
        NameValue for NameValue in DefinitionIds if NameValue not in Selected
    )
    Diagnostics = list(Initial)
    if Table.alternatives:
        Diagnostics.append(
            DiagValue(
                "catia.product.root_ambiguous",
                "Multiple CATIA product tables were retained; the deterministic Data-first table supplies normalized assembly semantics.",
                Severity.WARNING,
                attributes=FrozenMapping(
                    {
                        "selected": TableChoice(Table),
                        "alternatives": tuple(
                            (TableChoice(Choice) for Choice in Table.alternatives)
                        ),
                    }
                ),
            )
        )
    if Table.ambiguous_tokens:
        Diagnostics.append(
            DiagValue(
                "catia.product.native_tokens_retained",
                "CATIA product tokens without verified occurrence roles remain available as ordered native records.",
                Severity.INFO,
                attributes=FrozenMapping(
                    {
                        "tokens": tuple(
                            (TokenRecord(Token) for Token in Table.ambiguous_tokens)
                        )
                    }
                ),
            )
        )
    if Missing:
        Diagnostics.append(
            DiagValue(
                "catia.product.component_sources_missing",
                f"{len(Missing)} CATProduct component sources could not be resolved by internal product name.",
                Severity.INFO,
                attributes=FrozenMapping({"definition_names": Missing}),
            )
        )
    if Instances:
        Diagnostics.append(
            DiagValue(
                "catia.product.transforms_unresolved",
                "CATProduct occurrence order and names are decoded; proprietary position records remain byte-exact in the native payload and unresolved transforms retain the identity default.",
                Severity.WARNING,
                attributes=FrozenMapping(
                    {
                        "instance_count": len(Instances),
                        "resolved_count": 0,
                        "unresolved_default": "identity",
                    }
                ),
            )
        )
    Diagnostics.append(
        DiagValue(
            "catia.product.constraints_unresolved",
            "CATProduct connector and constraint records remain byte-exact in the native payload; no semantic mates are asserted without a verified decoder.",
            Severity.INFO,
        )
    )
    return tuple(Diagnostics)


# this definition exists because focused behavior needs one stable owner
def TokenRecord(Token: NativeProductToken) -> dict[str, object]:
    return {
        "value": Token.value,
        "offset": Token.offset,
        "length": Token.length,
        "encoding": Token.encoding,
    }


# this definition exists because focused behavior needs one stable owner
def TableChoice(
    Table: NativeProductTable | NativeProductTableCandidate,
) -> dict[str, object]:
    return {
        "root_name": Table.root_name,
        "stream_name": Table.stream_name,
        "stream_descriptor_offset": Table.stream_descriptor_offset,
        "table_offset": Table.table_offset,
        "tokens": tuple((TokenRecord(Token) for Token in Table.tokens)),
    }


# this definition exists because focused behavior needs one stable owner
def ProductTokens(DataValue: bytes) -> tuple[NativeProductD, ...]:
    Marker = DataValue.find(KProductMarker)
    if Marker < 1 or DataValue[Marker - 1] != len(KProductMarker) + 1:
        return ()
    Cursor = Marker - 1
    Result: list[NativeProductD] = []
    while Cursor < len(DataValue):
        StoredLength = DataValue[Cursor]
        Length = StoredLength - 1
        EndValue = Cursor + 1 + Length
        if Length < 1 or EndValue > len(DataValue):
            break
        RawValue = DataValue[Cursor + 1 : EndValue]
        Value, Encoding = DecodeProduct(RawValue)
        Result.append(NativeProductD(Value, Cursor + 1, Length, Encoding))
        Cursor = EndValue
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def DecodeProduct(RawValue: bytes) -> tuple[str, str]:
    if RawValue.startswith((b"\xff\xfe", b"\xfe\xff")):
        Decoded = DecodedText(RawValue, "utf-16")
        if Decoded is not None:
            return (Decoded, "utf-16")
    if len(RawValue) >= 2 and len(RawValue) % 2 == 0:
        Pairs = len(RawValue) // 2
        LittleZeroes = sum(
            (RawValue[Index] == 0 for Index in range(1, len(RawValue), 2))
        )
        BigZeroes = sum((RawValue[Index] == 0 for Index in range(0, len(RawValue), 2)))
        if LittleZeroes * 2 >= Pairs:
            Decoded = DecodedText(RawValue, "utf-16le")
            if Decoded is not None:
                return (Decoded, "utf-16le")
        if BigZeroes * 2 >= Pairs:
            Decoded = DecodedText(RawValue, "utf-16be")
            if Decoded is not None:
                return (Decoded, "utf-16be")
    Decoded = DecodedText(RawValue, "utf-8")
    return (
        (Decoded, "utf-8")
        if Decoded is not None
        else (RawValue.decode("latin-1"), "latin-1")
    )


# this definition exists because focused behavior needs one stable owner
def DecodedText(RawValue: bytes, Encoding: str) -> str | None:
    try:
        return RawValue.decode(Encoding)
    except UnicodeDecodeError:
        return None


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class ProductState:
    Result: list[NativeProduct]
    UsedValue: set[int]
    CurrentDefinition: int | None
    DefinitionsByInstanceKey: dict[str, int]
    Pending: int | None


# this definition exists because focused behavior needs one stable owner
def Product(
    Tokens: tuple[NativeProductToken, ...],
) -> tuple[tuple[NativeProduct, ...], tuple[NativeProductD, ...]]:
    Values = tuple(Token.value for Token in Tokens)
    try:
        Start = Values.index("_Reps") + 1
    except ValueError as ErrorInfo:
        raise CfvTwoFormatError(
            "CATIA ASMPRODUCT table has no _Reps boundary"
        ) from ErrorInfo
    Terminal = next(
        (
            Index
            for Index in range(Start, len(Tokens))
            if Tokens[Index].value == "IsRoot"
        ),
        len(Tokens),
    )
    State = ProductState([], set(), None, {}, None)
    PoolStart = InitProductMut(Tokens, Start, Terminal, State)
    ScanProductMut(Tokens, PoolStart, Terminal, State)
    TailProductMut(Tokens, Start, Terminal, State)
    Ambiguous = tuple(
        Token
        for Index, Token in enumerate(Tokens)
        if Index >= Start and Index not in State.UsedValue
    )
    return (tuple(State.Result), Ambiguous)


# this definition exists because focused behavior needs one stable owner
def AddProductMut(
    Tokens: tuple[NativeProductToken, ...],
    DefinitionIndex: int,
    InstanceIndex: int,
    RefValue: str,
    State: ProductState,
) -> None:
    Definition = Tokens[DefinitionIndex]
    Instance = Tokens[InstanceIndex]
    State.Result.append(
        NativeProduct(
            Definition.value,
            Instance.value,
            Definition.offset,
            Instance.offset,
            Definition.length,
            Instance.length,
            RefValue,
        )
    )
    State.UsedValue.update((DefinitionIndex, InstanceIndex))


# this definition exists because focused behavior needs one stable owner
def InitProductMut(
    Tokens: tuple[NativeProductToken, ...],
    Start: int,
    Terminal: int,
    State: ProductState,
) -> int:
    Marker = next(
        (
            Index
            for Index in range(Start + 1, Terminal)
            if Tokens[Index].value == "_InstanceName"
        ),
        None,
    )
    if Marker is None or Marker + 1 >= Terminal:
        return Start
    Identity = Numbered(Tokens[Marker + 1].value)
    AddProductMut(Tokens, Start, Marker + 1, Identity[1] if Identity else "", State)
    if Identity is not None:
        State.DefinitionsByInstanceKey[Identity[0]] = Start
    State.CurrentDefinition = Start
    Shape = next(
        (
            Index
            for Index in range(Marker + 2, Terminal)
            if Tokens[Index].value == "Shape 1"
        ),
        Marker + 1,
    )
    return Shape + 1


# this definition exists because focused behavior needs one stable owner
def ScanProductMut(
    Tokens: tuple[NativeProductToken, ...],
    PoolStart: int,
    Terminal: int,
    State: ProductState,
) -> None:
    for Index in range(PoolStart, Terminal):
        if Index in State.UsedValue:
            continue
        Identity = Numbered(Tokens[Index].value)
        if Identity is not None:
            AddNumberedMut(Tokens, Index, Identity, State)
            continue
        if Tokens[Index].value == "_InstanceName" and State.Pending is not None:
            AddNamedMut(Tokens, Index, Terminal, State)
            continue
        State.Pending = Index


# this definition exists because focused behavior needs one stable owner
def AddNumberedMut(
    Tokens: tuple[NativeProductToken, ...],
    Index: int,
    Identity: tuple[str, str],
    State: ProductState,
) -> None:
    InstanceKey, RefValue = Identity
    Established = State.DefinitionsByInstanceKey.get(InstanceKey)
    if State.Pending is not None:
        State.CurrentDefinition = State.Pending
        State.DefinitionsByInstanceKey[InstanceKey] = State.Pending
        State.Pending = None
    elif Established is not None:
        State.CurrentDefinition = Established
    if State.CurrentDefinition is not None:
        AddProductMut(Tokens, State.CurrentDefinition, Index, RefValue, State)


# this definition exists because focused behavior needs one stable owner
def AddNamedMut(
    Tokens: tuple[NativeProductToken, ...],
    Index: int,
    Terminal: int,
    State: ProductState,
) -> None:
    InstanceIndex = Index + 1
    if InstanceIndex >= Terminal or State.Pending is None:
        return
    Identity = Numbered(Tokens[InstanceIndex].value)
    AddProductMut(
        Tokens,
        State.Pending,
        InstanceIndex,
        Identity[1] if Identity is not None else "",
        State,
    )
    if Identity is not None:
        State.DefinitionsByInstanceKey[Identity[0]] = State.Pending
    State.CurrentDefinition = State.Pending
    State.Pending = None


# this definition exists because focused behavior needs one stable owner
def TailProductMut(
    Tokens: tuple[NativeProductToken, ...],
    Start: int,
    Terminal: int,
    State: ProductState,
) -> None:
    if Terminal < Start + 3:
        return
    Ordinal, Definition, Instance = range(Terminal - 3, Terminal)
    if Tokens[Ordinal].value.isdecimal() and Definition not in State.UsedValue:
        if Instance not in State.UsedValue:
            AddProductMut(Tokens, Definition, Instance, Tokens[Ordinal].value, State)


# this definition exists because focused behavior needs one stable owner
def Numbered(Value: str) -> tuple[str, str] | None:
    Identity, Separator, RefValue = Value.rpartition(".")
    if not Identity or not Separator or (not RefValue.isdecimal()):
        return None
    if Identity.startswith("I_"):
        Identity = Identity[2:]
    return (Identity, RefValue)


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class SearchState:
    References: Defaultdict[str, list[NativeProductA]]
    Diagnostics: list[DiagValue]
    FileCount: int
    TotalBytes: int
    LimitName: str | None


# this definition exists because focused behavior needs one stable owner
def ComponentRef(
    Label: str, Settings: ReadOptions
) -> tuple[dict[str, tuple[NativeProductA, ...]], tuple[DiagValue, ...]]:
    if Settings.values.get("resolve_components", True) is False:
        return ({}, ())
    MaxFiles = SearchLimit(Settings, "component_search_max_files", KDefaultMaxFiles)
    MaxTotalBytes = SearchLimit(
        Settings, "component_search_max_total_bytes", KDefaultMaxTotalBytes
    )
    MaxDepth = SearchLimit(
        Settings, "component_search_max_depth", KDefaultMaxDepth, AllowZero=True
    )
    Roots, RootDiagnostics = ComponentSearch(Label, Settings)
    State = SearchState(Defaultdict(list), list(RootDiagnostics), 0, 0, None)
    for RootValue in Roots:
        ScanRootMut(RootValue, MaxDepth, MaxFiles, MaxTotalBytes, State)
        if State.LimitName is not None:
            break
    if State.LimitName is not None:
        State.Diagnostics.append(
            DiagValue(
                "catia.product.component_search_limit",
                f"CATIA component discovery stopped at the configured {State.LimitName} limit.",
                Severity.WARNING,
                attributes=FrozenMapping(
                    {
                        "limit": State.LimitName,
                        "files": State.FileCount,
                        "total_bytes": State.TotalBytes,
                        "max_files": MaxFiles,
                        "max_total_bytes": MaxTotalBytes,
                        "max_depth": MaxDepth,
                    }
                ),
            )
        )

    # this callback exists because local behavior needs one focused transformation
    return (
        {
            NameValue: tuple(
                sorted(
                    Values,
                    key=lambda ItemValue: (
                        str(ItemValue.path).casefold(),
                        str(ItemValue.path),
                    ),
                )
            )
            for NameValue, Values in State.References.items()
        },
        tuple(State.Diagnostics),
    )


# this definition exists because focused behavior needs one stable owner
def ScanRootMut(
    RootValue: FilePath,
    MaxDepth: int,
    MaxFiles: int,
    MaxTotalBytes: int,
    State: SearchState,
) -> None:
    Pending: list[tuple[FilePath, int]] = [(RootValue, 0)]
    while Pending and State.LimitName is None:
        Folder, Depth = Pending.pop(0)
        Entries, Diagnostic = FolderEntries(Folder)
        if Diagnostic is not None:
            State.Diagnostics.append(Diagnostic)
        for PathValue in Entries:
            VisitPathMut(
                PathValue,
                RootValue,
                Depth,
                Pending,
                MaxDepth,
                MaxFiles,
                MaxTotalBytes,
                State,
            )
            if State.LimitName is not None:
                break


# this definition exists because focused behavior needs one stable owner
def FolderEntries(
    Folder: FilePath,
) -> tuple[tuple[FilePath, ...], DiagValue | None]:
    try:

        # this callback exists because local behavior needs one focused transformation
        Entries = tuple(
            sorted(
                Folder.iterdir(),
                key=lambda ItemValue: (ItemValue.name.casefold(), ItemValue.name),
            )
        )
    except OSError as ErrorInfo:
        return ((), SearchDiag(Folder, "unreadable_directory", str(ErrorInfo)))
    return (Entries, None)


# this definition exists because focused behavior needs one stable owner
def VisitPathMut(
    PathValue: FilePath,
    RootValue: FilePath,
    Depth: int,
    Pending: list[tuple[FilePath, int]],
    MaxDepth: int,
    MaxFiles: int,
    MaxTotalBytes: int,
    State: SearchState,
) -> None:
    if IsReparsePoint(PathValue):
        State.Diagnostics.append(SearchDiag(PathValue, "reparse_point"))
        return
    try:
        if PathValue.is_dir():
            VisitFolderMut(PathValue, RootValue, Depth, Pending, MaxDepth, State)
            return
        if (
            not PathValue.is_file()
            or PathValue.suffix.casefold() not in DocTypeBySuffix
        ):
            return
        Resolved = PathValue.resolve(strict=True)
        if not IsUnderRoot(Resolved, RootValue):
            State.Diagnostics.append(SearchDiag(PathValue, "root_escape"))
            return
        SizeValue = Resolved.stat().st_size
    except OSError as ErrorInfo:
        State.Diagnostics.append(
            SearchDiag(PathValue, "unreadable_candidate", str(ErrorInfo))
        )
        return
    if State.FileCount >= MaxFiles:
        State.LimitName = "files"
        return
    if SizeValue > MaxTotalBytes - State.TotalBytes:
        State.LimitName = "total_bytes"
        return
    State.FileCount += 1
    State.TotalBytes += SizeValue
    Loaded = LoadReference(Resolved)
    if Loaded is not None:
        NameValue, Reference = Loaded
        State.References[NameValue].append(Reference)


# this definition exists because focused behavior needs one stable owner
def VisitFolderMut(
    PathValue: FilePath,
    RootValue: FilePath,
    Depth: int,
    Pending: list[tuple[FilePath, int]],
    MaxDepth: int,
    State: SearchState,
) -> None:
    if Depth >= MaxDepth:
        State.LimitName = "depth"
        return
    Resolved = PathValue.resolve(strict=True)
    if not IsUnderRoot(Resolved, RootValue):
        State.Diagnostics.append(SearchDiag(PathValue, "root_escape"))
        return
    Pending.append((Resolved, Depth + 1))


# this definition exists because focused behavior needs one stable owner
def LoadReference(
    Resolved: FilePath,
) -> tuple[str, NativeProductA] | None:
    try:
        DataValue = Resolved.read_bytes()
        Archive = CfvTwoArchive.from_bytes(DataValue)
        Table = DecodeProductA(Archive)
    except (CfvTwoFormatError, OSError, UnicodeDecodeError, ValueError):
        return None
    Reference = NativeProductA(
        Table.root_name,
        Resolved,
        DocTypeBySuffix[Resolved.suffix.casefold()],
        Hashlib.sha256(DataValue).hexdigest(),
    )
    return (Table.root_name, Reference)


# this definition exists because focused behavior needs one stable owner
def ComponentSearch(
    Label: str, Settings: ReadOptions
) -> tuple[tuple[FilePath, ...], tuple[DiagValue, ...]]:
    Candidates = SearchRoots(Label, Settings)
    if not Candidates:
        return ((), ())
    Roots: list[FilePath] = []
    Diagnostics: list[DiagValue] = []
    SeenValue: set[str] = set()
    for Choice in Candidates:
        if IsReparsePoint(Choice):
            Diagnostics.append(SearchDiag(Choice, "reparse_root"))
            continue
        try:
            Resolved = Choice.resolve(strict=True)
        except OSError as ErrorInfo:
            Diagnostics.append(SearchDiag(Choice, "unavailable_root", str(ErrorInfo)))
            continue
        if not Resolved.is_dir():
            Diagnostics.append(SearchDiag(Resolved, "root_is_not_directory"))
            continue
        KeyValue = OsModule.path.normcase(str(Resolved))
        if KeyValue not in SeenValue:
            SeenValue.add(KeyValue)
            Roots.append(Resolved)
    return (tuple(Roots), tuple(Diagnostics))


# this definition exists because focused behavior needs one stable owner
def SearchRoots(Label: str, Settings: ReadOptions) -> tuple[FilePath, ...]:
    Requested = Settings.values.get("component_search_root")
    if Requested:
        return (FilePath(str(Requested)).expanduser(),)
    Source = SourcePath(Label)
    if Source is None:
        return ()
    Candidates: tuple[FilePath, ...] = (Source.parent,)
    if Source.parent.name.casefold() in {
        KProductSuffix,
        KProductSuffix.removeprefix("."),
    }:
        Candidates = (*Candidates, Source.parent.parent / f".{PartDocType}")
    return Candidates


# this definition exists because focused behavior needs one stable owner
def SearchLimit(
    Settings: ReadOptions, NameValue: str, Default: int, *, AllowZero: bool = False
) -> int:
    Value = Settings.values.get(NameValue, Default)
    if isinstance(Value, bool) or not isinstance(Value, int):
        raise ValueError(f"{NameValue} must be an integer")
    Parsed = Value
    Minimum = 0 if AllowZero else 1
    if Parsed < Minimum:
        raise ValueError(f"{NameValue} must be at least {Minimum}")
    return Parsed


# this definition exists because focused behavior needs one stable owner
def IsReparsePoint(PathValue: FilePath) -> bool:
    try:
        Value = PathValue.lstat()
    except OSError:
        return False
    Attributes = getattr(Value, "st_file_attributes", 0)
    ReparseFlag = getattr(StatValue, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return PathValue.is_symlink() or bool(Attributes & ReparseFlag)


# this definition exists because focused behavior needs one stable owner
def IsUnderRoot(PathValue: FilePath, RootValue: FilePath) -> bool:
    try:
        PathValue.relative_to(RootValue)
    except ValueError:
        return False
    return True


# this definition exists because focused behavior needs one stable owner
def SearchDiag(PathValue: FilePath, Reason: str, Detail: str = "") -> DiagValue:
    return DiagValue(
        "catia.product.component_search_rejected",
        f"CATIA component discovery rejected {PathValue}: {Reason}.",
        Severity.INFO,
        attributes=FrozenMapping(
            {"path": str(PathValue), "reason": Reason, "detail": Detail}
        ),
    )


# this definition exists because focused behavior needs one stable owner
def SelectRefs(
    Table: NativeProductTable, References: dict[str, tuple[NativeProductReference, ...]]
) -> tuple[
    dict[str, NativeProductA],
    dict[str, tuple[NativeProductA, ...]],
    tuple[DiagValue, ...],
]:
    Selected: dict[str, NativeProductA] = {}
    Retained: dict[str, tuple[NativeProductA, ...]] = {}
    Diagnostics: list[DiagValue] = []
    for NameValue in dict.fromkeys(
        (ItemValue.definition_name for ItemValue in Table.occurrences)
    ):
        Candidates = References.get(NameValue, ())
        if not Candidates:
            continue

        # this callback exists because local behavior needs one focused transformation
        Ordered = sorted(
            Candidates,
            key=lambda ItemValue: (str(ItemValue.path).casefold(), str(ItemValue.path)),
        )
        Retained[NameValue] = tuple(Ordered)
        if len(Ordered) == 1:
            Selected[NameValue] = Ordered[0]
        else:
            Diagnostics.append(
                DiagValue(
                    "catia.product.component_source_ambiguous",
                    f"Multiple CATIA documents declare product name {NameValue!r}; no source was selected without unique structural identity.",
                    Severity.WARNING,
                    attributes=FrozenMapping(
                        {
                            "definition_name": NameValue,
                            "selected": "",
                            "candidates": tuple(
                                (str(ItemValue.path) for ItemValue in Ordered)
                            ),
                        }
                    ),
                )
            )
    return (Selected, Retained, tuple(Diagnostics))


# this definition exists because focused behavior needs one stable owner
def Component(
    Label: str,
    Table: NativeProductTable,
    References: dict[str, NativeProductReference],
    Settings: ReadOptions,
    Reader: ComponentReader,
) -> tuple[tuple[ComponentDoc, ...], dict[str, str], tuple[DiagValue, ...]]:
    _, _, Active, Options = ReadContext(Label, Settings)
    Documents: list[ComponentDoc] = []
    DocIdsByPath: dict[FilePath, str] = {}
    DocIdsByName: dict[str, str] = {}
    Diagnostics: list[DiagValue] = []
    Names = dict.fromkeys(
        (ItemValue.definition_name for ItemValue in Table.occurrences)
    )
    for NameValue in Names:
        RefValue = References.get(NameValue)
        if RefValue is None:
            continue
        if str(RefValue.path).casefold() in Active:
            Diagnostics.append(
                DiagValue(
                    "catia.product.component_cycle",
                    f"Recursive CATIA product reference was not expanded: {RefValue.path}",
                    Severity.WARNING,
                )
            )
            continue
        Existing = DocIdsByPath.get(RefValue.path)
        if Existing is not None:
            DocIdsByName[NameValue] = Existing
            continue
        DocValue, Diagnostic = LoadComponent(NameValue, RefValue, Options, Reader)
        if Diagnostic is not None:
            Diagnostics.append(Diagnostic)
        if DocValue is None:
            continue
        DocId = f"catia:document:{DocValue.source.sha256[:20]}"
        Documents.append(ComponentDoc(DocId, DocValue))
        DocIdsByPath[RefValue.path] = DocId
        DocIdsByName[NameValue] = DocId
    return (tuple(Documents), DocIdsByName, tuple(Diagnostics))


# this definition exists because focused behavior needs one stable owner
def ReadContext(
    Label: str, Settings: ReadOptions
) -> tuple[FilePath | None, tuple[str, ...], set[str], ReadOptions]:
    Source = SourcePath(Label)
    StackValue = Settings.values.get("catia_path_stack", ())
    if not IsObjectTuple(StackValue):
        raise ValueError("catia path stack must be a tuple")
    StackItems: list[str] = []
    for PathValue in StackValue:
        if not isinstance(PathValue, str):
            raise ValueError("catia path stack entries must be strings")
        StackItems.append(PathValue)
    Stack = tuple(StackItems)
    Active = {Value.casefold() for Value in Stack}
    if Source is not None:
        Active.add(str(Source).casefold())
    return (Source, Stack, Active, NestedOptions(Settings, Stack, Source))


# this definition exists because focused behavior needs one stable owner
def NestedOptions(
    Settings: ReadOptions, Stack: tuple[str, ...], Source: FilePath | None
) -> ReadOptions:
    Values = dict(Settings.values)
    Values["catia_path_stack"] = (
        *Stack,
        *((str(Source),) if Source is not None else ()),
    )
    return ReadOptions(
        configuration=Settings.configuration,
        include_brep=Settings.include_brep,
        include_tessellation=Settings.include_tessellation,
        strict=Settings.strict,
        values=FrozenMapping(Values),
    )


# this definition exists because focused behavior needs one stable owner
def LoadComponent(
    NameValue: str,
    Reference: NativeProductReference,
    Options: ReadOptions,
    Reader: ComponentReader,
) -> tuple[CadDocument | None, DiagValue | None]:
    try:
        DocValue = Reader(Reference.path, Options)
    except (CfvTwoFormatError, OSError, TypeError, ValueError) as ErrorInfo:
        return (
            None,
            DiagValue(
                "catia.product.component_decode_failed",
                f"CATIA component could not be decoded: {Reference.path}: {ErrorInfo}",
                Severity.WARNING,
                attributes=FrozenMapping({"definition_name": NameValue}),
            ),
        )
    if DocValue.source.sha256.casefold() == Reference.sha256.casefold():
        return (DocValue, None)
    return (
        None,
        DiagValue(
            "catia.product.component_source_changed",
            f"CATIA component changed after discovery and was not linked: {Reference.path}",
            Severity.WARNING,
            attributes=FrozenMapping(
                {
                    "definition_name": NameValue,
                    "indexed_sha256": Reference.sha256,
                    "decoded_sha256": DocValue.source.sha256,
                }
            ),
        ),
    )


# this definition exists because focused behavior needs one stable owner
def SourcePath(Label: str) -> FilePath | None:
    if Label == "<memory>":
        return None
    PathValue = FilePath(Label).expanduser()
    return PathValue.resolve() if PathValue.is_file() else None


# this binding exists because shared behavior needs one stable value
AssemblyData = AsmData

# this binding exists because shared behavior needs one stable value
CadDocument = CadDoc

# this binding exists because shared behavior needs one stable value
Cfv2Archive = CfvTwoArchive

# this binding exists because shared behavior needs one stable value
Cfv2FormatError = CfvTwoFormatError

# this binding exists because shared behavior needs one stable value
Cfv2Stream = CfvTwoStream

# this binding exists because shared behavior needs one stable value
ComponentDocument = ComponentDoc

# this binding exists because shared behavior needs one stable value
ComponentReader = KComponentReader

# this binding exists because shared behavior needs one stable value
DOCUMENT_TYPE_BY_SUFFIX = DocTypeBySuffix

# this binding exists because shared behavior needs one stable value
Diagnostic = DiagValue

# this binding exists because shared behavior needs one stable value
INFO = InfoValue

# this binding exists because shared behavior needs one stable value
NativeProductOccurrence = NativeProduct

# this binding exists because shared behavior needs one stable value
NativeProductReference = NativeProductA

# this binding exists because shared behavior needs one stable value
NativeProductTable = NativeProductB

# this binding exists because shared behavior needs one stable value
NativeProductTableCandidate = NativeProductC

# this binding exists because shared behavior needs one stable value
NativeProductToken = NativeProductD

# this binding exists because shared behavior needs one stable value
PART_DOCUMENT_TYPE = PartDocType

# this binding exists because shared behavior needs one stable value
PRODUCT_DOCUMENT_TYPE = ProductDocType

# this binding exists because shared behavior needs one stable value
Path = FilePath

# this binding exists because shared behavior needs one stable value
SUFFIX_BY_DOCUMENT_TYPE = SuffixByDocType

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
dataclass = Dataclass

# this binding exists because shared behavior needs one stable value
decode_product_table = DecodeProductA

# this binding exists because shared behavior needs one stable value
defaultdict = Defaultdict

# this binding exists because shared behavior needs one stable value
frozen_mapping = FrozenMapping

# this binding exists because shared behavior needs one stable value
hashlib = Hashlib

# this binding exists because shared behavior needs one stable value
native_product_assembly = NativeProductE

# this binding exists because shared behavior needs one stable value
os = OsModule

# this binding exists because shared behavior needs one stable value
stat = StatValue

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Callable

from convert.adapters.base import ReadOptions
from interchange import (
    AssemblyData,
    CadDocument,
    ComponentDefinition,
    ComponentDocument,
    ComponentInstance,
    ComponentKind,
    Diagnostic,
    Provenance,
    ProvenanceSpan,
    Severity,
    frozen_mapping,
)

from .container import Cfv2Archive, Cfv2FormatError


_FORMAT_ID = "catia.v5"
_PRODUCT_MARKER = b"ASMPRODUCT"
_INSTANCE = re.compile(r"(?:I_)?(.+)\.(\d+)")
_TRAILING_VARIANT = re.compile(r"(?:_| )\d+$")
_SPACE_NUMBER = re.compile(r"(.+ )([0-9]+)$")
_NON_COMPONENT_VALUES = frozenset(
    {
        "3DIC",
        "FromCATPart",
        "IsRoot",
        "PRDBAGREP",
        "PRDREP",
        "Shape 1",
        "VPGlobal",
    }
)


@dataclass(frozen=True, slots=True)
class NativeProductToken:
    value: str
    offset: int
    length: int


@dataclass(frozen=True, slots=True)
class NativeProductOccurrence:
    definition_name: str
    instance_name: str
    definition_offset: int
    instance_offset: int
    reference_number: str


@dataclass(frozen=True, slots=True)
class NativeProductTable:
    root_name: str
    stream_name: str
    table_offset: int
    tokens: tuple[NativeProductToken, ...]
    occurrences: tuple[NativeProductOccurrence, ...]


@dataclass(frozen=True, slots=True)
class NativeProductReference:
    name: str
    path: Path
    document_type: str
    sha256: str


ComponentReader = Callable[[Path, ReadOptions], CadDocument]


def decode_product_table(archive: Cfv2Archive) -> NativeProductTable:
    candidates: list[tuple[str, tuple[NativeProductToken, ...]]] = []
    for stream in archive.outer.streams:
        data = archive.stream_bytes(stream, archive.outer)
        tokens = _product_tokens(data)
        if tokens:
            candidates.append((stream.name, tokens))
    if not candidates:
        raise Cfv2FormatError("CATIA product has no ASMPRODUCT table")
    candidates.sort(
        key=lambda item: (
            item[0] != "Data",
            -len(item[1]),
            item[0].casefold(),
        )
    )
    stream_name, tokens = candidates[0]
    if len(tokens) < 2:
        raise Cfv2FormatError("CATIA ASMPRODUCT table has no product name")
    occurrences = _product_occurrences(tokens)
    return NativeProductTable(
        root_name=tokens[1].value,
        stream_name=stream_name,
        table_offset=tokens[0].offset,
        tokens=tokens,
        occurrences=occurrences,
    )


def native_product_assembly(
    archive: Cfv2Archive,
    label: str,
    settings: ReadOptions,
    reader: ComponentReader,
) -> tuple[AssemblyData, tuple[Diagnostic, ...]]:
    table = decode_product_table(archive)
    references = _component_reference_index(label, settings)
    selected, reference_diagnostics = _selected_references(table, references)
    documents, document_ids, document_diagnostics = _component_documents(
        label,
        table,
        selected,
        settings,
        reader,
    )
    documents_by_id = {item.id: item.document for item in documents}
    root_id = "catia:assembly:root"
    root_path = _source_path(label)
    definitions: list[ComponentDefinition] = [
        ComponentDefinition(
            root_id,
            table.root_name,
            ComponentKind.ASSEMBLY,
            source_path=str(root_path) if root_path is not None else label,
            source_format_id=_FORMAT_ID,
            source_sha256=(
                hashlib.sha256(archive.data).hexdigest() if archive.data else ""
            ),
            provenance=Provenance(
                _FORMAT_ID,
                "ASMPRODUCT",
                spans=(
                    ProvenanceSpan(
                        table.stream_name,
                        table.tokens[1].offset,
                        table.tokens[1].length,
                        "product-name",
                    ),
                ),
            ),
            attributes=frozen_mapping(
                {
                    "native_structure": "ASMPRODUCT",
                    "native_string_table_offset": table.table_offset,
                }
            ),
        )
    ]
    definition_ids: dict[str, str] = {}
    first_offsets: dict[str, int] = {}
    for occurrence in table.occurrences:
        first_offsets.setdefault(
            occurrence.definition_name, occurrence.definition_offset
        )
    for definition_name in dict.fromkeys(
        occurrence.definition_name for occurrence in table.occurrences
    ):
        definition_id = f"catia:definition:{len(definition_ids) + 1}"
        definition_ids[definition_name] = definition_id
        reference = selected.get(definition_name)
        document_id = document_ids.get(definition_name, "")
        document = documents_by_id.get(document_id)
        kind = (
            ComponentKind.ASSEMBLY
            if reference is not None and reference.document_type == "CATProduct"
            else (
                ComponentKind.PART
                if reference is not None and reference.document_type == "CATPart"
                else ComponentKind.REFERENCE
            )
        )
        definitions.append(
            ComponentDefinition(
                definition_id,
                definition_name,
                kind,
                document_id=document_id,
                body_ids=(
                    tuple(body.id for body in document.bodies)
                    if document is not None and kind == ComponentKind.PART
                    else ()
                ),
                source_path=str(reference.path) if reference is not None else "",
                source_format_id=_FORMAT_ID if reference is not None else "",
                source_sha256=reference.sha256 if reference is not None else "",
                provenance=Provenance(
                    _FORMAT_ID,
                    definition_name,
                    spans=(
                        ProvenanceSpan(
                            table.stream_name,
                            first_offsets[definition_name],
                            len(definition_name),
                            "component-definition",
                        ),
                    ),
                ),
                attributes=frozen_mapping(
                    {
                        "native_reference_name": definition_name,
                        "source_resolved": reference is not None,
                    }
                ),
            )
        )
    instances = tuple(
        ComponentInstance(
            f"catia:instance:{order + 1}",
            occurrence.instance_name,
            definition_ids[occurrence.definition_name],
            root_id,
            order=order,
            reference_number=occurrence.reference_number,
            provenance=Provenance(
                _FORMAT_ID,
                occurrence.instance_name,
                spans=(
                    ProvenanceSpan(
                        table.stream_name,
                        occurrence.instance_offset,
                        len(occurrence.instance_name),
                        "component-instance",
                    ),
                ),
            ),
            attributes=frozen_mapping(
                {
                    "native_definition_name": occurrence.definition_name,
                    "native_string_offset": occurrence.instance_offset,
                    "transform_resolved": False,
                    "transform_source": "exact_native_payload",
                }
            ),
        )
        for order, occurrence in enumerate(table.occurrences)
    )
    missing = tuple(
        name for name in definition_ids if name not in selected
    )
    diagnostics: list[Diagnostic] = [*reference_diagnostics, *document_diagnostics]
    if missing:
        diagnostics.append(
            Diagnostic(
                "catia.product.component_sources_missing",
                f"{len(missing)} CATProduct component sources could not be resolved by internal product name.",
                Severity.INFO,
                attributes=frozen_mapping({"definition_names": missing}),
            )
        )
    if instances:
        diagnostics.append(
            Diagnostic(
                "catia.product.transforms_unresolved",
                "CATProduct occurrence order and names are decoded; proprietary position records remain byte-exact in the native payload and identity matrices are placeholders.",
                Severity.WARNING,
                attributes=frozen_mapping(
                    {
                        "instance_count": len(instances),
                        "resolved_count": 0,
                        "placeholder": "identity",
                    }
                ),
            )
        )
    diagnostics.append(
        Diagnostic(
            "catia.product.constraints_unresolved",
            "CATProduct connector and constraint records remain byte-exact in the native payload; no semantic mates are asserted without a verified decoder.",
            Severity.INFO,
        )
    )
    assembly = AssemblyData(
        root_definition_id=root_id,
        definitions=tuple(definitions),
        instances=instances,
        documents=documents,
        attributes=frozen_mapping(
            {
                "native_structure": "ASMPRODUCT",
                "native_stream": table.stream_name,
                "native_string_table_offset": table.table_offset,
                "native_string_count": len(table.tokens),
                "native_instance_count": len(instances),
                "native_definition_count": len(definition_ids),
                "resolved_definition_count": len(selected),
                "linked_document_count": len(documents),
                "linked_sketch_count": sum(
                    len(item.document.sketches) for item in documents
                ),
                "linked_feature_count": sum(
                    len(item.document.feature_timeline) for item in documents
                ),
                "transform_status": "native-only",
                "constraint_status": "native-only",
            }
        ),
    )
    return assembly, tuple(diagnostics)


def _product_tokens(data: bytes) -> tuple[NativeProductToken, ...]:
    marker = data.find(_PRODUCT_MARKER)
    if marker < 1 or data[marker - 1] != len(_PRODUCT_MARKER) + 1:
        return ()
    cursor = marker - 1
    result: list[NativeProductToken] = []
    while cursor < len(data):
        stored_length = data[cursor]
        length = stored_length - 1
        end = cursor + 1 + length
        if length < 1 or end > len(data):
            break
        raw = data[cursor + 1 : end]
        if any(value < 0x20 or value > 0x7E for value in raw):
            break
        result.append(
            NativeProductToken(raw.decode("ascii"), cursor + 1, length)
        )
        cursor = end
    return tuple(result)


def _product_occurrences(
    tokens: tuple[NativeProductToken, ...],
) -> tuple[NativeProductOccurrence, ...]:
    values = tuple(token.value for token in tokens)
    try:
        start = values.index("_Reps") + 1
    except ValueError as exc:
        raise Cfv2FormatError("CATIA ASMPRODUCT table has no _Reps boundary") from exc
    usable = tuple(
        token
        for token in tokens[start:]
        if not token.value.startswith("_")
        and token.value not in _NON_COMPONENT_VALUES
        and not token.value.isdecimal()
    )
    result: list[NativeProductOccurrence] = []
    definition_offsets: dict[str, int] = {}
    pending: NativeProductToken | None = None
    for token in usable:
        match = _INSTANCE.fullmatch(token.value)
        if match is not None:
            derived = match.group(1)
            definition = _instance_definition(pending, derived)
            offset = (
                pending.offset
                if pending is not None and definition == pending.value
                else definition_offsets.get(definition, token.offset)
            )
            definition_offsets.setdefault(definition, offset)
            result.append(
                NativeProductOccurrence(
                    definition,
                    token.value,
                    definition_offsets[definition],
                    token.offset,
                    match.group(2),
                )
            )
            pending = None
            continue
        custom = _custom_numbered_pair(pending, token)
        if custom is not None:
            definition_offsets.setdefault(custom, pending.offset)
            reference = _SPACE_NUMBER.fullmatch(token.value)
            result.append(
                NativeProductOccurrence(
                    custom,
                    token.value,
                    definition_offsets[custom],
                    token.offset,
                    reference.group(2) if reference is not None else "",
                )
            )
            pending = None
            continue
        pending = token
        definition_offsets.setdefault(token.value, token.offset)
    return tuple(result)


def _instance_definition(
    pending: NativeProductToken | None, derived: str
) -> str:
    if pending is None:
        return derived
    if pending.value == derived:
        return derived
    if _TRAILING_VARIANT.sub("", pending.value) == derived:
        return pending.value
    if pending.value.startswith(derived + "_"):
        return pending.value
    return derived


def _custom_numbered_pair(
    pending: NativeProductToken | None, current: NativeProductToken
) -> str | None:
    if pending is None:
        return None
    left = _SPACE_NUMBER.fullmatch(pending.value)
    right = _SPACE_NUMBER.fullmatch(current.value)
    if left is None or right is None or left.group(1) != right.group(1):
        return None
    if int(right.group(2)) != int(left.group(2)) + 1:
        return None
    return pending.value


def _component_reference_index(
    label: str, settings: ReadOptions
) -> dict[str, tuple[NativeProductReference, ...]]:
    if settings.values.get("resolve_components", True) is False:
        return {}
    requested_root = settings.values.get("component_search_root")
    if requested_root:
        root = Path(str(requested_root)).expanduser().resolve()
    else:
        source = _source_path(label)
        if source is None:
            return {}
        root = source.parent
    if not root.is_dir():
        return {}
    references: defaultdict[str, list[NativeProductReference]] = defaultdict(list)
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in {
            ".catpart",
            ".catproduct",
        }:
            continue
        resolved = path.resolve()
        try:
            data = resolved.read_bytes()
            archive = Cfv2Archive.from_bytes(data)
            table = decode_product_table(archive)
        except (Cfv2FormatError, OSError, UnicodeDecodeError, ValueError):
            continue
        references[table.root_name].append(
            NativeProductReference(
                table.root_name,
                resolved,
                "CATProduct"
                if resolved.suffix.casefold() == ".catproduct"
                else "CATPart",
                hashlib.sha256(data).hexdigest(),
            )
        )
    return {
        name: tuple(sorted(values, key=lambda item: str(item.path).casefold()))
        for name, values in references.items()
    }


def _selected_references(
    table: NativeProductTable,
    references: dict[str, tuple[NativeProductReference, ...]],
) -> tuple[dict[str, NativeProductReference], tuple[Diagnostic, ...]]:
    selected: dict[str, NativeProductReference] = {}
    diagnostics: list[Diagnostic] = []
    for name in dict.fromkeys(
        occurrence.definition_name for occurrence in table.occurrences
    ):
        candidates = references.get(name, ())
        if not candidates:
            continue
        ordered = sorted(
            candidates,
            key=lambda item: (
                item.path.stem.casefold() != name.casefold(),
                str(item.path).casefold(),
            ),
        )
        selected[name] = ordered[0]
        if len(ordered) > 1:
            diagnostics.append(
                Diagnostic(
                    "catia.product.component_source_ambiguous",
                    f"Multiple CATIA documents declare product name {name!r}; the deterministic best match was selected.",
                    Severity.WARNING,
                    attributes=frozen_mapping(
                        {
                            "selected": str(ordered[0].path),
                            "candidates": tuple(str(item.path) for item in ordered),
                        }
                    ),
                )
            )
    return selected, tuple(diagnostics)


def _component_documents(
    label: str,
    table: NativeProductTable,
    references: dict[str, NativeProductReference],
    settings: ReadOptions,
    reader: ComponentReader,
) -> tuple[
    tuple[ComponentDocument, ...],
    dict[str, str],
    tuple[Diagnostic, ...],
]:
    source = _source_path(label)
    stack = tuple(str(value) for value in settings.values.get("catia_path_stack", ()))
    active = {value.casefold() for value in stack}
    if source is not None:
        active.add(str(source).casefold())
    documents: list[ComponentDocument] = []
    document_ids_by_path: dict[Path, str] = {}
    document_ids_by_name: dict[str, str] = {}
    diagnostics: list[Diagnostic] = []
    names = dict.fromkeys(
        occurrence.definition_name for occurrence in table.occurrences
    )
    for name in names:
        reference = references.get(name)
        if reference is None:
            continue
        if str(reference.path).casefold() in active:
            diagnostics.append(
                Diagnostic(
                    "catia.product.component_cycle",
                    f"Recursive CATIA product reference was not expanded: {reference.path}",
                    Severity.WARNING,
                )
            )
            continue
        existing = document_ids_by_path.get(reference.path)
        if existing is not None:
            document_ids_by_name[name] = existing
            continue
        values = dict(settings.values)
        values["catia_path_stack"] = (
            *stack,
            *((str(source),) if source is not None else ()),
        )
        options = ReadOptions(
            configuration=settings.configuration,
            include_brep=settings.include_brep,
            include_tessellation=settings.include_tessellation,
            strict=settings.strict,
            values=frozen_mapping(values),
        )
        try:
            document = reader(reference.path, options)
        except (Cfv2FormatError, OSError, TypeError, ValueError) as exc:
            diagnostics.append(
                Diagnostic(
                    "catia.product.component_decode_failed",
                    f"CATIA component could not be decoded: {reference.path}: {exc}",
                    Severity.WARNING,
                    attributes=frozen_mapping({"definition_name": name}),
                )
            )
            continue
        document_id = f"catia:document:{document.source.sha256[:20]}"
        documents.append(ComponentDocument(document_id, document))
        document_ids_by_path[reference.path] = document_id
        document_ids_by_name[name] = document_id
    return tuple(documents), document_ids_by_name, tuple(diagnostics)


def _source_path(label: str) -> Path | None:
    if label == "<memory>":
        return None
    path = Path(label).expanduser()
    return path.resolve() if path.is_file() else None

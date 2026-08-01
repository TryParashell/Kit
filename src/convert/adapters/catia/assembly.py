from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import stat
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

from .container import Cfv2Archive, Cfv2FormatError, Cfv2Stream


_FORMAT_ID = "catia.v5"
_PRODUCT_MARKER = b"ASMPRODUCT"
_INSTANCE = re.compile(r"(?:I_)?(.+)\.(\d+)")
_TRAILING_VARIANT = re.compile(r"(?:_| )\d+$")
_SPACE_NUMBER = re.compile(r"(.+ )([0-9]+)$")
_DEFAULT_MAX_FILES = 4096
_DEFAULT_MAX_TOTAL_BYTES = 4 * 1024 * 1024 * 1024
_DEFAULT_MAX_DEPTH = 8
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
    stream_descriptor_offset: int
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
    candidates: list[tuple[Cfv2Stream, tuple[NativeProductToken, ...]]] = []
    for stream in archive.outer.streams:
        data = archive.stream_bytes(stream, archive.outer)
        tokens = _product_tokens(data)
        if tokens:
            candidates.append((stream, tokens))
    if not candidates:
        raise Cfv2FormatError("CATIA product has no ASMPRODUCT table")
    candidates.sort(
        key=lambda item: (
            item[0].name != "Data",
            -len(item[1]),
            item[0].name.casefold(),
        )
    )
    stream, tokens = candidates[0]
    if len(tokens) < 2:
        raise Cfv2FormatError("CATIA ASMPRODUCT table has no product name")
    occurrences = _product_occurrences(tokens)
    return NativeProductTable(
        root_name=tokens[1].value,
        stream_name=stream.name,
        stream_descriptor_offset=stream.descriptor_offset,
        table_offset=tokens[0].offset,
        tokens=tokens,
        occurrences=occurrences,
    )


def _physical_spans(
    archive: Cfv2Archive,
    table: NativeProductTable,
    logical_offset: int,
    length: int,
    record_kind: str,
) -> tuple[ProvenanceSpan, ...]:
    stream = next(
        (
            item
            for item in archive.outer.streams
            if item.descriptor_offset == table.stream_descriptor_offset
        ),
        None,
    )
    if stream is None:
        raise Cfv2FormatError("CATIA product stream descriptor is unavailable")
    logical_end = logical_offset + length
    spans: list[ProvenanceSpan] = []
    covered = 0
    for extent in stream.extents:
        extent_start = extent.logical_offset
        extent_end = extent_start + extent.physical_length
        overlap_start = max(logical_offset, extent_start)
        overlap_end = min(logical_end, extent_end)
        if overlap_start >= overlap_end:
            continue
        physical_offset = (
            archive.outer.physical_base
            + extent.physical_offset
            + overlap_start
            - extent_start
        )
        overlap_length = overlap_end - overlap_start
        spans.append(
            ProvenanceSpan(
                table.stream_name,
                physical_offset,
                overlap_length,
                record_kind,
            )
        )
        covered += overlap_length
    if covered != length:
        raise Cfv2FormatError("CATIA product token crosses an unavailable extent")
    return tuple(spans)


def native_product_assembly(
    archive: Cfv2Archive,
    label: str,
    settings: ReadOptions,
    reader: ComponentReader,
) -> tuple[AssemblyData, tuple[Diagnostic, ...]]:
    table = decode_product_table(archive)
    references, search_diagnostics = _component_reference_index(label, settings)
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
                spans=_physical_spans(
                    archive,
                    table,
                    table.tokens[1].offset,
                    table.tokens[1].length,
                    "product-name",
                ),
            ),
            attributes=frozen_mapping(
                {
                    "native_structure": "ASMPRODUCT",
                    "native_string_table_logical_offset": table.table_offset,
                    "native_string_table_physical_offset": _physical_spans(
                        archive,
                        table,
                        table.table_offset,
                        1,
                        "string-table-prefix",
                    )[0].offset,
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
                    spans=_physical_spans(
                        archive,
                        table,
                        first_offsets[definition_name],
                        len(definition_name),
                        "component-definition",
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
                spans=_physical_spans(
                    archive,
                    table,
                    occurrence.instance_offset,
                    len(occurrence.instance_name),
                    "component-instance",
                ),
            ),
            attributes=frozen_mapping(
                {
                    "native_definition_name": occurrence.definition_name,
                    "native_string_logical_offset": occurrence.instance_offset,
                    "native_string_physical_offset": _physical_spans(
                        archive,
                        table,
                        occurrence.instance_offset,
                        len(occurrence.instance_name),
                        "component-instance",
                    )[0].offset,
                    "transform_resolved": False,
                    "transform_source": "exact_native_payload",
                }
            ),
        )
        for order, occurrence in enumerate(table.occurrences)
    )
    missing = tuple(name for name in definition_ids if name not in selected)
    diagnostics: list[Diagnostic] = [
        *search_diagnostics,
        *reference_diagnostics,
        *document_diagnostics,
    ]
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
                "CATProduct occurrence order and names are decoded; proprietary position records remain byte-exact in the native payload and unresolved transforms retain the identity default.",
                Severity.WARNING,
                attributes=frozen_mapping(
                    {
                        "instance_count": len(instances),
                        "resolved_count": 0,
                        "unresolved_default": "identity",
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
                "native_string_table_logical_offset": table.table_offset,
                "native_string_table_physical_offset": _physical_spans(
                    archive,
                    table,
                    table.table_offset,
                    1,
                    "string-table-prefix",
                )[0].offset,
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
        result.append(NativeProductToken(raw.decode("ascii"), cursor + 1, length))
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


def _instance_definition(pending: NativeProductToken | None, derived: str) -> str:
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


def _component_reference_index(label: str, settings: ReadOptions) -> tuple[
    dict[str, tuple[NativeProductReference, ...]],
    tuple[Diagnostic, ...],
]:
    if settings.values.get("resolve_components", True) is False:
        return {}, ()
    max_files = _search_limit(
        settings,
        "component_search_max_files",
        _DEFAULT_MAX_FILES,
    )
    max_total_bytes = _search_limit(
        settings,
        "component_search_max_total_bytes",
        _DEFAULT_MAX_TOTAL_BYTES,
    )
    max_depth = _search_limit(
        settings,
        "component_search_max_depth",
        _DEFAULT_MAX_DEPTH,
        allow_zero=True,
    )
    roots, root_diagnostics = _component_search_roots(label, settings)
    references: defaultdict[str, list[NativeProductReference]] = defaultdict(list)
    diagnostics = list(root_diagnostics)
    file_count = 0
    total_bytes = 0
    limit: str | None = None
    for root in roots:
        pending: list[tuple[Path, int]] = [(root, 0)]
        while pending and limit is None:
            directory, depth = pending.pop(0)
            try:
                entries = tuple(
                    sorted(directory.iterdir(), key=lambda item: item.name.casefold())
                )
            except OSError as exc:
                diagnostics.append(
                    _search_diagnostic(directory, "unreadable_directory", str(exc))
                )
                continue
            for path in entries:
                if _is_reparse_point(path):
                    diagnostics.append(_search_diagnostic(path, "reparse_point"))
                    continue
                try:
                    if path.is_dir():
                        if depth >= max_depth:
                            limit = "depth"
                            break
                        resolved_directory = path.resolve(strict=True)
                        if not _under_root(resolved_directory, root):
                            diagnostics.append(_search_diagnostic(path, "root_escape"))
                            continue
                        pending.append((resolved_directory, depth + 1))
                        continue
                    if not path.is_file() or path.suffix.casefold() not in {
                        ".catpart",
                        ".catproduct",
                    }:
                        continue
                    resolved = path.resolve(strict=True)
                    if not _under_root(resolved, root):
                        diagnostics.append(_search_diagnostic(path, "root_escape"))
                        continue
                    size = resolved.stat().st_size
                except OSError as exc:
                    diagnostics.append(
                        _search_diagnostic(path, "unreadable_candidate", str(exc))
                    )
                    continue
                if file_count >= max_files:
                    limit = "files"
                    break
                if size > max_total_bytes - total_bytes:
                    limit = "total_bytes"
                    break
                file_count += 1
                total_bytes += size
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
                        (
                            "CATProduct"
                            if resolved.suffix.casefold() == ".catproduct"
                            else "CATPart"
                        ),
                        hashlib.sha256(data).hexdigest(),
                    )
                )
        if limit is not None:
            break
    if limit is not None:
        diagnostics.append(
            Diagnostic(
                "catia.product.component_search_limit",
                f"CATIA component discovery stopped at the configured {limit} limit.",
                Severity.WARNING,
                attributes=frozen_mapping(
                    {
                        "limit": limit,
                        "files": file_count,
                        "total_bytes": total_bytes,
                        "max_files": max_files,
                        "max_total_bytes": max_total_bytes,
                        "max_depth": max_depth,
                    }
                ),
            )
        )
    return (
        {
            name: tuple(sorted(values, key=lambda item: str(item.path).casefold()))
            for name, values in references.items()
        },
        tuple(diagnostics),
    )


def _component_search_roots(
    label: str, settings: ReadOptions
) -> tuple[tuple[Path, ...], tuple[Diagnostic, ...]]:
    requested = settings.values.get("component_search_root")
    if requested:
        candidates = (Path(str(requested)).expanduser(),)
    else:
        source = _source_path(label)
        if source is None:
            return (), ()
        candidates = (source.parent,)
        if source.parent.name.casefold() in {".catproduct", "catproduct"}:
            candidates = (*candidates, source.parent.parent / ".CATPart")
    roots: list[Path] = []
    diagnostics: list[Diagnostic] = []
    seen: set[str] = set()
    for candidate in candidates:
        if _is_reparse_point(candidate):
            diagnostics.append(_search_diagnostic(candidate, "reparse_root"))
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            diagnostics.append(
                _search_diagnostic(candidate, "unavailable_root", str(exc))
            )
            continue
        if not resolved.is_dir():
            diagnostics.append(_search_diagnostic(resolved, "root_is_not_directory"))
            continue
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        roots.append(resolved)
    return tuple(roots), tuple(diagnostics)


def _search_limit(
    settings: ReadOptions,
    name: str,
    default: int,
    *,
    allow_zero: bool = False,
) -> int:
    value = settings.values.get(name, default)
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    minimum = 0 if allow_zero else 1
    if parsed < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return parsed


def _is_reparse_point(path: Path) -> bool:
    try:
        value = path.lstat()
    except OSError:
        return False
    attributes = getattr(value, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(attributes & reparse_flag)


def _under_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _search_diagnostic(path: Path, reason: str, detail: str = "") -> Diagnostic:
    return Diagnostic(
        "catia.product.component_search_rejected",
        f"CATIA component discovery rejected {path}: {reason}.",
        Severity.INFO,
        attributes=frozen_mapping(
            {
                "path": str(path),
                "reason": reason,
                "detail": detail,
            }
        ),
    )


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
        if document.source.sha256.casefold() != reference.sha256.casefold():
            diagnostics.append(
                Diagnostic(
                    "catia.product.component_source_changed",
                    f"CATIA component changed after discovery and was not linked: {reference.path}",
                    Severity.WARNING,
                    attributes=frozen_mapping(
                        {
                            "definition_name": name,
                            "indexed_sha256": reference.sha256,
                            "decoded_sha256": document.source.sha256,
                        }
                    ),
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

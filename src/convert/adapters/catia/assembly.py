from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
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
from .format import (
    DOCUMENT_TYPE_BY_SUFFIX,
    INFO,
    PART_DOCUMENT_TYPE,
    PRODUCT_DOCUMENT_TYPE,
    SUFFIX_BY_DOCUMENT_TYPE,
)


_FORMAT_ID = INFO.format_id
_PART_SUFFIX = SUFFIX_BY_DOCUMENT_TYPE[PART_DOCUMENT_TYPE]
_PRODUCT_SUFFIX = SUFFIX_BY_DOCUMENT_TYPE[PRODUCT_DOCUMENT_TYPE]
_PRODUCT_MARKER = b"ASMPRODUCT"
_DEFAULT_MAX_FILES = 4096
_DEFAULT_MAX_TOTAL_BYTES = 4 * 1024 * 1024 * 1024
_DEFAULT_MAX_DEPTH = 8


@dataclass(frozen=True, slots=True)
class NativeProductToken:
    value: str
    offset: int
    length: int
    encoding: str


@dataclass(frozen=True, slots=True)
class NativeProductOccurrence:
    definition_name: str
    instance_name: str
    definition_offset: int
    instance_offset: int
    definition_length: int
    instance_length: int
    reference_number: str


@dataclass(frozen=True, slots=True)
class NativeProductTable:
    root_name: str
    stream_name: str
    stream_descriptor_offset: int
    table_offset: int
    tokens: tuple[NativeProductToken, ...]
    occurrences: tuple[NativeProductOccurrence, ...]
    ambiguous_tokens: tuple[NativeProductToken, ...]
    alternatives: tuple[NativeProductTableCandidate, ...] = ()


@dataclass(frozen=True, slots=True)
class NativeProductTableCandidate:
    root_name: str
    stream_name: str
    stream_descriptor_offset: int
    table_offset: int
    tokens: tuple[NativeProductToken, ...]


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
    occurrences, ambiguous_tokens = _product_occurrences(tokens)
    alternatives = tuple(
        NativeProductTableCandidate(
            root_name=value[1][1].value,
            stream_name=value[0].name,
            stream_descriptor_offset=value[0].descriptor_offset,
            table_offset=value[1][0].offset,
            tokens=value[1],
        )
        for value in candidates[1:]
        if len(value[1]) >= 2
    )
    return NativeProductTable(
        root_name=tokens[1].value,
        stream_name=stream.name,
        stream_descriptor_offset=stream.descriptor_offset,
        table_offset=tokens[0].offset,
        tokens=tokens,
        occurrences=occurrences,
        ambiguous_tokens=ambiguous_tokens,
        alternatives=alternatives,
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
    selected, reference_candidates, reference_diagnostics = _selected_references(
        table, references
    )
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
    first_occurrences: dict[str, NativeProductOccurrence] = {}
    for occurrence in table.occurrences:
        first_occurrences.setdefault(occurrence.definition_name, occurrence)
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
            if reference is not None
            and reference.document_type == PRODUCT_DOCUMENT_TYPE
            else (
                ComponentKind.PART
                if reference is not None
                and reference.document_type == PART_DOCUMENT_TYPE
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
                        first_occurrences[definition_name].definition_offset,
                        first_occurrences[definition_name].definition_length,
                        "component-definition",
                    ),
                ),
                attributes=frozen_mapping(
                    {
                        "native_reference_name": definition_name,
                        "source_resolved": reference is not None,
                        "source_ambiguous": len(
                            reference_candidates.get(definition_name, ())
                        )
                        > 1,
                        "native_reference_candidates": tuple(
                            {
                                "path": str(candidate.path),
                                "document_type": candidate.document_type,
                                "sha256": candidate.sha256,
                            }
                            for candidate in reference_candidates.get(
                                definition_name, ()
                            )
                        ),
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
                    occurrence.instance_length,
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
                        occurrence.instance_length,
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
    if table.alternatives:
        diagnostics.append(
            Diagnostic(
                "catia.product.root_ambiguous",
                "Multiple CATIA product tables were retained; the deterministic Data-first table supplies normalized assembly semantics.",
                Severity.WARNING,
                attributes=frozen_mapping(
                    {
                        "selected": _table_candidate_record(table),
                        "alternatives": tuple(
                            _table_candidate_record(candidate)
                            for candidate in table.alternatives
                        ),
                    }
                ),
            )
        )
    if table.ambiguous_tokens:
        diagnostics.append(
            Diagnostic(
                "catia.product.native_tokens_retained",
                "CATIA product tokens without verified occurrence roles remain available as ordered native records.",
                Severity.INFO,
                attributes=frozen_mapping(
                    {
                        "tokens": tuple(
                            _token_record(token) for token in table.ambiguous_tokens
                        )
                    }
                ),
            )
        )
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
                "native_table_candidates": (
                    _table_candidate_record(table),
                    *(
                        _table_candidate_record(candidate)
                        for candidate in table.alternatives
                    ),
                ),
                "native_unresolved_tokens": tuple(
                    _token_record(token) for token in table.ambiguous_tokens
                ),
                "native_reference_candidates": tuple(
                    {
                        "definition_name": name,
                        "candidates": tuple(
                            {
                                "path": str(candidate.path),
                                "document_type": candidate.document_type,
                                "sha256": candidate.sha256,
                            }
                            for candidate in candidates
                        ),
                    }
                    for name, candidates in reference_candidates.items()
                    if candidates
                ),
            }
        ),
    )
    return assembly, tuple(diagnostics)


def _token_record(token: NativeProductToken) -> dict[str, object]:
    return {
        "value": token.value,
        "offset": token.offset,
        "length": token.length,
        "encoding": token.encoding,
    }


def _table_candidate_record(
    table: NativeProductTable | NativeProductTableCandidate,
) -> dict[str, object]:
    return {
        "root_name": table.root_name,
        "stream_name": table.stream_name,
        "stream_descriptor_offset": table.stream_descriptor_offset,
        "table_offset": table.table_offset,
        "tokens": tuple(_token_record(token) for token in table.tokens),
    }


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
        value, encoding = _decode_product_token(raw)
        result.append(NativeProductToken(value, cursor + 1, length, encoding))
        cursor = end
    return tuple(result)


def _decode_product_token(raw: bytes) -> tuple[str, str]:
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        decoded = _decoded_text(raw, "utf-16")
        if decoded is not None:
            return decoded, "utf-16"
    if len(raw) >= 2 and len(raw) % 2 == 0:
        pairs = len(raw) // 2
        little_zeroes = sum(raw[index] == 0 for index in range(1, len(raw), 2))
        big_zeroes = sum(raw[index] == 0 for index in range(0, len(raw), 2))
        if little_zeroes * 2 >= pairs:
            decoded = _decoded_text(raw, "utf-16le")
            if decoded is not None:
                return decoded, "utf-16le"
        if big_zeroes * 2 >= pairs:
            decoded = _decoded_text(raw, "utf-16be")
            if decoded is not None:
                return decoded, "utf-16be"
    decoded = _decoded_text(raw, "utf-8")
    return (
        (decoded, "utf-8")
        if decoded is not None
        else (raw.decode("latin-1"), "latin-1")
    )


def _decoded_text(raw: bytes, encoding: str) -> str | None:
    try:
        return raw.decode(encoding)
    except UnicodeDecodeError:
        return None


def _product_occurrences(
    tokens: tuple[NativeProductToken, ...],
) -> tuple[tuple[NativeProductOccurrence, ...], tuple[NativeProductToken, ...]]:
    values = tuple(token.value for token in tokens)
    try:
        start = values.index("_Reps") + 1
    except ValueError as exc:
        raise Cfv2FormatError("CATIA ASMPRODUCT table has no _Reps boundary") from exc
    result: list[NativeProductOccurrence] = []
    used: set[int] = set()
    terminal = next(
        (
            index
            for index in range(start, len(tokens))
            if tokens[index].value == "IsRoot"
        ),
        len(tokens),
    )

    def append(definition_index: int, instance_index: int, reference: str) -> None:
        definition = tokens[definition_index]
        instance = tokens[instance_index]
        result.append(
            NativeProductOccurrence(
                definition.value,
                instance.value,
                definition.offset,
                instance.offset,
                definition.length,
                instance.length,
                reference,
            )
        )
        used.update((definition_index, instance_index))

    marker = next(
        (
            index
            for index in range(start + 1, terminal)
            if tokens[index].value == "_InstanceName"
        ),
        None,
    )
    current_definition: int | None = None
    definitions_by_instance_key: dict[str, int] = {}
    pool_start = start
    if marker is not None and marker + 1 < terminal:
        identity = _numbered_instance_identity(tokens[marker + 1].value)
        append(start, marker + 1, identity[1] if identity is not None else "")
        if identity is not None:
            definitions_by_instance_key[identity[0]] = start
        current_definition = start
        shape = next(
            (
                index
                for index in range(marker + 2, terminal)
                if tokens[index].value == "Shape 1"
            ),
            marker + 1,
        )
        pool_start = shape + 1
    pending: int | None = None
    for index in range(pool_start, terminal):
        if index in used:
            continue
        identity = _numbered_instance_identity(tokens[index].value)
        if identity is not None:
            instance_key, reference = identity
            established = definitions_by_instance_key.get(instance_key)
            if pending is not None:
                current_definition = pending
                definitions_by_instance_key[instance_key] = pending
                pending = None
            elif established is not None:
                current_definition = established
            if current_definition is not None:
                append(current_definition, index, reference)
            continue
        if tokens[index].value == "_InstanceName" and pending is not None:
            instance_index = index + 1
            if instance_index < terminal:
                append(
                    pending,
                    instance_index,
                    (
                        identity[1]
                        if (
                            identity := _numbered_instance_identity(
                                tokens[instance_index].value
                            )
                        )
                        is not None
                        else ""
                    ),
                )
                if identity is not None:
                    definitions_by_instance_key[identity[0]] = pending
                current_definition = pending
                pending = None
            continue
        pending = index
    if terminal >= start + 3:
        ordinal, definition, instance = range(terminal - 3, terminal)
        if (
            tokens[ordinal].value.isdecimal()
            and definition not in used
            and instance not in used
        ):
            append(definition, instance, tokens[ordinal].value)
    ambiguous = tuple(
        token
        for index, token in enumerate(tokens)
        if index >= start and index not in used
    )
    return tuple(result), ambiguous


def _numbered_instance_identity(value: str) -> tuple[str, str] | None:
    identity, separator, reference = value.rpartition(".")
    if not identity or not separator or not reference.isdecimal():
        return None
    if identity.startswith("I_"):
        identity = identity[2:]
    return identity, reference


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
                    sorted(
                        directory.iterdir(),
                        key=lambda item: (item.name.casefold(), item.name),
                    )
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
                    if (
                        not path.is_file()
                        or path.suffix.casefold() not in DOCUMENT_TYPE_BY_SUFFIX
                    ):
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
                        DOCUMENT_TYPE_BY_SUFFIX[resolved.suffix.casefold()],
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
            name: tuple(
                sorted(
                    values,
                    key=lambda item: (str(item.path).casefold(), str(item.path)),
                )
            )
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
        if source.parent.name.casefold() in {
            _PRODUCT_SUFFIX,
            _PRODUCT_SUFFIX.removeprefix("."),
        }:
            candidates = (
                *candidates,
                source.parent.parent / f".{PART_DOCUMENT_TYPE}",
            )
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
) -> tuple[
    dict[str, NativeProductReference],
    dict[str, tuple[NativeProductReference, ...]],
    tuple[Diagnostic, ...],
]:
    selected: dict[str, NativeProductReference] = {}
    retained: dict[str, tuple[NativeProductReference, ...]] = {}
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
                str(item.path).casefold(),
                str(item.path),
            ),
        )
        retained[name] = tuple(ordered)
        if len(ordered) == 1:
            selected[name] = ordered[0]
        else:
            diagnostics.append(
                Diagnostic(
                    "catia.product.component_source_ambiguous",
                    f"Multiple CATIA documents declare product name {name!r}; no source was selected without unique structural identity.",
                    Severity.WARNING,
                    attributes=frozen_mapping(
                        {
                            "definition_name": name,
                            "selected": "",
                            "candidates": tuple(str(item.path) for item in ordered),
                        }
                    ),
                )
            )
    return selected, retained, tuple(diagnostics)


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

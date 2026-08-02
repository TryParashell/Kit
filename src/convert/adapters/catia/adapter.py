from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import re
import struct
from types import MappingProxyType
import zlib

from convert.adapters.base import (
    AdapterInfo,
    Destination,
    ProbeResult,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
    is_binary_destination,
)
from convert.opencascade import decode_ascii_brep as decode_opencascade_brep
from convert.parasolid import decode_brep_model as decode_parasolid_brep
from interchange import (
    Body,
    BrepModel,
    BrepPayload,
    CadDocument,
    CadSource,
    Configuration,
    Diagnostic,
    FeatureKind,
    FeatureStep,
    NativeFeatureDefinition,
    PayloadRole,
    Provenance,
    ProvenanceSpan,
    Severity,
    SupportPlane,
    Transform,
    Vector3,
    frozen_mapping,
    filter_document,
    infer_capabilities,
    semantic_metadata,
    with_wrapper_metadata,
)

from .assembly import decode_product_table, native_product_assembly
from .container import (
    Cfv2Archive,
    Cfv2Declaration,
    Cfv2Directory,
    Cfv2FormatError,
    Cfv2Stream,
    OsmxArchive,
    OsmxFormatError,
    OsmxSymbol,
    append_cfv2_stream,
    build_cfv2,
    build_declaration,
)
from .format import (
    DOCUMENT_TYPE_BY_SUFFIX,
    INFO,
    PART_DOCUMENT_TYPE,
    PRODUCT_DOCUMENT_TYPE,
    SUFFIX_BY_DOCUMENT_TYPE,
)


_FORMAT_ID = INFO.format_id
_MANIFEST_NAME = "KitInterchange"
_MANIFEST_MAGIC = b"KITCFV2\x01"
_MAX_MANIFEST_BYTES = 512 * 1024 * 1024
_MAX_MANIFEST_JSON_DEPTH = 256
_PART_STREAM = "1000_00000002_2"
_PRODUCT_STREAM = "1000_00000001_1"
_PART_SUFFIX = SUFFIX_BY_DOCUMENT_TYPE[PART_DOCUMENT_TYPE]
_PRODUCT_SUFFIX = SUFFIX_BY_DOCUMENT_TYPE[PRODUCT_DOCUMENT_TYPE]
_NATIVE_DOCUMENT_ID = "catia:native-document"
_NATIVE_DOCUMENT_BINDING_ID = "catia:native-document-binding"
_PRESERVED_DOCUMENT_PREFIX = "catia:preserved-native-document:"
_PRESERVED_BINDING_PREFIX = "catia:preserved-native-document-binding:"
_REPLAY_SEMANTIC_ATTRIBUTE = "catia.replay_semantic_sha256"
_OPENCASCADE_FORMAT_IDS = frozenset({"freecad.brep", "opencascade", "opencascade.brep"})
_PARASOLID_FORMAT_IDS = frozenset({"parasolid", "parasolid.x_b", "parasolid.x_t"})
_NEUTRAL_BREP_FORMAT_IDS = _OPENCASCADE_FORMAT_IDS | _PARASOLID_FORMAT_IDS
_WRAPPER_METADATA_KEYS = frozenset(
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


class CatiaAdapterError(RuntimeError):
    __slots__ = ()


class CatiaAdapter:
    @property
    def info(self) -> AdapterInfo:
        return INFO

    def probe(self, source: Source) -> ProbeResult:
        try:
            data, _ = _source_bytes(source)
            archive = Cfv2Archive.from_bytes(data)
            manifest = _manifest_bytes(archive)
            if manifest is not None:
                _manifest_document(manifest)
                return ProbeResult(_FORMAT_ID, 1.0, "Kit manifest in V5_CFV2")
            declarations = archive.declarations()
            if declarations:
                return ProbeResult(_FORMAT_ID, 1.0, "native CATIA container graph")
            return ProbeResult(_FORMAT_ID, 0.9, "valid V5_CFV2 stream directory")
        except (
            CatiaAdapterError,
            Cfv2FormatError,
            OSError,
            TypeError,
            ValueError,
            zlib.error,
        ) as exc:
            return ProbeResult(_FORMAT_ID, 0.0, str(exc))

    def read(self, source: Source, options: ReadOptions | None = None) -> CadDocument:
        settings = options or ReadOptions()
        data, label = _source_bytes(source)
        archive = Cfv2Archive.from_bytes(data)
        manifest = _manifest_bytes(archive)
        if manifest is not None:
            return _embedded_document(archive, data, label, manifest, settings)
        document_type = _document_type(archive, label)
        payloads = _native_payloads(archive, data, document_type, settings)
        if document_type == PRODUCT_DOCUMENT_TYPE:
            assembly, assembly_diagnostics = native_product_assembly(
                archive,
                label,
                settings,
                self.read,
            )
        else:
            assembly, assembly_diagnostics = None, ()
        (
            part_metadata,
            support_planes,
            feature_timeline,
            bodies,
            part_diagnostics,
        ) = _native_part_data(archive, document_type)
        version = _application_version(data)
        metadata = {
            "catia.document_type": document_type,
            "catia.outer_directory_offset": archive.outer.offset,
            "catia.outer_directory_length": archive.outer.length,
            "catia.outer_streams": tuple(
                (stream.name, stream.logical_length) for stream in archive.outer.streams
            ),
            "catia.nested_directory_count": len(archive.nested),
            "catia.container_classes": tuple(
                (value.ordinal, value.class_name, value.base_class, value.stream_name)
                for value in archive.declarations()
            ),
            **_container_metadata(archive),
            **part_metadata,
        }
        document = CadDocument(
            source=CadSource(
                _FORMAT_ID,
                label,
                hashlib.sha256(data).hexdigest(),
                container_version="V5_CFV2",
                application_version=version,
            ),
            configurations=_selected_configurations(
                (Configuration("catia:default", "Default", active=True),),
                settings.configuration,
            ),
            parameters=(),
            support_planes=support_planes,
            sketches=(),
            selections=(),
            feature_timeline=feature_timeline,
            bodies=bodies,
            brep_payloads=payloads,
            brep=_typed_brep(payloads, bodies),
            diagnostics=assembly_diagnostics + part_diagnostics,
            capabilities=frozenset(),
            metadata=with_wrapper_metadata(metadata, _WRAPPER_METADATA_KEYS),
            assembly=assembly,
        )
        document = replace(
            document,
            capabilities=infer_capabilities(document, roundtrip_metadata=True),
        )
        digest = _semantic_digest(document)
        document = replace(
            document,
            metadata=frozen_mapping(
                {**document.metadata, "catia.roundtrip_sha256": digest}
            ),
        )
        if settings.strict:
            document.assert_valid()
        return document

    def supports(self, document: CadDocument, destination: Destination) -> bool:
        if isinstance(destination, (str, Path)):
            expected = (
                _PRODUCT_SUFFIX if document.assembly is not None else _PART_SUFFIX
            )
            return Path(destination).suffix.casefold() == expected
        return is_binary_destination(destination)

    def write(
        self,
        document: CadDocument,
        destination: Destination,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        settings = options or WriteOptions()
        if settings.validate:
            document.assert_valid()
        document_type = _destination_type(document, destination)
        native_candidate = _unchanged_native_payload(document, document_type)
        if (
            native_candidate is not None
            and not settings.values.get("rebuild", False)
            and not (
                settings.values.get("portable") is True
                and document.assembly is not None
            )
        ):
            native, _ = native_candidate
            compatibility = _replay_compatibility(native)
            native_exact = compatibility == "native-exact"
            native_base_preserved = compatibility == "native-base-neutral-overlay"
            path = _write_bytes(destination, native, settings.overwrite)
            requirements = (
                ("referenced CATIA component files",)
                if document.assembly is not None
                else ()
            )
            return WriteResult(
                path,
                _FORMAT_ID,
                len(native),
                diagnostics=document.diagnostics,
                metadata=MappingProxyType(
                    {
                        "mode": "exact_native_roundtrip",
                        "compatibility": compatibility,
                        "vendor_loadable": native_exact,
                        "native_geometry": native_exact,
                        "native_history": native_exact,
                        "native_assembly": native_exact
                        and document.assembly is not None,
                        "native_self_contained": native_exact
                        and document.assembly is None,
                        "native_base_preserved": native_base_preserved,
                        "native_streams_preserved": native_base_preserved,
                        "referenced_files_written": 0,
                        "container": "V5_CFV2",
                        "document_type": document_type,
                    }
                ),
                requirements=requirements,
                application_usable=native_exact,
                vendor_loadable=native_exact,
            )
        if settings.values.get("allow_non_native", True) is not True:
            raise CatiaAdapterError(
                "generated CATIA writing requires "
                "WriteOptions(values={'allow_non_native': True})"
            )
        carrier_document = _carrier_manifest_document(document)
        native_base = None
        if not settings.values.get("rebuild", False) and not (
            settings.values.get("portable") is True
            and document.assembly is not None
        ):
            native_base = _native_base_payload(document, document_type)
        if native_base is not None:
            data = append_cfv2_stream(
                native_base,
                _MANIFEST_NAME,
                _pack_manifest(carrier_document),
            )
            restored = _restore_generated(data)
            if (
                restored != carrier_document
                or _replay_compatibility(data) != "native-base-neutral-overlay"
            ):
                raise CatiaAdapterError(
                    "CATIA native-base output failed semantic validation"
                )
            path = _write_bytes(destination, data, settings.overwrite)
            diagnostic = Diagnostic(
                "catia.native_base_preserved",
                "The native CATIA streams are byte-exact; changed geometry, history, sketches, and assembly semantics remain neutral Kit data rather than native CATIA feature records.",
                Severity.WARNING,
            )
            requirements = (
                ("referenced CATIA component files",)
                if document.assembly is not None
                else ()
            )
            return WriteResult(
                path,
                _FORMAT_ID,
                len(data),
                diagnostics=(*document.diagnostics, diagnostic),
                metadata=MappingProxyType(
                    {
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
                        "neutral_geometry_embedded": document.brep is not None
                        or any(
                            payload.role == PayloadRole.BREP
                            for payload in document.brep_payloads
                        ),
                        "neutral_history_embedded": bool(
                            document.parameters
                            or document.support_planes
                            or document.sketches
                            or document.selections
                            or document.feature_timeline
                            or document.bodies
                        ),
                        "neutral_assembly_embedded": document.assembly is not None,
                        "referenced_files_written": 0,
                        "container": "V5_CFV2",
                        "document_type": document_type,
                        "native_base_sha256": hashlib.sha256(
                            native_base
                        ).hexdigest(),
                        "manifest_sha256": hashlib.sha256(
                            carrier_document.to_json(indent=None).encode("utf-8")
                        ).hexdigest(),
                    }
                ),
                requirements=requirements,
                application_usable=False,
                vendor_loadable=False,
            )
        data = _generated_archive(carrier_document, document_type)
        restored = _restore_generated(data)
        if restored != carrier_document:
            raise CatiaAdapterError(
                "generated CATIA manifest failed semantic validation"
            )
        path = _write_bytes(destination, data, settings.overwrite)
        diagnostic = Diagnostic(
            "catia.native_feature_graph_embedded",
            "Geometry and parametric data are embedded in CFV2 streams; native CATIA feature classes require exact CATIA source preservation.",
            Severity.WARNING,
        )
        archive = Cfv2Archive.from_bytes(data)
        return WriteResult(
            path,
            _FORMAT_ID,
            len(data),
            diagnostics=(*document.diagnostics, diagnostic),
            metadata=MappingProxyType(
                {
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
                    "document_type": document_type,
                    "outer_stream_count": len(archive.outer.streams),
                    "nested_directory_count": len(archive.nested),
                    "manifest_sha256": hashlib.sha256(
                        carrier_document.to_json(indent=None).encode("utf-8")
                    ).hexdigest(),
                }
            ),
            application_usable=False,
            vendor_loadable=False,
        )


def _source_bytes(source: Source) -> tuple[bytes, str]:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source), "<memory>"
    if isinstance(source, (str, Path)):
        path = Path(source).expanduser().resolve()
        return path.read_bytes(), str(path)
    reader = getattr(source, "read", None)
    if not callable(reader):
        raise TypeError("CATIA source must be a path, bytes, or binary stream")
    position = source.tell() if hasattr(source, "tell") else None
    value = reader()
    if position is not None and hasattr(source, "seek"):
        source.seek(position)
    if not isinstance(value, (bytes, bytearray)):
        raise TypeError("CATIA source stream must be binary")
    return bytes(value), getattr(source, "name", "<stream>")


def _write_bytes(destination: Destination, data: bytes, overwrite: bool) -> Path | None:
    if not isinstance(destination, (str, Path)):
        writer = getattr(destination, "write", None)
        if not callable(writer):
            raise TypeError("CATIA destination must be a path or binary stream")
        written = writer(data)
        if written is not None and written != len(data):
            raise OSError("short CATIA stream write")
        return None
    path = Path(destination).expanduser().resolve()
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        with suppress(FileNotFoundError):
            temporary.unlink()
        raise
    return path


def _generated_archive(document: CadDocument, document_type: str) -> bytes:
    manifest = _pack_manifest(document)
    type_data = document_type.encode("ascii")
    nested = build_cfv2(
        (
            (_MANIFEST_NAME, manifest),
            ("KitDocumentType", type_data),
        )
    )
    if document_type == PRODUCT_DOCUMENT_TYPE:
        selected = _PRODUCT_STREAM
        declarations = build_declaration(
            "CATProdCont", "CATFeatCont", selected, ordinal=1
        )
    else:
        selected = _PART_STREAM
        declarations = b"".join(
            (
                build_declaration(
                    "CATProdCont", "CATFeatCont", _PRODUCT_STREAM, ordinal=1
                ),
                build_declaration("CATPrtCont", "CATProdCont", _PART_STREAM, ordinal=2),
            )
        )
    summary = _summary_stream(document_type)
    streams: list[tuple[str, bytes]] = [
        ("Format", type_data),
        ("Data", declarations),
    ]
    if document_type == PART_DOCUMENT_TYPE:
        streams.append((_PRODUCT_STREAM, build_cfv2((("KitProduct", b"Part"),))))
    streams.extend(
        (
            (selected, nested),
            ("CATSummaryInformation", summary),
        )
    )
    return build_cfv2(tuple(streams))


def _summary_stream(document_type: str) -> bytes:
    name = b"CATSummaryInformation"
    version = (
        b"FirstStreamed<Version>5/<Version><Release>28/<Release>"
        b"<ServicePack>6/<ServicePack><BuildDate>03-10-2020.20.00/"
        b"<BuildDate><HotFix>0/<HotFix>LastSaveVersion<Version>5/<Version>"
        b"<Release>28/<Release><ServicePack>6/<ServicePack>"
        b"<BuildDate>03-10-2020.20.00/<BuildDate><HotFix>0/<HotFix>"
        b"MinimalVersionToReadCATIAV5R28"
    )
    return b"".join(
        (
            b"FINJPL  ",
            struct.pack(">I", 0x01010003),
            struct.pack(">I", len(name)),
            b"\x00",
            name,
            b"DASSAULT-SYSTEMES",
            document_type.encode("ascii"),
            version,
        )
    )


def _pack_manifest(document: CadDocument) -> bytes:
    raw = document.to_json(indent=None).encode("utf-8")
    if len(raw) > _MAX_MANIFEST_BYTES:
        raise CatiaAdapterError("CATIA Kit manifest exceeds the size limit")
    compressed = zlib.compress(raw, level=9)
    return b"".join(
        (
            _MANIFEST_MAGIC,
            struct.pack(">Q", len(raw)),
            hashlib.sha256(raw).digest(),
            compressed,
        )
    )


def _unpack_manifest(data: bytes) -> str:
    header = len(_MANIFEST_MAGIC) + 8 + 32
    if len(data) < header or not data.startswith(_MANIFEST_MAGIC):
        raise ValueError("invalid CATIA Kit manifest header")
    length = struct.unpack_from(">Q", data, len(_MANIFEST_MAGIC))[0]
    if length > _MAX_MANIFEST_BYTES:
        raise ValueError("CATIA Kit manifest exceeds the size limit")
    expected = data[len(_MANIFEST_MAGIC) + 8 : header]
    decompressor = zlib.decompressobj()
    raw = decompressor.decompress(data[header:], length + 1)
    if len(raw) > length or decompressor.unconsumed_tail:
        raise ValueError("CATIA Kit manifest exceeds its declared length")
    if not decompressor.eof:
        raise ValueError("CATIA Kit manifest compression stream is incomplete")
    if decompressor.unused_data:
        raise ValueError("CATIA Kit manifest has trailing compressed data")
    if len(raw) != length or hashlib.sha256(raw).digest() != expected:
        raise ValueError("CATIA Kit manifest checksum mismatch")
    return raw.decode("utf-8")


def _manifest_json(data: bytes) -> str:
    try:
        source = _unpack_manifest(data)
        depth = 0
        quoted = False
        escaped = False
        for character in source:
            if quoted:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    quoted = False
                continue
            if character == '"':
                quoted = True
            elif character in "[{":
                depth += 1
                if depth > _MAX_MANIFEST_JSON_DEPTH:
                    raise CatiaAdapterError(
                        "invalid Kit document in V5_CFV2: JSON nesting exceeds the depth limit"
                    )
            elif character in "]}":
                depth -= 1
        return source
    except CatiaAdapterError:
        raise
    except RecursionError as exc:
        raise CatiaAdapterError(
            "invalid Kit document in V5_CFV2: JSON nesting exceeds the depth limit"
        ) from exc
    except (TypeError, ValueError, zlib.error) as exc:
        raise CatiaAdapterError(f"invalid Kit document in V5_CFV2: {exc}") from exc


def _manifest_document(data: bytes) -> CadDocument:
    try:
        return CadDocument.from_json(_manifest_json(data))
    except CatiaAdapterError:
        raise
    except RecursionError as exc:
        raise CatiaAdapterError(
            "invalid Kit document in V5_CFV2: JSON nesting exceeds the depth limit"
        ) from exc
    except (TypeError, ValueError, zlib.error) as exc:
        raise CatiaAdapterError(f"invalid Kit document in V5_CFV2: {exc}") from exc


def _manifest_bytes(archive: Cfv2Archive) -> bytes | None:
    matches = tuple(
        (directory, stream)
        for directory in (archive.outer, *archive.nested)
        for stream in directory.streams
        if stream.name == _MANIFEST_NAME
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise Cfv2FormatError("multiple CATIA Kit manifests")
    directory, stream = matches[0]
    return archive.stream_bytes(stream, directory)


def _restore_generated(data: bytes) -> CadDocument:
    archive = Cfv2Archive.from_bytes(data)
    manifest = _manifest_bytes(archive)
    if manifest is None:
        raise CatiaAdapterError("generated V5_CFV2 has no Kit manifest")
    return _manifest_document(manifest)


def _carrier_manifest_document(document: CadDocument) -> CadDocument:
    current_envelope = document.source.format_id == _FORMAT_ID and isinstance(
        document.source.attributes.get("embedded_source_format_id"), str
    )
    if current_envelope:
        return replace(
            document,
            brep_payloads=tuple(
                payload
                for payload in document.brep_payloads
                if not _catia_envelope_payload(payload)
            ),
        )
    documents = tuple(
        payload
        for payload in document.brep_payloads
        if _is_native_document_payload(payload)
    )
    bindings = tuple(
        payload
        for payload in document.brep_payloads
        if _is_native_document_binding(payload)
    )
    if len(documents) != 1 or len(bindings) != 1:
        return document
    native_document = documents[0]
    native_binding = bindings[0]
    if not _binding_matches_payload(native_binding, native_document):
        return document
    token = native_document.sha256
    occupied = {
        payload.id
        for payload in document.brep_payloads
        if payload is not native_document and payload is not native_binding
    }
    sequence = 1
    while {
        f"{_PRESERVED_DOCUMENT_PREFIX}{token}",
        f"{_PRESERVED_BINDING_PREFIX}{token}",
    } & occupied:
        sequence += 1
        token = f"{native_document.sha256}:{sequence}"
    replay_digest = (
        _preserved_replay_digest(document, native_document, native_binding)
        if _native_candidate_is_unchanged(document, native_document)
        else None
    )
    attributes = dict(native_document.attributes)
    if replay_digest is not None:
        attributes[_REPLAY_SEMANTIC_ATTRIBUTE] = replay_digest
    preserved_document = replace(
        native_document,
        id=f"{_PRESERVED_DOCUMENT_PREFIX}{token}",
        attributes=frozen_mapping(attributes),
    )
    preserved_binding = replace(
        native_binding,
        id=f"{_PRESERVED_BINDING_PREFIX}{token}",
    )
    return replace(
        document,
        brep_payloads=tuple(
            (
                preserved_document
                if payload is native_document
                else preserved_binding if payload is native_binding else payload
            )
            for payload in document.brep_payloads
        ),
    )


def _embedded_document(
    archive: Cfv2Archive,
    data: bytes,
    label: str,
    manifest: bytes,
    settings: ReadOptions,
) -> CadDocument:
    embedded = _manifest_document(manifest)
    configurations = _selected_configurations(
        embedded.configurations, settings.configuration
    )
    document_type = _document_type(archive, label)
    expected_type = (
        PRODUCT_DOCUMENT_TYPE if embedded.assembly is not None else PART_DOCUMENT_TYPE
    )
    if document_type != expected_type:
        raise CatiaAdapterError(
            f"{expected_type} content cannot be read as {document_type}"
        )
    original = embedded.source
    metadata = dict(embedded.metadata)
    metadata.update(
        {
            "catia.document_type": document_type,
            "catia.outer_directory_offset": archive.outer.offset,
            "catia.outer_directory_length": archive.outer.length,
            "catia.outer_streams": tuple(
                (stream.name, stream.logical_length) for stream in archive.outer.streams
            ),
            "catia.nested_directory_count": len(archive.nested),
            "catia.container_classes": tuple(
                (value.ordinal, value.class_name, value.base_class, value.stream_name)
                for value in archive.declarations()
            ),
            "catia.embedded_source_format_id": original.format_id,
            "catia.embedded_source_path": original.path,
            "catia.embedded_source_sha256": original.sha256,
            "catia.embedded_source_container_version": original.container_version,
            "catia.embedded_source_application_version": original.application_version,
            "catia.embedded_source_attributes": dict(original.attributes),
            "catia.container_compatibility": _replay_compatibility(data),
        }
    )
    filtered = filter_document(
        replace(
            embedded,
            configurations=configurations,
            brep_payloads=tuple(
                payload
                for payload in embedded.brep_payloads
                if not _catia_envelope_payload(payload)
            ),
        ),
        include_brep=settings.include_brep,
        include_tessellation=settings.include_tessellation,
        keep_payload_records=True,
    )
    retained = filtered.brep_payloads
    physical = _native_document_payload(
        archive,
        data,
        document_type,
        include_data=settings.include_brep,
    )
    binding = _native_document_binding(data, include_data=settings.include_brep)
    payloads = (*retained, binding, physical)
    document = replace(
        filtered,
        source=CadSource(
            _FORMAT_ID,
            label,
            hashlib.sha256(data).hexdigest(),
            container_version="V5_CFV2",
            application_version=_application_version(data),
            attributes=frozen_mapping(
                {
                    "embedded_source_format_id": original.format_id,
                    "embedded_source_sha256": original.sha256,
                }
            ),
        ),
        brep_payloads=tuple(payloads),
        brep=(
            filtered.brep
            if filtered.brep is not None
            else _typed_brep(retained, filtered.bodies)
        ),
        metadata=with_wrapper_metadata(metadata, _WRAPPER_METADATA_KEYS),
    )
    digest = _semantic_digest(document)
    document = replace(
        document,
        metadata=frozen_mapping(
            {**document.metadata, "catia.roundtrip_sha256": digest}
        ),
    )
    if settings.strict:
        document.assert_valid()
    return document


def _selected_configurations(
    configurations: tuple[Configuration, ...], selected: str | None
) -> tuple[Configuration, ...]:
    if selected is None:
        return configurations
    matches = {
        configuration.id
        for configuration in configurations
        if selected in {configuration.id, configuration.name}
    }
    if not matches:
        raise CatiaAdapterError(f"configuration {selected!r} is unavailable")
    return tuple(
        replace(configuration, active=configuration.id in matches)
        for configuration in configurations
    )


def _typed_brep(
    payloads: tuple[BrepPayload, ...], bodies: tuple[Body, ...]
) -> BrepModel | None:
    eligible = tuple(
        payload
        for payload in payloads
        if payload.role == PayloadRole.BREP
        and payload.format_id.casefold().strip() in _NEUTRAL_BREP_FORMAT_IDS
    )
    if any(_is_delta_payload(payload) for payload in eligible):
        return None
    body_ids = frozenset(body.id for body in bodies)
    models = tuple(
        model
        for index, payload in enumerate(eligible)
        if (model := _decode_typed_brep(payload, index, body_ids)) is not None
        and not model.validate(body_ids)
    )
    return models[0] if len(models) == 1 else None


def _decode_typed_brep(
    payload: BrepPayload,
    index: int,
    body_ids: frozenset[str],
) -> BrepModel | None:
    if payload.data is None:
        return None
    format_id = payload.format_id.casefold().strip()
    if format_id in _PARASOLID_FORMAT_IDS:
        return decode_parasolid_brep(payload.data)
    body_id = payload.attributes.get("body_id")
    design_body_id = body_id if isinstance(body_id, str) and body_id in body_ids else ""
    if not design_body_id and len(body_ids) == 1:
        design_body_id = next(iter(body_ids))
    return decode_opencascade_brep(
        payload.data,
        id_prefix=f"catia-occ:{index}",
        design_body_id=design_body_id,
        attributes={
            "format_id": payload.format_id,
            "payload_id": payload.id,
            "source_stream": payload.source_stream,
        },
    )


def _is_delta_payload(payload: BrepPayload) -> bool:
    description = payload.attributes.get("description")
    text = " ".join(
        value
        for value in (
            payload.kind,
            payload.schema,
            payload.source_stream,
            description if isinstance(description, str) else "",
        )
        if value
    ).casefold()
    return "delta" in text or (
        payload.data is not None and b"delta" in payload.data[:8192].lower()
    )


def _document_type(archive: Cfv2Archive, label: str) -> str:
    declarations = archive.declarations()
    part_declarations = tuple(
        value for value in declarations if value.class_name == "CATPrtCont"
    )
    product_declarations = tuple(
        value for value in declarations if value.class_name == "CATProdCont"
    )
    if len(part_declarations) > 1 or len(product_declarations) > 1:
        raise CatiaAdapterError("CATIA container has contradictory document roots")
    detected = ""
    if part_declarations:
        if (
            product_declarations
            and part_declarations[0].base_class != product_declarations[0].class_name
        ):
            raise CatiaAdapterError("CATIA container has contradictory document roots")
        part_role = _declared_container_role(archive, part_declarations[0])
        product_role = (
            _declared_container_role(archive, product_declarations[0])
            if product_declarations
            else PayloadRole.AUXILIARY
        )
        if part_role == PayloadRole.ASSEMBLY_STRUCTURE or product_role in {
            PayloadRole.BREP,
            PayloadRole.FEATURE_HISTORY,
            PayloadRole.TESSELLATION,
        }:
            raise CatiaAdapterError("CATIA container has contradictory document roots")
        detected = PART_DOCUMENT_TYPE
    elif product_declarations:
        if (
            _declared_container_role(archive, product_declarations[0])
            == PayloadRole.FEATURE_HISTORY
        ):
            raise CatiaAdapterError("CATIA container has contradictory document roots")
        detected = PRODUCT_DOCUMENT_TYPE
    suffix = Path(label).suffix.casefold()
    format_type = ""
    format_stream = archive.named_stream("Format")
    if format_stream is not None:
        part_marker = PART_DOCUMENT_TYPE.encode("ascii") in format_stream
        product_marker = PRODUCT_DOCUMENT_TYPE.encode("ascii") in format_stream
        if part_marker == product_marker and part_marker:
            raise CatiaAdapterError("CATIA Format stream has conflicting markers")
        if part_marker:
            format_type = PART_DOCUMENT_TYPE
        elif product_marker:
            format_type = PRODUCT_DOCUMENT_TYPE
    if detected and format_type and detected != format_type:
        raise CatiaAdapterError("CATIA container has contradictory document roots")
    detected = detected or format_type
    if not detected:
        try:
            decode_product_table(archive)
        except Cfv2FormatError:
            detected = ""
        else:
            detected = PRODUCT_DOCUMENT_TYPE
    if detected:
        expected = SUFFIX_BY_DOCUMENT_TYPE[detected]
        if suffix in DOCUMENT_TYPE_BY_SUFFIX and suffix != expected:
            raise CatiaAdapterError(f"{detected} content requires a .{detected} source")
        return detected
    if suffix in DOCUMENT_TYPE_BY_SUFFIX:
        return DOCUMENT_TYPE_BY_SUFFIX[suffix]
    raise CatiaAdapterError("cannot distinguish CATPart from CATProduct")


def _declared_container_role(
    archive: Cfv2Archive, declaration: Cfv2Declaration
) -> PayloadRole:
    stream = archive.outer.stream(declaration.stream_name)
    if stream is None:
        return PayloadRole.AUXILIARY
    payload = archive.stream_bytes(stream, archive.outer)
    return _native_container_specification(declaration, payload)[3]


def _destination_type(document: CadDocument, destination: Destination) -> str:
    suffix = (
        Path(destination).suffix.casefold()
        if isinstance(destination, (str, Path))
        else (_PRODUCT_SUFFIX if document.assembly is not None else _PART_SUFFIX)
    )
    if suffix not in DOCUMENT_TYPE_BY_SUFFIX:
        raise ValueError("CATIA destination must end in .CATPart or .CATProduct")
    if document.assembly is None and suffix != _PART_SUFFIX:
        raise ValueError("part documents require a .CATPart destination")
    if document.assembly is not None and suffix != _PRODUCT_SUFFIX:
        raise ValueError("assembly documents require a .CATProduct destination")
    return DOCUMENT_TYPE_BY_SUFFIX[suffix]


def _container_metadata(archive: Cfv2Archive) -> dict[str, object]:
    declarations: list[dict[str, object]] = []
    for declaration in archive.declarations():
        stream = archive.outer.stream(declaration.stream_name)
        if stream is None:
            continue
        payload = archive.stream_bytes(stream, archive.outer)
        declarations.append(
            {
                "ordinal": declaration.ordinal,
                "class_name": declaration.class_name,
                "base_class": declaration.base_class,
                "stream_name": declaration.stream_name,
                "descriptor_offset": stream.descriptor_offset,
                "logical_length": stream.logical_length,
                "extent_count": len(stream.extents),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    outer_streams = tuple(
        {
            "index": index,
            "name": stream.name,
            "logical_length": stream.logical_length,
            "descriptor_offset": stream.descriptor_offset,
            "extents": tuple(
                {
                    "physical_offset": archive.outer.physical_base
                    + extent.physical_offset,
                    "physical_length": extent.physical_length,
                    "logical_offset": extent.logical_offset,
                    "flags": extent.flags,
                }
                for extent in stream.extents
            ),
        }
        for index, stream in enumerate(archive.outer.streams)
    )
    nested_directories = tuple(
        {
            "physical_base": directory.physical_base,
            "offset": directory.offset,
            "length": directory.length,
            "streams": tuple(
                (stream.name, stream.logical_length) for stream in directory.streams
            ),
        }
        for directory in archive.nested
    )
    return {
        "catia.container_declarations": tuple(declarations),
        "catia.outer_stream_records": outer_streams,
        "catia.nested_directories": nested_directories,
    }


def _replay_compatibility(data: bytes) -> str:
    archive = Cfv2Archive.from_bytes(data)
    manifest = _manifest_bytes(archive)
    if manifest is None:
        return "native-exact"
    document = _manifest_document(manifest)
    if _native_base_overlay_matches(archive, document):
        return "native-base-neutral-overlay"
    return "kit-neutral-only"


def _native_base_overlay_matches(
    archive: Cfv2Archive, document: CadDocument
) -> bool:
    manifest_matches = tuple(
        (directory, stream)
        for directory in (archive.outer, *archive.nested)
        for stream in directory.streams
        if stream.name == _MANIFEST_NAME
    )
    if len(manifest_matches) != 1 or manifest_matches[0][0] is not archive.outer:
        return False
    matches = 0
    for payload in document.brep_payloads:
        if not _is_preserved_document_payload(payload) or payload.data is None:
            continue
        if hashlib.sha256(payload.data).hexdigest() != payload.sha256:
            continue
        binding = _matching_document_binding(document, payload)
        if binding is None:
            continue
        try:
            base = Cfv2Archive.from_bytes(payload.data)
            if _manifest_bytes(base) is not None:
                continue
            if (
                _document_type(base, f"candidate.{payload.schema}")
                != payload.schema
            ):
                continue
            if _overlay_preserves_native_base(
                archive,
                base,
                manifest_matches[0][1],
            ):
                matches += 1
        except (CatiaAdapterError, Cfv2FormatError, TypeError, ValueError):
            continue
    return matches == 1


def _overlay_preserves_native_base(
    overlay: Cfv2Archive,
    base: Cfv2Archive,
    manifest_stream: Cfv2Stream,
) -> bool:
    manifest = overlay.stream_bytes(manifest_stream, overlay.outer)
    if overlay.outer.offset != base.outer.offset + len(manifest):
        return False
    if overlay.data[16 : base.outer.offset] != base.data[16 : base.outer.offset]:
        return False
    if overlay.data[base.outer.offset : overlay.outer.offset] != manifest:
        return False
    base_directory = base.data[
        base.outer.offset : base.outer.offset + base.outer.length
    ]
    overlay_directory = overlay.data[
        overlay.outer.offset : overlay.outer.offset + overlay.outer.length
    ]
    descriptor_length = overlay.outer.length - base.outer.length
    descriptor_offset = manifest_stream.descriptor_offset - overlay.outer.offset
    if (
        descriptor_length <= 0
        or descriptor_offset < 0
        or descriptor_offset + descriptor_length > len(overlay_directory)
    ):
        return False
    retained_directory = b"".join(
        (
            overlay_directory[:descriptor_offset],
            overlay_directory[descriptor_offset + descriptor_length :],
        )
    )
    if retained_directory != base_directory:
        return False
    base_streams = tuple(
        (stream.name, base.stream_bytes(stream, base.outer))
        for stream in base.outer.streams
    )
    overlay_streams = tuple(
        (stream.name, overlay.stream_bytes(stream, overlay.outer))
        for stream in overlay.outer.streams
        if stream.name != _MANIFEST_NAME
    )
    return overlay_streams == base_streams


def _native_part_data(archive: Cfv2Archive, document_type: str) -> tuple[
    dict[str, object],
    tuple[SupportPlane, ...],
    tuple[FeatureStep, ...],
    tuple[Body, ...],
    tuple[Diagnostic, ...],
]:
    if document_type != PART_DOCUMENT_TYPE:
        return {}, (), (), (), ()
    part_declaration, part_stream, part_graph = _declared_osmx_role(
        archive, PayloadRole.FEATURE_HISTORY
    )
    product_declaration, product_stream, product_graph = _declared_osmx_role(
        archive, PayloadRole.ASSEMBLY_STRUCTURE
    )
    product_symbol = product_graph.first_after("ASMPRODUCT")
    part_symbol = part_graph.first_after("MechanicalPart")
    body_symbol = part_graph.first_after("MMAlias")
    product_name = product_symbol.value if product_symbol is not None else ""
    internal_part_name = part_symbol.value if part_symbol is not None else ""
    body_name = (
        body_symbol.value
        if body_symbol is not None and body_symbol.value
        else product_name or internal_part_name or "PartBody"
    )
    native_symbols = tuple(
        dict.fromkeys(symbol.value for symbol in part_graph.symbols if symbol.value)
    )
    planes = _part_planes(archive.outer, part_stream, part_graph)
    feature_id = "catia:feature:graph"
    feature = FeatureStep(
        id=feature_id,
        name="CATIA native feature graph",
        kind=FeatureKind.NATIVE,
        order=0,
        definition=NativeFeatureDefinition(
            format_id="catia.v5.osmx",
            type_id=part_declaration.class_name,
            object_data=frozen_mapping(
                {
                    "native_payload_id": "catia:native-feature-graph",
                    "symbols": part_graph.values,
                    "version": part_graph.version,
                    "symbol_table_offset": part_graph.symbol_table_offset,
                    "symbol_data_offset": part_graph.symbol_data_offset,
                }
            ),
        ),
        provenance=_stream_provenance(
            archive.outer,
            part_stream,
            f"{part_declaration.class_name}:{part_declaration.ordinal}",
            "native-feature-graph",
        ),
        attributes=frozen_mapping(
            {
                "native_symbols": native_symbols,
                "native_payload_id": "catia:native-feature-graph",
                "symbol_count": len(part_graph.symbols),
            }
        ),
    )
    body = Body(
        id="catia:body:1",
        name=body_name,
        final_feature_id=feature_id,
        provenance=(
            _symbol_provenance(archive.outer, part_stream, body_symbol, "body-alias")
            if body_symbol is not None
            else feature.provenance
        ),
        attributes=frozen_mapping(
            {
                "native_class": "MMAlias",
                "native_part_name": internal_part_name,
            }
        ),
    )
    metadata: dict[str, object] = {
        "catia.product_name": product_name,
        "catia.internal_part_name": internal_part_name,
        "catia.body_name": body_name,
        "catia.native_symbols": native_symbols,
        "catia.product_symbols": product_graph.values,
        "catia.part_symbols": part_graph.values,
        "catia.osmx_streams": (
            _osmx_metadata(
                product_stream,
                product_graph,
                product_declaration.class_name,
            ),
            _osmx_metadata(
                part_stream,
                part_graph,
                part_declaration.class_name,
            ),
        ),
    }
    diagnostic = Diagnostic(
        "catia.part.native_graph_retained",
        "The exact native feature graph, symbol table, bodies, and reference planes are retained; proprietary object records remain native.",
        Severity.INFO,
        entity_id=feature_id,
        provenance=feature.provenance,
        attributes=frozen_mapping(
            {
                "native_symbols": native_symbols,
                "symbol_count": len(part_graph.symbols),
            }
        ),
    )
    return metadata, planes, (feature,), (body,), (diagnostic,)


def _declared_osmx_role(
    archive: Cfv2Archive, role: PayloadRole
) -> tuple[Cfv2Declaration, Cfv2Stream, OsmxArchive]:
    matches: list[tuple[Cfv2Declaration, Cfv2Stream, OsmxArchive]] = []
    for declaration in archive.declarations():
        stream = archive.outer.stream(declaration.stream_name)
        if stream is None:
            continue
        data = archive.stream_bytes(stream, archive.outer)
        if _osmx_payload_role(data) != role:
            continue
        matches.append((declaration, stream, OsmxArchive.from_bytes(data)))
    if len(matches) != 1:
        raise CatiaAdapterError(
            f"CATIA container requires one {role.value} OSMX declaration"
        )
    return matches[0]


def _osmx_metadata(
    stream: Cfv2Stream, graph: OsmxArchive, class_name: str
) -> dict[str, object]:
    return {
        "class_name": class_name,
        "stream_name": stream.name,
        "logical_length": stream.logical_length,
        "version": graph.version,
        "symbol_table_offset": graph.symbol_table_offset,
        "symbol_data_offset": graph.symbol_data_offset,
        "symbol_count": len(graph.symbols),
        "sha256": hashlib.sha256(graph.data).hexdigest(),
    }


def _part_planes(
    directory: Cfv2Directory, stream: Cfv2Stream, graph: OsmxArchive
) -> tuple[SupportPlane, ...]:
    transforms = (
        Transform(),
        Transform(
            x_axis=Vector3(0.0, 1.0, 0.0),
            y_axis=Vector3(0.0, 0.0, 1.0),
            z_axis=Vector3(1.0, 0.0, 0.0),
        ),
        Transform(
            x_axis=Vector3(0.0, 0.0, 1.0),
            y_axis=Vector3(1.0, 0.0, 0.0),
            z_axis=Vector3(0.0, 1.0, 0.0),
        ),
    )
    values = graph.values
    try:
        plane_type_index = values.index("GSMPlane")
        algorithm_id_index = values.index("_PartAlgoConfigUUID")
    except ValueError:
        return ()
    indices = (plane_type_index + 1, algorithm_id_index - 2, algorithm_id_index - 1)
    if any(index < 0 or index >= len(graph.symbols) for index in indices):
        return ()
    symbols = tuple(graph.symbols[index] for index in indices)
    if len({symbol.value for symbol in symbols if symbol.value}) != len(transforms):
        return ()
    return tuple(
        SupportPlane(
            id=f"catia:plane:{index}",
            name=symbol.value,
            transform=transform,
            provenance=_symbol_provenance(directory, stream, symbol, "reference-plane"),
            attributes=frozen_mapping(
                {"native_class": "GSMPlane", "principal_index": index - 1}
            ),
        )
        for index, (symbol, transform) in enumerate(
            zip(symbols, transforms, strict=True), start=1
        )
    )


def _symbol_provenance(
    directory: Cfv2Directory,
    stream: Cfv2Stream,
    symbol: OsmxSymbol,
    record_kind: str,
) -> Provenance:
    return Provenance(
        adapter=_FORMAT_ID,
        native_id=f"{stream.name}:{symbol.offset}",
        spans=_logical_spans(
            directory,
            stream,
            symbol.offset,
            len(symbol.value),
            record_kind,
        ),
    )


def _stream_provenance(
    directory: Cfv2Directory,
    stream: Cfv2Stream,
    native_id: str,
    record_kind: str,
) -> Provenance:
    return Provenance(
        adapter=_FORMAT_ID,
        native_id=native_id,
        spans=tuple(
            ProvenanceSpan(
                stream.name,
                directory.physical_base + extent.physical_offset,
                extent.physical_length,
                record_kind,
            )
            for extent in stream.extents
        ),
    )


def _logical_spans(
    directory: Cfv2Directory,
    stream: Cfv2Stream,
    logical_offset: int,
    length: int,
    record_kind: str,
) -> tuple[ProvenanceSpan, ...]:
    end = logical_offset + length
    spans: list[ProvenanceSpan] = []
    for extent in stream.extents:
        extent_start = extent.logical_offset
        extent_end = extent_start + extent.physical_length
        overlap_start = max(logical_offset, extent_start)
        overlap_end = min(end, extent_end)
        if overlap_start >= overlap_end:
            continue
        spans.append(
            ProvenanceSpan(
                stream.name,
                directory.physical_base
                + extent.physical_offset
                + overlap_start
                - extent_start,
                overlap_end - overlap_start,
                record_kind,
            )
        )
    if sum(span.length for span in spans) != length:
        raise CatiaAdapterError("CATIA logical provenance span is incomplete")
    return tuple(spans)


def _native_payloads(
    archive: Cfv2Archive,
    data: bytes,
    document_type: str,
    settings: ReadOptions,
) -> tuple[BrepPayload, ...]:
    payloads = [
        _native_document_payload(
            archive,
            data,
            document_type,
            include_data=settings.include_brep,
        ),
        _native_document_binding(data, include_data=settings.include_brep),
    ]
    payload_ids: set[str] = {payload.id for payload in payloads}
    for declaration in archive.declarations():
        stream = archive.outer.stream(declaration.stream_name)
        if stream is None:
            continue
        payload = archive.stream_bytes(stream, archive.outer)
        payload_id, format_id, kind, role, file_extension = (
            _native_container_specification(declaration, payload)
        )
        if payload_id in payload_ids:
            payload_id = f"{payload_id}:{declaration.ordinal}"
        payload_ids.add(payload_id)
        data_included = _native_container_data_included(role, settings)
        payloads.append(
            BrepPayload(
                payload_id,
                format_id,
                kind,
                declaration.class_name,
                hashlib.sha256(payload).hexdigest(),
                payload if data_included else None,
                source_stream=stream.name,
                provenance=_stream_provenance(
                    archive.outer,
                    stream,
                    f"{declaration.class_name}:{declaration.ordinal}",
                    kind,
                ),
                attributes=frozen_mapping(
                    {
                        "declaration_ordinal": declaration.ordinal,
                        "base_class": declaration.base_class,
                        "logical_length": stream.logical_length,
                        "extent_count": len(stream.extents),
                    }
                ),
                role=role,
                file_extension=file_extension,
            )
        )
    return tuple(payloads)


def _native_container_data_included(role: PayloadRole, settings: ReadOptions) -> bool:
    if role == PayloadRole.BREP:
        return settings.include_brep
    if role == PayloadRole.TESSELLATION:
        return settings.include_tessellation
    return True


def _catia_envelope_payload(payload: BrepPayload) -> bool:
    return _is_native_document_payload(payload) or _is_native_document_binding(payload)


def _is_catia_document_payload(payload: BrepPayload) -> bool:
    return (
        payload.kind == "native_document"
        and payload.role == PayloadRole.DOCUMENT
        and payload.format_id == "catia.v5.cfv2"
    )


def _is_native_document_payload(payload: BrepPayload) -> bool:
    return payload.id == _NATIVE_DOCUMENT_ID and _is_catia_document_payload(payload)


def _is_preserved_document_payload(payload: BrepPayload) -> bool:
    return payload.id.startswith(
        _PRESERVED_DOCUMENT_PREFIX
    ) and _is_catia_document_payload(payload)


def _is_catia_document_binding(payload: BrepPayload) -> bool:
    return (
        payload.format_id == "catia.v5.sha256"
        and payload.kind == "native_document_binding"
        and payload.schema == "sha256"
        and (
            payload.role == PayloadRole.DOCUMENT
            or payload.role == PayloadRole.VERIFICATION
        )
    )


def _is_native_document_binding(payload: BrepPayload) -> bool:
    return payload.id == _NATIVE_DOCUMENT_BINDING_ID and _is_catia_document_binding(
        payload
    )


def _is_preserved_document_binding(payload: BrepPayload) -> bool:
    return payload.id.startswith(
        _PRESERVED_BINDING_PREFIX
    ) and _is_catia_document_binding(payload)


def _native_container_specification(
    declaration: Cfv2Declaration, payload: bytes
) -> tuple[str, str, str, PayloadRole, str]:
    osmx_role = _osmx_payload_role(payload)
    if osmx_role == PayloadRole.FEATURE_HISTORY:
        return (
            "catia:native-feature-graph",
            "catia.v5.osmx",
            "native_feature_graph",
            osmx_role,
            ".osmx",
        )
    if osmx_role == PayloadRole.ASSEMBLY_STRUCTURE:
        return (
            "catia:native-product-graph",
            "catia.v5.osmx",
            "native_product_graph",
            osmx_role,
            ".osmx",
        )
    if _is_cgm_payload(payload):
        return (
            "catia:native-cgm",
            "catia.cgm",
            "native_brep",
            PayloadRole.BREP,
            ".cgm",
        )
    if _is_mfbrp_payload(payload):
        return (
            "catia:native-brep-topology",
            "catia.v5.mfbrp",
            "brep_topology",
            PayloadRole.BREP,
            ".mfbrp",
        )
    if _is_brep_mode_payload(payload):
        return (
            "catia:native-brep-mode",
            "catia.v5.brep-mode",
            "brep_mode",
            PayloadRole.BREP,
            ".bin",
        )
    if _is_cgr_payload(payload):
        return (
            "catia:native-tessellation",
            "catia.cgr",
            "native_tessellation",
            PayloadRole.TESSELLATION,
            ".cgr",
        )
    return (
        f"catia:native-container:{declaration.ordinal}",
        "catia.v5.cfv2.stream",
        "native_container",
        PayloadRole.AUXILIARY,
        ".bin",
    )


def _osmx_payload_role(payload: bytes) -> PayloadRole:
    if not payload.startswith(b"OSMX"):
        return PayloadRole.AUXILIARY
    try:
        values = set(OsmxArchive.from_bytes(payload).values)
    except (OsmxFormatError, TypeError, ValueError):
        return PayloadRole.AUXILIARY
    part = "MechanicalPart" in values
    product = "ASMPRODUCT" in values
    if part == product:
        return PayloadRole.AUXILIARY
    return PayloadRole.FEATURE_HISTORY if part else PayloadRole.ASSEMBLY_STRUCTURE


def _is_cgm_payload(payload: bytes) -> bool:
    if len(payload) < 17 or payload[0] != 1:
        return False
    if struct.unpack_from("<I", payload, 1)[0] != len(payload) - 5:
        return False
    cursor = 5
    labels: list[bytes] = []
    for _ in range(2):
        if cursor + 4 > len(payload):
            return False
        length = struct.unpack_from("<I", payload, cursor)[0]
        cursor += 4
        if not length or cursor + length > len(payload):
            return False
        labels.append(payload[cursor : cursor + length])
        cursor += length
    return labels[0] == labels[1]


def _is_mfbrp_payload(payload: bytes) -> bool:
    return payload.startswith(
        b"\x0f\x00\x01\x00\x00\x00\x00\x04\x00\x00\x00\x02\x00\x05\x00\x00\x00\x38\x00\x00"
    )


def _is_brep_mode_payload(payload: bytes) -> bool:
    return payload.startswith(
        b"\x04\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00"
    )


def _is_cgr_payload(payload: bytes) -> bool:
    if not payload.startswith(b"V5_CFV2\x00"):
        return False
    try:
        archive = Cfv2Archive.from_bytes(payload)
    except (Cfv2FormatError, TypeError, ValueError):
        return False
    names = {stream.name for stream in archive.outer.streams}
    return {"SceneGraph", "SurfacicReps"} <= names


def _native_document_payload(
    archive: Cfv2Archive,
    data: bytes,
    document_type: str,
    include_data: bool,
) -> BrepPayload:
    return BrepPayload(
        _NATIVE_DOCUMENT_ID,
        "catia.v5.cfv2",
        "native_document",
        document_type,
        hashlib.sha256(data).hexdigest(),
        data if include_data else None,
        source_stream="V5_CFV2",
        provenance=Provenance(
            adapter=_FORMAT_ID,
            native_id=document_type,
            spans=(ProvenanceSpan("V5_CFV2", 0, len(data), "native-document"),),
        ),
        attributes=frozen_mapping(
            {
                "outer_directory_offset": archive.outer.offset,
                "outer_directory_length": archive.outer.length,
            }
        ),
        role=PayloadRole.DOCUMENT,
        file_extension=(
            _PRODUCT_SUFFIX if document_type == PRODUCT_DOCUMENT_TYPE else _PART_SUFFIX
        ),
    )


def _native_document_binding(data: bytes, *, include_data: bool = True) -> BrepPayload:
    native_digest = hashlib.sha256(data).digest()
    return BrepPayload(
        _NATIVE_DOCUMENT_BINDING_ID,
        "catia.v5.sha256",
        "native_document_binding",
        "sha256",
        hashlib.sha256(native_digest).hexdigest(),
        native_digest if include_data else None,
        source_stream="V5_CFV2",
        provenance=Provenance(
            adapter=_FORMAT_ID,
            native_id=hashlib.sha256(data).hexdigest(),
            spans=(ProvenanceSpan("V5_CFV2", 0, len(data), "native-document-binding"),),
        ),
        role=PayloadRole.VERIFICATION,
        file_extension=".sha256",
    )


def _application_version(data: bytes) -> str:
    match = re.search(rb"V5R\d+(?:SP\d+)?(?:HF\d+)?", data)
    return match.group().decode("ascii") if match else "CATIA V5"


def _native_base_payload(document: CadDocument, document_type: str) -> bytes | None:
    candidates = sorted(
        (
            payload
            for payload in document.brep_payloads
            if (
                _is_native_document_payload(payload)
                or _is_preserved_document_payload(payload)
            )
            and payload.schema == document_type
            and payload.data is not None
        ),
        key=_is_preserved_document_payload,
    )
    for payload in candidates:
        data = payload.data
        if data is None or hashlib.sha256(data).hexdigest() != payload.sha256:
            continue
        if _matching_document_binding(document, payload) is None:
            continue
        try:
            archive = Cfv2Archive.from_bytes(data)
            if _manifest_bytes(archive) is not None:
                continue
            if _document_type(archive, f"candidate.{document_type}") != document_type:
                continue
        except (CatiaAdapterError, Cfv2FormatError, TypeError, ValueError):
            continue
        return data
    return None


def _unchanged_native_payload(
    document: CadDocument, document_type: str
) -> tuple[bytes, bool] | None:
    expected = document.metadata.get("catia.roundtrip_sha256")
    if not isinstance(expected, str) or expected != _semantic_digest(document):
        return None
    matches = sorted(
        (
            payload
            for payload in document.brep_payloads
            if (
                _is_native_document_payload(payload)
                or _is_preserved_document_payload(payload)
            )
            and payload.schema == document_type
            and payload.data is not None
        ),
        key=_is_native_document_payload,
    )
    for payload in matches:
        data = payload.data
        if data is None or hashlib.sha256(data).hexdigest() != payload.sha256:
            continue
        binding = _matching_document_binding(document, payload)
        if binding is None:
            continue
        if _is_preserved_document_payload(payload):
            replay_digest = payload.attributes.get(_REPLAY_SEMANTIC_ATTRIBUTE)
            if not isinstance(
                replay_digest, str
            ) or replay_digest != _preserved_replay_digest(document, payload, binding):
                continue
        if _native_payload_matches_document(
            document,
            data,
            document_type,
            payload,
            binding,
        ):
            return data, _is_preserved_document_payload(payload)
    return None


def _native_candidate_is_unchanged(document: CadDocument, payload: BrepPayload) -> bool:
    expected = document.metadata.get("catia.roundtrip_sha256")
    if not isinstance(expected, str) or expected != _semantic_digest(document):
        return False
    data = payload.data
    if data is None or hashlib.sha256(data).hexdigest() != payload.sha256:
        return False
    binding = _matching_document_binding(document, payload)
    if binding is None:
        return False
    return _native_payload_matches_document(
        document,
        data,
        payload.schema,
        payload,
        binding,
    )


def _matching_document_binding(
    document: CadDocument, native_document: BrepPayload
) -> BrepPayload | None:
    if _is_native_document_payload(native_document):
        binding_id = _NATIVE_DOCUMENT_BINDING_ID
    elif _is_preserved_document_payload(native_document):
        token = native_document.id.removeprefix(_PRESERVED_DOCUMENT_PREFIX)
        binding_id = f"{_PRESERVED_BINDING_PREFIX}{token}"
    else:
        return None
    matches = tuple(
        payload
        for payload in document.brep_payloads
        if payload.id == binding_id
        and _is_catia_document_binding(payload)
        and _binding_matches_payload(payload, native_document)
    )
    if len(matches) != 1:
        return None
    return matches[0]


def _binding_matches_payload(
    binding: BrepPayload, native_document: BrepPayload
) -> bool:
    try:
        native_digest = bytes.fromhex(native_document.sha256)
    except ValueError:
        return False
    if len(native_digest) != hashlib.sha256().digest_size:
        return False
    if (
        native_document.data is not None
        and hashlib.sha256(native_document.data).digest() != native_digest
    ):
        return False
    if binding.data is not None and binding.data != native_digest:
        return False
    return binding.sha256 == hashlib.sha256(native_digest).hexdigest()


def _preserved_replay_digest(
    document: CadDocument,
    native_document: BrepPayload,
    binding: BrepPayload,
) -> str:
    ignored_ids = {native_document.id, binding.id}
    stripped = replace(
        document,
        brep_payloads=tuple(
            payload
            for payload in document.brep_payloads
            if payload.id not in ignored_ids
        ),
    )
    return _carrier_semantic_digest(stripped)


def _native_payload_matches_document(
    document: CadDocument,
    data: bytes,
    document_type: str,
    native_document: BrepPayload,
    binding: BrepPayload,
) -> bool:
    try:
        archive = Cfv2Archive.from_bytes(data)
        if _document_type(archive, f"candidate.{document_type}") != document_type:
            return False
        if not _native_document_binding_matches(native_document, binding, data):
            return False
        manifest = _manifest_bytes(archive)
        if manifest is not None:
            embedded = _manifest_document(manifest)
            return _carrier_semantic_digest(embedded) == _carrier_semantic_digest(
                document
            )
        if document_type == PRODUCT_DOCUMENT_TYPE:
            table = decode_product_table(archive)
            assembly = document.assembly
            if assembly is None:
                return False
            definitions = {item.id: item for item in assembly.definitions}
            root = definitions.get(assembly.root_definition_id)
            if root is None or root.name != table.root_name:
                return False
            expected = tuple(
                (definitions[item.definition_id].name, item.name)
                for item in assembly.instances
            )
            actual = tuple(
                (item.definition_name, item.instance_name) for item in table.occurrences
            )
            if expected != actual:
                return False
        include_tessellation = any(
            payload.role == PayloadRole.TESSELLATION and payload.data is not None
            for payload in document.brep_payloads
        )
        candidate = _native_payloads(
            archive,
            data,
            document_type,
            ReadOptions(
                include_brep=True,
                include_tessellation=include_tessellation,
            ),
        )
    except (CatiaAdapterError, Cfv2FormatError, TypeError, ValueError, zlib.error):
        return False
    candidate_native = {
        payload.id: _payload_signature(payload)
        for payload in candidate
        if not _is_catia_document_payload(payload)
        and not _is_catia_document_binding(payload)
    }
    expected = {
        payload.id: _payload_signature(payload)
        for payload in document.brep_payloads
        if payload.id in candidate_native
    }
    return expected == candidate_native


def _payload_signature(payload: BrepPayload) -> tuple[str, str, str, str, str, str]:
    return (
        payload.format_id,
        payload.kind,
        payload.schema,
        payload.role.value,
        payload.file_extension,
        (
            hashlib.sha256(payload.data).hexdigest()
            if payload.data is not None
            else payload.sha256
        ),
    )


def _native_document_binding_matches(
    native_document: BrepPayload,
    binding: BrepPayload,
    data: bytes,
) -> bool:
    native_digest = hashlib.sha256(data).digest()
    return (
        native_document.data == data
        and native_document.sha256 == native_digest.hex()
        and binding.data == native_digest
        and binding.sha256 == hashlib.sha256(native_digest).hexdigest()
    )


def _semantic_digest(document: CadDocument) -> str:
    return _document_digest(document, _is_native_document_payload)


def _carrier_semantic_digest(document: CadDocument) -> str:
    return _document_digest(document, _catia_envelope_payload)


def _document_digest(
    document: CadDocument, ignored_payload: Callable[[BrepPayload], bool]
) -> str:
    value = _digest_document(document, ignored_payload)
    return hashlib.sha256(value.to_json(indent=None).encode("utf-8")).hexdigest()


def _digest_document(
    document: CadDocument,
    ignored_payload: Callable[[BrepPayload], bool],
) -> CadDocument:
    payloads = tuple(
        replace(
            payload,
            data=None,
            sha256=(
                hashlib.sha256(payload.data).hexdigest()
                if payload.data is not None
                else payload.sha256
            ),
        )
        for payload in document.brep_payloads
        if not ignored_payload(payload)
    )
    nested = document.assembly
    if nested is not None:
        nested = replace(
            nested,
            documents=tuple(
                replace(
                    item,
                    document=(
                        _digest_document(item.document, ignored_payload)
                        if isinstance(item.document, CadDocument)
                        else item.document
                    ),
                )
                for item in nested.documents
            ),
        )
    return replace(
        document,
        source=CadSource("", "", ""),
        brep_payloads=payloads,
        metadata=semantic_metadata(document.metadata),
        assembly=nested,
    )


def read_catia(source: Source, options: ReadOptions | None = None) -> CadDocument:
    return CatiaAdapter().read(source, options)


def write_catia(
    document: CadDocument,
    destination: Destination,
    *,
    overwrite: bool = False,
    validate: bool = True,
    allow_non_native: bool = True,
) -> WriteResult:
    return CatiaAdapter().write(
        document,
        destination,
        WriteOptions(
            overwrite=overwrite,
            validate=validate,
            values=frozen_mapping({"allow_non_native": allow_non_native}),
        ),
    )

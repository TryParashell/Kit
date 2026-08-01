from __future__ import annotations

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
)
from interchange import (
    AssemblyData,
    Body,
    BrepPayload,
    CadDocument,
    CadSource,
    Capability,
    ComponentDefinition,
    ComponentInstance,
    ComponentKind,
    Configuration,
    Diagnostic,
    FeatureKind,
    FeatureStep,
    Provenance,
    ProvenanceSpan,
    Severity,
    SupportPlane,
    Transform,
    Vector3,
    frozen_mapping,
)

from .container import (
    Cfv2Archive,
    Cfv2Declaration,
    Cfv2Directory,
    Cfv2FormatError,
    Cfv2Stream,
    OsmxArchive,
    build_cfv2,
    build_declaration,
    extract_ascii_values,
)


_FORMAT_ID = "catia.v5"
_MANIFEST_NAME = "KitInterchange"
_MANIFEST_MAGIC = b"KITCFV2\x01"
_PART_STREAM = "1000_00000002_2"
_PRODUCT_STREAM = "1000_00000001_1"
_PART_SUFFIX = ".catpart"
_PRODUCT_SUFFIX = ".catproduct"
_PART_FEATURE_CLASSES = frozenset(
    {
        "BooleanAdd",
        "BooleanRemove",
        "Chamfer",
        "CircPattern",
        "Draft",
        "EdgeFillet",
        "Groove",
        "GSMBlend",
        "GSMCircle",
        "GSMExtrude",
        "GSMExtract",
        "GSMFill",
        "GSMIntersect",
        "GSMJoin",
        "GSMLine",
        "GSMOffset",
        "GSMPoint",
        "GSMPointCoord",
        "GSMRevol",
        "GSMRotate",
        "GSMScaling",
        "GSMShapeFillet",
        "GSMSplit",
        "GSMSweep",
        "GSMSymmetry",
        "GSMTranslate",
        "GSMAxisToAxis",
        "Hole",
        "Mirror",
        "Pad",
        "Pocket",
        "RectPattern",
        "Shaft",
        "Shell",
        "Sketch",
        "Sketcher",
        "ThickSurface",
        "UserPattern",
    }
)


class CatiaAdapterError(RuntimeError):
    __slots__ = ()


class CatiaAdapter:
    @property
    def info(self) -> AdapterInfo:
        return AdapterInfo(
            format_id=_FORMAT_ID,
            name="CATIA V5",
            version="5",
            extensions=(".catpart", ".catproduct"),
            capabilities=frozenset(
                {
                    Capability.PARAMETRIC_HISTORY,
                    Capability.EDITABLE_SKETCHES,
                    Capability.EXPRESSIONS,
                    Capability.BREP,
                    Capability.TESSELLATION,
                    Capability.ASSEMBLIES,
                    Capability.MATERIALS,
                    Capability.NATIVE_PAYLOADS,
                    Capability.ROUNDTRIP_METADATA,
                }
            ),
            media_types=(
                "application/x-catia-part",
                "application/x-catia-product",
            ),
        )

    def probe(self, source: Source) -> ProbeResult:
        try:
            data, _ = _source_bytes(source)
            archive = Cfv2Archive.from_bytes(data)
        except (Cfv2FormatError, OSError, TypeError, ValueError) as exc:
            return ProbeResult(_FORMAT_ID, 0.0, str(exc))
        if _manifest_bytes(archive) is not None:
            return ProbeResult(_FORMAT_ID, 1.0, "Kit manifest in V5_CFV2")
        declarations = archive.declarations()
        if declarations:
            return ProbeResult(_FORMAT_ID, 1.0, "native CATIA container graph")
        return ProbeResult(_FORMAT_ID, 0.9, "valid V5_CFV2 stream directory")

    def read(self, source: Source, options: ReadOptions | None = None) -> CadDocument:
        settings = options or ReadOptions()
        data, label = _source_bytes(source)
        archive = Cfv2Archive.from_bytes(data)
        manifest = _manifest_bytes(archive)
        if manifest is not None:
            return _embedded_document(archive, data, label, manifest, settings)
        document_type = _document_type(archive, label)
        payloads = _native_payloads(archive, data, document_type, settings)
        assembly, assembly_diagnostics = _native_assembly(data, label, document_type)
        (
            part_metadata,
            support_planes,
            feature_timeline,
            bodies,
            part_diagnostics,
        ) = _native_part_data(archive, document_type)
        version = _application_version(data)
        capabilities = {
            Capability.NATIVE_PAYLOADS,
            Capability.ROUNDTRIP_METADATA,
        }
        if _has_brep_payload(payloads):
            capabilities.add(Capability.BREP)
        if any(
            payload.kind == "native_feature_graph" and payload.data is not None
            for payload in payloads
        ):
            capabilities.add(Capability.PARAMETRIC_HISTORY)
        if any(
            payload.format_id == "catia.cgr" and payload.data is not None
            for payload in payloads
        ):
            capabilities.add(Capability.TESSELLATION)
        if assembly is not None:
            capabilities.add(Capability.ASSEMBLIES)
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
            diagnostics=assembly_diagnostics + part_diagnostics,
            capabilities=frozenset(capabilities),
            metadata=frozen_mapping(metadata),
            assembly=assembly,
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
            return Path(destination).suffix.lower() in {
                _PART_SUFFIX,
                _PRODUCT_SUFFIX,
            }
        return hasattr(destination, "write")

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
        native = _unchanged_native_payload(document, document_type)
        if native is not None and not settings.values.get("rebuild", False):
            path = _write_bytes(destination, native, settings.overwrite)
            return WriteResult(
                path,
                _FORMAT_ID,
                len(native),
                metadata=MappingProxyType(
                    {
                        "mode": "exact_native_roundtrip",
                        "container": "V5_CFV2",
                        "document_type": document_type,
                    }
                ),
            )
        if settings.values.get("allow_non_native") is not True:
            raise CatiaAdapterError(
                "generated CATIA writing requires "
                "WriteOptions(values={'allow_non_native': True})"
            )
        data = _generated_archive(document, document_type)
        restored = _restore_generated(data)
        if restored != document:
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
            diagnostics=(diagnostic,),
            metadata=MappingProxyType(
                {
                    "mode": "generated_cfv2",
                    "compatibility": "kit-neutral-only",
                    "native_feature_graph": False,
                    "container": "V5_CFV2",
                    "document_type": document_type,
                    "outer_stream_count": len(archive.outer.streams),
                    "nested_directory_count": len(archive.nested),
                    "manifest_sha256": hashlib.sha256(
                        document.to_json(indent=None).encode("utf-8")
                    ).hexdigest(),
                }
            ),
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
    if document_type == "CATProduct":
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
    if document_type == "CATPart":
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
    expected = data[len(_MANIFEST_MAGIC) + 8 : header]
    raw = zlib.decompress(data[header:])
    if len(raw) != length or hashlib.sha256(raw).digest() != expected:
        raise ValueError("CATIA Kit manifest checksum mismatch")
    return raw.decode("utf-8")


def _manifest_bytes(archive: Cfv2Archive) -> bytes | None:
    values: list[bytes] = []
    outer = archive.named_stream(_MANIFEST_NAME)
    if outer is not None:
        values.append(outer)
    for directory in archive.nested:
        stream = directory.stream(_MANIFEST_NAME)
        if stream is not None:
            values.append(archive.stream_bytes(stream, directory))
    if not values:
        return None
    if len(values) != 1:
        raise Cfv2FormatError("multiple CATIA Kit manifests")
    return values[0]


def _restore_generated(data: bytes) -> CadDocument:
    archive = Cfv2Archive.from_bytes(data)
    manifest = _manifest_bytes(archive)
    if manifest is None:
        raise CatiaAdapterError("generated V5_CFV2 has no Kit manifest")
    return CadDocument.from_json(_unpack_manifest(manifest))


def _embedded_document(
    archive: Cfv2Archive,
    data: bytes,
    label: str,
    manifest: bytes,
    settings: ReadOptions,
) -> CadDocument:
    try:
        embedded = CadDocument.from_json(_unpack_manifest(manifest))
    except (TypeError, ValueError, zlib.error) as exc:
        raise CatiaAdapterError("invalid Kit document in V5_CFV2") from exc
    configurations = _selected_configurations(
        embedded.configurations, settings.configuration
    )
    document_type = _document_type(archive, label)
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
        }
    )
    if settings.include_brep:
        retained = tuple(
            payload
            for payload in embedded.brep_payloads
            if not (
                payload.format_id == "catia.v5.cfv2"
                and payload.kind == "native_document"
            )
        )
        physical = _native_document_payload(
            archive, data, document_type, include_data=True
        )
        payloads = (*retained, physical)
    else:
        payloads = ()
    capabilities = set(embedded.capabilities)
    capabilities.update({Capability.NATIVE_PAYLOADS, Capability.ROUNDTRIP_METADATA})
    if not _has_brep_payload(payloads):
        capabilities.discard(Capability.BREP)
    document = replace(
        embedded,
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
        configurations=configurations,
        brep_payloads=tuple(payloads),
        capabilities=frozenset(capabilities),
        metadata=frozen_mapping(metadata),
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


def _has_brep_payload(payloads: tuple[BrepPayload, ...]) -> bool:
    formats = {
        "acis",
        "acis.sat",
        "catia.cgm",
        "opencascade",
        "parasolid",
        "parasolid.x_t",
    }
    return any(
        payload.data is not None and payload.format_id.casefold() in formats
        for payload in payloads
    )


def _document_type(archive: Cfv2Archive, label: str) -> str:
    classes = {value.class_name for value in archive.declarations()}
    if "CATPrtCont" in classes:
        return "CATPart"
    if "CATProdCont" in classes:
        return "CATProduct"
    suffix = Path(label).suffix.lower()
    if suffix == _PART_SUFFIX:
        return "CATPart"
    if suffix == _PRODUCT_SUFFIX:
        return "CATProduct"
    format_stream = archive.named_stream("Format")
    if format_stream is not None:
        if b"CATPart" in format_stream:
            return "CATPart"
        if b"CATProduct" in format_stream:
            return "CATProduct"
    raise CatiaAdapterError("cannot distinguish CATPart from CATProduct")


def _destination_type(document: CadDocument, destination: Destination) -> str:
    suffix = (
        Path(destination).suffix.lower()
        if isinstance(destination, (str, Path))
        else (_PRODUCT_SUFFIX if document.assembly is not None else _PART_SUFFIX)
    )
    if suffix not in {_PART_SUFFIX, _PRODUCT_SUFFIX}:
        raise ValueError("CATIA destination must end in .CATPart or .CATProduct")
    if suffix == _PART_SUFFIX and document.assembly is not None:
        raise ValueError("assembly documents require a .CATProduct destination")
    if suffix == _PRODUCT_SUFFIX and document.assembly is None:
        raise ValueError("part documents require a .CATPart destination")
    return "CATProduct" if suffix == _PRODUCT_SUFFIX else "CATPart"


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


def _native_part_data(archive: Cfv2Archive, document_type: str) -> tuple[
    dict[str, object],
    tuple[SupportPlane, ...],
    tuple[FeatureStep, ...],
    tuple[Body, ...],
    tuple[Diagnostic, ...],
]:
    if document_type != "CATPart":
        return {}, (), (), (), ()
    part_declaration, part_stream, part_graph = _declared_osmx(archive, "CATPrtCont")
    _, product_stream, product_graph = _declared_osmx(archive, "CATProdCont")
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
    native_classes = tuple(
        dict.fromkeys(
            symbol.value
            for symbol in part_graph.symbols
            if symbol.value in _PART_FEATURE_CLASSES
        )
    )
    planes = _part_planes(archive.outer, part_stream, part_graph)
    feature_id = "catia:feature:graph"
    feature = FeatureStep(
        id=feature_id,
        name="CATIA native feature graph",
        kind=FeatureKind.NATIVE,
        order=0,
        provenance=_stream_provenance(
            archive.outer,
            part_stream,
            f"{part_declaration.class_name}:{part_declaration.ordinal}",
            "native-feature-graph",
        ),
        attributes=frozen_mapping(
            {
                "native_classes": native_classes,
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
        "catia.native_feature_classes": native_classes,
        "catia.product_symbols": product_graph.values,
        "catia.part_symbols": part_graph.values,
        "catia.osmx_streams": (
            _osmx_metadata(product_stream, product_graph, "CATProdCont"),
            _osmx_metadata(part_stream, part_graph, "CATPrtCont"),
        ),
    }
    diagnostic = Diagnostic(
        "catia.part.native_graph_retained",
        "The exact CATPrtCont feature graph, symbol table, bodies, and reference planes are retained; proprietary object records remain native.",
        Severity.INFO,
        entity_id=feature_id,
        provenance=feature.provenance,
        attributes=frozen_mapping(
            {
                "native_classes": native_classes,
                "symbol_count": len(part_graph.symbols),
            }
        ),
    )
    return metadata, planes, (feature,), (body,), (diagnostic,)


def _declared_osmx(
    archive: Cfv2Archive, class_name: str
) -> tuple[Cfv2Declaration, Cfv2Stream, OsmxArchive]:
    matches = tuple(
        declaration
        for declaration in archive.declarations()
        if declaration.class_name == class_name
    )
    if len(matches) != 1:
        raise CatiaAdapterError(
            f"CATIA container requires one {class_name} declaration"
        )
    declaration = matches[0]
    stream = archive.outer.stream(declaration.stream_name)
    if stream is None:
        raise CatiaAdapterError(f"CATIA {class_name} stream is missing")
    return (
        declaration,
        stream,
        OsmxArchive.from_bytes(archive.stream_bytes(stream, archive.outer)),
    )


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
    definitions = (
        (
            "xy-plane",
            Transform(),
        ),
        (
            "yz-plane",
            Transform(
                x_axis=Vector3(0.0, 1.0, 0.0),
                y_axis=Vector3(0.0, 0.0, 1.0),
                z_axis=Vector3(1.0, 0.0, 0.0),
            ),
        ),
        (
            "zx-plane",
            Transform(
                x_axis=Vector3(0.0, 0.0, 1.0),
                y_axis=Vector3(1.0, 0.0, 0.0),
                z_axis=Vector3(0.0, 1.0, 0.0),
            ),
        ),
    )
    symbols = {symbol.value: symbol for symbol in graph.symbols}
    return tuple(
        SupportPlane(
            id=f"catia:plane:{index}",
            name=name,
            transform=transform,
            provenance=_symbol_provenance(
                directory, stream, symbols[name], "reference-plane"
            ),
            attributes=frozen_mapping({"native_class": "GSMPlane"}),
        )
        for index, (name, transform) in enumerate(definitions, start=1)
        if name in symbols
    )


def _symbol_provenance(
    directory: Cfv2Directory,
    stream: Cfv2Stream,
    symbol: object,
    record_kind: str,
) -> Provenance:
    offset = int(getattr(symbol, "offset"))
    value = str(getattr(symbol, "value"))
    return Provenance(
        adapter=_FORMAT_ID,
        native_id=f"{stream.name}:{offset}",
        spans=_logical_spans(directory, stream, offset, len(value), record_kind),
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
        )
    ]
    if document_type != "CATPart":
        return tuple(payloads)
    requested = ["CATPrtCont", "CATProdCont"]
    if settings.include_brep:
        requested = ["CGMGeom", *requested, "CATMFBRP"]
    if settings.include_tessellation:
        requested.append("CATCGRCont")
    specifications = {
        "CGMGeom": ("catia:native-cgm", "catia.cgm", "native_brep"),
        "CATPrtCont": (
            "catia:native-feature-graph",
            "catia.v5.osmx",
            "native_feature_graph",
        ),
        "CATProdCont": (
            "catia:native-product-graph",
            "catia.v5.osmx",
            "native_product_graph",
        ),
        "CATMFBRP": (
            "catia:native-brep-topology",
            "catia.v5.mfbrp",
            "brep_topology",
        ),
        "CATCGRCont": (
            "catia:native-tessellation",
            "catia.cgr",
            "native_tessellation",
        ),
    }
    declarations = {value.class_name: value for value in archive.declarations()}
    for class_name in requested:
        declaration = declarations.get(class_name)
        if declaration is None:
            continue
        stream = archive.outer.stream(declaration.stream_name)
        if stream is None:
            continue
        payload = archive.stream_bytes(stream, archive.outer)
        payload_id, format_id, kind = specifications[class_name]
        payloads.append(
            BrepPayload(
                payload_id,
                format_id,
                kind,
                class_name,
                hashlib.sha256(payload).hexdigest(),
                payload,
                source_stream=stream.name,
                provenance=_stream_provenance(
                    archive.outer,
                    stream,
                    f"{class_name}:{declaration.ordinal}",
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
            )
        )
    return tuple(payloads)


def _native_document_payload(
    archive: Cfv2Archive,
    data: bytes,
    document_type: str,
    include_data: bool,
) -> BrepPayload:
    return BrepPayload(
        "catia:native-document",
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
    )


def _application_version(data: bytes) -> str:
    match = re.search(rb"V5R\d+(?:SP\d+)?(?:HF\d+)?", data)
    return match.group().decode("ascii") if match else "CATIA V5"


def _native_assembly(
    data: bytes, label: str, document_type: str
) -> tuple[AssemblyData | None, tuple[Diagnostic, ...]]:
    if document_type != "CATProduct":
        return None, ()
    strings = extract_ascii_values(data, minimum=3)
    root_name = Path(label).stem
    try:
        marker = strings.index("ASMPRODUCT")
        if marker + 1 < len(strings):
            root_name = strings[marker + 1]
    except ValueError:
        marker = 0
    instances = _product_instances(strings[marker:])
    root_id = "catia:assembly:root"
    definitions: list[ComponentDefinition] = [
        ComponentDefinition(root_id, root_name, ComponentKind.ASSEMBLY)
    ]
    definition_ids: dict[str, str] = {}
    component_instances: list[ComponentInstance] = []
    for order, (definition_name, instance_name) in enumerate(instances):
        definition_id = definition_ids.get(definition_name)
        if definition_id is None:
            definition_id = f"catia:definition:{len(definition_ids) + 1}"
            definition_ids[definition_name] = definition_id
            definitions.append(
                ComponentDefinition(
                    definition_id,
                    definition_name,
                    ComponentKind.PART,
                    source_path=definition_name + ".CATPart",
                    source_format_id=_FORMAT_ID,
                )
            )
        component_instances.append(
            ComponentInstance(
                f"catia:instance:{order + 1}",
                instance_name,
                definition_id,
                root_id,
                order=order,
            )
        )
    assembly = AssemblyData(
        root_definition_id=root_id,
        definitions=tuple(definitions),
        instances=tuple(component_instances),
        attributes=frozen_mapping({"native_structure": "ASMPRODUCT"}),
    )
    diagnostics = (
        Diagnostic(
            "catia.product.transforms_unresolved",
            "Native CATProduct instance names are retained; proprietary position and constraint records remain in the exact native payload.",
            Severity.WARNING,
        ),
    )
    return assembly, diagnostics


def _product_instances(values: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    ignored = {
        "_InstanceName",
        "_Position",
        "_Reps",
        "PRDREP",
        "Shape 1",
        "IsRoot",
    }
    candidates = [value for value in values if value not in ignored]
    results: list[tuple[str, str]] = []
    prior = ""
    for value in candidates:
        if "!I_" in value:
            definition = value.split("!I_", 1)[0]
            if definition:
                results.append((definition, value))
            prior = value
            continue
        prefixed = re.fullmatch(r"I_(.+)\.(\d+)", value)
        if prefixed:
            results.append((prefixed.group(1), value))
            prior = value
            continue
        numbered = re.fullmatch(r"(.+)\.(\d+)", value)
        if numbered and prior == numbered.group(1):
            results.append((prior, value))
        prior = value
    unique: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for value in results:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return tuple(unique)


def _unchanged_native_payload(
    document: CadDocument, document_type: str
) -> bytes | None:
    expected = document.metadata.get("catia.roundtrip_sha256")
    if not isinstance(expected, str) or expected != _semantic_digest(document):
        return None
    matches = [
        payload
        for payload in document.brep_payloads
        if payload.format_id == "catia.v5.cfv2"
        and payload.kind == "native_document"
        and payload.schema == document_type
        and payload.data is not None
    ]
    if len(matches) != 1:
        return None
    data = matches[0].data
    if data is None or hashlib.sha256(data).hexdigest() != matches[0].sha256:
        return None
    if not _native_payload_matches_document(document, data, document_type):
        return None
    return data


def _native_payload_matches_document(
    document: CadDocument, data: bytes, document_type: str
) -> bool:
    try:
        archive = Cfv2Archive.from_bytes(data)
        if _document_type(archive, f"candidate.{document_type}") != document_type:
            return False
        manifest = _manifest_bytes(archive)
        if manifest is not None:
            embedded = CadDocument.from_json(_unpack_manifest(manifest))
            return _semantic_digest(embedded) == _semantic_digest(document)
        if document_type == "CATProduct":
            assembly, _ = _native_assembly(data, "candidate.CATProduct", document_type)
            return assembly == document.assembly
        include_tessellation = any(
            payload.id == "catia:native-tessellation"
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
    native_ids = {
        "catia:native-cgm",
        "catia:native-feature-graph",
        "catia:native-product-graph",
        "catia:native-brep-topology",
        "catia:native-tessellation",
    }
    expected = {
        payload.id: (
            payload.format_id,
            payload.kind,
            payload.schema,
            (
                hashlib.sha256(payload.data).hexdigest()
                if payload.data is not None
                else payload.sha256
            ),
        )
        for payload in document.brep_payloads
        if payload.id in native_ids
    }
    actual = {
        payload.id: (
            payload.format_id,
            payload.kind,
            payload.schema,
            (
                hashlib.sha256(payload.data).hexdigest()
                if payload.data is not None
                else payload.sha256
            ),
        )
        for payload in candidate
        if payload.id in native_ids
    }
    return expected == actual and {
        "catia:native-cgm",
        "catia:native-feature-graph",
        "catia:native-product-graph",
        "catia:native-brep-topology",
    }.issubset(actual)


def _semantic_digest(document: CadDocument) -> str:
    payloads = tuple(
        replace(
            payload,
            data=None,
            sha256=(
                hashlib.sha256(payload.data).hexdigest()
                if payload.data is not None
                else payload.sha256
            ),
            source_stream="",
            provenance=None,
            attributes=frozen_mapping(),
        )
        for payload in document.brep_payloads
        if payload.kind != "native_document"
    )
    value = replace(
        document,
        source=CadSource("", "", ""),
        brep_payloads=payloads,
        diagnostics=(),
        capabilities=frozenset(),
        metadata=frozen_mapping(),
    )
    return hashlib.sha256(value.to_json(indent=None).encode("utf-8")).hexdigest()


def read_catia(source: Source, options: ReadOptions | None = None) -> CadDocument:
    return CatiaAdapter().read(source, options)


def write_catia(
    document: CadDocument,
    destination: Destination,
    *,
    overwrite: bool = False,
    validate: bool = True,
    allow_non_native: bool = False,
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

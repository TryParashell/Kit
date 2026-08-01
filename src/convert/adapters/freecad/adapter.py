from __future__ import annotations

import base64
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime, timezone
from enum import Enum
import io
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, BinaryIO
import xml.etree.ElementTree as ET
import zipfile

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
from interchange import (
    CadDocument,
    CadSource,
    Capability,
    ComponentDefinition,
    ComponentKind,
    Configuration,
    Mesh,
)

from .archive import MANIFEST_ENTRY, build_fcstd_archive, extract_manifest_from_fcstd
from .native import NativeFreeCADError, probe_native_fcstd, read_native_fcstd


class FreeCADAdapterError(RuntimeError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


_WINDOWS_RESERVED_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }
)


def _plain(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return {"$bytes": base64.b64encode(value).decode("ascii")}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return {"$enum": type(value).__name__, "value": _plain(value.value)}
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _plain(to_dict())
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, Sequence):
        return [_plain(item) for item in value]
    fields = getattr(value, "__dict__", None)
    if isinstance(fields, dict):
        return {
            str(key): _plain(item)
            for key, item in fields.items()
            if not str(key).startswith("_")
        }
    raise TypeError(
        f"cannot serialize {type(value).__name__} into the FreeCAD manifest"
    )


def document_to_manifest(document: Any) -> dict[str, Any]:
    manifest = _plain(document)
    if not isinstance(manifest, dict):
        raise TypeError("CadDocument.to_dict() must produce a mapping")
    required = {
        "source",
        "configurations",
        "parameters",
        "support_planes",
        "sketches",
        "selections",
        "feature_timeline",
        "bodies",
        "meshes",
        "brep_payloads",
        "diagnostics",
        "capabilities",
        "metadata",
    }
    if manifest.get("$type") == "CadDocument":
        missing = sorted(required.difference(manifest))
        if missing:
            raise ValueError("CadDocument manifest is missing: " + ", ".join(missing))
    return manifest


def _source_bytes(source: Source) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, bytearray):
        return bytes(source)
    if isinstance(source, (str, Path)):
        return Path(source).expanduser().resolve().read_bytes()
    reader = getattr(source, "read", None)
    if callable(reader):
        position = None
        tell = getattr(source, "tell", None)
        seek = getattr(source, "seek", None)
        if callable(tell):
            try:
                position = tell()
            except (OSError, ValueError):
                position = None
        data = reader()
        if position is not None and callable(seek):
            try:
                seek(position)
            except (OSError, ValueError):
                position = None
        if isinstance(data, str):
            raise TypeError("FCStd input must be opened in binary mode")
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
    raise TypeError("source must be a path, bytes, or binary stream")


def _destination_path(destination: Destination) -> Path | None:
    if isinstance(destination, (str, Path)):
        return Path(destination).expanduser().resolve()
    return None


def _source_path(source: Source) -> str:
    if isinstance(source, (str, Path)):
        return str(Path(source).expanduser().resolve())
    name = getattr(source, "name", "")
    return str(name) if isinstance(name, (str, Path)) else ""


def _write_bytes(destination: Destination, data: bytes, overwrite: bool) -> Path | None:
    path = _destination_path(destination)
    if path is None:
        writer = getattr(destination, "write", None)
        if not callable(writer):
            raise TypeError("destination must be a path or binary stream")
        try:
            written = writer(data)
        except TypeError as exc:
            raise TypeError("FCStd destination must be opened in binary mode") from exc
        if written is not None and written != len(data):
            raise OSError(
                f"short FCStd write: expected {len(data)} bytes, wrote {written}"
            )
        return None
    if path.suffix.lower() != ".fcstd":
        raise ValueError("FreeCAD destination must end in .FCStd")
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise
    return path


def _component_stem(value: str) -> str:
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    stem = stem or "Component"
    if stem.upper() in _WINDOWS_RESERVED_NAMES:
        stem += "_"
    return stem[:120].rstrip(" .") or "Component"


def _component_paths(document: CadDocument, destination: Path) -> dict[str, Path]:
    assembly = document.assembly
    if assembly is None:
        return {}
    documents = {item.id for item in assembly.documents}
    directory = destination.parent / destination.stem
    used: set[str] = set()
    result: dict[str, Path] = {}
    for definition in assembly.definitions:
        if definition.id == assembly.root_definition_id:
            continue
        if definition.document_id not in documents and not definition.mesh_ids:
            continue
        base = _component_stem(definition.name or definition.id)
        candidate = base
        suffix = 1
        while candidate.casefold() in used:
            suffix += 1
            ending = f"_{suffix}"
            candidate = base[: 120 - len(ending)].rstrip(" .") + ending
        used.add(candidate.casefold())
        result[definition.id] = directory / f"{candidate}.FCStd"
    return result


def _selected_meshes(
    document: CadDocument, definition: ComponentDefinition
) -> tuple[Mesh, ...]:
    meshes = {item.id: item for item in document.meshes}
    missing = [mesh_id for mesh_id in definition.mesh_ids if mesh_id not in meshes]
    if missing:
        raise FreeCADAdapterError(
            f"component definition {definition.id!r} references missing meshes: "
            + ", ".join(missing)
        )
    return tuple(meshes[mesh_id] for mesh_id in definition.mesh_ids)


def _mesh_component_document(
    document: CadDocument,
    definition: ComponentDefinition,
    meshes: tuple[Mesh, ...],
) -> CadDocument:
    source = CadSource(
        format_id=definition.source_format_id or document.source.format_id,
        path=definition.source_path or definition.name or definition.id,
        sha256=definition.source_sha256,
        container_version=document.source.container_version,
        application_version=document.source.application_version,
        attributes=definition.attributes,
    )
    configuration_name = definition.configuration_name or "Default"
    configuration_id = (
        definition.configuration_id or f"{definition.id}:configuration:default"
    )
    return CadDocument(
        source=source,
        configurations=(
            Configuration(configuration_id, configuration_name, active=True),
        ),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        meshes=meshes,
        capabilities=frozenset({Capability.TESSELLATION}),
        units=document.units,
        schema_version=document.schema_version,
    )


def _component_document(
    document: CadDocument,
    definition: ComponentDefinition,
    documents: Mapping[str, CadDocument],
) -> CadDocument | None:
    selected_meshes = _selected_meshes(document, definition)
    linked = documents.get(definition.document_id)
    if linked is None:
        return (
            _mesh_component_document(document, definition, selected_meshes)
            if selected_meshes
            else None
        )
    selected_ids = {mesh.id for mesh in selected_meshes}
    meshes = (
        *selected_meshes,
        *(mesh for mesh in linked.meshes if mesh.id not in selected_ids),
    )
    capabilities = linked.capabilities
    if meshes:
        capabilities = capabilities | {Capability.TESSELLATION}
    return replace(linked, meshes=meshes, capabilities=capabilities)


def _xml_string(node: ET.Element, name: str, default: str = "") -> str:
    value = node.find(f"./Properties/Property[@name='{name}']/String")
    return default if value is None else value.get("value", default)


def _xml_bool(node: ET.Element, name: str, default: bool = False) -> bool:
    value = node.find(f"./Properties/Property[@name='{name}']/Bool")
    if value is None:
        return default
    return value.get("value", "false").casefold() in {"1", "true"}


def _xml_string_list(node: ET.Element, name: str) -> list[str]:
    return [
        value.get("value", "")
        for value in node.findall(
            f"./Properties/Property[@name='{name}']/StringList/String"
        )
    ]


def _xml_link_list(node: ET.Element, name: str) -> list[str]:
    return [
        value.get("value", "")
        for value in node.findall(
            f"./Properties/Property[@name='{name}']/LinkList/Link"
        )
    ]


def _xml_number(value: str | None, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _xml_transform(node: ET.Element) -> list[float]:
    value = node.find("./Properties/Property[@name='Placement']/PropertyPlacement")
    if value is None:
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
    x = _xml_number(value.get("Q0"), 0.0)
    y = _xml_number(value.get("Q1"), 0.0)
    z = _xml_number(value.get("Q2"), 0.0)
    w = _xml_number(value.get("Q3"), 1.0)
    norm = (x * x + y * y + z * z + w * w) ** 0.5
    if norm <= 1e-15:
        x, y, z, w = 0.0, 0.0, 0.0, 1.0
    else:
        x, y, z, w = x / norm, y / norm, z / norm, w / norm
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    xw, yw, zw = x * w, y * w, z * w
    return [
        1.0 - 2.0 * (yy + zz),
        2.0 * (xy - zw),
        2.0 * (xz + yw),
        _xml_number(value.get("Px"), 0.0),
        2.0 * (xy + zw),
        1.0 - 2.0 * (xx + zz),
        2.0 * (yz - xw),
        _xml_number(value.get("Py"), 0.0),
        2.0 * (xz - yw),
        2.0 * (yz + xw),
        1.0 - 2.0 * (xx + yy),
        _xml_number(value.get("Pz"), 0.0),
        0.0,
        0.0,
        0.0,
        1.0,
    ]


def _xml_scale(node: ET.Element) -> list[float]:
    value = node.find("./Properties/Property[@name='ScaleVector']/PropertyVector")
    if value is None:
        return [1.0, 1.0, 1.0]
    return [
        _xml_number(value.get("valueX"), 1.0),
        _xml_number(value.get("valueY"), 1.0),
        _xml_number(value.get("valueZ"), 1.0),
    ]


def _external_link_details(data: bytes) -> tuple[str, list[dict[str, Any]]]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
    value = root.find(
        "./ObjectData/Object[@name='KitMetadata']/Properties/"
        "Property[@name='ExternalLinkTarget']/String"
    )
    target = "" if value is None else value.get("value", "")
    if not target:
        raise FreeCADAdapterError("component FCStd has no external link target")
    types = {
        item.get("name", ""): item.get("type", "")
        for item in root.findall("./Objects/Object")
    }
    objects = {
        item.get("name", ""): item for item in root.findall("./ObjectData/Object")
    }

    def occurrence(name: str, active: frozenset[str]) -> dict[str, Any] | None:
        node = objects.get(name)
        type_id = types.get(name, "")
        if (
            node is None
            or name in active
            or type_id not in {"App::Link", "Assembly::AssemblyLink"}
        ):
            return None
        instance_id = _xml_string(node, "InstanceId")
        if not instance_id:
            return None
        raw_instance_data = _xml_string(node, "InstanceDataJSON")
        instance_data: Any = {}
        if raw_instance_data:
            try:
                instance_data = json.loads(raw_instance_data)
            except json.JSONDecodeError:
                instance_data = {}
        children = [
            child
            for child_name in _xml_link_list(node, "Group")
            if (child := occurrence(child_name, active | {name})) is not None
        ]
        return {
            "target": name,
            "type_id": type_id,
            "label": _xml_string(node, "Label", name),
            "instance_id": instance_id,
            "definition_id": _xml_string(node, "DefinitionId"),
            "owner_definition_id": _xml_string(node, "OwnerDefinitionId"),
            "instance_path": _xml_string_list(node, "InstancePath"),
            "reference_number": _xml_string(node, "ReferenceNumber"),
            "configuration_name": _xml_string(node, "ConfigurationName"),
            "configuration_id": _xml_string(node, "ConfigurationId"),
            "suppressed": _xml_bool(node, "Suppressed"),
            "hidden": _xml_bool(node, "Hidden"),
            "fixed": _xml_bool(node, "Fixed"),
            "flexible": _xml_bool(node, "Flexible"),
            "exclude_from_bom": _xml_bool(node, "ExcludeFromBOM"),
            "visibility": _xml_bool(node, "Visibility", True),
            "rigid": _xml_bool(node, "Rigid", True),
            "transform": _xml_transform(node),
            "scale": _xml_scale(node),
            "instance_data": instance_data,
            "occurrences": children,
        }

    target_node = objects.get(target)
    occurrences = (
        [
            item
            for child_name in _xml_link_list(target_node, "Group")
            if (item := occurrence(child_name, frozenset())) is not None
        ]
        if target_node is not None
        else []
    )
    return target, occurrences


def _external_link_target(data: bytes) -> str:
    return _external_link_details(data)[0]


def _parsed_timestamp(value: str) -> float | None:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None
    return parsed.timestamp()


def _existing_timestamps(path: Path) -> tuple[float, ...]:
    values: list[float] = []
    try:
        values.append(path.stat().st_mtime)
    except OSError:
        return ()
    try:
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("Document.xml"))
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile):
        return tuple(values)
    for property_name in ("CreationDate", "LastModifiedDate"):
        element = root.find(f"./Properties/Property[@name='{property_name}']/String")
        parsed = _parsed_timestamp("" if element is None else element.get("value", ""))
        if parsed is not None:
            values.append(parsed)
    for element in root.findall(".//XLink"):
        parsed = _parsed_timestamp(element.get("stamp", ""))
        if parsed is not None:
            values.append(parsed)
    return tuple(values)


def _bundle_timestamp(destination: Path) -> tuple[str, float]:
    now = datetime.now(timezone.utc).replace(microsecond=0).timestamp()
    files = [destination]
    directory = destination.parent / destination.stem
    if directory.is_dir():
        try:
            component_files = tuple(
                path
                for path in directory.iterdir()
                if path.is_file() and path.suffix.lower() == ".fcstd"
            )
        except OSError:
            component_files = ()
        files.extend(component_files)
    existing = [timestamp for path in files for timestamp in _existing_timestamps(path)]
    epoch = int(now)
    if existing:
        epoch = max(epoch, int(max(existing)) + 1)
    modified = datetime.fromtimestamp(epoch, timezone.utc)
    return modified.strftime("%Y-%m-%dT%H:%M:%SZ"), float(epoch)


def _definition_sources(
    definition: ComponentDefinition, documents: Mapping[str, CadDocument]
) -> frozenset[tuple[str, str, str]]:
    configuration = definition.configuration_id or definition.configuration_name
    scope = f"{definition.kind.value}:{configuration}"
    values: set[tuple[str, str, str]] = set()

    def add(sha256: str, path: str) -> None:
        if sha256:
            values.add(("sha256", sha256.casefold(), scope))
        if path:
            normalized = os.path.normpath(path).replace("\\", "/").casefold()
            segments = [value for value in normalized.split("/") if value]
            values.add(("path", normalized, scope))
            values.add(("path-tail", "/".join(segments[-2:]), scope))

    add(definition.source_sha256, definition.source_path)
    if definition.name:
        values.add(("name", definition.name.casefold(), scope))
    linked = documents.get(definition.document_id)
    if linked is not None:
        add(linked.source.sha256, linked.source.path)
    return frozenset(values)


def _matching_component_link(
    definition: ComponentDefinition,
    documents: Mapping[str, CadDocument],
    root_definitions: Mapping[str, ComponentDefinition],
    root_documents: Mapping[str, CadDocument],
    links: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    sources = _definition_sources(definition, documents)
    if not sources:
        return None
    matches = [
        link
        for definition_id, link in links.items()
        if sources
        & _definition_sources(root_definitions[definition_id], root_documents)
    ]
    identities = {
        (
            str(link.get("path", "")),
            str(link.get("target", "")),
            str(link.get("stamp", "")),
        )
        for link in matches
    }
    return matches[0] if len(identities) == 1 else None


def _nested_external_links(
    component: CadDocument,
    component_path: Path,
    root_definitions: Mapping[str, ComponentDefinition],
    root_documents: Mapping[str, CadDocument],
    links: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    assembly = component.assembly
    if assembly is None:
        return {}
    documents = {
        item.id: item.document
        for item in assembly.documents
        if isinstance(item.document, CadDocument)
    }
    result: dict[str, dict[str, Any]] = {}
    for definition in assembly.definitions:
        if definition.id == assembly.root_definition_id:
            continue
        link = _matching_component_link(
            definition,
            documents,
            root_definitions,
            root_documents,
            links,
        )
        if link is None:
            continue
        path = Path(link["path"])
        result[definition.id] = {
            "file": Path(os.path.relpath(path, component_path.parent)).as_posix(),
            "stamp": str(link.get("stamp", "")),
            "target": str(link.get("target", "")),
            "occurrences": list(link.get("occurrences", [])),
        }
    return result


def _write_components(
    document: CadDocument,
    destination: Path,
    overwrite: bool,
    validate: bool,
    document_timestamp: str,
    timestamp_epoch: float,
) -> tuple[dict[str, dict[str, Any]], int]:
    assembly = document.assembly
    if assembly is None:
        return {}, 0
    paths = _component_paths(document, destination)
    if not overwrite:
        existing = next((path for path in paths.values() if path.exists()), None)
        if existing is not None:
            raise FileExistsError(existing)
    documents = {
        item.id: item.document
        for item in assembly.documents
        if isinstance(item.document, CadDocument)
    }
    definitions = {item.id: item for item in assembly.definitions}
    plans: list[tuple[str, Path, ComponentDefinition, CadDocument]] = []
    for definition_id, path in paths.items():
        definition = definitions[definition_id]
        component = _component_document(document, definition, documents)
        if component is not None:
            plans.append((definition_id, path, definition, component))
    plans.sort(key=lambda item: item[2].kind == ComponentKind.ASSEMBLY)
    component_links: dict[str, dict[str, Any]] = {}
    external_links: dict[str, dict[str, Any]] = {}
    bytes_written = 0
    for definition_id, path, definition, component in plans:
        if validate:
            component.assert_valid()
        nested_links = (
            _nested_external_links(
                component,
                path,
                definitions,
                documents,
                component_links,
            )
            if definition.kind == ComponentKind.ASSEMBLY
            else {}
        )
        data = build_fcstd_archive(
            document_to_manifest(component),
            external_links=nested_links,
            document_timestamp=document_timestamp,
        )
        target, occurrences = _external_link_details(data)
        _write_bytes(path, data, overwrite)
        os.utime(path, (timestamp_epoch, timestamp_epoch))
        component_links[definition_id] = {
            "path": path,
            "stamp": document_timestamp,
            "target": target,
            "occurrences": occurrences,
        }
        external_links[definition_id] = {
            "file": path.relative_to(destination.parent).as_posix(),
            "stamp": document_timestamp,
            "target": target,
            "occurrences": occurrences,
        }
        bytes_written += len(data)
    return external_links, bytes_written


class FreeCADAdapter:
    @property
    def info(self) -> AdapterInfo:
        return AdapterInfo(
            format_id="freecad.fcstd",
            name="FreeCAD FCStd",
            version="1.0",
            extensions=(".fcstd",),
            capabilities=frozenset(
                {
                    Capability.PARAMETRIC_HISTORY,
                    Capability.EDITABLE_SKETCHES,
                    Capability.EXPRESSIONS,
                    Capability.BREP,
                    Capability.ASSEMBLIES,
                    Capability.NATIVE_PAYLOADS,
                    Capability.ROUNDTRIP_METADATA,
                }
            ),
            media_types=("application/vnd.freecad", "application/zip"),
        )

    def probe(self, source: Source) -> ProbeResult:
        try:
            data = _source_bytes(source)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = set(archive.namelist())
                if MANIFEST_ENTRY in names and "Document.xml" in names:
                    return ProbeResult(self.info.format_id, 1.0, "Kit FCStd archive")
                if "Document.xml" in names:
                    confidence, reason = probe_native_fcstd(data)
                    return ProbeResult(self.info.format_id, confidence, reason)
        except (OSError, TypeError, zipfile.BadZipFile):
            return ProbeResult(self.info.format_id, 0.0, "not a readable FCStd archive")
        return ProbeResult(
            self.info.format_id, 0.0, "ZIP archive has no FreeCAD document"
        )

    def read(self, source: Source, options: ReadOptions | None = None) -> CadDocument:
        data = _source_bytes(source)
        try:
            value = extract_manifest_from_fcstd(data)
        except ValueError as exc:
            if str(exc) != "FCStd archive has no embedded Kit interchange document":
                raise FreeCADAdapterError(str(exc)) from exc
            try:
                document = read_native_fcstd(data, _source_path(source))
            except NativeFreeCADError as native_exc:
                raise FreeCADAdapterError(str(native_exc)) from native_exc
        else:
            try:
                document = CadDocument.from_dict(value)
            except (TypeError, ValueError) as exc:
                raise FreeCADAdapterError(
                    "embedded neutral document cannot be restored"
                ) from exc
        if options is None or options.strict:
            document.assert_valid()
        return document

    def supports(self, document: CadDocument, destination: Destination) -> bool:
        path = _destination_path(destination)
        if path is not None:
            return path.suffix.lower() == ".fcstd"
        return is_binary_destination(destination)

    def write(
        self,
        document: CadDocument,
        destination: Destination,
        options: WriteOptions | None = None,
        *,
        overwrite: bool | None = None,
    ) -> WriteResult:
        selected = options or WriteOptions()
        should_overwrite = selected.overwrite if overwrite is None else overwrite
        if selected.validate:
            document.assert_valid()
        if not self.supports(document, destination):
            raise FreeCADAdapterError(
                "FreeCAD destination must be a .FCStd path or writable binary stream"
            )
        destination_path = _destination_path(destination)
        if (
            destination_path is not None
            and destination_path.exists()
            and not should_overwrite
        ):
            raise FileExistsError(destination_path)
        external_links: dict[str, dict[str, Any]] = {}
        component_bytes_written = 0
        document_timestamp: str | None = None
        timestamp_epoch: float | None = None
        if destination_path is not None and document.assembly is not None:
            document_timestamp, timestamp_epoch = _bundle_timestamp(destination_path)
            external_links, component_bytes_written = _write_components(
                document,
                destination_path,
                should_overwrite,
                selected.validate,
                document_timestamp,
                timestamp_epoch,
            )
        manifest = document_to_manifest(document)
        data = build_fcstd_archive(
            manifest,
            external_links=external_links,
            document_timestamp=document_timestamp,
        )
        path = _write_bytes(destination, data, should_overwrite)
        if path is not None and timestamp_epoch is not None:
            os.utime(path, (timestamp_epoch, timestamp_epoch))
        metadata = {
            "schema_version": document.schema_version,
            "sketch_count": len(document.sketches),
            "timeline_count": len(document.feature_timeline),
            "native_payload_count": len(document.brep_payloads),
            "assembly_occurrence_count": (
                len(document.assembly.instances) if document.assembly is not None else 0
            ),
            "assembly_mate_count": (
                len(document.assembly.mates) if document.assembly is not None else 0
            ),
            "component_file_count": len(external_links),
            "component_bytes_written": component_bytes_written,
            "runtime": "python-stdlib",
            "recompute_required": True,
        }
        return WriteResult(
            path=path,
            adapter=self.info.format_id,
            bytes_written=len(data),
            diagnostics=document.diagnostics,
            metadata=metadata,
        )


def extract_freecad_manifest(source: Source) -> dict[str, Any]:
    return extract_manifest_from_fcstd(_source_bytes(source))


def read_freecad(source: Source, options: ReadOptions | None = None) -> CadDocument:
    return FreeCADAdapter().read(source, options)


def write_freecad(
    document: CadDocument,
    destination: Destination,
    *,
    overwrite: bool = False,
    validate: bool = True,
) -> WriteResult:
    return FreeCADAdapter().write(
        document, destination, WriteOptions(overwrite=overwrite, validate=validate)
    )

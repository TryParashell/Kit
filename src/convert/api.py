from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Mapping

from interchange import CadDocument, PayloadRole, frozen_mapping

from .adapters import (
    AdapterInfo,
    AdapterRegistry,
    Destination,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
    is_windows_device_name,
)
from .engine import ConversionEngine, ConversionResult


def _build_registry() -> AdapterRegistry:
    result = AdapterRegistry()
    result.introspect()
    return result


registry = _build_registry()
_engine = ConversionEngine(registry)


def available_adapters() -> tuple[AdapterInfo, ...]:
    by_id = {adapter.info.format_id: adapter.info for adapter in registry.readers()}
    by_id.update(
        {adapter.info.format_id: adapter.info for adapter in registry.writers()}
    )
    return tuple(by_id[key] for key in sorted(by_id))


def open_document(
    source: Source,
    *,
    source_format: str | None = None,
    configuration: str | None = None,
    include_brep: bool = True,
    include_tessellation: bool = True,
    strict: bool = True,
) -> CadDocument:
    return _engine.read(
        source,
        format_id=source_format,
        options=ReadOptions(
            configuration=configuration,
            include_brep=include_brep,
            include_tessellation=include_tessellation,
            strict=strict,
        ),
    )


def write_document(
    document: CadDocument,
    destination: Destination,
    *,
    destination_format: str | None = None,
    configuration: str | None = None,
    overwrite: bool = False,
    validate: bool = True,
    allow_carrier: bool = False,
    values: Mapping[str, Any] | None = None,
) -> WriteResult:
    selected_values = {"portable": True}
    if values is not None:
        selected_values.update(values)
    selected_values["allow_carrier"] = allow_carrier
    return _engine.write(
        document,
        destination,
        format_id=destination_format,
        options=WriteOptions(
            configuration=configuration,
            overwrite=overwrite,
            validate=validate,
            values=frozen_mapping(selected_values),
        ),
    )


def convert(
    source: Source,
    destination: Destination,
    *,
    source_format: str | None = None,
    destination_format: str | None = None,
    configuration: str | None = None,
    include_brep: bool = True,
    include_tessellation: bool = True,
    strict: bool = True,
    overwrite: bool = False,
    allow_carrier: bool = False,
    write_values: Mapping[str, Any] | None = None,
) -> ConversionResult:
    values = {"portable": True}
    if write_values is not None:
        values.update(write_values)
    values["allow_carrier"] = allow_carrier
    return _engine.convert(
        source,
        destination,
        source_format=source_format,
        destination_format=destination_format,
        read_options=ReadOptions(
            configuration=configuration,
            include_brep=include_brep,
            include_tessellation=include_tessellation,
            strict=strict,
        ),
        write_options=WriteOptions(
            configuration=configuration,
            overwrite=overwrite,
            validate=True,
            values=frozen_mapping(values),
        ),
    )


def extract_brep(
    source: Source | CadDocument,
    directory: str | Path,
    *,
    source_format: str | None = None,
    overwrite: bool = False,
) -> tuple[Path, ...]:
    document = (
        source
        if isinstance(source, CadDocument)
        else open_document(source, source_format=source_format, include_brep=True)
    )
    target = Path(directory).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    used: set[str] = set()
    payloads = tuple(
        payload
        for payload in document.brep_payloads
        if payload.role == PayloadRole.BREP and payload.data is not None
    )
    for index, payload in enumerate(payloads, start=1):
        base = re.sub(r"[^A-Za-z0-9._-]", "_", payload.id).strip("._-")
        base = base or f"payload_{index}"
        if is_windows_device_name(base):
            base = f"_{base}"
        name = base
        suffix = 2
        while name.lower() in used:
            name = f"{base}_{suffix}"
            suffix += 1
        used.add(name.lower())
        output = target / f"{name}{payload.file_extension}"
        if output.exists() and not overwrite:
            raise FileExistsError(output)
        output.write_bytes(payload.data)
        outputs.append(output)
    return tuple(outputs)

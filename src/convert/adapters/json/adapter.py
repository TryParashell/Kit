# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace
from io import TextIOBase
from pathlib import Path

from convert.adapters.base import (
    AdapterInfo,
    Destination,
    ProbeResult,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
)
from interchange import CadDocument, Capability, filter_document

_SUFFIX = ".json"
_INFO = AdapterInfo(
    format_id="interchange.json",
    name="Kit interchange JSON",
    version="1.0",
    extensions=(_SUFFIX,),
    capabilities=frozenset(Capability),
    native_capabilities=frozenset(Capability),
    media_types=("application/vnd.parashell.kit+json",),
    part_extensions=(_SUFFIX,),
    assembly_extensions=(_SUFFIX,),
)


class JsonAdapter:
    @property
    def info(self) -> AdapterInfo:
        return _INFO

    def probe(self, source: Source) -> ProbeResult:
        suffix = ""
        if isinstance(source, (str, Path)):
            suffix = Path(source).suffix.lower()
        try:
            prefix = _read_prefix(source, 4096)
        except OSError as exc:
            return ProbeResult(_INFO.format_id, 0.0, str(exc))
        if b'"$type"' in prefix and b'"CadDocument"' in prefix:
            return ProbeResult(_INFO.format_id, 1.0, "CadDocument type marker")
        if suffix in _INFO.extensions:
            return ProbeResult(_INFO.format_id, 0.5, "JSON extension")
        return ProbeResult(_INFO.format_id, 0.0, "no interchange document marker")

    def read(self, source: Source, options: ReadOptions | None = None) -> CadDocument:
        settings = options or ReadOptions()
        document = CadDocument.from_json(_read_text(source))
        if settings.configuration is not None:
            matches = {
                configuration.id
                for configuration in document.configurations
                if settings.configuration in {configuration.id, configuration.name}
            }
            if not matches:
                raise ValueError(
                    f"configuration {settings.configuration!r} is unavailable"
                )
            document = replace(
                document,
                configurations=tuple(
                    replace(configuration, active=configuration.id in matches)
                    for configuration in document.configurations
                ),
            )
        document = filter_document(
            document,
            include_brep=settings.include_brep,
            include_tessellation=settings.include_tessellation,
            keep_payload_records=False,
        )
        if settings.strict:
            document.assert_valid()
        return document

    def supports(self, document: CadDocument, destination: Destination) -> bool:
        if isinstance(destination, (str, Path)):
            return Path(destination).suffix.lower() in _INFO.extensions
        return callable(getattr(destination, "write", None))

    def write(
        self,
        document: CadDocument,
        destination: Destination,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        effective = options or WriteOptions()
        if effective.validate:
            document.assert_valid()
        payload = (document.to_json() + "\n").encode("utf-8")
        if isinstance(destination, (str, Path)):
            output = Path(destination).expanduser().resolve()
            if output.exists() and not effective.overwrite:
                raise FileExistsError(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(payload)
            return WriteResult(
                output,
                self.info.format_id,
                len(payload),
                application_usable=True,
                vendor_loadable=True,
            )
        text = payload.decode("utf-8")
        _write_stream(destination, text, payload)
        return WriteResult(
            None,
            self.info.format_id,
            len(payload),
            application_usable=True,
            vendor_loadable=True,
        )


def _write_stream(destination: Destination, text: str, payload: bytes) -> None:
    writer = getattr(destination, "write", None)
    if not callable(writer):
        raise TypeError("JSON destination must be a path or writable stream")
    if isinstance(destination, TextIOBase):
        written = writer(text)
        expected = len(text)
    else:
        try:
            written = writer(payload)
            expected = len(payload)
        except TypeError:
            written = writer(text)
            expected = len(text)
    if written is not None and written != expected:
        raise OSError(f"short JSON write: expected {expected}, wrote {written}")


def _read_prefix(source: Source, limit: int) -> bytes:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source[:limit])
    if isinstance(source, (str, Path)):
        with Path(source).expanduser().open("rb") as handle:
            return handle.read(limit)
    position = source.tell() if hasattr(source, "tell") else None
    value = source.read(limit)
    if position is not None and hasattr(source, "seek"):
        source.seek(position)
    return value.encode("utf-8") if isinstance(value, str) else bytes(value)


def _read_text(source: Source) -> str:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source).decode("utf-8")
    if isinstance(source, (str, Path)):
        return Path(source).expanduser().read_text("utf-8")
    value = source.read()
    return value.decode("utf-8") if isinstance(value, bytes) else value

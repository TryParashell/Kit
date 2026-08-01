from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, TextIO

from convert.adapters.base import (
    AdapterInfo,
    Destination,
    ProbeResult,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
)
from interchange import CadDocument, Capability


class JsonAdapter:
    @property
    def info(self) -> AdapterInfo:
        return AdapterInfo(
            format_id="interchange.json",
            name="Kit interchange JSON",
            version="1.0",
            extensions=(".json",),
            capabilities=frozenset(Capability),
            media_types=("application/vnd.parashell.kit+json",),
        )

    def probe(self, source: Source) -> ProbeResult:
        suffix = ""
        if isinstance(source, (str, Path)):
            suffix = Path(source).suffix.lower()
        try:
            prefix = _read_prefix(source, 4096)
        except OSError as exc:
            return ProbeResult("interchange.json", 0.0, str(exc))
        if b'"$type"' in prefix and b'"CadDocument"' in prefix:
            return ProbeResult("interchange.json", 1.0, "CadDocument type marker")
        if suffix == ".json":
            return ProbeResult("interchange.json", 0.5, "JSON extension")
        return ProbeResult("interchange.json", 0.0, "no interchange document marker")

    def read(self, source: Source, options: ReadOptions | None = None) -> CadDocument:
        document = CadDocument.from_json(_read_text(source))
        if options is None or options.strict:
            document.assert_valid()
        return document

    def supports(self, document: CadDocument, destination: Destination) -> bool:
        if isinstance(destination, (str, Path)):
            return Path(destination).suffix.lower() == ".json"
        return hasattr(destination, "write")

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
            return WriteResult(output, self.info.format_id, len(payload))
        written = destination.write(payload)
        if written is None:
            written = len(payload)
        return WriteResult(None, self.info.format_id, int(written))


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

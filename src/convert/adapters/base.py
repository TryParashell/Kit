from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Mapping, Protocol, TextIO, runtime_checkable

from interchange import CadDocument, Capability, Diagnostic, frozen_mapping


Source = str | Path | bytes | bytearray | BinaryIO
Destination = str | Path | BinaryIO | TextIO


@dataclass(frozen=True, slots=True)
class AdapterInfo:
    format_id: str
    name: str
    version: str
    extensions: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    capabilities: frozenset[Capability] = frozenset()
    media_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProbeResult:
    format_id: str
    confidence: float
    reason: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("probe confidence must be between zero and one")


@dataclass(frozen=True, slots=True)
class ReadOptions:
    configuration: str | None = None
    include_brep: bool = True
    include_tessellation: bool = False
    strict: bool = True
    values: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class WriteOptions:
    configuration: str | None = None
    overwrite: bool = False
    validate: bool = True
    values: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class WriteResult:
    path: Path | None
    adapter: str
    bytes_written: int
    diagnostics: tuple[Diagnostic, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=frozen_mapping)


@runtime_checkable
class CadReaderAdapter(Protocol):
    @property
    def info(self) -> AdapterInfo: ...

    def probe(self, source: Source) -> ProbeResult: ...

    def read(
        self, source: Source, options: ReadOptions | None = None
    ) -> CadDocument: ...


@runtime_checkable
class CadWriterAdapter(Protocol):
    @property
    def info(self) -> AdapterInfo: ...

    def supports(self, document: CadDocument, destination: Destination) -> bool: ...

    def write(
        self,
        document: CadDocument,
        destination: Destination,
        options: WriteOptions | None = None,
    ) -> WriteResult: ...


@runtime_checkable
class CadAdapter(CadReaderAdapter, CadWriterAdapter, Protocol):
    __slots__ = ()

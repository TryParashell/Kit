from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from io import TextIOBase
from pathlib import Path
from typing import Any, BinaryIO, Mapping, Protocol, TextIO, runtime_checkable

from interchange import CadDocument, Capability, Diagnostic, frozen_mapping


Source = str | Path | bytes | bytearray | BinaryIO | TextIO
Destination = str | Path | BinaryIO | TextIO


class TransferMode(StrEnum):
    NATIVE = "native"
    MIXED = "mixed"
    CARRIER = "carrier"


class CarrierReason(StrEnum):
    TARGET_UNSUPPORTED = "target_unsupported"
    WRITER_UNIMPLEMENTED = "writer_unimplemented"
    SOURCE_OPAQUE = "source_opaque"


@dataclass(frozen=True, slots=True)
class CapabilityTransfer:
    capability: Capability
    mode: TransferMode
    carrier_reason: CarrierReason | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.capability, Capability):
            raise TypeError("transfer capability must be a Capability")
        if not isinstance(self.mode, TransferMode):
            raise TypeError("transfer mode must be a TransferMode")
        if self.mode is TransferMode.NATIVE:
            if self.carrier_reason is not None:
                raise ValueError("native transfers cannot have a carrier reason")
            return
        if self.carrier_reason is None:
            object.__setattr__(
                self,
                "carrier_reason",
                CarrierReason.WRITER_UNIMPLEMENTED,
            )
        elif not isinstance(self.carrier_reason, CarrierReason):
            raise TypeError("carrier reason must be a CarrierReason")


def is_windows_device_name(value: str) -> bool:
    stem = value.split(".", 1)[0].casefold()
    return stem in {"con", "prn", "aux", "nul"} or (
        len(stem) == 4 and stem[:3] in {"com", "lpt"} and stem[3] in "123456789¹²³"
    )


def is_binary_destination(destination: Destination) -> bool:
    if isinstance(destination, (str, Path, TextIOBase)):
        return False
    writer = getattr(destination, "write", None)
    return callable(writer) and getattr(destination, "encoding", None) is None


@dataclass(frozen=True, slots=True)
class AdapterInfo:
    format_id: str
    name: str
    version: str
    extensions: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    capabilities: frozenset[Capability] = frozenset()
    media_types: tuple[str, ...] = ()
    native_capabilities: frozenset[Capability] = frozenset()
    part_extensions: tuple[str, ...] = ()
    assembly_extensions: tuple[str, ...] = ()

    def extensions_for(self, *, assembly: bool) -> tuple[str, ...]:
        if not isinstance(assembly, bool):
            raise TypeError("assembly must be a boolean")
        return self.assembly_extensions if assembly else self.part_extensions


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
    include_tessellation: bool = True
    strict: bool = True
    values: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class WriteOptions:
    configuration: str | None = None
    overwrite: bool = False
    validate: bool = True
    destination_format: str | None = None
    values: Mapping[str, Any] = field(default_factory=frozen_mapping)


@dataclass(frozen=True, slots=True)
class WriteResult:
    path: Path | None
    adapter: str
    bytes_written: int
    diagnostics: tuple[Diagnostic, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=frozen_mapping)
    transfers: tuple[CapabilityTransfer, ...] = ()
    dropped: frozenset[Capability] = frozenset()
    requirements: tuple[str, ...] = ()
    application_usable: bool = False
    vendor_loadable: bool = False

    def __post_init__(self) -> None:
        if self.bytes_written < 0:
            raise ValueError("bytes written cannot be negative")
        if not isinstance(self.transfers, tuple) or any(
            not isinstance(transfer, CapabilityTransfer) for transfer in self.transfers
        ):
            raise TypeError("transfers must be CapabilityTransfer values")
        capabilities = tuple(transfer.capability for transfer in self.transfers)
        if len(capabilities) != len(set(capabilities)):
            raise ValueError("transfer capabilities must be unique")
        if not isinstance(self.dropped, frozenset) or any(
            not isinstance(capability, Capability) for capability in self.dropped
        ):
            raise TypeError("dropped capabilities must be Capability values")
        if set(capabilities) & self.dropped:
            raise ValueError("transferred capabilities cannot also be dropped")
        if not isinstance(self.requirements, tuple) or any(
            not isinstance(requirement, str)
            or not requirement.strip()
            or requirement != requirement.strip()
            for requirement in self.requirements
        ):
            raise TypeError("requirements must be non-empty strings")
        if len(set(self.requirements)) != len(self.requirements):
            raise ValueError("requirements must be unique")
        if not isinstance(self.application_usable, bool):
            raise TypeError("application usable must be a boolean")
        if not isinstance(self.vendor_loadable, bool):
            raise TypeError("vendor loadable must be a boolean")
        if self.application_usable and not self.vendor_loadable:
            raise ValueError("application-usable output must be vendor-loadable")
        for key, expected in (
            ("application_usable", self.application_usable),
            ("vendor_loadable", self.vendor_loadable),
        ):
            if key not in self.metadata:
                continue
            value = self.metadata[key]
            if not isinstance(value, bool):
                raise TypeError(f"metadata {key} must be a boolean")
            if value is not expected:
                raise ValueError(f"metadata {key} contradicts the write result")

    @property
    def native_capabilities(self) -> frozenset[Capability]:
        return frozenset(
            transfer.capability
            for transfer in self.transfers
            if transfer.mode in {TransferMode.NATIVE, TransferMode.MIXED}
        )

    @property
    def carrier_capabilities(self) -> frozenset[Capability]:
        return frozenset(
            transfer.capability
            for transfer in self.transfers
            if transfer.mode in {TransferMode.CARRIER, TransferMode.MIXED}
        )

    @property
    def transferred_capabilities(self) -> frozenset[Capability]:
        return frozenset(transfer.capability for transfer in self.transfers)

    @property
    def roundtrip_safe(self) -> bool:
        return not self.dropped

    @property
    def near_lossless(self) -> bool:
        return (
            self.application_usable
            and self.vendor_loadable
            and not self.requirements
            and not self.dropped
            and all(
                transfer.carrier_reason is CarrierReason.TARGET_UNSUPPORTED
                for transfer in self.transfers
                if transfer.mode in {TransferMode.CARRIER, TransferMode.MIXED}
            )
        )


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

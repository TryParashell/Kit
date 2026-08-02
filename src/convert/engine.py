from __future__ import annotations

from dataclasses import dataclass

from .adapters import (
    AdapterRegistry,
    CapabilityTransfer,
    Destination,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
)
from interchange import CadDocument, Capability


@dataclass(frozen=True, slots=True)
class ConversionResult:
    document: CadDocument
    output: WriteResult
    source_format: str
    destination_format: str

    @property
    def transfers(self) -> tuple[CapabilityTransfer, ...]:
        return self.output.transfers

    @property
    def dropped(self) -> frozenset[Capability]:
        return self.output.dropped

    @property
    def requirements(self) -> tuple[str, ...]:
        return self.output.requirements

    @property
    def application_usable(self) -> bool:
        return self.output.application_usable

    @property
    def vendor_loadable(self) -> bool:
        return self.output.vendor_loadable

    @property
    def roundtrip_safe(self) -> bool:
        return self.output.roundtrip_safe

    @property
    def near_lossless(self) -> bool:
        return self.output.near_lossless


class ConversionEngine:
    def __init__(self, registry: AdapterRegistry):
        self.registry = registry

    def read(
        self,
        source: Source,
        *,
        format_id: str | None = None,
        options: ReadOptions | None = None,
    ) -> CadDocument:
        return self.registry.read(
            source, format_id=format_id, options=options or ReadOptions()
        )

    def write(
        self,
        document: CadDocument,
        destination: Destination,
        *,
        format_id: str | None = None,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        return self.registry.write(
            document,
            destination,
            format_id=format_id,
            options=options or WriteOptions(),
        )

    def convert(
        self,
        source: Source,
        destination: Destination,
        *,
        source_format: str | None = None,
        destination_format: str | None = None,
        read_options: ReadOptions | None = None,
        write_options: WriteOptions | None = None,
    ) -> ConversionResult:
        document, reader = self.registry.read_with_adapter(
            source,
            format_id=source_format,
            options=read_options or ReadOptions(),
        )
        output = self.registry.write(
            document,
            destination,
            format_id=destination_format,
            options=write_options or WriteOptions(),
        )
        source_ids = {
            value.casefold() for value in (reader.info.format_id, *reader.info.aliases)
        }
        return ConversionResult(
            document=document,
            output=output,
            source_format=(
                document.source.format_id
                if document.source.format_id.casefold() in source_ids
                else reader.info.format_id
            ),
            destination_format=output.adapter,
        )

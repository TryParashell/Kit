from __future__ import annotations

from dataclasses import dataclass, replace

from .adapters import (
    AdapterRegistry,
    Destination,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
)
from interchange import CadDocument


@dataclass(frozen=True, slots=True)
class ConversionResult:
    document: CadDocument
    output: WriteResult
    source_format: str
    destination_format: str


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
        reader = (
            self.registry.reader(source_format)
            if source_format
            else self.registry.select_reader(source)
        )
        document = reader.read(source, read_options or ReadOptions())
        document.assert_valid()
        writer = (
            self.registry.writer(destination_format)
            if destination_format
            else self.registry.select_writer(document, destination)
        )
        selected_options = write_options or WriteOptions()
        if destination_format is not None:
            selected_options = replace(
                selected_options,
                destination_format=destination_format,
            )
        output = writer.write(document, destination, selected_options)
        source_ids = {reader.info.format_id, *reader.info.aliases}
        return ConversionResult(
            document=document,
            output=output,
            source_format=(
                document.source.format_id
                if document.source.format_id in source_ids
                else reader.info.format_id
            ),
            destination_format=output.adapter,
        )

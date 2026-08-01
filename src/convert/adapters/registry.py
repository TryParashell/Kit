from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
from typing import Iterable

from interchange import CadDocument

from .base import (
    CadReaderAdapter,
    CadWriterAdapter,
    Destination,
    ProbeResult,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
)


class AdapterRegistryError(RuntimeError):
    __slots__ = ()


class AdapterNotFoundError(AdapterRegistryError):
    __slots__ = ()


class AmbiguousAdapterError(AdapterRegistryError):
    __slots__ = ()


@dataclass(slots=True)
class AdapterBinding:
    reader: CadReaderAdapter | None = None
    writer: CadWriterAdapter | None = None


class AdapterRegistry:
    def __init__(self) -> None:
        self._bindings: dict[str, AdapterBinding] = {}
        self._aliases: dict[str, str] = {}

    def _register_aliases(self, adapter: object, replace: bool) -> None:
        info = adapter.info
        for alias in info.aliases:
            if not alias or alias == info.format_id:
                raise AdapterRegistryError(
                    "adapter alias must be distinct and non-empty"
                )
            existing = self._aliases.get(alias)
            if alias in self._bindings or (
                existing is not None and existing != info.format_id
            ):
                if not replace:
                    raise AdapterRegistryError(
                        f"adapter alias already registered: {alias}"
                    )
            self._aliases[alias] = info.format_id

    def register_reader(
        self, adapter: CadReaderAdapter, *, replace: bool = False
    ) -> None:
        self._register_aliases(adapter, replace)
        binding = self._bindings.setdefault(adapter.info.format_id, AdapterBinding())
        if binding.reader is not None and not replace:
            raise AdapterRegistryError(
                f"reader already registered for {adapter.info.format_id}"
            )
        binding.reader = adapter

    def register_writer(
        self, adapter: CadWriterAdapter, *, replace: bool = False
    ) -> None:
        self._register_aliases(adapter, replace)
        binding = self._bindings.setdefault(adapter.info.format_id, AdapterBinding())
        if binding.writer is not None and not replace:
            raise AdapterRegistryError(
                f"writer already registered for {adapter.info.format_id}"
            )
        binding.writer = adapter

    def register(self, adapter: object, *, replace: bool = False) -> None:
        registered = False
        if isinstance(adapter, CadReaderAdapter):
            self.register_reader(adapter, replace=replace)
            registered = True
        if isinstance(adapter, CadWriterAdapter):
            self.register_writer(adapter, replace=replace)
            registered = True
        if not registered:
            raise TypeError("adapter implements neither reader nor writer protocol")

    def discover(self, group: str = "kit.adapters") -> tuple[str, ...]:
        loaded: list[str] = []
        for entry_point in entry_points(group=group):
            factory = entry_point.load()
            adapter = factory() if isinstance(factory, type) else factory
            self.register(adapter)
            loaded.append(entry_point.name)
        return tuple(loaded)

    def readers(self) -> tuple[CadReaderAdapter, ...]:
        return tuple(
            binding.reader
            for binding in self._bindings.values()
            if binding.reader is not None
        )

    def writers(self) -> tuple[CadWriterAdapter, ...]:
        return tuple(
            binding.writer
            for binding in self._bindings.values()
            if binding.writer is not None
        )

    def reader(self, format_id: str) -> CadReaderAdapter:
        binding = self._bindings.get(self._aliases.get(format_id, format_id))
        if binding is None or binding.reader is None:
            raise AdapterNotFoundError(f"no reader registered for {format_id}")
        return binding.reader

    def writer(self, format_id: str) -> CadWriterAdapter:
        binding = self._bindings.get(self._aliases.get(format_id, format_id))
        if binding is None or binding.writer is None:
            raise AdapterNotFoundError(f"no writer registered for {format_id}")
        return binding.writer

    def select_reader(self, source: Source) -> CadReaderAdapter:
        results: list[tuple[ProbeResult, CadReaderAdapter]] = []
        for adapter in self.readers():
            result = adapter.probe(source)
            if result.confidence > 0:
                results.append((result, adapter))
        if not results:
            raise AdapterNotFoundError("no reader recognizes the source")
        results.sort(key=lambda item: item[0].confidence, reverse=True)
        if len(results) > 1 and results[0][0].confidence == results[1][0].confidence:
            raise AmbiguousAdapterError(
                f"reader probe tied between {results[0][1].info.format_id} and "
                f"{results[1][1].info.format_id}"
            )
        return results[0][1]

    def select_writer(
        self, document: CadDocument, destination: Destination
    ) -> CadWriterAdapter:
        candidates = [
            adapter
            for adapter in self.writers()
            if adapter.supports(document, destination)
        ]
        if not candidates:
            raise AdapterNotFoundError("no writer supports the destination")
        if len(candidates) > 1:
            extension = (
                Path(destination).suffix.lower()
                if isinstance(destination, (str, Path))
                else ""
            )
            exact = [
                adapter
                for adapter in candidates
                if extension in {item.lower() for item in adapter.info.extensions}
            ]
            if len(exact) == 1:
                return exact[0]
            raise AmbiguousAdapterError("multiple writers support the destination")
        return candidates[0]

    def read(
        self,
        source: Source,
        *,
        format_id: str | None = None,
        options: ReadOptions | None = None,
    ) -> CadDocument:
        adapter = self.reader(format_id) if format_id else self.select_reader(source)
        document = adapter.read(source, options)
        document.assert_valid()
        return document

    def write(
        self,
        document: CadDocument,
        destination: Destination,
        *,
        format_id: str | None = None,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        adapter = (
            self.writer(format_id)
            if format_id
            else self.select_writer(document, destination)
        )
        if options is None or options.validate:
            document.assert_valid()
        return adapter.write(document, destination, options)

    def format_ids(self) -> tuple[str, ...]:
        return tuple(sorted((*self._bindings, *self._aliases)))

    def extend(self, adapters: Iterable[object], *, replace: bool = False) -> None:
        for adapter in adapters:
            self.register(adapter, replace=replace)

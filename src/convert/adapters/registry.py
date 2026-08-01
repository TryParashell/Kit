from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from inspect import isabstract, isclass
from pathlib import Path
from pkgutil import iter_modules
from types import ModuleType
from typing import Iterable

from interchange import CadDocument

from .base import (
    AdapterInfo,
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


class AdapterDiscoveryError(AdapterRegistryError):
    __slots__ = ()


class AmbiguousAdapterError(AdapterRegistryError):
    __slots__ = ()


@dataclass(slots=True)
class AdapterBinding:
    reader: CadReaderAdapter | None = None
    writer: CadWriterAdapter | None = None


def _adapter_type(value: object, package_name: str) -> type[object] | None:
    if (
        not isclass(value)
        or isabstract(value)
        or getattr(value, "_is_protocol", False)
        or not (
            value.__module__ == package_name
            or value.__module__.startswith(package_name + ".")
        )
        or not hasattr(value, "info")
    ):
        return None
    reader = all(callable(getattr(value, name, None)) for name in ("probe", "read"))
    writer = all(callable(getattr(value, name, None)) for name in ("supports", "write"))
    return value if reader or writer else None


def _public_adapter_types(module: ModuleType) -> tuple[type[object], ...]:
    exports = getattr(module, "__all__", ())
    if not isinstance(exports, (tuple, list)) or not all(
        isinstance(name, str) for name in exports
    ):
        raise AdapterDiscoveryError(f"invalid public exports in {module.__name__}")
    adapter_types: set[type[object]] = set()
    for name in sorted(set(exports)):
        if not hasattr(module, name):
            raise AdapterDiscoveryError(
                f"missing public export {module.__name__}.{name}"
            )
        adapter_type = _adapter_type(getattr(module, name), module.__name__)
        if adapter_type is not None:
            adapter_types.add(adapter_type)
    return tuple(
        sorted(adapter_types, key=lambda value: (value.__module__, value.__qualname__))
    )


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

    def introspect(self, package_name: str = __package__) -> tuple[str, ...]:
        try:
            package = import_module(package_name)
        except Exception as exc:
            raise AdapterDiscoveryError(
                f"could not import adapter package {package_name}"
            ) from exc
        paths = getattr(package, "__path__", None)
        if paths is None:
            raise AdapterDiscoveryError(f"adapter package has no path: {package_name}")
        try:
            packages = tuple(
                sorted(
                    item.name
                    for item in iter_modules(paths, package.__name__ + ".")
                    if item.ispkg and not item.name.rsplit(".", 1)[-1].startswith("_")
                )
            )
        except Exception as exc:
            raise AdapterDiscoveryError(
                f"could not enumerate adapter package {package_name}"
            ) from exc
        if not packages:
            raise AdapterDiscoveryError(f"adapter package is empty: {package_name}")
        instances: list[object] = []
        seen_types: set[type[object]] = set()
        for discovered_name in packages:
            try:
                module = import_module(discovered_name)
            except Exception as exc:
                raise AdapterDiscoveryError(
                    f"could not import format package {discovered_name}"
                ) from exc
            adapter_types = _public_adapter_types(module)
            if not adapter_types:
                raise AdapterDiscoveryError(
                    f"format package exports no adapter: {discovered_name}"
                )
            for adapter_type in adapter_types:
                if adapter_type in seen_types:
                    continue
                seen_types.add(adapter_type)
                try:
                    adapter = adapter_type()
                    info = adapter.info
                except Exception as exc:
                    raise AdapterDiscoveryError(
                        f"could not construct adapter {adapter_type.__module__}."
                        f"{adapter_type.__qualname__}"
                    ) from exc
                reader = isinstance(adapter, CadReaderAdapter) and all(
                    callable(getattr(adapter, name, None)) for name in ("probe", "read")
                )
                writer = isinstance(adapter, CadWriterAdapter) and all(
                    callable(getattr(adapter, name, None))
                    for name in ("supports", "write")
                )
                if not reader and not writer:
                    raise AdapterDiscoveryError(
                        f"invalid adapter {adapter_type.__module__}."
                        f"{adapter_type.__qualname__}"
                    )
                if not isinstance(info, AdapterInfo) or not info.format_id:
                    raise AdapterDiscoveryError(
                        f"invalid adapter metadata {adapter_type.__module__}."
                        f"{adapter_type.__qualname__}"
                    )
                instances.append(adapter)
        bindings = {
            name: AdapterBinding(binding.reader, binding.writer)
            for name, binding in self._bindings.items()
        }
        aliases = dict(self._aliases)
        try:
            self.extend(instances)
        except Exception as exc:
            self._bindings = bindings
            self._aliases = aliases
            raise AdapterDiscoveryError(
                f"could not register adapters from {package_name}"
            ) from exc
        return tuple(dict.fromkeys(adapter.info.format_id for adapter in instances))

    def readers(self) -> tuple[CadReaderAdapter, ...]:
        return tuple(
            binding.reader
            for _, binding in sorted(self._bindings.items())
            if binding.reader is not None
        )

    def writers(self) -> tuple[CadWriterAdapter, ...]:
        return tuple(
            binding.writer
            for _, binding in sorted(self._bindings.items())
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

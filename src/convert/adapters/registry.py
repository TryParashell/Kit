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


def _validated_info(adapter: object) -> AdapterInfo:
    info = adapter.info
    if not isinstance(info, AdapterInfo):
        raise AdapterRegistryError("adapter info must be AdapterInfo")
    for field_name in ("format_id", "name", "version"):
        value = getattr(info, field_name)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise AdapterRegistryError(
                f"adapter {field_name} must be a non-empty string"
            )
    for field_name in ("extensions", "aliases", "media_types"):
        values = getattr(info, field_name)
        if not isinstance(values, tuple) or any(
            not isinstance(value, str) or not value for value in values
        ):
            raise AdapterRegistryError(f"adapter {field_name} must be a string tuple")
    if len(set(info.aliases)) != len(info.aliases):
        raise AdapterRegistryError("adapter aliases must be unique")
    if info.format_id in info.aliases:
        raise AdapterRegistryError("adapter alias must differ from its format id")
    return info


class AdapterRegistry:
    def __init__(self) -> None:
        self._bindings: dict[str, AdapterBinding] = {}
        self._aliases: dict[str, str] = {}

    def _validate_namespace(self, info: AdapterInfo) -> None:
        owner = self._aliases.get(info.format_id)
        if owner is not None:
            raise AdapterRegistryError(
                f"format id is already an alias for {owner}: {info.format_id}"
            )
        for alias in info.aliases:
            if alias in self._bindings:
                raise AdapterRegistryError(
                    f"adapter alias is already a format id: {alias}"
                )
            existing = self._aliases.get(alias)
            if existing is not None and existing != info.format_id:
                raise AdapterRegistryError(f"adapter alias already registered: {alias}")

    def _register_aliases(self, info: AdapterInfo) -> None:
        for alias in info.aliases:
            self._aliases[alias] = info.format_id

    def _state(
        self,
    ) -> tuple[dict[str, AdapterBinding], dict[str, str]]:
        return (
            {
                name: AdapterBinding(binding.reader, binding.writer)
                for name, binding in self._bindings.items()
            },
            dict(self._aliases),
        )

    def _restore(self, state: tuple[dict[str, AdapterBinding], dict[str, str]]) -> None:
        self._bindings, self._aliases = state

    def register_reader(
        self, adapter: CadReaderAdapter, *, replace: bool = False
    ) -> None:
        info = _validated_info(adapter)
        self._validate_namespace(info)
        binding = self._bindings.get(info.format_id)
        if binding is None:
            binding = AdapterBinding()
        if binding.reader is not None and not replace:
            if type(binding.reader) is type(adapter) and binding.reader.info == info:
                return
            raise AdapterRegistryError(
                f"reader already registered for {info.format_id}"
            )
        self._register_aliases(info)
        self._bindings.setdefault(info.format_id, binding)
        binding.reader = adapter

    def register_writer(
        self, adapter: CadWriterAdapter, *, replace: bool = False
    ) -> None:
        info = _validated_info(adapter)
        self._validate_namespace(info)
        binding = self._bindings.get(info.format_id)
        if binding is None:
            binding = AdapterBinding()
        if binding.writer is not None and not replace:
            if type(binding.writer) is type(adapter) and binding.writer.info == info:
                return
            raise AdapterRegistryError(
                f"writer already registered for {info.format_id}"
            )
        self._register_aliases(info)
        self._bindings.setdefault(info.format_id, binding)
        binding.writer = adapter

    def register(self, adapter: object, *, replace: bool = False) -> None:
        state = self._state()
        registered = False
        try:
            if isinstance(adapter, CadReaderAdapter):
                self.register_reader(adapter, replace=replace)
                registered = True
            if isinstance(adapter, CadWriterAdapter):
                self.register_writer(adapter, replace=replace)
                registered = True
            if not registered:
                raise TypeError("adapter implements neither reader nor writer protocol")
        except Exception:
            self._restore(state)
            raise

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
        try:
            self.extend(instances)
        except Exception as exc:
            raise AdapterDiscoveryError(
                f"could not register adapters from {package_name}"
            ) from exc
        return tuple(sorted({adapter.info.format_id for adapter in instances}))

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
        return tuple(sorted(set(self._bindings) | set(self._aliases)))

    def extend(self, adapters: Iterable[object], *, replace: bool = False) -> None:
        state = self._state()
        try:
            for adapter in adapters:
                self.register(adapter, replace=replace)
        except Exception:
            self._restore(state)
            raise

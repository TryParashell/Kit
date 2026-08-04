# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from importlib import import_module
from inspect import isabstract, isclass
from io import BytesIO, StringIO
import os
from pathlib import Path
from pkgutil import iter_modules, walk_packages
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Iterable, get_args, get_origin, get_type_hints

from interchange import CadDocument, Capability, frozen_mapping, infer_capabilities

from .base import (
    AdapterInfo,
    CarrierReason,
    CadReaderAdapter,
    CadWriterAdapter,
    CapabilityTransfer,
    Destination,
    ProbeResult,
    ReadOptions,
    Source,
    TransferMode,
    WriteOptions,
    WriteResult,
    is_binary_destination,
)


class AdapterRegistryError(RuntimeError):
    __slots__ = ()


class AdapterNotFoundError(AdapterRegistryError):
    __slots__ = ()


class AdapterDiscoveryError(AdapterRegistryError):
    __slots__ = ()


class CapabilityLossError(AdapterRegistryError):
    __slots__ = ("format_id", "dropped")

    def __init__(self, format_id: str, dropped: frozenset[Capability]) -> None:
        self.format_id = format_id
        self.dropped = dropped
        names = ", ".join(sorted(capability.value for capability in dropped))
        super().__init__(f"{format_id} cannot preserve capabilities: {names}")


class ApplicationUsabilityError(AdapterRegistryError):
    __slots__ = (
        "application_usable",
        "carrier_capabilities",
        "carrier_reasons",
        "code",
        "dropped",
        "format_id",
        "issues",
        "requirements",
        "source_opaque_capabilities",
        "unimplemented_capabilities",
        "vendor_loadable",
    )

    def __init__(self, format_id: str, result: WriteResult) -> None:
        issues: list[str] = []
        if not result.application_usable:
            issues.append("application_unusable")
        if not result.vendor_loadable:
            issues.append("vendor_unloadable")
        if result.requirements:
            issues.append("external_requirements")
        if result.dropped:
            issues.append("capability_loss")
        if result.transfers and not result.native_capabilities:
            issues.append("carrier_only")
        unimplemented_capabilities = frozenset(
            transfer.capability
            for transfer in result.transfers
            if transfer.carrier_reason is CarrierReason.WRITER_UNIMPLEMENTED
        )
        source_opaque_capabilities = frozenset(
            transfer.capability
            for transfer in result.transfers
            if transfer.carrier_reason is CarrierReason.SOURCE_OPAQUE
        )
        if unimplemented_capabilities:
            issues.append("unimplemented_translation")
        if source_opaque_capabilities:
            issues.append("opaque_source_data")
        self.code = "output_not_application_usable"
        self.format_id = format_id
        self.issues = tuple(issues)
        self.application_usable = result.application_usable
        self.vendor_loadable = result.vendor_loadable
        self.requirements = result.requirements
        self.dropped = result.dropped
        self.carrier_capabilities = result.carrier_capabilities
        self.carrier_reasons = frozen_mapping(
            {
                transfer.capability: transfer.carrier_reason
                for transfer in result.transfers
                if transfer.carrier_reason is not None
            }
        )
        self.unimplemented_capabilities = unimplemented_capabilities
        self.source_opaque_capabilities = source_opaque_capabilities
        detail = ", ".join(self.issues) or "unverified_output"
        super().__init__(f"{format_id} output failed application usability: {detail}")

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "format_id": self.format_id,
            "issues": self.issues,
            "application_usable": self.application_usable,
            "vendor_loadable": self.vendor_loadable,
            "requirements": self.requirements,
            "dropped": tuple(sorted(capability.value for capability in self.dropped)),
            "carrier_capabilities": tuple(
                sorted(capability.value for capability in self.carrier_capabilities)
            ),
            "carrier_reasons": {
                capability.value: reason.value
                for capability, reason in sorted(
                    self.carrier_reasons.items(),
                    key=lambda item: item[0].value,
                )
            },
            "unimplemented_capabilities": tuple(
                sorted(
                    capability.value for capability in self.unimplemented_capabilities
                )
            ),
            "source_opaque_capabilities": tuple(
                sorted(
                    capability.value for capability in self.source_opaque_capabilities
                )
            ),
        }


class AmbiguousAdapterError(AdapterRegistryError):
    __slots__ = ()


@dataclass(slots=True)
class AdapterBinding:
    reader: CadReaderAdapter | None = None
    writer: CadWriterAdapter | None = None


def _replayable_source(source: Source) -> Source:
    if isinstance(source, (str, Path, bytes, bytearray)):
        return source
    try:
        position = source.tell()
        source.seek(position)
        return source
    except (AttributeError, OSError, TypeError, ValueError):
        value = source.read()
    if isinstance(value, str):
        return StringIO(value)
    if isinstance(value, (bytes, bytearray)):
        return BytesIO(bytes(value))
    raise TypeError("source stream must yield text or bytes")


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
    reader = _implements_protocol_methods(value, CadReaderAdapter)
    writer = _implements_protocol_methods(value, CadWriterAdapter)
    return value if reader or writer else None


def _implements_protocol_methods(value: object, protocol: type[object]) -> bool:
    names = (
        name
        for name, member in vars(protocol).items()
        if not name.startswith("_") and callable(member)
    )
    return all(callable(getattr(value, name, None)) for name in names)


def _module_adapter_types(module: ModuleType) -> tuple[type[object], ...]:
    adapter_types = {
        adapter_type
        for value in vars(module).values()
        if (adapter_type := _adapter_type(value, module.__name__)) is not None
    }
    return tuple(
        sorted(adapter_types, key=lambda value: (value.__module__, value.__qualname__))
    )


def _validated_info(adapter: object) -> AdapterInfo:
    info = adapter.info
    if not isinstance(info, AdapterInfo):
        raise AdapterRegistryError("adapter info must be AdapterInfo")
    hints = get_type_hints(AdapterInfo)
    for item in fields(info):
        value = getattr(info, item.name)
        hint = hints[item.name]
        origin = get_origin(hint)
        arguments = get_args(hint)
        if hint is str:
            valid_type = isinstance(value, str)
        elif origin is tuple and len(arguments) == 2 and arguments[1] is Ellipsis:
            valid_type = isinstance(value, tuple) and all(
                isinstance(member, arguments[0]) for member in value
            )
        elif origin is frozenset and len(arguments) == 1:
            valid_type = isinstance(value, frozenset) and all(
                isinstance(member, arguments[0]) for member in value
            )
        else:
            raise AdapterRegistryError(f"unsupported adapter field {item.name}")
        if not valid_type:
            raise AdapterRegistryError(f"adapter {item.name} has an invalid type")
        if isinstance(value, str) and (not value.strip() or value != value.strip()):
            raise AdapterRegistryError(
                f"adapter {item.name} must be a non-empty string"
            )
        if isinstance(value, tuple):
            if any(
                not isinstance(member, str)
                or not member.strip()
                or member != member.strip()
                for member in value
            ):
                raise AdapterRegistryError(
                    f"adapter {item.name} must be a string tuple"
                )
            if len({member.casefold() for member in value}) != len(value):
                raise AdapterRegistryError(f"adapter {item.name} must be unique")
    if info.format_id.casefold() in {alias.casefold() for alias in info.aliases}:
        raise AdapterRegistryError("adapter alias must differ from its format id")
    extensions = {value.casefold() for value in info.extensions}
    if any(not value.startswith(".") for value in info.extensions):
        raise AdapterRegistryError("adapter extensions must begin with a dot")
    for kind, values in (
        ("part", info.part_extensions),
        ("assembly", info.assembly_extensions),
    ):
        if any(value.casefold() not in extensions for value in values):
            raise AdapterRegistryError(
                f"adapter {kind} extensions must also be declared extensions"
            )
    if not info.native_capabilities <= info.capabilities:
        raise AdapterRegistryError(
            "adapter native capabilities must also be preservation capabilities"
        )
    return info


def _key(value: str) -> str:
    return value.casefold()


def _format_keys(info: AdapterInfo) -> frozenset[str]:
    return frozenset(_key(value) for value in (info.format_id, *info.aliases))


def _document_capabilities(document: CadDocument) -> frozenset[Capability]:
    inferred = infer_capabilities(
        document,
        roundtrip_metadata=(Capability.ROUNDTRIP_METADATA in document.capabilities),
    )
    return document.capabilities | inferred


def _write_result(
    document: CadDocument,
    info: AdapterInfo,
    result: WriteResult,
) -> WriteResult:
    capabilities = _document_capabilities(document)
    if result.dropped:
        raise CapabilityLossError(info.format_id, result.dropped)
    if result.transfers:
        transferred = frozenset(transfer.capability for transfer in result.transfers)
        if transferred != capabilities:
            missing = capabilities - transferred
            if missing:
                raise CapabilityLossError(info.format_id, missing)
            raise AdapterRegistryError(
                f"{info.format_id} reported capabilities absent from the source"
            )
        transfers = result.transfers
    else:
        exact = result.metadata.get("compatibility") == "native-exact"
        native = capabilities if exact else capabilities & info.native_capabilities
        transfers = tuple(
            CapabilityTransfer(
                capability,
                (TransferMode.NATIVE if capability in native else TransferMode.CARRIER),
            )
            for capability in sorted(capabilities, key=lambda value: value.value)
        )
    return replace(
        result,
        transfers=transfers,
        dropped=frozenset(),
    )


def _allow_carrier(options: WriteOptions) -> bool:
    value = options.values.get("allow_carrier", False)
    if not isinstance(value, bool):
        raise TypeError("allow_carrier must be a boolean")
    return value


def _require_self_contained(options: WriteOptions) -> bool:
    value = options.values.get("require_self_contained", True)
    if not isinstance(value, bool):
        raise TypeError("require_self_contained must be a boolean")
    return value


def _writer_options(options: WriteOptions) -> tuple[WriteOptions, bool, bool]:
    allow_carrier = _allow_carrier(options)
    require_self_contained = _require_self_contained(options)
    values = dict(options.values)
    values["allow_carrier"] = allow_carrier
    values["require_self_contained"] = require_self_contained
    values["allow_non_native"] = True
    return (
        replace(options, values=frozen_mapping(values)),
        allow_carrier,
        require_self_contained,
    )


def _checked_write(
    document: CadDocument,
    adapter: CadWriterAdapter,
    destination: Destination,
    options: WriteOptions,
    allow_carrier: bool,
    require_self_contained: bool,
) -> WriteResult:
    result = adapter.write(document, destination, options)
    if not isinstance(result, WriteResult):
        raise AdapterRegistryError(
            f"writer {adapter.info.format_id} returned an invalid write result"
        )
    if _key(result.adapter) not in _format_keys(adapter.info):
        raise AdapterRegistryError(
            f"writer {adapter.info.format_id} returned write format {result.adapter}"
        )
    checked = _write_result(document, adapter.info, result)
    carrier_only = bool(checked.transfers) and not checked.native_capabilities
    default_carrier_blockers = tuple(
        transfer
        for transfer in checked.transfers
        if transfer.carrier_reason is not None
        and transfer.carrier_reason is not CarrierReason.TARGET_UNSUPPORTED
    )
    if (
        carrier_only
        and default_carrier_blockers
        and (checked.application_usable or checked.vendor_loadable)
    ):
        metadata = dict(checked.metadata)
        metadata["application_usable"] = False
        metadata["vendor_loadable"] = False
        checked = replace(
            checked,
            metadata=frozen_mapping(metadata),
            application_usable=False,
            vendor_loadable=False,
        )
    if require_self_contained and checked.requirements:
        raise ApplicationUsabilityError(adapter.info.format_id, checked)
    if not allow_carrier and (
        not checked.application_usable
        or not checked.vendor_loadable
        or bool(checked.requirements)
        or bool(checked.dropped)
        or bool(default_carrier_blockers)
    ):
        raise ApplicationUsabilityError(adapter.info.format_id, checked)
    return checked


def _path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _absent_ancestors(path: Path) -> tuple[Path, ...]:
    result: list[Path] = []
    current = path
    while not _path_exists(current):
        result.append(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return tuple(result)


def _directory_identity(path: Path) -> tuple[int, int, int]:
    status = path.stat(follow_symlinks=False)
    return status.st_dev, status.st_ino, status.st_mode


def _remove_created_ancestors(
    values: tuple[tuple[Path, tuple[int, int, int]], ...],
) -> None:
    for path, identity in values:
        try:
            if _directory_identity(path) != identity:
                break
            path.rmdir()
        except FileNotFoundError:
            continue
        except OSError:
            break


def _commit_staged_outputs(
    staging: Path,
    destination: Path,
    overwrite: bool,
) -> None:
    outputs = tuple(
        sorted(
            staging.iterdir(),
            key=lambda path: (
                path.name.casefold() != destination.name.casefold(),
                path.name.casefold(),
                path.name,
            ),
        )
    )
    if not outputs or not _path_exists(staging / destination.name):
        raise AdapterRegistryError("writer did not create the requested destination")
    targets = tuple((output, destination.parent / output.name) for output in outputs)
    if not overwrite:
        conflict = next(
            (target for _, target in targets if _path_exists(target)),
            None,
        )
        if conflict is not None:
            raise FileExistsError(conflict)
    backup = staging / ".kit-backup"
    replaced: list[tuple[Path, Path]] = []
    committed: list[tuple[Path, Path]] = []
    try:
        if overwrite and any(_path_exists(target) for _, target in targets):
            backup.mkdir()
            for _, target in targets:
                if not _path_exists(target):
                    continue
                saved = backup / target.name
                os.replace(target, saved)
                replaced.append((saved, target))
        for output, target in targets:
            os.replace(output, target)
            committed.append((target, output))
    except BaseException:
        for target, output in reversed(committed):
            if _path_exists(target):
                os.replace(target, output)
        for saved, target in reversed(replaced):
            if _path_exists(saved):
                os.replace(saved, target)
        raise


def _write_path_staged(
    document: CadDocument,
    adapter: CadWriterAdapter,
    destination: str | Path,
    options: WriteOptions,
    allow_carrier: bool,
    require_self_contained: bool,
) -> WriteResult:
    final = Path(destination).expanduser().resolve()
    if _path_exists(final) and not options.overwrite:
        raise FileExistsError(final)
    absent = _absent_ancestors(final.parent)
    created: list[tuple[Path, tuple[int, int, int]]] = []
    try:
        for path in reversed(absent):
            try:
                path.mkdir()
            except FileExistsError:
                if path.is_symlink() or not path.is_dir():
                    raise
                continue
            created.append((path, _directory_identity(path)))
        prefix = f".{final.name}.kit-"
        with TemporaryDirectory(prefix=prefix, dir=final.parent) as temporary:
            staging = Path(temporary)
            staged_destination = staging / final.name
            result = _checked_write(
                document,
                adapter,
                staged_destination,
                replace(options, overwrite=False),
                allow_carrier,
                require_self_contained,
            )
            if (
                result.path is None
                or result.path.resolve() != staged_destination.resolve()
            ):
                raise AdapterRegistryError(
                    "path writer returned an unexpected destination"
                )
            _commit_staged_outputs(staging, final, options.overwrite)
    except BaseException:
        _remove_created_ancestors(tuple(reversed(created)))
        raise
    return replace(result, path=final)


def _write_stream_staged(
    document: CadDocument,
    adapter: CadWriterAdapter,
    destination: Destination,
    options: WriteOptions,
    allow_carrier: bool,
    require_self_contained: bool,
) -> WriteResult:
    staged = BytesIO() if is_binary_destination(destination) else StringIO()
    result = _checked_write(
        document,
        adapter,
        staged,
        options,
        allow_carrier,
        require_self_contained,
    )
    if result.path is not None:
        raise AdapterRegistryError("stream writer returned a filesystem path")
    payload = staged.getvalue()
    writer = getattr(destination, "write", None)
    if not callable(writer):
        raise TypeError("destination must be a writable path or stream")
    written = writer(payload)
    if written is not None and written != len(payload):
        raise OSError(
            f"short destination write: expected {len(payload)}, wrote {written}"
        )
    return result


class AdapterRegistry:
    def __init__(self) -> None:
        self._bindings: dict[str, AdapterBinding] = {}
        self._aliases: dict[str, str] = {}

    def _validate_namespace(self, info: AdapterInfo) -> None:
        format_key = _key(info.format_id)
        owner = self._aliases.get(format_key)
        if owner is not None:
            raise AdapterRegistryError(
                f"format id is already an alias for {owner}: {info.format_id}"
            )
        for alias in info.aliases:
            alias_key = _key(alias)
            if alias_key in self._bindings:
                raise AdapterRegistryError(
                    f"adapter alias is already a format id: {alias}"
                )
            existing = self._aliases.get(alias_key)
            if existing is not None and existing != format_key:
                raise AdapterRegistryError(f"adapter alias already registered: {alias}")

    def _register_aliases(self, info: AdapterInfo, replace: bool) -> None:
        owner_key = _key(info.format_id)
        alias_keys = {_key(alias) for alias in info.aliases}
        if replace:
            stale = tuple(
                alias
                for alias, owner in self._aliases.items()
                if owner == owner_key and alias not in alias_keys
            )
            for alias in stale:
                del self._aliases[alias]
        for alias in info.aliases:
            self._aliases[_key(alias)] = owner_key

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

    def _register_reader(
        self,
        adapter: CadReaderAdapter,
        replace: bool,
        coordinated: bool,
    ) -> None:
        info = _validated_info(adapter)
        self._validate_namespace(info)
        format_key = _key(info.format_id)
        binding = self._bindings.get(format_key)
        if binding is None:
            binding = AdapterBinding()
        if (
            binding.writer is not None
            and binding.writer.info != info
            and not coordinated
        ):
            raise AdapterRegistryError(
                f"reader and writer metadata differ for {info.format_id}"
            )
        if binding.reader is not None and not replace:
            if type(binding.reader) is type(adapter) and binding.reader.info == info:
                return
            raise AdapterRegistryError(
                f"reader already registered for {info.format_id}"
            )
        self._register_aliases(info, replace)
        self._bindings.setdefault(format_key, binding)
        binding.reader = adapter

    def register_reader(
        self, adapter: CadReaderAdapter, *, replace: bool = False
    ) -> None:
        self._register_reader(adapter, replace, False)

    def _register_writer(
        self,
        adapter: CadWriterAdapter,
        replace: bool,
        coordinated: bool,
    ) -> None:
        info = _validated_info(adapter)
        self._validate_namespace(info)
        format_key = _key(info.format_id)
        binding = self._bindings.get(format_key)
        if binding is None:
            binding = AdapterBinding()
        if (
            binding.reader is not None
            and binding.reader.info != info
            and not coordinated
        ):
            raise AdapterRegistryError(
                f"reader and writer metadata differ for {info.format_id}"
            )
        if binding.writer is not None and not replace:
            if type(binding.writer) is type(adapter) and binding.writer.info == info:
                return
            raise AdapterRegistryError(
                f"writer already registered for {info.format_id}"
            )
        self._register_aliases(info, replace)
        self._bindings.setdefault(format_key, binding)
        binding.writer = adapter

    def register_writer(
        self, adapter: CadWriterAdapter, *, replace: bool = False
    ) -> None:
        self._register_writer(adapter, replace, False)

    def register(self, adapter: object, *, replace: bool = False) -> None:
        state = self._state()
        reader = isinstance(adapter, CadReaderAdapter)
        writer = isinstance(adapter, CadWriterAdapter)
        coordinated = reader and writer and replace
        try:
            if reader:
                self._register_reader(adapter, replace, coordinated)
            if writer:
                self._register_writer(adapter, replace, coordinated)
            if not reader and not writer:
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
            discovered_modules = tuple(
                sorted(
                    (item.name, item.ispkg)
                    for item in iter_modules(paths, package.__name__ + ".")
                    if not item.name.rsplit(".", 1)[-1].startswith("_")
                )
            )
        except Exception as exc:
            raise AdapterDiscoveryError(
                f"could not enumerate adapter package {package_name}"
            ) from exc
        if not discovered_modules:
            raise AdapterDiscoveryError(f"adapter package is empty: {package_name}")
        instances: list[object] = []
        seen_types: set[type[object]] = set()
        for discovered_name, is_package in discovered_modules:
            try:
                module = import_module(discovered_name)
            except Exception as exc:
                raise AdapterDiscoveryError(
                    f"could not import format package {discovered_name}"
                ) from exc
            modules = [module]
            if is_package:
                try:
                    nested_names = tuple(
                        sorted(
                            item.name
                            for item in walk_packages(
                                module.__path__, module.__name__ + "."
                            )
                            if all(
                                not segment.startswith("_")
                                for segment in item.name[
                                    len(module.__name__) + 1 :
                                ].split(".")
                            )
                        )
                    )
                    modules.extend(import_module(name) for name in nested_names)
                except Exception as exc:
                    raise AdapterDiscoveryError(
                        f"could not inspect format package {discovered_name}"
                    ) from exc
            adapter_types = tuple(
                sorted(
                    {
                        adapter_type
                        for candidate in modules
                        for adapter_type in _module_adapter_types(candidate)
                    },
                    key=lambda value: (value.__module__, value.__qualname__),
                )
            )
            if not adapter_types:
                if is_package:
                    raise AdapterDiscoveryError(
                        f"format package contains no adapter: {discovered_name}"
                    )
                continue
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
                reader = isinstance(
                    adapter, CadReaderAdapter
                ) and _implements_protocol_methods(adapter, CadReaderAdapter)
                writer = isinstance(
                    adapter, CadWriterAdapter
                ) and _implements_protocol_methods(adapter, CadWriterAdapter)
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
        format_key = _key(format_id)
        binding = self._bindings.get(self._aliases.get(format_key, format_key))
        if binding is None or binding.reader is None:
            raise AdapterNotFoundError(f"no reader registered for {format_id}")
        return binding.reader

    def writer(self, format_id: str) -> CadWriterAdapter:
        format_key = _key(format_id)
        binding = self._bindings.get(self._aliases.get(format_key, format_key))
        if binding is None or binding.writer is None:
            raise AdapterNotFoundError(f"no writer registered for {format_id}")
        return binding.writer

    def select_reader(self, source: Source) -> CadReaderAdapter:
        results: list[tuple[ProbeResult, CadReaderAdapter]] = []
        for adapter in self.readers():
            result = adapter.probe(source)
            if not isinstance(result, ProbeResult):
                raise AdapterRegistryError(
                    f"reader {adapter.info.format_id} returned an invalid probe result"
                )
            if _key(result.format_id) not in _format_keys(adapter.info):
                raise AdapterRegistryError(
                    f"reader {adapter.info.format_id} returned probe format "
                    f"{result.format_id}"
                )
            if result.confidence > 0:
                results.append((result, adapter))
        if not results:
            raise AdapterNotFoundError("no reader recognizes the source")
        results.sort(key=lambda item: item[0].confidence, reverse=True)
        confidence = results[0][0].confidence
        tied = tuple(
            adapter.info.format_id
            for result, adapter in results
            if result.confidence == confidence
        )
        if len(tied) > 1:
            raise AmbiguousAdapterError("reader probe tied between " + ", ".join(tied))
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
                Path(destination).suffix.casefold()
                if isinstance(destination, (str, Path))
                else ""
            )
            exact = [
                adapter
                for adapter in candidates
                if extension in {item.casefold() for item in adapter.info.extensions}
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
        document, _ = self.read_with_adapter(
            source, format_id=format_id, options=options
        )
        return document

    def read_with_adapter(
        self,
        source: Source,
        *,
        format_id: str | None = None,
        options: ReadOptions | None = None,
    ) -> tuple[CadDocument, CadReaderAdapter]:
        selected_source = _replayable_source(source)
        position = 0
        if not isinstance(selected_source, (str, Path, bytes, bytearray)):
            position = selected_source.tell()
        adapter = (
            self.reader(format_id) if format_id else self.select_reader(selected_source)
        )
        if not isinstance(selected_source, (str, Path, bytes, bytearray)):
            selected_source.seek(position)
        document = adapter.read(selected_source, options)
        document.assert_valid()
        return document, adapter

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
        selected = options or WriteOptions()
        if format_id is not None:
            selected = replace(selected, destination_format=format_id)
        selected, allow_carrier, require_self_contained = _writer_options(selected)
        if not adapter.supports(document, destination):
            raise AdapterNotFoundError(
                f"{adapter.info.format_id} does not support the destination"
            )
        if selected.validate:
            document.assert_valid()
        required = _document_capabilities(document)
        unsupported = required - adapter.info.capabilities
        if unsupported:
            raise CapabilityLossError(adapter.info.format_id, unsupported)
        if isinstance(destination, (str, Path)):
            return _write_path_staged(
                document,
                adapter,
                destination,
                selected,
                allow_carrier,
                require_self_contained,
            )
        return _write_stream_staged(
            document,
            adapter,
            destination,
            selected,
            allow_carrier,
            require_self_contained,
        )

    def format_ids(self) -> tuple[str, ...]:
        values = {
            value
            for binding in self._bindings.values()
            for adapter in (binding.reader, binding.writer)
            if adapter is not None
            for value in (adapter.info.format_id, *adapter.info.aliases)
        }
        return tuple(sorted(values, key=lambda value: (value.casefold(), value)))

    def extend(self, adapters: Iterable[object], *, replace: bool = False) -> None:
        state = self._state()
        try:
            for adapter in adapters:
                self.register(adapter, replace=replace)
        except Exception:
            self._restore(state)
            raise

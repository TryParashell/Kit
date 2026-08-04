# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import base64
from collections.abc import Mapping as MappingABC
from dataclasses import fields, is_dataclass
from enum import Enum
import json
from types import MappingProxyType
from typing import Any, Callable, Mapping, get_origin, get_type_hints

_TYPE_REGISTRY: dict[str, type] = {}
_MIGRATION_REGISTRY: dict[type, Callable[[Mapping[str, Any]], Mapping[str, Any]]] = {}


def register_types(*types: type) -> None:
    for value in types:
        existing = _TYPE_REGISTRY.get(value.__name__)
        if existing is not None and existing is not value:
            raise ValueError(f"duplicate interchange type name {value.__name__!r}")
        _TYPE_REGISTRY[value.__name__] = value


def register_migration(
    target: type, migration: Callable[[Mapping[str, Any]], Mapping[str, Any]]
) -> None:
    existing = _MIGRATION_REGISTRY.get(target)
    if existing is not None and existing is not migration:
        raise ValueError(f"duplicate interchange migration for {target.__name__!r}")
    _MIGRATION_REGISTRY[target] = migration


def _ordered_data(values: set[Any] | frozenset[Any]) -> list[Any]:
    encoded = [to_data(item) for item in values]
    return sorted(
        encoded,
        key=lambda item: json.dumps(
            item,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )


def to_data(value: Any) -> Any:
    if is_dataclass(value):
        result = {"$type": type(value).__name__}
        for item in fields(value):
            result[item.name] = to_data(getattr(value, item.name))
        return result
    if isinstance(value, Enum):
        return {"$enum": type(value).__name__, "value": value.value}
    if isinstance(value, bytes):
        return {"$bytes": base64.b64encode(value).decode("ascii")}
    if isinstance(value, tuple):
        return {"$tuple": [to_data(item) for item in value]}
    if isinstance(value, frozenset):
        return {"$frozenset": _ordered_data(value)}
    if isinstance(value, set):
        return {"$set": _ordered_data(value)}
    if isinstance(value, list):
        return [to_data(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): to_data(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"cannot serialize value of type {type(value).__name__}")


def from_data(value: Any) -> Any:
    if isinstance(value, list):
        return [from_data(item) for item in value]
    if not isinstance(value, dict):
        return value
    if set(value) == {"$bytes"}:
        return base64.b64decode(value["$bytes"], validate=True)
    if set(value) == {"$tuple"}:
        return tuple(from_data(item) for item in value["$tuple"])
    if set(value) == {"$frozenset"}:
        return frozenset(from_data(item) for item in value["$frozenset"])
    if set(value) == {"$set"}:
        return set(from_data(item) for item in value["$set"])
    if "$enum" in value:
        enum_type = _TYPE_REGISTRY.get(value["$enum"])
        if enum_type is None or not issubclass(enum_type, Enum):
            raise ValueError(f"unknown enum type {value['$enum']!r}")
        return enum_type(value["value"])
    type_name = value.get("$type")
    if type_name:
        target = _TYPE_REGISTRY.get(type_name)
        if target is None:
            raise ValueError(f"unknown data type {type_name!r}")
        arguments = {
            key: from_data(item) for key, item in value.items() if key != "$type"
        }
        migration = _MIGRATION_REGISTRY.get(target)
        if migration is not None:
            arguments = dict(migration(MappingProxyType(arguments)))
        hints = get_type_hints(target)
        for item in fields(target):
            hint = hints.get(item.name)
            if (
                item.name in arguments
                and isinstance(arguments[item.name], dict)
                and get_origin(hint) in {Mapping, MappingABC}
            ):
                arguments[item.name] = MappingProxyType(dict(arguments[item.name]))
        return target(**arguments)
    return {key: from_data(item) for key, item in value.items()}


def dumps(value: Any, *, indent: int | None = 2) -> str:
    return json.dumps(to_data(value), indent=indent, sort_keys=True, ensure_ascii=False)


def loads(source: str) -> Any:
    return from_data(json.loads(source))

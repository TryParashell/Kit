# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from typing import Mapping as TypeMap

from interchange import frozen_mapping as FreezeMapping

from convert.adapters.base.ContractCompat import ContractBase


# write policy stays immutable so staging and adapters share one transactional intent
@DataClass(frozen=True, slots=True)
class WriteOptions(ContractBase):
    ConfigName: str | None = None
    Overwrite: bool = False
    Validate: bool = True
    TargetFormat: str | None = None
    OptionValues: TypeMap[str, object] = DataField(default_factory=FreezeMapping)

    # historical configuration access remains typed because writers consume this public selection field
    @property
    def configuration(self) -> str | None:
        return self.ConfigName

    # historical overwrite access remains typed because staging consumes this public transaction field
    @property
    def overwrite(self) -> bool:
        return self.Overwrite

    # historical validation access remains typed because writers consume this public safety field
    @property
    def validate(self) -> bool:
        return self.Validate

    # historical format access remains typed because registries consume this public selection field
    @property
    def destination_format(self) -> str | None:
        return self.TargetFormat

    # historical option access remains typed because adapters consume this public extension field
    @property
    def values(self) -> TypeMap[str, object]:
        return self.OptionValues

    # explicit construction keeps canonical storage and historical keywords visible to static callers
    def __init__(
        self,
        ConfigName: str | None = None,
        Overwrite: bool = False,
        Validate: bool = True,
        TargetFormat: str | None = None,
        OptionValues: TypeMap[str, object] | None = None,
        *,
        configuration: str | None = None,
        overwrite: bool | None = None,
        validate: bool | None = None,
        destination_format: str | None = None,
        values: TypeMap[str, object] | None = None,
    ) -> None:
        object.__setattr__(
            self,
            "ConfigName",
            ConfigName if configuration is None else configuration,
        )
        object.__setattr__(
            self,
            "Overwrite",
            Overwrite if overwrite is None else overwrite,
        )
        object.__setattr__(
            self,
            "Validate",
            Validate if validate is None else validate,
        )
        object.__setattr__(
            self,
            "TargetFormat",
            TargetFormat if destination_format is None else destination_format,
        )
        SelectedValues = OptionValues if values is None else values
        object.__setattr__(
            self,
            "OptionValues",
            (
                FreezeMapping()
                if SelectedValues is None
                else FreezeMapping(SelectedValues)
            ),
        )

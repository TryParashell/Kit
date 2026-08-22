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
    configuration: str | None = None
    overwrite: bool = False
    validate: bool = True
    destination_format: str | None = None
    values: TypeMap[str, object] = DataField(default_factory=FreezeMapping)

    # historical configuration access remains typed because writers consume this public selection field
    @property
    def ConfigName(self) -> str | None:
        return self.configuration

    # historical overwrite access remains typed because staging consumes this public transaction field
    @property
    def Overwrite(self) -> bool:
        return self.overwrite

    # historical validation access remains typed because writers consume this public safety field
    @property
    def Validate(self) -> bool:
        return self.validate

    # historical format access remains typed because registries consume this public selection field
    @property
    def TargetFormat(self) -> str | None:
        return self.destination_format

    # historical option access remains typed because adapters consume this public extension field
    @property
    def OptionValues(self) -> TypeMap[str, object]:
        return self.values

    # explicit construction keeps canonical storage and historical keywords visible to static callers
    def __init__(
        self,
        configuration: str | None = None,
        overwrite: bool = False,
        validate: bool = True,
        destination_format: str | None = None,
        values: TypeMap[str, object] | None = None,
        *,
        ConfigName: str | None = None,
        Overwrite: bool | None = None,
        Validate: bool | None = None,
        TargetFormat: str | None = None,
        OptionValues: TypeMap[str, object] | None = None,
    ) -> None:
        super().__init__()
        object.__setattr__(
            self,
            "configuration",
            configuration if ConfigName is None else ConfigName,
        )
        object.__setattr__(
            self,
            "overwrite",
            overwrite if Overwrite is None else Overwrite,
        )
        object.__setattr__(
            self,
            "validate",
            validate if Validate is None else Validate,
        )
        object.__setattr__(
            self,
            "destination_format",
            destination_format if TargetFormat is None else TargetFormat,
        )
        SelectedValues = values if OptionValues is None else OptionValues
        object.__setattr__(
            self,
            "values",
            (
                FreezeMapping()
                if SelectedValues is None
                else FreezeMapping(SelectedValues)
            ),
        )

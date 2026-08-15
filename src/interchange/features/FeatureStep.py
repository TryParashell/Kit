# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from dataclasses import field as MakeDataField
from typing import ClassVar
from typing import Mapping as TypeMap
from typing import TYPE_CHECKING

from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.features.FeatureContract import FeatureDef
from interchange.core.ModelBase import ModelBase
from interchange.records.RecordProvenance import Provenance


# runtime construction accepts untrusted values so feature definitions need one checked boundary
def ValidateFeature(SourceValue: object) -> FeatureDef | None:
    if SourceValue is None or isinstance(SourceValue, FeatureDef):
        return SourceValue
    raise TypeError("feature definition must implement FeatureDefinition")


# canonical typing needs an inherited key while public reflection exposes historical fields
class FeatureHintBase(ModelBase):
    Definition: FeatureDef | None
    if TYPE_CHECKING:
        definition: ClassVar[FeatureDef | None]


# configuration state retains suppression and parameter changes without duplicate features
@MakeDataClass(frozen=True, slots=True)
class FeatureCfgState(ModelBase):
    ConfigurationId: str
    IsSuppressed: bool = False
    ParamOverrideIds: tuple[str, ...] = ()


# feature steps preserve ordered dependencies and definitions for editable translation
@MakeDataClass(frozen=True, slots=True)
class FeatureStep(FeatureHintBase):
    EntityId: str
    EntityName: str
    EntityKind: FeatureKind | str
    Order: int
    InputFeatureIds: tuple[str, ...] = ()
    SketchId: str | None = None
    ParameterIds: tuple[str, ...] = ()
    Operation: BooleanOp | str | None = None
    Definition: FeatureDef | None = None
    SelectionIds: tuple[str, ...] = ()
    IsSuppressed: bool = False
    ConfigStates: tuple[FeatureCfgState, ...] = ()
    Provenance: Provenance | None = None
    Attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    # invalid definitions must fail before corrupt feature records propagate
    def __post_init__(self) -> None:
        ValidateFeature(self.Definition)

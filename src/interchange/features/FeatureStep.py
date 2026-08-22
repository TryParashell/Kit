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
    definition: FeatureDef | None
    if TYPE_CHECKING:
        Definition: ClassVar[FeatureDef | None]


# configuration state retains suppression and parameter changes without duplicate features
@MakeDataClass(frozen=True, slots=True)
class FeatureCfgState(ModelBase):
    configuration_id: str
    suppressed: bool = False
    parameter_override_ids: tuple[str, ...] = ()
    if TYPE_CHECKING:
        ConfigurationId: ClassVar[str]
        IsSuppressed: ClassVar[bool]
        ParamOverrideIds: ClassVar[tuple[str, ...]]


# feature steps preserve ordered dependencies and definitions for editable translation
@MakeDataClass(frozen=True, slots=True)
class FeatureStep(FeatureHintBase):
    id: str
    name: str
    kind: FeatureKind | str
    order: int
    input_feature_ids: tuple[str, ...] = ()
    sketch_id: str | None = None
    parameter_ids: tuple[str, ...] = ()
    operation: BooleanOp | str | None = None
    definition: FeatureDef | None = None
    selection_ids: tuple[str, ...] = ()
    suppressed: bool = False
    configuration_states: tuple[FeatureCfgState, ...] = ()
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityName: ClassVar[str]
        EntityKind: ClassVar[FeatureKind | str]
        Order: ClassVar[int]
        InputFeatureIds: ClassVar[tuple[str, ...]]
        SketchId: ClassVar[str | None]
        ParameterIds: ClassVar[tuple[str, ...]]
        Operation: ClassVar[BooleanOp | str | None]
        Definition: ClassVar[FeatureDef | None]
        SelectionIds: ClassVar[tuple[str, ...]]
        IsSuppressed: ClassVar[bool]
        ConfigStates: ClassVar[tuple[FeatureCfgState, ...]]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]

    # invalid definitions must fail before corrupt feature records propagate
    def __post_init__(self) -> None:
        ValidateFeature(self.definition)

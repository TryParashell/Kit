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
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.features.FeatureContract import FeatureDef
from interchange.core.ModelBase import ModelBase
from interchange.records.RecordProvenance import Provenance

from typing_extensions import override as Override


# runtime construction accepts untrusted values so feature definitions need one checked boundary
def ValidateFeature(SourceValue: object) -> FeatureDef | None:
    if SourceValue is None or isinstance(SourceValue, FeatureDef):
        return SourceValue
    raise TypeError("feature definition must implement FeatureDefinition")


# canonical typing needs an inherited key while public reflection exposes historical fields
class FeatureHintBase(ModelBase):
    definition: FeatureDef | None = None

    # linked parameters keep feature configuration editable after creation
    @property
    def Definition(self) -> FeatureDef | None:
        return self.definition


# configuration state retains suppression and parameter changes without duplicate features
@MakeDataClass(frozen=True, slots=True)
class FeatureCfgState(ModelBase):
    configuration_id: str
    suppressed: bool = False
    parameter_override_ids: tuple[str, ...] = ()

    # configuration id keeps variant references stable across renames
    @property
    def ConfigurationId(self) -> str:
        return self.configuration_id

    # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return self.suppressed

    # override list tracks configuration specific parameters without cloning steps
    @property
    def ParamOverrideIds(self) -> tuple[str, ...]:
        return self.parameter_override_ids


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

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

    # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return self.name

    # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> FeatureKind | str:
        return self.kind

    # explicit order keeps sibling sequencing stable across adapter round trips
    @property
    def Order(self) -> int:
        return self.order

    # input list preserves feature dependency order for rebuilds
    @property
    def InputFeatureIds(self) -> tuple[str, ...]:
        return self.input_feature_ids

    # optional sketch link keeps sketch driven features traceable
    @property
    def SketchId(self) -> str | None:
        return self.sketch_id

    # parameter links keep mate values driven by configurable expressions
    @property
    def ParameterIds(self) -> tuple[str, ...]:
        return self.parameter_ids

    # boolean operation names the combine subtract or keep intent explicitly
    @property
    def Operation(self) -> BooleanOp | str | None:
        return self.operation

    # linked parameters keep feature configuration editable after creation
    @property
    @Override
    @Override
    def Definition(self) -> FeatureDef | None:
        return self.definition

    # selection list keeps user picked references replayable on reload
    @property
    def SelectionIds(self) -> tuple[str, ...]:
        return self.selection_ids

    # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return self.suppressed

    # per configuration states capture suppression without duplicated features
    @property
    def ConfigStates(self) -> tuple[FeatureCfgState, ...]:
        return self.configuration_states

    # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes

    # invalid definitions must fail before corrupt feature records propagate
    def __post_init__(self) -> None:
        _ = ValidateFeature(self.definition)

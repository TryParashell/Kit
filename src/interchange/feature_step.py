# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from .common import FreezeMapping
from .enum_features import BooleanOp, FeatureKind
from .feature_contract import FeatureDef
from .model_base import ModelBase, ModelDataMut
from .record_provenance import Provenance


# canonical typing needs an inherited key while public reflection exposes historical fields
class FeatureHintBase(ModelBase):
    Definition: FeatureDef | None


# configuration state retains suppression and parameter changes without duplicate features
@ModelDataMut(DefaultMap={"IsSuppressed": False, "ParamOverrideIds": ()})
class FeatureCfgState(ModelBase):
    ConfigurationId: str
    IsSuppressed: bool
    ParamOverrideIds: tuple[str, ...]


# feature steps preserve ordered dependencies and definitions for editable translation
@ModelDataMut(
    DefaultMap={
        "InputFeatureIds": (),
        "SketchId": None,
        "ParameterIds": (),
        "Operation": None,
        "Definition": None,
        "SelectionIds": (),
        "IsSuppressed": False,
        "ConfigStates": (),
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class FeatureStep(FeatureHintBase):
    EntityId: str
    EntityName: str
    EntityKind: FeatureKind | str
    Order: int
    InputFeatureIds: tuple[str, ...]
    SketchId: str | None
    ParameterIds: tuple[str, ...]
    Operation: BooleanOp | str | None
    Definition: FeatureDef | None
    SelectionIds: tuple[str, ...]
    IsSuppressed: bool
    ConfigStates: tuple[FeatureCfgState, ...]
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]

    # invalid definitions must fail before corrupt feature records propagate
    def __post_init__(SelfValue) -> None:
        if SelfValue.Definition is not None and not isinstance(
            SelfValue.Definition, FeatureDef
        ):
            raise TypeError("feature definition must implement FeatureDefinition")

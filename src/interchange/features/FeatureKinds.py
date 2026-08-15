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

from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.FeatureContract import FeatureDef
from interchange.features.FeatureExtrude import ExtrudeEnd
from interchange.core.ModelBase import ModelDataMut
from interchange.records.RecordParameter import ParameterValue
from interchange.geometry.models.VectorSpace import SpaceVector


# fillets retain constant and variable radius bindings for target reconstruction
@ModelDataMut(DefaultMap={"VariableRadiusParamIds": ()})
class FilletFeature(FeatureDef):
    Radius: ParameterValue
    VariableRadiusParamIds: tuple[str, ...]


# revolutions preserve axis direction and angular extent rather than only geometry
@ModelDataMut(DefaultMap={"IsReversed": False, "IsSymmetric": False})
class RevolveFeature(FeatureDef):
    Angle: ParameterValue
    AxisEntityId: str
    IsReversed: bool
    IsSymmetric: bool


# holes retain diameter depth and termination so targets create native features
@ModelDataMut(DefaultMap={"EndCondition": ExtrudeEnd.KBlind})
class HoleFeature(FeatureDef):
    Diameter: ParameterValue
    Depth: ParameterValue
    EndCondition: ExtrudeEnd | str


# chamfers retain alternate measurement modes so targets receive equivalent intent
@ModelDataMut(
    DefaultMap={"ValueMode": "equal_distance", "SecondDistance": None, "Angle": None}
)
class ChamferFeature(FeatureDef):
    Distance: ParameterValue
    ValueMode: str
    SecondDistance: ParameterValue | None
    Angle: ParameterValue | None


# shell features retain thickness orientation when topology cannot recover intent
@ModelDataMut(DefaultMap={"IsOutward": None})
class ShellFeature(FeatureDef):
    Thickness: ParameterValue
    IsOutward: bool | None


# linear patterns preserve editable pitch count and direction bindings
@ModelDataMut(DefaultMap={"IsReversed": False})
class LinearPattern(FeatureDef):
    Spacing: ParameterValue
    InstanceCount: int
    DirectionSelectionId: str
    IsReversed: bool


# circular patterns preserve angular span count and selected axis bindings
@ModelDataMut(DefaultMap={"IsReversed": False})
class CirclePattern(FeatureDef):
    Angle: ParameterValue
    InstanceCount: int
    AxisSelectionId: str
    IsReversed: bool


# reference planes retain support and offset bindings for editable reconstruction
@ModelDataMut
class RefPlaneFeature(FeatureDef):
    SupportPlaneId: str
    ReferencePlaneId: str
    Offset: ParameterValue


# dome features retain their driving height rather than only resulting surfaces
@ModelDataMut
class DomeFeature(FeatureDef):
    Height: ParameterValue


# body moves retain explicit translations and copy intent across histories
@ModelDataMut(DefaultMap={"IsCopy": False})
class MoveBodyFeature(FeatureDef):
    Translation: SpaceVector
    IsCopy: bool


# combine features preserve constructive operation intent between modeling kernels
@ModelDataMut(DefaultMap={"Operation": BooleanOp.KJoin})
class CombineFeature(FeatureDef):
    Operation: BooleanOp


# scale features retain anisotropic factors needed to reconstruct target operations
@ModelDataMut
class ScaleFeature(FeatureDef):
    Factors: SpaceVector


# native definitions preserve unsupported data without claiming portable semantics
@ModelDataMut(FactoryMap={"ObjectData": FreezeMapping})
class NativeFeature(FeatureDef):
    FormatId: str
    TypeId: str
    ObjectData: TypeMap[str, AnyValue]

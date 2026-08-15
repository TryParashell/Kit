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
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.FeatureContract import FeatureDef
from interchange.features.FeatureExtrude import ExtrudeEnd
from interchange.records.RecordParameter import ParameterValue
from interchange.geometry.models.VectorSpace import SpaceVector


# fillets retain constant and variable radius bindings for target reconstruction
@MakeDataClass(frozen=True, slots=True)
class FilletFeature(FeatureDef):
    Radius: ParameterValue
    VariableRadiusParamIds: tuple[str, ...] = ()


# revolutions preserve axis direction and angular extent rather than only geometry
@MakeDataClass(frozen=True, slots=True)
class RevolveFeature(FeatureDef):
    Angle: ParameterValue
    AxisEntityId: str
    IsReversed: bool = False
    IsSymmetric: bool = False


# holes retain diameter depth and termination so targets create native features
@MakeDataClass(frozen=True, slots=True)
class HoleFeature(FeatureDef):
    Diameter: ParameterValue
    Depth: ParameterValue
    EndCondition: ExtrudeEnd | str = ExtrudeEnd.KBlind


# chamfers retain alternate measurement modes so targets receive equivalent intent
@MakeDataClass(frozen=True, slots=True)
class ChamferFeature(FeatureDef):
    Distance: ParameterValue
    ValueMode: str = "equal_distance"
    SecondDistance: ParameterValue | None = None
    Angle: ParameterValue | None = None


# shell features retain thickness orientation when topology cannot recover intent
@MakeDataClass(frozen=True, slots=True)
class ShellFeature(FeatureDef):
    Thickness: ParameterValue
    IsOutward: bool | None = None


# linear patterns preserve editable pitch count and direction bindings
@MakeDataClass(frozen=True, slots=True)
class LinearPattern(FeatureDef):
    Spacing: ParameterValue
    InstanceCount: int
    DirectionSelectionId: str
    IsReversed: bool = False


# circular patterns preserve angular span count and selected axis bindings
@MakeDataClass(frozen=True, slots=True)
class CirclePattern(FeatureDef):
    Angle: ParameterValue
    InstanceCount: int
    AxisSelectionId: str
    IsReversed: bool = False


# reference planes retain support and offset bindings for editable reconstruction
@MakeDataClass(frozen=True, slots=True)
class RefPlaneFeature(FeatureDef):
    SupportPlaneId: str
    ReferencePlaneId: str
    Offset: ParameterValue


# dome features retain their driving height rather than only resulting surfaces
@MakeDataClass(frozen=True, slots=True)
class DomeFeature(FeatureDef):
    Height: ParameterValue


# body moves retain explicit translations and copy intent across histories
@MakeDataClass(frozen=True, slots=True)
class MoveBodyFeature(FeatureDef):
    Translation: SpaceVector
    IsCopy: bool = False


# combine features preserve constructive operation intent between modeling kernels
@MakeDataClass(frozen=True, slots=True)
class CombineFeature(FeatureDef):
    Operation: BooleanOp = BooleanOp.KJoin


# scale features retain anisotropic factors needed to reconstruct target operations
@MakeDataClass(frozen=True, slots=True)
class ScaleFeature(FeatureDef):
    Factors: SpaceVector


# native definitions preserve unsupported data without claiming portable semantics
@MakeDataClass(frozen=True, slots=True)
class NativeFeature(FeatureDef):
    FormatId: str
    TypeId: str
    ObjectData: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

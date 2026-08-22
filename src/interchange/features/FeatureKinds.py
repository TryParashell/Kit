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
    radius: ParameterValue
    variable_radius_parameter_ids: tuple[str, ...] = ()

    @property
    def Radius(self) -> ParameterValue:
        return self.radius

    @property
    def VariableRadiusParamIds(self) -> tuple[str, ...]:
        return self.variable_radius_parameter_ids


# revolutions preserve axis direction and angular extent rather than only geometry
@MakeDataClass(frozen=True, slots=True)
class RevolveFeature(FeatureDef):
    angle: ParameterValue
    axis_entity_id: str
    reversed: bool = False
    symmetric: bool = False

    @property
    def Angle(self) -> ParameterValue:
        return self.angle

    @property
    def AxisEntityId(self) -> str:
        return self.axis_entity_id

    @property
    def IsReversed(self) -> bool:
        return self.reversed

    @property
    def IsSymmetric(self) -> bool:
        return self.symmetric


# holes retain diameter depth and termination so targets create native features
@MakeDataClass(frozen=True, slots=True)
class HoleFeature(FeatureDef):
    diameter: ParameterValue
    depth: ParameterValue
    end_condition: ExtrudeEnd | str = ExtrudeEnd.KBlind

    @property
    def Diameter(self) -> ParameterValue:
        return self.diameter

    @property
    def Depth(self) -> ParameterValue:
        return self.depth

    @property
    def EndCondition(self) -> ExtrudeEnd | str:
        return self.end_condition


# chamfers retain alternate measurement modes so targets receive equivalent intent
@MakeDataClass(frozen=True, slots=True)
class ChamferFeature(FeatureDef):
    distance: ParameterValue
    mode: str = "equal_distance"
    second_distance: ParameterValue | None = None
    angle: ParameterValue | None = None

    @property
    def Distance(self) -> ParameterValue:
        return self.distance

    @property
    def ValueMode(self) -> str:
        return self.mode

    @property
    def SecondDistance(self) -> ParameterValue | None:
        return self.second_distance

    @property
    def Angle(self) -> ParameterValue | None:
        return self.angle


# shell features retain thickness orientation when topology cannot recover intent
@MakeDataClass(frozen=True, slots=True)
class ShellFeature(FeatureDef):
    thickness: ParameterValue
    outward: bool | None = None

    @property
    def Thickness(self) -> ParameterValue:
        return self.thickness

    @property
    def IsOutward(self) -> bool | None:
        return self.outward


# linear patterns preserve editable pitch count and direction bindings
@MakeDataClass(frozen=True, slots=True)
class LinearPattern(FeatureDef):
    spacing: ParameterValue
    instance_count: int
    direction_selection_id: str
    reversed: bool = False

    @property
    def Spacing(self) -> ParameterValue:
        return self.spacing

    @property
    def InstanceCount(self) -> int:
        return self.instance_count

    @property
    def DirectionSelectionId(self) -> str:
        return self.direction_selection_id

    @property
    def IsReversed(self) -> bool:
        return self.reversed


# circular patterns preserve angular span count and selected axis bindings
@MakeDataClass(frozen=True, slots=True)
class CirclePattern(FeatureDef):
    angle: ParameterValue
    instance_count: int
    axis_selection_id: str
    reversed: bool = False

    @property
    def Angle(self) -> ParameterValue:
        return self.angle

    @property
    def InstanceCount(self) -> int:
        return self.instance_count

    @property
    def AxisSelectionId(self) -> str:
        return self.axis_selection_id

    @property
    def IsReversed(self) -> bool:
        return self.reversed


# reference planes retain support and offset bindings for editable reconstruction
@MakeDataClass(frozen=True, slots=True)
class RefPlaneFeature(FeatureDef):
    support_plane_id: str
    reference_plane_id: str
    offset: ParameterValue

    @property
    def SupportPlaneId(self) -> str:
        return self.support_plane_id

    @property
    def ReferencePlaneId(self) -> str:
        return self.reference_plane_id

    @property
    def Offset(self) -> ParameterValue:
        return self.offset


# dome features retain their driving height rather than only resulting surfaces
@MakeDataClass(frozen=True, slots=True)
class DomeFeature(FeatureDef):
    height: ParameterValue

    @property
    def Height(self) -> ParameterValue:
        return self.height


# body moves retain explicit translations and copy intent across histories
@MakeDataClass(frozen=True, slots=True)
class MoveBodyFeature(FeatureDef):
    translation: SpaceVector
    copy: bool = False

    @property
    def Translation(self) -> SpaceVector:
        return self.translation

    @property
    def IsCopy(self) -> bool:
        return self.copy


# combine features preserve constructive operation intent between modeling kernels
@MakeDataClass(frozen=True, slots=True)
class CombineFeature(FeatureDef):
    operation: BooleanOp = BooleanOp.KJoin

    @property
    def Operation(self) -> BooleanOp:
        return self.operation


# scale features retain anisotropic factors needed to reconstruct target operations
@MakeDataClass(frozen=True, slots=True)
class ScaleFeature(FeatureDef):
    factors: SpaceVector

    @property
    def Factors(self) -> SpaceVector:
        return self.factors


# native definitions preserve unsupported data without claiming portable semantics
@MakeDataClass(frozen=True, slots=True)
class NativeFeature(FeatureDef):
    format_id: str
    type_id: str
    object_data: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    @property
    def FormatId(self) -> str:
        return self.format_id

    @property
    def TypeId(self) -> str:
        return self.type_id

    @property
    def ObjectData(self) -> TypeMap[str, object]:
        return self.object_data

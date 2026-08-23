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

     # radius keeps circles arcs and cylinders sized without sampling geometry
    @property
    def Radius(self) -> ParameterValue:
        return self.radius

     # per point radius ids keep variable fillets data driven
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

     # sweep angle defines partial revolutions without geometry evaluation
    @property
    def Angle(self) -> ParameterValue:
        return self.angle

     # axis reference keeps revolution geometry anchored to real entities
    @property
    def AxisEntityId(self) -> str:
        return self.axis_entity_id

     # orientation flag preserves which side of the topology is used
    @property
    def IsReversed(self) -> bool:
        return self.reversed

     # symmetric mode doubles length automatically so writers need no second value
    @property
    def IsSymmetric(self) -> bool:
        return self.symmetric


# holes retain diameter depth and termination so targets create native features
@MakeDataClass(frozen=True, slots=True)
class HoleFeature(FeatureDef):
    diameter: ParameterValue
    depth: ParameterValue
    end_condition: ExtrudeEnd | str = ExtrudeEnd.KBlind

     # diameter based definition matches how holes are engineered daily
    @property
    def Diameter(self) -> ParameterValue:
        return self.diameter

     # hole depth keeps drilled extents exact without geometry queries
    @property
    def Depth(self) -> ParameterValue:
        return self.depth

     # end condition captures blind through all and up to semantics in one field
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

     # offset distance keeps derived surfaces reproducible without measuring geometry
    @property
    def Distance(self) -> ParameterValue:
        return self.distance

     # value mode disambiguates blind versus through interpretations of depth
    @property
    def ValueMode(self) -> str:
        return self.mode

     # second distance covers through two extents in one feature
    @property
    def SecondDistance(self) -> ParameterValue | None:
        return self.second_distance

     # sweep angle defines partial revolutions without geometry evaluation
    @property
    def Angle(self) -> ParameterValue | None:
        return self.angle


# shell features retain thickness orientation when topology cannot recover intent
@MakeDataClass(frozen=True, slots=True)
class ShellFeature(FeatureDef):
    thickness: ParameterValue
    outward: bool | None = None

     # wall thickness defines thin features without inner loop construction
    @property
    def Thickness(self) -> ParameterValue:
        return self.thickness

     # outward choice decides which side gains material during offsets
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

     # spacing controls pattern pitch so instances never overlap silently
    @property
    def Spacing(self) -> ParameterValue:
        return self.spacing

     # explicit count keeps pattern results predictable across kernels
    @property
    def InstanceCount(self) -> int:
        return self.instance_count

     # direction reference keeps linear patterns aligned with user intent
    @property
    def DirectionSelectionId(self) -> str:
        return self.direction_selection_id

     # orientation flag preserves which side of the topology is used
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

     # sweep angle defines partial revolutions without geometry evaluation
    @property
    def Angle(self) -> ParameterValue:
        return self.angle

     # explicit count keeps pattern results predictable across kernels
    @property
    def InstanceCount(self) -> int:
        return self.instance_count

     # axis reference keeps circular patterns anchored to user picks
    @property
    def AxisSelectionId(self) -> str:
        return self.axis_selection_id

     # orientation flag preserves which side of the topology is used
    @property
    def IsReversed(self) -> bool:
        return self.reversed


# reference planes retain support and offset bindings for editable reconstruction
@MakeDataClass(frozen=True, slots=True)
class RefPlaneFeature(FeatureDef):
    support_plane_id: str
    reference_plane_id: str
    offset: ParameterValue

     # plane anchor locates the sketch in space without embedding transforms
    @property
    def SupportPlaneId(self) -> str:
        return self.support_plane_id

     # reference link keeps datum creation history explicit and replayable
    @property
    def ReferencePlaneId(self) -> str:
        return self.reference_plane_id

     # start offset lets extrudes begin away from the sketch plane
    @property
    def Offset(self) -> ParameterValue:
        return self.offset


# dome features retain their driving height rather than only resulting surfaces
@MakeDataClass(frozen=True, slots=True)
class DomeFeature(FeatureDef):
    height: ParameterValue

     # datum height positions planes without requiring sketch geometry
    @property
    def Height(self) -> ParameterValue:
        return self.height


# body moves retain explicit translations and copy intent across histories
@MakeDataClass(frozen=True, slots=True)
class MoveBodyFeature(FeatureDef):
    translation: SpaceVector
    copy: bool = False

     # translation vector moves datums without rotating their frames
    @property
    def Translation(self) -> SpaceVector:
        return self.translation

     # copy flag separates moved originals from true duplicates
    @property
    def IsCopy(self) -> bool:
        return self.copy


# combine features preserve constructive operation intent between modeling kernels
@MakeDataClass(frozen=True, slots=True)
class CombineFeature(FeatureDef):
    operation: BooleanOp = BooleanOp.KJoin

     # boolean operation names the combine subtract or keep intent explicitly
    @property
    def Operation(self) -> BooleanOp:
        return self.operation


# scale features retain anisotropic factors needed to reconstruct target operations
@MakeDataClass(frozen=True, slots=True)
class ScaleFeature(FeatureDef):
    factors: SpaceVector

     # scale factors keep uniform and anisotropic scaling representable together
    @property
    def Factors(self) -> SpaceVector:
        return self.factors


# native definitions preserve unsupported data without claiming portable semantics
@MakeDataClass(frozen=True, slots=True)
class NativeFeature(FeatureDef):
    format_id: str
    type_id: str
    object_data: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # format id keeps payload interpretation tied to its producing dialect
    @property
    def FormatId(self) -> str:
        return self.format_id

     # type id routes kind specific payloads to correct parsers
    @property
    def TypeId(self) -> str:
        return self.type_id

     # opaque payload keeps vendor detail recoverable beyond typed fields
    @property
    def ObjectData(self) -> TypeMap[str, object]:
        return self.object_data

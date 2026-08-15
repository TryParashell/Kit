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
from typing import ClassVar, TYPE_CHECKING
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
    if TYPE_CHECKING:
        Radius: ClassVar[ParameterValue]
        VariableRadiusParamIds: ClassVar[tuple[str, ...]]


# revolutions preserve axis direction and angular extent rather than only geometry
@MakeDataClass(frozen=True, slots=True)
class RevolveFeature(FeatureDef):
    angle: ParameterValue
    axis_entity_id: str
    reversed: bool = False
    symmetric: bool = False
    if TYPE_CHECKING:
        Angle: ClassVar[ParameterValue]
        AxisEntityId: ClassVar[str]
        IsReversed: ClassVar[bool]
        IsSymmetric: ClassVar[bool]


# holes retain diameter depth and termination so targets create native features
@MakeDataClass(frozen=True, slots=True)
class HoleFeature(FeatureDef):
    diameter: ParameterValue
    depth: ParameterValue
    end_condition: ExtrudeEnd | str = ExtrudeEnd.KBlind
    if TYPE_CHECKING:
        Diameter: ClassVar[ParameterValue]
        Depth: ClassVar[ParameterValue]
        EndCondition: ClassVar[ExtrudeEnd | str]


# chamfers retain alternate measurement modes so targets receive equivalent intent
@MakeDataClass(frozen=True, slots=True)
class ChamferFeature(FeatureDef):
    distance: ParameterValue
    mode: str = "equal_distance"
    second_distance: ParameterValue | None = None
    angle: ParameterValue | None = None
    if TYPE_CHECKING:
        Distance: ClassVar[ParameterValue]
        ValueMode: ClassVar[str]
        SecondDistance: ClassVar[ParameterValue | None]
        Angle: ClassVar[ParameterValue | None]


# shell features retain thickness orientation when topology cannot recover intent
@MakeDataClass(frozen=True, slots=True)
class ShellFeature(FeatureDef):
    thickness: ParameterValue
    outward: bool | None = None
    if TYPE_CHECKING:
        Thickness: ClassVar[ParameterValue]
        IsOutward: ClassVar[bool | None]


# linear patterns preserve editable pitch count and direction bindings
@MakeDataClass(frozen=True, slots=True)
class LinearPattern(FeatureDef):
    spacing: ParameterValue
    instance_count: int
    direction_selection_id: str
    reversed: bool = False
    if TYPE_CHECKING:
        Spacing: ClassVar[ParameterValue]
        InstanceCount: ClassVar[int]
        DirectionSelectionId: ClassVar[str]
        IsReversed: ClassVar[bool]


# circular patterns preserve angular span count and selected axis bindings
@MakeDataClass(frozen=True, slots=True)
class CirclePattern(FeatureDef):
    angle: ParameterValue
    instance_count: int
    axis_selection_id: str
    reversed: bool = False
    if TYPE_CHECKING:
        Angle: ClassVar[ParameterValue]
        InstanceCount: ClassVar[int]
        AxisSelectionId: ClassVar[str]
        IsReversed: ClassVar[bool]


# reference planes retain support and offset bindings for editable reconstruction
@MakeDataClass(frozen=True, slots=True)
class RefPlaneFeature(FeatureDef):
    support_plane_id: str
    reference_plane_id: str
    offset: ParameterValue
    if TYPE_CHECKING:
        SupportPlaneId: ClassVar[str]
        ReferencePlaneId: ClassVar[str]
        Offset: ClassVar[ParameterValue]


# dome features retain their driving height rather than only resulting surfaces
@MakeDataClass(frozen=True, slots=True)
class DomeFeature(FeatureDef):
    height: ParameterValue
    if TYPE_CHECKING:
        Height: ClassVar[ParameterValue]


# body moves retain explicit translations and copy intent across histories
@MakeDataClass(frozen=True, slots=True)
class MoveBodyFeature(FeatureDef):
    translation: SpaceVector
    copy: bool = False
    if TYPE_CHECKING:
        Translation: ClassVar[SpaceVector]
        IsCopy: ClassVar[bool]


# combine features preserve constructive operation intent between modeling kernels
@MakeDataClass(frozen=True, slots=True)
class CombineFeature(FeatureDef):
    operation: BooleanOp = BooleanOp.KJoin
    if TYPE_CHECKING:
        Operation: ClassVar[BooleanOp]


# scale features retain anisotropic factors needed to reconstruct target operations
@MakeDataClass(frozen=True, slots=True)
class ScaleFeature(FeatureDef):
    factors: SpaceVector
    if TYPE_CHECKING:
        Factors: ClassVar[SpaceVector]


# native definitions preserve unsupported data without claiming portable semantics
@MakeDataClass(frozen=True, slots=True)
class NativeFeature(FeatureDef):
    format_id: str
    type_id: str
    object_data: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
    if TYPE_CHECKING:
        FormatId: ClassVar[str]
        TypeId: ClassVar[str]
        ObjectData: ClassVar[TypeMap[str, object]]

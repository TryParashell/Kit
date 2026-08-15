# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass
from types import MappingProxyType
from interchange import (
    BooleanOperation as BoolOperation,
    ConstraintKind as RuleKind,
    ExtrusionEndCondition,
    FeatureKind,
    GeometryKind as GeomKind,
    MateEntityKind,
    MateKind,
    ValueKind,
)

# this binding exists because shared behavior needs one stable value
KAsmObjectTypePrefix = "Assembly::"

# this binding exists because shared behavior needs one stable value
KAsmRootTypeId = "Assembly::AssemblyObject"

# this binding exists because shared behavior needs one stable value
KAsmJointGroupTypeId = "Assembly::JointGroup"

# this binding exists because shared behavior needs one stable value
KAsmLinkTypeId = "Assembly::AssemblyLink"

# this binding exists because shared behavior needs one stable value
KAppLinkTypeId = "App::Link"

# this binding exists because shared behavior needs one stable value
KAppPartTypeId = "App::Part"

# this binding exists because shared behavior needs one stable value
KBodyTypeId = "PartDesign::Body"

# this binding exists because shared behavior needs one stable value
KSketchTypeId = "Sketcher::SketchObject"

# this binding exists because shared behavior needs one stable value
KPartContainerTypeIds = frozenset({"Part::BodyBase", KBodyTypeId})

# this binding exists because shared behavior needs one stable value
KBodyContainerTypeIds = KPartContainerTypeIds | {KAppPartTypeId}

# this binding exists because shared behavior needs one stable value
KNonFeatureObjectTypeIds = KBodyContainerTypeIds | {KSketchTypeId}

# this binding exists because shared behavior needs one stable value
KStringHasherTags = frozenset({"StringHasher", "StringHasher2"})

# this binding exists because shared behavior needs one stable value
KJointGroundProp = "ObjectToGround"

# this binding exists because shared behavior needs one stable value
KJointRefProperties = ("Reference1", "Reference2")

# this binding exists because shared behavior needs one stable value
KJointRefIndexByProp = {
    NameValue: Index for Index, NameValue in enumerate(KJointRefProperties)
}

# this binding exists because shared behavior needs one stable value
KJointTypeProperties = frozenset({"JointType", "MateType"})

# this binding exists because shared behavior needs one stable value
KJointReservedLink = frozenset((KJointGroundProp, *KJointRefProperties))

# this binding exists because shared behavior needs one stable value
KAsmConnectorPropPrefixes = ("Reference", "Placement")

# this binding exists because shared behavior needs one stable value
KXmlTrueValues = frozenset({"1", "true"})

# this binding exists because shared behavior needs one stable value
KPermissiveTrueValues = KXmlTrueValues | {"yes"}

# this binding exists because shared behavior needs one stable value
KSplineControlTags = frozenset({"Pole", "Knot"})

# this binding exists because shared behavior needs one stable value
KFreecadBrepFormatIds = frozenset({"freecad.brep", "opencascade", "opencascade.brep"})

# this binding exists because shared behavior needs one stable value
KFreecadBrepHeader = b"CASCADE Topology V"

# this binding exists because shared behavior needs one stable value
KSubElemMateEntityKinds = (
    MateEntityKind.FACE,
    MateEntityKind.EDGE,
    MateEntityKind.VERTEX,
    MateEntityKind.AXIS,
    MateEntityKind.PLANE,
)

# this binding exists because shared behavior needs one stable value
KSubElemKindByPrefix = {
    KindValue.value.title(): KindValue for KindValue in KSubElemMateEntityKinds
}

# this binding exists because shared behavior needs one stable value
KSupportPlaneTypeIds = frozenset(
    {"App::Plane", "Part::DatumPlane", "PartDesign::Plane"}
)

# this binding groups motion and geometric quantity units by responsibility
KQuantityMotionUnits = {
    "Acceleration": "mm/s^2",
    "Angle": "deg",
    "Area": "mm^2",
    "DissipationRate": "mm^2/s^3",
    "Distance": "mm",
    "Frequency": "1/s",
    "InverseArea": "1/mm^2",
    "InverseLength": "1/mm",
    "InverseVolume": "1/mm^3",
    "KinematicViscosity": "mm^2/s",
    "Length": "mm",
    "SpecificEnergy": "mm^2/s^2",
    "Speed": "mm/s",
    "Time": "s",
    "Velocity": "mm/s",
    "Volume": "mm^3",
    "VolumeFlowRate": "mm^3/s",
}

# this binding groups electrical and magnetic quantity units by responsibility
KQuantityElectricUnits = {
    "CurrentDensity": "A/mm^2",
    "ElectricalCapacitance": "A^2*s^4/(kg*mm^2)",
    "ElectricalConductance": "A^2*s^3/(kg*mm^2)",
    "ElectricalConductivity": "A^2*s^3/(kg*mm^3)",
    "ElectricalInductance": "kg*mm^2/(A^2*s^2)",
    "ElectricalResistance": "kg*mm^2/(A^2*s^3)",
    "ElectricCharge": "A*s",
    "ElectricCurrent": "A",
    "ElectricPotential": "kg*mm^2/(A*s^3)",
    "ElectromagneticPotential": "kg*mm/(A*s^2)",
    "MagneticFieldStrength": "A/mm",
    "MagneticFlux": "kg*mm^2/(A*s^2)",
    "MagneticFluxDensity": "kg/(A*s^2)",
    "Magnetization": "A/mm",
    "SurfaceChargeDensity": "A*s/mm^2",
    "VacuumPermittivity": "A^2*s^4/(kg*mm^3)",
    "VolumeChargeDensity": "A*s/mm^3",
}

# this binding groups mechanical quantity units by responsibility
KQuantityMechanicUnits = {
    "CompressiveStrength": "kg/(mm*s^2)",
    "Density": "kg/mm^3",
    "DynamicViscosity": "kg/(mm*s)",
    "Force": "kg*mm/s^2",
    "Mass": "kg",
    "Moment": "kg*mm^2/s^2",
    "Power": "kg*mm^2/s^3",
    "Pressure": "kg/(mm*s^2)",
    "ShearModulus": "kg/(mm*s^2)",
    "Stiffness": "kg/s^2",
    "StiffnessDensity": "kg/(mm^2*s^2)",
    "Stress": "kg/(mm*s^2)",
    "UltimateTensileStrength": "kg/(mm*s^2)",
    "Work": "kg*mm^2/s^2",
    "YieldStrength": "kg/(mm*s^2)",
    "YoungsModulus": "kg/(mm*s^2)",
}

# this binding groups thermal and remaining base quantity units by responsibility
KQuantityThermalUnits = {
    "AmountOfSubstance": "mol",
    "HeatFlux": "kg/s^3",
    "LuminousIntensity": "cd",
    "SpecificHeat": "mm^2/(s^2*K)",
    "Temperature": "K",
    "ThermalConductivity": "kg*mm/(s^3*K)",
    "ThermalExpansionCoefficient": "1/K",
    "ThermalTransferCoefficient": "kg/(s^3*K)",
    "VolumetricThermalExpansionCoefficient": "1/K",
}

# this binding preserves the complete quantity lookup contract
KQuantityPropUnits = {
    **KQuantityMotionUnits,
    **KQuantityElectricUnits,
    **KQuantityMechanicUnits,
    **KQuantityThermalUnits,
}


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class ScalarPropType:
    locals().setdefault("__annotations__", {})
    __annotations__["type_id"] = "str"
    __annotations__["value_kind"] = "ValueKind"
    __annotations__["unit"] = "str"
    __annotations__["value_tag"] = "str"


# this binding exists because shared behavior needs one stable value
KScalarPropTypes = (
    ScalarPropType("App::PropertyAngle", ValueKind.ANGLE, "deg", "Float"),
    ScalarPropType("App::PropertyBool", ValueKind.BOOLEAN, "", "Bool"),
    ScalarPropType("App::PropertyDistance", ValueKind.LENGTH, "mm", "Float"),
    ScalarPropType("App::PropertyFile", ValueKind.STRING, "", "String"),
    ScalarPropType("App::PropertyFloat", ValueKind.NUMBER, "", "Float"),
    ScalarPropType("App::PropertyFloatConstraint", ValueKind.NUMBER, "", "Float"),
    ScalarPropType("App::PropertyFont", ValueKind.STRING, "", "String"),
    ScalarPropType("App::PropertyInteger", ValueKind.INTEGER, "", "Integer"),
    ScalarPropType("App::PropertyIntegerConstraint", ValueKind.INTEGER, "", "Integer"),
    ScalarPropType("App::PropertyLength", ValueKind.LENGTH, "mm", "Float"),
    ScalarPropType("App::PropertyPath", ValueKind.STRING, "", "Path"),
    ScalarPropType("App::PropertyPercent", ValueKind.QUANTITY, "%", "Integer"),
    ScalarPropType("App::PropertyPersistentObject", ValueKind.STRING, "", "String"),
    ScalarPropType("App::PropertyPrecision", ValueKind.NUMBER, "", "Float"),
    ScalarPropType("App::PropertyQuantity", ValueKind.QUANTITY, "", "Float"),
    ScalarPropType("App::PropertyQuantityConstraint", ValueKind.QUANTITY, "", "Float"),
    ScalarPropType("App::PropertyString", ValueKind.STRING, "", "String"),
    ScalarPropType("App::PropertyUUID", ValueKind.STRING, "", "Uuid"),
)

# this binding exists because shared behavior needs one stable value
KScalarPropKinds = {
    **{
        f"App::Property{NameValue}": (ValueKind.QUANTITY, UnitValue, "Float")
        for NameValue, UnitValue in KQuantityPropUnits.items()
    },
    **{
        Value.type_id: (Value.value_kind, Value.unit, Value.value_tag)
        for Value in KScalarPropTypes
    },
}


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class FeatureType:
    locals().setdefault("__annotations__", {})
    __annotations__["type_id"] = "str"
    __annotations__["kind"] = "FeatureKind"


# this binding groups foundational part workbench feature identities
KPartCoreTypes = (
    FeatureType("Part::Boolean", FeatureKind.BOOLEAN),
    FeatureType("Part::Chamfer", FeatureKind.CHAMFER),
    FeatureType("Part::Common", FeatureKind.BOOLEAN),
    FeatureType("Part::Compound", FeatureKind.BOOLEAN),
    FeatureType("Part::Compound2", FeatureKind.BOOLEAN),
    FeatureType("Part::Cut", FeatureKind.BOOLEAN),
    FeatureType("Part::CurveNet", FeatureKind.SURFACE),
    FeatureType("Part::CustomFeature", FeatureKind.NATIVE),
    FeatureType("Part::CustomFeaturePython", FeatureKind.NATIVE),
    FeatureType("Part::Datum", FeatureKind.REFERENCE),
    FeatureType("Part::DatumLine", FeatureKind.REFERENCE),
    FeatureType("Part::DatumPoint", FeatureKind.REFERENCE),
    FeatureType("Part::Extrusion", FeatureKind.EXTRUSION),
    FeatureType("Part::Face", FeatureKind.SURFACE),
    FeatureType("Part::Feature", FeatureKind.NATIVE),
    FeatureType("Part::FeatureExt", FeatureKind.NATIVE),
    FeatureType("Part::FeatureGeometrySet", FeatureKind.REFERENCE),
    FeatureType("Part::FeaturePython", FeatureKind.NATIVE),
    FeatureType("Part::FeatureReference", FeatureKind.REFERENCE),
    FeatureType("Part::Fillet", FeatureKind.FILLET),
    FeatureType("Part::FilletBase", FeatureKind.FILLET),
    FeatureType("Part::Fuse", FeatureKind.BOOLEAN),
    FeatureType("Part::Helix", FeatureKind.HELIX),
    FeatureType("Part::ImportBrep", FeatureKind.IMPORTED),
    FeatureType("Part::ImportIges", FeatureKind.IMPORTED),
    FeatureType("Part::ImportStep", FeatureKind.IMPORTED),
)

# this binding groups advanced part workbench feature identities
KPartShapeTypes = (
    FeatureType("Part::LocalCoordinateSystem", FeatureKind.REFERENCE),
    FeatureType("Part::Loft", FeatureKind.LOFT),
    FeatureType("Part::Mirroring", FeatureKind.MIRROR),
    FeatureType("Part::MultiCommon", FeatureKind.BOOLEAN),
    FeatureType("Part::MultiFuse", FeatureKind.BOOLEAN),
    FeatureType("Part::Offset", FeatureKind.OFFSET),
    FeatureType("Part::Offset2D", FeatureKind.OFFSET),
    FeatureType("Part::Part2DObject", FeatureKind.REFERENCE),
    FeatureType("Part::Part2DObjectPython", FeatureKind.REFERENCE),
    FeatureType("Part::Polygon", FeatureKind.NATIVE),
    FeatureType("Part::Primitive", FeatureKind.NATIVE),
    FeatureType("Part::ProjectOnSurface", FeatureKind.SURFACE),
    FeatureType("Part::Refine", FeatureKind.REFINE),
    FeatureType("Part::Revolution", FeatureKind.REVOLUTION),
    FeatureType("Part::RuledSurface", FeatureKind.SURFACE),
    FeatureType("Part::Reverse", FeatureKind.REVERSE),
    FeatureType("Part::Scale", FeatureKind.SCALE),
    FeatureType("Part::Section", FeatureKind.BOOLEAN),
    FeatureType("Part::Sweep", FeatureKind.SWEEP),
    FeatureType("Part::Spline", FeatureKind.NATIVE),
    FeatureType("Part::Thickness", FeatureKind.SHELL),
)

# this binding groups additive and foundational design feature identities
KDesignCoreTypes = (
    FeatureType("PartDesign::AdditiveHelix", FeatureKind.HELIX),
    FeatureType("PartDesign::AdditiveLoft", FeatureKind.LOFT),
    FeatureType("PartDesign::AdditivePipe", FeatureKind.SWEEP),
    FeatureType("PartDesign::Boolean", FeatureKind.BOOLEAN),
    FeatureType("PartDesign::Chamfer", FeatureKind.CHAMFER),
    FeatureType("PartDesign::CoordinateSystem", FeatureKind.REFERENCE),
    FeatureType("PartDesign::Draft", FeatureKind.DRAFT),
    FeatureType("PartDesign::DressUp", FeatureKind.NATIVE),
    FeatureType("PartDesign::Feature", FeatureKind.NATIVE),
    FeatureType("PartDesign::FeatureAdditivePython", FeatureKind.NATIVE),
    FeatureType("PartDesign::FeatureAddSub", FeatureKind.NATIVE),
    FeatureType("PartDesign::FeatureAddSubPython", FeatureKind.NATIVE),
    FeatureType("PartDesign::FeatureBase", FeatureKind.REFERENCE),
    FeatureType("PartDesign::FeatureExtrude", FeatureKind.EXTRUSION),
    FeatureType("PartDesign::FeaturePrimitive", FeatureKind.NATIVE),
    FeatureType("PartDesign::FeaturePython", FeatureKind.NATIVE),
    FeatureType("PartDesign::FeatureRefine", FeatureKind.REFINE),
    FeatureType("PartDesign::FeatureRefinePython", FeatureKind.REFINE),
    FeatureType("PartDesign::FeatureSubtractivePython", FeatureKind.NATIVE),
    FeatureType("PartDesign::Fillet", FeatureKind.FILLET),
    FeatureType("PartDesign::Groove", FeatureKind.REVOLUTION),
    FeatureType("PartDesign::Helix", FeatureKind.HELIX),
    FeatureType("PartDesign::Hole", FeatureKind.HOLE),
)

# this binding groups patterned and profile based design feature identities
KDesignProfileTypes = (
    FeatureType("PartDesign::Line", FeatureKind.REFERENCE),
    FeatureType("PartDesign::LinearPattern", FeatureKind.PATTERN),
    FeatureType("PartDesign::Loft", FeatureKind.LOFT),
    FeatureType("PartDesign::Mirrored", FeatureKind.MIRROR),
    FeatureType("PartDesign::MultiTransform", FeatureKind.PATTERN),
    FeatureType("PartDesign::Pad", FeatureKind.EXTRUSION),
    FeatureType("PartDesign::Pocket", FeatureKind.EXTRUSION),
    FeatureType("PartDesign::Point", FeatureKind.REFERENCE),
    FeatureType("PartDesign::PolarPattern", FeatureKind.PATTERN),
    FeatureType("PartDesign::Pipe", FeatureKind.SWEEP),
    FeatureType("PartDesign::ProfileBased", FeatureKind.NATIVE),
    FeatureType("PartDesign::Revolution", FeatureKind.REVOLUTION),
    FeatureType("PartDesign::Revolved", FeatureKind.REVOLUTION),
    FeatureType("PartDesign::Scaled", FeatureKind.SCALE),
)

# this binding groups binder and subtractive design feature identities
KDesignBinderTypes = (
    FeatureType("PartDesign::ShapeBinder", FeatureKind.REFERENCE),
    FeatureType("PartDesign::Solid", FeatureKind.NATIVE),
    FeatureType("PartDesign::SubShapeBinder", FeatureKind.REFERENCE),
    FeatureType("PartDesign::SubShapeBinderPython", FeatureKind.REFERENCE),
    FeatureType("PartDesign::SubtractiveHelix", FeatureKind.HELIX),
    FeatureType("PartDesign::SubtractiveLoft", FeatureKind.LOFT),
    FeatureType("PartDesign::SubtractivePipe", FeatureKind.SWEEP),
    FeatureType("PartDesign::Thickness", FeatureKind.SHELL),
    FeatureType("PartDesign::Transformed", FeatureKind.PATTERN),
)

# this binding preserves the complete ordered feature type contract
KFeatureTypes = (
    *KPartCoreTypes,
    *KPartShapeTypes,
    *KDesignCoreTypes,
    *KDesignProfileTypes,
    *KDesignBinderTypes,
)

# this binding exists because shared behavior needs one stable value
KFeatureKindByTypeId = {Value.type_id: Value.kind for Value in KFeatureTypes}


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class BoolOperationA:
    locals().setdefault("__annotations__", {})
    __annotations__["operation"] = "BoolOperation"
    __annotations__["type_id"] = "str"
    __annotations__["label"] = "str"
    __annotations__["input_mode"] = "str"


# this binding exists because shared behavior needs one stable value
KBoolOperationTypes = (
    BoolOperationA(BoolOperation.CREATE, "Part::Extrusion", "Extrusion", "standalone"),
    BoolOperationA(BoolOperation.JOIN, "Part::MultiFuse", "Fuse", "shapes"),
    BoolOperationA(BoolOperation.CUT, "Part::Cut", "Cut", "base_tool"),
    BoolOperationA(BoolOperation.INTERSECT, "Part::Common", "Common", "base_tool"),
)

# this binding exists because shared behavior needs one stable value
KBoolOperationTypeByKind = {
    Value.operation.value: Value for Value in KBoolOperationTypes
}

# this binding exists because shared behavior needs one stable value
KCreateOperationNames = frozenset({"", BoolOperation.CREATE.value})

# this binding exists because shared behavior needs one stable value
KFeatureWriteTypeIds = MappingProxyType(
    {
        FeatureKind.EXTRUSION: frozenset(
            (Value.type_id for Value in KBoolOperationTypes)
        ),
        FeatureKind.REVOLUTION: frozenset(),
        FeatureKind.SWEEP: frozenset(),
        FeatureKind.LOFT: frozenset(),
        FeatureKind.HOLE: frozenset(),
        FeatureKind.HELIX: frozenset(),
        FeatureKind.FILLET: frozenset({"Part::Fillet"}),
        FeatureKind.CHAMFER: frozenset(),
        FeatureKind.SHELL: frozenset(),
        FeatureKind.DRAFT: frozenset(),
        FeatureKind.PATTERN: frozenset(),
        FeatureKind.MIRROR: frozenset(),
        FeatureKind.SCALE: frozenset(),
        FeatureKind.OFFSET: frozenset(),
        FeatureKind.PRIMITIVE: frozenset(),
        FeatureKind.SURFACE: frozenset(),
        FeatureKind.REFINE: frozenset(),
        FeatureKind.REVERSE: frozenset(),
        FeatureKind.BOOLEAN: frozenset(),
        FeatureKind.IMPORTED: frozenset({"Part::Feature"}),
        FeatureKind.REFERENCE: frozenset(),
        FeatureKind.NATIVE: frozenset(),
    }
)
if KFeatureWriteTypeIds.keys() != set(FeatureKind):
    raise RuntimeError("FreeCAD feature write types are not exhaustive")

# this binding exists because shared behavior needs one stable value
KFeatureWriteKinds = frozenset(
    (KindValue for KindValue, TypeIds in KFeatureWriteTypeIds.items() if TypeIds)
)

# this binding exists because shared behavior needs one stable value
KFeatureCarrierKinds = frozenset(FeatureKind) - KFeatureWriteKinds


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class ExtrusionType:
    locals().setdefault("__annotations__", {})
    __annotations__["code"] = "int"
    __annotations__["end_condition"] = "ExtrusionEndCondition"
    __annotations__["pocket_end_condition"] = "ExtrusionEndCondition | None"
    locals()["pocket_end_condition"] = None


# this binding exists because shared behavior needs one stable value
KExtrusionTypes = (
    ExtrusionType(0, ExtrusionEndCondition.BLIND),
    ExtrusionType(
        1, ExtrusionEndCondition.UP_TO_LAST, ExtrusionEndCondition.THROUGH_ALL
    ),
    ExtrusionType(2, ExtrusionEndCondition.UP_TO_FIRST),
    ExtrusionType(3, ExtrusionEndCondition.UP_TO_FACE),
    ExtrusionType(4, ExtrusionEndCondition.TWO_LENGTHS),
    ExtrusionType(5, ExtrusionEndCondition.UP_TO_SHAPE),
)

# this binding exists because shared behavior needs one stable value
KExtrusionTypeByCode = {Value.code: Value for Value in KExtrusionTypes}

# this binding exists because shared behavior needs one stable value
KPocketTypeId = "PartDesign::Pocket"


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class PrimitiveFamily:
    locals().setdefault("__annotations__", {})
    __annotations__["namespace"] = "str"
    __annotations__["prefixes"] = "tuple[str, ...]"
    __annotations__["shapes"] = "tuple[str, ...]"


# this binding exists because shared behavior needs one stable value
KPrimitiveFeatureFamilies = (
    PrimitiveFamily(
        "Part",
        ("",),
        (
            "Box",
            "Circle",
            "Cone",
            "Cylinder",
            "Ellipse",
            "Ellipsoid",
            "Line",
            "Plane",
            "Prism",
            "RegularPolygon",
            "Sphere",
            "Spiral",
            "Torus",
            "Vertex",
            "Wedge",
        ),
    ),
    PrimitiveFamily(
        "PartDesign",
        ("", "Additive", "Subtractive"),
        ("Box", "Cone", "Cylinder", "Ellipsoid", "Prism", "Sphere", "Torus", "Wedge"),
    ),
)

# this binding exists because shared behavior needs one stable value
KPrimitiveFeatureTypeIds = frozenset(
    (
        f"{Family.namespace}::{Prefix}{Shape}"
        for Family in KPrimitiveFeatureFamilies
        for Prefix in Family.prefixes
        for Shape in Family.shapes
    )
)

# this binding exists because shared behavior needs one stable value
KPartObjectTypeIds = frozenset(
    (
        *KFeatureKindByTypeId,
        *KPrimitiveFeatureTypeIds,
        *KSupportPlaneTypeIds,
        *KBodyContainerTypeIds,
    )
)

# this binding exists because shared behavior needs one stable value
KAdditionalPartObjectType = frozenset({"App::Plane", "Part::FeatureGeometrySet"})

# this binding exists because shared behavior needs one stable value
KRegisteredPartObjectType = KPartObjectTypeIds - KAdditionalPartObjectType


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RulePoint:
    locals().setdefault("__annotations__", {})
    __annotations__["index"] = "int"
    __annotations__["name"] = "str"
    __annotations__["aliases"] = "tuple[str, ...]"
    locals()["aliases"] = ()


# this binding exists because shared behavior needs one stable value
KRulePoints = (
    RulePoint(1, "start", ("startpoint",)),
    RulePoint(2, "end", ("endpoint",)),
    RulePoint(3, "center", ("centre", "midpoint")),
)

# this binding exists because shared behavior needs one stable value
KRulePointByIndex = {Value.index: Value.name for Value in KRulePoints}

# this binding exists because shared behavior needs one stable value
KRulePointIndexByName = {
    NameValue: Value.index
    for Value in KRulePoints
    for NameValue in (Value.name, *Value.aliases)
}

# this binding exists because shared behavior needs one stable value
KMidpointRefPointNames = frozenset(
    (
        "",
        "mid",
        *(
            NameValue
            for Value in KRulePoints
            if Value.index == 3
            for NameValue in (Value.name, *Value.aliases)
        ),
    )
)


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RuleType:
    locals().setdefault("__annotations__", {})
    __annotations__["code"] = "int"
    __annotations__["kind"] = "RuleKind"
    __annotations__["value_kind"] = "ValueKind | None"
    locals()["value_kind"] = None
    __annotations__["unit"] = "str"
    locals()["unit"] = ""
    __annotations__["write_kinds"] = "tuple[RuleKind, ...]"
    locals()["write_kinds"] = ()


# this binding exists because shared behavior needs one stable value
KRuleTypes = (
    RuleType(1, RuleKind.COINCIDENT, write_kinds=(RuleKind.CONCENTRIC,)),
    RuleType(2, RuleKind.HORIZONTAL),
    RuleType(3, RuleKind.VERTICAL),
    RuleType(4, RuleKind.PARALLEL),
    RuleType(5, RuleKind.TANGENT),
    RuleType(6, RuleKind.DISTANCE, ValueKind.LENGTH, "mm"),
    RuleType(7, RuleKind.DISTANCE_X, ValueKind.LENGTH, "mm"),
    RuleType(8, RuleKind.DISTANCE_Y, ValueKind.LENGTH, "mm"),
    RuleType(9, RuleKind.ANGLE, ValueKind.ANGLE, "rad"),
    RuleType(10, RuleKind.PERPENDICULAR),
    RuleType(11, RuleKind.RADIUS, ValueKind.LENGTH, "mm"),
    RuleType(12, RuleKind.EQUAL),
    RuleType(13, RuleKind.POINT_ON_OBJECT),
    RuleType(14, RuleKind.SYMMETRIC),
    RuleType(15, RuleKind.INTERNAL_ALIGNMENT),
    RuleType(16, RuleKind.SNELLS_LAW, ValueKind.NUMBER),
    RuleType(17, RuleKind.BLOCK, write_kinds=(RuleKind.FIXED,)),
    RuleType(18, RuleKind.DIAMETER, ValueKind.LENGTH, "mm"),
    RuleType(19, RuleKind.WEIGHT, ValueKind.NUMBER),
    RuleType(20, RuleKind.GROUP),
    RuleType(21, RuleKind.TEXT),
)

# this binding exists because shared behavior needs one stable value
KRuleKindByCode = {Value.code: Value.kind for Value in KRuleTypes}

# this binding exists because shared behavior needs one stable value
KRuleValueKindByCode = {
    Value.code: (Value.value_kind, Value.unit)
    for Value in KRuleTypes
    if Value.value_kind is not None
}

# this binding exists because shared behavior needs one stable value
KRuleCodeByKind = {
    KindValue.value: Value.code
    for Value in KRuleTypes
    for KindValue in (Value.kind, *Value.write_kinds)
}

# this binding exists because shared behavior needs one stable value
KRuleWriteCodes = MappingProxyType(
    {
        RuleKind.COINCIDENT: frozenset({1}),
        RuleKind.HORIZONTAL: frozenset({2}),
        RuleKind.VERTICAL: frozenset({3}),
        RuleKind.PARALLEL: frozenset({4}),
        RuleKind.PERPENDICULAR: frozenset({10}),
        RuleKind.TANGENT: frozenset({5}),
        RuleKind.EQUAL: frozenset({12}),
        RuleKind.CONCENTRIC: frozenset({1}),
        RuleKind.POINT_ON_OBJECT: frozenset({13}),
        RuleKind.SYMMETRIC: frozenset({14}),
        RuleKind.MIDPOINT: frozenset({14}),
        RuleKind.DISTANCE: frozenset({6}),
        RuleKind.DISTANCE_X: frozenset({7}),
        RuleKind.DISTANCE_Y: frozenset({8}),
        RuleKind.ANGLE: frozenset({9}),
        RuleKind.RADIUS: frozenset({11}),
        RuleKind.DIAMETER: frozenset({18}),
        RuleKind.FIXED: frozenset({17}),
        RuleKind.INTERNAL_ALIGNMENT: frozenset({15}),
        RuleKind.SNELLS_LAW: frozenset({16}),
        RuleKind.BLOCK: frozenset({17}),
        RuleKind.WEIGHT: frozenset({19}),
        RuleKind.GROUP: frozenset({20}),
        RuleKind.TEXT: frozenset({21}),
        RuleKind.NATIVE: frozenset(),
    }
)
if KRuleWriteCodes.keys() != set(RuleKind):
    raise RuntimeError("FreeCAD constraint write codes are not exhaustive")

# this binding exists because shared behavior needs one stable value
KRuleComposedKinds = frozenset({RuleKind.CONCENTRIC, RuleKind.FIXED, RuleKind.MIDPOINT})

# this binding exists because shared behavior needs one stable value
KRuleWriteKinds = frozenset(
    (KindValue for KindValue, Codes in KRuleWriteCodes.items() if Codes)
)

# this binding exists because shared behavior needs one stable value
KRuleDirectKinds = KRuleWriteKinds - KRuleComposedKinds

# this binding exists because shared behavior needs one stable value
KRuleCarrierKinds = frozenset(RuleKind) - KRuleWriteKinds

# this binding exists because shared behavior needs one stable value
KFixedRuleKinds = frozenset(
    (
        KindValue
        for KindValue, CodeValue in KRuleCodeByKind.items()
        if CodeValue == KRuleCodeByKind[RuleKind.BLOCK.value]
    )
)

# this binding exists because shared behavior needs one stable value
KDimensionalRuleCodes = frozenset(KRuleValueKindByCode)


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class GeomType:
    locals().setdefault("__annotations__", {})
    __annotations__["type_id"] = "str"
    __annotations__["kind"] = "GeomKind"
    __annotations__["neutral_type"] = "str"
    locals()["neutral_type"] = ""
    __annotations__["neutral_default"] = "bool"
    locals()["neutral_default"] = False


# this binding exists because shared behavior needs one stable value
KGeomTypes = (
    GeomType("Part::GeomPoint", GeomKind.POINT, "PointGeometry", True),
    GeomType("Part::GeomLine", GeomKind.LINE),
    GeomType("Part::GeomLineSegment", GeomKind.LINE, "LineGeometry", True),
    GeomType("Part::GeomCircle", GeomKind.CIRCLE, "CircleGeometry", True),
    GeomType("Part::GeomArcOfCircle", GeomKind.ARC, "ArcGeometry", True),
    GeomType("Part::GeomEllipse", GeomKind.ELLIPSE, "EllipseGeometry", True),
    GeomType(
        "Part::GeomArcOfEllipse", GeomKind.ARC_ELLIPSE, "ArcEllipseGeometry", True
    ),
    GeomType("Part::GeomHyperbola", GeomKind.HYPERBOLA, "HyperbolaGeometry"),
    GeomType(
        "Part::GeomArcOfHyperbola", GeomKind.ARC_HYPERBOLA, "ArcHyperbolaGeometry", True
    ),
    GeomType("Part::GeomParabola", GeomKind.PARABOLA, "ParabolaGeometry"),
    GeomType(
        "Part::GeomArcOfParabola", GeomKind.ARC_PARABOLA, "ArcParabolaGeometry", True
    ),
    GeomType("Part::GeomBezierCurve", GeomKind.BEZIER, "SplineGeometry", True),
    GeomType("Part::GeomBSplineCurve", GeomKind.SPLINE, "SplineGeometry", True),
    GeomType("Part::GeomOffsetCurve", GeomKind.OFFSET),
    GeomType("Part::GeomTrimmedCurve", GeomKind.TRIMMED),
)

# this binding exists because shared behavior needs one stable value
KGeomKindByTypeId = {Value.type_id: Value.kind for Value in KGeomTypes}

# this binding exists because shared behavior needs one stable value
KGeomTypeIdsByKind = {
    KindValue.value: frozenset(
        (Value.type_id for Value in KGeomTypes if Value.kind == KindValue)
    )
    for KindValue in GeomKind
    if KindValue != GeomKind.NATIVE
}

# this binding exists because shared behavior needs one stable value
KNeutralGeomTypeByKind = {
    Value.kind.value: Value.neutral_type
    for Value in KGeomTypes
    if Value.neutral_default
}

# this binding exists because shared behavior needs one stable value
KNeutralGeomTypeIdByKind = {
    Value.kind.value: Value.type_id for Value in KGeomTypes if Value.neutral_default
}

# this binding exists because shared behavior needs one stable value
KGeomWriteTypeIds = MappingProxyType(
    {
        GeomKind.POINT: frozenset({"Part::GeomPoint"}),
        GeomKind.LINE: frozenset({"Part::GeomLineSegment"}),
        GeomKind.CIRCLE: frozenset({"Part::GeomCircle"}),
        GeomKind.ARC: frozenset({"Part::GeomArcOfCircle"}),
        GeomKind.ELLIPSE: frozenset({"Part::GeomEllipse"}),
        GeomKind.ARC_ELLIPSE: frozenset({"Part::GeomArcOfEllipse"}),
        GeomKind.HYPERBOLA: frozenset(),
        GeomKind.ARC_HYPERBOLA: frozenset({"Part::GeomArcOfHyperbola"}),
        GeomKind.PARABOLA: frozenset(),
        GeomKind.ARC_PARABOLA: frozenset({"Part::GeomArcOfParabola"}),
        GeomKind.BEZIER: frozenset({"Part::GeomBezierCurve"}),
        GeomKind.SPLINE: frozenset({"Part::GeomBSplineCurve"}),
        GeomKind.OFFSET: frozenset(),
        GeomKind.TRIMMED: frozenset(),
        GeomKind.NATIVE: frozenset(),
    }
)
if KGeomWriteTypeIds.keys() != set(GeomKind):
    raise RuntimeError("FreeCAD geometry write types are not exhaustive")

# this binding exists because shared behavior needs one stable value
KGeomWriteKinds = frozenset(
    (KindValue for KindValue, TypeIds in KGeomWriteTypeIds.items() if TypeIds)
)

# this binding exists because shared behavior needs one stable value
KGeomCarrierKinds = frozenset(GeomKind) - KGeomWriteKinds

# this binding exists because shared behavior needs one stable value
KCircularGeomKinds = frozenset({GeomKind.CIRCLE.value, GeomKind.ARC.value})

# this binding exists because shared behavior needs one stable value
KSplineGeomKinds = frozenset({GeomKind.BEZIER.value, GeomKind.SPLINE.value})

# this binding exists because shared behavior needs one stable value
KSplineGeomTypeIds = frozenset(
    (Value.type_id for Value in KGeomTypes if Value.kind.value in KSplineGeomKinds)
)


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class JointType:
    locals().setdefault("__annotations__", {})
    __annotations__["name"] = "str"
    __annotations__["kind"] = "MateKind"
    __annotations__["write_kinds"] = "tuple[MateKind, ...]"
    locals()["write_kinds"] = ()
    __annotations__["write_aliases"] = "tuple[str, ...]"
    locals()["write_aliases"] = ()
    __annotations__["uses_distance"] = "bool"
    locals()["uses_distance"] = False
    __annotations__["uses_second_distance"] = "bool"
    locals()["uses_second_distance"] = False


# this binding exists because shared behavior needs one stable value
KJointTypeDefinitions = (
    JointType("Fixed", MateKind.LOCK, write_aliases=("fixed",)),
    JointType("Revolute", MateKind.HINGE, write_aliases=("revolute",)),
    JointType("Cylindrical", MateKind.CONCENTRIC, write_aliases=("cylindrical",)),
    JointType("Slider", MateKind.SLIDER),
    JointType("Ball", MateKind.BALL),
    JointType("Distance", MateKind.DISTANCE, uses_distance=True),
    JointType("Parallel", MateKind.PARALLEL),
    JointType("Perpendicular", MateKind.PERPENDICULAR),
    JointType("Angle", MateKind.ANGLE),
    JointType(
        "RackPinion",
        MateKind.RACK_PINION,
        write_aliases=("rackpinion",),
        uses_distance=True,
    ),
    JointType("Screw", MateKind.SCREW, uses_distance=True),
    JointType(
        "Gears",
        MateKind.GEAR,
        write_aliases=("gears",),
        uses_distance=True,
        uses_second_distance=True,
    ),
    JointType("Belt", MateKind.BELT, uses_distance=True, uses_second_distance=True),
)

# this binding exists because shared behavior needs one stable value
KMateKindByJointType = {Value.name: Value.kind for Value in KJointTypeDefinitions}

# this binding exists because shared behavior needs one stable value
KJointTypeByMateKind = {
    KeyValue: Value.name
    for Value in KJointTypeDefinitions
    for KeyValue in (
        Value.kind.value,
        *(KindValue.value for KindValue in Value.write_kinds),
        *Value.write_aliases,
    )
}

# this binding exists because shared behavior needs one stable value
KMateWriteTypes = MappingProxyType(
    {
        MateKind.COINCIDENT: frozenset(),
        MateKind.CONCENTRIC: frozenset({"Cylindrical"}),
        MateKind.PARALLEL: frozenset({"Parallel"}),
        MateKind.PERPENDICULAR: frozenset({"Perpendicular"}),
        MateKind.TANGENT: frozenset(),
        MateKind.DISTANCE: frozenset({"Distance"}),
        MateKind.ANGLE: frozenset({"Angle"}),
        MateKind.LOCK: frozenset({"Fixed"}),
        MateKind.GEAR: frozenset({"Gears"}),
        MateKind.RACK_PINION: frozenset({"RackPinion"}),
        MateKind.SCREW: frozenset({"Screw"}),
        MateKind.COORDINATE: frozenset(),
        MateKind.SLIDER: frozenset({"Slider"}),
        MateKind.UNIVERSAL_JOINT: frozenset(),
        MateKind.CAM: frozenset(),
        MateKind.SLOT: frozenset(),
        MateKind.BALL: frozenset({"Ball"}),
        MateKind.WIDTH: frozenset(),
        MateKind.SYMMETRIC: frozenset(),
        MateKind.LINEAR_COUPLER: frozenset(),
        MateKind.BELT: frozenset({"Belt"}),
        MateKind.PATH: frozenset(),
        MateKind.MAGNETIC: frozenset(),
        MateKind.HINGE: frozenset({"Revolute"}),
        MateKind.PROFILE_CENTER: frozenset(),
        MateKind.NATIVE: frozenset(),
    }
)
if KMateWriteTypes.keys() != set(MateKind):
    raise RuntimeError("FreeCAD mate write types are not exhaustive")

# this binding exists because shared behavior needs one stable value
KMateWriteKinds = frozenset(
    (KindValue for KindValue, Types in KMateWriteTypes.items() if Types)
)

# this binding exists because shared behavior needs one stable value
KMateCarrierKinds = frozenset(MateKind) - KMateWriteKinds

# this binding exists because shared behavior needs one stable value
KJointTypes = tuple((Value.name for Value in KJointTypeDefinitions))

# this binding exists because shared behavior needs one stable value
KJointTypesUsingDistance = frozenset(
    (Value.name for Value in KJointTypeDefinitions if Value.uses_distance)
)

# this binding exists because shared behavior needs one stable value
KJointTypesUsingSecond = frozenset(
    (Value.name for Value in KJointTypeDefinitions if Value.uses_second_distance)
)

# this binding exists because shared behavior needs one stable value
KMateKindsUsingDistance = frozenset(
    (Value.kind for Value in KJointTypeDefinitions if Value.uses_distance)
)

# this binding exists because shared behavior needs one stable value
KMateKindsUsingSecond = frozenset(
    (Value.kind for Value in KJointTypeDefinitions if Value.uses_second_distance)
)

# this binding exists because shared behavior needs one stable value
globals()["ADDITIONAL_PART_OBJECT_TYPE_IDS"] = KAdditionalPartObjectType

# this binding exists because shared behavior needs one stable value
globals()["APP_LINK_TYPE_ID"] = KAppLinkTypeId

# this binding exists because shared behavior needs one stable value
globals()["APP_PART_TYPE_ID"] = KAppPartTypeId

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_CONNECTOR_PROPERTY_PREFIXES"] = KAsmConnectorPropPrefixes

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_JOINT_GROUP_TYPE_ID"] = KAsmJointGroupTypeId

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_LINK_TYPE_ID"] = KAsmLinkTypeId

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_OBJECT_TYPE_PREFIX"] = KAsmObjectTypePrefix

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_ROOT_TYPE_ID"] = KAsmRootTypeId

# this binding exists because shared behavior needs one stable value
globals()["BODY_CONTAINER_TYPE_IDS"] = KBodyContainerTypeIds

# this binding exists because shared behavior needs one stable value
globals()["BODY_TYPE_ID"] = KBodyTypeId

# this binding exists because shared behavior needs one stable value
globals()["BOOLEAN_OPERATION_TYPES"] = KBoolOperationTypes

# this binding exists because shared behavior needs one stable value
globals()["BOOLEAN_OPERATION_TYPE_BY_KIND"] = KBoolOperationTypeByKind

# this binding exists because shared behavior needs one stable value
globals()["BooleanOperation"] = BoolOperation

# this binding exists because shared behavior needs one stable value
globals()["BooleanOperationType"] = BoolOperationA

# this binding exists because shared behavior needs one stable value
globals()["CIRCULAR_GEOMETRY_KINDS"] = KCircularGeomKinds

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_CARRIER_KINDS"] = KRuleCarrierKinds

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_CODE_BY_KIND"] = KRuleCodeByKind

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_COMPOSED_KINDS"] = KRuleComposedKinds

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_DIRECT_KINDS"] = KRuleDirectKinds

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_KIND_BY_CODE"] = KRuleKindByCode

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_POINTS"] = KRulePoints

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_POINT_BY_INDEX"] = KRulePointByIndex

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_POINT_INDEX_BY_NAME"] = KRulePointIndexByName

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_TYPES"] = KRuleTypes

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_VALUE_KIND_BY_CODE"] = KRuleValueKindByCode

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_WRITE_CODES"] = KRuleWriteCodes

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_WRITE_KINDS"] = KRuleWriteKinds

# this binding exists because shared behavior needs one stable value
globals()["CREATE_OPERATION_NAMES"] = KCreateOperationNames

# this binding exists because shared behavior needs one stable value
globals()["ConstraintKind"] = RuleKind

# this binding exists because shared behavior needs one stable value
globals()["ConstraintPoint"] = RulePoint

# this binding exists because shared behavior needs one stable value
globals()["ConstraintType"] = RuleType

# this binding exists because shared behavior needs one stable value
globals()["DIMENSIONAL_CONSTRAINT_CODES"] = KDimensionalRuleCodes

# this binding exists because shared behavior needs one stable value
globals()["EXTRUSION_TYPES"] = KExtrusionTypes

# this binding exists because shared behavior needs one stable value
globals()["EXTRUSION_TYPE_BY_CODE"] = KExtrusionTypeByCode

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_CARRIER_KINDS"] = KFeatureCarrierKinds

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_KIND_BY_TYPE_ID"] = KFeatureKindByTypeId

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_TYPES"] = KFeatureTypes

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_WRITE_KINDS"] = KFeatureWriteKinds

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_WRITE_TYPE_IDS"] = KFeatureWriteTypeIds

# this binding exists because shared behavior needs one stable value
globals()["FIXED_CONSTRAINT_KINDS"] = KFixedRuleKinds

# this binding exists because shared behavior needs one stable value
globals()["FREECAD_BREP_FORMAT_IDS"] = KFreecadBrepFormatIds

# this binding exists because shared behavior needs one stable value
globals()["FREECAD_BREP_HEADER"] = KFreecadBrepHeader

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_CARRIER_KINDS"] = KGeomCarrierKinds

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_KIND_BY_TYPE_ID"] = KGeomKindByTypeId

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_TYPES"] = KGeomTypes

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_TYPE_IDS_BY_KIND"] = KGeomTypeIdsByKind

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_WRITE_KINDS"] = KGeomWriteKinds

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_WRITE_TYPE_IDS"] = KGeomWriteTypeIds

# this binding exists because shared behavior needs one stable value
globals()["GeometryKind"] = GeomKind

# this binding exists because shared behavior needs one stable value
globals()["GeometryType"] = GeomType

# this binding exists because shared behavior needs one stable value
globals()["JOINT_GROUND_PROPERTY"] = KJointGroundProp

# this binding exists because shared behavior needs one stable value
globals()["JOINT_REFERENCE_INDEX_BY_PROPERTY"] = KJointRefIndexByProp

# this binding exists because shared behavior needs one stable value
globals()["JOINT_REFERENCE_PROPERTIES"] = KJointRefProperties

# this binding exists because shared behavior needs one stable value
globals()["JOINT_RESERVED_LINK_PROPERTIES"] = KJointReservedLink

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPES"] = KJointTypes

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPES_USING_DISTANCE"] = KJointTypesUsingDistance

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPES_USING_SECOND_DISTANCE"] = KJointTypesUsingSecond

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPE_BY_MATE_KIND"] = KJointTypeByMateKind

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPE_DEFINITIONS"] = KJointTypeDefinitions

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPE_PROPERTIES"] = KJointTypeProperties

# this binding exists because shared behavior needs one stable value
globals()["MATE_CARRIER_KINDS"] = KMateCarrierKinds

# this binding exists because shared behavior needs one stable value
globals()["MATE_KINDS_USING_DISTANCE"] = KMateKindsUsingDistance

# this binding exists because shared behavior needs one stable value
globals()["MATE_KINDS_USING_SECOND_DISTANCE"] = KMateKindsUsingSecond

# this binding exists because shared behavior needs one stable value
globals()["MATE_KIND_BY_JOINT_TYPE"] = KMateKindByJointType

# this binding exists because shared behavior needs one stable value
globals()["MATE_WRITE_KINDS"] = KMateWriteKinds

# this binding exists because shared behavior needs one stable value
globals()["MATE_WRITE_TYPES"] = KMateWriteTypes

# this binding exists because shared behavior needs one stable value
globals()["MIDPOINT_REFERENCE_POINT_NAMES"] = KMidpointRefPointNames

# this binding exists because shared behavior needs one stable value
globals()["NEUTRAL_GEOMETRY_TYPE_BY_KIND"] = KNeutralGeomTypeByKind

# this binding exists because shared behavior needs one stable value
globals()["NEUTRAL_GEOMETRY_TYPE_ID_BY_KIND"] = KNeutralGeomTypeIdByKind

# this binding exists because shared behavior needs one stable value
globals()["NON_FEATURE_OBJECT_TYPE_IDS"] = KNonFeatureObjectTypeIds

# this binding exists because shared behavior needs one stable value
globals()["PART_CONTAINER_TYPE_IDS"] = KPartContainerTypeIds

# this binding exists because shared behavior needs one stable value
globals()["PART_OBJECT_TYPE_IDS"] = KPartObjectTypeIds

# this binding exists because shared behavior needs one stable value
globals()["PERMISSIVE_TRUE_VALUES"] = KPermissiveTrueValues

# this binding exists because shared behavior needs one stable value
globals()["POCKET_TYPE_ID"] = KPocketTypeId

# this binding exists because shared behavior needs one stable value
globals()["PRIMITIVE_FEATURE_FAMILIES"] = KPrimitiveFeatureFamilies

# this binding exists because shared behavior needs one stable value
globals()["PRIMITIVE_FEATURE_TYPE_IDS"] = KPrimitiveFeatureTypeIds

# this binding exists because shared behavior needs one stable value
globals()["PrimitiveFeatureFamily"] = PrimitiveFamily

# this binding exists because shared behavior needs one stable value
globals()["QUANTITY_PROPERTY_UNITS"] = KQuantityPropUnits

# this binding exists because shared behavior needs one stable value
globals()["REGISTERED_PART_OBJECT_TYPE_IDS"] = KRegisteredPartObjectType

# this binding exists because shared behavior needs one stable value
globals()["SCALAR_PROPERTY_KINDS"] = KScalarPropKinds

# this binding exists because shared behavior needs one stable value
globals()["SCALAR_PROPERTY_TYPES"] = KScalarPropTypes

# this binding exists because shared behavior needs one stable value
globals()["SKETCH_TYPE_ID"] = KSketchTypeId

# this binding exists because shared behavior needs one stable value
globals()["SPLINE_CONTROL_TAGS"] = KSplineControlTags

# this binding exists because shared behavior needs one stable value
globals()["SPLINE_GEOMETRY_KINDS"] = KSplineGeomKinds

# this binding exists because shared behavior needs one stable value
globals()["SPLINE_GEOMETRY_TYPE_IDS"] = KSplineGeomTypeIds

# this binding exists because shared behavior needs one stable value
globals()["STRING_HASHER_TAGS"] = KStringHasherTags

# this binding exists because shared behavior needs one stable value
globals()["SUBELEMENT_KIND_BY_PREFIX"] = KSubElemKindByPrefix

# this binding exists because shared behavior needs one stable value
globals()["SUBELEMENT_MATE_ENTITY_KINDS"] = KSubElemMateEntityKinds

# this binding exists because shared behavior needs one stable value
globals()["SUPPORT_PLANE_TYPE_IDS"] = KSupportPlaneTypeIds

# this binding exists because shared behavior needs one stable value
globals()["ScalarPropertyType"] = ScalarPropType

# this binding exists because shared behavior needs one stable value
globals()["XML_TRUE_VALUES"] = KXmlTrueValues

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["dataclass"] = Dataclass

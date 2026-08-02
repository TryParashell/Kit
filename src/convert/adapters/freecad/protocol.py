from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from interchange import (
    BooleanOperation,
    ConstraintKind,
    ExtrusionEndCondition,
    FeatureKind,
    GeometryKind,
    MateEntityKind,
    MateKind,
    ValueKind,
)


ASSEMBLY_OBJECT_TYPE_PREFIX = "Assembly::"
ASSEMBLY_ROOT_TYPE_ID = "Assembly::AssemblyObject"
ASSEMBLY_JOINT_GROUP_TYPE_ID = "Assembly::JointGroup"
ASSEMBLY_LINK_TYPE_ID = "Assembly::AssemblyLink"
APP_LINK_TYPE_ID = "App::Link"
APP_PART_TYPE_ID = "App::Part"
BODY_TYPE_ID = "PartDesign::Body"
SKETCH_TYPE_ID = "Sketcher::SketchObject"
PART_CONTAINER_TYPE_IDS = frozenset({"Part::BodyBase", BODY_TYPE_ID})
BODY_CONTAINER_TYPE_IDS = PART_CONTAINER_TYPE_IDS | {APP_PART_TYPE_ID}
NON_FEATURE_OBJECT_TYPE_IDS = BODY_CONTAINER_TYPE_IDS | {SKETCH_TYPE_ID}
STRING_HASHER_TAGS = frozenset({"StringHasher", "StringHasher2"})
JOINT_GROUND_PROPERTY = "ObjectToGround"
JOINT_REFERENCE_PROPERTIES = ("Reference1", "Reference2")
JOINT_REFERENCE_INDEX_BY_PROPERTY = {
    name: index for index, name in enumerate(JOINT_REFERENCE_PROPERTIES)
}
JOINT_TYPE_PROPERTIES = frozenset({"JointType", "MateType"})
JOINT_RESERVED_LINK_PROPERTIES = frozenset(
    (JOINT_GROUND_PROPERTY, *JOINT_REFERENCE_PROPERTIES)
)
ASSEMBLY_CONNECTOR_PROPERTY_PREFIXES = ("Reference", "Placement")
XML_TRUE_VALUES = frozenset({"1", "true"})
PERMISSIVE_TRUE_VALUES = XML_TRUE_VALUES | {"yes"}
SPLINE_CONTROL_TAGS = frozenset({"Pole", "Knot"})
FREECAD_BREP_FORMAT_IDS = frozenset({"freecad.brep", "opencascade", "opencascade.brep"})
FREECAD_BREP_HEADER = b"CASCADE Topology V"
SUBELEMENT_MATE_ENTITY_KINDS = (
    MateEntityKind.FACE,
    MateEntityKind.EDGE,
    MateEntityKind.VERTEX,
    MateEntityKind.AXIS,
    MateEntityKind.PLANE,
)
SUBELEMENT_KIND_BY_PREFIX = {
    kind.value.title(): kind for kind in SUBELEMENT_MATE_ENTITY_KINDS
}

SUPPORT_PLANE_TYPE_IDS = frozenset(
    {"App::Plane", "Part::DatumPlane", "PartDesign::Plane"}
)

QUANTITY_PROPERTY_UNITS = {
    "Acceleration": "mm/s^2",
    "AmountOfSubstance": "mol",
    "Angle": "deg",
    "Area": "mm^2",
    "CompressiveStrength": "kg/(mm*s^2)",
    "CurrentDensity": "A/mm^2",
    "Density": "kg/mm^3",
    "DissipationRate": "mm^2/s^3",
    "Distance": "mm",
    "DynamicViscosity": "kg/(mm*s)",
    "ElectricalCapacitance": "A^2*s^4/(kg*mm^2)",
    "ElectricalConductance": "A^2*s^3/(kg*mm^2)",
    "ElectricalConductivity": "A^2*s^3/(kg*mm^3)",
    "ElectricalInductance": "kg*mm^2/(A^2*s^2)",
    "ElectricalResistance": "kg*mm^2/(A^2*s^3)",
    "ElectricCharge": "A*s",
    "ElectricCurrent": "A",
    "ElectricPotential": "kg*mm^2/(A*s^3)",
    "ElectromagneticPotential": "kg*mm/(A*s^2)",
    "Force": "kg*mm/s^2",
    "Frequency": "1/s",
    "HeatFlux": "kg/s^3",
    "InverseArea": "1/mm^2",
    "InverseLength": "1/mm",
    "InverseVolume": "1/mm^3",
    "KinematicViscosity": "mm^2/s",
    "Length": "mm",
    "LuminousIntensity": "cd",
    "MagneticFieldStrength": "A/mm",
    "MagneticFlux": "kg*mm^2/(A*s^2)",
    "MagneticFluxDensity": "kg/(A*s^2)",
    "Magnetization": "A/mm",
    "Mass": "kg",
    "Moment": "kg*mm^2/s^2",
    "Power": "kg*mm^2/s^3",
    "Pressure": "kg/(mm*s^2)",
    "ShearModulus": "kg/(mm*s^2)",
    "SpecificEnergy": "mm^2/s^2",
    "SpecificHeat": "mm^2/(s^2*K)",
    "Speed": "mm/s",
    "Stiffness": "kg/s^2",
    "StiffnessDensity": "kg/(mm^2*s^2)",
    "Stress": "kg/(mm*s^2)",
    "SurfaceChargeDensity": "A*s/mm^2",
    "Temperature": "K",
    "ThermalConductivity": "kg*mm/(s^3*K)",
    "ThermalExpansionCoefficient": "1/K",
    "ThermalTransferCoefficient": "kg/(s^3*K)",
    "Time": "s",
    "UltimateTensileStrength": "kg/(mm*s^2)",
    "VacuumPermittivity": "A^2*s^4/(kg*mm^3)",
    "Velocity": "mm/s",
    "Volume": "mm^3",
    "VolumeChargeDensity": "A*s/mm^3",
    "VolumeFlowRate": "mm^3/s",
    "VolumetricThermalExpansionCoefficient": "1/K",
    "Work": "kg*mm^2/s^2",
    "YieldStrength": "kg/(mm*s^2)",
    "YoungsModulus": "kg/(mm*s^2)",
}


@dataclass(frozen=True, slots=True)
class ScalarPropertyType:
    type_id: str
    value_kind: ValueKind
    unit: str
    value_tag: str


SCALAR_PROPERTY_TYPES = (
    ScalarPropertyType("App::PropertyAngle", ValueKind.ANGLE, "deg", "Float"),
    ScalarPropertyType("App::PropertyBool", ValueKind.BOOLEAN, "", "Bool"),
    ScalarPropertyType("App::PropertyDistance", ValueKind.LENGTH, "mm", "Float"),
    ScalarPropertyType("App::PropertyFile", ValueKind.STRING, "", "String"),
    ScalarPropertyType("App::PropertyFloat", ValueKind.NUMBER, "", "Float"),
    ScalarPropertyType("App::PropertyFloatConstraint", ValueKind.NUMBER, "", "Float"),
    ScalarPropertyType("App::PropertyFont", ValueKind.STRING, "", "String"),
    ScalarPropertyType("App::PropertyInteger", ValueKind.INTEGER, "", "Integer"),
    ScalarPropertyType(
        "App::PropertyIntegerConstraint", ValueKind.INTEGER, "", "Integer"
    ),
    ScalarPropertyType("App::PropertyLength", ValueKind.LENGTH, "mm", "Float"),
    ScalarPropertyType("App::PropertyPath", ValueKind.STRING, "", "Path"),
    ScalarPropertyType("App::PropertyPercent", ValueKind.QUANTITY, "%", "Integer"),
    ScalarPropertyType("App::PropertyPersistentObject", ValueKind.STRING, "", "String"),
    ScalarPropertyType("App::PropertyPrecision", ValueKind.NUMBER, "", "Float"),
    ScalarPropertyType("App::PropertyQuantity", ValueKind.QUANTITY, "", "Float"),
    ScalarPropertyType(
        "App::PropertyQuantityConstraint", ValueKind.QUANTITY, "", "Float"
    ),
    ScalarPropertyType("App::PropertyString", ValueKind.STRING, "", "String"),
    ScalarPropertyType("App::PropertyUUID", ValueKind.STRING, "", "Uuid"),
)
SCALAR_PROPERTY_KINDS = {
    **{
        f"App::Property{name}": (ValueKind.QUANTITY, unit, "Float")
        for name, unit in QUANTITY_PROPERTY_UNITS.items()
    },
    **{
        value.type_id: (value.value_kind, value.unit, value.value_tag)
        for value in SCALAR_PROPERTY_TYPES
    },
}


@dataclass(frozen=True, slots=True)
class FeatureType:
    type_id: str
    kind: FeatureKind


FEATURE_TYPES = (
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
FEATURE_KIND_BY_TYPE_ID = {value.type_id: value.kind for value in FEATURE_TYPES}


@dataclass(frozen=True, slots=True)
class BooleanOperationType:
    operation: BooleanOperation
    type_id: str
    label: str
    input_mode: str


BOOLEAN_OPERATION_TYPES = (
    BooleanOperationType(
        BooleanOperation.CREATE,
        "Part::Extrusion",
        "Extrusion",
        "standalone",
    ),
    BooleanOperationType(
        BooleanOperation.JOIN,
        "Part::MultiFuse",
        "Fuse",
        "shapes",
    ),
    BooleanOperationType(
        BooleanOperation.CUT,
        "Part::Cut",
        "Cut",
        "base_tool",
    ),
    BooleanOperationType(
        BooleanOperation.INTERSECT,
        "Part::Common",
        "Common",
        "base_tool",
    ),
)
BOOLEAN_OPERATION_TYPE_BY_KIND = {
    value.operation.value: value for value in BOOLEAN_OPERATION_TYPES
}
CREATE_OPERATION_NAMES = frozenset({"", BooleanOperation.CREATE.value})
FEATURE_WRITE_TYPE_IDS = MappingProxyType(
    {
        FeatureKind.EXTRUSION: frozenset(
            value.type_id for value in BOOLEAN_OPERATION_TYPES
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
if FEATURE_WRITE_TYPE_IDS.keys() != set(FeatureKind):
    raise RuntimeError("FreeCAD feature write types are not exhaustive")
FEATURE_WRITE_KINDS = frozenset(
    kind for kind, type_ids in FEATURE_WRITE_TYPE_IDS.items() if type_ids
)
FEATURE_CARRIER_KINDS = frozenset(FeatureKind) - FEATURE_WRITE_KINDS


@dataclass(frozen=True, slots=True)
class ExtrusionType:
    code: int
    end_condition: ExtrusionEndCondition
    pocket_end_condition: ExtrusionEndCondition | None = None


EXTRUSION_TYPES = (
    ExtrusionType(0, ExtrusionEndCondition.BLIND),
    ExtrusionType(
        1,
        ExtrusionEndCondition.UP_TO_LAST,
        ExtrusionEndCondition.THROUGH_ALL,
    ),
    ExtrusionType(2, ExtrusionEndCondition.UP_TO_FIRST),
    ExtrusionType(3, ExtrusionEndCondition.UP_TO_FACE),
    ExtrusionType(4, ExtrusionEndCondition.TWO_LENGTHS),
    ExtrusionType(5, ExtrusionEndCondition.UP_TO_SHAPE),
)
EXTRUSION_TYPE_BY_CODE = {value.code: value for value in EXTRUSION_TYPES}
POCKET_TYPE_ID = "PartDesign::Pocket"


@dataclass(frozen=True, slots=True)
class PrimitiveFeatureFamily:
    namespace: str
    prefixes: tuple[str, ...]
    shapes: tuple[str, ...]


PRIMITIVE_FEATURE_FAMILIES = (
    PrimitiveFeatureFamily(
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
    PrimitiveFeatureFamily(
        "PartDesign",
        ("", "Additive", "Subtractive"),
        (
            "Box",
            "Cone",
            "Cylinder",
            "Ellipsoid",
            "Prism",
            "Sphere",
            "Torus",
            "Wedge",
        ),
    ),
)
PRIMITIVE_FEATURE_TYPE_IDS = frozenset(
    f"{family.namespace}::{prefix}{shape}"
    for family in PRIMITIVE_FEATURE_FAMILIES
    for prefix in family.prefixes
    for shape in family.shapes
)
PART_OBJECT_TYPE_IDS = frozenset(
    (
        *FEATURE_KIND_BY_TYPE_ID,
        *PRIMITIVE_FEATURE_TYPE_IDS,
        *SUPPORT_PLANE_TYPE_IDS,
        *BODY_CONTAINER_TYPE_IDS,
    )
)
ADDITIONAL_PART_OBJECT_TYPE_IDS = frozenset({"App::Plane", "Part::FeatureGeometrySet"})
REGISTERED_PART_OBJECT_TYPE_IDS = PART_OBJECT_TYPE_IDS - ADDITIONAL_PART_OBJECT_TYPE_IDS


@dataclass(frozen=True, slots=True)
class ConstraintPoint:
    index: int
    name: str
    aliases: tuple[str, ...] = ()


CONSTRAINT_POINTS = (
    ConstraintPoint(1, "start", ("startpoint",)),
    ConstraintPoint(2, "end", ("endpoint",)),
    ConstraintPoint(3, "center", ("centre", "midpoint")),
)
CONSTRAINT_POINT_BY_INDEX = {value.index: value.name for value in CONSTRAINT_POINTS}
CONSTRAINT_POINT_INDEX_BY_NAME = {
    name: value.index
    for value in CONSTRAINT_POINTS
    for name in (value.name, *value.aliases)
}
MIDPOINT_REFERENCE_POINT_NAMES = frozenset(
    (
        "",
        "mid",
        *(
            name
            for value in CONSTRAINT_POINTS
            if value.index == 3
            for name in (value.name, *value.aliases)
        ),
    )
)


@dataclass(frozen=True, slots=True)
class ConstraintType:
    code: int
    kind: ConstraintKind
    value_kind: ValueKind | None = None
    unit: str = ""
    write_kinds: tuple[ConstraintKind, ...] = ()


CONSTRAINT_TYPES = (
    ConstraintType(
        1,
        ConstraintKind.COINCIDENT,
        write_kinds=(ConstraintKind.CONCENTRIC,),
    ),
    ConstraintType(2, ConstraintKind.HORIZONTAL),
    ConstraintType(3, ConstraintKind.VERTICAL),
    ConstraintType(4, ConstraintKind.PARALLEL),
    ConstraintType(5, ConstraintKind.TANGENT),
    ConstraintType(6, ConstraintKind.DISTANCE, ValueKind.LENGTH, "mm"),
    ConstraintType(7, ConstraintKind.DISTANCE_X, ValueKind.LENGTH, "mm"),
    ConstraintType(8, ConstraintKind.DISTANCE_Y, ValueKind.LENGTH, "mm"),
    ConstraintType(9, ConstraintKind.ANGLE, ValueKind.ANGLE, "rad"),
    ConstraintType(10, ConstraintKind.PERPENDICULAR),
    ConstraintType(11, ConstraintKind.RADIUS, ValueKind.LENGTH, "mm"),
    ConstraintType(12, ConstraintKind.EQUAL),
    ConstraintType(13, ConstraintKind.POINT_ON_OBJECT),
    ConstraintType(14, ConstraintKind.SYMMETRIC),
    ConstraintType(15, ConstraintKind.INTERNAL_ALIGNMENT),
    ConstraintType(16, ConstraintKind.SNELLS_LAW, ValueKind.NUMBER),
    ConstraintType(
        17,
        ConstraintKind.BLOCK,
        write_kinds=(ConstraintKind.FIXED,),
    ),
    ConstraintType(18, ConstraintKind.DIAMETER, ValueKind.LENGTH, "mm"),
    ConstraintType(19, ConstraintKind.WEIGHT, ValueKind.NUMBER),
    ConstraintType(20, ConstraintKind.GROUP),
    ConstraintType(21, ConstraintKind.TEXT),
)
CONSTRAINT_KIND_BY_CODE = {value.code: value.kind for value in CONSTRAINT_TYPES}
CONSTRAINT_VALUE_KIND_BY_CODE = {
    value.code: (value.value_kind, value.unit)
    for value in CONSTRAINT_TYPES
    if value.value_kind is not None
}
CONSTRAINT_CODE_BY_KIND = {
    kind.value: value.code
    for value in CONSTRAINT_TYPES
    for kind in (value.kind, *value.write_kinds)
}
CONSTRAINT_WRITE_CODES = MappingProxyType(
    {
        ConstraintKind.COINCIDENT: frozenset({1}),
        ConstraintKind.HORIZONTAL: frozenset({2}),
        ConstraintKind.VERTICAL: frozenset({3}),
        ConstraintKind.PARALLEL: frozenset({4}),
        ConstraintKind.PERPENDICULAR: frozenset({10}),
        ConstraintKind.TANGENT: frozenset({5}),
        ConstraintKind.EQUAL: frozenset({12}),
        ConstraintKind.CONCENTRIC: frozenset({1}),
        ConstraintKind.POINT_ON_OBJECT: frozenset({13}),
        ConstraintKind.SYMMETRIC: frozenset({14}),
        ConstraintKind.MIDPOINT: frozenset({14}),
        ConstraintKind.DISTANCE: frozenset({6}),
        ConstraintKind.DISTANCE_X: frozenset({7}),
        ConstraintKind.DISTANCE_Y: frozenset({8}),
        ConstraintKind.ANGLE: frozenset({9}),
        ConstraintKind.RADIUS: frozenset({11}),
        ConstraintKind.DIAMETER: frozenset({18}),
        ConstraintKind.FIXED: frozenset({17}),
        ConstraintKind.INTERNAL_ALIGNMENT: frozenset({15}),
        ConstraintKind.SNELLS_LAW: frozenset({16}),
        ConstraintKind.BLOCK: frozenset({17}),
        ConstraintKind.WEIGHT: frozenset({19}),
        ConstraintKind.GROUP: frozenset({20}),
        ConstraintKind.TEXT: frozenset({21}),
        ConstraintKind.NATIVE: frozenset(),
    }
)
if CONSTRAINT_WRITE_CODES.keys() != set(ConstraintKind):
    raise RuntimeError("FreeCAD constraint write codes are not exhaustive")
CONSTRAINT_COMPOSED_KINDS = frozenset(
    {
        ConstraintKind.CONCENTRIC,
        ConstraintKind.FIXED,
        ConstraintKind.MIDPOINT,
    }
)
CONSTRAINT_WRITE_KINDS = frozenset(
    kind for kind, codes in CONSTRAINT_WRITE_CODES.items() if codes
)
CONSTRAINT_DIRECT_KINDS = CONSTRAINT_WRITE_KINDS - CONSTRAINT_COMPOSED_KINDS
CONSTRAINT_CARRIER_KINDS = frozenset(ConstraintKind) - CONSTRAINT_WRITE_KINDS
FIXED_CONSTRAINT_KINDS = frozenset(
    kind
    for kind, code in CONSTRAINT_CODE_BY_KIND.items()
    if code == CONSTRAINT_CODE_BY_KIND[ConstraintKind.BLOCK.value]
)
DIMENSIONAL_CONSTRAINT_CODES = frozenset(CONSTRAINT_VALUE_KIND_BY_CODE)


@dataclass(frozen=True, slots=True)
class GeometryType:
    type_id: str
    kind: GeometryKind
    neutral_type: str = ""
    neutral_default: bool = False


GEOMETRY_TYPES = (
    GeometryType("Part::GeomPoint", GeometryKind.POINT, "PointGeometry", True),
    GeometryType("Part::GeomLine", GeometryKind.LINE),
    GeometryType("Part::GeomLineSegment", GeometryKind.LINE, "LineGeometry", True),
    GeometryType("Part::GeomCircle", GeometryKind.CIRCLE, "CircleGeometry", True),
    GeometryType("Part::GeomArcOfCircle", GeometryKind.ARC, "ArcGeometry", True),
    GeometryType("Part::GeomEllipse", GeometryKind.ELLIPSE, "EllipseGeometry", True),
    GeometryType(
        "Part::GeomArcOfEllipse",
        GeometryKind.ARC_ELLIPSE,
        "ArcEllipseGeometry",
        True,
    ),
    GeometryType(
        "Part::GeomHyperbola",
        GeometryKind.HYPERBOLA,
        "HyperbolaGeometry",
    ),
    GeometryType(
        "Part::GeomArcOfHyperbola",
        GeometryKind.ARC_HYPERBOLA,
        "ArcHyperbolaGeometry",
        True,
    ),
    GeometryType(
        "Part::GeomParabola",
        GeometryKind.PARABOLA,
        "ParabolaGeometry",
    ),
    GeometryType(
        "Part::GeomArcOfParabola",
        GeometryKind.ARC_PARABOLA,
        "ArcParabolaGeometry",
        True,
    ),
    GeometryType("Part::GeomBezierCurve", GeometryKind.BEZIER, "SplineGeometry", True),
    GeometryType("Part::GeomBSplineCurve", GeometryKind.SPLINE, "SplineGeometry", True),
    GeometryType("Part::GeomOffsetCurve", GeometryKind.OFFSET),
    GeometryType("Part::GeomTrimmedCurve", GeometryKind.TRIMMED),
)
GEOMETRY_KIND_BY_TYPE_ID = {value.type_id: value.kind for value in GEOMETRY_TYPES}
GEOMETRY_TYPE_IDS_BY_KIND = {
    kind.value: frozenset(
        value.type_id for value in GEOMETRY_TYPES if value.kind == kind
    )
    for kind in GeometryKind
    if kind != GeometryKind.NATIVE
}
NEUTRAL_GEOMETRY_TYPE_BY_KIND = {
    value.kind.value: value.neutral_type
    for value in GEOMETRY_TYPES
    if value.neutral_default
}
NEUTRAL_GEOMETRY_TYPE_ID_BY_KIND = {
    value.kind.value: value.type_id for value in GEOMETRY_TYPES if value.neutral_default
}
GEOMETRY_WRITE_TYPE_IDS = MappingProxyType(
    {
        GeometryKind.POINT: frozenset({"Part::GeomPoint"}),
        GeometryKind.LINE: frozenset({"Part::GeomLineSegment"}),
        GeometryKind.CIRCLE: frozenset({"Part::GeomCircle"}),
        GeometryKind.ARC: frozenset({"Part::GeomArcOfCircle"}),
        GeometryKind.ELLIPSE: frozenset({"Part::GeomEllipse"}),
        GeometryKind.ARC_ELLIPSE: frozenset({"Part::GeomArcOfEllipse"}),
        GeometryKind.HYPERBOLA: frozenset(),
        GeometryKind.ARC_HYPERBOLA: frozenset({"Part::GeomArcOfHyperbola"}),
        GeometryKind.PARABOLA: frozenset(),
        GeometryKind.ARC_PARABOLA: frozenset({"Part::GeomArcOfParabola"}),
        GeometryKind.BEZIER: frozenset({"Part::GeomBezierCurve"}),
        GeometryKind.SPLINE: frozenset({"Part::GeomBSplineCurve"}),
        GeometryKind.OFFSET: frozenset(),
        GeometryKind.TRIMMED: frozenset(),
        GeometryKind.NATIVE: frozenset(),
    }
)
if GEOMETRY_WRITE_TYPE_IDS.keys() != set(GeometryKind):
    raise RuntimeError("FreeCAD geometry write types are not exhaustive")
GEOMETRY_WRITE_KINDS = frozenset(
    kind for kind, type_ids in GEOMETRY_WRITE_TYPE_IDS.items() if type_ids
)
GEOMETRY_CARRIER_KINDS = frozenset(GeometryKind) - GEOMETRY_WRITE_KINDS
CIRCULAR_GEOMETRY_KINDS = frozenset({GeometryKind.CIRCLE.value, GeometryKind.ARC.value})
SPLINE_GEOMETRY_KINDS = frozenset(
    {GeometryKind.BEZIER.value, GeometryKind.SPLINE.value}
)
SPLINE_GEOMETRY_TYPE_IDS = frozenset(
    value.type_id
    for value in GEOMETRY_TYPES
    if value.kind.value in SPLINE_GEOMETRY_KINDS
)


@dataclass(frozen=True, slots=True)
class JointType:
    name: str
    kind: MateKind
    write_kinds: tuple[MateKind, ...] = ()
    write_aliases: tuple[str, ...] = ()
    uses_distance: bool = False
    uses_second_distance: bool = False


JOINT_TYPE_DEFINITIONS = (
    JointType(
        "Fixed",
        MateKind.LOCK,
        write_aliases=("fixed",),
    ),
    JointType("Revolute", MateKind.HINGE, write_aliases=("revolute",)),
    JointType(
        "Cylindrical",
        MateKind.CONCENTRIC,
        write_aliases=("cylindrical",),
    ),
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
    JointType(
        "Belt",
        MateKind.BELT,
        uses_distance=True,
        uses_second_distance=True,
    ),
)
MATE_KIND_BY_JOINT_TYPE = {value.name: value.kind for value in JOINT_TYPE_DEFINITIONS}
JOINT_TYPE_BY_MATE_KIND = {
    key: value.name
    for value in JOINT_TYPE_DEFINITIONS
    for key in (
        value.kind.value,
        *(kind.value for kind in value.write_kinds),
        *value.write_aliases,
    )
}
MATE_WRITE_TYPES = MappingProxyType(
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
if MATE_WRITE_TYPES.keys() != set(MateKind):
    raise RuntimeError("FreeCAD mate write types are not exhaustive")
MATE_WRITE_KINDS = frozenset(kind for kind, types in MATE_WRITE_TYPES.items() if types)
MATE_CARRIER_KINDS = frozenset(MateKind) - MATE_WRITE_KINDS
JOINT_TYPES = tuple(value.name for value in JOINT_TYPE_DEFINITIONS)
JOINT_TYPES_USING_DISTANCE = frozenset(
    value.name for value in JOINT_TYPE_DEFINITIONS if value.uses_distance
)
JOINT_TYPES_USING_SECOND_DISTANCE = frozenset(
    value.name for value in JOINT_TYPE_DEFINITIONS if value.uses_second_distance
)
MATE_KINDS_USING_DISTANCE = frozenset(
    value.kind for value in JOINT_TYPE_DEFINITIONS if value.uses_distance
)
MATE_KINDS_USING_SECOND_DISTANCE = frozenset(
    value.kind for value in JOINT_TYPE_DEFINITIONS if value.uses_second_distance
)

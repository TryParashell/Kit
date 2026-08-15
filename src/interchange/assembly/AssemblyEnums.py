# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.enums.EnumBase import WireEnum


# component kinds distinguish reusable parts assemblies references and native definitions
class ComponentKind(WireEnum):
    KPart = "part"
    KAssembly = "assembly"
    KReference = "reference"
    KNative = "native"


# mate kinds preserve mechanical relationship intent beyond generic geometric constraints
class MateKind(WireEnum):
    KCoincident = "coincident"
    KConcentric = "concentric"
    KParallel = "parallel"
    KPerpendicular = "perpendicular"
    KTangent = "tangent"
    KDistance = "distance"
    KAngle = "angle"
    KLock = "lock"
    KGear = "gear"
    KRackPinion = "rack_pinion"
    KScrew = "screw"
    KCoordinate = "coordinate"
    KSlider = "slider"
    KUniversalJoint = "universal_joint"
    KCamera = "cam"
    KSlot = "slot"
    KBall = "ball"
    KWidth = "width"
    KSymmetric = "symmetric"
    KLinearCoupler = "linear_coupler"
    KBelt = "belt"
    KPath = "path"
    KMagnetic = "magnetic"
    KHinge = "hinge"
    KProfileCenter = "profile_center"
    KNative = "native"


# mate entity kinds identify geometric primitives participating in assembly constraints
class MateEntityKind(WireEnum):
    KVertex = "vertex"
    KEdge = "edge"
    KFace = "face"
    KPoint = "point"
    KLine = "line"
    KAxis = "axis"
    KPlane = "plane"
    KCircle = "circle"
    KCylinder = "cylinder"
    KCone = "cone"
    KSphere = "sphere"
    KCurve = "curve"
    KSurface = "surface"
    KSketchEntity = "sketch_entity"
    KCoordinateSystem = "coordinate_system"
    KNative = "native"


# mate alignment captures orientation choices that geometry kind alone cannot express
class MateAlignment(WireEnum):
    KAligned = "aligned"
    KAntiAligned = "anti_aligned"
    KClosest = "closest"
    KUnknown = "unknown"

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.enums.EnumBase import WireEnum


# feature categories provide exhaustive portable dispatch without erasing native extensions
class FeatureKind(WireEnum):
    KExtrusion = "extrusion"
    KRevolution = "revolution"
    KSweep = "sweep"
    KLoft = "loft"
    KHole = "hole"
    KHelix = "helix"
    KFillet = "fillet"
    KChamfer = "chamfer"
    KShell = "shell"
    KDraft = "draft"
    KPattern = "pattern"
    KMirror = "mirror"
    KScale = "scale"
    KOffset = "offset"
    KPrimitive = "primitive"
    KSurface = "surface"
    KRefine = "refine"
    KReverse = "reverse"
    KBoolean = "boolean"
    KImported = "imported"
    KReference = "reference"
    KNative = "native"


# boolean operations preserve constructive intent between feature history implementations
class BooleanOp(WireEnum):
    KCreate = "create"
    KJoin = "join"
    KCutOperation = "cut"
    KIntersect = "intersect"

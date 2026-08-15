# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue, Callable


# mate type construction stays independent because classification data has one focused owner
def BuildMateTypes(MateType: Callable[..., AnyValue]) -> tuple[AnyValue, ...]:
    return (
        MateType(
            0,
            "swMateCOINCIDENT",
            "coincident",
            ("MateCoincident", "moMateCoincident"),
            ("coincident",),
        ),
        MateType(
            1,
            "swMateCONCENTRIC",
            "concentric",
            ("MateConcentric", "moMateConcentric"),
            ("concentric",),
        ),
        MateType(
            2,
            "swMatePERPENDICULAR",
            "perpendicular",
            ("MatePerpendicular", "moMatePerpendicular"),
            ("perpendicular",),
        ),
        MateType(
            3,
            "swMatePARALLEL",
            "parallel",
            ("MateParallel", "moMateParallel"),
            ("parallel",),
        ),
        MateType(
            4,
            "swMateTANGENT",
            "tangent",
            ("MateTangent", "moMateTangent"),
            ("tangent",),
        ),
        MateType(
            5,
            "swMateDISTANCE",
            "distance",
            (
                "MateDistanceDim",
                "MateLimitDistanceDim",
                "moMateDistanceDim",
                "moMateDistanceDim_c",
                "moMateLimitDistanceDim",
                "moMateLimitDistanceDim_c",
            ),
            ("distance", "limitdistance"),
            "length",
        ),
        MateType(
            6,
            "swMateANGLE",
            "angle",
            (
                "MateLimitAngleDim",
                "MatePlanarAngleDim",
                "moMateAngleDim_c",
                "moMateLimitAngleDim",
                "moMateLimitAngleDim_c",
                "moMatePlanarAngleDim",
                "moMatePlanarAngleDim_c",
            ),
            ("angle", "limitangle"),
            "angle",
        ),
        MateType(7, "swMateUNKNOWN", "native"),
        MateType(
            8,
            "swMateSYMMETRIC",
            "symmetric",
            ("MateSymmetric", "moMateSymmetric"),
            ("symmetric",),
        ),
        MateType(
            9,
            "swMateCAMFOLLOWER",
            "cam_tangent",
            ("MateCamTangent", "moMateCamTangent"),
            ("cam", "cammatetangent", "camfollower"),
            neutral_kind="cam",
        ),
        MateType(
            10,
            "swMateGEAR",
            "gear",
            ("MateGearDim", "moMateGearDim", "moMateGearDim_c"),
            ("gear", "gearmate"),
            "ratio",
        ),
        MateType(
            11,
            "swMateWIDTH",
            "width",
            ("MateWidth", "moMateWidth"),
            ("width", "widthmate"),
        ),
        MateType(
            12,
            "swMateLOCKTOSKETCH",
            "lock_to_sketch",
            ("moLockToSketchMate",),
            ("locktosketch", "locktosketchmate"),
            neutral_kind="lock",
        ),
        MateType(
            13,
            "swMateRACKPINION",
            "rack_pinion",
            ("MateRackPinionDim", "moMateRackPinionDim", "moMateRackPinionDim_c"),
            ("rackpinion",),
            "length",
        ),
        MateType(14, "swMateMAXMATES", "native"),
        MateType(
            15, "swMatePATH", "path", ("MatePath", "moMatePath"), ("path", "pathmate")
        ),
        MateType(
            16,
            "swMateLOCK",
            "lock",
            ("MateInPlace", "MateLock", "moMateInPlace", "moMateLock"),
            ("inplace", "lock", "lockmate"),
        ),
        MateType(
            17,
            "swMateSCREW",
            "screw",
            ("MateScrew", "moMateScrew", "moMateScrewDim_c"),
            ("screw", "screwmate"),
            "length",
        ),
        MateType(
            18,
            "swMateLINEARCOUPLER",
            "linear_coupler",
            ("MateLinearCoupler", "moMateLinearCoupler"),
            ("linearcoupler",),
            "ratio",
        ),
        MateType(
            19,
            "swMateUNIVERSALJOINT",
            "universal_joint",
            ("MateUniversalJoint", "moMateUniversalJoint"),
            ("universaljoint", "universalmate"),
        ),
        MateType(
            20,
            "swMateCOORDINATE",
            "coordinate",
            ("MateCoordinate", "moMateCoordinate"),
            ("coordinate",),
        ),
        MateType(
            21, "swMateSLOT", "slot", ("MateSlot", "moMateSlot"), ("slot", "slotmate")
        ),
        MateType(22, "swMateHINGE", "hinge", ("MateHinge", "moMateHinge"), ("hinge",)),
        MateType(
            23, "swMateSLIDER", "slider", ("MateSlider", "moMateSlider"), ("slider",)
        ),
        MateType(
            24,
            "swMatePROFILECENTER",
            "profile_center",
            ("MateProfileCenter", "moMateProfileCenter"),
            ("profilecenter",),
        ),
        MateType(
            25,
            "swMateMAGNETIC",
            "magnetic",
            ("MateMagnetic", "moMateMagnetic"),
            ("magnetic", "magneticmate"),
        ),
    )


# entity reference construction stays independent because geometry classification has one focused owner
def BuildRefTypes(MateType: Callable[..., AnyValue]) -> tuple[AnyValue, ...]:
    return (
        MateType(0, "swMateEntity2ReferenceType_Point", "point", ("refpoint", "point")),
        MateType(1, "swMateEntity2ReferenceType_Line", "line", ("line",)),
        MateType(2, "swMateEntity2ReferenceType_Circle", "circle", ("circle",)),
        MateType(3, "swMateEntity2ReferenceType_Plane", "plane", ("plane",)),
        MateType(
            4,
            "swMateEntity2ReferenceType_Cylinder",
            "cylinder",
            ("cylinder", "wzdhole", "sweepside"),
        ),
        MateType(5, "swMateEntity2ReferenceType_Sphere", "sphere", ("sphere",)),
        MateType(6, "swMateEntity2ReferenceType_Set", "native"),
        MateType(7, "swMateEntity2ReferenceType_Cone", "cone", ("cone",)),
        MateType(
            8, "swMateEntity2ReferenceType_SweptSurface", "surface", ("sweptsurface",)
        ),
        MateType(
            9,
            "swMateEntity2ReferenceType_MultipleSurface",
            "surface",
            ("multiplesurface",),
        ),
        MateType(
            10,
            "swMateEntity2ReferenceType_GenSurface",
            "surface",
            ("gensurface", "generalsurface", "surface"),
        ),
        MateType(11, "swMateEntity2ReferenceType_Ellipse", "curve", ("ellipse",)),
        MateType(
            12,
            "swMateEntity2ReferenceType_GeneralCurve",
            "curve",
            ("generalcurve", "curve"),
        ),
        MateType(13, "swMateEntity2ReferenceType_UNKNOWN", "native"),
    )

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass


# mate classification records stay concrete so catalog construction cannot erase their fields
@DataClass(frozen=True, slots=True)
class NativeMateType:
    code: int | None
    api_name: str
    kind: str
    class_names: tuple[str, ...] = ()
    name_prefixes: tuple[str, ...] = ()
    value_semantic: str = ""
    neutral_kind: str = ""


# entity classification records stay concrete so marker catalogs retain exact element types
@DataClass(frozen=True, slots=True)
class NativeMateTypeA:
    code: int | None
    api_name: str
    kind: str
    markers: tuple[str, ...] = ()


# mate type construction stays independent because classification data has one focused owner
def BuildMateTypes() -> tuple[NativeMateType, ...]:
    return (
        NativeMateType(
            0,
            "swMateCOINCIDENT",
            "coincident",
            ("MateCoincident", "moMateCoincident"),
            ("coincident",),
        ),
        NativeMateType(
            1,
            "swMateCONCENTRIC",
            "concentric",
            ("MateConcentric", "moMateConcentric"),
            ("concentric",),
        ),
        NativeMateType(
            2,
            "swMatePERPENDICULAR",
            "perpendicular",
            ("MatePerpendicular", "moMatePerpendicular"),
            ("perpendicular",),
        ),
        NativeMateType(
            3,
            "swMatePARALLEL",
            "parallel",
            ("MateParallel", "moMateParallel"),
            ("parallel",),
        ),
        NativeMateType(
            4,
            "swMateTANGENT",
            "tangent",
            ("MateTangent", "moMateTangent"),
            ("tangent",),
        ),
        NativeMateType(
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
        NativeMateType(
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
        NativeMateType(7, "swMateUNKNOWN", "native"),
        NativeMateType(
            8,
            "swMateSYMMETRIC",
            "symmetric",
            ("MateSymmetric", "moMateSymmetric"),
            ("symmetric",),
        ),
        NativeMateType(
            9,
            "swMateCAMFOLLOWER",
            "cam_tangent",
            ("MateCamTangent", "moMateCamTangent"),
            ("cam", "cammatetangent", "camfollower"),
            neutral_kind="cam",
        ),
        NativeMateType(
            10,
            "swMateGEAR",
            "gear",
            ("MateGearDim", "moMateGearDim", "moMateGearDim_c"),
            ("gear", "gearmate"),
            "ratio",
        ),
        NativeMateType(
            11,
            "swMateWIDTH",
            "width",
            ("MateWidth", "moMateWidth"),
            ("width", "widthmate"),
        ),
        NativeMateType(
            12,
            "swMateLOCKTOSKETCH",
            "lock_to_sketch",
            ("moLockToSketchMate",),
            ("locktosketch", "locktosketchmate"),
            neutral_kind="lock",
        ),
        NativeMateType(
            13,
            "swMateRACKPINION",
            "rack_pinion",
            ("MateRackPinionDim", "moMateRackPinionDim", "moMateRackPinionDim_c"),
            ("rackpinion",),
            "length",
        ),
        NativeMateType(14, "swMateMAXMATES", "native"),
        NativeMateType(
            15, "swMatePATH", "path", ("MatePath", "moMatePath"), ("path", "pathmate")
        ),
        NativeMateType(
            16,
            "swMateLOCK",
            "lock",
            ("MateInPlace", "MateLock", "moMateInPlace", "moMateLock"),
            ("inplace", "lock", "lockmate"),
        ),
        NativeMateType(
            17,
            "swMateSCREW",
            "screw",
            ("MateScrew", "moMateScrew", "moMateScrewDim_c"),
            ("screw", "screwmate"),
            "length",
        ),
        NativeMateType(
            18,
            "swMateLINEARCOUPLER",
            "linear_coupler",
            ("MateLinearCoupler", "moMateLinearCoupler"),
            ("linearcoupler",),
            "ratio",
        ),
        NativeMateType(
            19,
            "swMateUNIVERSALJOINT",
            "universal_joint",
            ("MateUniversalJoint", "moMateUniversalJoint"),
            ("universaljoint", "universalmate"),
        ),
        NativeMateType(
            20,
            "swMateCOORDINATE",
            "coordinate",
            ("MateCoordinate", "moMateCoordinate"),
            ("coordinate",),
        ),
        NativeMateType(
            21, "swMateSLOT", "slot", ("MateSlot", "moMateSlot"), ("slot", "slotmate")
        ),
        NativeMateType(
            22, "swMateHINGE", "hinge", ("MateHinge", "moMateHinge"), ("hinge",)
        ),
        NativeMateType(
            23, "swMateSLIDER", "slider", ("MateSlider", "moMateSlider"), ("slider",)
        ),
        NativeMateType(
            24,
            "swMatePROFILECENTER",
            "profile_center",
            ("MateProfileCenter", "moMateProfileCenter"),
            ("profilecenter",),
        ),
        NativeMateType(
            25,
            "swMateMAGNETIC",
            "magnetic",
            ("MateMagnetic", "moMateMagnetic"),
            ("magnetic", "magneticmate"),
        ),
    )


# entity reference construction stays independent because geometry classification has one focused owner
def BuildRefTypes() -> tuple[NativeMateTypeA, ...]:
    return (
        NativeMateTypeA(
            0, "swMateEntity2ReferenceType_Point", "point", ("refpoint", "point")
        ),
        NativeMateTypeA(1, "swMateEntity2ReferenceType_Line", "line", ("line",)),
        NativeMateTypeA(2, "swMateEntity2ReferenceType_Circle", "circle", ("circle",)),
        NativeMateTypeA(3, "swMateEntity2ReferenceType_Plane", "plane", ("plane",)),
        NativeMateTypeA(
            4,
            "swMateEntity2ReferenceType_Cylinder",
            "cylinder",
            ("cylinder", "wzdhole", "sweepside"),
        ),
        NativeMateTypeA(5, "swMateEntity2ReferenceType_Sphere", "sphere", ("sphere",)),
        NativeMateTypeA(6, "swMateEntity2ReferenceType_Set", "native"),
        NativeMateTypeA(7, "swMateEntity2ReferenceType_Cone", "cone", ("cone",)),
        NativeMateTypeA(
            8, "swMateEntity2ReferenceType_SweptSurface", "surface", ("sweptsurface",)
        ),
        NativeMateTypeA(
            9,
            "swMateEntity2ReferenceType_MultipleSurface",
            "surface",
            ("multiplesurface",),
        ),
        NativeMateTypeA(
            10,
            "swMateEntity2ReferenceType_GenSurface",
            "surface",
            ("gensurface", "generalsurface", "surface"),
        ),
        NativeMateTypeA(
            11, "swMateEntity2ReferenceType_Ellipse", "curve", ("ellipse",)
        ),
        NativeMateTypeA(
            12,
            "swMateEntity2ReferenceType_GeneralCurve",
            "curve",
            ("generalcurve", "curve"),
        ),
        NativeMateTypeA(13, "swMateEntity2ReferenceType_UNKNOWN", "native"),
    )

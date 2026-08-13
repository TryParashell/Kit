# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from enum import EnumMeta as BaseEnumMeta
from enum import StrEnum as StringEnum
from typing import Any as AnyValue


# historical names differ where compact canonical identifiers cannot mirror wire vocabulary
KLegacyEnums: dict[str, dict[str, str]] = {
    "BooleanOp": {"cut": "CUT", "intersect": "INTERSECT"},
    "Capability": {
        "parametric_history": "PARAMETRIC_HISTORY",
        "component_documents": "COMPONENT_DOCUMENTS",
        "external_references": "EXTERNAL_REFERENCES",
        "roundtrip_metadata": "ROUNDTRIP_METADATA",
    },
    "ExtrudeEnd": {"offset_from_surface": "OFFSET_FROM_SURFACE"},
    "GeometryKind": {"arc": "ARC"},
    "MateKind": {"cam": "CAM"},
    "UnitSystem": {"mm": "MILLIMETER", "m": "METER", "in": "INCH"},
}


# canonical member bindings stay reachable because implementation modules use steering compliant names
KCanonicalEnums: dict[type, dict[str, AnyValue]] = {}


# enum classes need historical member names while canonical declarations remain steering compliant
class EnumAliasMeta(BaseEnumMeta):

    # member construction translates canonical identifiers into their historical reflective names
    def __new__(
        MetaType, ClassName: str, BaseTypes: tuple[type, ...], ClassScope: AnyValue
    ):
        CanonicalNames = {
            NameText: ValueText
            for NameText, ValueText in ClassScope.items()
            if NameText.startswith("K") and isinstance(ValueText, str)
        }
        EnumType = super().__new__(MetaType, ClassName, BaseTypes, ClassScope)
        CanonicalMembers = {
            CanonicalName: EnumType.__members__[CanonicalName]
            for CanonicalName in CanonicalNames
        }
        LegacyMembers: dict[str, AnyValue] = {}
        for CanonicalName, WireValue in CanonicalNames.items():
            MemberValue = EnumType.__members__[CanonicalName]
            LegacyName = KLegacyEnums.get(ClassName, {}).get(
                WireValue,
                WireValue.upper(),
            )
            setattr(MemberValue, "_name_", LegacyName)
            LegacyMembers[LegacyName] = MemberValue
        KCanonicalEnums[EnumType] = CanonicalMembers
        if LegacyMembers:
            setattr(EnumType, "_member_names_", list(LegacyMembers))
            setattr(EnumType, "_member_map_", LegacyMembers)
        return EnumType

    # historical uppercase and canonical pascal names both resolve during migration
    def __getattr__(ClassType, NameText: str) -> AnyValue:
        CanonicalMembers = KCanonicalEnums.get(ClassType, {})
        if NameText in CanonicalMembers:
            return CanonicalMembers[NameText]
        MemberMap = type.__getattribute__(ClassType, "_member_map_")
        if NameText in MemberMap:
            return MemberMap[NameText]
        raise AttributeError(NameText)


# shared enum behavior keeps compatibility handling consistent across every model category
class WireEnum(StringEnum, metaclass=EnumAliasMeta):
    locals()["__slots__"] = ()

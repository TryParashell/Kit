# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping as MappingBase
from enum import EnumMeta as BaseEnumMeta
from enum import StrEnum as StringEnum
from typing import cast as CastValue

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
KCanonicalEnums: dict[object, dict[str, object]] = {}


# enum classes need historical member names while canonical declarations remain steering compliant
class EnumAliasMeta(BaseEnumMeta):

    # historical uppercase and canonical pascal names both resolve during migration
    def __getattr__(self, NameText: str) -> object:
        CanonicalMembers = KCanonicalEnums.get(self, {})
        if NameText in CanonicalMembers:
            return CanonicalMembers[NameText]
        MemberMap: object = type.__getattribute__(self, "_member_map_")
        if not isinstance(MemberMap, dict):
            raise AttributeError(NameText)
        MemberValues = CastValue(dict[object, object], MemberMap)
        if NameText in MemberValues:
            return MemberValues[NameText]
        raise AttributeError(NameText)


# shared enum behavior keeps compatibility handling consistent across every model category
class WireEnum(StringEnum, metaclass=EnumAliasMeta):
    locals()["__slots__"] = ()

    # completed enum classes can safely publish historical names without private namespace typing
    def __init_subclass__(cls, **KeywordValues: object) -> None:
        super().__init_subclass__(**KeywordValues)
        RawMembers: object = type.__getattribute__(cls, "__members__")
        if not isinstance(RawMembers, MappingBase):
            raise TypeError("enum members must form a mapping")
        EnumMembers = CastValue(MappingBase[str, object], RawMembers)
        CanonicalMembers = {
            MemberName: MemberValue
            for MemberName, MemberValue in EnumMembers.items()
            if MemberName.startswith("K")
        }
        LegacyMembers: dict[str, object] = {}
        for MemberValue in CanonicalMembers.values():
            WireValue: object = getattr(MemberValue, "value", None)
            if not isinstance(WireValue, str):
                raise TypeError("wire enum values must be strings")
            LegacyName = KLegacyEnums.get(cls.__name__, {}).get(
                WireValue,
                WireValue.upper(),
            )
            setattr(MemberValue, "_name_", LegacyName)
            LegacyMembers[LegacyName] = MemberValue
        KCanonicalEnums[cls] = CanonicalMembers
        if LegacyMembers:
            setattr(cls, "_member_names_", list(LegacyMembers))
            setattr(cls, "_member_map_", LegacyMembers)

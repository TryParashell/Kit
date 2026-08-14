# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from .payload_record import FindExtError
from .payload_roles import PayloadRole
from .payload_rules import KLegacyPayloadRules, PayloadRule


# payload inference normalizes optional historical text before evidence matching
def GetPayloadText(SourceValues: TypeMap[str, AnyValue], FieldName: str) -> str:
    WireName = {
        "EntityKind": "kind",
        "FormatId": "format_id",
        "SchemaText": "schema",
        "SourceStream": "source_stream",
    }.get(FieldName, FieldName)
    FieldValue = SourceValues.get(FieldName, SourceValues.get(WireName))
    return FieldValue.casefold().strip() if isinstance(FieldValue, str) else ""


# historical stream names provide fallback evidence for payload extensions
def GetSourceSuffix(SourceValues: TypeMap[str, AnyValue]) -> str:
    SourceText = GetPayloadText(SourceValues, "SourceStream").replace("\\", "/")
    NameValue = SourceText.rsplit("/", 1)[-1]
    DotIndex = NameValue.rfind(".")
    return NameValue[DotIndex:] if DotIndex >= 0 else ""


# declarative payload rules need one predicate shared by migration branches
def IsRuleMatch(
    RuleValue: PayloadRule,
    FormatId: str,
    KindValue: str,
    SchemaText: str,
    SourceSuffix: str,
) -> bool:
    return (
        (not RuleValue.FormatIds or FormatId in RuleValue.FormatIds)
        and (not RuleValue.Kinds or KindValue in RuleValue.Kinds)
        and (not RuleValue.Schemas or SchemaText in RuleValue.Schemas)
        and (not RuleValue.SourceSuffixes or SourceSuffix in RuleValue.SourceSuffixes)
    )


# old payload records need role and extension recovery without altering bytes
def GetLegacyFields(SourceValues: TypeMap[str, AnyValue]) -> tuple[PayloadRole, str]:
    FormatId = GetPayloadText(SourceValues, "FormatId")
    KindValue = GetPayloadText(SourceValues, "EntityKind")
    SchemaText = GetPayloadText(SourceValues, "SchemaText")
    SourceSuffix = GetSourceSuffix(SourceValues)
    SelectedRule = next(
        (
            RuleValue
            for RuleValue in KLegacyPayloadRules
            if IsRuleMatch(RuleValue, FormatId, KindValue, SchemaText, SourceSuffix)
        ),
        None,
    )
    if SelectedRule is None:
        FileExtension = SourceSuffix if not FindExtError(SourceSuffix) else ".bin"
        return PayloadRole.KAuxiliary, FileExtension
    if SelectedRule.FileExtension:
        return SelectedRule.ValueRole, SelectedRule.FileExtension
    SourceRule = next(
        (
            RuleValue
            for RuleValue in KLegacyPayloadRules
            if RuleValue.ValueRole == SelectedRule.ValueRole
            and RuleValue.SourceSuffixes
            and IsRuleMatch(RuleValue, FormatId, KindValue, SchemaText, SourceSuffix)
        ),
        None,
    )
    if SourceRule is not None:
        return SelectedRule.ValueRole, SourceRule.FileExtension
    FileExtension = SourceSuffix if not FindExtError(SourceSuffix) else ".bin"
    return SelectedRule.ValueRole, FileExtension


# old payload records need compatible defaults before immutable construction
def MigratePayload(SourceValues: TypeMap[str, AnyValue]) -> TypeMap[str, AnyValue]:
    IsRoleMissing = "role" not in SourceValues
    IsExtMissing = "file_extension" not in SourceValues
    if not IsRoleMissing and not IsExtMissing:
        return SourceValues
    ValueRole, FileExtension = GetLegacyFields(SourceValues)
    MigratedValues = dict(SourceValues)
    if IsRoleMissing:
        MigratedValues["role"] = ValueRole
    if IsExtMissing:
        MigratedValues["file_extension"] = FileExtension
    return MigratedValues

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Mapping as TypeMap

from interchange.payloads.PayloadRecord import FindExtError
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.payloads.PayloadRuleModel import PayloadRule
from interchange.payloads.PayloadRules import KLegacyPayloadRules


# payload inference normalizes optional historical text before evidence matching
def GetPayloadText(SourceValues: TypeMap[str, object], FieldName: str) -> str:
    WireName = {
        "EntityKind": "kind",
        "FormatId": "format_id",
        "SchemaText": "schema",
        "SourceStream": "source_stream",
    }.get(FieldName, FieldName)
    FieldValue = SourceValues.get(FieldName, SourceValues.get(WireName))
    return FieldValue.casefold().strip() if isinstance(FieldValue, str) else ""


# historical stream names provide fallback evidence for payload extensions
def GetSourceSuffix(SourceValues: TypeMap[str, object]) -> str:
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
        (not RuleValue.format_ids or FormatId in RuleValue.format_ids)
        and (not RuleValue.kinds or KindValue in RuleValue.kinds)
        and (not RuleValue.schemas or SchemaText in RuleValue.schemas)
        and (not RuleValue.source_suffixes or SourceSuffix in RuleValue.source_suffixes)
    )


# old payload records need role and extension recovery without altering bytes
def GetLegacyFields(SourceValues: TypeMap[str, object]) -> tuple[PayloadRole, str]:
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
    if SelectedRule.file_extension:
        return SelectedRule.role, SelectedRule.file_extension
    SourceRule = next(
        (
            RuleValue
            for RuleValue in KLegacyPayloadRules
            if RuleValue.role == SelectedRule.role
            and RuleValue.source_suffixes
            and IsRuleMatch(RuleValue, FormatId, KindValue, SchemaText, SourceSuffix)
        ),
        None,
    )
    if SourceRule is not None:
        return SelectedRule.role, SourceRule.file_extension
    FileExtension = SourceSuffix if not FindExtError(SourceSuffix) else ".bin"
    return SelectedRule.role, FileExtension


# old payload records need compatible defaults before immutable construction
def MigratePayload(SourceValues: TypeMap[str, object]) -> TypeMap[str, object]:
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

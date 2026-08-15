# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from importlib import import_module as ImportModule
from typing import Any as AnyValue

from tools.audit.FcstdArgs import ParseArguments
from tools.audit.FcstdCli import MainRun
from tools.audit.FcstdDiscovery import DiscoverSources
from tools.audit.FcstdFeatures import FeatureTypes


# legacy lookups preserve programmatic consumers while compliant focused modules own behavior
KLegacyApi = {
    "REPOSITORY_ROOT": ("tools.audit.FcstdContext", "KRepositoryRoot"),
    "ParseArguments": ParseArguments,
    "DiscoverSources": DiscoverSources,
    "FeatureTypes": FeatureTypes,
    "AuditSource": ("tools.audit.FcstdAudit", "AuditSource"),
    "AuditSourceIsolated": ("tools.audit.FcstdIsolate", "AuditIsolated"),
    "Main": MainRun,
}


# compatibility resolution prevents module restructuring from breaking existing audit automation
def GetLegacyAttr(NameText: str) -> AnyValue:
    try:
        ApiValue = KLegacyApi[NameText]
    except KeyError as ErrorInfo:
        raise AttributeError(NameText) from ErrorInfo
    if isinstance(ApiValue, tuple):
        ModuleName, SymbolName = ApiValue
        ApiValue = getattr(ImportModule(ModuleName), SymbolName)
    return ApiValue

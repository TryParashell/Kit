# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from importlib import import_module as ImportModule
from typing import NamedTuple

from tools.audit.FcstdArgs import ParseArguments
from tools.audit.FcstdCli import MainRun
from tools.audit.FcstdDiscovery import DiscoverSources
from tools.audit.FcstdFeatures import FeatureTypes


# delayed imports keep compatibility names available without introducing eager dependency cycles
class ImportPayload(NamedTuple):
    ModuleName: str
    SymbolName: str


# legacy lookups preserve programmatic consumers while compliant focused modules own behavior
KLegacyApi: dict[str, object | ImportPayload] = {
    "REPOSITORY_ROOT": ImportPayload("tools.audit.FcstdContext", "KRepositoryRoot"),
    "ParseArguments": ParseArguments,
    "DiscoverSources": DiscoverSources,
    "FeatureTypes": FeatureTypes,
    "AuditSource": ImportPayload("tools.audit.FcstdAudit", "AuditSource"),
    "AuditSourceIsolated": ImportPayload("tools.audit.FcstdIsolate", "AuditIsolated"),
    "Main": MainRun,
}


# compatibility resolution prevents module restructuring from breaking existing audit automation
def GetLegacyAttr(NameText: str) -> object:
    try:
        ApiValue = KLegacyApi[NameText]
    except KeyError as ErrorInfo:
        raise AttributeError(NameText) from ErrorInfo
    if isinstance(ApiValue, ImportPayload):
        ApiValue = getattr(
            ImportModule(ApiValue.ModuleName),
            ApiValue.SymbolName,
        )
    return ApiValue

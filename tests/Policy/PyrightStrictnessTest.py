# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import tomllib
from typing import cast as CastValue
from pathlib import Path

import pytest

# repo root derivation keeps tests runnable from any working directory
KRootPath = Path(__file__).resolve().parents[2]

# every diagnostic the strictest pyright surface can express stays pinned at error because repository rules must stay recognized by the pinned cli
KRequiredRules = (
    "reportAssertTypeFailure",
    "reportCallInDefaultInitializer",
    "reportDeprecated",
    "reportImplicitOverride",
    "reportImplicitStringConcatenation",
    "reportInvalidStubStatement",
    "reportMatchNotExhaustive",
    "reportMissingSuperCall",
    "reportPrivateUsage",
    "reportSelfClsParameterName",
    "reportTypeCommentUsage",
    "reportUninitializedInstanceVariable",
    "reportUnnecessaryCast",
    "reportUnnecessaryComparison",
    "reportUnnecessaryContains",
    "reportUnnecessaryIsInstance",
    "reportUnnecessaryTypeIgnoreComment",
    "reportUnsupportedDunderAll",
    "reportUnusedCallResult",
    "reportUnusedExpression",
    "reportUnusedImport",
    "reportUnusedVariable",
)


# config loading stays centralized so every assertion sees identical settings
def LoadPyConfig() -> dict[str, object]:
    Metadata = tomllib.loads((KRootPath / "pyproject.toml").read_text(encoding="utf-8"))
    return CastValue(dict[str, object], Metadata["tool"]["pyright"])


# strict mode is the baseline the whole policy depends on
def TestStrictMode() -> None:
    assert LoadPyConfig()["typeCheckingMode"] == "strict"


# scope assertions stop silent exclusions from weakening future checks
def TestConfigScope() -> None:
    Config = LoadPyConfig()
    IncludeValue = CastValue(list[str], Config["include"])
    assert set(IncludeValue) == {"src", "tests", "tools"}
    assert Config["pythonVersion"] == "3.11"


# pinning severity keeps regressions loud instead of advisory whispers
@pytest.mark.parametrize("RuleName", KRequiredRules)
def TestRulePinned(RuleName: str) -> None:
    Config = LoadPyConfig()
    assert Config.get(RuleName) == "error", RuleName


# hash marker stays isolated because probe text must assemble without literal adjacency
KHashMarker = "#"

# probe fragments stay split because literal pragmas would flag this scanner itself
KIgnoreProbeText = KHashMarker + " type" + ": ignore"

# pyright probes stay split because literal pragmas would flag this scanner itself
KPyrightProbeText = KHashMarker + " pyright" + ":"


# suppression scans keep diagnostics honest by banning inline escapes
def TestBansEscapes() -> None:
    Offenders: list[str] = []
    for AreaName in ("src", "tests", "tools"):
        for PathInfo in (KRootPath / AreaName).rglob("*.py"):
            FileText = PathInfo.read_text(encoding="utf-8", errors="ignore")
            if KIgnoreProbeText in FileText or KPyrightProbeText in FileText:
                Offenders.append(str(PathInfo))
    assert Offenders == []

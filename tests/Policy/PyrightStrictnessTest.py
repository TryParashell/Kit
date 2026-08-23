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

# every diagnostic the strictest pylance surface can express stays pinned at error because repository pyright lags behind editors
KRequiredRules = (
    "reportAssertTypeFailure",
    "reportCallInDefaultInitializer",
    "reportDeprecated",
    "reportImplicitAbstractClass",
    "reportImplicitOverride",
    "reportImplicitStringConcatenation",
    "reportIncompleteStubValue",
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
    "reportUnsafeMultipleInheritance",
    "reportUnsupportedDunderAll",
    "reportUnusedCallResult",
    "reportUnusedExpression",
    "reportUnusedImport",
    "reportUnusedVariable",
)


 # config loading stays centralized so every assertion sees identical settings
def LoadPyrightConfig() -> dict[str, object]:
    Metadata = tomllib.loads((KRootPath / "pyproject.toml").read_text(encoding="utf-8"))
    return CastValue(dict[str, object], Metadata["tool"]["pyright"])


 # strict mode is the baseline the whole policy depends on
def TestStrictMode() -> None:
    assert LoadPyrightConfig()["typeCheckingMode"] == "strict"


 # scope assertions stop silent exclusions from weakening future checks
def TestScopeCoversWholeTree() -> None:
    Config = LoadPyrightConfig()
    IncludeValue = CastValue(list[str], Config["include"])
    assert set(IncludeValue) == {"src", "tests", "tools"}
    assert Config["pythonVersion"] == "3.11"


 # pinning severity keeps regressions loud instead of advisory whispers
@pytest.mark.parametrize("RuleName", KRequiredRules)
def TestRulePinnedAtError(RuleName: str) -> None:
    Config = LoadPyrightConfig()
    assert Config.get(RuleName) == "error", RuleName


 # suppression scans keep diagnostics honest by banning inline escapes
def TestNoSuppressionEscapes() -> None:
    Offenders = []
    for Root in ("src", "tests", "tools"):
        for PathInfo in (KRootPath / Root).rglob("*.py"):
            Text = PathInfo.read_text(encoding="utf-8", errors="ignore")
            if "# type: ignore" in Text or "# pyright:" in Text:
                Offenders.append(str(PathInfo))
    assert Offenders == []

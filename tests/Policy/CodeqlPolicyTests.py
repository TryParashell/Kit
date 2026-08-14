# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from ast import literal_eval as LiteralEval
from pathlib import Path as PathInfo
import re as Regex

# repository discovery keeps policy tests independent from the invocation directory
KRootInfo = PathInfo(__file__).resolve().parents[2]

# exact exceptions prevent security findings from entering the policy allowance
KQueryExcludes = frozenset(
    (
        "py/not-named-self",
        "py/not-named-cls",
        "py/possible-timing-attack-sensitive-info",
        "py/possible-timing-attack-against-hash",
    )
)

# modeled path barriers correspond only to fixed root containment functions
KPathBarriers = frozenset(
    (
        ("convert.Security.PathBoundary", "ResolveInput"),
        ("convert.Security.PathBoundary", "ResolveLocal"),
        ("convert.Security.PathBoundary", "ResolveOutput"),
        ("convert.Security.PathBoundary", "ResolveFolder"),
        ("convert.Security.PathBoundary", "ResolveTemp"),
        ("convert.Security.ProgramBoundary", "GetFreecadPath"),
    )
)

# modeled command barriers correspond only to strict allowlist validation functions
KCommandBarriers = frozenset(
    (
        ("convert.Security.PathBoundary", "ValidateLabel"),
        ("convert.Security.ProgramBoundary", "GetFreecadPath"),
    )
)


# text loading keeps configuration assertions independent from optional yaml packages
def LoadText(RelativePath: str) -> str:
    return (KRootInfo / RelativePath).read_text(encoding="utf-8")


# query extraction keeps the two configured policy surfaces exactly synchronized
def QueryIds(SourceText: str) -> frozenset[str]:
    return frozenset(Regex.findall(r"^\s+- (py/[a-z0-9-]+)$", SourceText, Regex.M))


# model extraction verifies every sanitizer row without accepting broader predicates
def ModelRows(SourceText: str) -> frozenset[tuple[str, str, str]]:
    RowTexts = Regex.findall(r"^\s+- (\[.*\])$", SourceText, Regex.M)
    return frozenset((tuple(LiteralEval(RowText)) for RowText in RowTexts))


# workflow configuration must run every suite and supported repository language
def TestFlowScope() -> None:
    SourceText = LoadText(".github/workflows/CodeqlSecurity.yml")
    assert "config-file: ./.github/CodeQL/CodeqlConfig.yml" in SourceText
    for LanguageName in ("actions", "java-kotlin", "python"):
        assert f"- {LanguageName}" in SourceText


# query exceptions stay limited to receiver naming and nonsecret timing heuristics
def TestFilters() -> None:
    ConfigText = LoadText(".github/CodeQL/CodeqlConfig.yml")
    SuiteText = LoadText(".github/CodeQL/PythonMaximal.qls")
    assert QueryIds(ConfigText) == KQueryExcludes
    assert QueryIds(SuiteText) == KQueryExcludes
    assert "security-and-quality" in ConfigText
    assert "security-experimental" in ConfigText


# model rows stay limited to tested path containment and command allowlists
def TestModels() -> None:
    SourceText = LoadText(
        ".github/codeql/extensions/KitPython/PythonModels.yml"
    )
    RowsInfo = ModelRows(SourceText)
    PathRows = {
        (ModuleName, f"Member[{FunctionName}].ReturnValue", "path-injection")
        for ModuleName, FunctionName in KPathBarriers
    }
    CommandRows = {
        (ModuleName, f"Member[{FunctionName}].ReturnValue", "command-injection")
        for ModuleName, FunctionName in KCommandBarriers
    }
    assert RowsInfo == PathRows | CommandRows

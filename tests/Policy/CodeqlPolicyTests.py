# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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

# common path barriers correspond only to fixed root containment functions
KCorePathBarriers = frozenset(
    (
        (
            "convert",
            "Member[Security].Member[PathBoundary].Member[ResolveLexical].ReturnValue",
        ),
        (
            "convert",
            "Member[Security].Member[PathBoundary].Member[ResolveInput].ReturnValue",
        ),
        (
            "convert",
            "Member[Security].Member[PathBoundary].Member[ResolveLocal].ReturnValue",
        ),
        (
            "convert",
            "Member[Security].Member[PathBoundary].Member[ResolveOutput].ReturnValue",
        ),
        (
            "convert",
            "Member[Security].Member[PathBoundary].Member[ResolveFolder].ReturnValue",
        ),
        (
            "convert",
            "Member[Security].Member[PathBoundary].Member[ResolveTemp].ReturnValue",
        ),
    )
)

# specialized path barriers keep strict labels and executable roots explicit
KEdgePathBarriers = frozenset(
    (
        (
            "convert",
            "Member[Security].Member[PathBoundary].Member[ValidateLabel].ReturnValue",
        ),
        (
            "convert",
            "Member[Security].Member[ProgramBoundary].Member[GetFreecadPath].ReturnValue",
        ),
    )
)

# one expected set keeps model validation independent from yaml ordering
KPathBarriers = KCorePathBarriers | KEdgePathBarriers

# modeled command barriers correspond only to strict allowlist validation functions
KCommandBarriers = frozenset(
    (
        (
            "convert",
            "Member[Security].Member[PathBoundary].Member[ValidateLabel].ReturnValue",
        ),
        (
            "convert",
            "Member[Security].Member[PathBoundary].Member[ResolveArgPath].ReturnValue",
        ),
        (
            "convert",
            "Member[Security].Member[ProgramBoundary].Member[GetFreecadPath].ReturnValue",
        ),
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
    Matches = Regex.findall(
        r'^\s+- - "([^"]+)"\n\s+- "([^"]+\.ReturnValue)"\n\s+- "([^"]+)"$',
        SourceText,
        Regex.M,
    )
    return frozenset(Matches)


# workflow configuration must scan every suite and maintained repository language
def TestFlowScope() -> None:
    SourceText = LoadText(".github/workflows/CodeqlSecurity.yml")
    ConfigText = LoadText(".github/CodeQL/CodeqlConfig.yml")
    assert "config-file: ./.github/CodeQL/CodeqlConfig.yml" in SourceText
    assert "cp -R .github/CodeQL/extensions .github/codeql/extensions" in SourceText
    assert "paths-ignore:\n  - re/**" in ConfigText
    assert "queries: ./.github/CodeQL/PythonMaximal.qls" in SourceText
    assert 'select(any(.suppressions[]?; .kind == "inSource") | not)' in SourceText
    for LanguageName in ("actions", "python"):
        assert f"language: {LanguageName}" in SourceText
    assert "- java-kotlin" not in SourceText


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
    SourceText = LoadText(".github/CodeQL/extensions/KitPython/PythonModels.yml")
    RowsInfo = ModelRows(SourceText)
    PathRows = {
        (ModuleName, AccessPath, "path-injection")
        for ModuleName, AccessPath in KPathBarriers
    }
    CommandRows = {
        (ModuleName, AccessPath, "command-injection")
        for ModuleName, AccessPath in KCommandBarriers
    }
    assert RowsInfo == PathRows | CommandRows

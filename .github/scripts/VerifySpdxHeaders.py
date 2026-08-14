# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify exact SPDX headers on every in-scope changed file."""

from __future__ import annotations

import argparse as Argparse
import hashlib as Hashlib
import pathlib as Pathlib
import subprocess as Subprocess
import sys as System

from SpdxHeaderRemediation import CanRepairMut
from SpdxHeaderRemediation import GetNewline
from SpdxHeaderRemediation import WriteMissingMut


# repository root stays canonical because every path check needs one trusted boundary
KRepoRoot = Pathlib.Path(__file__).resolve().parents[2]

# canonical notice location stays explicit because rendered headers must share exact source text
KHeaderNoticePath = KRepoRoot / "HEADER_NOTICE"

# required skill license stays immutable because frontmatter cannot carry the normal leading block
KSkillLicenseField = "license: LicenseRef-PolyForm-Strict-1.0.0"

# exempt prefixes stay narrow because only steering sources and vendor examples omit normal headers
KExemptPrefixes = (".kiro/", "examples/")

# canonical notice remains exempt because it is the uncommented source used to render headers
KExemptPaths = frozenset({"HEADER_NOTICE"})

# generated research data stays exact because its record grammar has no comment syntax
KRawArtifactPaths = frozenset(
    {
        "re/data/Serialization/SldmfcuSigtableRefs.txt",
        "re/data/vocabulary/Flagmap.txt",
        "re/data/vocabulary/Vocabulary.txt",
    }
)

# hash comment extensions stay grouped because these formats share one exact rendering rule
KHashExtensions = frozenset(
    {
        ".bash",
        ".cfg",
        ".conf",
        ".gitattributes",
        ".ini",
        ".lock",
        ".py",
        ".pyi",
        ".sh",
        ".toml",
        ".yaml",
        ".yml",
        ".zsh",
    }
)

# slash comment extensions stay grouped because these languages share one exact rendering rule
KSlashExtensions = frozenset(
    {
        ".c",
        ".cc",
        ".cjs",
        ".cpp",
        ".cs",
        ".go",
        ".h",
        ".hpp",
        ".java",
        ".js",
        ".jsx",
        ".kt",
        ".mjs",
        ".rs",
        ".swift",
        ".ts",
        ".tsx",
    }
)

# line styles stay declarative because extension lookup must not depend on branch order
KLineStyles = {"#": KHashExtensions, "//": KSlashExtensions}

# block extensions stay explicit because these formats require wrapped comment delimiters
KBlockExtensions = frozenset({".htm", ".html", ".markdown", ".md", ".svg", ".xml"})

# special filenames stay explicit because reliable comment syntax cannot come from an extension
KSpecialStyles = {
    ".gitignore": "#",
    "Dockerfile": "#",
    "LICENSE": "block",
    "Makefile": "#",
}

# syntaxless formats stay explicit because inserting comments would invalidate their grammar
KNoCommentExtensions = frozenset({".json"})

# binary extensions stay explicit because byte oriented artifacts cannot carry text headers
KBinaryExtensions = frozenset(
    {
        ".7z",
        ".catpart",
        ".catproduct",
        ".f3d",
        ".f3z",
        ".gif",
        ".ico",
        ".iges",
        ".igs",
        ".jpeg",
        ".jpg",
        ".pdf",
        ".png",
        ".sat",
        ".sldasm",
        ".sldprt",
        ".step",
        ".stl",
        ".stp",
        ".webp",
        ".whl",
        ".x_t",
        ".zip",
    }
)


# canonical loading stays isolated because every renderer must consume identical normalized lines
def LoadCanon() -> list[str]:
    NoticeText = KHeaderNoticePath.read_text(encoding="utf-8")
    return NoticeText.splitlines()


# line rendering stays centralized because comment prefixes must preserve blank notice lines exactly
def RenderLines(CanonLines: list[str], PrefixText: str) -> list[str]:
    return [
        PrefixText if LineText == "" else f"{PrefixText} {LineText}"
        for LineText in CanonLines
    ]


# block rendering stays centralized because markup files require balanced delimiters around the notice
def RenderBlock(CanonLines: list[str]) -> list[str]:
    return ["<!--", *CanonLines, "-->"]


# header hashing stays centralized because comparisons must normalize exactly one trailing newline
def HashLines(SourceLines: list[str]) -> str:
    JoinedText = "\n".join(SourceLines) + "\n"
    return Hashlib.sha256(JoinedText.encode("utf-8")).hexdigest()


# path exemption remains a predicate because scope decisions must be testable independently
def IsPathExempt(RelPath: str) -> bool:
    if RelPath in KExemptPaths or RelPath in KRawArtifactPaths:
        return True
    return any(RelPath.startswith(PrefixText) for PrefixText in KExemptPrefixes)


# style lookup stays isolated because format classification must remain separate from content checking
def GetStyle(SourcePath: Pathlib.Path) -> str | None:
    if SourcePath.name in KSpecialStyles:
        return KSpecialStyles[SourcePath.name]
    ExtensionText = SourcePath.suffix.lower()
    if ExtensionText in KNoCommentExtensions or ExtensionText in KBinaryExtensions:
        return None
    if ExtensionText in KBlockExtensions:
        return "block"
    return next(
        (
            PrefixText
            for PrefixText, Extensions in KLineStyles.items()
            if ExtensionText in Extensions
        ),
        "unknown",
    )


# text loading stays tolerant because unreadable changed files must be treated as binary artifacts
def ReadLines(SourcePath: Pathlib.Path) -> list[str] | None:
    try:
        return SourcePath.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return None


# leading offset stays isolated because executable scripts may place one shebang before the notice
def GetLeadOffset(SourceLines: list[str]) -> int:
    return int(bool(SourceLines and SourceLines[0].startswith("#!")))


# skill detection remains worktree relative because detached pull request trees need the same contract
def IsAgentSkill(SourcePath: Pathlib.Path, WorktreeRoot: Pathlib.Path) -> bool:
    SkillRoot = WorktreeRoot / ".agents" / "skills"
    return SourcePath.name == "SKILL.md" and SourcePath.parent.parent == SkillRoot


# skill checking stays separate because frontmatter licensing differs from normal comment headers
def CheckSkill(SourcePath: Pathlib.Path) -> tuple[bool, str]:
    SourceLines = ReadLines(SourcePath)
    if SourceLines is None:
        return False, "Agent Skills file is not readable as UTF-8 text"
    if not SourceLines or SourceLines[0] != "---":
        return False, "Agent Skills frontmatter is missing"
    try:
        FrontEnd = SourceLines.index("---", 1)
    except ValueError:
        return False, "Agent Skills frontmatter is not terminated"
    LicenseFields = [
        LineText
        for LineText in SourceLines[1:FrontEnd]
        if LineText.startswith("license:")
    ]
    if LicenseFields != [KSkillLicenseField]:
        return False, "Agent Skills license field is missing or invalid"
    return True, "Agent Skills license field OK"


# candidate construction stays isolated because unknown text formats support several safe comment styles
def GetCandidates(StyleText: str, CanonLines: list[str]) -> list[list[str]]:
    if StyleText == "block":
        return [RenderBlock(CanonLines)]
    if StyleText == "unknown":
        return [
            RenderLines(CanonLines, "#"),
            RenderLines(CanonLines, "$$"),
            RenderBlock(CanonLines),
        ]
    return [RenderLines(CanonLines, StyleText)]


# header matching stays isolated because exact hashes and useful failure evidence share one contract
def MatchHeader(
    SourceLines: list[str], OffsetValue: int, CandidateSets: list[list[str]]
) -> tuple[bool, str]:
    for ExpectedLines in CandidateSets:
        ActualLines = SourceLines[OffsetValue : OffsetValue + len(ExpectedLines)]
        ActualHash = HashLines(ActualLines)
        if ActualHash == HashLines(ExpectedLines):
            return True, f"header hash OK ({ActualHash[:12]})"
    ExpectedLines = CandidateSets[0]
    ActualLines = SourceLines[OffsetValue : OffsetValue + len(ExpectedLines)]
    ExpectedHash = HashLines(ExpectedLines)
    ActualHash = HashLines(ActualLines)
    FailureKind = (
        "missing or truncated"
        if len(ActualLines) < len(ExpectedLines)
        else "modified or tampered"
    )
    return False, (
        f"header {FailureKind} "
        f"(expected sha256={ExpectedHash[:12]}, got sha256={ActualHash[:12]})"
    )


# file checking composes focused policies because skill binary and text artifacts need distinct handling
def CheckFile(
    SourcePath: Pathlib.Path,
    CanonLines: list[str],
    WorktreeRoot: Pathlib.Path = KRepoRoot,
) -> tuple[bool, str]:
    if IsAgentSkill(SourcePath, WorktreeRoot):
        return CheckSkill(SourcePath)
    StyleText = GetStyle(SourcePath)
    if StyleText is None:
        return True, "exempt (no comment syntax available)"
    SourceLines = ReadLines(SourcePath)
    if SourceLines is None:
        return True, "exempt (not readable as UTF-8 text; treated as binary)"
    CandidateSets = GetCandidates(StyleText, CanonLines)
    return MatchHeader(SourceLines, GetLeadOffset(SourceLines), CandidateSets)


# containment validation prevents a crafted changed path or symlink from escaping its materialized worktree
def ResolvePath(
    WorktreeRoot: Pathlib.Path, RelPath: str
) -> Pathlib.Path | None:
    CandidatePath = (WorktreeRoot / RelPath).resolve()
    try:
        CandidatePath.relative_to(WorktreeRoot)
    except ValueError:
        return None
    return CandidatePath


# invalid skill licenses can be normalized without disturbing any other frontmatter or body bytes
def CanFixSkillMut(SourcePath: Pathlib.Path) -> bool:
    SourceBytes = SourcePath.read_bytes()
    Newline = GetNewline(SourceBytes)
    SourceLines = SourceBytes.splitlines(keepends=True)
    if not SourceLines or SourceLines[0].strip() != b"---":
        return False
    try:
        FrontEnd = next(
            LineIndex
            for LineIndex, LineBytes in enumerate(SourceLines[1:], 1)
            if LineBytes.strip() == b"---"
        )
    except StopIteration:
        return False
    LicenseBytes = KSkillLicenseField.encode("utf-8") + Newline
    UpdatedLines = SourceLines[:1] + [LicenseBytes]
    UpdatedLines.extend(
        LineBytes
        for LineBytes in SourceLines[1:FrontEnd]
        if not LineBytes.lstrip().startswith(b"license:")
    )
    UpdatedLines.extend(SourceLines[FrontEnd:])
    SourcePath.write_bytes(b"".join(UpdatedLines))
    return True


# unknown text formats need their existing leading marker retained during a safe replacement
def GetRepairStyle(SourceLines: list[str], StyleText: str) -> str:
    if StyleText != "unknown":
        return StyleText
    LeadOffset = GetLeadOffset(SourceLines)
    for LineText in SourceLines[LeadOffset:]:
        StrippedLine = LineText.strip()
        if not StrippedLine:
            continue
        if StrippedLine.startswith("$$"):
            return "$$"
        if StrippedLine.startswith("<!--"):
            return "block"
        return "#"
    return "#"


# repair dispatch keeps skill licensing and ordinary header mutation behind one verified contract
def RepairHeadMut(
    SourcePath: Pathlib.Path,
    CanonLines: list[str],
    WorktreeRoot: Pathlib.Path,
) -> tuple[bool, str]:
    SourceLines = ReadLines(SourcePath)
    if SourceLines is None:
        return False, "file is not readable as UTF-8 text"
    if IsAgentSkill(SourcePath, WorktreeRoot):
        if CanFixSkillMut(SourcePath):
            return True, "added Agent Skills license field"
        return False, "Agent Skills frontmatter cannot be safely repaired"
    StyleText = GetStyle(SourcePath)
    if StyleText is None:
        return False, "file has no comment syntax"
    HeaderLines = GetCandidates(StyleText, CanonLines)[0]
    if not any("SPDX-" in LineText for LineText in SourceLines):
        WriteMissingMut(SourcePath, HeaderLines)
        return True, "added missing SPDX header"
    RepairStyle = GetRepairStyle(SourceLines, StyleText)
    if CanRepairMut(SourcePath, HeaderLines, RepairStyle):
        return True, "replaced safely bounded mangled SPDX header"
    return False, "mangled SPDX header cannot be safely repaired"


# batch remediation rechecks every write so automation never publishes an unverified transformation
def RepairFilesMut(
    ChangedPaths: list[str], CanonLines: list[str], WorktreeRoot: Pathlib.Path
) -> int:
    FailureList: list[tuple[str, str]] = []
    RepairedCount = 0
    for RelPath in ChangedPaths:
        if IsPathExempt(RelPath):
            continue
        SourcePath = ResolvePath(WorktreeRoot, RelPath)
        if SourcePath is None:
            FailureList.append((RelPath, "path escapes the selected worktree"))
            print(f"FAIL {RelPath}: path escapes the selected worktree")
            continue
        if not SourcePath.is_file():
            continue
        IsValid, ReasonText = CheckFile(SourcePath, CanonLines, WorktreeRoot)
        if IsValid:
            print(f"OK   {RelPath}: {ReasonText}")
            continue
        IsFixed, RepairReason = RepairHeadMut(
            SourcePath, CanonLines, WorktreeRoot
        )
        if IsFixed:
            IsVerified, VerifyReason = CheckFile(
                SourcePath, CanonLines, WorktreeRoot
            )
            if IsVerified:
                RepairedCount += 1
                print(f"FIXED {RelPath}: {RepairReason}")
                continue
            RepairReason = VerifyReason
        FailureList.append((RelPath, RepairReason))
        print(f"FAIL {RelPath}: {RepairReason}")
    print(
        f"\nRepaired {RepairedCount} in-scope file(s); "
        f"{len(FailureList)} failure(s)."
    )
    return int(bool(FailureList))


# git diff parsing stays isolated because rename destinations are the only paths requiring validation
def GetDiffFiles(BaseRef: str, HeadRef: str) -> list[str]:
    ResultInfo = Subprocess.run(
        [
            "git",
            "diff",
            "--name-status",
            "-M",
            "--diff-filter=ACMR",
            BaseRef,
            HeadRef,
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=True,
    )
    ResultPaths: list[str] = []
    for LineText in ResultInfo.stdout.splitlines():
        FieldParts = LineText.split("\t")
        ResultPaths.append(FieldParts[-1])
    return ResultPaths


# argument parsing stays focused because command validation and repository work change independently
def ParseArgs(ArgValues: list[str] | None = None) -> Argparse.Namespace:
    ParserInfo = Argparse.ArgumentParser(description=__doc__)
    ParserInfo.add_argument(
        "--base", dest="BaseRef", required=True, help="base git reference to diff from"
    )
    ParserInfo.add_argument(
        "--head", dest="HeadRef", required=True, help="head git reference to diff to"
    )
    ParserInfo.add_argument(
        "--worktree",
        dest="WorktreeRoot",
        type=Pathlib.Path,
        default=KRepoRoot,
        help="filesystem tree whose changed files are checked or repaired",
    )
    ParserInfo.add_argument(
        "--fix-missing",
        dest="FixMissing",
        action="store_true",
        help="repair only absent or safely bounded top level SPDX metadata",
    )
    return ParserInfo.parse_args(ArgValues)


# command orchestration stays small because policy helpers own classification and validation details
def MainRun(ArgValues: list[str] | None = None) -> int:
    ArgsInfo = ParseArgs(ArgValues)
    CanonLines = LoadCanon()
    ChangedPaths = GetDiffFiles(ArgsInfo.BaseRef, ArgsInfo.HeadRef)
    WorktreeRoot = ArgsInfo.WorktreeRoot.resolve()
    if not WorktreeRoot.is_dir():
        print(f"Selected worktree is not a directory: {WorktreeRoot}", file=System.stderr)
        return 1
    if ArgsInfo.FixMissing:
        return RepairFilesMut(ChangedPaths, CanonLines, WorktreeRoot)
    FailureList: list[tuple[str, str]] = []
    CheckedCount = 0
    for RelPath in ChangedPaths:
        if IsPathExempt(RelPath):
            continue
        SourcePath = ResolvePath(WorktreeRoot, RelPath)
        if SourcePath is None:
            FailureList.append((RelPath, "path escapes the selected worktree"))
            print(f"FAIL {RelPath}: path escapes the selected worktree")
            continue
        if not SourcePath.is_file():
            continue
        CheckedCount += 1
        IsValid, ReasonText = CheckFile(SourcePath, CanonLines, WorktreeRoot)
        if not IsValid:
            FailureList.append((RelPath, ReasonText))
        StatusText = "OK " if IsValid else "FAIL"
        print(f"{StatusText} {RelPath}: {ReasonText}")
    print(f"\nChecked {CheckedCount} in-scope file(s); {len(FailureList)} failure(s).")
    if FailureList:
        print(
            "\nOne or more changed files are missing or have a modified required SPDX header",
            file=System.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())

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
import re as Regex
import stat as StatLib
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

# complete commit identifiers keep diff and worktree selection free from revision expression ambiguity
KFullShaPattern = Regex.compile(r"\A[0-9a-f]{40}\Z")

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
        if StyleText == "unknown":
            return True, "exempt (unknown format is not readable as UTF-8 text)"
        return False, "known text format is not readable as UTF-8"
    CandidateSets = GetCandidates(StyleText, CanonLines)
    return MatchHeader(SourceLines, GetLeadOffset(SourceLines), CandidateSets)


# commit predicates prevent revision syntax from selecting anything other than an exact commit object
def IsCommit(ShaText: str) -> bool:
    if KFullShaPattern.fullmatch(ShaText) is None:
        return False
    ResultInfo = Subprocess.run(
        ["git", "cat-file", "-t", ShaText],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
    )
    return ResultInfo.returncode == 0 and ResultInfo.stdout.strip() == "commit"


# byte path decoding rejects ambiguous platform syntax before any filesystem access can occur
def DecodePath(PathBytes: bytes) -> str:
    try:
        PathText = PathBytes.decode("utf-8")
    except UnicodeDecodeError as ErrorInfo:
        raise ValueError("git diff contains a non UTF-8 path") from ErrorInfo
    PosixPath = Pathlib.PurePosixPath(PathText)
    WinPath = Pathlib.PureWindowsPath(PathText)
    IsControl = any(ord(CharText) < 32 for CharText in PathText)
    IsInvalid = (
        not PathText
        or "\\" in PathText
        or ":" in PathText
        or "\x00" in PathText
        or IsControl
        or PosixPath.is_absolute()
        or bool(WinPath.drive)
        or ".." in PosixPath.parts
        or PathText != PosixPath.as_posix()
    )
    if IsInvalid:
        raise ValueError(f"git diff contains a noncanonical path: {PathText!r}")
    return PathText


# nul parsing preserves rename boundaries while rejecting malformed status records and duplicate destinations
def ParseDiff(DiffBytes: bytes) -> list[str]:
    DiffFields = DiffBytes.split(b"\0")
    if not DiffFields or DiffFields[-1] != b"":
        raise ValueError("git diff name status output is not NUL terminated")
    DiffFields.pop()
    ResultPaths: list[str] = []
    SeenPaths: set[str] = set()
    FieldIndex = 0
    while FieldIndex < len(DiffFields):
        try:
            StatusText = DiffFields[FieldIndex].decode("ascii")
        except UnicodeDecodeError as ErrorInfo:
            raise ValueError("git diff contains a non ASCII status") from ErrorInfo
        FieldIndex += 1
        IsRename = Regex.fullmatch(r"[RC][0-9]{1,3}", StatusText) is not None
        if not IsRename and StatusText not in {"A", "M"}:
            raise ValueError(f"git diff contains an unexpected status: {StatusText!r}")
        PathCount = 2 if IsRename else 1
        if FieldIndex + PathCount > len(DiffFields):
            raise ValueError("git diff contains a truncated status record")
        PathFields = DiffFields[FieldIndex : FieldIndex + PathCount]
        FieldIndex += PathCount
        for PathBytes in PathFields:
            DecodePath(PathBytes)
        TargetPath = DecodePath(PathFields[-1])
        if TargetPath in SeenPaths:
            raise ValueError(f"git diff repeats a destination path: {TargetPath!r}")
        SeenPaths.add(TargetPath)
        ResultPaths.append(TargetPath)
    return ResultPaths


# exact worktree validation ensures untrusted pull request files remain detached data at the expected commit
def CheckWorktree(
    WorktreePath: Pathlib.Path, HeadRef: str
) -> tuple[Pathlib.Path | None, str]:
    LexicalRoot = WorktreePath.absolute()
    try:
        WorktreeRoot = WorktreePath.resolve(strict=True)
    except OSError:
        return None, "selected worktree does not exist"
    if LexicalRoot != WorktreeRoot or not WorktreeRoot.is_dir():
        return None, "selected worktree is symlinked or is not a directory"
    ResultInfo = Subprocess.run(
        ["git", "-C", str(WorktreeRoot), "rev-parse", "--show-toplevel", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    ResultLines = ResultInfo.stdout.splitlines()
    if ResultInfo.returncode != 0 or len(ResultLines) != 2:
        return None, "selected directory is not a valid git worktree"
    try:
        GitRoot = Pathlib.Path(ResultLines[0]).resolve(strict=True)
    except OSError:
        return None, "selected git worktree root cannot be resolved"
    if GitRoot != WorktreeRoot:
        return None, "selected path is not the exact git worktree root"
    if ResultLines[1] != HeadRef:
        return None, "selected worktree HEAD does not match the requested head commit"
    return WorktreeRoot, "selected worktree matches the requested head commit"


# containment validation rejects missing symlinked and nonregular candidates before content inspection
def ResolvePath(
    WorktreeRoot: Pathlib.Path, RelPath: str
) -> Pathlib.Path | None:
    PosixPath = Pathlib.PurePosixPath(RelPath)
    CandidatePath = WorktreeRoot.joinpath(*PosixPath.parts)
    CurrentPath = WorktreeRoot
    try:
        for PartText in PosixPath.parts:
            CurrentPath = CurrentPath / PartText
            PathInfo = CurrentPath.lstat()
            if StatLib.S_ISLNK(PathInfo.st_mode):
                return None
        ResolvedPath = CandidatePath.resolve(strict=True)
    except OSError:
        return None
    try:
        ResolvedPath.relative_to(WorktreeRoot)
    except ValueError:
        return None
    if ResolvedPath != CandidatePath.absolute():
        return None
    if not StatLib.S_ISREG(CandidatePath.lstat().st_mode):
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


# unknown text formats need a proven existing leading marker before any replacement is allowed
def GetRepairStyle(SourceLines: list[str], StyleText: str) -> str | None:
    if StyleText != "unknown":
        return StyleText
    LeadOffset = GetLeadOffset(SourceLines)
    if LeadOffset >= len(SourceLines):
        return None
    StrippedLine = SourceLines[LeadOffset].strip()
    if StrippedLine.startswith("$$"):
        return "$$"
    if StrippedLine == "<!--":
        return "block"
    if StrippedLine.startswith("#"):
        return "#"
    return None


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
    if not any("SPDX-" in LineText for LineText in SourceLines):
        if StyleText == "unknown":
            return False, "unknown text style cannot receive a guessed header"
        HeaderLines = GetCandidates(StyleText, CanonLines)[0]
        WriteMissingMut(SourcePath, HeaderLines)
        return True, "added missing SPDX header"
    RepairStyle = GetRepairStyle(SourceLines, StyleText)
    if RepairStyle is None:
        return False, "mangled SPDX header style cannot be proven"
    HeaderLines = (
        RenderBlock(CanonLines)
        if RepairStyle == "block"
        else RenderLines(CanonLines, RepairStyle)
    )
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
            RepairReason = "path is missing symlinked or nonregular"
            FailureList.append((RelPath, RepairReason))
            print(f"FAIL {RelPath!r}: {RepairReason}")
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
    if not IsCommit(BaseRef) or not IsCommit(HeadRef):
        raise ValueError("base and head must be full commit object identifiers")
    ResultInfo = Subprocess.run(
        [
            "git",
            "diff",
            "--name-status",
            "-z",
            "--no-ext-diff",
            "--no-textconv",
            "-M",
            "--diff-filter=ACMR",
            BaseRef,
            HeadRef,
            "--",
        ],
        cwd=KRepoRoot,
        capture_output=True,
        check=True,
    )
    return ParseDiff(ResultInfo.stdout)


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
    if not IsCommit(ArgsInfo.BaseRef) or not IsCommit(ArgsInfo.HeadRef):
        print("Base and head must be full commit object identifiers", file=System.stderr)
        return 1
    WorktreeRoot, WorktreeReason = CheckWorktree(
        ArgsInfo.WorktreeRoot, ArgsInfo.HeadRef
    )
    if WorktreeRoot is None:
        print(WorktreeReason, file=System.stderr)
        return 1
    CanonLines = LoadCanon()
    ChangedPaths = GetDiffFiles(ArgsInfo.BaseRef, ArgsInfo.HeadRef)
    if ArgsInfo.FixMissing:
        return RepairFilesMut(ChangedPaths, CanonLines, WorktreeRoot)
    FailureList: list[tuple[str, str]] = []
    CheckedCount = 0
    for RelPath in ChangedPaths:
        if IsPathExempt(RelPath):
            continue
        SourcePath = ResolvePath(WorktreeRoot, RelPath)
        if SourcePath is None:
            FailureList.append((RelPath, "path is missing symlinked or nonregular"))
            print(f"FAIL {RelPath!r}: path is missing symlinked or nonregular")
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

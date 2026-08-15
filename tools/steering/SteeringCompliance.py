# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import argparse as Argparse
import ast as AstLib
import io as IoStream
import re as Regex
import sys as System
import tokenize as Tokenize
from dataclasses import dataclass as DataClass
from pathlib import Path as FilePath

# exact notice stays embedded so checks remain independent from local repository state
KPythonHeader = """# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.
"""

# generated and third party folders stay excluded because repository scans must remain actionable
KSkipFolders = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".rescratch",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "venv",
    }
)

# known destructive methods stay centralized because static mutation inference needs safe evidence
KMutatorNames = frozenset(
    {
        "add",
        "append",
        "clear",
        "difference_update",
        "discard",
        "extend",
        "insert",
        "intersection_update",
        "pop",
        "popitem",
        "remove",
        "reverse",
        "seek",
        "setdefault",
        "sort",
        "symmetric_difference_update",
        "truncate",
        "update",
        "write",
        "writelines",
    }
)

# mechanical lead verbs stay explicit because bare operation summaries are not rationales
KMechanicalWords = frozenset(
    {
        "adds",
        "appends",
        "builds",
        "calculates",
        "checks",
        "creates",
        "deletes",
        "gets",
        "iterates",
        "loads",
        "loops",
        "multiplies",
        "parses",
        "reads",
        "removes",
        "returns",
        "sets",
        "sorts",
        "stores",
        "updates",
        "validates",
        "writes",
    }
)

# causal vocabulary permits operation wording when the comment also states its purpose
KPurposeWords = frozenset(
    {
        "allow",
        "allows",
        "avoid",
        "avoids",
        "because",
        "enable",
        "enables",
        "ensure",
        "ensures",
        "instead",
        "must",
        "need",
        "needed",
        "needs",
        "otherwise",
        "preserve",
        "preserves",
        "prevent",
        "prevents",
        "protect",
        "protects",
        "requested",
        "since",
        "so",
        "unless",
    }
)

# permitted type comments remain explicit because static typing metadata is not explanatory code commentary
KPragmaPrefixes = (
    "mypy:",
    "pyre-ignore",
    "pyright:",
    "type:",
)

# type alias wrappers stay explicit because boolean contracts may retain metadata without changing their result
KBoolTypeWraps = frozenset({"Annotated", "Final", "Required", "NotRequired"})

# type narrowing annotations stay explicit because their runtime result is always boolean
KBoolTypeReturns = frozenset({"TypeGuard", "TypeIs"})

# forbidden vocabulary stays centralized because rationale comments cannot excuse incomplete work
KStubWords = frozenset({"fixme", "placeholder", "stub", "todo"})


# structured findings keep diagnostics deterministic because command line and test consumers share results
@DataClass(frozen=True, order=True, slots=True)
class Finding:
    SourcePath: FilePath
    LineNum: int
    ColNum: int
    RuleCode: str
    MsgText: str


# dunder recognition preserves names reserved by the python data model
def IsDunderName(NameText: str) -> bool:
    return len(NameText) > 4 and NameText.startswith("__") and NameText.endswith("__")


# one predicate keeps every identifier category on the exact shared casing rules
def IsValidName(NameText: str, KindText: str) -> bool:
    MinLength, MaxLength = (5, 15) if KindText in {"class", "function"} else (5, 25)
    return bool(Regex.fullmatch(r"[A-Z][a-zA-Z]*", NameText)) and (
        MinLength <= len(NameText) <= MaxLength
    )


# a single constructor keeps all naming diagnostics precise and consistently phrased
def CheckName(
    SourcePath: FilePath,
    AstNode: AstLib.AST,
    NameText: str,
    KindText: str,
) -> Finding | None:
    if IsDunderName(NameText):
        return None
    if IsValidName(NameText, KindText):
        return None
    MinLength, MaxLength = (5, 15) if KindText in {"class", "function"} else (5, 25)
    MsgText = (
        f"{KindText} identifier {NameText!r} must be PascalCase ASCII letters "
        f"with length {MinLength} through {MaxLength}"
    )
    return Finding(
        SourcePath,
        getattr(AstNode, "lineno", 1),
        getattr(AstNode, "col_offset", 0) + 1,
        "NAM001",
        MsgText,
    )


# complete argument collection prevents alternate parameter forms from escaping checks
def GetFuncArgs(
    FuncNode: AstLib.FunctionDef | AstLib.AsyncFunctionDef,
) -> list[AstLib.arg]:
    ArgList = [*FuncNode.args.posonlyargs, *FuncNode.args.args]
    ArgList.extend(FuncNode.args.kwonlyargs)
    if FuncNode.args.vararg is not None:
        ArgList.append(FuncNode.args.vararg)
    if FuncNode.args.kwarg is not None:
        ArgList.append(FuncNode.args.kwarg)
    return ArgList


# declaration checks stay unified because public and nested definitions share naming constraints
def CheckDefs(SourcePath: FilePath, SyntaxTree: AstLib.Module) -> list[Finding]:
    FindingList: list[Finding] = []
    for AstNode in AstLib.walk(SyntaxTree):
        FindingInfo = None
        if isinstance(AstNode, AstLib.ClassDef):
            FindingInfo = CheckName(SourcePath, AstNode, AstNode.name, "class")
        elif isinstance(AstNode, (AstLib.FunctionDef, AstLib.AsyncFunctionDef)):
            FindingInfo = CheckName(SourcePath, AstNode, AstNode.name, "function")
            for ArgNode in GetFuncArgs(AstNode):
                ArgFinding = CheckName(SourcePath, ArgNode, ArgNode.arg, "argument")
                if ArgFinding is not None:
                    FindingList.append(ArgFinding)
        elif isinstance(AstNode, AstLib.Lambda):
            for ArgNode in [
                *AstNode.args.posonlyargs,
                *AstNode.args.args,
                *AstNode.args.kwonlyargs,
            ]:
                ArgFinding = CheckName(SourcePath, ArgNode, ArgNode.arg, "argument")
                if ArgFinding is not None:
                    FindingList.append(ArgFinding)
            for OptionalArg in (AstNode.args.vararg, AstNode.args.kwarg):
                if OptionalArg is not None:
                    ArgFinding = CheckName(
                        SourcePath, OptionalArg, OptionalArg.arg, "argument"
                    )
                    if ArgFinding is not None:
                        FindingList.append(ArgFinding)
        if FindingInfo is not None:
            FindingList.append(FindingInfo)
    return FindingList


# stored binding checks stay unified because every writable identifier follows one convention
def CheckStores(SourcePath: FilePath, SyntaxTree: AstLib.Module) -> list[Finding]:
    FindingList: list[Finding] = []
    for AstNode in AstLib.walk(SyntaxTree):
        NameText = None
        KindText = "variable"
        if isinstance(AstNode, AstLib.Name) and isinstance(
            AstNode.ctx, (AstLib.Store, AstLib.Del)
        ):
            NameText = AstNode.id
        elif isinstance(AstNode, AstLib.Attribute) and isinstance(
            AstNode.ctx, (AstLib.Store, AstLib.Del)
        ):
            NameText = AstNode.attr
            KindText = "attribute"
        elif isinstance(AstNode, AstLib.ExceptHandler) and AstNode.name:
            NameText = AstNode.name
        elif isinstance(AstNode, (AstLib.MatchAs, AstLib.MatchStar)) and AstNode.name:
            NameText = AstNode.name
        elif isinstance(AstNode, AstLib.MatchMapping) and AstNode.rest:
            NameText = AstNode.rest
        if NameText is not None:
            FindingInfo = CheckName(SourcePath, AstNode, NameText, KindText)
            if FindingInfo is not None:
                FindingList.append(FindingInfo)
    return FindingList


# wildcard checks stay separate because exact dependency ownership needs explicit merge failures
def CheckStarImport(SourcePath: FilePath, SyntaxTree: AstLib.Module) -> list[Finding]:
    FindingList: list[Finding] = []
    for ImportNode in AstLib.walk(SyntaxTree):
        if not isinstance(ImportNode, AstLib.ImportFrom):
            continue
        for AliasInfo in ImportNode.names:
            if AliasInfo.name != "*":
                continue
            FindingList.append(
                Finding(
                    SourcePath,
                    AliasInfo.lineno,
                    AliasInfo.col_offset + 1,
                    "IMP001",
                    "wildcard imports are forbidden use exact symbol imports",
                )
            )
    return FindingList


# import binding checks prevent noncompliant aliases because imports create locally controlled identifiers
def CheckImports(SourcePath: FilePath, SyntaxTree: AstLib.Module) -> list[Finding]:
    FindingList: list[Finding] = []
    for AstNode in AstLib.walk(SyntaxTree):
        if isinstance(AstNode, AstLib.Import):
            AliasList = AstNode.names
        elif isinstance(AstNode, AstLib.ImportFrom) and AstNode.module != "__future__":
            AliasList = AstNode.names
        else:
            continue
        for AliasInfo in AliasList:
            if AliasInfo.name == "*":
                continue
            NameText = AliasInfo.asname or AliasInfo.name.split(".", 1)[0]
            FindingInfo = CheckName(SourcePath, AliasInfo, NameText, "import")
            if FindingInfo is not None:
                FindingList.append(FindingInfo)
    return FindingList


# combined naming results stay unified because callers need one entry point for every category
def CheckNames(SourcePath: FilePath, SyntaxTree: AstLib.Module) -> list[Finding]:
    return [
        *CheckDefs(SourcePath, SyntaxTree),
        *CheckStores(SourcePath, SyntaxTree),
        *CheckStarImport(SourcePath, SyntaxTree),
        *CheckImports(SourcePath, SyntaxTree),
    ]


# parent links exist because scope and containing statement analysis needs upward traversal
def BuildParents(SyntaxTree: AstLib.Module) -> dict[AstLib.AST, AstLib.AST]:
    ParentMap: dict[AstLib.AST, AstLib.AST] = {}
    for ParentNode in AstLib.walk(SyntaxTree):
        for ChildNode in AstLib.iter_child_nodes(ParentNode):
            ParentMap[ChildNode] = ParentNode
    return ParentMap


# simple syntax names support decorator base and annotation classification without resolving imports
def GetSyntaxName(AstNode: AstLib.AST | None) -> str | None:
    if isinstance(AstNode, AstLib.Name):
        return AstNode.id
    if isinstance(AstNode, AstLib.Attribute):
        return AstNode.attr
    return None


# nearest lexical ownership keeps nested bindings out of surrounding constant analysis
def FindScope(
    AstNode: AstLib.AST, ParentMap: dict[AstLib.AST, AstLib.AST]
) -> AstLib.AST | None:
    ParentNode = ParentMap.get(AstNode)
    ScopeTypes = (
        AstLib.Module,
        AstLib.ClassDef,
        AstLib.FunctionDef,
        AstLib.AsyncFunctionDef,
        AstLib.Lambda,
        AstLib.ListComp,
        AstLib.SetComp,
        AstLib.DictComp,
        AstLib.GeneratorExp,
    )
    while ParentNode is not None and not isinstance(ParentNode, ScopeTypes):
        ParentNode = ParentMap.get(ParentNode)
    return ParentNode


# write grouping exists because constants differ from reassigned module and class state
def CollectWrites(
    SyntaxTree: AstLib.Module, ParentMap: dict[AstLib.AST, AstLib.AST]
) -> dict[tuple[AstLib.AST, str], list[AstLib.Name]]:
    WriteMap: dict[tuple[AstLib.AST, str], list[AstLib.Name]] = {}
    for AstNode in AstLib.walk(SyntaxTree):
        if not isinstance(AstNode, AstLib.Name) or not isinstance(
            AstNode.ctx, (AstLib.Store, AstLib.Del)
        ):
            continue
        ParentNode = ParentMap.get(AstNode)
        while isinstance(ParentNode, (AstLib.Tuple, AstLib.List, AstLib.Starred)):
            ParentNode = ParentMap.get(ParentNode)
        if isinstance(ParentNode, AstLib.AnnAssign) and ParentNode.value is None:
            continue
        ScopeNode = FindScope(AstNode, ParentMap)
        if isinstance(ScopeNode, (AstLib.Module, AstLib.ClassDef)):
            WriteMap.setdefault((ScopeNode, AstNode.id), []).append(AstNode)
    return WriteMap


# fixed write detection prevents mutation targets because constants need one value bearing assignment
def IsFixedWrite(
    NameNode: AstLib.Name, ParentMap: dict[AstLib.AST, AstLib.AST]
) -> bool:
    CurrentNode: AstLib.AST = NameNode
    ParentNode = ParentMap.get(CurrentNode)
    while isinstance(ParentNode, (AstLib.Tuple, AstLib.List, AstLib.Starred)):
        CurrentNode = ParentNode
        ParentNode = ParentMap.get(CurrentNode)
    if isinstance(ParentNode, AstLib.Assign):
        return True
    return isinstance(ParentNode, AstLib.AnnAssign) and ParentNode.value is not None


# field container recognition prevents instance schema members from masquerading as class constants
def IsFieldClass(ClassNode: AstLib.ClassDef) -> bool:
    if any(GetSyntaxName(BaseNode) == "NamedTuple" for BaseNode in ClassNode.bases):
        return True
    for DecoratorNode in ClassNode.decorator_list:
        TargetNode = (
            DecoratorNode.func
            if isinstance(DecoratorNode, AstLib.Call)
            else DecoratorNode
        )
        if GetSyntaxName(TargetNode) in {"dataclass", "DataClass"}:
            return True
    return False


# class variable annotations distinguish shared constants from dataclass and named tuple instance fields
def IsClassVarAnnot(AnnotNode: AstLib.AST | None) -> bool:
    if GetSyntaxName(AnnotNode) == "ClassVar":
        return True
    return isinstance(AnnotNode, AstLib.Subscript) and (
        GetSyntaxName(AnnotNode.value) == "ClassVar"
    )


# schema field detection excludes instance declarations while retaining explicit class variables
def IsInstanceField(
    NameNode: AstLib.Name,
    ScopeNode: AstLib.AST,
    ParentMap: dict[AstLib.AST, AstLib.AST],
) -> bool:
    if not isinstance(ScopeNode, AstLib.ClassDef) or not IsFieldClass(ScopeNode):
        return False
    ParentNode = ParentMap.get(NameNode)
    while isinstance(ParentNode, (AstLib.Tuple, AstLib.List, AstLib.Starred)):
        ParentNode = ParentMap.get(ParentNode)
    if not isinstance(ParentNode, AstLib.AnnAssign):
        return False
    return not IsClassVarAnnot(ParentNode.annotation)


# constant checks preserve markers because misleading prefixed globals obscure runtime state
def CheckConstants(
    SourcePath: FilePath,
    SyntaxTree: AstLib.Module,
    ParentMap: dict[AstLib.AST, AstLib.AST],
) -> list[Finding]:
    FindingList: list[Finding] = []
    for (ScopeNode, NameText), WriteNodes in CollectWrites(
        SyntaxTree, ParentMap
    ).items():
        if IsDunderName(NameText) or all(
            IsInstanceField(NameNode, ScopeNode, ParentMap) for NameNode in WriteNodes
        ):
            continue
        IsConstant = len(WriteNodes) == 1 and IsFixedWrite(WriteNodes[0], ParentMap)
        if IsConstant and not NameText.startswith("K"):
            RuleCode = "CON001"
            MsgText = f"constant {NameText!r} must start with K"
        elif not IsConstant and NameText.startswith("K"):
            RuleCode = "CON002"
            MsgText = f"reassigned binding {NameText!r} must not start with K"
        else:
            continue
        NameNode = min(WriteNodes, key=GetNodePos)
        FindingList.append(
            Finding(
                SourcePath, NameNode.lineno, NameNode.col_offset + 1, RuleCode, MsgText
            )
        )
    return FindingList


# node position keys keep diagnostics stable because anonymous callbacks require rationale comments
def GetNodePos(AstNode: AstLib.AST) -> tuple[int, int]:
    return (
        getattr(AstNode, "lineno", 1),
        getattr(AstNode, "col_offset", 0),
    )


# declaration starts include decorators because rationale comments belong above the complete stack
def GetStartPos(AstNode: AstLib.AST) -> tuple[int, int]:
    DecoratorList = getattr(AstNode, "decorator_list", [])
    if DecoratorList:
        StartLine = min(GetNodePos(EntryNode)[0] for EntryNode in DecoratorList)
        return StartLine, getattr(AstNode, "col_offset", 0)
    return GetNodePos(AstNode)


# statement lookup exists because inline lambdas share rationale with their full statement
def FindStatement(
    AstNode: AstLib.AST, ParentMap: dict[AstLib.AST, AstLib.AST]
) -> AstLib.stmt | None:
    CurrentNode: AstLib.AST | None = AstNode
    while CurrentNode is not None and not isinstance(CurrentNode, AstLib.stmt):
        CurrentNode = ParentMap.get(CurrentNode)
    return CurrentNode


# value bearing module assignments need rationale because annotations alone define no runtime state
def IsModuleBinding(
    AstNode: AstLib.Assign | AstLib.AnnAssign,
    ParentMap: dict[AstLib.AST, AstLib.AST],
) -> bool:
    if not isinstance(FindScope(AstNode, ParentMap), AstLib.Module):
        return False
    return AstNode.value is not None


# rationale sites merge because multiple lambdas may legitimately share one source statement
def FindReasonSites(
    SyntaxTree: AstLib.Module, ParentMap: dict[AstLib.AST, AstLib.AST]
) -> list[tuple[int, int, str]]:
    SiteMap: dict[tuple[int, int], str] = {}
    for AstNode in AstLib.walk(SyntaxTree):
        TargetNode: AstLib.stmt | None = None
        KindText = "declaration"
        if isinstance(
            AstNode, (AstLib.ClassDef, AstLib.FunctionDef, AstLib.AsyncFunctionDef)
        ):
            TargetNode = AstNode
        elif isinstance(AstNode, AstLib.Lambda):
            TargetNode = FindStatement(AstNode, ParentMap)
            KindText = "lambda"
        elif isinstance(AstNode, (AstLib.Assign, AstLib.AnnAssign)) and IsModuleBinding(
            AstNode, ParentMap
        ):
            TargetNode = AstNode
            KindText = "module binding"
        if TargetNode is not None:
            LineNum, ColNum = GetStartPos(TargetNode)
            SiteMap.setdefault((LineNum, ColNum), KindText)
    return [(*SitePos, KindText) for SitePos, KindText in sorted(SiteMap.items())]


# strict text validation stays centralized because rationale syntax has several exact requirements
def FindReasonError(CommentText: str) -> str | None:
    WordList = CommentText.split()
    if not 5 <= len(WordList) <= 25:
        return "rationale must contain between 5 and 25 whitespace separated words"
    if CommentText != CommentText.lower():
        return "rationale must use lowercase text only"
    if any(not (CharText.isalnum() or CharText.isspace()) for CharText in CommentText):
        return "rationale must not contain punctuation or symbols"
    if set(WordList) & KStubWords:
        return "rationale must not contain placeholder language"
    return None


# purpose recognition rejects obvious mechanics because rationale comments must answer why
def IsPurposeText(CommentText: str) -> bool:
    WordList = CommentText.split()
    if not WordList or WordList[0] not in KMechanicalWords:
        return True
    return bool(set(WordList) & KPurposeWords)


# one site check ensures callers receive the most actionable rationale failure available
def CheckReason(
    SourcePath: FilePath,
    SourceLines: list[str],
    LineNum: int,
    ColNum: int,
    KindText: str,
) -> Finding | None:
    CommentIndex = LineNum - 2
    if CommentIndex < 0:
        return Finding(
            SourcePath,
            LineNum,
            ColNum + 1,
            "RAT001",
            f"{KindText} needs a rationale comment",
        )
    IndentText = " " * ColNum
    MatchInfo = Regex.fullmatch(
        Regex.escape(IndentText) + r"# (.*)", SourceLines[CommentIndex]
    )
    if MatchInfo is None:
        return Finding(
            SourcePath,
            LineNum,
            ColNum + 1,
            "RAT001",
            f"{KindText} needs one immediate rationale comment",
        )
    if CommentIndex == 0 or SourceLines[CommentIndex - 1].strip():
        return Finding(
            SourcePath,
            CommentIndex + 1,
            ColNum + 1,
            "RAT002",
            "rationale comment needs a blank line immediately before it",
        )
    CommentText = MatchInfo.group(1)
    ErrorText = FindReasonError(CommentText)
    if ErrorText is not None:
        return Finding(SourcePath, CommentIndex + 1, ColNum + 1, "RAT003", ErrorText)
    if not IsPurposeText(CommentText):
        return Finding(
            SourcePath,
            CommentIndex + 1,
            ColNum + 1,
            "RAT004",
            "rationale describes mechanics without explaining purpose",
        )
    return None


# complete rationale traversal exists because every required site needs identical placement rules
def CheckReasons(
    SourcePath: FilePath,
    SourceText: str,
    SyntaxTree: AstLib.Module,
    ParentMap: dict[AstLib.AST, AstLib.AST],
) -> list[Finding]:
    SourceLines = SourceText.splitlines()
    FindingList: list[Finding] = []
    for LineNum, ColNum, KindText in FindReasonSites(SyntaxTree, ParentMap):
        FindingInfo = CheckReason(SourcePath, SourceLines, LineNum, ColNum, KindText)
        if FindingInfo is not None:
            FindingList.append(FindingInfo)
    return FindingList


# encoding and tool directives remain allowed because they configure parsers rather than explain implementation
def IsPragmaComment(TokenInfo: Tokenize.TokenInfo) -> bool:
    CommentText = TokenInfo.string[1:].strip().lower()
    if TokenInfo.start == (1, 0) and TokenInfo.string.startswith("#!"):
        return True
    if TokenInfo.start[0] <= 2 and Regex.fullmatch(
        r"coding[:=][ \t]*[-\w.]+", CommentText
    ):
        return True
    return any(CommentText.startswith(PrefixText) for PrefixText in KPragmaPrefixes)


# exact license token positions protect only the required notice instead of exempting arbitrary spdx commentary
def IsHeaderComment(TokenInfo: Tokenize.TokenInfo, StartLine: int) -> bool:
    HeaderLines = KPythonHeader.splitlines()
    LineOffset = TokenInfo.start[0] - StartLine
    return (
        TokenInfo.start[1] == 0
        and 0 <= LineOffset < len(HeaderLines)
        and TokenInfo.line.rstrip("\r\n") == HeaderLines[LineOffset]
    )


# rationale positions identify the single comments that may explain required declarations
def GetReasonLines(
    SyntaxTree: AstLib.Module, ParentMap: dict[AstLib.AST, AstLib.AST]
) -> set[tuple[int, int]]:
    return {
        (LineNum - 1, ColNum)
        for LineNum, ColNum, KindText in FindReasonSites(SyntaxTree, ParentMap)
        if KindText
    }


# comment enforcement preserves only steering mandated rationales license text and parser pragmas
def CheckComments(
    SourcePath: FilePath,
    SourceText: str,
    SyntaxTree: AstLib.Module,
    ParentMap: dict[AstLib.AST, AstLib.AST],
) -> list[Finding]:
    TokenList = list(Tokenize.generate_tokens(IoStream.StringIO(SourceText).readline))
    ReasonLines = GetReasonLines(SyntaxTree, ParentMap)
    SourceLines = SourceText.splitlines()
    StartLine = 2 if SourceLines and SourceLines[0].startswith("#!") else 1
    FindingList: list[Finding] = []
    for TokenInfo in TokenList:
        if TokenInfo.type != Tokenize.COMMENT:
            continue
        TokenPos = (TokenInfo.start[0], TokenInfo.start[1])
        if (
            TokenPos in ReasonLines
            or IsHeaderComment(TokenInfo, StartLine)
            or IsPragmaComment(TokenInfo)
        ):
            continue
        MsgText = "code comment is not an allowed rationale license line or type pragma"
        FindingList.append(
            Finding(
                SourcePath,
                TokenInfo.start[0],
                TokenInfo.start[1] + 1,
                "CMT001",
                MsgText,
            )
        )
    return FindingList


# owned traversal excludes nested declarations so return and mutation inference stays local
def GetOwnedNodes(AstNode: AstLib.AST) -> list[AstLib.AST]:
    OwnedNodes: list[AstLib.AST] = []
    PendingNodes = list(AstLib.iter_child_nodes(AstNode))
    ScopeTypes = (
        AstLib.ClassDef,
        AstLib.FunctionDef,
        AstLib.AsyncFunctionDef,
        AstLib.Lambda,
    )
    while PendingNodes:
        ChildNode = PendingNodes.pop()
        if isinstance(ChildNode, ScopeTypes):
            continue
        OwnedNodes.append(ChildNode)
        PendingNodes.extend(AstLib.iter_child_nodes(ChildNode))
    return OwnedNodes


# boolean annotation recognition stays centralized because python exposes several equivalent forms
def IsBoolAnnot(AnnotNode: AstLib.AST | None) -> bool:
    if isinstance(AnnotNode, AstLib.Name):
        return AnnotNode.id == "bool"
    if isinstance(AnnotNode, AstLib.Attribute):
        return AnnotNode.attr == "bool"
    if isinstance(AnnotNode, AstLib.Constant) and isinstance(AnnotNode.value, str):
        try:
            ParsedNode = AstLib.parse(AnnotNode.value.strip(), mode="eval").body
        except SyntaxError:
            return False
        return IsBoolAnnot(ParsedNode)
    if isinstance(AnnotNode, AstLib.Subscript):
        BaseName = GetSyntaxName(AnnotNode.value)
        SliceNode = AnnotNode.slice
        ValueNodes = (
            SliceNode.elts if isinstance(SliceNode, AstLib.Tuple) else [SliceNode]
        )
        if BaseName == "Literal":
            return bool(ValueNodes) and all(
                isinstance(ValueNode, AstLib.Constant)
                and isinstance(ValueNode.value, bool)
                for ValueNode in ValueNodes
            )
        if BaseName in KBoolTypeReturns:
            return True
        if BaseName in KBoolTypeWraps and ValueNodes:
            return IsBoolAnnot(ValueNodes[0])
    return False


# return inference stays conservative because marker diagnostics require statically proven boolean results
def IsBoolReturn(FuncNode: AstLib.FunctionDef | AstLib.AsyncFunctionDef) -> bool:
    if IsBoolAnnot(FuncNode.returns):
        return True
    ReturnNodes = [
        AstNode
        for AstNode in GetOwnedNodes(FuncNode)
        if isinstance(AstNode, AstLib.Return)
    ]
    return bool(ReturnNodes) and all(
        isinstance(ReturnNode.value, AstLib.Constant)
        and isinstance(ReturnNode.value.value, bool)
        for ReturnNode in ReturnNodes
    )


# decorator matching exists because static methods lack receiver based mutation exemptions
def HasDecorator(
    FuncNode: AstLib.FunctionDef | AstLib.AsyncFunctionDef, NameText: str
) -> bool:
    for DecoratorNode in FuncNode.decorator_list:
        TargetNode = (
            DecoratorNode.func
            if isinstance(DecoratorNode, AstLib.Call)
            else DecoratorNode
        )
        if isinstance(TargetNode, AstLib.Name) and TargetNode.id == NameText:
            return True
        if isinstance(TargetNode, AstLib.Attribute) and TargetNode.attr == NameText:
            return True
    return False


# lexical ownership matters because only true methods receive receiver mutation exemptions
def IsClassMethod(
    FuncNode: AstLib.FunctionDef | AstLib.AsyncFunctionDef,
    ParentMap: dict[AstLib.AST, AstLib.AST],
) -> bool:
    ParentNode = ParentMap.get(FuncNode)
    while ParentNode is not None:
        if isinstance(ParentNode, AstLib.ClassDef):
            return True
        if isinstance(
            ParentNode, (AstLib.FunctionDef, AstLib.AsyncFunctionDef, AstLib.Lambda)
        ):
            return False
        ParentNode = ParentMap.get(ParentNode)
    return False


# relevant argument collection excludes ordinary receivers because their mutation is expected
def GetArgNames(
    FuncNode: AstLib.FunctionDef | AstLib.AsyncFunctionDef,
    ParentMap: dict[AstLib.AST, AstLib.AST],
) -> set[str]:
    ArgNodes = GetFuncArgs(FuncNode)
    PositionalNodes = [*FuncNode.args.posonlyargs, *FuncNode.args.args]
    ReceiverName = None
    if IsClassMethod(FuncNode, ParentMap) and not HasDecorator(
        FuncNode, "staticmethod"
    ):
        if PositionalNodes:
            ReceiverName = PositionalNodes[0].arg
    return {ArgNode.arg for ArgNode in ArgNodes if ArgNode.arg != ReceiverName}


# root extraction exists because nested writes must connect back to their argument
def GetRootName(AstNode: AstLib.AST | None) -> str | None:
    CurrentNode = AstNode
    while isinstance(CurrentNode, (AstLib.Attribute, AstLib.Subscript, AstLib.Starred)):
        if isinstance(CurrentNode, AstLib.Attribute):
            CurrentNode = CurrentNode.value
        elif isinstance(CurrentNode, AstLib.Subscript):
            CurrentNode = CurrentNode.value
        else:
            CurrentNode = CurrentNode.value
    return CurrentNode.id if isinstance(CurrentNode, AstLib.Name) else None


# mutation discovery combines syntax because several operations can destructively change arguments
def FindMutations(
    FuncNode: AstLib.FunctionDef | AstLib.AsyncFunctionDef,
    ParentMap: dict[AstLib.AST, AstLib.AST],
) -> set[str]:
    ArgNames = GetArgNames(FuncNode, ParentMap)
    MutatedNames: set[str] = set()
    for AstNode in GetOwnedNodes(FuncNode):
        RootName = None
        if isinstance(AstNode, (AstLib.Attribute, AstLib.Subscript)) and isinstance(
            AstNode.ctx, (AstLib.Store, AstLib.Del)
        ):
            RootName = GetRootName(AstNode)
        elif isinstance(AstNode, AstLib.Call):
            if (
                isinstance(AstNode.func, AstLib.Attribute)
                and AstNode.func.attr in KMutatorNames
            ):
                RootName = GetRootName(AstNode.func.value)
            elif isinstance(AstNode.func, AstLib.Name) and AstNode.func.id in {
                "setattr",
                "delattr",
            }:
                RootName = GetRootName(AstNode.args[0]) if AstNode.args else None
        if RootName in ArgNames:
            MutatedNames.add(RootName)
    return MutatedNames


# conservative purity avoids false positives because unknown calls may mutate passed arguments
def IsClearlyPure(
    FuncNode: AstLib.FunctionDef | AstLib.AsyncFunctionDef,
    ParentMap: dict[AstLib.AST, AstLib.AST],
) -> bool:
    ArgNames = GetArgNames(FuncNode, ParentMap)
    if FindMutations(FuncNode, ParentMap):
        return False
    for AstNode in GetOwnedNodes(FuncNode):
        if not isinstance(AstNode, AstLib.Call):
            continue
        ValueNodes = [
            *AstNode.args,
            *(EntryNode.value for EntryNode in AstNode.keywords),
        ]
        if isinstance(AstNode.func, AstLib.Attribute):
            ValueNodes.append(AstNode.func.value)
        if any(GetRootName(ValueNode) in ArgNames for ValueNode in ValueNodes):
            return False
    return True


# marker checks exist because return and mutation contracts must remain visible to callers
def CheckMarkers(
    SourcePath: FilePath,
    SyntaxTree: AstLib.Module,
    ParentMap: dict[AstLib.AST, AstLib.AST],
) -> list[Finding]:
    FindingList: list[Finding] = []
    for FuncNode in AstLib.walk(SyntaxTree):
        if not isinstance(FuncNode, (AstLib.FunctionDef, AstLib.AsyncFunctionDef)):
            continue
        if IsDunderName(FuncNode.name):
            continue
        if IsBoolReturn(FuncNode) and not FuncNode.name.startswith(
            ("Is", "Has", "Can")
        ):
            MsgText = (
                f"boolean function {FuncNode.name!r} must start with Is Has or Can"
            )
            FindingList.append(
                Finding(
                    SourcePath,
                    FuncNode.lineno,
                    FuncNode.col_offset + 1,
                    "MRK001",
                    MsgText,
                )
            )
        MutatedNames = FindMutations(FuncNode, ParentMap)
        if MutatedNames and not FuncNode.name.endswith("Mut"):
            NameList = ", ".join(sorted(MutatedNames))
            MsgText = f"function {FuncNode.name!r} mutates argument {NameList} and must end with Mut"
            FindingList.append(
                Finding(
                    SourcePath,
                    FuncNode.lineno,
                    FuncNode.col_offset + 1,
                    "MRK002",
                    MsgText,
                )
            )
        elif FuncNode.name.endswith("Mut") and IsClearlyPure(FuncNode, ParentMap):
            MsgText = (
                f"function {FuncNode.name!r} has Mut suffix but is statically pure"
            )
            FindingList.append(
                Finding(
                    SourcePath,
                    FuncNode.lineno,
                    FuncNode.col_offset + 1,
                    "MRK003",
                    MsgText,
                )
            )
    return FindingList


# token based counting exists because visual wrapping must not inflate declaration size
def GetLogicalLines(
    TokenList: list[Tokenize.TokenInfo], StartLine: int, EndLine: int
) -> int:
    return sum(
        1
        for TokenInfo in TokenList
        if TokenInfo.type == Tokenize.NEWLINE
        and StartLine <= TokenInfo.start[0] <= EndLine
    )


# module assignment targeting limits table checks to declarations that can own focused data files
def GetAssignName(
    AstNode: AstLib.AST, ParentMap: dict[AstLib.AST, AstLib.AST]
) -> str | None:
    if not isinstance(AstNode, (AstLib.Assign, AstLib.AnnAssign)):
        return None
    if not isinstance(FindScope(AstNode, ParentMap), AstLib.Module):
        return None
    TargetNode = (
        AstNode.targets[0] if isinstance(AstNode, AstLib.Assign) else AstNode.target
    )
    if isinstance(AstNode, AstLib.Assign) and len(AstNode.targets) != 1:
        return None
    return TargetNode.id if isinstance(TargetNode, AstLib.Name) else None


# focused filenames prove large data already owns the dedicated module required by split steering
def IsFocusedAssign(SourcePath: FilePath, NameText: str) -> bool:
    CompareName = NameText[1:] if NameText.startswith("K") else NameText
    NormalName = Regex.sub(r"[^a-zA-Z]", "", CompareName).lower()
    NormalStem = Regex.sub(r"[^a-zA-Z]", "", SourcePath.stem).lower()
    return NormalName == NormalStem


# generated program tables stay atomic because semantic method boundaries must not become arbitrary chunks
def IsProgramTable(SourcePath: FilePath, NameText: str) -> bool:
    PartNames = tuple((PartText.casefold() for PartText in SourcePath.parts))
    RootParts = (
        "src",
        "convert",
        "adapters",
        "solidworks",
        "programs",
    )
    RootIndex = next(
        (
            PartIndex
            for PartIndex in range(len(PartNames) - len(RootParts) + 1)
            if PartNames[PartIndex : PartIndex + len(RootParts)] == RootParts
        ),
        None,
    )
    if RootIndex is None:
        return False
    RelativeParts = PartNames[RootIndex + len(RootParts) :]
    IsMethod = "methods" in RelativeParts[:-1] and NameText == "KMethodProgram"
    IsOwner = "owners" in RelativeParts[:-1] and NameText == "KOwnerSites"
    IsRegistry = SourcePath.name == "Registry.py" and NameText == "KMethodPrograms"
    return IsMethod or IsOwner or IsRegistry


# split diagnostics exist because oversized declarations obscure independently reviewable responsibilities
def CheckSplits(
    SourcePath: FilePath, SourceText: str, SyntaxTree: AstLib.Module
) -> list[Finding]:
    TokenList = list(Tokenize.generate_tokens(IoStream.StringIO(SourceText).readline))
    ParentMap = BuildParents(SyntaxTree)
    FindingList: list[Finding] = []
    for AstNode in AstLib.walk(SyntaxTree):
        NameText: str | None
        if isinstance(
            AstNode, (AstLib.ClassDef, AstLib.FunctionDef, AstLib.AsyncFunctionDef)
        ):
            NameText = AstNode.name
        else:
            NameText = GetAssignName(AstNode, ParentMap)
        if NameText is None:
            continue
        if isinstance(AstNode, (AstLib.Assign, AstLib.AnnAssign)) and (
            IsFocusedAssign(SourcePath, NameText)
            or IsProgramTable(SourcePath, NameText)
        ):
            continue
        StartLine, ColNum = GetStartPos(AstNode)
        EndLine = getattr(AstNode, "end_lineno", StartLine)
        LogicalLines = GetLogicalLines(TokenList, StartLine, EndLine)
        if isinstance(AstNode, (AstLib.Assign, AstLib.AnnAssign)):
            LogicalLines = EndLine - StartLine + 1
        if LogicalLines > 30:
            MsgText = f"declaration {NameText!r} has {LogicalLines} logical lines and must be split at 30"
            FindingList.append(
                Finding(SourcePath, StartLine, ColNum + 1, "SPL001", MsgText)
            )
    return FindingList


# path based exemptions exist because license steering explicitly excludes two repository areas
def IsHeaderExempt(SourcePath: FilePath) -> bool:
    return any(PartText in {".kiro", "examples"} for PartText in SourcePath.parts)


# exact prefix comparison prevents invalid notices because altered licensing immediately breaks compliance
def CheckHeader(SourcePath: FilePath, SourceText: str) -> list[Finding]:
    if IsHeaderExempt(SourcePath):
        return []
    SourceLines = SourceText.splitlines()
    HeaderLines = KPythonHeader.splitlines()
    StartIndex = 1 if SourceLines and SourceLines[0].startswith("#!") else 0
    ActualLines = SourceLines[StartIndex : StartIndex + len(HeaderLines)]
    if ActualLines == HeaderLines:
        return []
    MsgText = "file must begin with the exact HEADER_NOTICE python comment block"
    return [Finding(SourcePath, StartIndex + 1, 1, "SPX001", MsgText)]


# encoded source loading uses python rules because source files may declare alternate encodings
def ReadSource(SourcePath: FilePath) -> str:
    with Tokenize.open(SourcePath) as SourceFile:
        return SourceFile.read()


# one file pipeline preserves header diagnostics even when python syntax is invalid
def CheckFile(SourcePath: FilePath) -> list[Finding]:
    SourceText = ReadSource(SourcePath)
    FindingList = CheckHeader(SourcePath, SourceText)
    try:
        SyntaxTree = AstLib.parse(SourceText, filename=str(SourcePath))
    except SyntaxError as ErrorInfo:
        LineNum = ErrorInfo.lineno or 1
        ColNum = ErrorInfo.offset or 1
        MsgText = ErrorInfo.msg or "invalid python syntax"
        FindingList.append(Finding(SourcePath, LineNum, ColNum, "SYN001", MsgText))
        return FindingList
    ParentMap = BuildParents(SyntaxTree)
    FindingList.extend(CheckNames(SourcePath, SyntaxTree))
    FindingList.extend(CheckConstants(SourcePath, SyntaxTree, ParentMap))
    FindingList.extend(CheckReasons(SourcePath, SourceText, SyntaxTree, ParentMap))
    FindingList.extend(CheckComments(SourcePath, SourceText, SyntaxTree, ParentMap))
    FindingList.extend(CheckMarkers(SourcePath, SyntaxTree, ParentMap))
    FindingList.extend(CheckSplits(SourcePath, SourceText, SyntaxTree))
    return FindingList


# directory filtering avoids dependencies because generated files do not belong to repository compliance
def HasSkippedPart(SourcePath: FilePath, RootPath: FilePath) -> bool:
    RelativePath = SourcePath.relative_to(RootPath)
    return any(PartText in KSkipFolders for PartText in RelativePath.parts)


# path expansion supports mixed files and trees with deduplication and explicit input errors
def ResolvePaths(PathValues: list[FilePath | str]) -> list[FilePath]:
    ResolvedFiles: list[FilePath] = []
    SeenFiles: set[FilePath] = set()
    for PathValue in PathValues:
        InputPath = FilePath(PathValue).expanduser().resolve()
        if not InputPath.exists():
            raise FileNotFoundError(f"path does not exist: {PathValue}")
        if InputPath.is_file():
            if InputPath.suffix != ".py":
                raise ValueError(f"unsupported non python file: {PathValue}")
            CandidatePaths = [InputPath]
        else:
            CandidatePaths = sorted(InputPath.rglob("*.py"))
        for SourcePath in CandidatePaths:
            if InputPath.is_dir() and HasSkippedPart(SourcePath, InputPath):
                continue
            if SourcePath not in SeenFiles:
                SeenFiles.add(SourcePath)
                ResolvedFiles.append(SourcePath)
    return sorted(ResolvedFiles)


# batch checking stays separate because callers may already own path collection and validation
def CheckFiles(FilePaths: list[FilePath]) -> list[Finding]:
    FindingList: list[Finding] = []
    for SourcePath in FilePaths:
        FindingList.extend(CheckFile(SourcePath))
    return sorted(FindingList)


# public path checking keeps programmatic users aligned with command line expansion semantics
def CheckPaths(PathValues: list[FilePath | str]) -> list[Finding]:
    return CheckFiles(ResolvePaths(PathValues))


# argument parsing requires at least one explicit target so accidental broad scans cannot happen
def ParseArgs(ArgValues: list[str] | None = None) -> Argparse.Namespace:
    ParserInfo = Argparse.ArgumentParser(
        description="check python files against repository steering conventions"
    )
    ParserInfo.add_argument(
        "PathValues",
        metavar="PATH",
        nargs="+",
        help="python file or directory to check recursively",
    )
    return ParserInfo.parse_args(ArgValues)


# relative rendering keeps local diagnostics concise because external paths still need complete locations
def FormatFinding(FindingInfo: Finding) -> str:
    try:
        DisplayPath = FindingInfo.SourcePath.relative_to(FilePath.cwd())
    except ValueError:
        DisplayPath = FindingInfo.SourcePath
    return (
        f"{DisplayPath.as_posix()}:{FindingInfo.LineNum}:{FindingInfo.ColNum}: "
        f"{FindingInfo.RuleCode} {FindingInfo.MsgText}"
    )


# explicit status handling exists because automation must distinguish violations from invalid inputs
def MainRun(ArgValues: list[str] | None = None) -> int:
    NamespaceInfo = ParseArgs(ArgValues)
    try:
        FilePaths = ResolvePaths(NamespaceInfo.PathValues)
        FindingList = CheckFiles(FilePaths)
    except (OSError, UnicodeError, ValueError) as ErrorInfo:
        print(f"steering compliance input error: {ErrorInfo}", file=System.stderr)
        return 2
    for FindingInfo in FindingList:
        print(FormatFinding(FindingInfo))
    if FindingList:
        print(
            f"steering compliance failed with {len(FindingList)} violations",
            file=System.stderr,
        )
        return 1
    print(f"steering compliance passed for {len(FilePaths)} python files")
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())

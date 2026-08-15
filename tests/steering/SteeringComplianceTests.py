# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
import unittest as Unittest
from pathlib import Path as FilePath

from tools.steering.SteeringCompliance import CheckPaths

# fixtures reuse the production notice so tests isolate every other compliance rule
KPythonHeader = """# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.
"""

# command tests need the checked in entry point because fixtures use temporary directories
KCheckerPath = (
    FilePath(__file__).resolve().parents[2]
    / "tools"
    / "steering"
    / "SteeringCompliance.py"
)

# static test methods need standard assertion behavior without violating receiver naming policy
KAssertions = Unittest.TestCase()


# source assembly exists because each focused test fixture still needs a complete header
def MakeSource(BodyText: str) -> str:
    return KPythonHeader + "\n" + BodyText


# isolated writes prevent leakage because compliance cases require independent fixture state
def WriteSample(FolderPath: FilePath, SourceText: str) -> FilePath:
    SourcePath = FolderPath / "sample.py"
    SourcePath.write_text(SourceText, encoding="utf-8")
    return SourcePath


# compact code extraction exists because tests should avoid coupling to diagnostic prose
def ReadCodes(SourcePath: FilePath) -> set[str]:
    return {FindingInfo.RuleCode for FindingInfo in CheckPaths([SourcePath])}


# a fully compliant fixture protects the checker from rejecting intended steering syntax
class TestValid(Unittest.TestCase):

    # valid coverage ensures combined rules accept a realistic class and predicate method
    @staticmethod
    def CheckValid() -> None:
        CaseSelf = KAssertions
        BodyText = """# shared limits stay stable because every caller needs one boundary
KLimitValue = 3

# request state stays grouped so callers share one stable contract
class RequestState:

    # cached status avoids repeated work across frequent request checks
    def IsReady(CaseSelf, InputValue: int) -> bool:
        LocalValue = InputValue
        return LocalValue > 0
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            CaseSelf.assertEqual(CheckPaths([SourcePath]), [])


# malformed declarations stay together because every controlled identifier category needs focused coverage
class TestNaming(Unittest.TestCase):

    # invalid coverage prevents short snake case and receiver names from slipping through
    @staticmethod
    def CheckNaming() -> None:
        CaseSelf = KAssertions
        BodyText = """# invalid shapes stay grouped because one fixture should exercise every binding
class bad:

    # invalid names remain together because diagnostics must identify each distinct category
    def calc(self, xvalue):
        self.bad_attr = xvalue
        local_name = xvalue
        return local_name
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            FindingList = CheckPaths([SourcePath])
        BadNames = {
            FindingInfo.MsgText.split("'")[1]
            for FindingInfo in FindingList
            if FindingInfo.RuleCode == "NAM001"
        }
        CaseSelf.assertLessEqual(
            {"bad", "calc", "self", "bad_attr", "local_name"}, BadNames
        )


# reserved bindings and type only imports share coverage because both remain valid python binding forms
class TestBindings(Unittest.TestCase):

    # reserved dunders stay exempt while aliases inside type checking branches still require compliant names
    @staticmethod
    def CheckBindings() -> None:
        CaseSelf = KAssertions
        BodyText = """from typing import TYPE_CHECKING as TypeChecking

# reserved slots constrain instances because records require predictable storage
__slots__ = ("FieldValue",)

if TypeChecking:
    from pathlib import Path as bad_path
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            FindingList = CheckPaths([SourcePath])
        NamedValues = {
            FindingInfo.MsgText.split("'")[1]
            for FindingInfo in FindingList
            if FindingInfo.RuleCode == "NAM001"
        }
        CaseSelf.assertNotIn("__slots__", NamedValues)
        CaseSelf.assertIn("bad_path", NamedValues)
        CaseSelf.assertNotIn(
            "CON001", {FindingInfo.RuleCode for FindingInfo in FindingList}
        )


# import fixtures stay focused because wildcard dependencies need one unmistakable diagnostic
class TestImports(Unittest.TestCase):

    # exact diagnostics prevent broad namespace ownership from returning through future refactors
    @staticmethod
    def CheckWildcard() -> None:
        CaseSelf = KAssertions
        BodyText = "from SampleModule import *\n"
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            FindingList = CheckPaths([SourcePath])
        ImportCodes = [
            FindingInfo.RuleCode
            for FindingInfo in FindingList
            if FindingInfo.RuleCode.startswith("IMP")
        ]
        CaseSelf.assertEqual(ImportCodes, ["IMP001"])


# predicate examples stay together because annotation and literal inference share one contract
class TestBoolMark(Unittest.TestCase):

    # both inference paths matter because unannotated legacy functions still expose boolean contracts
    @staticmethod
    def CheckBoolMark() -> None:
        CaseSelf = KAssertions
        BodyText = """# annotation checks exist because callers need visible predicate contracts
def FetchReady(InputValue: int) -> bool:
    return InputValue > 0

# literal checks exist because older call sites omit return annotations
def FetchFlag(InputValue):
    if InputValue:
        return True
    return False
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            FindingList = CheckPaths([SourcePath])
        MarkerNames = {
            FindingInfo.MsgText.split("'")[1]
            for FindingInfo in FindingList
            if FindingInfo.RuleCode == "MRK001"
        }
        CaseSelf.assertEqual(MarkerNames, {"FetchReady", "FetchFlag"})


# asynchronous and type only return fixtures stay together because both expose explicit predicate contracts
class TestBoolTypes(Unittest.TestCase):

    # quoted literal and annotated boolean returns must retain markers across async and typing syntax
    @staticmethod
    def CheckBoolTypes() -> None:
        CaseSelf = KAssertions
        BodyText = """from typing import Annotated, TypeGuard

# async readiness exists because callers must avoid blocking the shared event loop
async def FetchReady() -> "Literal[True, False]":
    return True

# metadata stays attached because validation consumers need the explicit return contract
def FetchTyped() -> Annotated[bool, "predicate"]:
    return True

# narrowing exists because callers need static knowledge after one runtime check
def FetchNarrow(InputValue: object) -> TypeGuard[str]:
    return isinstance(InputValue, str)
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            FindingList = CheckPaths([SourcePath])
        MarkerNames = {
            FindingInfo.MsgText.split("'")[1]
            for FindingInfo in FindingList
            if FindingInfo.RuleCode == "MRK001"
        }
        CaseSelf.assertEqual(MarkerNames, {"FetchNarrow", "FetchReady", "FetchTyped"})


# destructive examples stay together because argument signals contrast directly with receiver exemptions
class TestMutation(Unittest.TestCase):

    # direct writes and pure suffixes matter because both misleading contracts harm callers
    @staticmethod
    def CheckMutation() -> None:
        CaseSelf = KAssertions
        BodyText = """# queue ordering exists because consumers share the same mutable collection
def SortQueue(QueueValue):
    QueueValue.sort()

# copied totals stay pure because callers compare original and derived values
def CalcTotalMut(InputValue):
    return InputValue + 1

# local cache owns state because instance mutation is expected by its callers
class CacheState:

    # cache replacement exists because each instance controls its own stored value
    def StoreValue(CaseSelf, InputValue):
        CaseSelf.CacheValue = InputValue
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            CodeSet = ReadCodes(SourcePath)
        CaseSelf.assertLessEqual({"MRK002", "MRK003"}, CodeSet)


# constant examples stay together because stable and reassigned state require contrasting assertions
class TestConstants(Unittest.TestCase):

    # marker coverage prevents constants and mutable globals from sharing misleading names
    @staticmethod
    def CheckConstants() -> None:
        CaseSelf = KAssertions
        BodyText = """# one limit exists because all workers must share the same boundary
LimitValue = 5

# runtime state starts here because later startup logic replaces its value
KRuntimeValue = 1
KRuntimeValue = 2

# policy values stay grouped because every instance shares the same default
class PolicyState:

    # one timeout exists because every policy instance needs the same boundary
    TimeoutValue = 30
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            CodeSet = ReadCodes(SourcePath)
        CaseSelf.assertLessEqual({"CON001", "CON002"}, CodeSet)


# field container fixtures stay together because instance fields and explicit class constants need contrast
class TestDataFields(Unittest.TestCase):

    # dataclass and named tuple fields remain instance state while class variables retain constant markers
    @staticmethod
    def CheckDataFields() -> None:
        CaseSelf = KAssertions
        BodyText = """from dataclasses import dataclass as DataClass
from typing import ClassVar, NamedTuple

# dataclass records exist because consumers need one mutable payload contract
@DataClass
class RecordState:
    FieldValue: int
    OtherValue: int = 1
    KSharedLimit: ClassVar[int] = 2
    SharedLimit: ClassVar[int] = 3

# tuple records exist because consumers need one immutable payload contract
class TupleRecord(NamedTuple):
    FieldValue: int
    OtherValue: int = 1
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            FindingList = CheckPaths([SourcePath])
        ConstantNames = {
            FindingInfo.MsgText.split("'")[1]
            for FindingInfo in FindingList
            if FindingInfo.RuleCode.startswith("CON")
        }
        CaseSelf.assertEqual(ConstantNames, {"SharedLimit"})


# rationale fixtures stay focused because structural wording and purpose failures need independent evidence
class TestReasons(Unittest.TestCase):

    # malformed comments stay grouped because syntax and purpose checks need contrasting evidence
    @staticmethod
    def CheckReasons() -> None:
        CaseSelf = KAssertions
        BodyText = """# This comment has enough words because it exists
def BuildValue(InputValue):
    return InputValue

# returns the provided value without changes
def KeepValue(InputValue):
    return InputValue

# needed because callers need one conversion boundary

def ParseValue(InputValue):
    return InputValue
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            CodeSet = ReadCodes(SourcePath)
        CaseSelf.assertLessEqual({"RAT001", "RAT003", "RAT004"}, CodeSet)


# comment fixtures stay focused because rationale uniqueness and narrow pragma exemptions form one contract
class TestComments(Unittest.TestCase):

    # duplicate and inline commentary must fail while type checking pragmas remain valid tooling metadata
    @staticmethod
    def CheckComments() -> None:
        CaseSelf = KAssertions
        BodyText = """# duplicate purposes exist because this fixture needs one forbidden extra comment
# stable limits exist because every consumer needs one shared boundary
KLimitValue = 1

# typed limits exist because static analysis needs one shared boundary
KTypedLimit = 2  # type: int

# inline prose exists because this fixture needs one forbidden trailing explanation
KOtherLimit = 3  # explains the assignment
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            FindingList = CheckPaths([SourcePath])
        CommentLines = {
            FindingInfo.LineNum
            for FindingInfo in FindingList
            if FindingInfo.RuleCode == "CMT001"
        }
        CaseSelf.assertEqual(CommentLines, {9, 17})

    # forbidden words need coverage because mandated rationale syntax cannot hide incomplete work
    @staticmethod
    def CheckStubWords() -> None:
        CaseSelf = KAssertions
        BodyText = """# todo exists because this fixture needs one forbidden placeholder rationale
KLimitValue = 1
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            CaseSelf.assertIn("RAT003", ReadCodes(SourcePath))


# lambda coverage exists because inline callbacks require statement level rationale placement
class TestLambda(Unittest.TestCase):

    # inline callbacks need their own purpose because enclosing function rationale is insufficient
    @staticmethod
    def CheckLambda() -> None:
        CaseSelf = KAssertions
        BodyText = """# ordering stays centralized because callers need deterministic output
def BuildValues(InputValues):
    ResultValues = sorted(InputValues, key=lambda InputValue: InputValue)
    return ResultValues
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            CaseSelf.assertIn("RAT001", ReadCodes(SourcePath))


# oversized fixture generation exists because logical counting must ignore physical wrapping
class TestSplits(Unittest.TestCase):

    # repeated statements exist because the declaration must exceed exactly the mandatory split threshold
    @staticmethod
    def CheckSplits() -> None:
        CaseSelf = KAssertions
        StepLines = "\n".join(["    LocalValue = LocalValue + 1"] * 31)
        BodyText = (
            "# payload assembly stays centralized because this fixture needs one oversized declaration\n"
            "def BuildPayload():\n"
            "    LocalValue = 0\n"
            f"{StepLines}\n"
            "    return LocalValue\n"
        )
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            CaseSelf.assertIn("SPL001", ReadCodes(SourcePath))


# module table coverage exists because substantial data definitions need focused files just like functions
class TestDataSplits(Unittest.TestCase):

    # large module data must split while equally sized local data remains owned by its focused declaration
    @staticmethod
    def CheckDataSplits() -> None:
        CaseSelf = KAssertions
        TableLines = "\n".join(
            f'    "Key{IndexValue}": {IndexValue},' for IndexValue in range(31)
        )
        BodyText = (
            "# fixture data stays large because split checks need one substantial module table\n"
            "KLargeTable = {\n"
            f"{TableLines}\n"
            "}\n"
        )
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = WriteSample(FilePath(TmpPath), MakeSource(BodyText))
            FindingList = CheckPaths([SourcePath])
        SplitNames = {
            FindingInfo.MsgText.split("'")[1]
            for FindingInfo in FindingList
            if FindingInfo.RuleCode == "SPL001"
        }
        CaseSelf.assertEqual(SplitNames, {"KLargeTable"})

    # focused table modules remain valid because isolation already satisfies the structural steering purpose
    @staticmethod
    def CheckDataFile() -> None:
        CaseSelf = KAssertions
        TableLines = "\n".join(
            f'    "Key{IndexValue}": {IndexValue},' for IndexValue in range(31)
        )
        BodyText = (
            "# fixture data stays isolated because consumers import this focused table directly\n"
            "KLargeTable = {\n"
            f"{TableLines}\n"
            "}\n"
        )
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            SourcePath = FolderPath / "large_table.py"
            SourcePath.write_text(MakeSource(BodyText), encoding="utf-8")
            CaseSelf.assertNotIn("SPL001", ReadCodes(SourcePath))


# generated table cases stay separate because the path scoped exception needs focused boundary coverage
class TestPrograms(Unittest.TestCase):

    # generated method tables stay intact because each file already represents one natural serializer method
    @staticmethod
    def CheckProgram() -> None:
        CaseSelf = KAssertions
        TableLines = "\n".join(
            f"    ({IndexValue}, 1, 'Owner', 'primitive', {IndexValue}),"
            for IndexValue in range(31)
        )
        BodyText = (
            "# method operations stay atomic because offsets describe one recovered serializer method\n"
            "KMethodProgram = (\n"
            f"{TableLines}\n"
            ")\n"
        )
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = (
                FilePath(TmpPath)
                / "src/convert/adapters/solidworks/programs/resolved/box/Methods/Serialize.py"
            )
            SourcePath.parent.mkdir(parents=True)
            SourcePath.write_text(MakeSource(BodyText), encoding="utf-8")
            CaseSelf.assertNotIn("SPL001", ReadCodes(SourcePath))

    # near misses remain violations because only generated bindings at exact semantic paths are exceptional
    @staticmethod
    def CheckNearMiss() -> None:
        CaseSelf = KAssertions
        TableLines = "\n".join(f"    {IndexValue}," for IndexValue in range(31))
        BodyText = (
            "# unrelated data stays large because this fixture must prove the exception remains narrow\n"
            "KUnrelatedTable = (\n"
            f"{TableLines}\n"
            ")\n"
        )
        with Tempfile.TemporaryDirectory() as TmpPath:
            SourcePath = (
                FilePath(TmpPath)
                / "src/convert/adapters/solidworks/programs/resolved/box/Methods/Serialize.py"
            )
            SourcePath.parent.mkdir(parents=True)
            SourcePath.write_text(MakeSource(BodyText), encoding="utf-8")
            CaseSelf.assertIn("SPL001", ReadCodes(SourcePath))


# header fixtures stay together because exact notices and shebang placement share prefix logic
class TestHeaders(Unittest.TestCase):

    # exact prefix coverage matters because altered notices immediately void repository licensing
    @staticmethod
    def CheckHeaders() -> None:
        CaseSelf = KAssertions
        BodyText = """# stable values exist because this fixture needs valid module state
KValidValue = 1
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            MissingPath = WriteSample(FolderPath, BodyText)
            CaseSelf.assertIn("SPX001", ReadCodes(MissingPath))
            ShebangPath = WriteSample(
                FolderPath, "#!/usr/bin/env python3\n" + MakeSource(BodyText)
            )
            CaseSelf.assertNotIn("SPX001", ReadCodes(ShebangPath))
            CaseSelf.assertNotIn("CMT001", ReadCodes(ShebangPath))


# subprocess coverage exists because command status codes matter only at the process boundary
class TestCommand(Unittest.TestCase):

    # distinct outcomes exist because automation must separate violations from invalid user input
    @staticmethod
    def CheckCommand() -> None:
        CaseSelf = KAssertions
        BodyText = """# stable values exist because this fixture needs valid module state
KValidValue = 1
"""
        with Tempfile.TemporaryDirectory() as TmpPath:
            FolderPath = FilePath(TmpPath)
            ValidPath = WriteSample(FolderPath, MakeSource(BodyText))
            ValidResult = Subprocess.run(
                [System.executable, str(KCheckerPath), str(ValidPath)],
                capture_output=True,
                text=True,
                check=False,
            )
            InvalidPath = FolderPath / "missing.py"
            InvalidResult = Subprocess.run(
                [System.executable, str(KCheckerPath), str(InvalidPath)],
                capture_output=True,
                text=True,
                check=False,
            )
        CaseSelf.assertEqual(
            ValidResult.returncode, 0, ValidResult.stdout + ValidResult.stderr
        )
        CaseSelf.assertEqual(InvalidResult.returncode, 2)


# path filtering stays focused because local analysis databases are not repository source
class TestPathFilter(Unittest.TestCase):

    # scratch trees stay excluded because broad local checks must not traverse generated analyzer data
    @staticmethod
    def CheckScratch() -> None:
        CaseSelf = KAssertions
        with Tempfile.TemporaryDirectory() as TmpPath:
            RootPath = FilePath(TmpPath)
            SourcePath = RootPath / ".rescratch" / "Broken.py"
            SourcePath.parent.mkdir()
            SourcePath.write_text("def bad():\n    pass\n", encoding="utf-8")
            CaseSelf.assertEqual(CheckPaths([RootPath]), [])


# self checking prevents regressions because enforcement sources must follow their own rules
class TestBootstrap(Unittest.TestCase):

    # checker sources pass themselves because enforcement credibility depends on consistent application
    @staticmethod
    def CheckBootstrap() -> None:
        CaseSelf = KAssertions
        TestFilePath = FilePath(__file__).resolve()
        FindingList = CheckPaths([KCheckerPath, TestFilePath])
        CaseSelf.assertEqual(
            FindingList, [], "\n".join(str(FindingInfo) for FindingInfo in FindingList)
        )

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from importlib.util import module_from_spec as BuildModule
from importlib.util import spec_from_file_location as BuildSpec
import pathlib as Pathlib
import tempfile as Tempfile
from unittest import TestCase as UnitTestCase
from typing import Callable as CallType
from typing import Protocol
from typing import cast as TypeCast
from unittest import mock as Mocking

from tests.Policy.RepoFixture import RepoFixture
from tests.Policy.SpdxHeadersTest import LoadGuard


# dynamic repair loading needs concrete signatures so byte mutation calls remain strictly checked
class RepairContract(Protocol):
    CanRepairMut: CallType[[Pathlib.Path, list[str], str], bool]
    MakeHeader: CallType[[list[str], bytes], bytes]
    WriteMissingMut: CallType[[Pathlib.Path, list[str]], None]


# direct helper loading keeps byte transformation tests independent from script execution
def LoadRepair() -> RepairContract:
    ScriptPath = (
        Pathlib.Path(__file__).parents[2]
        / ".github"
        / "scripts"
        / "SpdxHeaderRemediation.py"
    )
    RepairSpec = BuildSpec("SpdxRepairTest", ScriptPath)
    if RepairSpec is None or RepairSpec.loader is None:
        raise RuntimeError("spdx remediation script cannot be loaded")
    RepairModule = BuildModule(RepairSpec)
    RepairSpec.loader.exec_module(RepairModule)
    return TypeCast(RepairContract, RepairModule)


# adversarial diff fixtures prove automation accepts only canonical repository destinations
class TestDiffGuard(UnitTestCase):

    # nul records must preserve rename destinations while rejecting every ambiguous path spelling
    def TestDiffParse(self) -> None:
        ParseDiff = LoadGuard().ParseDiff
        DiffBytes = b"M\0Alpha.py\0R100\0Old.py\0New.py\0"
        self.assertEqual(ParseDiff(DiffBytes), ["Alpha.py", "New.py"])
        BadPaths = (
            b"",
            b"/Absolute.py",
            b"../Escape.py",
            b"Folder\\Wrong.py",
            b"Folder//Wrong.py",
            b"Bad\nName.py",
            b"Bad\xffName.py",
        )
        for PathBytes in BadPaths:
            with self.subTest(PathBytes=PathBytes):
                with self.assertRaises(ValueError):
                    ParseDiff(b"M\0" + PathBytes + b"\0")


# byte focused fixtures protect untouched content from newline normalization during repair
class TestByteRepair(UnitTest.TestCase):

    # inserted headers must retain existing newline bytes and preserve unterminated shebang content
    def TestMissBytes(self) -> None:
        GuardModule = LoadGuard()
        RepairModule = LoadRepair()
        HeaderLines = GuardModule.RenderLines(GuardModule.LoadCanon(), "#")
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            CrLfPath = RootPath / "CrLf.py"
            CrLfPath.write_bytes(b"print('ok')\r\n")
            RepairModule.WriteMissingMut(CrLfPath, HeaderLines)
            HeaderBytes = RepairModule.MakeHeader(HeaderLines, b"\r\n")
            self.assertEqual(CrLfPath.read_bytes(), HeaderBytes + b"print('ok')\r\n")
            ScriptPath = RootPath / "Script.py"
            ShebangBytes = b"#!/usr/bin/env python"
            ScriptPath.write_bytes(ShebangBytes)
            RepairModule.WriteMissingMut(ScriptPath, HeaderLines)
            self.assertEqual(
                ScriptPath.read_bytes(),
                ShebangBytes + b"\n" + RepairModule.MakeHeader(HeaderLines, b"\n"),
            )


# span focused fixtures prevent damaged notices from consuming neighboring source documentation
class TestSpanRepair(UnitTest.TestCase):

    # recognizable fragments may be replaced but adjacent documentation must make repair fail closed
    def TestBoundRepair(self) -> None:
        GuardModule = LoadGuard()
        RepairModule = LoadRepair()
        HeaderLines = GuardModule.RenderLines(GuardModule.LoadCanon(), "#")
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            SafePath = RootPath / "Safe.py"
            SafePath.write_bytes(
                b"# SPDX-License-Identifier: damaged\n"
                b"# SPDX-FileCopyrightText: damaged\n\n"
                b"print('safe')\n"
            )
            self.assertTrue(RepairModule.CanRepairMut(SafePath, HeaderLines, "#"))
            self.assertTrue(SafePath.read_bytes().endswith(b"print('safe')\n"))
            DocsPath = RootPath / "Docs.py"
            DocsBytes = (
                b"# SPDX-License-Identifier: damaged\n"
                b"# unrelated module documentation\n\n"
                b"print('safe')\n"
            )
            DocsPath.write_bytes(DocsBytes)
            self.assertFalse(RepairModule.CanRepairMut(DocsPath, HeaderLines, "#"))
            self.assertEqual(DocsPath.read_bytes(), DocsBytes)
            EncodingPath = RootPath / "Encoding.py"
            EncodingBytes = (
                b"# coding: utf-8\n"
                b"# SPDX-License-Identifier: damaged\n\n"
                b"print('safe')\n"
            )
            EncodingPath.write_bytes(EncodingBytes)
            self.assertFalse(RepairModule.CanRepairMut(EncodingPath, HeaderLines, "#"))
            self.assertEqual(EncodingPath.read_bytes(), EncodingBytes)


# format focused fixtures allow proven legacy styles without authorizing style guesses
class TestStyleGuard(UnitTest.TestCase):

    # unknown formats may retain a proven marker but must never receive a guessed missing style
    def TestUnkStyle(self) -> None:
        GuardModule = LoadGuard()
        CanonLines = GuardModule.LoadCanon()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            DebugPath = RootPath / "Debug.trace"
            DebugPath.write_bytes(
                b"$$ SPDX-License-Identifier: damaged\n"
                b"$$ SPDX-FileCopyrightText: damaged\n\n"
                b"command\n"
            )
            IsFixed, ReasonText = GuardModule.RepairHeadMut(
                DebugPath, CanonLines, RootPath
            )
            self.assertTrue(IsFixed, ReasonText)
            self.assertTrue(DebugPath.read_bytes().startswith(b"$$ SPDX-"))
            BlockPath = RootPath / "Markup.trace"
            BlockPath.write_bytes(
                b"<!--\n"
                b"SPDX-License-Identifier: damaged\n"
                b"SPDX-FileCopyrightText: damaged\n"
                b"-->\n\n"
                b"markup\n"
            )
            IsFixed, ReasonText = GuardModule.RepairHeadMut(
                BlockPath, CanonLines, RootPath
            )
            self.assertTrue(IsFixed, ReasonText)
            self.assertTrue(BlockPath.read_bytes().startswith(b"<!--\nSPDX-"))
            MissingPath = RootPath / "Missing.trace"
            MissingPath.write_bytes(b"command\n")
            OriginalBytes = MissingPath.read_bytes()
            IsFixed, ReasonText = GuardModule.RepairHeadMut(
                MissingPath, CanonLines, RootPath
            )
            self.assertFalse(IsFixed, ReasonText)
            self.assertEqual(MissingPath.read_bytes(), OriginalBytes)


# text focused fixtures keep malformed known source files inside the enforcement boundary
class TestTextGuard(UnitTest.TestCase):

    # known source formats must report invalid utf eight instead of being silently treated as binary
    def TestInvalidText(self) -> None:
        GuardModule = LoadGuard()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            SourcePath = RootPath / "Invalid.py"
            SourcePath.write_bytes(b"\xff\xfe")
            IsValid, ReasonText = GuardModule.CheckFile(
                SourcePath, GuardModule.LoadCanon(), RootPath
            )
        self.assertFalse(IsValid)
        self.assertIn("UTF-8", ReasonText)


# path focused fixtures keep filesystem traversal limited to regular worktree files
class TestPathGuard(UnitTest.TestCase):

    # regular candidates pass while missing directories and lexical links never reach content checks
    def TestPathBound(self) -> None:
        GuardModule = LoadGuard()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath).resolve()
            SourcePath = RootPath / "Source.py"
            SourcePath.write_text("source\n", encoding="utf-8")
            self.assertEqual(GuardModule.ResolvePath(RootPath, "Source.py"), SourcePath)
            self.assertIsNone(GuardModule.ResolvePath(RootPath, "Missing.py"))
            FolderPath = RootPath / "Folder"
            FolderPath.mkdir()
            self.assertIsNone(GuardModule.ResolvePath(RootPath, "Folder"))
            ChildPath = FolderPath / "Child.py"
            ChildPath.write_text("child\n", encoding="utf-8")
            with Mocking.patch.object(
                GuardModule.StatLib, "S_ISLNK", return_value=True
            ):
                self.assertIsNone(GuardModule.ResolvePath(RootPath, "Folder/Child.py"))


# skill focused fixtures preserve agent metadata while restoring its distinct license contract
class TestSkillGuard(UnitTest.TestCase):

    # agent skill repair stays inside the selected worktree and preserves all nonlicense frontmatter
    def TestSkillField(self) -> None:
        GuardModule = LoadGuard()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            SkillPath = RootPath / ".agents" / "skills" / "alpha" / "SKILL.md"
            SkillPath.parent.mkdir(parents=True)
            SkillPath.write_bytes(
                b"---\r\nname: alpha\r\nlicense: damaged\r\n---\r\nbody\r\n"
            )
            IsFixed, ReasonText = GuardModule.RepairHeadMut(
                SkillPath, GuardModule.LoadCanon(), RootPath
            )
            self.assertTrue(IsFixed, ReasonText)
            SourceBytes = SkillPath.read_bytes()
            self.assertIn(b"license: LicenseRef-PolyForm-Strict-1.0.0\r\n", SourceBytes)
            self.assertIn(b"name: alpha\r\n", SourceBytes)


# revision focused fixtures bind materialized files to one exact commit identity
class TestHeadGuard(UnitTest.TestCase):

    # exact commit and worktree checks prevent symbolic revisions or a stale materialized head
    def TestExactHead(self) -> None:
        GuardModule = LoadGuard()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Source.py")
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.MoveFile("Source.py", "Target.py")
            HeadRef = FixtureInfo.CommitAll("head")
            self.assertTrue(GuardModule.IsCommit(HeadRef, RootPath))
            self.assertFalse(GuardModule.IsCommit("HEAD", RootPath))
            self.assertEqual(
                GuardModule.GetDiffFiles(BaseRef, HeadRef, RootPath), ["Target.py"]
            )
            WorktreeRoot, ReasonText = GuardModule.CheckWorktree(RootPath, HeadRef)
            self.assertEqual(WorktreeRoot, RootPath.resolve(), ReasonText)
            WorktreeRoot, ReasonText = GuardModule.CheckWorktree(RootPath, "0" * 40)
            self.assertIsNone(WorktreeRoot, ReasonText)

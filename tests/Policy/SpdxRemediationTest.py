# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import pathlib as Pathlib
import runpy as Runpy
import tempfile as Tempfile
import unittest as UnitTest
from unittest import mock as Mocking

from tests.Policy.RepoFixture import RepoFixture
from tests.Policy.SpdxHeadersTest import LoadGuard


# direct helper loading keeps byte transformation tests independent from script execution
def LoadRepair() -> dict[str, object]:
    ScriptPath = (
        Pathlib.Path(__file__).parents[2]
        / ".github"
        / "scripts"
        / "SpdxHeaderRemediation.py"
    )
    return Runpy.run_path(str(ScriptPath), run_name="SpdxRepairTest")


# adversarial diff fixtures prove automation accepts only canonical repository destinations
class TestDiffGuard(UnitTest.TestCase):

    # nul records must preserve rename destinations while rejecting every ambiguous path spelling
    def TestDiffParse(CaseSelf) -> None:
        ParseDiff = LoadGuard()["ParseDiff"]
        DiffBytes = b"M\0Alpha.py\0R100\0Old.py\0New.py\0"
        CaseSelf.assertEqual(ParseDiff(DiffBytes), ["Alpha.py", "New.py"])
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
            with CaseSelf.subTest(PathBytes=PathBytes):
                with CaseSelf.assertRaises(ValueError):
                    ParseDiff(b"M\0" + PathBytes + b"\0")


# byte focused fixtures protect untouched content from newline normalization during repair
class TestByteRepair(UnitTest.TestCase):

    # inserted headers must retain existing newline bytes and preserve unterminated shebang content
    def TestMissBytes(CaseSelf) -> None:
        GuardValues = LoadGuard()
        RepairValues = LoadRepair()
        HeaderLines = GuardValues["RenderLines"](GuardValues["LoadCanon"](), "#")
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            CrLfPath = RootPath / "CrLf.py"
            CrLfPath.write_bytes(b"print('ok')\r\n")
            RepairValues["WriteMissingMut"](CrLfPath, HeaderLines)
            HeaderBytes = RepairValues["MakeHeader"](HeaderLines, b"\r\n")
            CaseSelf.assertEqual(
                CrLfPath.read_bytes(), HeaderBytes + b"print('ok')\r\n"
            )
            ScriptPath = RootPath / "Script.py"
            ShebangBytes = b"#!/usr/bin/env python"
            ScriptPath.write_bytes(ShebangBytes)
            RepairValues["WriteMissingMut"](ScriptPath, HeaderLines)
            CaseSelf.assertEqual(
                ScriptPath.read_bytes(),
                ShebangBytes + b"\n" + RepairValues["MakeHeader"](HeaderLines, b"\n"),
            )


# span focused fixtures prevent damaged notices from consuming neighboring source documentation
class TestSpanRepair(UnitTest.TestCase):

    # recognizable fragments may be replaced but adjacent documentation must make repair fail closed
    def TestBoundRepair(CaseSelf) -> None:
        GuardValues = LoadGuard()
        RepairValues = LoadRepair()
        HeaderLines = GuardValues["RenderLines"](GuardValues["LoadCanon"](), "#")
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            SafePath = RootPath / "Safe.py"
            SafePath.write_bytes(
                b"# SPDX-License-Identifier: damaged\n"
                b"# SPDX-FileCopyrightText: damaged\n\n"
                b"print('safe')\n"
            )
            CaseSelf.assertTrue(
                RepairValues["CanRepairMut"](SafePath, HeaderLines, "#")
            )
            CaseSelf.assertTrue(SafePath.read_bytes().endswith(b"print('safe')\n"))
            DocsPath = RootPath / "Docs.py"
            DocsBytes = (
                b"# SPDX-License-Identifier: damaged\n"
                b"# unrelated module documentation\n\n"
                b"print('safe')\n"
            )
            DocsPath.write_bytes(DocsBytes)
            CaseSelf.assertFalse(
                RepairValues["CanRepairMut"](DocsPath, HeaderLines, "#")
            )
            CaseSelf.assertEqual(DocsPath.read_bytes(), DocsBytes)
            EncodingPath = RootPath / "Encoding.py"
            EncodingBytes = (
                b"# coding: utf-8\n"
                b"# SPDX-License-Identifier: damaged\n\n"
                b"print('safe')\n"
            )
            EncodingPath.write_bytes(EncodingBytes)
            CaseSelf.assertFalse(
                RepairValues["CanRepairMut"](EncodingPath, HeaderLines, "#")
            )
            CaseSelf.assertEqual(EncodingPath.read_bytes(), EncodingBytes)


# format focused fixtures allow proven legacy styles without authorizing style guesses
class TestStyleGuard(UnitTest.TestCase):

    # unknown formats may retain a proven marker but must never receive a guessed missing style
    def TestUnkStyle(CaseSelf) -> None:
        GuardValues = LoadGuard()
        CanonLines = GuardValues["LoadCanon"]()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            DebugPath = RootPath / "Debug.trace"
            DebugPath.write_bytes(
                b"$$ SPDX-License-Identifier: damaged\n"
                b"$$ SPDX-FileCopyrightText: damaged\n\n"
                b"command\n"
            )
            IsFixed, ReasonText = GuardValues["RepairHeadMut"](
                DebugPath, CanonLines, RootPath
            )
            CaseSelf.assertTrue(IsFixed, ReasonText)
            CaseSelf.assertTrue(DebugPath.read_bytes().startswith(b"$$ SPDX-"))
            BlockPath = RootPath / "Markup.trace"
            BlockPath.write_bytes(
                b"<!--\n"
                b"SPDX-License-Identifier: damaged\n"
                b"SPDX-FileCopyrightText: damaged\n"
                b"-->\n\n"
                b"markup\n"
            )
            IsFixed, ReasonText = GuardValues["RepairHeadMut"](
                BlockPath, CanonLines, RootPath
            )
            CaseSelf.assertTrue(IsFixed, ReasonText)
            CaseSelf.assertTrue(BlockPath.read_bytes().startswith(b"<!--\nSPDX-"))
            MissingPath = RootPath / "Missing.trace"
            MissingPath.write_bytes(b"command\n")
            OriginalBytes = MissingPath.read_bytes()
            IsFixed, ReasonText = GuardValues["RepairHeadMut"](
                MissingPath, CanonLines, RootPath
            )
            CaseSelf.assertFalse(IsFixed, ReasonText)
            CaseSelf.assertEqual(MissingPath.read_bytes(), OriginalBytes)


# text focused fixtures keep malformed known source files inside the enforcement boundary
class TestTextGuard(UnitTest.TestCase):

    # known source formats must report invalid utf eight instead of being silently treated as binary
    def TestInvalidText(CaseSelf) -> None:
        GuardValues = LoadGuard()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            SourcePath = RootPath / "Invalid.py"
            SourcePath.write_bytes(b"\xff\xfe")
            IsValid, ReasonText = GuardValues["CheckFile"](
                SourcePath, GuardValues["LoadCanon"](), RootPath
            )
        CaseSelf.assertFalse(IsValid)
        CaseSelf.assertIn("UTF-8", ReasonText)


# path focused fixtures keep filesystem traversal limited to regular worktree files
class TestPathGuard(UnitTest.TestCase):

    # regular candidates pass while missing directories and lexical links never reach content checks
    def TestPathBound(CaseSelf) -> None:
        GuardValues = LoadGuard()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath).resolve()
            SourcePath = RootPath / "Source.py"
            SourcePath.write_text("source\n", encoding="utf-8")
            CaseSelf.assertEqual(
                GuardValues["ResolvePath"](RootPath, "Source.py"), SourcePath
            )
            CaseSelf.assertIsNone(GuardValues["ResolvePath"](RootPath, "Missing.py"))
            FolderPath = RootPath / "Folder"
            FolderPath.mkdir()
            CaseSelf.assertIsNone(GuardValues["ResolvePath"](RootPath, "Folder"))
            ChildPath = FolderPath / "Child.py"
            ChildPath.write_text("child\n", encoding="utf-8")
            with Mocking.patch.object(
                GuardValues["StatLib"], "S_ISLNK", return_value=True
            ):
                CaseSelf.assertIsNone(
                    GuardValues["ResolvePath"](RootPath, "Folder/Child.py")
                )


# skill focused fixtures preserve agent metadata while restoring its distinct license contract
class TestSkillGuard(UnitTest.TestCase):

    # agent skill repair stays inside the selected worktree and preserves all nonlicense frontmatter
    def TestSkillField(CaseSelf) -> None:
        GuardValues = LoadGuard()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            SkillPath = RootPath / ".agents" / "skills" / "alpha" / "SKILL.md"
            SkillPath.parent.mkdir(parents=True)
            SkillPath.write_bytes(
                b"---\r\nname: alpha\r\nlicense: damaged\r\n---\r\nbody\r\n"
            )
            IsFixed, ReasonText = GuardValues["RepairHeadMut"](
                SkillPath, GuardValues["LoadCanon"](), RootPath
            )
            CaseSelf.assertTrue(IsFixed, ReasonText)
            SourceBytes = SkillPath.read_bytes()
            CaseSelf.assertIn(
                b"license: LicenseRef-PolyForm-Strict-1.0.0\r\n", SourceBytes
            )
            CaseSelf.assertIn(b"name: alpha\r\n", SourceBytes)


# revision focused fixtures bind materialized files to one exact commit identity
class TestHeadGuard(UnitTest.TestCase):

    # exact commit and worktree checks prevent symbolic revisions or a stale materialized head
    def TestExactHead(CaseSelf) -> None:
        GuardValues = LoadGuard()
        with Tempfile.TemporaryDirectory() as TempPath:
            RootPath = Pathlib.Path(TempPath)
            FixtureInfo = RepoFixture(RootPath)
            FixtureInfo.WriteFile("Source.py")
            BaseRef = FixtureInfo.CommitAll("base")
            FixtureInfo.MoveFile("Source.py", "Target.py")
            HeadRef = FixtureInfo.CommitAll("head")
            CaseSelf.assertTrue(GuardValues["IsCommit"](HeadRef, RootPath))
            CaseSelf.assertFalse(GuardValues["IsCommit"]("HEAD", RootPath))
            CaseSelf.assertEqual(
                GuardValues["GetDiffFiles"](BaseRef, HeadRef, RootPath), ["Target.py"]
            )
            WorktreeRoot, ReasonText = GuardValues["CheckWorktree"](RootPath, HeadRef)
            CaseSelf.assertEqual(WorktreeRoot, RootPath.resolve(), ReasonText)
            WorktreeRoot, ReasonText = GuardValues["CheckWorktree"](RootPath, "0" * 40)
            CaseSelf.assertIsNone(WorktreeRoot, ReasonText)

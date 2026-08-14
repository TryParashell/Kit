# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import unittest as UnitTest

from tools.Policy.CheckPathPolicy import CheckPathPolicy
from tools.Policy.FormatFinding import FormatFinding
from tools.Policy.PathFinding import PathFinding


# combined policy coverage protects naming directory limits and changed target isolation together
class TestPathPolicy(UnitTest.TestCase):

    # ordinary violations remain visible while every deliberately narrow exception stays accepted
    def CheckNameRules(CaseSelf) -> None:
        TrackedPaths = (
            "Source/Alpha.py",
            "Source/bad_name.py",
            "Source/Thing2.py",
            "examples/vendor/bad_2.SLDPRT",
            ".kiro/skills/vendor/bad_2.py",
            "re/binaries/sldmfcu.dll",
        )
        FindingList = CheckPathPolicy(TrackedPaths)
        FailedPaths = {
            FindingInfo.RepoPath
            for FindingInfo in FindingList
            if FindingInfo.RuleCode == "PTH001"
        }
        CaseSelf.assertEqual(FailedPaths, {"Source/Thing2.py", "Source/bad_name.py"})

    # the first file beyond the boundary must force a focused subfolder decision
    def CheckCountCap(CaseSelf) -> None:
        TrackedPaths = tuple(
            f"Crowded/File{chr(65 + IndexValue // 26)}"
            f"{chr(65 + IndexValue % 26)}.py"
            for IndexValue in range(33)
        )
        FindingList = CheckPathPolicy(TrackedPaths)
        CountFindings = [
            FindingInfo
            for FindingInfo in FindingList
            if FindingInfo.RuleCode == "PTH002"
        ]
        CaseSelf.assertEqual(len(CountFindings), 1)
        CaseSelf.assertEqual(CountFindings[0].RepoPath, "Crowded")
        CaseSelf.assertIn("33 direct tracked files", CountFindings[0].MessageText)

    # changed mode judges only destination names and directories directly touched by the diff
    def CheckTargetDirs(CaseSelf) -> None:
        CrowdedPaths = tuple(
            f"Crowded/File{chr(65 + IndexValue // 26)}"
            f"{chr(65 + IndexValue % 26)}.py"
            for IndexValue in range(33)
        )
        TrackedPaths = (*CrowdedPaths, "Other/Alpha.py", "Legacy/bad_name.py")
        OtherFindings = CheckPathPolicy(TrackedPaths, ("Other/Alpha.py",))
        CaseSelf.assertEqual(OtherFindings, [])
        CrowdedFindings = CheckPathPolicy(TrackedPaths, (CrowdedPaths[0],))
        CaseSelf.assertEqual(
            [FindingInfo.RuleCode for FindingInfo in CrowdedFindings],
            ["PTH002"],
        )

    # stable ordering and escaped paths keep automation output comparable and line oriented
    def CheckOrdering(CaseSelf) -> None:
        TrackedPaths = ("Zulu/bad_two.py", "Alpha/bad_one.py")
        FindingList = CheckPathPolicy(TrackedPaths)
        CaseSelf.assertEqual(
            [FindingInfo.RepoPath for FindingInfo in FindingList],
            ["Alpha/bad_one.py", "Zulu/bad_two.py"],
        )
        FindingInfo = PathFinding("Line\nBreak.py", "PTH001", "invalid stem")
        RenderedText = FormatFinding(FindingInfo)
        CaseSelf.assertNotIn("\n", RenderedText)
        CaseSelf.assertIn("\\n", RenderedText)

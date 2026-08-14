# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import sys as System

from tools.descriptions import KDescriptions
from tools.skill_args import ParseArgs
from tools.skill_checker import CheckSkills
from tools.skill_specs import ValidateSpecs
from tools.skill_writer import WriteSkills


# one command coordinator keeps generation failures distinct from synchronization failures
def MainRun() -> int:
    ArgumentsData = ParseArgs()
    if ArgumentsData.write:
        ErrorList = ValidateSpecs()
        if ErrorList:
            print("Cannot write Agent Skills migration:", file=System.stderr)
            print(
                "\n".join(f"- {ErrorText}" for ErrorText in ErrorList),
                file=System.stderr,
            )
            return 1
        WriteSkills()
    ErrorList = CheckSkills()
    if ErrorList:
        print("Agent Skills migration check failed:", file=System.stderr)
        print(
            "\n".join(f"- {ErrorText}" for ErrorText in ErrorList),
            file=System.stderr,
        )
        return 1
    print(f"Agent Skills migration is current: {len(KDescriptions)} skills.")
    return 0

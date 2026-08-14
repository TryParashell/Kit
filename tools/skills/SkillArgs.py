# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import argparse as Argparse


# explicit modes prevent verification commands from mutating checked in generated files
def ParseArgs() -> Argparse.Namespace:
    ParserInfo = Argparse.ArgumentParser(
        description="Generate and verify the Agent Skills copy of Kiro steering."
    )
    ModeGroup = ParserInfo.add_mutually_exclusive_group()
    ModeGroup.add_argument(
        "--write",
        action="store_true",
        help="write the Agent Skills copy from .kiro/steering",
    )
    ModeGroup.add_argument(
        "--check",
        action="store_true",
        help="verify the Agent Skills copy without writing (the default)",
    )
    return ParserInfo.parse_args()

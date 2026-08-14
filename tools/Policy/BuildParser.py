# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import argparse as ArgParse
from pathlib import Path as FilePath


# dedicated parsing keeps automation flags stable while policy evaluation stays library friendly
def BuildParser() -> ArgParse.ArgumentParser:
    ParserInfo = ArgParse.ArgumentParser(
        description="Validate tracked repository paths and direct directory file counts."
    )
    ParserInfo.add_argument(
        "--root",
        dest="RootPath",
        type=FilePath,
        default=FilePath.cwd(),
        help="repository working tree path",
    )
    ParserInfo.add_argument(
        "--base",
        dest="BaseRef",
        help="base revision for changed destination mode",
    )
    ParserInfo.add_argument(
        "--head",
        dest="HeadRef",
        help="head revision for changed destination mode",
    )
    return ParserInfo

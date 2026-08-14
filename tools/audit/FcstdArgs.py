# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import argparse as Argparse
from pathlib import Path as FilePath

from tools.audit.FcstdContext import KRepositoryRoot


# explicit arguments keep recursive scope output mode and failure policy reviewable
def ParseArguments() -> Argparse.Namespace:
    ParserData = Argparse.ArgumentParser(
        description=(
            "Audit FCStd files through the CAD-free first-principles SOLIDWORKS "
            "writer. No CAD application or vendor automation is launched."
        )
    )
    ParserData.add_argument(
        "roots",
        nargs="*",
        type=FilePath,
        default=(KRepositoryRoot,),
        help="file or directory roots to scan recursively",
    )
    ParserData.add_argument(
        "--json",
        action="store_true",
        help="emit the complete machine-readable audit instead of one row per file",
    )
    ParserData.add_argument(
        "--require-vendor-loadable",
        action="store_true",
        help="return a non-zero status unless every discovered FCStd is vendor-loadable",
    )
    ParserData.add_argument("--worker-source", type=FilePath, help=Argparse.SUPPRESS)
    ParserData.add_argument("--worker-output", type=FilePath, help=Argparse.SUPPRESS)
    ParserData.add_argument("--worker-index", type=int, help=Argparse.SUPPRESS)
    return ParserData.parse_args()

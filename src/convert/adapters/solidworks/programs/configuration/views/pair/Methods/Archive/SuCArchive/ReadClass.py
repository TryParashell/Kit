# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import MethodProgram
from convert.adapters.solidworks.programs.Owners.Archive.SuCArchive.ReadClass import (
    KOwnerSites,
)


# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: MethodProgram = (
    KOwnerSites,
    {
        "AnnotationManager": (
            (0, 24, "SuCArchiveReadClass", "definition", ("moAnnotationView_c", 1)),
            (234, 2, "SuCArchiveReadClass", "null", 0),
            (236, 2, "SuCArchiveReadClass", "null", 0),
            (250, 2, "SuCArchiveReadClass", "null", 0),
            (260, 2, "SuCArchiveReadClass", "null", 0),
            (278, 2, "SuCArchiveReadClass", "classref", 101),
            (494, 2, "SuCArchiveReadClass", "null", 0),
            (496, 2, "SuCArchiveReadClass", "null", 0),
            (510, 2, "SuCArchiveReadClass", "null", 0),
            (520, 2, "SuCArchiveReadClass", "null", 0),
            (554, 2, "SuCArchiveReadClass", "null", 0),
            (580, 2, "SuCArchiveReadClass", "null", 0),
        ),
    },
)

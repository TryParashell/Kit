# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath
from tempfile import TemporaryDirectory
from typing import Iterator

import pytest as PytestLib


# supplies compliant temporary paths so test signatures remain valid under naming steering
@PytestLib.fixture
def TmpPath() -> Iterator[FilePath]:
    with TemporaryDirectory(prefix="KitSolidworks") as TempName:
        yield FilePath(TempName)

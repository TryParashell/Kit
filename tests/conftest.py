# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import unittest as Unittest
import inspect as Inspect
from pathlib import Path as FilePath

import pytest as Pytest

# mixed prefixes preserve legacy coverage while compliant method names replace generated aliases
KTestPrefixes = ("test", "Test", "Check")

# pytest dependency injection requires its reserved request spelling at runtime
KRequestSig = Inspect.Signature(
    [Inspect.Parameter("request", Inspect.Parameter.KEYWORD_ONLY)]
)


# repository collection needs unittest to honor the same names as native pytest
def EnableNames() -> None:
    setattr(Unittest.TestLoader, "testMethodPrefix", KTestPrefixes)


EnableNames()


# migrated tests need a compliant spelling without changing temporary directory lifetime
def GiveTmpPath(**FixtureValues: object) -> FilePath:
    RequestInfo = FixtureValues["request"]
    if not isinstance(RequestInfo, Pytest.FixtureRequest):
        raise TypeError("pytest request fixture has an unexpected type")
    TmpPath = RequestInfo.getfixturevalue("tmp_path")
    if not isinstance(TmpPath, FilePath):
        raise TypeError("pytest temporary path fixture has an unexpected type")
    return TmpPath


setattr(GiveTmpPath, "__signature__", KRequestSig)


# explicit fixture registration keeps pytest internals outside the compatibility seam
KTmpPathFix = Pytest.fixture(name="TmpPath")(GiveTmpPath)


# migrated tests need a compliant spelling while retaining automatic patch rollback
def GivePatch(**FixtureValues: object) -> Pytest.MonkeyPatch:
    RequestInfo = FixtureValues["request"]
    if not isinstance(RequestInfo, Pytest.FixtureRequest):
        raise TypeError("pytest request fixture has an unexpected type")
    PatchValue = RequestInfo.getfixturevalue("monkeypatch")
    if not isinstance(PatchValue, Pytest.MonkeyPatch):
        raise TypeError("pytest monkeypatch fixture has an unexpected type")
    return PatchValue


setattr(GivePatch, "__signature__", KRequestSig)


# explicit fixture registration keeps pytest internals outside the compatibility seam
KPatchFixture = Pytest.fixture(name="MonkeyPatch")(GivePatch)

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from email.parser import BytesParser as MailParser
from email.policy import default as DefaultPolicy
from typing import Any as AnyValue


# wheel metadata must keep runtime dependencies optional and entry points deterministic
def CheckWheelMeta(ArchiveData: AnyValue, EntryNames: tuple[str, ...]) -> None:
    WheelName = next(NameValue for NameValue in EntryNames if NameValue.endswith("/WHEEL"))
    MetadataName = next(
        NameValue for NameValue in EntryNames if NameValue.endswith("/METADATA")
    )
    EntryPointName = next(
        NameValue
        for NameValue in EntryNames
        if NameValue.endswith("/entry_points.txt")
    )
    WheelMetadata = ArchiveData.read(WheelName).decode("utf-8")
    assert "Root-Is-Purelib: true" in WheelMetadata
    assert "Tag: py3-none-any" in WheelMetadata
    MetadataInfo = MailParser(policy=DefaultPolicy).parsebytes(
        ArchiveData.read(MetadataName)
    )
    RequirementList = tuple(MetadataInfo.get_all("Requires-Dist", ()))
    ExtraNames = tuple(MetadataInfo.get_all("Provides-Extra", ()))
    ExtraMarkers = {
        MarkerText
        for ExtraName in ExtraNames
        for MarkerText in (f"extra == '{ExtraName}'", f'extra == "{ExtraName}"')
    }
    assert all(
        any(
            MarkerText in RequirementText.partition(";")[2]
            for MarkerText in ExtraMarkers
        )
        for RequirementText in RequirementList
    )
    assert ArchiveData.read(EntryPointName).decode("utf-8") == (
        "[kit]\nconvert = convert:convert\n"
    )

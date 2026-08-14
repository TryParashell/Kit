# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import re


# digit words keep generated filenames meaningful and free from numeric suffixes
KDigitWords = {
    "0": "Zero",
    "1": "One",
    "2": "Two",
    "3": "Three",
    "4": "Four",
    "5": "Five",
    "6": "Six",
    "7": "Seven",
    "8": "Eight",
    "9": "Nine",
}


# ordinal trace labels belong to shared semantic roles rather than numbered modules
KFoldRules = (
    (r"bounding box \d+ per body chooser index", "Synthetic/BodyChooserBoundingBoxes"),
    (
        r"display dimension(?: \d+)? derived scalar",
        "Synthetic/DisplayDimensionDerivedScalars",
    ),
    (
        r"display dimension(?: \d+)? direct slot",
        "Synthetic/DisplayDimensionDirectSlots",
    ),
    (r"display dimension(?: \d+)? index", "Synthetic/DisplayDimensionIndices"),
    (
        r"(?:sketch \d+ (?:first|second)|(?:first|second) sketch) chain entity (?:index|indices)",
        "Synthetic/SketchChainEntityIndices",
    ),
    (
        r"component edge \d+ bucket \d+ indices",
        "Synthetic/ComponentEdgeBucketIndices",
    ),
    (
        r"chamfer \d+ child \d+ surface identifiers",
        "Synthetic/ChamferChildSurfaceIdentifiers",
    ),
)


# callsite suffixes are metadata and must not create arbitrary serializer modules
def GetOwnerBase(OwnerText: str) -> str:
    return re.sub(r"\+0x[0-9a-fA-F]+$", "", OwnerText)


# generated path components need one deterministic pascal conversion across every owner
def MakePascal(NameText: str) -> str:
    ExpandedText = "".join(
        KDigitWords.get(CharText, CharText) for CharText in NameText
    )
    WordParts = re.findall(r"[A-Za-z]+", ExpandedText)
    PascalParts = (
        WordText.capitalize()
        if WordText.isupper() or WordText.islower()
        else WordText[0].upper() + WordText[1:]
        for WordText in WordParts
    )
    PascalText = "".join(PascalParts)
    if not PascalText:
        raise ValueError(f"owner component has no letters {NameText!r}")
    return PascalText


# each recovered native or synthetic responsibility needs one collision checked path
def GetGroupPath(OwnerText: str) -> str:
    OwnerBase = GetOwnerBase(OwnerText)
    LowerOwner = OwnerBase.lower()
    for PatternText, GroupPath in KFoldRules:
        if re.fullmatch(PatternText, LowerOwner):
            return GroupPath
    if "::" in OwnerBase:
        ScopeText, MethodText = OwnerBase.rsplit("::", 1)
        if "!" in ScopeText:
            LibraryText, ClassText = ScopeText.split("!", 1)
        else:
            LibraryText, ClassText = "Archive", ScopeText
        MethodText = {
            "operator>>": "ReadOperator",
            "operator<<": "WriteOperator",
        }.get(MethodText, MethodText)
        return "/".join(
            MakePascal(NameText)
            for NameText in (LibraryText, ClassText, MethodText)
        )
    if "!" in OwnerBase:
        LibraryText, MethodText = OwnerBase.split("!", 1)
        MethodText = {
            "operator>>": "ReadOperator",
            "operator<<": "WriteOperator",
        }.get(MethodText, MethodText)
        return "/".join(
            (MakePascal(LibraryText), "Functions", MakePascal(MethodText))
        )
    return "/".join(("Synthetic", MakePascal(OwnerBase)))


# stable callsite keys prevent new traces from renumbering unrelated generated operations
def GetOwnerKey(OwnerText: str) -> object:
    MatchData = re.search(r"\+0x([0-9a-fA-F]+)$", OwnerText)
    if MatchData is not None:
        return int(MatchData.group(1), 16)
    return MakePascal(OwnerText)

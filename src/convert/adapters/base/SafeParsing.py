# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Hardened untrusted-XML parsing shared by every CAD adapter."""

from __future__ import annotations as Annotations

from re import compile as CompilePattern
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import fromstring as ParseTreeText  # noqa: DUO107

# doctype detection stays lexical because every entity expansion vector requires one declared doctype
KDoctypeMark = CompilePattern("<![dD][oO][cC][tT][yY][pP][eE]")


# parsing rejects document types before feeding because references cannot expand without declarations
def ParseUntrusted(ValueData: str | bytes) -> Element:
    ScanValue = (
        ValueData.decode("latin-1") if isinstance(ValueData, bytes) else ValueData
    )
    if KDoctypeMark.search(ScanValue) is not None:
        raise ValueError("untrusted XML must not declare a doctype")
    return ParseTreeText(ValueData)

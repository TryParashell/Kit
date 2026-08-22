# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Hardened untrusted-XML parsing shared by every CAD adapter."""

from __future__ import annotations as Annotations

import defusedxml.ElementTree as SafeXmlTree
import xml.etree.ElementTree as XmlTree  # noqa: DUO107

# serialization aliases stay stdlib because hardened writers emit XML instead of parsing it
Element = XmlTree.Element


# this wrapper exists because adapters must never hand attacker-controlled bytes to parsing that
# permits DTDs, entity expansion, or external resolution, so every defense stays explicitly enabled
def ParseUntrusted(ValueData: str | bytes) -> Element:
    return SafeXmlTree.fromstring(
        ValueData,
        forbid_dtd=True,
        forbid_entities=True,
        forbid_external=True,
    )

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath


# one repository anchor prevents split api tests from duplicating path traversal logic
KRootPath = FilePath(__file__).parents[3]

# one solidworks sample covers native replay and cross format carrier behavior
KSamplePath = KRootPath / "examples" / ".SLDPRT" / "example.SLDPRT"

# one catia sample covers tessellation and exact native replay behavior
KCatPartPath = KRootPath / "examples" / ".CATPart" / "Banjo.CATPart"

# one freecad sample covers archive replay through the shared public api
KFcstdPath = (
    KRootPath / "examples" / "Random" / "V8_engine" / "hex bolt gradeb_iso.FCStd"
)

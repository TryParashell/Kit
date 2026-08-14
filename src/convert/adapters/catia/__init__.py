# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.catia.Adapter import CatiaAdapter, CatiaAdapterError, read_catia, write_catia
from convert.adapters.catia.Container import Cfv2Archive, Cfv2Declaration, Cfv2Directory, Cfv2Extent, Cfv2FormatError, Cfv2Stream, OsmxArchive, OsmxFormatError, OsmxSymbol, append_cfv2_stream, build_cfv2, build_declaration

__all__ = [name for name in globals() if not name.startswith("_")]

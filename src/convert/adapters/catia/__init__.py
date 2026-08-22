# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.catia.Adapter import (
    CatiaAdapter,
    CatiaAdapterError,
    read_catia as ReadCatia,
    write_catia as WriteCatia,
)
from convert.adapters.catia.Container import (
    Cfv2Archive as CfvTwoArchive,
    Cfv2Declaration as CfvTwoDecl,
    Cfv2Directory as CfvTwoFolder,
    Cfv2Extent as CfvTwoExtent,
    Cfv2FormatError as CfvTwoFormatError,
    Cfv2Stream as CfvTwoStream,
    OsmxArchive,
    OsmxFormatError,
    OsmxSymbol,
    append_cfv2_stream as AppendCfvTwoStream,
    build_cfv2 as BuildCfvTwo,
    build_declaration as BuildDecl,
)

# explicit exports keep the CATIA compatibility boundary visible to static analysis
__all__ = (
    "CatiaAdapter",
    "CatiaAdapterError",
    "Cfv2Archive",
    "Cfv2Declaration",
    "Cfv2Directory",
    "Cfv2Extent",
    "Cfv2FormatError",
    "Cfv2Stream",
    "OsmxArchive",
    "OsmxFormatError",
    "OsmxSymbol",
    "append_cfv2_stream",
    "build_cfv2",
    "build_declaration",
    "read_catia",
    "write_catia",
)

# this binding exists because shared behavior needs one stable value
Cfv2Archive = CfvTwoArchive

# this binding exists because shared behavior needs one stable value
Cfv2Declaration = CfvTwoDecl

# this binding exists because shared behavior needs one stable value
Cfv2Directory = CfvTwoFolder

# this binding exists because shared behavior needs one stable value
Cfv2Extent = CfvTwoExtent

# this binding exists because shared behavior needs one stable value
Cfv2FormatError = CfvTwoFormatError

# this binding exists because shared behavior needs one stable value
Cfv2Stream = CfvTwoStream

# this binding exists because shared behavior needs one stable value
append_cfv2_stream = AppendCfvTwoStream

# this binding exists because shared behavior needs one stable value
build_cfv2 = BuildCfvTwo

# this binding exists because shared behavior needs one stable value
build_declaration = BuildDecl

# this binding exists because shared behavior needs one stable value
read_catia = ReadCatia

# this binding exists because shared behavior needs one stable value
write_catia = WriteCatia

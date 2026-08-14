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

# this binding exists because shared behavior needs one stable value
KAllValue = [NameValue for NameValue in globals() if not NameValue.startswith("_")]

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Archive"] = CfvTwoArchive

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Declaration"] = CfvTwoDecl

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Directory"] = CfvTwoFolder

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Extent"] = CfvTwoExtent

# this binding exists because shared behavior needs one stable value
globals()["Cfv2FormatError"] = CfvTwoFormatError

# this binding exists because shared behavior needs one stable value
globals()["Cfv2Stream"] = CfvTwoStream

# this binding exists because shared behavior needs one stable value
globals()["append_cfv2_stream"] = AppendCfvTwoStream

# this binding exists because shared behavior needs one stable value
globals()["build_cfv2"] = BuildCfvTwo

# this binding exists because shared behavior needs one stable value
globals()["build_declaration"] = BuildDecl

# this binding exists because shared behavior needs one stable value
globals()["read_catia"] = ReadCatia

# this binding exists because shared behavior needs one stable value
globals()["write_catia"] = WriteCatia

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.enums.EnumBase import WireEnum


# payload roles distinguish representations so filtering never guesses from filenames
class PayloadRole(WireEnum):
    KBrep = "brep"
    KTessellation = "tessellation"
    KFeatureHistory = "feature_history"
    KAssemblyStructure = "assembly_structure"
    KDocument = "document"
    KVerification = "verification"
    KAuxiliary = "auxiliary"

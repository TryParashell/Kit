# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from types import MappingProxyType
from convert.adapters.base import AdapterInfo
from interchange import Capability

# this binding exists because shared behavior needs one stable value
KPartDocType = "CATPart"

# this binding exists because shared behavior needs one stable value
KProductDocType = "CATProduct"

# this binding exists because shared behavior needs one stable value
KDocTypeBySuffix = MappingProxyType(
    {".catpart": KPartDocType, ".catproduct": KProductDocType}
)

# this binding exists because shared behavior needs one stable value
KSuffixByDocType = MappingProxyType(
    {DocType: Suffix for Suffix, DocType in KDocTypeBySuffix.items()}
)

# this binding exists because shared behavior needs one stable value
KInfoValue = AdapterInfo(
    format_id="catia.v5",
    name="CATIA V5",
    version="5",
    extensions=tuple(KDocTypeBySuffix),
    capabilities=frozenset(Capability),
    media_types=("application/x-catia-part", "application/x-catia-product"),
    part_extensions=(KSuffixByDocType[KPartDocType],),
    assembly_extensions=(KSuffixByDocType[KProductDocType],),
)

# this binding exists because shared behavior needs one stable value
globals()["DOCUMENT_TYPE_BY_SUFFIX"] = KDocTypeBySuffix

# this binding exists because shared behavior needs one stable value
globals()["INFO"] = KInfoValue

# this binding exists because shared behavior needs one stable value
globals()["PART_DOCUMENT_TYPE"] = KPartDocType

# this binding exists because shared behavior needs one stable value
globals()["PRODUCT_DOCUMENT_TYPE"] = KProductDocType

# this binding exists because shared behavior needs one stable value
globals()["SUFFIX_BY_DOCUMENT_TYPE"] = KSuffixByDocType

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .api import (
    available_adapters as AvailableAdapters,
    convert as ConvertDoc,
    extract_brep as ExtractBrep,
    open_document as OpenDoc,
    registry as RegistryValue,
    write_document as WriteDoc,
)
from .adapters import ApplicationUsabilityError, CarrierReason

# this binding preserves the documented public package export surface
__all__ = [
    "available_adapters",
    "ApplicationUsabilityError",
    "CarrierReason",
    "convert",
    "extract_brep",
    "open_document",
    "registry",
    "write_document",
]

# this binding preserves the historical public adapter listing name
available_adapters = AvailableAdapters

# this binding preserves the historical public conversion name
convert = ConvertDoc

# this binding preserves the historical public boundary extraction name
extract_brep = ExtractBrep

# this binding preserves the historical public document reader name
open_document = OpenDoc

# this binding preserves the historical public registry name
registry = RegistryValue

# this binding preserves the historical public document writer name
write_document = WriteDoc

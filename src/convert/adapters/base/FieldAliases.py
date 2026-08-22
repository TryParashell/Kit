# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

# legacy contract fields remain readable while stored dataclass identifiers follow steering
KFieldAliases: TypeMap[str, str] = {
    "adapter": "AdapterName",
    "aliases": "AliasNames",
    "application_usable": "IsAppUsable",
    "assembly_extensions": "AssemblyExts",
    "bytes_written": "ByteCount",
    "capabilities": "Capabilities",
    "capability": "CapabilityData",
    "carrier_capabilities": "CarrierCaps",
    "carrier_reason": "CarrierCause",
    "confidence": "Confidence",
    "configuration": "ConfigName",
    "destination_format": "TargetFormat",
    "diagnostics": "Diagnostics",
    "dropped": "DroppedCaps",
    "extensions": "Extensions",
    "format_id": "FormatId",
    "include_brep": "IncludeBrep",
    "include_tessellation": "IncludeMesh",
    "media_types": "MediaTypes",
    "metadata": "MetadataMap",
    "mode": "TransferModeData",
    "name": "DisplayName",
    "native_capabilities": "NativeCaps",
    "near_lossless": "IsNearLossless",
    "overwrite": "Overwrite",
    "part_extensions": "PartExts",
    "path": "OutputPath",
    "reason": "ReasonText",
    "requirements": "Requirements",
    "roundtrip_safe": "IsRoundtripSafe",
    "strict": "StrictMode",
    "transferred_capabilities": "TransferCaps",
    "transfers": "Transfers",
    "validate": "Validate",
    "values": "OptionValues",
    "vendor_loadable": "IsVendorLoadable",
    "version": "VersionText",
}

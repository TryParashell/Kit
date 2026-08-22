# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

# stored dataclass identifiers follow steering while historical Pascal spellings
# remain accepted constructor keywords and readable attribute aliases
KFieldAliases: TypeMap[str, str] = {
    "AdapterName": "adapter",
    "AliasNames": "aliases",
    "IsAppUsable": "application_usable",
    "AssemblyExts": "assembly_extensions",
    "ByteCount": "bytes_written",
    "Capabilities": "capabilities",
    "CapabilityData": "capability",
    "CarrierCaps": "carrier_capabilities",
    "CarrierCause": "carrier_reason",
    "Confidence": "confidence",
    "ConfigName": "configuration",
    "TargetFormat": "destination_format",
    "Diagnostics": "diagnostics",
    "DroppedCaps": "dropped",
    "Extensions": "extensions",
    "FormatId": "format_id",
    "IncludeBrep": "include_brep",
    "IncludeMesh": "include_tessellation",
    "MediaTypes": "media_types",
    "MetadataMap": "metadata",
    "TransferModeData": "mode",
    "DisplayName": "name",
    "NativeCaps": "native_capabilities",
    "IsNearLossless": "near_lossless",
    "Overwrite": "overwrite",
    "PartExts": "part_extensions",
    "OutputPath": "path",
    "ReasonText": "reason",
    "Requirements": "requirements",
    "IsRoundtripSafe": "roundtrip_safe",
    "StrictMode": "strict",
    "TransferCaps": "transferred_capabilities",
    "Transfers": "transfers",
    "Validate": "validate",
    "OptionValues": "values",
    "IsVendorLoadable": "vendor_loadable",
    "VersionText": "version",
}

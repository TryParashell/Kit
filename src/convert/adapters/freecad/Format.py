# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from collections.abc import Mapping
from types import MappingProxyType
from convert.adapters.base import AdapterInfo, CarrierReason
from interchange import Capability
from convert.adapters.freecad.Protocol import (
    ASSEMBLY_JOINT_GROUP_TYPE_ID as AsmJointGroupTypeId,
    ASSEMBLY_LINK_TYPE_ID as AsmLinkTypeId,
    ASSEMBLY_ROOT_TYPE_ID as AsmRootTypeId,
    FEATURE_WRITE_TYPE_IDS as FeatureWriteTypeIds,
    SKETCH_TYPE_ID as SketchTypeId,
)

# this binding exists because shared behavior needs one stable value
KSuffix = ".FCStd"

# this binding exists because shared behavior needs one stable value
KCapabilityWriteTypeIds: Mapping[Capability, frozenset[str]] = MappingProxyType(
    {
        Capability.PARAMETERS: frozenset({"Spreadsheet::Sheet"}),
        Capability.PARAMETRIC_HISTORY: frozenset[str]().union(
            *FeatureWriteTypeIds.values()
        ),
        Capability.SUPPORT_PLANES: frozenset({"App::Plane"}),
        Capability.EDITABLE_SKETCHES: frozenset({SketchTypeId}),
        Capability.SELECTIONS: frozenset({"App::PropertyLinkSubList"}),
        Capability.BODY_STRUCTURE: frozenset({"App::Part"}),
        Capability.CONFIGURATIONS: frozenset(
            {"App::PropertyString:KitConfigurationId"}
        ),
        Capability.EXPRESSIONS: frozenset(
            {"App::PropertyExpressionEngine", "Spreadsheet::PropertySheet"}
        ),
        Capability.BREP: frozenset({"Part::PropertyPartShape"}),
        Capability.TESSELLATION: frozenset(
            {"Mesh::Feature", "Mesh::PropertyMeshKernel"}
        ),
        Capability.ASSEMBLIES: frozenset({AsmRootTypeId, AsmLinkTypeId, "App::Link"}),
        Capability.ASSEMBLY_MATES: frozenset(
            {AsmJointGroupTypeId, "App::PropertyEnumeration:JointType"}
        ),
        Capability.COMPONENT_DOCUMENTS: frozenset({"App::PropertyXLink"}),
        Capability.EXTERNAL_REFERENCES: frozenset({"App::PropertyXLink"}),
        Capability.MATERIALS: frozenset({"App::PropertyString:MaterialId"}),
        Capability.NATIVE_PAYLOADS: frozenset[str](),
        Capability.PROVENANCE: frozenset[str](),
        Capability.ROUNDTRIP_METADATA: frozenset[str](),
    }
)
if set(KCapabilityWriteTypeIds) != set(Capability):
    raise RuntimeError("FreeCAD capability write types are not exhaustive")

# this binding exists because shared behavior needs one stable value
KCapabilityCarrierReasons = MappingProxyType(
    {
        Capability.PARAMETERS: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.PARAMETRIC_HISTORY: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.SUPPORT_PLANES: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.EDITABLE_SKETCHES: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.SELECTIONS: CarrierReason.TARGET_UNSUPPORTED,
        Capability.BODY_STRUCTURE: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.CONFIGURATIONS: CarrierReason.TARGET_UNSUPPORTED,
        Capability.EXPRESSIONS: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.BREP: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.TESSELLATION: CarrierReason.SOURCE_OPAQUE,
        Capability.ASSEMBLIES: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.ASSEMBLY_MATES: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.COMPONENT_DOCUMENTS: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.EXTERNAL_REFERENCES: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.MATERIALS: CarrierReason.WRITER_UNIMPLEMENTED,
        Capability.NATIVE_PAYLOADS: CarrierReason.SOURCE_OPAQUE,
        Capability.PROVENANCE: CarrierReason.TARGET_UNSUPPORTED,
        Capability.ROUNDTRIP_METADATA: CarrierReason.TARGET_UNSUPPORTED,
    }
)
if set(KCapabilityCarrierReasons) != set(Capability):
    raise RuntimeError("FreeCAD capability carrier reasons are not exhaustive")

# this binding exists because shared behavior needs one stable value
KNativeCapabilities = frozenset(
    (Capability for Capability, TypeIds in KCapabilityWriteTypeIds.items() if TypeIds)
)

# this binding exists because shared behavior needs one stable value
KInfoValue = AdapterInfo(
    format_id="freecad.fcstd",
    name="FreeCAD FCStd",
    version="1.0",
    extensions=(KSuffix,),
    capabilities=frozenset(Capability),
    native_capabilities=KNativeCapabilities,
    media_types=("application/x-extension-fcstd",),
    part_extensions=(KSuffix,),
    assembly_extensions=(KSuffix,),
)

# this binding exists because shared behavior needs one stable value
KFormatId = KInfoValue.format_id

# this binding exists because shared behavior needs one stable value
ASSEMBLY_JOINT_GROUP_TYPE_ID = AsmJointGroupTypeId

# this binding exists because shared behavior needs one stable value
ASSEMBLY_LINK_TYPE_ID = AsmLinkTypeId

# this binding exists because shared behavior needs one stable value
ASSEMBLY_ROOT_TYPE_ID = AsmRootTypeId

# this binding exists because shared behavior needs one stable value
CAPABILITY_CARRIER_REASONS = KCapabilityCarrierReasons

# this binding exists because shared behavior needs one stable value
CAPABILITY_WRITE_TYPE_IDS = KCapabilityWriteTypeIds

# this binding exists because shared behavior needs one stable value
FEATURE_WRITE_TYPE_IDS = FeatureWriteTypeIds

# this binding exists because shared behavior needs one stable value
FORMAT_ID = KFormatId

# this binding exists because shared behavior needs one stable value
INFO = KInfoValue

# this binding exists because shared behavior needs one stable value
NATIVE_CAPABILITIES = KNativeCapabilities

# this binding exists because shared behavior needs one stable value
SKETCH_TYPE_ID = SketchTypeId

# this binding exists because shared behavior needs one stable value
SUFFIX = KSuffix

# this binding exists because shared behavior needs one stable value
annotations = Annotations

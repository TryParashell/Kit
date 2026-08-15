# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.enums.EnumBase import WireEnum


# diagnostic levels let callers distinguish recoverable degradation from invalid documents
class Severity(WireEnum):
    KInfo = "info"
    KWarning = "warning"
    KError = "error"


# capabilities make representation guarantees explicit for planning and validation
class Capability(WireEnum):
    KParameters = "parameters"
    KParamHistory = "parametric_history"
    KSupportPlanes = "support_planes"
    KEditableSketches = "editable_sketches"
    KSelections = "selections"
    KBodyStructure = "body_structure"
    KConfigurations = "configurations"
    KExpressions = "expressions"
    KBrep = "brep"
    KTessellation = "tessellation"
    KAssemblies = "assemblies"
    KAssemblyMates = "assembly_mates"
    KComponentDocs = "component_documents"
    KExternalRefs = "external_references"
    KMaterials = "materials"
    KNativePayloads = "native_payloads"
    KProvenance = "provenance"
    KRoundtripMeta = "roundtrip_metadata"

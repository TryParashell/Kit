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
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    KInfo = "info"
    KWarning = "warning"
    KError = "error"


# capabilities make representation guarantees explicit for planning and validation
class Capability(WireEnum):
    PARAMETERS = "parameters"
    PARAMETRIC_HISTORY = "parametric_history"
    SUPPORT_PLANES = "support_planes"
    EDITABLE_SKETCHES = "editable_sketches"
    SELECTIONS = "selections"
    BODY_STRUCTURE = "body_structure"
    CONFIGURATIONS = "configurations"
    EXPRESSIONS = "expressions"
    BREP = "brep"
    TESSELLATION = "tessellation"
    ASSEMBLIES = "assemblies"
    ASSEMBLY_MATES = "assembly_mates"
    COMPONENT_DOCUMENTS = "component_documents"
    EXTERNAL_REFERENCES = "external_references"
    MATERIALS = "materials"
    NATIVE_PAYLOADS = "native_payloads"
    PROVENANCE = "provenance"
    ROUNDTRIP_METADATA = "roundtrip_metadata"
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

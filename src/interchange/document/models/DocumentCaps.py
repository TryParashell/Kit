# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING as TypeChecking

from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumFeatures import FeatureKind
from interchange.payloads.PayloadRoles import PayloadRole

if TypeChecking:
    from interchange.document.models.DocumentModel import CadDocument


# inferred capability sets prevent stale declarations from overstating document content
def InferCaps(
    DocumentValue: CadDocument,
    *,
    RoundtripMeta: bool = False,
    **LegacyValues: bool,
) -> frozenset[Capability]:
    from interchange.document.models.DocumentProvenance import HasProvenance
    from interchange.document.models.DocumentWalk import WalkDocuments

    RemainingValues = dict(LegacyValues)
    if "roundtrip_metadata" in RemainingValues:
        RoundtripMeta = RemainingValues.pop("roundtrip_metadata")
    if RemainingValues:
        UnknownName = next(iter(RemainingValues))
        raise TypeError(f"InferCaps got an unexpected keyword argument {UnknownName!r}")
    DocumentValues = tuple(WalkDocuments(DocumentValue))
    AssemblyValues = tuple(
        ItemValue.assembly
        for ItemValue in DocumentValues
        if ItemValue.assembly is not None
    )
    Conditions = {
        Capability.KParameters: any(
            ItemValue.parameters for ItemValue in DocumentValues
        ),
        Capability.KParamHistory: any(
            FeatureValue.kind != FeatureKind.KImported
            for ItemValue in DocumentValues
            for FeatureValue in ItemValue.feature_timeline
        ),
        Capability.KSupportPlanes: any(
            ItemValue.support_planes for ItemValue in DocumentValues
        ),
        Capability.KEditableSketches: any(
            ItemValue.sketches for ItemValue in DocumentValues
        ),
        Capability.KSelections: any(
            ItemValue.selections for ItemValue in DocumentValues
        ),
        Capability.KBodyStructure: any(
            ItemValue.bodies for ItemValue in DocumentValues
        ),
        Capability.KConfigurations: any(
            ItemValue.configurations for ItemValue in DocumentValues
        ),
        Capability.KExpressions: any(
            ParamValue.expression is not None
            for ItemValue in DocumentValues
            for ParamValue in ItemValue.parameters
        ),
        Capability.KBrep: any(
            ItemValue.brep is not None
            or any(
                PayloadValue.role == PayloadRole.KBrep and PayloadValue.data is not None
                for PayloadValue in ItemValue.brep_payloads
            )
            for ItemValue in DocumentValues
        ),
        Capability.KTessellation: any(ItemValue.meshes for ItemValue in DocumentValues)
        or any(
            PayloadValue.role == PayloadRole.KTessellation
            and PayloadValue.data is not None
            for ItemValue in DocumentValues
            for PayloadValue in ItemValue.brep_payloads
        ),
        Capability.KAssemblies: bool(AssemblyValues),
        Capability.KAssemblyMates: any(
            AssemblyValue.mates for AssemblyValue in AssemblyValues
        ),
        Capability.KComponentDocs: any(
            AssemblyValue.documents for AssemblyValue in AssemblyValues
        ),
        Capability.KExternalRefs: any(
            DefinitionValue.source_path
            for AssemblyValue in AssemblyValues
            for DefinitionValue in AssemblyValue.definitions
        ),
        Capability.KMaterials: any(
            BodyValue.material_id
            for ItemValue in DocumentValues
            for BodyValue in ItemValue.bodies
        ),
        Capability.KNativePayloads: any(
            ItemValue.brep_payloads for ItemValue in DocumentValues
        ),
        Capability.KProvenance: HasProvenance(DocumentValue),
        Capability.KRoundtripMeta: RoundtripMeta,
    }
    if Conditions.keys() != set(Capability):
        raise RuntimeError("CapabilityValue inference is not exhaustive")
    return frozenset(
        CapabilityValue
        for CapabilityValue, IsPresent in Conditions.items()
        if IsPresent
    )


# filtered documents must not advertise geometry that no longer remains
def GetRetainedCaps(
    DocumentValue: CadDocument,
    Capabilities: frozenset[Capability],
    *,
    IncludeBrep: bool = True,
    IncludeMesh: bool = True,
    **LegacyValues: bool,
) -> frozenset[Capability]:
    from interchange.document.models.DocumentWalk import WalkDocuments

    RemainingValues = dict(LegacyValues)
    if "include_brep" in RemainingValues:
        IncludeBrep = RemainingValues.pop("include_brep")
    if "include_tessellation" in RemainingValues:
        IncludeMesh = RemainingValues.pop("include_tessellation")
    if RemainingValues:
        UnknownName = next(iter(RemainingValues))
        raise TypeError(
            f"GetRetainedCaps got an unexpected keyword argument {UnknownName!r}"
        )
    RetainedCaps = set(Capabilities)
    if not IncludeBrep:
        RetainedCaps.discard(Capability.KBrep)
    DocumentValues = tuple(WalkDocuments(DocumentValue))
    if not IncludeMesh and not any(
        ItemValue.meshes
        or any(
            PayloadValue.role == PayloadRole.KTessellation
            and PayloadValue.data is not None
            for PayloadValue in ItemValue.brep_payloads
        )
        for ItemValue in DocumentValues
    ):
        RetainedCaps.discard(Capability.KTessellation)
    if not any(ItemValue.brep_payloads for ItemValue in DocumentValues):
        RetainedCaps.discard(Capability.KNativePayloads)
    return frozenset(RetainedCaps)

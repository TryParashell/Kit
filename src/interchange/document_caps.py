# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING as TypeChecking

from .enum_document import Capability
from .enum_features import FeatureKind
from .payload_roles import PayloadRole

if TypeChecking:
    from .document_model import CadDocument


# inferred capability sets prevent stale declarations from overstating document content
def InferCaps(
    DocumentValue: CadDocument,
    *,
    RoundtripMeta: bool = False,
    **LegacyValues: bool,
) -> frozenset[Capability]:
    from .document_provenance import HasProvenance
    from .document_walk import WalkDocuments

    RemainingValues = dict(LegacyValues)
    if "roundtrip_metadata" in RemainingValues:
        RoundtripMeta = RemainingValues.pop("roundtrip_metadata")
    if RemainingValues:
        UnknownName = next(iter(RemainingValues))
        raise TypeError(f"InferCaps got an unexpected keyword argument {UnknownName!r}")
    DocumentValues = tuple(WalkDocuments(DocumentValue))
    AssemblyValues = tuple(
        ItemValue.Assembly
        for ItemValue in DocumentValues
        if ItemValue.Assembly is not None
    )
    Conditions = {
        Capability.KParameters: any(
            ItemValue.Parameters for ItemValue in DocumentValues
        ),
        Capability.KParamHistory: any(
            FeatureValue.EntityKind != FeatureKind.KImported
            for ItemValue in DocumentValues
            for FeatureValue in ItemValue.FeatureTimeline
        ),
        Capability.KSupportPlanes: any(
            ItemValue.SupportPlanes for ItemValue in DocumentValues
        ),
        Capability.KEditableSketches: any(
            ItemValue.Sketches for ItemValue in DocumentValues
        ),
        Capability.KSelections: any(
            ItemValue.Selections for ItemValue in DocumentValues
        ),
        Capability.KBodyStructure: any(
            ItemValue.Bodies for ItemValue in DocumentValues
        ),
        Capability.KConfigurations: any(
            ItemValue.Configurations for ItemValue in DocumentValues
        ),
        Capability.KExpressions: any(
            ParamValue.Expression is not None
            for ItemValue in DocumentValues
            for ParamValue in ItemValue.Parameters
        ),
        Capability.KBrep: any(
            ItemValue.BrepModel is not None
            or any(
                PayloadValue.ValueRole == PayloadRole.KBrep
                and PayloadValue.PayloadData is not None
                for PayloadValue in ItemValue.BrepPayloads
            )
            for ItemValue in DocumentValues
        ),
        Capability.KTessellation: any(ItemValue.Meshes for ItemValue in DocumentValues)
        or any(
            PayloadValue.ValueRole == PayloadRole.KTessellation
            and PayloadValue.PayloadData is not None
            for ItemValue in DocumentValues
            for PayloadValue in ItemValue.BrepPayloads
        ),
        Capability.KAssemblies: bool(AssemblyValues),
        Capability.KAssemblyMates: any(
            AssemblyValue.Mates for AssemblyValue in AssemblyValues
        ),
        Capability.KComponentDocs: any(
            AssemblyValue.Documents for AssemblyValue in AssemblyValues
        ),
        Capability.KExternalRefs: any(
            DefinitionValue.SourcePath
            for AssemblyValue in AssemblyValues
            for DefinitionValue in AssemblyValue.Definitions
        ),
        Capability.KMaterials: any(
            BodyValue.MaterialId
            for ItemValue in DocumentValues
            for BodyValue in ItemValue.Bodies
        ),
        Capability.KNativePayloads: any(
            ItemValue.BrepPayloads for ItemValue in DocumentValues
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
    from .document_walk import WalkDocuments

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
        ItemValue.Meshes
        or any(
            PayloadValue.ValueRole == PayloadRole.KTessellation
            and PayloadValue.PayloadData is not None
            for PayloadValue in ItemValue.BrepPayloads
        )
        for ItemValue in DocumentValues
    ):
        RetainedCaps.discard(Capability.KTessellation)
    if not any(ItemValue.BrepPayloads for ItemValue in DocumentValues):
        RetainedCaps.discard(Capability.KNativePayloads)
    return frozenset(RetainedCaps)

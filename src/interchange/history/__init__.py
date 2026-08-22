# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as DataClass
from inspect import Signature as FuncSig
from typing import ClassVar
from typing import TYPE_CHECKING

from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureContract import FeatureDef
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.features.FeatureKinds import (
    ChamferFeature,
    CirclePattern,
    CombineFeature,
    DomeFeature,
    FilletFeature,
    HoleFeature,
    LinearPattern,
    MoveBodyFeature,
    NativeFeature,
    RefPlaneFeature,
    RevolveFeature,
    ScaleFeature,
    ShellFeature,
)
from interchange.features.FeatureStep import FeatureCfgState, FeatureStep
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.core.ModelBase import ModelBase
from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.compatibility.PythonCompatHistoryMethods import BindHistoryMut
from interchange.records.RecordTopology import TopologyCounts


# adapter capability sets centralize feature support checks for conversion decisions
@DataClass(frozen=True, slots=True)
class AdapterCaps(ModelBase):
    Values: frozenset[Capability] = frozenset()

    # historical constructor keywords must remain accepted without changing canonical storage
    def __init__(
        self,
        Values: frozenset[Capability] = frozenset(),
    ) -> None:
        object.__setattr__(self, "Values", Values)

    # callers need one consistent containment check for adapter support declarations
    def HasCapability(self, CapabilityValue: Capability) -> bool:
        return CapabilityValue in self.Values

    if TYPE_CHECKING:
        values: ClassVar[frozenset[Capability]]
        supports = HasCapability


BindCompatMut(
    (
        FeatureCfgState,
        ExtrudeFeature,
        FilletFeature,
        RevolveFeature,
        HoleFeature,
        ChamferFeature,
        ShellFeature,
        LinearPattern,
        CirclePattern,
        RefPlaneFeature,
        DomeFeature,
        MoveBodyFeature,
        CombineFeature,
        ScaleFeature,
        NativeFeature,
        FeatureStep,
        TopologyCounts,
        DesignBody,
        BrepPayload,
        AdapterCaps,
    ),
    {__name__: globals()},
)
BindHistoryMut(AdapterCaps)

for FeatureAttrName, FeatureAttrValue in {
    "__name__": "ExtrusionEndCondition",
    "__qualname__": "ExtrusionEndCondition",
    "__module__": __name__,
}.items():
    setattr(ExtrudeEnd, FeatureAttrName, FeatureAttrValue)
for PayloadAttrName, PayloadAttrValue in {"__module__": __name__}.items():
    setattr(PayloadRole, PayloadAttrName, PayloadAttrValue)
for DefinitionAttrName, DefinitionAttrValue in {
    "__name__": "FeatureDefinition",
    "__qualname__": "FeatureDefinition",
    "__module__": __name__,
    "__signature__": FuncSig(),
}.items():
    setattr(FeatureDef, DefinitionAttrName, DefinitionAttrValue)
for TopologyAttrName, TopologyAttrValue in {"__module__": __name__}.items():
    setattr(TopologyCounts, TopologyAttrName, TopologyAttrValue)

ExtrusionEndCondition = ExtrudeEnd
FeatureDefinition = FeatureDef
TopologySummary = TopologyCounts
AdapterCapabilities = AdapterCaps
Body = DesignBody
CircularPatternFeature = CirclePattern
ExtrusionFeature = ExtrudeFeature
FeatureConfigurationState = FeatureCfgState
LinearPatternFeature = LinearPattern
NativeFeatureDefinition = NativeFeature
ReferencePlaneFeature = RefPlaneFeature
RevolutionFeature = RevolveFeature


# legacy module exports stay explicit so integrations cannot depend on implementation details
__all__ = (
    "AdapterCapabilities",
    "Body",
    "BrepPayload",
    "ChamferFeature",
    "CircularPatternFeature",
    "CombineFeature",
    "DomeFeature",
    "ExtrusionEndCondition",
    "ExtrusionFeature",
    "FeatureConfigurationState",
    "FeatureDefinition",
    "FeatureStep",
    "FilletFeature",
    "HoleFeature",
    "LinearPatternFeature",
    "MoveBodyFeature",
    "NativeFeatureDefinition",
    "PayloadRole",
    "ReferencePlaneFeature",
    "RevolutionFeature",
    "ScaleFeature",
    "ShellFeature",
    "TopologySummary",
)

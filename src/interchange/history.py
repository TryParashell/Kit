# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as DataClass
from inspect import Signature as FuncSig

from .enum_document import Capability
from .feature_body import DesignBody
from .feature_contract import FeatureDef
from .feature_extrude import ExtrudeEnd, ExtrudeFeature
from .feature_kinds import (
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
from .feature_step import FeatureCfgState, FeatureStep
from .payload_record import BrepPayload
from .payload_roles import PayloadRole
from .model_base import ModelBase
from .python_compat import BindCompatMut
from .python_compat_history_methods import BindHistoryMut
from .record_topology import TopologyCounts


# adapter capability sets centralize feature support checks for conversion decisions
@DataClass(frozen=True, slots=True)
class AdapterCaps(ModelBase):
    Values: frozenset[Capability] = frozenset()

    # historical constructor keywords must remain accepted without changing canonical storage
    def __init__(
        SelfValue,
        Values: frozenset[Capability] = frozenset(),
    ) -> None:
        object.__setattr__(SelfValue, "Values", Values)

    # callers need one consistent containment check for adapter support declarations
    def HasCapability(SelfValue, CapabilityValue: Capability) -> bool:
        return CapabilityValue in SelfValue.Values


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

for AttrName, AttrValue in {
    "__name__": "ExtrusionEndCondition",
    "__qualname__": "ExtrusionEndCondition",
    "__module__": __name__,
}.items():
    setattr(ExtrudeEnd, AttrName, AttrValue)
for AttrName, AttrValue in {"__module__": __name__}.items():
    setattr(PayloadRole, AttrName, AttrValue)
for AttrName, AttrValue in {
    "__name__": "FeatureDefinition",
    "__qualname__": "FeatureDefinition",
    "__module__": __name__,
    "__signature__": FuncSig(),
}.items():
    setattr(FeatureDef, AttrName, AttrValue)
for AttrName, AttrValue in {"__module__": __name__}.items():
    setattr(TopologyCounts, AttrName, AttrValue)

globals().update(
    {
        "ExtrusionEndCondition": ExtrudeEnd,
        "FeatureDefinition": FeatureDef,
        "TopologySummary": TopologyCounts,
    }
)


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

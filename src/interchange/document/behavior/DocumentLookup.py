# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Protocol as TypeProtocol
from typing import TypeVar

from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane


# generic lookup results remain the exact model type stored by each collection
EntityType = TypeVar("EntityType")


# document lookup needs only the four collections exposed by its focused behavior
class LookupDocument(TypeProtocol):
    Parameters: tuple[Parameter, ...]
    Sketches: tuple[Sketch, ...]
    FeatureTimeline: tuple[FeatureStep, ...]
    SupportPlanes: tuple[SupportPlane, ...]


# dynamic compatibility callers need one checked identifier boundary
def GetEntityId(SourceValue: object) -> str:
    RawValue: object = getattr(SourceValue, "EntityId", None)
    if not isinstance(RawValue, str):
        raise TypeError("lookup entities must expose a string identifier")
    return RawValue


# entity lookup keeps every document convenience method on one failure contract
def FindEntity(
    ItemValues: tuple[EntityType, ...], EntityId: str, LabelText: str
) -> EntityType:
    for ItemValue in ItemValues:
        if GetEntityId(ItemValue) == EntityId:
            return ItemValue
    raise KeyError(f"unknown {LabelText} id {EntityId!r}")


# parameter access hides storage details from document consumers
def GetParameter(DocumentValue: LookupDocument, EntityId: str) -> Parameter:
    return FindEntity(DocumentValue.Parameters, EntityId, "parameter")


# sketch access hides storage details from document consumers
def GetSketch(DocumentValue: LookupDocument, EntityId: str) -> Sketch:
    return FindEntity(DocumentValue.Sketches, EntityId, "sketch")


# feature access hides timeline storage details from document consumers
def GetFeature(DocumentValue: LookupDocument, EntityId: str) -> FeatureStep:
    return FindEntity(DocumentValue.FeatureTimeline, EntityId, "feature")


# plane access hides support storage details from document consumers
def GetPlane(DocumentValue: LookupDocument, EntityId: str) -> SupportPlane:
    return FindEntity(DocumentValue.SupportPlanes, EntityId, "plane")

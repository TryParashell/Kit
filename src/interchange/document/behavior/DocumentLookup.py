# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Protocol as TypeProtocol
from typing import runtime_checkable as RuntimeCheck
from typing import TypeVar

from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane


# lookup entities share a concrete lowercase identity contract across model domains
class Identified(TypeProtocol):

    # immutable model identities remain readable through the narrow lookup contract
    @property
    def id(self) -> str: ...  # lgtm[py/ineffectual-statement]


# generic lookup results remain the exact model type stored by each collection
EntityType = TypeVar("EntityType", bound=Identified)


# document lookup needs only the four collections exposed by its focused behavior
@RuntimeCheck
class LookupDocument(TypeProtocol):
    parameters: tuple[Parameter, ...]
    sketches: tuple[Sketch, ...]
    feature_timeline: tuple[FeatureStep, ...]
    support_planes: tuple[SupportPlane, ...]


# behavior mixins validate their concrete document before relying on storage fields
def GetLookupDoc(SourceValue: object) -> LookupDocument:
    if not isinstance(SourceValue, LookupDocument):
        raise TypeError("lookup requires document collections")
    return SourceValue


# entity lookup keeps every document convenience method on one failure contract
def FindEntity(
    ItemValues: tuple[EntityType, ...], EntityId: str, LabelText: str
) -> EntityType:
    for ItemValue in ItemValues:
        if ItemValue.id == EntityId:
            return ItemValue
    raise KeyError(f"unknown {LabelText} id {EntityId!r}")


# parameter access hides storage details from document consumers
def GetParameter(DocumentValue: LookupDocument, EntityId: str) -> Parameter:
    return FindEntity(DocumentValue.parameters, EntityId, "parameter")


# sketch access hides storage details from document consumers
def GetSketch(DocumentValue: LookupDocument, EntityId: str) -> Sketch:
    return FindEntity(DocumentValue.sketches, EntityId, "sketch")


# feature access hides timeline storage details from document consumers
def GetFeature(DocumentValue: LookupDocument, EntityId: str) -> FeatureStep:
    return FindEntity(DocumentValue.feature_timeline, EntityId, "feature")


# plane access hides support storage details from document consumers
def GetPlane(DocumentValue: LookupDocument, EntityId: str) -> SupportPlane:
    return FindEntity(DocumentValue.support_planes, EntityId, "plane")

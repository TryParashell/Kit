# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue

from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane


# entity lookup keeps every document convenience method on one failure contract
def FindEntity(
    ItemValues: tuple[AnyValue, ...], EntityId: str, LabelText: str
) -> AnyValue:
    for ItemValue in ItemValues:
        if ItemValue.EntityId == EntityId:
            return ItemValue
    raise KeyError(f"unknown {LabelText} id {EntityId!r}")


# parameter access hides storage details from document consumers
def GetParameter(DocumentValue: AnyValue, EntityId: str) -> Parameter:
    return FindEntity(DocumentValue.Parameters, EntityId, "parameter")


# sketch access hides storage details from document consumers
def GetSketch(DocumentValue: AnyValue, EntityId: str) -> Sketch:
    return FindEntity(DocumentValue.Sketches, EntityId, "sketch")


# feature access hides timeline storage details from document consumers
def GetFeature(DocumentValue: AnyValue, EntityId: str) -> FeatureStep:
    return FindEntity(DocumentValue.FeatureTimeline, EntityId, "feature")


# plane access hides support storage details from document consumers
def GetPlane(DocumentValue: AnyValue, EntityId: str) -> SupportPlane:
    return FindEntity(DocumentValue.SupportPlanes, EntityId, "plane")

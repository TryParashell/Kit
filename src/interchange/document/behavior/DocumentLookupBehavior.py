# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import TYPE_CHECKING as TypeChecking

from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane


# document lookup methods preserve convenient access without owning collection storage
class DocumentLookup:
    locals()["__slots__"] = ()
    if TypeChecking:
        parameters: tuple[Parameter, ...]
        sketches: tuple[Sketch, ...]
        feature_timeline: tuple[FeatureStep, ...]
        support_planes: tuple[SupportPlane, ...]

    # parameter lookup uses its public spelling so its return type remains concrete
    def parameter(self, entity_id: str) -> Parameter:
        from interchange.document.behavior.DocumentLookup import (
            GetLookupDoc,
            GetParameter,
        )

        return GetParameter(GetLookupDoc(self), entity_id)

    # sketch lookup uses its public spelling so its return type remains concrete
    def sketch(self, entity_id: str) -> Sketch:
        from interchange.document.behavior.DocumentLookup import GetLookupDoc, GetSketch

        return GetSketch(GetLookupDoc(self), entity_id)

    # feature lookup uses its public spelling so its return type remains concrete
    def feature(self, entity_id: str) -> FeatureStep:
        from interchange.document.behavior.DocumentLookup import (
            GetFeature,
            GetLookupDoc,
        )

        return GetFeature(GetLookupDoc(self), entity_id)

    # plane lookup uses its public spelling so its return type remains concrete
    def plane(self, entity_id: str) -> SupportPlane:
        from interchange.document.behavior.DocumentLookup import GetLookupDoc, GetPlane

        return GetPlane(GetLookupDoc(self), entity_id)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def GetParameter(self, EntityId: str) -> Parameter:
        return self.parameter(EntityId)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def GetSketch(self, EntityId: str) -> Sketch:
        return self.sketch(EntityId)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def GetFeature(self, EntityId: str) -> FeatureStep:
        return self.feature(EntityId)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def GetPlane(self, EntityId: str) -> SupportPlane:
        return self.plane(EntityId)

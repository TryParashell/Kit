# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .feature_step import FeatureStep
from .record_parameter import Parameter
from .sketch import Sketch
from .support_plane import SupportPlane


# document lookup methods preserve convenient access without owning collection storage
class DocumentLookup:
    locals()["__slots__"] = ()

    # parameter lookup remains discoverable without coupling storage to callers
    def GetParameter(SelfValue, EntityId: str) -> Parameter:
        from .document_lookup import GetParameter

        return GetParameter(SelfValue, EntityId)

    # sketch lookup remains discoverable without coupling storage to callers
    def GetSketch(SelfValue, EntityId: str) -> Sketch:
        from .document_lookup import GetSketch

        return GetSketch(SelfValue, EntityId)

    # feature lookup remains discoverable without coupling timeline storage to callers
    def GetFeature(SelfValue, EntityId: str) -> FeatureStep:
        from .document_lookup import GetFeature

        return GetFeature(SelfValue, EntityId)

    # plane lookup remains discoverable without coupling support storage to callers
    def GetPlane(SelfValue, EntityId: str) -> SupportPlane:
        from .document_lookup import GetPlane

        return GetPlane(SelfValue, EntityId)

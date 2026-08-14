# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector

# explicit facade exports preserve historical imports while keeping ownership discoverable
__all__ = ["BoundingBox", "PlaneVector", "SpaceVector", "Transform"]

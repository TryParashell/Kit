# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

# historical api identity set 2 keeps pickle globals stable after module splits
KLegacyApiTwo: TypeMap[str, tuple[str, str]] = {
    "HoleFeature": ("HoleFeature", "interchange.history"),
    "ChamferFeature": ("ChamferFeature", "interchange.history"),
    "ShellFeature": ("ShellFeature", "interchange.history"),
    "LinearPattern": ("LinearPatternFeature", "interchange.history"),
    "CirclePattern": ("CircularPatternFeature", "interchange.history"),
    "RefPlaneFeature": ("ReferencePlaneFeature", "interchange.history"),
    "DomeFeature": ("DomeFeature", "interchange.history"),
    "MoveBodyFeature": ("MoveBodyFeature", "interchange.history"),
    "CombineFeature": ("CombineFeature", "interchange.history"),
    "ScaleFeature": ("ScaleFeature", "interchange.history"),
    "NativeFeature": ("NativeFeatureDefinition", "interchange.history"),
    "FeatureStep": ("FeatureStep", "interchange.history"),
    "TopologyCounts": ("TopologySummary", "interchange.history"),
    "DesignBody": ("Body", "interchange.history"),
    "BrepPayload": ("BrepPayload", "interchange.history"),
    "AdapterCaps": ("AdapterCapabilities", "interchange.history"),
    "SurfaceMesh": ("Mesh", "interchange.mesh"),
}

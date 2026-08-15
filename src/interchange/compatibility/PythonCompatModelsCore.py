# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap


# historical core model identity keeps pickle globals stable across internal splits
KLegacyCore: TypeMap[str, tuple[str, str]] = {
    "TransformMatrix": ("Matrix4", "interchange.assembly"),
    "ComponentDoc": ("ComponentDocument", "interchange.assembly"),
    "ComponentDef": ("ComponentDefinition", "interchange.assembly"),
    "ComponentInst": ("ComponentInstance", "interchange.assembly"),
    "MateEntity": ("MateEntity", "interchange.assembly"),
    "MateConstraint": ("MateConstraint", "interchange.assembly"),
    "MateGroup": ("MateGroup", "interchange.assembly"),
    "AssemblyData": ("AssemblyData", "interchange.assembly"),
    "PlaneVector": ("Vector2", "interchange.types"),
    "SpaceVector": ("Vector3", "interchange.types"),
    "Transform": ("Transform", "interchange.types"),
    "BoundingBox": ("BoundingBox", "interchange.types"),
    "ProvenanceSpan": ("ProvenanceSpan", "interchange.types"),
    "Provenance": ("Provenance", "interchange.types"),
    "ParameterValue": ("ParameterValue", "interchange.types"),
    "Expression": ("Expression", "interchange.types"),
    "Parameter": ("Parameter", "interchange.types"),
    "ParamOverride": ("ParameterOverride", "interchange.types"),
    "Configuration": ("Configuration", "interchange.types"),
    "CadSource": ("CadSource", "interchange.types"),
    "Diagnostic": ("Diagnostic", "interchange.types"),
}

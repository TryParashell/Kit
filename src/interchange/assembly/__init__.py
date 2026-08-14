# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.assembly.AssemblyData import AssemblyData
from interchange.assembly.AssemblyEnums import (
    ComponentKind,
    MateAlignment,
    MateEntityKind,
    MateKind,
)
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentDocument import ComponentDoc
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.compatibility.PythonCompatAssemblyMethods import BindAssemblyMut
from interchange.compatibility.PublicMetadata import BindModules
from interchange.assembly.TransformMatrix import TransformMatrix

BindModules((ComponentKind, MateAlignment, MateEntityKind, MateKind), __name__)

BindCompatMut(
    (
        TransformMatrix,
        ComponentDoc,
        ComponentDef,
        ComponentInst,
        MateEntity,
        MateConstraint,
        MateGroup,
        AssemblyData,
    ),
    {__name__: globals()},
)
BindAssemblyMut(AssemblyData, TransformMatrix)

# assembly consumers need one intentional historical public contract
__all__ = (
    "AssemblyData",
    "ComponentDefinition",
    "ComponentDocument",
    "ComponentInstance",
    "ComponentKind",
    "MateAlignment",
    "MateConstraint",
    "MateEntity",
    "MateEntityKind",
    "MateGroup",
    "MateKind",
    "Matrix4",
)

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .assembly_data import AssemblyData
from .assembly_enums import ComponentKind, MateAlignment, MateEntityKind, MateKind
from .component_definition import ComponentDef
from .component_document import ComponentDoc
from .component_instance import ComponentInst
from .mate_constraint import MateConstraint
from .mate_entity import MateEntity
from .mate_group import MateGroup
from .python_compat import BindCompatMut
from .python_compat_assembly_methods import BindAssemblyMut
from .transform_matrix import TransformMatrix

ComponentKind.__module__ = __name__
MateAlignment.__module__ = __name__
MateEntityKind.__module__ = __name__
MateKind.__module__ = __name__

# historical defining module identity preserves direct imports and existing pickle payloads
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

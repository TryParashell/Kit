# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramComposer import BuildProgram
from convert.adapters.solidworks.programs.configuration.pattern.views.Methods.Archive.SuCArchive.ReadClass import (
    KMethodProgram as KMethodA,
)
from convert.adapters.solidworks.programs.configuration.pattern.views.Methods.Archive.SuCArchive.WriteString import (
    KMethodProgram as KMethodB,
)
from convert.adapters.solidworks.programs.configuration.pattern.views.Methods.Sldmgu.MgMatrixC.Restore import (
    KMethodProgram as KMethodC,
)
from convert.adapters.solidworks.programs.configuration.pattern.views.Methods.Sldmgu.MgXformC.Restore import (
    KMethodProgram as KMethodD,
)
from convert.adapters.solidworks.programs.configuration.pattern.views.Methods.Sldmodu.MoPartConfigurationC.SerializeMBSMDataObjects import (
    KMethodProgram as KMethodE,
)
from convert.adapters.solidworks.programs.configuration.pattern.views.Methods.Sldmodu.MoThreedViewC.Serialize import (
    KMethodProgram as KMethodF,
)
from convert.adapters.solidworks.programs.configuration.pattern.views.Methods.Sldmodu.MoViewC.Serialize import (
    KMethodProgram as KMethodG,
)
from convert.adapters.solidworks.programs.configuration.pattern.views.Methods.Swccu.SuCArchive.ReadCount import (
    KMethodProgram as KMethodH,
)


# explicit ordering keeps generated imports deterministic while offsets govern composition
KMethodPrograms = (
    KMethodA,
    KMethodB,
    KMethodC,
    KMethodD,
    KMethodE,
    KMethodF,
    KMethodG,
    KMethodH,
)


# composed tables stay immutable because generated registries expose stable format facts
KFieldOwners, KAnnotationOps = BuildProgram(
    KMethodPrograms,
    "AnnotationManager",
)

# generated registry exports remain explicit for facade composition and extension imports
__all__ = [
    "KFieldOwners",
    "KAnnotationOps",
    "KMethodPrograms",
    "FieldOwners",
    "AnnotationOps",
]

# compatibility binding preserves its established public import after decomposition
FieldOwners = KFieldOwners

# compatibility binding preserves its established public import after decomposition
AnnotationOps = KAnnotationOps

# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .python_compat_annots import KPythonCompatAnnots
from .python_compat_models_api_1 import KLegacyApiOne
from .python_compat_models_api_2 import KLegacyApiTwo
from .python_compat_models_brep_1 import KLegacyBrepOne
from .python_compat_models_brep_2 import KLegacyBrepTwo
from .python_compat_models_core import KLegacyCore


# split identity registries combine here so installers consume one immutable contract
KLegacyModels = {
    **KLegacyCore,
    **KLegacyBrepOne,
    **KLegacyBrepTwo,
    **KLegacyApiOne,
    **KLegacyApiTwo,
}


# split annotation registries combine here so reflection installation remains declarative
KLegacyAnnots = KPythonCompatAnnots

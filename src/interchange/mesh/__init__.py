# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.mesh.SurfaceMesh import SurfaceMesh

BindCompatMut((SurfaceMesh,), {__name__: globals()})

# mesh consumers need one intentional historical public contract
__all__ = ("Mesh",)

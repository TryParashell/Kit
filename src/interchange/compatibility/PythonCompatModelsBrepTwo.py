# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

# historical brep identity set 2 keeps pickle globals stable after module splits
KLegacyBrepTwo: TypeMap[str, tuple[str, str]] = {
    "BrepCoedge": ("BrepCoedge", "interchange.brep"),
    "BrepLoop": ("BrepLoop", "interchange.brep"),
    "BrepWire": ("BrepWire", "interchange.brep"),
    "BrepFace": ("BrepFace", "interchange.brep"),
    "BrepFaceUse": ("BrepFaceUse", "interchange.brep"),
    "BrepShell": ("BrepShell", "interchange.brep"),
    "BrepShellUse": ("BrepShellUse", "interchange.brep"),
    "BrepRegion": ("BrepRegion", "interchange.brep"),
    "BrepBody": ("BrepBody", "interchange.brep"),
    "BrepModel": ("BrepModel", "interchange.brep"),
}

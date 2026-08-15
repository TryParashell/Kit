# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue
from typing import Protocol as TypeProtocol


# the validation view decouples topology storage from independent diagnostic passes
class BrepView(TypeProtocol):
    Curves: tuple[AnyValue, ...]
    Pcurves: tuple[AnyValue, ...]
    Surfaces: tuple[AnyValue, ...]
    Vertices: tuple[AnyValue, ...]
    Edges: tuple[AnyValue, ...]
    Coedges: tuple[AnyValue, ...]
    Loops: tuple[AnyValue, ...]
    Wires: tuple[AnyValue, ...]
    Faces: tuple[AnyValue, ...]
    FaceUses: tuple[AnyValue, ...]
    Shells: tuple[AnyValue, ...]
    ShellUses: tuple[AnyValue, ...]
    Regions: tuple[AnyValue, ...]
    Bodies: tuple[AnyValue, ...]
    SchemaVersion: str

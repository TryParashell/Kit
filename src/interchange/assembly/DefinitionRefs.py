# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue


# payload routing reads reference and origin fields together so they share one view
class DefinitionRefs:
    __slots__ = ()

    # body references keep solid topology reachable without embedding geometry
    @property
    def BodyIds(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "body_ids"))

    # mesh references keep tessellation reachable without duplicating payloads
    @property
    def MeshIds(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "mesh_ids"))

    # original path keeps provenance traceable back to the source container
    @property
    def SourcePath(self) -> str:
        return CastValue(str, getattr(self, "source_path"))

    # format id keeps multi format routing decisions possible downstream
    @property
    def SourceFormatId(self) -> str:
        return CastValue(str, getattr(self, "source_format_id"))

    # digest lets consumers detect source drift without rereading containers
    @property
    def SourceDigest(self) -> str:
        return CastValue(str, getattr(self, "source_sha256"))

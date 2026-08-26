# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange.payloads.PayloadRoles import PayloadRole


# payload consumers read identity and transport metadata through one typed view
class PayloadView:
    __slots__ = ()

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return CastValue(str, getattr(self, "id"))

    # format id keeps payload interpretation tied to its producing dialect
    @property
    def FormatId(self) -> str:
        return CastValue(str, getattr(self, "format_id"))

    # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> str:
        return CastValue(str, getattr(self, "kind"))

    # inline schema keeps payloads self describing without external lookups
    @property
    def SchemaText(self) -> str:
        return CastValue(str, getattr(self, "schema"))

    # digest lets consumers detect source drift without rereading containers
    @property
    def SourceDigest(self) -> str:
        return CastValue(str, getattr(self, "sha256"))

    # raw bytes keep vendor specifics recoverable even when schema parsing fails
    @property
    def PayloadData(self) -> bytes | None:
        return CastValue(bytes | None, getattr(self, "data"))

    # stream name tells extractors where the payload lives inside containers
    @property
    def SourceStream(self) -> str:
        return CastValue(str, getattr(self, "source_stream"))

    # role tags separate driven driving and reference usages cleanly
    @property
    def ValueRole(self) -> PayloadRole:
        return CastValue(PayloadRole, getattr(self, "role"))

    # extension hint keeps extracted files recognizable on disk immediately
    @property
    def FileExtension(self) -> str:
        return CastValue(str, getattr(self, "file_extension"))

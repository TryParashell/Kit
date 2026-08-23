# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.records.RecordProvenance import Provenance


# payload extensions need validation before writers derive filesystem paths
def FindExtError(ExtensionText: object) -> str:
    if not isinstance(ExtensionText, str):
        return "payload file extension must start with a period"
    NameValue = ExtensionText[1:] if ExtensionText.startswith(".") else ""
    if not NameValue or not NameValue[0].isascii() or not NameValue[0].isalnum():
        return "payload file extension must start with a period"
    IsInvalid = any(
        not Character.isascii() or not (Character.isalnum() or Character in "._-")
        for Character in NameValue
    )
    if IsInvalid or NameValue.endswith("."):
        return "payload file extension contains an invalid character"
    return ""


# native bytes need identity purpose and integrity metadata for lossless translation
@ModelDataMut
class BrepPayload(ModelBase):
    id: str
    format_id: str
    kind: str
    schema: str
    sha256: str
    data: bytes | None = None
    source_stream: str = ""
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
    role: PayloadRole = PayloadRole.KAuxiliary
    file_extension: str = ".bin"

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # format id keeps payload interpretation tied to its producing dialect
    @property
    def FormatId(self) -> str:
        return self.format_id

     # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> str:
        return self.kind

     # inline schema keeps payloads self describing without external lookups
    @property
    def SchemaText(self) -> str:
        return self.schema

     # digest lets consumers detect source drift without rereading containers
    @property
    def SourceDigest(self) -> str:
        return self.sha256

     # raw bytes keep vendor specifics recoverable even when schema parsing fails
    @property
    def PayloadData(self) -> bytes | None:
        return self.data

     # stream name tells extractors where the payload lives inside containers
    @property
    def SourceStream(self) -> str:
        return self.source_stream

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes

     # role tags separate driven driving and reference usages cleanly
    @property
    def ValueRole(self) -> PayloadRole:
        return self.role

     # extension hint keeps extracted files recognizable on disk immediately
    @property
    def FileExtension(self) -> str:
        return self.file_extension

    # invalid metadata must fail before bytes reach archive writers
    def __post_init__(self) -> None:
        if type(self.role) is not PayloadRole:
            raise TypeError("payload role must be a PayloadRole")
        ErrorText = FindExtError(self.file_extension)
        if ErrorText:
            raise ValueError(ErrorText)

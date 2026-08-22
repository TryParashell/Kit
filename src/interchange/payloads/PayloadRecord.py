# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar, TYPE_CHECKING
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
@ModelDataMut(
    DefaultMap={
        "data": None,
        "source_stream": "",
        "provenance": None,
        "role": PayloadRole.KAuxiliary,
        "file_extension": ".bin",
    },
    FactoryMap={"attributes": FreezeMapping},
)
class BrepPayload(ModelBase):
    id: str
    format_id: str
    kind: str
    schema: str
    sha256: str
    data: bytes | None
    source_stream: str
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    role: PayloadRole
    file_extension: str
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        FormatId: ClassVar[str]
        EntityKind: ClassVar[str]
        SchemaText: ClassVar[str]
        SourceDigest: ClassVar[str]
        PayloadData: ClassVar[bytes | None]
        SourceStream: ClassVar[str]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
        ValueRole: ClassVar[PayloadRole]
        FileExtension: ClassVar[str]

    # invalid metadata must fail before bytes reach archive writers
    def __post_init__(self) -> None:
        if type(self.role) is not PayloadRole:
            raise TypeError("payload role must be a PayloadRole")
        ErrorText = FindExtError(self.file_extension)
        if ErrorText:
            raise ValueError(ErrorText)

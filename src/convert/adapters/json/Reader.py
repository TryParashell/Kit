# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.adapters.base import ReadOptions
from convert.adapters.base import Source
from convert.adapters.json.StreamIo import ReadText
from interchange import CadDocument
from interchange import filter_document as FilterDocument


# this mixin isolates filtering and validation from probing behavior
class JsonReader:

    # this reader restores filters and validates one interchange document
    def ReadAction(
        self, SourceValue: Source, Options: ReadOptions | None = None
    ) -> CadDocument:
        Settings = Options or ReadOptions()
        Document = CadDocument.from_json(ReadText(SourceValue))
        if Settings.configuration is not None:
            Matches = {
                Config.id
                for Config in Document.configurations
                if Settings.configuration in {Config.id, Config.name}
            }
            if not Matches:
                raise ValueError(
                    f"configuration {Settings.configuration!r} is unavailable"
                )
            Configs = tuple(
                Replace(Config, active=Config.id in Matches)
                for Config in Document.configurations
            )
            Document = Replace(Document, configurations=Configs)
        Document = FilterDocument(
            Document,
            include_brep=Settings.include_brep,
            include_tessellation=Settings.include_tessellation,
            keep_payload_records=False,
        )
        if Settings.strict:
            Document.assert_valid()
        return Document

    read = ReadAction

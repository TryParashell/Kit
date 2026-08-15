# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions


# capture behavior isolates enforced public options from adapter and filesystem side effects
class CaptureEngine:

    # shared observations let write and conversion calls prove identical option enforcement
    def __init__(
        self,
        CapturedVals: list[dict[str, object]],
        SentinelValue: object,
    ) -> None:
        self.CapturedVals = CapturedVals
        self.SentinelValue = SentinelValue

    # write interception exists because public option enforcement happens before engine delegation
    def WriteTarget(
        self,
        DocumentData: object,
        TargetData: object,
        *,
        FormatId: str | None,
        WriteOpts: WriteOptions,
    ) -> object:
        self.CapturedVals.append(dict(WriteOpts.values))
        return self.SentinelValue

    # conversion interception exists because combined calls build their own write options
    def ConvertData(
        self,
        SourceData: object,
        TargetData: object,
        *,
        SourceFormat: str | None,
        DestFormat: str | None,
        ReadOpts: ReadOptions,
        WriteOpts: WriteOptions,
    ) -> object:
        self.CapturedVals.append(dict(WriteOpts.values))
        return self.SentinelValue

    # direct conversion interception keeps tests aligned with the concrete engine contract
    def convert(
        self,
        source: object,
        destination: object,
        *,
        source_format: str | None = None,
        destination_format: str | None = None,
        read_options: ReadOptions | None = None,
        write_options: WriteOptions | None = None,
    ) -> object:
        if write_options is None:
            raise TypeError("write options are required for conversion capture")
        self.CapturedVals.append(dict(write_options.OptionValues))
        return self.SentinelValue
